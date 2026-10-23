"""Targeted geometry, error-separation and optional real OpenCV CPU checks.

These synthetic image checks are engineering checks.  They are not a Linux
model smoke, a crop-IoU experiment, or evidence of official score improvement.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
import unittest

from .spatial import (SpatialConfig, SubjectTracker, crop_from_subjects,
                      parse_grounding, pixel_subjects, process_source, validate_box)


class GeometryTests(unittest.TestCase):
    def test_subject_extent_changes_scale_and_position(self):
        cfg = SpatialConfig()
        native = (1920, 1080)
        baseline = [0, 0, 1920]
        first, proof = crop_from_subjects([[100, 100, 500, 600]], *native, [16, 9], baseline, cfg)
        second, _ = crop_from_subjects([[1000, 250, 1750, 950]], *native, [16, 9], baseline, cfg)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first[2], second[2])
        self.assertNotEqual(first, baseline)
        self.assertEqual(proof["decision"], "SEMANTIC_SUBJECT_CONTAINMENT")
        validate_box(first, *native, [16, 9])
        validate_box(second, *native, [16, 9])

    def test_both_ratios_and_fractional_native_height(self):
        for width, height in [(300, 301), (853, 480), (360, 640), (1919, 1079)]:
            for ratio in ([16, 9], [9, 16]):
                subjects = [[width * .35, height * .4, width * .55, height * .6]]
                box, evidence = crop_from_subjects(subjects, width, height, ratio, None, SpatialConfig())
                validate_box(box, width, height, ratio)
                self.assertTrue(all(type(value) is int for value in box))
                if evidence["decision"] == "SEMANTIC_SUBJECT_CONTAINMENT":
                    self.assertLessEqual(box[0], subjects[0][0])
                    self.assertLessEqual(box[1], subjects[0][1])
                    self.assertGreaterEqual(box[0] + box[2], subjects[0][2])
                    self.assertGreaterEqual(box[1] + box[2] * ratio[1] / ratio[0], subjects[0][3])

    def test_whole_scene_preserves_float_baseline_exactly(self):
        baseline = [101.25, 5.5, 150.5]
        box, evidence = crop_from_subjects([], 500, 300, [16, 9], baseline, SpatialConfig())
        self.assertEqual(box, baseline)
        self.assertEqual(evidence["decision"], "WHOLE_SCENE_KEEP_EXACT_BASELINE")

    def test_whole_scene_added_frame_has_explicit_new_scene_geometry(self):
        box, evidence = crop_from_subjects([], 1920, 1080, [9, 16], None, SpatialConfig())
        validate_box(box, 1920, 1080, [9, 16])
        self.assertEqual(evidence["decision"], "MODEL_WHOLE_SCENE_NEW_FRAME_MAX_FIELD")
        self.assertEqual(box[2], 1080 * 9 // 16)

    def test_distributed_subjects_keep_accepted_box(self):
        baseline = [650, 2, 600]
        box, evidence = crop_from_subjects([[10, 10, 400, 1000], [1500, 10, 1900, 1000]],
                                           1920, 1080, [9, 16], baseline, SpatialConfig())
        self.assertEqual(box, baseline)
        self.assertEqual(evidence["decision"], "DISTRIBUTED_SUBJECTS_KEEP_EXACT_BASELINE")

    def test_bounds_rejected_instead_of_clipped(self):
        for subject in ([[0, 0, 1921, 1080]], [[5, 5, 5, 8]], [[0, 0, float("nan"), 2]]):
            with self.assertRaises(ValueError):
                crop_from_subjects(subject, 1920, 1080, [16, 9], [0, 0, 1920], SpatialConfig())
        with self.assertRaises(ValueError):
            validate_box([0, 0, 169], 300, 300, [9, 16])


class ParserTests(unittest.TestCase):
    def test_complete_grounding_and_normalization(self):
        parsed = parse_grounding('{"mode":"subject","boxes":[[50,100,750,900]]}')
        self.assertEqual(pixel_subjects(parsed, 200, 100), [[10., 10., 150., 90.]])
        self.assertEqual(parse_grounding('{"mode":"whole_scene","boxes":[]}')["mode"], "whole_scene")

    def test_normalized_boundary_cannot_round_outside_native_frame(self):
        parsed = parse_grounding('{"mode":"subject","boxes":[[0,0,1000,1000]]}')
        subjects = pixel_subjects(parsed, 2007, 1129)
        self.assertEqual(subjects, [[0., 0., 2007., 1129.]])
        box, _ = crop_from_subjects(subjects, 2007, 1129, [16, 9], None, SpatialConfig())
        validate_box(box, 2007, 1129, [16, 9])

    def test_failure_cannot_become_whole_scene(self):
        for raw in ["", "{}", '{"mode":"subject","boxes":[]}',
                    '{"mode":"whole_scene","boxes":[[1,2,3,4]]}',
                    '{"mode":"subject","boxes":[[true,2,3,4]]}',
                    '{"mode":"subject","boxes":[[0,0,1001,1000]]}',
                    '{"mode":"subject","boxes":[[0,0,3,NaN]]}',
                    '{"mode":"subject","boxes":[[0,0,3,4]],"confidence":1}',
                    'prefix {"mode":"whole_scene","boxes":[]}']:
            with self.subTest(raw=raw), self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_grounding(raw)


HAS_CV2 = importlib.util.find_spec("cv2") is not None


@unittest.skipUnless(HAS_CV2, "OpenCV absent in public audit environment; run on Linux")
class OpenCVTests(unittest.TestCase):
    def setUp(self):
        import cv2
        import numpy as np
        self.np, self.cv2 = np, cv2
        cv2.setNumThreads(1)
        rng = np.random.default_rng(31)
        self.image = np.zeros((160, 240, 3), dtype=np.uint8)
        self.image[40:120, 60:150] = rng.integers(40, 255, size=(80, 90, 3), dtype=np.uint8)

    def test_real_forward_backward_transport_measures_translation(self):
        tracker = SubjectTracker(SpatialConfig())
        tracker.reset(self.image, [[60, 40, 150, 120]])
        moved = self.cv2.warpAffine(self.image, self.np.array([[1., 0., 4.], [0., 1., 3.]]), (240, 160))
        boxes, evidence = tracker.transport(moved)
        self.assertIsNotNone(boxes)
        self.assertEqual(evidence["tracking_status"], "MEASURED_FORWARD_BACKWARD_FLOW")
        for actual, wanted in zip(boxes[0], [64, 43, 154, 123]):
            self.assertAlmostEqual(actual, wanted, delta=.75)

    def test_actual_foreground_segmentation_is_bounded(self):
        tracker = SubjectTracker(SpatialConfig())
        boxes, evidence = tracker.foreground_support(self.image, [[50, 30, 160, 130]])
        self.assertEqual(len(boxes), 1)
        self.assertEqual(evidence[0]["status"], "MEASURED_FOREGROUND_EXTENT")
        self.assertGreater(evidence[0]["support_pixels"], 0)
        self.assertTrue(45 <= boxes[0][0] <= 65)
        self.assertTrue(145 <= boxes[0][2] <= 165)

    def test_execution_failure_and_call_budget_never_make_default_answer(self):
        def broken(_image, _request):
            raise RuntimeError("synthetic model failure")
        observations = [{"frame": 0, "pts": "0", "rgb": self.image}]
        with self.assertRaisesRegex(RuntimeError, "synthetic model failure"):
            process_source(observations, [0], {0: [0, 0, 240]}, [16, 9], broken)
        def good(_image, _request):
            return {"raw_text": '{"mode":"whole_scene","boxes":[]}', "input_sha256": "a" * 64}
        observations = [{"frame": 0, "pts": "0", "rgb": self.image},
                        {"frame": 3, "pts": "1/10", "rgb": self.image}]
        with self.assertRaisesRegex(RuntimeError, "call budget reached"):
            process_source(observations, [0, 3], {}, [16, 9], good,
                           replace(SpatialConfig(), max_ground_calls=1))

    def test_compact_source_evidence_and_added_frame_semantics(self):
        calls = []
        def good(_image, request):
            calls.append(request)
            return {"raw_text": '{"mode":"whole_scene","boxes":[]}', "input_sha256": "b" * 64}
        observed = [{"frame": 0, "pts": "0", "rgb": self.image},
                    {"frame": 1, "pts": "1/30", "rgb": self.image}]
        result = process_source(observed, [0, 1], {0: [4, 5, 200]}, [16, 9], good)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["predictions"][0]["bboxes"], [4, 5, 200])
        self.assertEqual(len(result["groundings"]), 1)
        self.assertEqual(result["diagnostics"]["new_frames"], 1)
        self.assertEqual(result["diagnostics"]["selected_frames"], 2)
        self.assertNotIn("ground_anchor", result["spatial_evidence"][0])
        self.assertEqual(result["spatial_evidence"][1]["spatial_source"], "QWEN_OBSERVED_WHOLE_SCENE_MAX_FIELD")


if __name__ == "__main__":
    unittest.main()
