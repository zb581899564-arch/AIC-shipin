"""Meaningful CPU-only T engineering contracts; no model import or quality mock."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from fractions import Fraction

sys.dont_write_bytecode = True
import train_student as student
RUN = Path(__file__).resolve().parent.parent
student.helper_paths(RUN)
from sft_contract import assistant_labels
from contracts import answer_string, parse_segments
from training_target import target_text
from exact_pts import exact_native_pts


def test_production_cfr_tolerance_uses_native_ordinal_one():
    """Real T selector catches the reported ceil(FPS) off-by-one regression."""
    import production_t
    item = dict(video_id="v", n_frames=4, source_path="/approved/v.mp4", width=32, height=32,
        fps_num=30, fps_den=1, targetRatioWH=[9, 16], scope_start_sec=0, scope_end_sec=4 / 30,
        clock_branch="CFR_LEGACY")
    clock = dict(branch="CFR_LEGACY", pts=list(map(Fraction, ["0", ".034", ".068", ".102"])),
                 clock_record_sha256="a" * 64)
    manifest = dict(kind="NONTEST_FROZEN8", records=[item])
    window = dict(start_sec=0, end_sec=4 / 30, parsed_segments=[[.03334, .067]], status="MODEL_OK",
                  output_valid=True, parse_errors=[], clock_record_sha256="a" * 64)
    record = dict(video_id="v", n_frames=4, video_path=item["source_path"], targetRatioWH=[9, 16], fps=30, windows=[window])
    result = production_t.select_native_frames(manifest, [record], {"v": clock})
    assert [row["source_frame"] for row in result] == [1]
    # Same exact code must preserve a legitimate empty and block execution failure.
    empty = copy.deepcopy(record); empty["windows"][0].update(parsed_segments=[], status="LEGAL_EMPTY")
    assert production_t.select_native_frames(manifest, [empty], {"v": clock}) == []
    failed = copy.deepcopy(empty); failed["windows"][0].update(status="INFERENCE_FAILURE", output_valid=False)
    try:
        production_t.select_native_frames(manifest, [failed], {"v": clock})
    except (RuntimeError, ValueError):
        pass
    else:
        raise AssertionError("failed T window was accepted as empty")


def test_production_fractional_origin_preserves_boundary_ordinal_one():
    import production_t
    arrays = dict(raw_time_base="1/10", raw_first_pts_ticks=1, native_pts_ticks=[1, 3, 5])
    start, end = production_t.raw_window_bounds(arrays, .2, .4)
    assert start == .3 and end == .5
    points = [float(i * Fraction(arrays["raw_time_base"])) for i in arrays["native_pts_ticks"]]
    window = student.window_from_pts("source", "sha", points, start, end, "origin")
    assert window["planned_source_frame_ordinals"] == [1]
    assert window["planned_actual_pts_sec"] == [.3]


class StudentContracts(unittest.TestCase):
    def test_production_cfr_native_selector_regression(self):
        test_production_cfr_tolerance_uses_native_ordinal_one()

    def test_production_fractional_origin_regression(self):
        test_production_fractional_origin_preserves_boundary_ordinal_one()

    def test_all_frozen_runtime_helpers_exist(self):
        missing = [p for p in student.REQUIRED_HELPERS if not (RUN / p).is_file()]
        self.assertEqual(missing, [])

    def test_empty_target_has_supervised_json_and_end_tokens(self):
        target = target_text(dict(observation_complete=True, status="OBSERVED_EMPTY", segments=[]), 30)
        self.assertEqual(target, '{"segments":[]}')
        # Token IDs model the causal boundary, not training quality or tokenizer output.
        mask = assistant_labels([90, 91, 12, 13, 14, 99, 0], [1, 1, 1, 1, 1, 1, 0], [90, 91], [1, 1])
        self.assertEqual(mask["labels"], [-100, -100, 12, 13, 14, 99, -100])
        self.assertEqual(mask["tail_labels"], [-100, 12, 13, 14, 99, -100])
        self.assertEqual(mask["supervised_tokens"], 4)
        self.assertEqual(mask["assistant_token_ids"], [12, 13, 14, 99])

    def test_left_padding_prompt_video_and_padding_are_masked(self):
        mask = assistant_labels([0, 5, 6, 7, 8], [0, 1, 1, 1, 1], [0, 0, 5, 6], [0, 0, 1, 1])
        self.assertEqual(mask["labels"], [-100, -100, -100, 7, 8])
        self.assertEqual(mask["tail_labels"], [-100, 7, 8])
        with self.assertRaises(Exception):
            assistant_labels([5, 9, 7], [1, 1, 1], [5, 6], [1, 1])

    def test_unknown_missing_observation_never_becomes_empty(self):
        for label in (dict(status="UNKNOWN", segments=[]), dict(observation_complete=False, status="OBSERVED_EMPTY", segments=[]),
                      dict(observation_complete=True, status="OBSERVED_POSITIVE", segments=[])):
            with self.assertRaises(ValueError):
                target_text(label, 30)

    def test_same_20_prefix_is_inside_three_epochs(self):
        batches = student.schedule(128)
        self.assertEqual(len(batches), 24)
        self.assertEqual(batches[19]["epoch"], 3)
        self.assertEqual(batches[20]["epoch"], 3)
        self.assertEqual(sum(len(b["indices"]) for b in batches), 384)
        for epoch in (1, 2, 3):
            ids = [i for b in batches if b["epoch"] == epoch for i in b["indices"]]
            self.assertEqual(sorted(ids), list(range(128)))
        self.assertEqual(student.schedule(128), batches)

    def test_update20_epoch_end_is_saved_as_pending_checkpoint_and_dev(self):
        batches = student.schedule(145)
        report = dict(checkpoints=[dict(epoch=1, adapter_dir="epoch_1")], devmetrics=[dict(name="epoch_1_dev")], optimizer_steps=20)
        position = student.prefix_resume_position(batches, 20, report)
        self.assertEqual(position["pending_phase"], "EPOCH_END_CHECKPOINT_AND_DEV_PENDING")
        self.assertEqual(position["pending_epoch_end"], 2)
        self.assertEqual(position["next_epoch"], 3)
        self.assertEqual(position["next_schedule_index"], 20)
        self.assertEqual(position["completed_epoch_checkpoints"], report["checkpoints"])
        self.assertEqual(position["completed_epoch_devmetrics"], report["devmetrics"])
        position["report_snapshot"]["optimizer_steps"] = 99
        self.assertEqual(report["optimizer_steps"], 20)
        middle = student.prefix_resume_position(student.schedule(128), 20, report)
        self.assertEqual(middle["pending_phase"], "NEXT_TRAIN_BATCH")
        self.assertIsNone(middle["pending_epoch_end"])

    def test_genuine_cpu_adamw_rng_and_state_roundtrip_without_active_reset(self):
        import numpy as np
        import torch
        parameter = torch.nn.Parameter(torch.tensor([.25, -.5], device="cpu"))
        optimizer = torch.optim.AdamW([parameter], lr=1e-5)
        for _ in range(2):
            optimizer.zero_grad(); (parameter.square().sum()).backward(); optimizer.step()
        trainable = [("lora_engineering_fixture", parameter)]
        rng = student.rng_snapshot(torch, np, cuda=False)
        expected = dict(optimizer=optimizer.state_dict(), lora={trainable[0][0]: parameter.detach().clone()},
                        optimizer_parameter_name_order=[trainable[0][0]], **rng,
                        **student.prefix_resume_position(student.schedule(145), 20, dict(checkpoints=[], devmetrics=[])))
        optimizer_identity = id(optimizer); parameter_identity = id(parameter)
        with tempfile.TemporaryDirectory(prefix="aic-prefix-state-cpu-") as temporary:
            path = Path(temporary) / "own_state.pt"
            torch.save(expected, path)
            result = student.trusted_state_roundtrip(path, expected, optimizer, trainable, torch, np, cuda=False)
            self.assertEqual(result["status"], "PASS_TRUSTED_PREFIX_STATE_ROUNDTRIP")
            self.assertEqual((id(optimizer), id(parameter)), (optimizer_identity, parameter_identity))
            student.assert_tree_equal(rng, student.rng_snapshot(torch, np, cuda=False), torch, np)
            corrupt = torch.load(path, map_location="cpu", weights_only=False)
            first_state = next(iter(corrupt["optimizer"]["state"].values()))
            first_state["exp_avg"][0] += 1
            torch.save(corrupt, path)
            with self.assertRaisesRegex(ValueError, "tensor roundtrip mismatch"):
                student.trusted_state_roundtrip(path, expected, optimizer, trainable, torch, np, cuda=False)
            self.assertEqual((id(optimizer), id(parameter)), (optimizer_identity, parameter_identity))

    def test_insufficient_20_updates_never_adds_epoch_four(self):
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT"):
            student.schedule(96)
        batches = student.schedule(97)
        self.assertEqual(len(batches), 21)
        self.assertEqual([len(b["indices"]) for b in batches if b["epoch_last"]], [1, 1, 1])

    def test_source_isolation_rejects_youtube_path_and_bytes_overlap(self):
        def row(split, group, path, digest):
            return dict(window=dict(window_id=split, split=split, youtube_id=group, source_group=group,
                                    source_path="/home/inspur/aic_video_data/videos/" + path, source_sha256=digest))
        train = [row("train", "A", "a.mp4", "a")]
        dev = [row("dev", "B", "b.mp4", "b")]
        student.validate_isolation(train, dev)
        for bad in (row("dev", "A", "b.mp4", "b"), row("dev", "B", "a.mp4", "b"), row("dev", "B", "b.mp4", "a")):
            with self.assertRaisesRegex(ValueError, "leakage"):
                student.validate_isolation(train, [bad])

    def test_confirm_source_cannot_gain_train_membership_by_split_flag(self):
        original = [dict(split="train", sample_id="s1", youtube_id="Y", source_path="approved")]
        row = dict(window=dict(source_path="approved", youtube_id="Y", parent_sample_ids=["s1"]))
        student.validate_lineage([row], original, "train")
        foreign = dict(window=dict(source_path="confirm", youtube_id="Y", parent_sample_ids=["s1"]))
        with self.assertRaisesRegex(ValueError, "not in approved"):
            student.validate_lineage([foreign], original, "train")

    def test_floor_sampling_preserves_real_native_pts_and_endpoints(self):
        points = [100 + i * .04 + (i % 3) * .001 for i in range(200)]
        window = student.window_from_pts("source", "sha", points, 100, 108, "w")
        ids = window["planned_source_frame_ordinals"]
        self.assertEqual(len(ids), 64)
        self.assertEqual((ids[0], ids[-1]), (0, 199))
        self.assertEqual(window["planned_actual_pts_sec"], [points[i] for i in ids])
        self.assertNotEqual(ids, [round(i * 199 / 63) for i in range(64)])
        self.assertEqual(student.floor_indices(7, 8), [7])
        with self.assertRaises(ValueError):
            student.window_from_pts("source", "sha", [2, 1], 0, 3, "bad")

    def test_exact_pts_overrides_fps_and_restores_processor(self):
        class Processor:
            def _calculate_timestamps(self, indices, fps, merge_size=2):
                return [i / fps for i in indices]
        p = Processor()
        plan = dict(source_frame_ids=[0, 2, 4], source_relative_pts=[100, 100.3, 100.9], window_start=100)
        with exact_native_pts(p, plan, 30) as identity:
            times = p._calculate_timestamps([0, 2, 4], 30, 2)
            self.assertAlmostEqual(times[0], .15)
            self.assertAlmostEqual(times[1], .9)
            self.assertEqual(identity["padded_source_frame_ids"], [0, 2, 4, 4])
        self.assertNotIn("_calculate_timestamps", p.__dict__)
        self.assertEqual(p._calculate_timestamps([30], 30), [1])

    def test_target_endpoints_are_not_silently_rounded(self):
        self.assertEqual(answer_string([[.1234, .5678]], 1), '{"segments":[[0.1234,0.5678]]}')
        text = answer_string([[.12345, .6]], 1)
        self.assertEqual(text, '{"segments":[[0.12345,0.6]]}')
        self.assertEqual(parse_segments(text,1)[0], [[.12345,.6]])
        self.assertEqual(parse_segments('{"segments":[]}', 30)[0], [])
        self.assertIsNone(parse_segments("not JSON", 30)[0])

    def test_semantic_receipt_must_agree_with_real_raw_scope_and_response(self):
        original = dict(window_id="w", window=dict(window_pts_start_sec=10, window_pts_end_exclusive_sec=12),
                        actual_observation=dict(actual_pts_sec=[10, 11], frame_pixel_sha256=["p1", "p2"], source_frame_ordinals=[5, 9]))
        value = dict(window_id="w", observation_scope=dict(window_pts_start_sec=10, window_pts_end_exclusive_sec=12,
            sampled_pts_sec=[10, 11], all_provided_frames_reviewed=True), semantics_consistent=True, uncertain=False,
            reason="Observable event and boundaries agree.", issues=[])
        receipt = dict(raw_response=json.dumps(value), parsed_response=value, reason=value["reason"],
                       source_frame_pixel_sha256=["p1", "p2"], source_frame_ordinals=[5, 9], actual_pts_sec=[10, 11])
        student.validate_raw_semantic(receipt, original)
        for field, bad in (("uncertain", True), ("semantics_consistent", False), ("issues", ["unknown gap"]), ("reason", "different explanation")):
            changed = copy.deepcopy(receipt); raw = copy.deepcopy(value); raw[field] = bad
            changed["raw_response"] = json.dumps(raw)
            with self.assertRaises(ValueError):
                student.validate_raw_semantic(changed, original)
        changed = copy.deepcopy(receipt); changed["source_frame_pixel_sha256"][0] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity"):
            student.validate_raw_semantic(changed, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
