"""Focused CPU regressions; no media, model, or project-wide test execution."""

import math
import unittest

import numpy as np

from geometry import (
    box_for_width,
    conditioned_target,
    human_width_target,
    iou,
    rect,
    risk_summary,
)


class GeometryTests(unittest.TestCase):
    def test_maximum_width_and_non_16_9_sources(self):
        self.assertEqual(box_for_width(1920, 1080, (0.99, 0.01), 1000), [0, 0, 1920])
        self.assertEqual(box_for_width(640, 200, (0.5, 0.5), 1000), [142, 0, 355])
        self.assertEqual(box_for_width(1000, 1000, (1, 1), 1000), [0, 437, 1000])
        self.assertEqual(box_for_width(1, 1, (0.5, 0.5), 1), [0, 0, 1])

    def test_edge_center_clamps_before_rounding(self):
        self.assertEqual(box_for_width(1000, 700, (1, 0), 500), [500, 0, 500])
        self.assertEqual(box_for_width(1000, 700, (0, 1), 500), [0, 418, 500])
        self.assertEqual(rect([0, 418, 500]), [0, 418, 500, 281.25])

    def test_edge_center_makes_human_width_suboptimal(self):
        reference = [650.0, 400.0, 300.0, 168.75]
        normalized = [0.65, 0.4, 0.95, 0.56875]
        human = human_width_target(1000, 1000, normalized)
        human_box = box_for_width(1000, 1000, (0.95, 0.5), human)
        target, best_box, best_score = conditioned_target(
            1000, 1000, (0.95, 0.5), reference
        )
        self.assertEqual(human, 300)
        self.assertNotEqual(target, human)
        self.assertGreater(best_score, iou(human_box, reference))
        self.assertEqual(best_box, box_for_width(1000, 1000, (0.95, 0.5), target))
        self.assertEqual(reference, [650.0, 400.0, 300.0, 168.75])

    def test_conditioned_target_dominates_all_finite_widths(self):
        cases = [
            (1920, 1080, (0.5, 0.5), [0.2, 0.1, 0.7, 0.8]),
            (640, 200, (0.99, 0.01), [0.4, 0.1, 0.9, 0.9]),
            (100, 400, (0, 1), [0.1, 0.2, 0.8, 0.7]),
        ]
        for W, H, center, normalized in cases:
            with self.subTest(W=W, H=H, center=center):
                x1, y1, x2, y2 = normalized
                reference = [x1 * W, y1 * H, (x2 - x1) * W, (y2 - y1) * H]
                relative, best_box, best_score = conditioned_target(W, H, center, reference)
                human = human_width_target(W, H, normalized)
                self.assertGreaterEqual(best_score, iou(box_for_width(W, H, center, human), reference))
                candidates = [
                    (iou(box_for_width(W, H, center, r), reference),
                     box_for_width(W, H, center, r)[2], r)
                    for r in range(1, 1001)
                ]
                expected = max(candidates)
                self.assertEqual((best_score, best_box[2], relative), expected)

    def test_exact_tie_prefers_larger_width_then_relative(self):
        relative, box, score = conditioned_target(1, 1, (0, 0), [0, 0, 1, 1])
        self.assertEqual((relative, box, score), (1000, [0, 0, 1], 0.5625))
        relative, box, score = conditioned_target(100, 100, (0, 0), [99, 99, 1, 1])
        self.assertEqual((relative, box, score), (1000, [0, 0, 100], 0.0))

    def test_human_width_uses_maximum_legal_integer_width(self):
        original = np.array([0.1, 0.2, 0.6, 0.7])
        before = original.copy()
        self.assertEqual(human_width_target(640, 200, original), round(320 / 355 * 1000))
        np.testing.assert_array_equal(original, before)
        self.assertEqual(human_width_target(640, 200, [0, 0, 1, 1]), 1000)
        self.assertEqual(human_width_target(640, 200, [0, 0, 0.000001, 1]), 1)

    def test_iou_identity_and_disjoint(self):
        self.assertEqual(iou([2, 3, 16], [2, 3, 16, 9]), 1.0)
        self.assertEqual(iou([0, 0, 16], [100, 100, 16, 9]), 0.0)

    def test_invalid_frame_center_relative_and_boxes(self):
        for bad in [0, -1, 1.5, True, math.nan, math.inf, "640"]:
            with self.subTest(frame=bad), self.assertRaises(ValueError):
                box_for_width(bad, 200, [0.5, 0.5], 1000)
            with self.subTest(height=bad), self.assertRaises(ValueError):
                human_width_target(640, bad, [0, 0, 1, 1])
        for bad in [[0.5], [[0.5, 0.5]], [0, 0, 0], [math.nan, 0], [-0.1, 0],
                    [0, 1.1], [True, 0], ["0", 0]]:
            with self.subTest(center=bad), self.assertRaises(ValueError):
                box_for_width(640, 200, bad, 1000)
        for bad in [0, 1001, -1, 2.5, 1.0, True, math.nan]:
            with self.subTest(relative=bad), self.assertRaises(ValueError):
                box_for_width(640, 200, [0.5, 0.5], bad)
        for bad in [[0, 0], [0, 0, 1, 2], [[0, 0, 1]], [-1, 0, 1],
                    [0, 0, 0], [0, 0, math.nan], [0, 0, True], [0.0, 0, 1]]:
            with self.subTest(box=bad), self.assertRaises(ValueError):
                rect(bad)

    def test_invalid_reference_is_rejected_explicitly(self):
        for bad in [[0, 0, 1], [[0, 0, 1, 1]], [0, 0, 0, 1], [0, 0, 1, -1],
                    [-1, 0, 1, 1], [0, 0, math.nan, 1], [0, 0, 1, math.inf],
                    [0, 0, True, 1]]:
            with self.subTest(reference=bad), self.assertRaises(ValueError):
                iou([0, 0, 1], bad)
        with self.assertRaises(ValueError):
            conditioned_target(10, 10, [0.5, 0.5], [0, 0, 11, 1])
        for bad in [[0, 0, 1], [0, 0, 1.1, 1], [-0.1, 0, 1, 1], [0.5, 0, 0.4, 1],
                    [0, 0, 1, 0], [0, math.nan, 1, 1]]:
            with self.subTest(normalized=bad), self.assertRaises(ValueError):
                human_width_target(640, 200, bad)


