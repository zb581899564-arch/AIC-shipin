"""Regression contracts for duration-only cells in the actual PTS time grid."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import unittest

from select_windows import (HERE, SELECTOR_REVISION, audit_grid, load_identities, make_window,
    natural_windows, parse_clock_frames, rank_sources, spaced_indices, validate_isolation)


def source(rank=2):
    return {"split": "train", "source_rank": rank, "source_group": "synthetic_group",
        "youtube_id": "synthetic_group", "downloaded_clip_group": "synthetic_clip",
        "source_path": "/home/inspur/aic_video_data/videos/s/synthetic.mp4",
        "parent_sample_ids": ["synthetic_sample"], "parent_video_ids": ["synthetic_video"]}


def clock(points, last_duration):
    frames = [{"best_effort_timestamp_time": str(p), "pkt_duration_time": str(last_duration)} for p in points]
    actual, evidence = parse_clock_frames(frames)
    evidence["source_sha256"] = "a" * 64
    return actual, evidence


class GridRegression(unittest.TestCase):
    def test_actual_failure_extent_has_zero_pts_tail_but_selects_last_real_window(self):
        points, evidence = clock([0, 30.01, 60.02, 90.03, 120.04, 149.983167], 0.041708)
        audit = audit_grid(points, evidence)
        window = make_window(source(), points, evidence)
        self.assertEqual(natural_windows(0, 150.024875)[-1], (150, 150.024875))
        self.assertEqual(audit["nonempty_pts_window_count"], 5)
        self.assertEqual(audit["non_sampleable_time_cells"][0]["presentation_start_frame_count"], 0)
        self.assertEqual((window["window_ordinal"], window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"]), (4, 120, 150))
        self.assertEqual(window["planned_source_frame_ordinals"][-1], 5)
        self.assertAlmostEqual(window["terminal_display_remainder_outside_last_pts_cell_sec"], 0.024875)
        self.assertTrue(window["selected_cell_reaches_last_source_frame"])

    def test_tail_with_an_actual_presentation_start_is_still_sampled(self):
        points, evidence = clock([0, 30, 60, 90, 120, 150.00001], 0.04)
        window = make_window(source(), points, evidence)
        self.assertEqual(window["window_ordinal"], 5)
        self.assertEqual(window["planned_actual_pts_sec"], [150.00001])
        self.assertEqual(window["source_non_sampleable_time_cells"], [])

    def test_nonzero_origin_preserves_the_original_grid(self):
        points, evidence = clock([0.125, 30.13, 60.14, 90.15, 120.16, 150.108167], 0.041708)
        window = make_window(source(), points, evidence)
        self.assertEqual((window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"]), (120.125, 150.125))
        self.assertEqual(window["source_clock_first_pts_sec"], 0.125)
        self.assertEqual(window["planned_actual_pts_sec"][-1], 150.108167)

    def test_negative_origin_is_not_reset_or_invented(self):
        points, evidence = clock([-0.125, 29.88, 59.85], 0.04)
        audit = audit_grid(points, evidence)
        self.assertEqual(audit["cells"][0]["pts_start_sec"], -0.125)
        self.assertTrue(audit["all_source_pts_covered_once"])

    def test_exact_endpoint_adds_no_duration_only_grid_cell(self):
        points, evidence = clock([0, 20, 40, 59.96], 0.04)
        audit = audit_grid(points, evidence)
        self.assertEqual(audit["natural_window_count"], 2)
        self.assertEqual(audit["non_sampleable_time_cells"], [])

    def test_long_final_display_preserves_every_clock_only_cell(self):
        points, evidence = clock([0, 30, 60, 90, 120, 149.98], 70)
        window = make_window(source(), points, evidence)
        self.assertEqual([c["window_ordinal"] for c in window["source_non_sampleable_time_cells"]], [5, 6, 7])
        self.assertEqual(window["source_clock_end_exclusive_sec"], 219.98)
        self.assertEqual(window["window_ordinal"], 4)
        self.assertAlmostEqual(window["terminal_display_remainder_outside_last_pts_cell_sec"], 69.98)

    def test_interior_zero_pts_cells_are_audited_not_synthetic_frames(self):
        points, evidence = clock([0, 0.01, 90, 90.01, 149.98], 0.04)
        audit = audit_grid(points, evidence)
        self.assertEqual(audit["eligible_window_ordinals"], [0, 3, 4])
        self.assertEqual([c["window_ordinal"] for c in audit["non_sampleable_time_cells"]], [1, 2, 5])
        window = make_window(source(rank=1), points, evidence)
        self.assertEqual(window["window_ordinal"], 3)
        self.assertEqual(window["planned_source_frame_ordinals"], [2, 3])
        self.assertEqual(window["label_status"], "UNLABELLED")

    def test_boundary_pts_belongs_to_exactly_one_cell(self):
        points, evidence = clock([0, 30, 60, 90], 0.04)
        audit = audit_grid(points, evidence)
        self.assertEqual([c["presentation_start_frame_count"] for c in audit["cells"]], [1, 1, 1, 1])
        self.assertEqual(sum(c["presentation_start_frame_count"] for c in audit["cells"]), len(points))

    def test_source_order_and_window_metadata_identity_do_not_change(self):
        points, evidence = clock([0, 29.99, 30.01, 59.99, 60.01, 89.98], 0.02)
        row = source(rank=0)
        window = make_window(row, points, evidence)
        self.assertEqual(window["source_rank"], row["source_rank"])
        self.assertEqual(window["source_group"], row["source_group"])
        self.assertEqual(window["source_path"], row["source_path"])
        self.assertEqual(window["window_ordinal"], 0)
        self.assertEqual(window["planned_source_frame_ordinals"], [0, 1])

    def test_grid_extent_disagrees_with_actual_pts_stops(self):
        points, evidence = clock([0, 1], 0.1)
        evidence["last_pts_sec"] = 1.1
        with self.assertRaises(ValueError):
            audit_grid(points, evidence)

    def test_duplicate_missing_or_nonfinite_frame_clock_still_stops(self):
        for bad in ("0", "N/A", "nan"):
            with self.assertRaises(ValueError):
                parse_clock_frames([{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": bad, "pkt_duration_time": "0.04"}])

    def test_missing_actual_last_frame_duration_still_stops(self):
        with self.assertRaises(ValueError):
            parse_clock_frames([{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": "1"}])

    def test_sampling_has_actual_endpoints_no_duplicate_ordinals(self):
        selected = spaced_indices(400, 3400)
        self.assertEqual((len(selected), selected[0], selected[-1], len(set(selected))), (64, 400, 3399, 64))

    def test_new_window_uses_existing_unchanged_teacher_window_contract(self):
        points, evidence = clock([0, 30.01, 60.02, 90.03, 120.04, 149.983167], 0.041708)
        window = make_window(source(), points, evidence)
        original = HERE.parent / "supervision"
        # Separate Python process ensures the old teacher module still imports
        # its own unchanged v1 dependency; no teacher file is copied or edited.
        code = "import json,sys;sys.path.insert(0,sys.argv[1]);import validate_teacher as t;t.validate_window(json.load(sys.stdin))"
        result = subprocess.run([sys.executable, "-B", "-c", code, str(original)], input=json.dumps(window),
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_time_cell_never_has_empty_semantic_label(self):
        points, evidence = clock([0, 30.01, 60.02, 90.03, 120.04, 149.983167], 0.041708)
        window = make_window(source(), points, evidence)
        self.assertTrue(all(c["empty_semantic_label"] is False for c in window["source_non_sampleable_time_cells"]))
        self.assertTrue(window["non_sampleable_cells_are_not_empty_labels"])
        self.assertFalse(window["old_positive_segments_used"])


class SourceContracts(unittest.TestCase):
    def test_pinned_train_dev_counts_sha_and_youtube_isolation(self):
        root = HERE.parents[3] / "r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs"
        train = load_identities(root / "train_temporal.jsonl", "train")
        dev = load_identities(root / "dev_temporal.jsonl", "dev")
        validate_isolation(train, dev)
        self.assertEqual((len(train), len(dev)), (704, 104))
        self.assertEqual((len(rank_sources(train, "train")), len(rank_sources(dev, "dev"))), (602, 96))

    def test_source_prefix_and_order_match_v1_for_first_three_real_train_groups(self):
        root = HERE.parents[3] / "r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs"
        ranked = rank_sources(load_identities(root / "train_temporal.jsonl", "train"), "train")
        self.assertEqual([r["source_group"] for r in ranked[:3]], ["oq_GMEBnDqA", "Re22hIsmVIA", "2dKTLCv__ds"])
        self.assertEqual(ranked[:128], ranked[:512][:128])

    def test_old_positive_values_do_not_select_windows(self):
        row = {"sample_id": "x", "video_id": "v", "youtube_id": "g", "source_group": "clip",
               "source_path": "/source.mp4", "segments_clip_local": [[1, 2]], "clip_start_sec": 100}
        self.assertEqual(rank_sources([row], "train"), rank_sources([dict(row, segments_clip_local=[], clip_start_sec=0)], "train"))

    def test_youtube_group_leakage_rejected_even_for_distinct_downloads(self):
        with self.assertRaises(ValueError):
            validate_isolation([{"youtube_id": "g", "source_path": "/a"}], [{"youtube_id": "g", "source_path": "/b"}])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    if args.receipt:
        target = args.receipt.resolve()
        if HERE not in target.parents or target.exists():
            raise ValueError("fresh CPU receipt must remain in supervision_v2")
        target.write_text(json.dumps({"schema": "aic_selector_v2_cpu_contract_result_v1",
            "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "selector_revision": SELECTOR_REVISION,
            "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "passed": result.wasSuccessful(), "full_linux_128_32_selection_run_by_this_agent": False,
            "labels_generated": False, "gpu_used": False, "teacher_contract_unchanged": True}, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
