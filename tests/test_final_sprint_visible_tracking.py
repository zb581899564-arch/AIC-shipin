"""Synthetic CPU checks for explicit visible-region subject tracking.

These are geometry/engineering checks, without official video or quality data.
"""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import unittest
from unittest.mock import patch

from improvement.final_sprint_v1.spatial import (
    SpatialConfig, SubjectTracker, _visible_polygon_boxes, crop_from_subjects,
    transport_polygon, validate_box,
)
from improvement.final_sprint_v1.visible_geometry import polygon_bounds, visible_polygon


class VisibleGeometryTests(unittest.TestCase):
    def test_partial_border_uses_only_real_intersection(self):
        polygon = [[-20., 10.], [40., 10.], [40., 50.], [-20., 50.]]
        original = [point[:] for point in polygon]
        visible = visible_polygon(polygon, 100, 80)
        self.assertEqual(polygon_bounds(visible), [0., 10., 40., 50.])
        self.assertEqual(polygon, original)
        box, _ = crop_from_subjects([polygon_bounds(visible)], 100, 80, [1, 1], None,
                                    SpatialConfig())
        validate_box(box, 100, 80, [1, 1])

    def test_rotated_partial_polygon_bounds_follow_clipped_edges(self):
        polygon = [[-20., 10.], [10., -20.], [20., -10.], [-10., 20.]]
        visible = visible_polygon(polygon, 100, 80)
        for actual, expected in zip(polygon_bounds(visible), [0., 0., 10., 10.]):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertTrue(all(0 <= x <= 100 and 0 <= y <= 80 for x, y in visible))

    def test_rotated_polygon_projection_overlap_is_not_visible_support(self):
        # Its bounding box overlaps [0,5]x[0,5], but x+y<=-5 everywhere.
        polygon = [[-10., -25.], [5., -10.], [-10., 5.], [-25., -10.]]
        self.assertEqual(visible_polygon(polygon, 100, 80), [])
        with self.assertRaisesRegex(ValueError, "no visible support"):
            _visible_polygon_boxes([polygon], 100, 80)

    def test_fully_exited_degenerate_and_boundary_only_have_no_area(self):
        for polygon in (
            [[110, 10], [130, 10], [130, 30], [110, 30]],
            [[-20, 10], [0, 10], [0, 30], [-20, 30]],
            [[-20, -20], [0, -20], [0, 0], [-20, 0]],
            [[10, 20], [20, 20], [30, 20], [40, 20]],
        ):
            with self.subTest(polygon=polygon):
                self.assertEqual(visible_polygon(polygon, 100, 80), [])

    def test_interior_extent_unchanged_in_either_winding(self):
        polygon = [[10., 20.], [30., 20.], [30., 50.], [10., 50.]]
        for ordered in (polygon, polygon[::-1]):
            self.assertEqual(visible_polygon(ordered, 100, 80), ordered)
            self.assertEqual(_visible_polygon_boxes([ordered], 100, 80),
                             [[10., 20., 30., 50.]])


HAS_CV2 = importlib.util.find_spec("cv2") is not None


