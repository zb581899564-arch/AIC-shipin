import unittest
import numpy as np
from ranking_diagnostic import weighted_auc, matched_budget, paired_f1


class RankingDiagnosticTest(unittest.TestCase):
    def test_auc_ties_are_half(self):
        self.assertEqual(weighted_auc([1, 1], [0, 5], [5, 5]), .5)

    def test_auc_correct_and_reversed(self):
        self.assertEqual(weighted_auc([0, 1], [0, 5], [5, 5]), 1.)
        self.assertEqual(weighted_auc([1, 0], [0, 5], [5, 5]), 0.)

    def test_soft_counts_match_expanded_native(self):
        self.assertEqual(weighted_auc([0, 1], [1, 3], [4, 4]), .75)

    def test_single_class_undefined(self):
        self.assertIsNone(weighted_auc([0, 1], [0, 0], [2, 2]))

    def test_budget_copies_count_not_reference(self):
        self.assertEqual(matched_budget([.3, .8, .4], [4, 3, 2], 5).tolist(), [False, True, True])
        self.assertEqual(matched_budget([1, 1], [3, 3], 3).tolist(), [True, False])

    def test_paired_f1_averages_all_raters(self):
        self.assertAlmostEqual(paired_f1([True, False], [[True, False], [False, True]]), .5)


if __name__ == '__main__':
    unittest.main()
