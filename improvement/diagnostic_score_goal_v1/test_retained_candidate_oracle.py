"""Pure synthetic checks only; no historical metrics, media or model access."""
from fractions import Fraction as F
import unittest

from retained_candidate_oracle import common_subset_oracle, native_projection


class CommonSubsetOracleTests(unittest.TestCase):
    def test_common_output_cannot_choose_different_subset_per_rater(self):
        refs = [[[0, 1]]]*5 + [[[1, 2]]]*5
        result = common_subset_oracle([[[0, 1]], [[1, 2]]], refs)
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '2/3')
        self.assertEqual(result['enumerated_subsets'], 4)

    def test_overlap_counted_once_and_duplicate_masks_removed(self):
        refs = [[[0, 3]] for _ in range(10)]
        result = common_subset_oracle([[[0, 2]], [[1, 3]], [[0, 2]]], refs)
        self.assertEqual(result['deduplicated_candidate_masks'], 2)
        self.assertEqual(result['best']['selected_duration']['exact'], '3')
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '1')

    def test_exact_fractions_and_whole_reference_denominator(self):
        refs = [[['0', '1/3'], ['2', '3']] for _ in range(10)]
        result = common_subset_oracle([[['0', '1/3']]], refs)
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '2/5')
        self.assertEqual(result['all_candidate_union']['mean_rater_recall']['exact'], '1/4')

    def test_over_limit_is_feasible_lower_bound(self):
        candidates = [[[i, i+1]] for i in range(21)]
        result = common_subset_oracle(candidates, [[[0, 21]] for _ in range(10)])
        self.assertFalse(result['exact_optimum'])
        self.assertIsNone(result['enumerated_subsets'])
        self.assertIn('LOWER_BOUND_NOT_AN_UPPER_BOUND', result['method'])
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '1')

    def test_empty_pool_and_empty_rater_no_fabricated_perfect_score(self):
        result = common_subset_oracle([], [[] for _ in range(10)])
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '0')
        self.assertEqual(result['enumerated_subsets'], 1)

    def test_native_vfr_half_open_projection_not_duration_resampling(self):
        result = native_projection([['1/10', '7/10']], [F(0), F(1, 10), F(3, 5), F(7, 10)])
        self.assertEqual(result, dict(native_ordinal_ranges_half_open=[[1, 3]], native_selected_frames=2))

    def test_ten_original_raters_required(self):
        with self.assertRaises(ValueError):
            common_subset_oracle([[[0, 1]]], [[[0, 1]]]*9)

    def test_additions_cannot_remove_mandatory_baseline(self):
        refs = [[[1, 2]] for _ in range(10)]
        result = common_subset_oracle([[[1, 2]], [[3, 4]]], refs, mandatory_spans=[[0, 1]])
        self.assertEqual(result['best']['intervals_exact'], [['0', '2']])
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '2/3')
        self.assertFalse(result['null_choice_allowed'])
        self.assertTrue(result['mandatory_mask_never_removed'])

    def test_fully_covered_additions_do_not_expand_search(self):
        result = common_subset_oracle([[[0, 1]], [[0, 2]]], [[[0, 2]]]*10, mandatory_spans=[[0, 2]])
        self.assertEqual(result['deduplicated_candidate_masks'], 0)
        self.assertEqual(result['enumerated_subsets'], 1)
        self.assertEqual(result['candidates_already_fully_covered_by_mandatory'], 2)
        self.assertEqual(result['best']['mean_paired_duration_f1']['exact'], '1')

    def test_greedy_lower_bound_also_keeps_mandatory(self):
        result = common_subset_oracle([[[1, 2]], [[2, 3]]], [[[0, 3]]]*10,
                                      exact_limit=1, mandatory_spans=[[0, 1]])
        self.assertFalse(result['exact_optimum'])
        self.assertEqual(result['best']['intervals_exact'], [['0', '3']])


if __name__ == '__main__':
    unittest.main()