@unittest.skipUnless(HAS_CV2, "OpenCV absent; run targeted CPU checks on Linux")
class VisibleTrackerTests(unittest.TestCase):
    def setUp(self):
        import cv2
        import numpy as np
        self.cv2, self.np = cv2, np
        self.image = np.zeros((80, 100, 3), dtype=np.uint8)
        self.tracker = SubjectTracker(SpatialConfig())
        self.original = [[10., 20.], [30., 20.], [30., 50.], [10., 50.]]
        self.tracker.reset(self.image, [[10, 20, 30, 50]])

    def measured_transport(self, affine, *, inlier_fraction=1., backward_error=0.):
        """Inject a measured transform while exercising original tracker guards."""
        np = self.np
        before = np.array([[[12 + i % 4 * 4, 24 + i // 4 * 8]] for i in range(8)],
                          dtype=np.float32)
        matrix = np.array(affine, dtype=np.float64)
        after = (before.reshape(-1, 2) @ matrix[:, :2].T + matrix[:, 2]).astype(np.float32)
        status = np.ones((8, 1), dtype=np.uint8)
        returned = before + np.array([backward_error, 0], dtype=np.float32)
        inliers = np.zeros((8, 1), dtype=np.uint8)
        inliers[:round(8 * inlier_fraction)] = 1
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.cv2, "goodFeaturesToTrack", return_value=before))
            stack.enter_context(patch.object(self.cv2, "calcOpticalFlowPyrLK", side_effect=[
                (after.reshape(-1, 1, 2), status, None), (returned, status, None)]))
            stack.enter_context(patch.object(self.cv2, "estimateAffinePartial2D",
                                            return_value=(matrix, inliers)))
            return self.tracker.transport(self.image)

    def test_partial_exit_retains_quad_and_reentry_restores_original_extent(self):
        left = [[1., 0., -15.], [0., 1., 0.]]
        boxes, witness = self.measured_transport(left)
        self.assertEqual(boxes, [[0., 20., 15., 50.]])
        expected_quad = transport_polygon(self.original, left, [100, 80], [100, 80])
        self.assertEqual(self.tracker.polygons, [expected_quad])
        proof = witness["subjects"][0]
        self.assertEqual(proof["subject_polygon_xy"], expected_quad)
        self.assertEqual(proof["visible_subject_xyxy"], boxes[0])
        self.assertEqual(proof["visibility_geometry"], "POSITIVE_AREA_POLYGON_IMAGE_INTERSECTION")
        boxes, _ = self.measured_transport([[1., 0., 15.], [0., 1., 0.]])
        self.assertEqual(boxes, [[10., 20., 30., 50.]])
        self.assertEqual(self.tracker.polygons, [self.original])

    def test_fully_exited_subject_regrounds_without_mutating_memory(self):
        boxes, witness = self.measured_transport([[1., 0., 100.], [0., 1., 0.]])
        self.assertIsNone(boxes)
        self.assertEqual(witness["reason"], "SUBJECT_HAS_NO_VISIBLE_AREA")
        self.assertEqual(self.tracker.polygons, [self.original])

    def test_rotated_false_intersection_and_degenerate_subject_reground(self):
        for polygon in (
            [[-10., -25.], [5., -10.], [-10., 5.], [-25., -10.]],
            [[10., 20.], [20., 20.], [30., 20.], [40., 20.]],
        ):
            with self.subTest(polygon=polygon):
                self.tracker.polygons = [polygon]
                boxes, witness = self.measured_transport([[1., 0., 0.], [0., 1., 0.]])
                self.assertIsNone(boxes)
                self.assertEqual(witness["reason"], "SUBJECT_HAS_NO_VISIBLE_AREA")

    def test_original_flow_inlier_and_scale_guards_still_reground(self):
        cases = (
            ([[1., 0., -15.], [0., 1., 0.]], {"backward_error": 2.}, "FLOW_CONSISTENCY_LOST"),
            ([[1., 0., -15.], [0., 1., 0.]], {"inlier_fraction": .5}, "UNTRUSTED_SUBJECT_TRANSFORM"),
            ([[2., 0., 0.], [0., 2., 0.]], {}, "UNTRUSTED_SUBJECT_TRANSFORM"),
        )
        for affine, options, reason in cases:
            with self.subTest(reason=reason):
                boxes, witness = self.measured_transport(affine, **options)
                self.assertIsNone(boxes)
                self.assertEqual(witness["reason"], reason)

    def test_real_cpu_flow_can_continue_partly_outside_image(self):
        rng = self.np.random.default_rng(31)
        image = self.np.zeros((160, 240, 3), dtype=self.np.uint8)
        image[40:120, :90] = rng.integers(40, 255, size=(80, 90, 3), dtype=self.np.uint8)
        tracker = SubjectTracker(SpatialConfig())
        tracker.reset(image, [[0, 40, 90, 120]])
        moved = self.cv2.warpAffine(image, self.np.array([[1., 0., -3.], [0., 1., 0.]]),
                                    (240, 160))
        boxes, witness = tracker.transport(moved)
        self.assertEqual(witness["tracking_status"], "MEASURED_FORWARD_BACKWARD_FLOW")
        self.assertEqual(boxes[0][0], 0.)
        self.assertLess(min(point[0] for point in tracker.polygons[0]), -2.)
        for actual, expected in zip(boxes[0][1:], [40., 87., 120.]):
            self.assertAlmostEqual(actual, expected, delta=.75)
        box, _ = crop_from_subjects(boxes, 240, 160, [16, 9], [0, 0, 240], SpatialConfig())
        validate_box(box, 240, 160, [16, 9])


if __name__ == "__main__":
    unittest.main()
