"""Synthetic native geometry/reference tests; no file IO or real labels."""
import unittest

import crop_geometry_v31 as crop


class CropGeometryTests(unittest.TestCase):
    def test_nearest_legal_center_ties_floor_and_fractional_height_boundary(self):
        self.assertEqual(crop.place_crop(100, 100, 32, (51.5, 50.5)), [35, 41, 32])
        self.assertEqual(crop.place_crop(100, 19, 33, (1000, 1000)), [67, 0, 33])
        self.assertTrue(crop.legal([67, 0, 33], 100, 19))
        self.assertFalse(crop.legal([67, 1, 33], 100, 19))
        self.assertEqual(crop.largest_width(100, 19), 33)

    def test_exact_fixed_pool_order_and_observed_baseline_prepend(self):
        pool = crop.candidate_pool(1000, 1000)
        self.assertEqual(pool, [[0, 219, 1000], [100, 275, 800], [0, 275, 800],
                                [200, 275, 800], [100, 219, 800], [100, 331, 800]])
        baseline = [1, 1, 16]
        self.assertEqual(crop.candidate_pool(1000, 1000, baseline), [baseline]+pool)
        self.assertEqual(crop.candidate_pool(1000, 1000, pool[2]), [pool[2]]+pool[:2]+pool[3:])

    def test_pool_gt_independent_dedup_legal_and_small_source_not_padded(self):
        for width, height in ((1, 1), (9, 1), (31, 80), (1920, 1080), (4096, 2160), (81, 53)):
            pool = crop.candidate_pool(width, height)
            self.assertEqual(len({tuple(b) for b in pool}), len(pool))
            self.assertLessEqual(len(pool), 6)
            self.assertTrue(all(crop.legal(b, width, height) for b in pool))
        self.assertEqual(crop.candidate_pool(1, 1), [[0, 0, 1]])
        with self.assertRaises(TypeError): crop.candidate_pool(100, 100, reference=[0, 0, 100, 100])

    def test_iou_hand_calculation_preserves_original_float_reference(self):
        reference = [8.0, 0.0, 16.0, 9.0]
        saved = list(reference)
        self.assertAlmostEqual(crop.crop_iou([0, 0, 16], reference), 1/3)
        self.assertEqual(crop.crop_iou([8, 0, 16], reference), 1.)
        self.assertEqual(reference, saved)
        normalized = [.1, .2, .9, .8]
        expected = [.1*100, .2*100, (.9-.1)*100, (.8-.2)*100]
        self.assertEqual(crop.reference_from_normalized(normalized, 100, 100), expected)
        self.assertEqual(normalized, [.1, .2, .9, .8])

    def test_fixed_inclusive_deadband_and_swap_classes(self):
        for a, b, expected in ((.52, .5, 2), (.5, .52, 2), (.521, .5, 0), (.5, .521, 1), (.1, .1, 2)):
            self.assertEqual(crop.preference_label(a, b), expected)
            self.assertEqual(crop.preference_label(b, a), crop.swap_class(expected))
        self.assertEqual(crop.pair_target([0, 0, 16], [8, 0, 16], [0., 0., 16., 9.]), 0)
        self.assertEqual(crop.pair_target([0, 0, 16], [0, 0, 16], [0., 0., 16., 9.]), 2)

    def test_invalid_geometry_reference_and_labels_fail_without_repair(self):
        for dims in ((0, 10), (True, 10), (10.0, 10)):
            with self.assertRaises(ValueError): crop.candidate_pool(*dims)
        with self.assertRaises(ValueError): crop.candidate_pool(100, 100, [-1, 0, 16])
        with self.assertRaises(ValueError): crop.place_crop(100, 10, 100, (50, 5))
        with self.assertRaises(ValueError): crop.place_crop(100, 100, 10, (float('nan'), 5))
        with self.assertRaises(ValueError): crop.validate_reference([0, 0, 101, 1], 100, 100)
        with self.assertRaises(ValueError): crop.crop_iou([0, 0, 16], [0, 0, -1, 9])
        with self.assertRaises(ValueError): crop.preference_label(1.1, .5)
        with self.assertRaises(ValueError): crop.swap_class(True)


if __name__ == '__main__':
    unittest.main()
