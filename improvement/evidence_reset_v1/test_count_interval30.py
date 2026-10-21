import itertools
import unittest
import numpy as np
from count_interval30_math import certify,range_program,source_utility


class Tests(unittest.TestCase):
    def test_certificate_matches_small_exhaustive_variable_P(self):
        rng=np.random.default_rng(30)
        for unused in range(30):
            lengths=rng.integers(0,5,size=(4,3)).tolist();source_positives=rng.integers(0,5,size=(4,3));gt=source_positives.sum(axis=0);tp=[]
            for row,positives in zip(lengths,source_positives):tp.append([rng.integers(0,np.minimum(n,positives)+1).tolist()for n in row])
            keep=[[0]*3 for row in lengths];baseline=[0]*4
            values=[source_utility(lengths,tp,gt,c)[0]for c in itertools.product(range(3),repeat=4)]
            out=certify(lengths,tp,gt,baseline,keep)
            self.assertAlmostEqual(out['witness_F1'],max(values),places=9)
            self.assertGreaterEqual(out['upper_bound']+1e-12,max(values));self.assertLessEqual(out['certified_gap'],1.01e-10)
            self.assertEqual(out['native_programs'],3**4)

    def test_empty_rater_and_all_empty_actions(self):
        out=certify([[0,2]],[[[0,0],[0,1]]],[0,1],[0],[[0,0]])
        self.assertEqual(out['witness_F1'],.5);self.assertEqual(out['witness_frames'],0)
        out=certify([[0],[0]],[[[0]],[[0]]],[0],[0,0],[[0],[0]])
        self.assertEqual(out['witness_F1'],1.);self.assertEqual(out['native_programs'],1)

    def test_additive_range_DP_and_unreachable_counts(self):
        c,value,k=range_program([[0,2],[0,3]],[[0,4],[0,5]],2,4,[[0,2],[0,3]])
        self.assertEqual(c,[0,1]);self.assertEqual(value,5);self.assertEqual(k,3)
        with self.assertRaises(ValueError):range_program([[0,2]],[[0,1]],1,1,[[0,1]])

    def test_large_cartesian_support_without_enumerating_it(self):
        lengths=[[0,1,2,3,4]]*12;tp=[[[n if w<6 else 0]for n in row]for w,row in enumerate(lengths)]
        out=certify(lengths,tp,[24],[2]*12,[[0,0,0,0,0]]*12)
        self.assertEqual(out['native_programs'],5**12);self.assertAlmostEqual(out['witness_F1'],1.)
        self.assertLess(out['count_interval_DP_nodes'],150)
        with self.assertRaises(AssertionError):certify([[2],[2]],[[[2]],[[2]]],[2],[0,0],[[0],[0]])


if __name__=='__main__':unittest.main()
