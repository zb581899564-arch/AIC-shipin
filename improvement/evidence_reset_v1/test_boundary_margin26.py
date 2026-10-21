import unittest
import numpy as np
from boundary_margin26_math import F1,diagnose


class Tests(unittest.TestCase):
    def test_complete_source_denominator_and_all_reviewers(self):
        actions=[[[0,1],[2]],[[3],[4,5]]];lengths=[[2,1],[1,2]];tp=[[[2,0],[0,1]],[[1,0],[0,2]]]
        r=diagnose(actions,lengths,tp,[[0.,-1.],[0.,-1.]],[[0.,-.5],[0.,-1.4]],[3,3])
        self.assertAlmostEqual(r['initial_MAP_F1'],.5)
        self.assertAlmostEqual(r['rows'][0]['F1_if_one_swap'],.4)
        self.assertAlmostEqual(r['rows'][1]['F1_if_one_swap'],4/7)
        self.assertLess(r['mean_utility_weighted_margin_alignment'],0.)
        self.assertEqual(F1([0,0],0,[0,1]),.5)

    def test_native_duplicate_texts_do_not_double_count_swaps(self):
        r=diagnose([[[0],[1],[1]]],[[1,1,1]],[[[1],[0],[0]]],[[0.,-2.,-3.]],[[0.,-1.,-.5]],[1])
        self.assertEqual(r['alternative_swaps'],1);self.assertEqual(r['unique_native_groups'],2)
        self.assertEqual(r['rows'][0]['alternative_suffixes'],[1,2]);self.assertEqual(r['rows'][0]['delta_margin'],1.5)
        self.assertLess(r['mean_utility_weighted_margin_alignment'],0.)


if __name__=='__main__':unittest.main()
