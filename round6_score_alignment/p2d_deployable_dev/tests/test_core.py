from __future__ import annotations

import math
import unittest

from p2d_core import box_is_legal, center_max_crop, validate_outputs, xywh_iou


def request(frame=10, video_id="v"):
    return {"video_id": video_id, "source_frame": frame, "source_width": 534,
            "source_height": 300, "target_ratio_wh": [9.0, 16.0]}


def output(frame=10, video_id="v", status="MODEL_OK", box=None):
    return {"video_id": video_id, "source_frame": frame, "status": status,
            "box_xyw": box or [183, 0, 168], "spatial_source": "REAL_QWEN_SAME_FRAME",
            "used_fallback": False}


class GeometryTests(unittest.TestCase):
    def test_center_max_legal_crop(self):
        # The implicit evaluator height is 168*16/9 = 298.666..., so the
        # frozen baseline rounds the centered y coordinate to 1.
        self.assertEqual(center_max_crop(534, 300, 9, 16), [183, 1, 168])
        self.assertTrue(box_is_legal([183, 1, 168], 534, 300, 9, 16))

    def test_width_169_is_illegal_for_300px_9x16(self):
        self.assertFalse(box_is_legal([0, 0, 169], 534, 300, 9, 16))

    def test_bounds_and_types_fail_closed(self):
        for box in ([367, 0, 168], [0, 2, 168], [0, 0, 0], [-1, 0, 168],
                    [0, 0, 168.0], [True, 0, 168], [0, 0], None):
            self.assertFalse(box_is_legal(box, 534, 300, 9, 16))

    def test_iou_identity_and_missing(self):
        self.assertAlmostEqual(xywh_iou([10, 0, 168], [10, 0, 168, 168 * 16 / 9]), 1.0)
        self.assertEqual(xywh_iou(None, [0, 0, 169, 300]), 0.0)


class AccountingTests(unittest.TestCase):
    def test_complete_real_inference(self):
        verdict = validate_outputs([request()], [output()])
        self.assertTrue(verdict["format_valid"])
        self.assertTrue(verdict["selection_complete"])
        self.assertTrue(verdict["deployable"])

    def test_failure_is_not_legal_empty(self):
        verdict = validate_outputs([request()], [output(status="PARSE_FAILURE")])
        self.assertFalse(verdict["selection_complete"])
        self.assertEqual(verdict["failure_count"], 1)

    def test_missing_and_extra_are_counted(self):
        verdict = validate_outputs([request()], [output(frame=11)])
        self.assertEqual(verdict["missing_count"], 1)
        self.assertEqual(verdict["extra_count"], 1)
        self.assertFalse(verdict["deployable"])

    def test_duplicate_output_fails(self):
        verdict = validate_outputs([request()], [output(), output()])
        self.assertEqual(verdict["duplicate_outputs"], 1)
        self.assertFalse(verdict["format_valid"])

    def test_wrong_video_id_fails(self):
        verdict = validate_outputs([request()], [output(video_id="other")])
        self.assertFalse(verdict["deployable"])

    def test_weak_or_fallback_source_fails(self):
        weak = output()
        weak["spatial_source"] = "WEAK_ROI_SAME_FRAME"
        self.assertFalse(validate_outputs([request()], [weak])["deployable"])
        fallback = output()
        fallback["used_fallback"] = True
        self.assertFalse(validate_outputs([request()], [fallback])["deployable"])

    def test_nan_like_invalid_payload_fails(self):
        bad = output()
        bad["box_xyw"] = [0, 0, math.nan]
        self.assertFalse(validate_outputs([request()], [bad])["format_valid"])


if __name__ == "__main__":
    unittest.main()
