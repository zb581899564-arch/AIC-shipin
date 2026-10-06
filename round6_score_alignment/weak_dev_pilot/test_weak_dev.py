from __future__ import annotations

import unittest

from freeze_inputs import evenly_spaced_indices, record_for
from weak_metrics import center_crop, iou_xywh, score_records, summarize
from temporal_metrics import f1, union_intervals
from compare_spatial_adapter import compare


def sample(key: str, youtube_id: str, weak):
    return {"sample_key": key, "video_id": key.split("#")[0], "youtube_id": youtube_id,
            "source_width": 534, "source_height": 300, "target_ratio_wh": [9.0, 16.0],
            "weak_roi_xywh": weak}


class FreezeBoundaryTests(unittest.TestCase):
    def test_fixed_even_selection_keeps_endpoints_and_never_duplicates(self):
        self.assertEqual(evenly_spaced_indices(0), [])
        self.assertEqual(evenly_spaced_indices(3), [0, 1, 2])
        self.assertEqual(evenly_spaced_indices(5), [0, 1, 3, 4])
        self.assertEqual(evenly_spaced_indices(9), [0, 3, 5, 8])

    def test_record_rejects_identity_mismatch(self):
        manifest = {"video_id": "a", "row_index": 0, "youtube_id": "source",
                    "split": "dev", "source_path": "/home/inspur/aic_video_data/videos/a.mp4"}
        row = {"video_id": "b", "cropRois": [[0, [0, 0, 169, 300]]],
               "clip": {"start_sec": 0}, "targetRatioWH": [9, 16]}
        mapping = {"video_id": "b", "status": "usable"}
        with self.assertRaisesRegex(ValueError, "identity"):
            record_for(manifest, row, mapping, 0)

    def test_record_rejects_out_of_bounds_box(self):
        manifest = {"video_id": "a", "row_index": 0, "youtube_id": "source",
                    "split": "dev", "source_path": "/home/inspur/aic_video_data/videos/a.mp4"}
        row = {"video_id": "a", "cropRois": [[0, [400, 0, 169, 300]]],
               "clip": {"start_sec": 0}, "targetRatioWH": [9, 16]}
        mapping = {"video_id": "a", "status": "usable", "source_path": manifest["source_path"],
                   "source_probe": {"width": 534, "height": 300, "avg_fps": 30, "nb_frames": 4500},
                   "clip_fps": 30}
        with self.assertRaisesRegex(ValueError, "outside"):
            record_for(manifest, row, mapping, 0)


class WeakMetricBoundaryTests(unittest.TestCase):
    def test_teacher_169_by_300_is_not_forced_to_exact_9_by_16(self):
        p0 = center_crop(534, 300, [9, 16])
        self.assertEqual(p0[:3], [183, 1, 168])
        self.assertAlmostEqual(p0[3], 298.6666666666667)
        self.assertGreater(iou_xywh(p0, [183, 0, 169, 300]), 0.98)

    def test_invalid_model_output_keeps_zero_in_denominator(self):
        frames = [sample("v#0", "g", [183, 0, 169, 300]),
                  sample("v#1", "g", [183, 0, 169, 300])]
        preds = {"v#0": {"output_valid": True, "box_xywh": [183, 0, 169, 300]},
                 "v#1": {"output_valid": False, "box_xywh": [183, 0, 169, 300]}}
        rows = score_records(frames, preds)
        self.assertEqual(rows[0]["WEAK_PROXY_IoU_P1"], 1)
        self.assertEqual(rows[1]["WEAK_PROXY_IoU_P1"], 0)
        self.assertEqual(summarize(rows, bootstrap=100)["P1_valid_rate"], .5)

    def test_prediction_universe_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError, "prediction set"):
            score_records([sample("v#0", "g", [183, 0, 169, 300])], {})

    def test_macro_source_not_frame_micro(self):
        frames = [sample("a#0", "g1", [183, 0, 169, 300]),
                  sample("b#0", "g2", [0, 0, 169, 300]),
                  sample("b#1", "g2", [0, 0, 169, 300]),
                  sample("b#2", "g2", [0, 0, 169, 300])]
        result = summarize(score_records(frames), bootstrap=10)
        per = {g["youtube_id"]: g["P0_mean"] for g in result["per_source_group"]}
        self.assertAlmostEqual(result["P0_source_macro_mean"], (per["g1"] + per["g2"]) / 2)
        self.assertNotAlmostEqual(result["P0_source_macro_mean"],
                                  (per["g1"] + 3 * per["g2"]) / 4)


class WeakTemporalBoundaryTests(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(f1([[1, 3]], [[1, 3]]), 1.0)

    def test_partial_intersection(self):
        self.assertAlmostEqual(f1([[1, 3]], [[2, 4]]), 0.5)

    def test_overlap_does_not_duplicate_duration(self):
        self.assertEqual(union_intervals([[1, 3], [2, 4]]), [[1, 4]])
        self.assertEqual(f1([[1, 3], [2, 4]], [[1, 4]]), 1.0)

    def test_empty_prediction_is_zero(self):
        self.assertEqual(f1([], [[1, 3]]), 0.0)


class SpatialTrainGateTests(unittest.TestCase):
    def test_equal_adapter_stops(self):
        frames = [sample("a#0", "g1", [0, 0, 169, 300]),
                  sample("b#0", "g2", [0, 0, 169, 300])]
        base = [{"sample_key": f["sample_key"], "output_valid": True,
                 "box_xywh": [183, 1, 168, 298.6666666666667]} for f in frames]
        self.assertEqual(compare(frames, base, base)["full_training_gate"], "STOP_KEEP_BASE")

    def test_paired_improvement_can_pass(self):
        frames = [sample("a#0", "g1", [0, 0, 169, 300]),
                  sample("b#0", "g2", [0, 0, 169, 300])]
        base = [{"sample_key": f["sample_key"], "output_valid": True,
                 "box_xywh": [183, 1, 168, 298.6666666666667]} for f in frames]
        better = [{"sample_key": f["sample_key"], "output_valid": True,
                   "box_xywh": [0, 1, 168, 298.6666666666667]} for f in frames]
        self.assertEqual(compare(frames, base, better)["full_training_gate"], "PASS")

    def test_legality_drop_stops_even_when_iou_improves(self):
        frames = [sample("a#0", "g1", [0, 0, 169, 300]),
                  sample("b#0", "g2", [0, 0, 169, 300])]
        base = [{"sample_key": f["sample_key"], "output_valid": True,
                 "box_xywh": [183, 1, 168, 298.6666666666667]} for f in frames]
        candidate = [{"sample_key": "a#0", "output_valid": True,
                      "box_xywh": [0, 1, 168, 298.6666666666667]},
                     {"sample_key": "b#0", "output_valid": False, "box_xywh": None}]
        self.assertEqual(compare(frames, base, candidate)["full_training_gate"], "STOP_KEEP_BASE")


if __name__ == "__main__":
    unittest.main()
