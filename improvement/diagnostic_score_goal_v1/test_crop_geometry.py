"""Pure synthetic geometry checks; no media/model or old experiment access."""
import copy
import unittest

from crop_geometry import (best_candidate, candidate_pool, crop_iou, largest_width,
                           legal, place_crop, reference_from_normalized, source_split)


class CropGeometryTests(unittest.TestCase):
    def test_original_baseline_preserved_first_without_mutation(self):
        base = [3, 4, 16]; original = base.copy()
        pool = candidate_pool(100, 80, base)
        self.assertEqual(pool[0], original)
        self.assertEqual(base, original)

    def test_all_grid_boxes_legal_for_extreme_dimensions(self):
        for width, height in [(1920, 1080), (1080, 1920), (13, 7), (1, 1), (1001, 3)]:
            base = place_crop(width, height, (.5, .5))
            self.assertTrue(all(legal(b, width, height) for b in candidate_pool(width, height, base)))

    def test_width_floor_and_fractional_height(self):
        self.assertEqual(largest_width(100, 7), 12)
        self.assertEqual(place_crop(100, 7, (1., 1.), 900), [90, 1, 10])
        self.assertEqual(place_crop(100, 7, (0., 0.), 700), [0, 0, 8])

    def test_round_ties_even_and_y_clamp_floor(self):
        self.assertEqual(place_crop(10, 10, (.5, .5), 500), [2, 4, 5])
        self.assertEqual(place_crop(20, 20, (.5, .5), 1000), [0, 4, 20])
        self.assertEqual(place_crop(20, 20, (1., 1.), 1000), [0, 8, 20])

    def test_final_triplet_dedup_after_clamp(self):
        pool = candidate_pool(1, 1, [0, 0, 1])
        self.assertEqual(pool, [[0, 0, 1]])

    def test_original_float_reference_unchanged(self):
        normalized = [.1, .2, .9, .65]; original = copy.deepcopy(normalized)
        ref = reference_from_normalized(normalized, 100, 100)
        self.assertEqual(normalized, original)
        self.assertEqual(ref, [10., 20., 80., 45.])

    def test_iou_hand_calculation(self):
        # Both boxes 16x9, overlap 8x9: 72/(144+144-72)=1/3.
        self.assertAlmostEqual(crop_iou([0, 0, 16], [8., 0., 16., 9.]), 1/3)
        self.assertEqual(crop_iou([0, 0, 16], [0., 0., 16., 9.]), 1.)

    def test_pool_has_no_reference_argument_and_is_reference_independent(self):
        before = candidate_pool(100, 100, [0, 0, 16])
        best_candidate(before, [0., 0., 16., 9.])
        best_candidate(before, [70., 70., 16., 9.])
        self.assertEqual(before, candidate_pool(100, 100, [0, 0, 16]))

    def test_oracle_cannot_lose_contained_baseline_and_tie_is_first(self):
        pool = [[0, 0, 16], [0, 0, 16], [16, 0, 16]]
        index, score, scores = best_candidate(pool, [0., 0., 16., 9.])
        self.assertEqual(index, 0)
        self.assertGreaterEqual(score, scores[0])

    def test_invalid_geometry_or_reference_rejected_without_repair(self):
        with self.assertRaises(ValueError): candidate_pool(100, 100, [-1, 0, 16])
        with self.assertRaises(ValueError): reference_from_normalized([-.1, 0., .9, 1.], 100, 100)
        with self.assertRaises(ValueError): reference_from_normalized([0., 0., 1., 1.], 100, 100)

    def test_source_hash_split_exact_stable_and_order_independent(self):
        rows = [dict(id='train:'+str(i), source_sha256=format(i, '064x')) for i in range(602)]
        split = source_split(rows)
        self.assertEqual(list(split.values()).count('train'), 482)
        self.assertEqual(list(split.values()).count('dev'), 120)
        self.assertEqual(split, source_split(list(reversed(rows))))

    def test_pool_never_exceeds_baseline_plus_36_grid_candidates(self):
        pool = candidate_pool(1000, 1000, [1, 2, 333])
        self.assertLessEqual(len(pool), 37)
        self.assertEqual(len(pool), len({tuple(box) for box in pool}))


if __name__ == '__main__':
    unittest.main()
