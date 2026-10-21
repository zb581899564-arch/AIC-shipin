import itertools
import math
import unittest
import numpy as np
from budget_program25_math import best_program,conditional,project_budget


class Checks(unittest.TestCase):
    def test_conditional_partition_marginal_and_gradient_bruteforce(self):
        rng=np.random.default_rng(25)
        for _ in range(24):
            c=[[0,1,2],[0,2],[0,1,3]];l=[rng.normal(size=len(v)).tolist()for v in c];k=3
            programs=[a for a in itertools.product(*[range(len(v))for v in c])if sum(v[j]for v,j in zip(c,a))==k]
            scores=np.array([sum(v[j]for v,j in zip(l,a))for a in programs]);weights=np.exp(scores-scores.max());weights/=weights.sum()
            target=list(programs[0]);out=conditional(c,l,k,target)
            self.assertAlmostEqual(out['log_partition'],float(scores.max()+np.log(np.exp(scores-scores.max()).sum())),places=12)
            for w in range(len(c)):
                for j in range(len(c[w])):
                    expected=sum(p for p,a in zip(weights,programs)if a[w]==j)
                    self.assertAlmostEqual(out['marginals'][w][j],float(expected),places=12)
                    hi=[v.copy()for v in l];lo=[v.copy()for v in l];hi[w][j]+=1e-5;lo[w][j]-=1e-5
                    derivative=(conditional(c,hi,k,target)['NLL']-conditional(c,lo,k,target)['NLL'])/2e-5
                    self.assertAlmostEqual(derivative,out['gradient'][w][j],places=8)

    def test_map_ties_projection_and_successful_empty(self):
        self.assertEqual(project_budget([[0,2],[0,4]],3)[0],2)
        c=[[0,2],[0,2]];scores=[[0,0],[0,0]]
        self.assertEqual(best_program(c,scores,2,[[0,1],[0,2]])[0],[0,1])
        self.assertEqual(best_program(c,scores,2)[0],[1,0]) # reverse-window lexicographic slots
        self.assertEqual(best_program(c,scores,0)[0],[0,0])
        with self.assertRaises(ValueError):best_program(c,scores,1)

    def test_extreme_logp_and_single_feasible_target(self):
        out=conditional([[0,2],[0,3]],[[-1e6,0.],[-1e6,0.]],2,[1,0])
        self.assertEqual(out['NLL'],0.);self.assertEqual(out['gradient_L1'],0.)
        out=conditional([[0,1],[0,1]],[[-1e6,0.],[-1e6,0.]],1,[1,0])
        self.assertAlmostEqual(out['NLL'],math.log(2),places=8)

    def test_oracle_is_all_reviewer_source_F1_at_one_count(self):
        c=[[0,2],[0,2]];gt=np.array([2,5]);tp=[[[0,0],[2,0]],[[0,0],[0,2]]]
        gains=[[float(np.mean(2*np.array(v)/(2+gt)))for v in window]for window in tp]
        a,score,_=best_program(c,gains,2)
        self.assertEqual(a,[1,0]);self.assertAlmostEqual(score,.5)


if __name__=='__main__':unittest.main()
