import itertools
import unittest
import numpy as np
from source_risk19 import action_gradient,expected_utility,normalize


class SourceRisk(unittest.TestCase):
    def fixture(self):
        actions=[[{0,1},set()],[{2},{3},set()]];raters=[{0,2},{1,3},set()]
        lengths=[list(map(len,w))for w in actions];tp=[[np.array([len(a&r)for r in raters])for a in w]for w in actions]
        logits=[np.array([-.2,-1.3]),np.array([-2.,-.7,-1.1])]
        return actions,raters,lengths,tp,logits,np.array(list(map(len,raters)))

    def test_exact_utility_matches_all_programs(self):
        actions,raters,c,tp,l,g=self.fixture();q=[normalize(np,v)for v in l];value,_=expected_utility(np,c,tp,q,g);oracle=0
        for sequence in itertools.product(*[range(len(w))for w in actions]):
            s=set().union(*[actions[i][j]for i,j in enumerate(sequence)]);p=np.prod([q[i][j]for i,j in enumerate(sequence)])
            u=np.mean([2*len(s&r)/(len(s)+len(r))if len(s)+len(r)else 1 for r in raters]);oracle+=p*u
        self.assertAlmostEqual(value,oracle,places=13)

    def test_logit_gradient_matches_independent_finite_difference(self):
        _,_,c,tp,l,g=self.fixture();q=[normalize(np,v)for v in l];_,_,gradient,_=action_gradient(np,c,tp,q,g)
        for i in range(len(l)):
            for j in range(len(l[i])):
                lo=[v.copy()for v in l];hi=[v.copy()for v in l];lo[i][j]-=1e-5;hi[i][j]+=1e-5
                a,_=expected_utility(np,c,tp,[normalize(np,v)for v in lo],g);b,_=expected_utility(np,c,tp,[normalize(np,v)for v in hi],g)
                self.assertAlmostEqual(float(gradient[i][j]),(b-a)/2e-5,places=10)

    def test_full_source_denominator_not_window_average(self):
        v,_=expected_utility(np,[[1],[3]],[[np.array([1])],[np.array([0])]],[[1.],[1.]],np.array([1]))
        self.assertAlmostEqual(v,.4)

    def test_actual_empty_truth_convention(self):
        v,s=expected_utility(np,[[0,1]],[[np.array([0]),np.array([0])]],[[.25,.75]],np.array([0]))
        self.assertEqual(v,.25);self.assertEqual(s['probability_source_empty'],.25)


if __name__=='__main__':unittest.main()
