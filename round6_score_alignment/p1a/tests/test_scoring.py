"""Hand-computed boundary tests for the joint scorer.

Every expected number is derived by hand here and written as a literal:

    F = 2 * sum(matched_frame_IoU) / (N_pred + N_gt)
    both empty -> 1 ; one side empty -> 0 ; mean over the index videos, x100

Index: two videos ("0", "1"), 720x1280, ratio [16,9] -> a box [0,0,720] has
derived height 720*9/16 = 405 (area 291600) and fits the frame.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aic6 import scoring
from tests.hand_cases import (
    BOX_FULL,
    BOX_NO_OVERLAP,
    BOX_SHIFTED_HIGH,
    BOX_SHIFTED_LOW,
    two_video_index,
    write_predictions,
    write_raw_predictions,
    write_reference,
)

INDEX = two_video_index()


class ScoringTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aic6_score_")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_case(self, *, predictions, reference=None, index=None):
        pred_path = write_predictions(self.tmp / "predictions.jsonl", predictions)
        prediction_set = scoring.load_predictions(pred_path, index or INDEX)
        ref = None
        if reference is not None:
            ref_path = write_reference(self.tmp / "reference.json", **reference)
            ref = scoring.load_reference(ref_path, index or INDEX)
        return scoring.score_joint(predictions=prediction_set, reference=ref, index=index or INDEX)


class JointMathTests(ScoringTestCase):
    def test_both_empty_scores_one_hundred(self):
        # video 0: 0 pred, 0 gt -> F = 1 ; video 1: 0 pred, 0 gt -> F = 1 ; mean 1 -> 100.0
        out = self.run_case(predictions={"0": [], "1": []},
                            reference={"coverage": "full", "videos": {"0": {}, "1": {}}})
        self.assertEqual(out["status"], "OK")
        self.assertEqual(out["score"], 100.0)

    def test_one_side_empty_scores_zero_for_that_video(self):
        # video 0: 0 pred, 1 gt -> F = 0 ; video 1: both empty -> F = 1 ; mean 0.5 -> 50.0
        out = self.run_case(predictions={"0": [], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_FULL}, "1": {}}})
        self.assertEqual(out["score"], 50.0)
        per_video = {row["video_id"]: row["f1"] for row in out["per_video"]}
        self.assertEqual(per_video, {"0": 0.0, "1": 1.0})

    def test_exact_match_scores_one_hundred(self):
        # video 0: 1 pred, 1 gt, IoU = 1 -> F = 2*1/(1+1) = 1 ; video 1 empty -> mean 1 -> 100.0
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_FULL}, "1": {}}})
        self.assertEqual(out["score"], 100.0)

    def test_partial_time_intersection_uses_the_formula(self):
        # video 0: pred frames {5,6}, gt frame {6} with IoU 1 -> s_iou = 1
        # F = 2*1/(2+1) = 0.666666... ; video 1 -> 1 ; mean = 0.833333... -> 83.333333
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL},
                                               {"frame": 6, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {6: BOX_FULL}, "1": {}}})
        self.assertAlmostEqual(out["score"], 83.333333, places=5)
        self.assertEqual(out["per_video"][0]["matched_frames"], 1)
        self.assertEqual(out["per_video"][0]["unmatched_predictions"], 1)

    def test_same_frame_but_zero_spatial_iou_scores_zero(self):
        # same frame 5, boxes y 0..405 and y 500..905 -> no overlap -> s_iou = 0 -> F = 0
        # mean with the empty video (F = 1) -> 0.5 -> 50.0
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_NO_OVERLAP}, "1": {}}})
        self.assertEqual(out["score"], 50.0)
        self.assertEqual(out["per_video"][0]["s_iou"], 0.0)

    def test_hand_computed_iou_of_one_third(self):
        # box A [0,0,100] -> h = 100*9/16 = 56.25 ; box B [0,28.125,100] -> same height shifted
        # by half.  inter = 100*28.125 = 2812.5 ; union = 5625+5625-2812.5 = 8437.5
        # IoU = 2812.5/8437.5 = 1/3 ; F = 2*(1/3)/(1+1) = 1/3
        # mean over the two videos = (1/3 + 1)/2 = 2/3 -> 66.666666...
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_SHIFTED_LOW}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_SHIFTED_HIGH}, "1": {}}})
        self.assertAlmostEqual(out["per_video"][0]["s_iou"], 1 / 3, places=9)
        self.assertAlmostEqual(out["score"], 66.666667, places=5)

    def test_duplicate_frame_is_counted_in_n_pred_and_lowers_the_score(self):
        # video 0: the same frame 5 twice -> N_pred = 2, only the first contributes IoU = 1
        # F = 2*1/(2+1) = 0.666666... ; mean with the empty video -> 0.833333 -> 83.333333
        single = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                               reference={"coverage": "full",
                                          "videos": {"0": {5: BOX_FULL}, "1": {}}})
        duplicated = self.run_case(
            predictions={"0": [{"frame": 5, "box": BOX_FULL}, {"frame": 5, "box": BOX_FULL}], "1": []},
            reference={"coverage": "full", "videos": {"0": {5: BOX_FULL}, "1": {}}})
        self.assertEqual(single["score"], 100.0)
        self.assertAlmostEqual(duplicated["score"], 83.333333, places=5)
        self.assertLess(duplicated["score"], single["score"])
        self.assertEqual(duplicated["per_video"][0]["n_pred"], 2)
        self.assertEqual(duplicated["per_video"][0]["duplicate_frames"], 1)

    def test_macro_mean_differs_from_frame_micro_pooling(self):
        # video 0: 1 pred, 1 gt, IoU 1 -> F = 1 ; video 1: 0 pred, 1 gt -> F = 0
        # macro = (1+0)/2 = 0.5 -> 50.0
        # frame-pooled (wrong) micro = 2*(1+0)/((1+0)+(1+1)) = 2/3 = 0.666667 -> 66.666667
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_FULL}, "1": {7: BOX_FULL}}})
        self.assertEqual(out["score"], 50.0)
        self.assertAlmostEqual(out["aggregate"]["frame_micro_f1"], 2 / 3, places=9)
        self.assertNotAlmostEqual(out["score"], out["aggregate"]["frame_micro_f1"] * 100, places=3)

    def test_decomposition_fields(self):
        # video 0: pred {5,6}, gt {5,7}, IoU(frame5) = 1, unmatched pred 1, missed gt 1
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL},
                                               {"frame": 6, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full",
                                       "videos": {"0": {5: BOX_FULL, 7: BOX_FULL}, "1": {}}})
        row = out["per_video"][0]
        self.assertEqual(row["matched_frames"], 1)
        self.assertEqual(row["unmatched_predictions"], 1)
        self.assertEqual(row["missed_ground_truth"], 1)
        self.assertAlmostEqual(row["time_precision"], 1 / 2, places=9)
        self.assertAlmostEqual(row["time_recall"], 1 / 2, places=9)
        self.assertAlmostEqual(row["time_f1"], 1 / 2, places=9)
        self.assertEqual(out["aggregate"]["matched_frame_iou"], 1.0)


class StrictValidationTests(ScoringTestCase):
    """Invalid input must never be cleaned and then scored."""

    def assert_invalid(self, raw_lines, *, expect_code=None):
        pred_path = write_raw_predictions(self.tmp / "raw.jsonl", raw_lines)
        prediction_set = scoring.load_predictions(pred_path, INDEX)
        ref_path = write_reference(self.tmp / "reference.json", coverage="full",
                                   videos={"0": {}, "1": {}})
        reference = scoring.load_reference(ref_path, INDEX)
        out = scoring.score_joint(predictions=prediction_set, reference=reference, index=INDEX)
        self.assertEqual(out["status"], "INVALID_INPUT")
        self.assertIsNone(out["score"])
        if expect_code:
            self.assertIn(expect_code, out["issue_codes"])
        return out

    def test_bool_frame_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":'
                             '[{"frame":true,"bboxes":[0,0,720]}]}',
                             '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="FRAME_TYPE")

    def test_nan_box_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":'
                             '[{"frame":5,"bboxes":[NaN,0,720]}]}',
                             '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="NON_FINITE")

    def test_out_of_bounds_box_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":'
                             '[{"frame":5,"bboxes":[1,0,720]}]}',
                             '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="BOX_OUT_OF_BOUNDS")

    def test_frame_equals_n_frames_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":'
                             '[{"frame":630,"bboxes":[0,0,720]}]}',
                             '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="FRAME_OUT_OF_RANGE")

    def test_missing_prediction_line_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="MISSING_VIDEO_ID")

    def test_invalid_json_line_is_invalid(self):
        self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":[]}',
                             '{"video_id":"1", broken'],
                            expect_code=None)

    def test_non_object_row_is_invalid(self):
        self.assert_invalid(['["not","an","object"]',
                             '{"video_id":"0","targetRatioWH":[16,9],"predictions":[]}',
                             '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'],
                            expect_code="ROW_SHAPE")

    def test_invalid_input_is_never_reported_as_zero_or_partial_score(self):
        out = self.assert_invalid(['{"video_id":"0","targetRatioWH":[16,9],"predictions":'
                                   '[{"frame":5,"bboxes":[0,0,720]},{"frame":5.5,"bboxes":[0,0,720]}]}',
                                   '{"video_id":"1","targetRatioWH":[16,9],"predictions":[]}'])
        self.assertNotEqual(out["score"], 0)
        self.assertIn("not removed", " ".join(out["reasons"]))


class ReferenceCoverageTests(ScoringTestCase):
    def test_no_reference_is_not_computable(self):
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []})
        self.assertEqual(out["status"], "NOT_COMPUTABLE")
        self.assertIsNone(out["score"])
        self.assertTrue(any("empty ground truth" in r for r in out["reasons"]))

    def test_incomplete_reference_is_not_computable(self):
        # reference covers only video 0 -> the missing video 1 is NOT treated as empty gt.
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "full", "videos": {"0": {5: BOX_FULL}}})
        self.assertEqual(out["status"], "NOT_COMPUTABLE")
        self.assertIsNone(out["score"])
        self.assertEqual(out["missing_video_ids"], ["1"])

    def test_reference_with_unknown_video_is_rejected(self):
        ref_path = write_reference(self.tmp / "reference.json", coverage="full",
                                   videos={"0": {}, "1": {}, "9": {}})
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(ref_path, INDEX)

    def test_duplicate_reference_frame_is_rejected(self):
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "videos": [{"video_id": "0", "frames": [{"frame": 5, "box_xyw": BOX_FULL},
                                                           {"frame": 5, "box_xyw": BOX_FULL}]},
                              {"video_id": "1", "frames": []}]}
        path = self.tmp / "dup_ref.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(path, INDEX)

    def test_sparse_reference_yields_sparse_diagnostic_only(self):
        # coverage=sparse -> no full-video joint score at all, and score stays null.
        out = self.run_case(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                            reference={"coverage": "sparse", "videos": {"0": {5: BOX_FULL}, "1": {}}})
        self.assertEqual(out["status"], "SPARSE_DIAGNOSTIC")
        self.assertIsNone(out["score"])
        self.assertEqual(out["sparse"]["videos_with_annotated_frames"], 1)
        self.assertEqual(out["sparse"]["annotated_frames"], 1)
        self.assertAlmostEqual(out["sparse"]["mean_matched_iou_on_annotated_frames"], 1.0, places=9)


class VendoredCrossCheckTests(ScoringTestCase):
    """Second opinion: the vendored implementation must agree on the same inputs."""

    @classmethod
    def setUpClass(cls):
        import sys

        vendor_parent = str(Path(__file__).resolve().parents[1])
        if vendor_parent not in sys.path:
            sys.path.insert(0, vendor_parent)
        sys.dont_write_bytecode = True
        from vendor.existing_internal_evaluator import internal_metric, schema

        cls.schema = schema
        cls.metric = internal_metric

    def test_vendored_agrees_on_hand_cases(self):
        cases = {
            "exact_match": ({"0": {5: BOX_FULL}}, {"0": [{"frame": 5, "box": BOX_FULL}], "1": []}),
            "partial_time": ({"0": {6: BOX_FULL}},
                             {"0": [{"frame": 5, "box": BOX_FULL}, {"frame": 6, "box": BOX_FULL}], "1": []}),
            "duplicate": ({"0": {5: BOX_FULL}},
                          {"0": [{"frame": 5, "box": BOX_FULL}, {"frame": 5, "box": BOX_FULL}], "1": []}),
            "iou_one_third": ({"0": {5: BOX_SHIFTED_HIGH}},
                              {"0": [{"frame": 5, "box": BOX_SHIFTED_LOW}], "1": []}),
        }
        for name, (gt, predictions) in cases.items():
            with self.subTest(case=name):
                out = self.run_case(predictions=predictions,
                                    reference={"coverage": "full",
                                               "videos": {**gt, "1": {}}})
                prediction_set = scoring.load_predictions(
                    write_predictions(self.tmp / f"p_{name}.jsonl", predictions), INDEX)
                reference = scoring.load_reference(
                    write_reference(self.tmp / f"r_{name}.json", coverage="full",
                                    videos={**gt, "1": {}}), INDEX)
                vendored = scoring.cross_check_with_vendored(
                    predictions=prediction_set, reference=reference, index=INDEX,
                    vendored_schema=self.schema, vendored_metric=self.metric)
                self.assertAlmostEqual(out["score"], vendored["vendored_score_percent"], places=4,
                                       msg=f"{name}: new={out['score']} vendored={vendored}")
                self.assertEqual(vendored["vendored_official_status"], "internal_diagnostic")


if __name__ == "__main__":
    unittest.main()
