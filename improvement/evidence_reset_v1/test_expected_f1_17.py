import itertools
import math
import random
import unittest
from expected_f1_17 import expected_select


class ExpectedF1(unittest.TestCase):
    def test_bruteforce_fixed_budget(self):
        rng=random.Random(1717)
        for _ in range(128):
            n=7;actions=[{i for i in range(n)if rng.random()<.4}for j in range(4)]
            baseline={i for i in range(n)if rng.random()<.5};logs=[rng.uniform(-20,0)for j in actions]
            selected,info=expected_select(actions,logs,baseline,n)
            self.assertEqual(len(selected),len(baseline));union=set().union(*actions);fixed=baseline-union;k=len(baseline)
            if not k:continue
            z=max(logs);q=[math.exp(x-z)for x in logs];norm=sum(q);q=[p/norm for p in q]
            def value(s):return sum(p*2*len(s&a)/(k+len(a))for p,a in zip(q,actions))
            best=max(value(fixed|set(c))for c in itertools.combinations(sorted(union),k-len(fixed)))
            self.assertAlmostEqual(value(selected),best,places=12)

    def test_underflow_does_not_erase_rare_action_ranking(self):
        selected,_=expected_select([{0},{1,2},set()],[0.,-1000.,1000.],{0,3},4)
        self.assertEqual(selected,{0,3})

    def test_equal_scores_retain_baseline(self):
        s,_=expected_select([{0,1,2,3}],[0.],{2,3},4);self.assertEqual(s,{2,3})

    def test_foreign_domain_rejected(self):
        with self.assertRaises(ValueError):expected_select([{9}],[0.],{0},3)


if __name__=='__main__':unittest.main()