class RiskTests(unittest.TestCase):
    def test_unsigned_subtraction_is_signed(self):
        result = risk_summary(np.array([1, 0], dtype=np.uint8),
                              np.array([0, 1], dtype=np.uint8), [100, 1000])
        self.assertEqual(result["mean_delta"], 0.0)
        self.assertEqual(result["worst_decile_mean_delta"], -1.0)
        self.assertEqual(result["loss_over_025_fraction"], 0.5)
        self.assertFalse(result["passed"])

    def test_worst_decile_uses_ceiling_and_reports_human_bins(self):
        candidate = np.array([0.4, 0.45] + [0.6] * 9)
        result = risk_summary([0.5] * 11, candidate, [500] * 11,
                              ["narrow"] * 2 + ["wide"] * 9)
        self.assertAlmostEqual(result["worst_decile_mean_delta"], -0.075)
        self.assertAlmostEqual(result["median_delta"], 0.1)
        self.assertAlmostEqual(result["positive_fraction"], 9 / 11)
        self.assertEqual(result["n"], 11)
        self.assertEqual(result["by_human_bin"]["narrow"]["n"], 2)
        self.assertTrue(result["passed"])

    def test_all_four_risk_gates_are_required(self):
        equal = risk_summary([0.5], [0.5], [500])
        self.assertFalse(equal["gates"]["mean_positive"])
        self.assertFalse(equal["passed"])
        # Positive average alone must not hide a negative median.
        median_loss = risk_summary([0.5] * 3, [0.49, 0.49, 0.9], [500] * 3)
        self.assertGreater(median_loss["mean_delta"], 0)
        self.assertFalse(median_loss["gates"]["median_nonnegative"])
        tail_loss = risk_summary([0.5] * 20, [0.19] + [0.6] * 19, [500] * 20)
        self.assertFalse(tail_loss["gates"]["worst_decile_at_least_minus_010"])
        self.assertTrue(tail_loss["gates"]["severe_loss_at_most_005"])
        severe_loss = risk_summary([0.5] * 20, [0.2] * 2 + [0.6] * 18, [500] * 20)
        self.assertFalse(severe_loss["gates"]["severe_loss_at_most_005"])

    def test_invalid_risk_inputs_are_rejected(self):
        cases = [
            ([], [], []), ([0.5], [0.5, 0.6], [500]),
            ([[0.5]], [0.5], [500]), ([math.nan], [0.5], [500]),
            ([0.5], [math.inf], [500]), ([-0.1], [0.5], [500]),
            ([0.5], [1.1], [500]), ([0.5], [0.5], [0]),
            ([0.5], [0.5], [1001]), ([0.5], [0.5], [500.5]),
            ([0.5], [0.5], [math.nan]), ([True], [0.5], [500]),
            ([0.5], [0.5], [[500]]),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                risk_summary(*args)
        for labels in [[math.nan], [""], [True], [], [[1]]]:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                risk_summary([0.5], [0.5], [500], labels)


if __name__ == "__main__":
    unittest.main()
