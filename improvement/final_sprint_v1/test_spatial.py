"""Targeted geometry, error-separation and optional real OpenCV CPU checks.

These synthetic image checks are engineering checks.  They are not a Linux
model smoke, a crop-IoU experiment, or evidence of official score improvement.
"""
from __future__ import annotations

from dataclasses import replace
import copy
import hashlib
import importlib.util
import json
import math
import unittest

from .spatial import (SpatialConfig, SubjectTracker, crop_from_subjects,
                      parse_grounding, pixel_subjects, process_source, semantic_extent_control,
                      transport_polygon, validate_box)


class GeometryTests(unittest.TestCase):
    def test_rotation_round_trip_does_not_accumulate_bounding_box_growth(self):
        original = [[70., 80.], [130., 80.], [130., 120.], [70., 120.]]
        polygon = original
        angle = math.radians(5)
        cosine, sine = math.cos(angle), math.sin(angle)
        affine = [[cosine, -sine, 100 * (1 - cosine + sine)],
                  [sine, cosine, 100 * (1 - cosine - sine)]]
        for _ in range(72):
            polygon = transport_polygon(polygon, affine, [200, 200], [200, 200])
        for expected, actual in zip(original, polygon):
            self.assertAlmostEqual(actual[0], expected[0], places=9)
            self.assertAlmostEqual(actual[1], expected[1], places=9)

    def test_polygon_transport_uses_actual_thumbnail_axes(self):
        polygon = [[20, 30], [60, 30], [60, 70], [20, 70]]
        transformed = transport_polygon(polygon, [[1, 0, 2], [0, 1, 3]],
                                        [600, 400], [300, 100])
        self.assertEqual(transformed, [[24., 42.], [64., 42.], [64., 82.], [24., 82.]])

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


class SemanticControlTests(unittest.TestCase):
    def fixture(self):
        source = {"video_id": "synthetic", "media": {"sha256": "d" * 64},
                  "width": 240, "height": 160, "targetRatioWH": [16, 9],
                  "n_frames": 2, "normalized_exact_pts": ["0", "1/30"]}
        raw = '{"mode":"subject","boxes":[[250,250,650,650]]}'
        raw_sha = hashlib.sha256(raw.encode()).hexdigest()
        anchor = {"frame": 0, "native_pts": "0", "pixel_sha256": "b" * 64,
                  "input_sha256": "a" * 64, "raw_text": raw, "raw_sha256": raw_sha,
                  "mode": "subject", "subjects_normalized": [[250, 250, 650, 650]]}
        affine = [[1., 0., 4.], [0., 1., 2.]]
        polygon = transport_polygon([[70., 45.], [110., 45.], [110., 80.], [70., 80.]],
                                    affine, [240, 160], [240, 160])
        rows = []
        for frame, measured in enumerate(([[70., 45., 110., 80.]], [[74., 47., 114., 82.]])):
            box, _ = crop_from_subjects(measured, 240, 160, [16, 9], [0, 0, 240], SpatialConfig())
            rows.append({"frame": frame, "native_pts": source["normalized_exact_pts"][frame],
                         "bboxes": box, "box_xyw": box, "pixel_sha256": ("b" if frame == 0 else "c") * 64,
                         "ground_anchor_frame": 0, "ground_anchor_raw_sha256": raw_sha,
                         "same_frame_grounding": frame == 0, "subjects_xyxy": measured,
                         "previous_observed_frame": 0, "previous_pixel_sha256": "b" * 64,
                         "tracking": {"tracking_status": "ANCHOR_DUE"} if frame == 0 else {
                             "tracking_status": "MEASURED_FORWARD_BACKWARD_FLOW", "subjects": [{
                                 "geometry": "PERSISTENT_GROUNDED_QUADRILATERAL",
                                 "affine_thumbnail": affine, "thumbnail_wh": [240, 160],
                                 "subject_polygon_xy": polygon}]}})
        proof = {"schema": "AIC_FINAL_SPATIAL_EVIDENCE_V1", "video_id": "synthetic",
                 "source_sha256": "d" * 64,
                 "frames": [{"frame": row["frame"], "bboxes": row["bboxes"]} for row in rows],
                 "observed_pixel_evidence": {"frame_evidence": rows, "groundings": [anchor]}}
        return source, proof, {0: [0, 0, 240], 1: [0, 0, 240]}

    def test_control_reuses_raw_extents_and_exact_measured_motion_without_calls(self):
        source, proof, baseline = self.fixture()
        result = semantic_extent_control(source, proof, baseline)
        self.assertEqual(result["spatial_evidence"][0]["visible_semantic_extents"], [[60., 40., 156., 104.]])
        self.assertEqual(result["spatial_evidence"][1]["visible_semantic_extents"], [[64., 42., 160., 106.]])
        self.assertEqual(result["diagnostics"]["new_neural_calls"], 0)
        self.assertFalse(result["diagnostics"]["new_independent_tracking"])
        self.assertEqual([p["frame"] for p in result["predictions"]], [0, 1])
        self.assertEqual(result["diagnostics"]["changed_parent_boxes"], 2)
        for row in result["predictions"]:
            validate_box(row["bboxes"], 240, 160, [16, 9])

    def test_changed_affine_anchor_clock_or_membership_is_rejected(self):
        source, proof, baseline = self.fixture()
        corruptions = [
            lambda p: p.update(source_sha256="e" * 64),
            lambda p: p["observed_pixel_evidence"]["frame_evidence"][1].update(native_pts="1/29"),
            lambda p: p["observed_pixel_evidence"]["frame_evidence"][1].update(previous_pixel_sha256="f" * 64),
            lambda p: p["observed_pixel_evidence"]["frame_evidence"][1]["tracking"]["subjects"][0]["affine_thumbnail"][0].__setitem__(2, 5.),
            lambda p: p["observed_pixel_evidence"]["groundings"][0].update(subjects_normalized=[[250, 250, 600, 600]]),
            lambda p: p["frames"].pop(),
        ]
        for corrupt in corruptions:
            changed = copy.deepcopy(proof)
            corrupt(changed)
            with self.assertRaises(ValueError):
                semantic_extent_control(source, changed, baseline)

    def test_legal_empty_source_control_has_no_synthetic_observations(self):
        source, proof, _ = self.fixture()
        proof["frames"] = []
        proof["observed_pixel_evidence"] = {"frame_evidence": [], "groundings": []}
        result = semantic_extent_control(source, proof, {})
        self.assertEqual(result["predictions"], [])
        self.assertEqual(result["diagnostics"]["new_neural_calls"], 0)

    def test_explicit_whole_scene_control_keeps_each_exact_baseline(self):
        source, proof, baseline = self.fixture()
        raw = '{"mode":"whole_scene","boxes":[]}'
        raw_sha = hashlib.sha256(raw.encode()).hexdigest()
        detail = proof["observed_pixel_evidence"]
        detail["groundings"][0].update(raw_text=raw, raw_sha256=raw_sha,
                                       mode="whole_scene", subjects_normalized=[])
        for row in detail["frame_evidence"]:
            row.update(subjects_xyxy=[], ground_anchor_raw_sha256=raw_sha)
        detail["frame_evidence"][1]["tracking"] = {"tracking_status": "WHOLE_SCENE_CONTINUATION"}
        result = semantic_extent_control(source, proof, baseline)
        self.assertEqual(result["predictions"], [{"frame": frame, "bboxes": box} for frame, box in baseline.items()])


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
