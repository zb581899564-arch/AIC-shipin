"""CPU contracts for window coverage, source isolation and empty/uncertain semantics."""
import copy
import argparse
import datetime as dt
import json
from pathlib import Path
import unittest

from select_windows import (HERE, load_identities, make_window, natural_windows, parse_clock_frames,
                            rank_sources, spaced_indices, validate_isolation)
from validate_teacher import make_record, prompt_for, strict_json, summarize, text_sha
from check_supervision_gate import decision, REVIEW_FLAGS


def fixture():
    source = {"split": "train", "source_rank": 0, "source_group": "synthetic_group",
        "youtube_id": "synthetic_group", "downloaded_clip_group": "synthetic_clip",
        "source_path": "/home/inspur/aic_video_data/videos/s/synthetic.mp4",
        "parent_sample_ids": ["synthetic_parent"], "parent_video_ids": ["synthetic_video"]}
    points, clock = parse_clock_frames([{"best_effort_timestamp_time": str(i / 10), "pkt_duration_time": "0.1"}
                                        for i in range(301)])
    clock.update(source_sha256="a" * 64)
    window = make_window(source, points, clock)
    observation = {"decode_status": "PASS_REAL_SEQUENTIAL_DECODE", "pixel_identity_status": "PASS",
        "all_planned_frames_delivered": True, **{k: window[k] for k in
        ("window_id", "source_path", "source_sha256", "clock_sequence_sha256")},
        "source_frame_ordinals": window["planned_source_frame_ordinals"], "actual_pts_sec": window["planned_actual_pts_sec"],
        "frame_pixel_sha256": ["b" * 64] * len(window["planned_actual_pts_sec"]),
        "input_contract_sha256": "c" * 64, "actual_processed_pixels_per_frame": [32768] * len(window["planned_actual_pts_sec"]),
        "max_pixels_per_frame": 32768, "max_sequence_length": 6144, "input_sequence_length": 1296, "max_frames": 64}
    teacher = {"base_model_id": "Qwen/Qwen3-VL-32B-Instruct", "model_id": "Qwen/Qwen3-VL-32B-Instruct-GGUF",
        "model_revision": "e3e1fe0c76de7ee58ea65db420c643adfe2e457c",
        "inference_status": "PASS_REAL_TEACHER_GENERATION", "production_test_access": False,
        "capacity_admission_pass": True, "job_source_lock_sha256": "d" * 64,
        "prompt_sha256": text_sha(prompt_for(window, observation)),
        "weight_files": [
            {"path": "SYNTHETIC_TEST_ONLY/Qwen3VL-32B-Instruct-Q4_K_M.gguf", "sha256": "5cf0136e721d6294718ec71fd8c93b17ab5dd4e2714d6079e83fa46571ad94c8"},
            {"path": "SYNTHETIC_TEST_ONLY/mmproj-Qwen3VL-32B-Instruct-F16.gguf", "sha256": "8617824839df91f84b4840ad5084dcf50a1403a435a1f4cfc4d8c84ce6cac2fc"}],
        "runtime_revision": "SYNTHETIC_TEST_ONLY", "generated_utc": "2026-10-07T00:00:00Z"}
    response = {"window_id": window["window_id"], "observation_scope": {
        "window_pts_start_sec": window["window_pts_start_sec"],
        "window_pts_end_exclusive_sec": window["window_pts_end_exclusive_sec"],
        "sampled_pts_sec": observation["actual_pts_sec"], "all_provided_frames_reviewed": True},
        "retained_segments": [{"start_sec": 2.0, "end_sec": 4.0, "reason": "Visible distinct action starts and completes in the provided frames"}],
        "explicit_no_highlight": False, "uncertain": False, "uncertainty_reasons": [],
        "decision_reason": "Only the distinct event has explanatory retention evidence in this sampled window", "boundary_notes": []}
    return window, observation, teacher, response


