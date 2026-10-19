import json
from fractions import Fraction
import unittest

import numpy as np

from marginal_addition_math import f1_delta, gain_distribution, preference_comparison


def mask(n, *ids):
    value = np.zeros(n, dtype=bool)
    value[list(ids)] = True
    return value


class MarginalF1Tests(unittest.TestCase):
    def test_exact_regular_formula_and_all_rater_macro(self):
        y = np.array([[1, 0], [1, 1], [0, 1], [1, 0], [0, 0]], dtype=bool)
        result = f1_delta(y, mask(5, 0, 1), mask(5, 2, 3))
        self.assertEqual(result['baseline_native_frames'], 2)
        self.assertEqual(result['augmented_native_frames'], 4)
        for row in result['per_rater']:
            b, c, r, t, s = 2, 2, row['truth_native_frames'], row['baseline_truth_native_frames'], row['candidate_truth_native_frames']
            exact = Fraction(2*(s*(b+r)-t*c), (b+r)*(b+c+r))
            self.assertEqual(row['f1_delta_exact'], dict(numerator=exact.numerator, denominator=exact.denominator))
            self.assertEqual(row['f1_delta'], float(exact))
        self.assertAlmostEqual(result['macro_delta'], result['augmented_macro_f1']-result['baseline_macro_f1'])
        json.dumps(result, allow_nan=False)

    def test_positive_gain_does_not_require_beating_anchor(self):
        y = np.array([[1], [1], [1], [1], [1], [1], [0], [0]], dtype=bool)
        result = preference_comparison(y, mask(8, 0, 1, 2, 3), mask(8, 4, 5, 6, 7), mask(8, 0, 1, 2, 3))
        self.assertGreater(result['marginal']['macro_delta'], 0)
        self.assertEqual(result['preference_distribution'], [0., 1., 0.])
        self.assertEqual(result['positive_gain_without_candidate_preference_raters'], 1)
        self.assertTrue(result['macro_positive_without_preference_majority'])
        self.assertEqual(result['marginal']['per_rater'][0]['positive_gain_density_threshold'], .4)

    def test_beating_poor_anchor_is_not_sufficient_for_positive_gain(self):
        y = np.array([[1], [1], [1], [0], [1], [0], [0], [0]], dtype=bool)
        result = preference_comparison(y, mask(8, 0, 1, 2, 3), mask(8, 4, 5, 6, 7), mask(8, 3))
        self.assertLess(result['marginal']['macro_delta'], 0)
        self.assertEqual(result['preference_distribution'], [1., 0., 0.])
        self.assertEqual(result['candidate_preference_without_positive_gain_raters'], 1)
        self.assertTrue(result['preference_majority_without_macro_positive'])

    def test_different_lengths_true_density_tie_can_have_positive_gain(self):
        y = np.array([[1], [1], [0], [0], [1], [0]], dtype=bool)
        result = preference_comparison(y, mask(6, 0, 1, 2, 3), mask(6, 4, 5), mask(6, 0, 1, 2, 3))
        self.assertEqual(result['preference_distribution'], [0., 0., 1.])
        self.assertEqual(result['positive_equal_density_tie_raters'], 1)
        self.assertEqual(result['zero_zero_tie_raters'], 0)
        self.assertGreater(result['marginal']['macro_delta'], 0)

    def test_rater_disagreement_and_magnitude_are_separate(self):
        y = np.array([[0, 1], [1, 0]], dtype=bool)
        result = preference_comparison(y, mask(2, 0), mask(2, 1), mask(2, 0))
        self.assertEqual(result['preference_distribution'], [.5, .5, 0.])
        self.assertFalse(result['rater_disagreement_is_TIE'])
        gain = result['marginal']['gain_distribution']
        self.assertEqual(gain['vote_fractions'], [.5, .5, 0.])
        self.assertEqual(gain['magnitude_probabilities'], [2/3, 1/3, 0.])
        self.assertEqual(result['marginal']['macro_delta_exact'], dict(numerator=1, denominator=6))
        self.assertTrue(result['macro_positive_without_preference_majority'])

    def test_empty_baseline_and_empty_truth_have_explicit_negative_gain(self):
        result = f1_delta(np.zeros((3, 1), bool), mask(3), mask(3, 1))
        row = result['per_rater'][0]
        self.assertEqual((row['baseline_f1'], row['augmented_f1'], row['f1_delta']), (1., 0., -1.))
        self.assertTrue(row['empty_prediction_and_truth_before'])
        self.assertIsNone(row['regular_integer_gain_numerator'])
        self.assertEqual(result['gain_distribution']['vote_fractions'], [0., 1., 0.])

    def test_empty_baseline_with_nonempty_truth_is_allowed(self):
        result = f1_delta(np.array([[0], [1], [1]], bool), mask(3), mask(3, 1))
        self.assertEqual(result['baseline_macro_f1'], 0.)
        self.assertEqual(result['macro_delta'], 2/3)

    def test_all_zero_summary_memberships_are_not_named_ordinary(self):
        result = preference_comparison(np.zeros((3, 4), bool), mask(3, 0), mask(3, 1, 2), mask(3, 0))
        self.assertEqual(result['marginal']['gain_distribution']['vote_fractions'], [0., 0., 1.])
        self.assertEqual(result['marginal']['gain_distribution']['magnitude_probabilities'], [0., 0., 1.])
        self.assertEqual(result['zero_zero_tie_raters'], 4)
        self.assertFalse(result['zero_is_ordinary'])

    def test_exact_gain_cancellation_is_zero(self):
        result = gain_distribution([Fraction(1, 3), Fraction(-1, 3), Fraction(0)])
        self.assertEqual(result['mean_gain_sign'], 'ZERO')
        self.assertEqual(result['mean_delta_exact'], dict(numerator=0, denominator=1))
        self.assertEqual(result['vote_fractions'], [1/3, 1/3, 1/3])
        self.assertEqual(result['magnitude_probabilities'], [.5, .5, 0.])

    def test_unknown_nonbool_and_missing_dimensions_rejected(self):
        for y in (np.array([[1, -1], [0, 1]]), np.array([[1., np.nan], [0., 1.]]),
                  np.array([[True, None], [False, True]], object), np.ones(2, bool),
                  np.empty((2, 0), bool), np.empty((0, 2), bool)):
            with self.subTest(y=y):
                with self.assertRaises(ValueError): f1_delta(y, mask(2, 0), mask(2, 1))
        for bad in ([1, 0], [True, None], np.array([True]), np.array([[True, False]])):
            with self.assertRaises(ValueError): f1_delta(np.zeros((2, 1), bool), bad, mask(2, 1))
            with self.assertRaises(ValueError): f1_delta(np.zeros((2, 1), bool), mask(2, 0), bad)

    def test_overlap_empty_candidate_and_invalid_anchor_rejected(self):
        y = np.zeros((3, 2), bool)
        with self.assertRaises(ValueError): f1_delta(y, mask(3, 0, 1), mask(3, 1, 2))
        with self.assertRaises(ValueError): f1_delta(y, mask(3, 0), mask(3))
        with self.assertRaises(ValueError): preference_comparison(y, mask(3, 0), mask(3, 1), mask(3))
        with self.assertRaises(ValueError): preference_comparison(y, mask(3, 0), mask(3, 1), mask(3, 2))

    def test_inputs_preserved_and_json_results_are_finite(self):
        y = np.array([[1, 0], [0, 1], [0, 0]], bool)
        b, c, a = mask(3, 0), mask(3, 1, 2), mask(3, 0)
        snapshots = [v.copy() for v in (y, b, c, a)]
        result = preference_comparison(y, b, c, a)
        json.dumps(result, allow_nan=False)
        for value, before in zip((y, b, c, a), snapshots): np.testing.assert_array_equal(value, before)

    def test_invalid_gain_values_rejected(self):
        for bad in ([], [np.nan], [np.inf], [None], [True], [1.1], [Fraction(-2)]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): gain_distribution(bad)


if __name__ == '__main__':
    unittest.main()
