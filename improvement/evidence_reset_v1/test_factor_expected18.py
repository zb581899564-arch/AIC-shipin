import itertools
import math
import random
import unittest
from factor_expected18 import select


def expected(s,actions,logs):
    probabilities=[]
    for w in logs:
        q=[math.exp(x-max(w))for x in w];z=sum(q);probabilities.append([x/z for x in q])
    v=0.
    for sequence in itertools.product(*[range(len(a))for a in actions]):
        truth=set().union(*[actions[i][j]for i,j in enumerate(sequence)])
        p=math.prod(probabilities[i][j]for i,j in enumerate(sequence));d=len(s)+len(truth)
        v+=p*(2*len(s&truth)/d if d else 1.)
    return v


class FactorizedF1(unittest.TestCase):
    def test_matches_exhaustive_program_and_output_search(self):
        rng=random.Random(18018)
        for _ in range(48):
            domains=[range(3),range(3,7)];actions=[[{i for i in domain if rng.random()<.5}for j in range(3)]for domain in domains]
            logs=[[rng.uniform(-6,0)for a in w]for w in actions];b={i for i in range(7)if rng.random()<.5}
            s,stats=select(actions,logs,b,7);self.assertEqual(len(s),len(b));union=set().union(*[set().union(*w)for w in actions]);fixed=b-union
            self.assertEqual(s-union,fixed)
            best=max(expected(fixed|set(c),actions,logs)for c in itertools.combinations(sorted(union),len(b)-len(fixed)))
            self.assertAlmostEqual(expected(s,actions,logs),best,places=12)
            if stats['mutable_count']:
                self.assertAlmostEqual(stats['model_expected_F1'],expected(s,actions,logs),places=12)

    def test_different_windows_overlap_is_invalid(self):
        with self.assertRaises(ValueError):select([[{0}],[{0}]],[[0.],[0.]],{0},3)

    def test_equal_scores_keep_old_frames(self):
        s,_=select([[{0,1,2,3}]],[[0.]],{2,3},4);self.assertEqual(s,{2,3})

    def test_empty_baseline_stays_successful_empty(self):
        s,_=select([[{1},set()]],[[0.,0.]],set(),3);self.assertEqual(s,set())


if __name__=='__main__':unittest.main()