class WindowContracts(unittest.TestCase):
    def test_natural_windows_cover_nonzero_actual_pts_and_tail_without_overlap(self):
        windows = natural_windows(1.25, 64.0)
        self.assertEqual(windows, [(1.25, 31.25), (31.25, 61.25), (61.25, 64.0)])

    def test_30s_exact_source_does_not_add_empty_tail(self):
        self.assertEqual(natural_windows(0, 60), [(0, 30), (30, 60)])

    def test_missing_actual_final_duration_stops(self):
        with self.assertRaises(ValueError):
            parse_clock_frames([{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": "1"}])

    def test_missing_pts_is_not_dropped(self):
        with self.assertRaises(ValueError):
            parse_clock_frames([{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": "N/A", "pkt_duration_time": "1"}])

    def test_repeated_or_nonfinite_pts_stops(self):
        for second in ("0", "NaN"):
            with self.assertRaises(ValueError):
                parse_clock_frames([{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": second, "pkt_duration_time": "1"}])

    def test_sampling_includes_actual_first_and_last_frames(self):
        indices = spaced_indices(100, 4100)
        self.assertEqual((len(indices), indices[0], indices[-1]), (64, 100, 4099))
        self.assertEqual(len(set(indices)), 64)

    def test_old_positive_bounds_do_not_select_new_window(self):
        row = {"sample_id": "x", "video_id": "v", "youtube_id": "g", "source_group": "g_clip",
               "source_path": "/home/inspur/aic_video_data/videos/g/g.mp4", "clip_start_sec": 91, "segments_clip_local": [[2, 3]]}
        changed = dict(row, clip_start_sec=0, segments_clip_local=[])
        self.assertEqual(rank_sources([row], "train"), rank_sources([changed], "train"))

    def test_same_youtube_different_clips_cannot_cross_split(self):
        train = [{"youtube_id": "g", "source_path": "/approved/a.mp4"}]
        dev = [{"youtube_id": "g", "source_path": "/approved/b.mp4"}]
        with self.assertRaises(ValueError):
            validate_isolation(train, dev)

    def test_source_ranking_is_stable_prefix_not_label_dependent(self):
        rows = [{"sample_id": str(i), "video_id": "v" + str(i), "youtube_id": "g" + str(i),
                 "source_group": "clip" + str(i), "source_path": "/x/" + str(i)} for i in range(150)]
        ordered = rank_sources(rows, "train")
        self.assertEqual(ordered[:128], rank_sources(list(reversed(rows)), "train")[:128])

    def test_original_train_dev_bytes_counts_and_isolation(self):
        root = HERE.parents[3] / "r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs"
        train = load_identities(root / "train_temporal.jsonl", "train")
        dev = load_identities(root / "dev_temporal.jsonl", "dev")
        validate_isolation(train, dev)
        self.assertEqual((len(train), len(dev)), (704, 104))
        self.assertEqual((len(rank_sources(train, "train")), len(rank_sources(dev, "dev"))), (602, 96))


class TeacherContracts(unittest.TestCase):
    def record(self, change=None):
        window, observation, teacher, response = fixture()
        if change:
            change(window, observation, teacher, response)
        return make_record(window, observation, teacher, json.dumps(response))

    def test_valid_positive_is_weak_interval_target(self):
        record = self.record()
        self.assertTrue(record["sft_eligible"])
        self.assertEqual(json.loads(record["target_json"]), {"segments": [[2.0, 4.0]]})
        self.assertEqual(record["label_status"], "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH")

    def test_explicit_justified_no_highlight_is_legal_empty(self):
        def change(w, o, t, r):
            r.update(retained_segments=[], explicit_no_highlight=True, decision_reason="Ordinary static background throughout the provided samples")
        record = self.record(change)
        self.assertTrue(record["sft_eligible"])
        self.assertEqual(record["target_json"], '{"segments":[]}')

    def test_empty_without_explicit_no_highlight_is_rejected(self):
        record = self.record(lambda w, o, t, r: r.update(retained_segments=[]))
        self.assertFalse(record["sft_eligible"])
        self.assertIsNone(record["target_json"])

    def test_uncertain_empty_remains_excluded_unknown(self):
        record = self.record(lambda w, o, t, r: r.update(retained_segments=[], uncertain=True,
            uncertainty_reasons=["Action may occur between sparse delivered samples"]))
        self.assertEqual(record["status"], "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET")
        self.assertIsNone(record["target_json"])

    def test_uncertain_positive_candidates_are_preserved_but_excluded(self):
        record = self.record(lambda w, o, t, r: r.update(uncertain=True, uncertainty_reasons=["Event crosses an unseen boundary"]))
        self.assertFalse(record["sft_eligible"])
        self.assertEqual(len(record["retained_segments"]), 1)

    def test_uncertain_cannot_claim_explicit_empty(self):
        record = self.record(lambda w, o, t, r: r.update(retained_segments=[], uncertain=True,
            explicit_no_highlight=True, uncertainty_reasons=["Missing observation"]))
        self.assertEqual(record["status"], "INVALID_TEACHER_OR_INPUT_RECEIPT")

    def test_missing_or_mismatched_actual_pts_excludes_target(self):
        record = self.record(lambda w, o, t, r: o.update(actual_pts_sec=[0.0]))
        self.assertFalse(record["sft_eligible"])

    def test_missing_frame_pixel_identity_excludes_target(self):
        record = self.record(lambda w, o, t, r: o.update(frame_pixel_sha256=[]))
        self.assertFalse(record["sft_eligible"])

    def test_processor_overflow_excludes_target(self):
        record = self.record(lambda w, o, t, r: o.update(input_sequence_length=7000))
        self.assertFalse(record["sft_eligible"])

    def test_same_8b_teacher_fallback_is_rejected(self):
        record = self.record(lambda w, o, t, r: t.update(base_model_id="Qwen/Qwen3-VL-8B-Instruct"))
        self.assertFalse(record["sft_eligible"])

    def test_missing_projector_or_wrong_weight_sha_is_rejected(self):
        self.assertFalse(self.record(lambda w, o, t, r: t.update(weight_files=t["weight_files"][:1]))["sft_eligible"])
        self.assertFalse(self.record(lambda w, o, t, r: t["weight_files"][0].update(sha256="f" * 64))["sft_eligible"])

    def test_prompt_revision_or_capacity_mismatch_is_rejected(self):
        for change in (lambda w, o, t, r: t.update(prompt_sha256="f" * 64),
                       lambda w, o, t, r: t.update(model_revision="f" * 40),
                       lambda w, o, t, r: t.update(capacity_admission_pass=False)):
            self.assertFalse(self.record(change)["sft_eligible"])

    def test_foreign_teacher_scope_is_rejected(self):
        record = self.record(lambda w, o, t, r: r["observation_scope"].update(window_pts_end_exclusive_sec=35))
        self.assertFalse(record["sft_eligible"])

    def test_out_of_scope_overlapping_or_boolean_bounds_rejected(self):
        for segments in ([{"start_sec": 2, "end_sec": 31, "reason": "event"}],
                         [{"start_sec": True, "end_sec": 3, "reason": "event"}],
                         [{"start_sec": 2, "end_sec": 4, "reason": "a"}, {"start_sec": 3, "end_sec": 5, "reason": "b"}]):
            self.assertFalse(self.record(lambda w, o, t, r: r.update(retained_segments=segments))["sft_eligible"])

    def test_multisegment_target_keeps_every_segment(self):
        record = self.record(lambda w, o, t, r: r["retained_segments"].append({"start_sec": 5, "end_sec": 6, "reason": "second completed event"}))
        self.assertTrue(record["sft_eligible"])
        self.assertEqual(len(json.loads(record["target_json"])["segments"]), 2)

    def test_more_than_five_segments_not_silently_clipped(self):
        segments = [{"start_sec": i * 2, "end_sec": i * 2 + 1, "reason": "distinct event"} for i in range(6)]
        record = self.record(lambda w, o, t, r: r.update(retained_segments=segments))
        self.assertEqual(record["status"], "EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT")
        self.assertEqual(len(record["retained_segments"]), 6)

    def test_duplicate_keys_nonfinite_and_markdown_are_not_cleaned(self):
        for raw in ('{"window_id":"a","window_id":"b"}', '{"x":NaN}', '```json\n{}\n```'):
            with self.assertRaises(ValueError):
                strict_json(raw)

    def test_raw_invalid_answer_is_retained_and_not_made_empty(self):
        w, o, t, r = fixture()
        record = make_record(w, o, t, "not generated JSON")
        self.assertEqual(record["raw_answer"], "not generated JSON")
        self.assertIsNone(record["target_json"])

    def test_explanations_required(self):
        record = self.record(lambda w, o, t, r: r.update(decision_reason=""))
        self.assertFalse(record["sft_eligible"])

    def test_summary_never_admits_semantic_training(self):
        summary = summarize([self.record()])
        self.assertEqual(summary["positive_by_split"]["train"], 1)
        self.assertFalse(summary["semantic_training_admitted"])


class StopGateContracts(unittest.TestCase):
    def test_unavailable_supervision_stops_after_first_workday(self):
        gate = decision({"status": "STOP_32B_TEACHER_CAPACITY"}, None, None,
                        dt.datetime.fromisoformat("2026-10-08T00:00:00+08:00"))
        self.assertEqual(gate["status"], "STOP_T_FIRST_WORKDAY_SUPERVISION_UNAVAILABLE")
        self.assertFalse(gate["same_8b_teacher_fallback"])
        self.assertEqual(gate["continue_low_cost_candidate"], "Z_WITHOUT_WAITING_FOR_T")

    def test_data_pass_still_does_not_start_training(self):
        report = {"positive_by_split": {"train": 10, "dev": 2}, "explicit_empty_by_split": {"train": 3, "dev": 1},
                  "eligible_by_split": {"train": 128, "dev": 32}, "weak_teacher_only": True,
                  "unlabelled_windows_never_converted_to_empty": True}
        gate = decision({"status": "PASS_REAL_STRONGER_TEACHER_ADMISSION"}, report, {flag: True for flag in REVIEW_FLAGS},
                        dt.datetime.fromisoformat("2026-10-07T12:00:00+08:00"))
        self.assertEqual(gate["status"], "PASS_SUPERVISION_PREPARATION_ONLY_REQUIRES_TRAINING_ADMISSION")
        self.assertFalse(gate["semantic_training_admitted"])

    def test_missing_natural_empty_cannot_be_waived_to_meet_quota(self):
        report = {"positive_by_split": {"train": 128, "dev": 32}, "explicit_empty_by_split": {"train": 0, "dev": 0},
                  "eligible_by_split": {"train": 128, "dev": 32}, "weak_teacher_only": True,
                  "unlabelled_windows_never_converted_to_empty": True}
        gate = decision({"status": "PASS_REAL_STRONGER_TEACHER_ADMISSION"}, report, {flag: True for flag in REVIEW_FLAGS},
                        dt.datetime.fromisoformat("2026-10-08T00:00:00+08:00"))
        self.assertEqual(gate["status"], "STOP_T_FIRST_WORKDAY_SUPERVISION_UNAVAILABLE")

    def test_capacity_block_is_not_ignored_by_semantic_receipt(self):
        report = {"positive_by_split": {"train": 10, "dev": 2}, "explicit_empty_by_split": {"train": 3, "dev": 1},
                  "eligible_by_split": {"train": 128, "dev": 32}, "weak_teacher_only": True,
                  "unlabelled_windows_never_converted_to_empty": True}
        gate = decision({"status": "STOP_32B_TEACHER_CAPACITY"}, report, {flag: True for flag in REVIEW_FLAGS},
                        dt.datetime.fromisoformat("2026-10-07T12:00:00+08:00"))
        self.assertFalse(gate["semantic_training_admitted"])
        self.assertTrue(gate["reasons"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    if args.receipt:
        target = args.receipt.resolve()
        if HERE not in target.parents or target.exists():
            raise ValueError("fresh CPU receipt must stay in supervision")
        report = {"schema": "aic_supervision_cpu_contract_result_v1", "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "passed": result.wasSuccessful(), "actual_media_clock_selector_run": False,
            "actual_teacher_generation_run": False, "confirm_opened": False, "contest_assets_opened": False, "gpu_used": False}
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
