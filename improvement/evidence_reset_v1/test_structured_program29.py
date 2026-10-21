import itertools
import unittest
import numpy as np
from structured_program29_math import enumerate_programs,structured_loss


class Tests(unittest.TestCase):
    def test_source_global_not_sum_local_utility(self):
        c,P,u=enumerate_programs([[0,2],[0,3]],[[[0,0],[2,0]],[[0,0],[1,3]]],[3,3])
        expected=[.0,2/3,.4,.75]
        self.assertTrue(np.allclose(u,expected));self.assertEqual(c.tolist(),[[0,0],[0,1],[1,0],[1,1]])
        self.assertEqual(P.tolist(),[0,3,2,5])

    def test_hinge_logit_gradient_on_all_programs(self):
        rng=np.random.default_rng(29);c=np.asarray(list(itertools.product(range(3),repeat=3)))
        for unused in range(20):
            u=rng.uniform(size=len(c));logits=rng.normal(size=(3,3));out=structured_loss(c,u,logits)
            for w,j in itertools.product(range(3),repeat=2):
                plus=logits.copy();minus=logits.copy();plus[w,j]+=1e-6;minus[w,j]-=1e-6
                derivative=(structured_loss(c,u,plus)['loss']-structured_loss(c,u,minus)['loss'])/2e-6
                self.assertAlmostEqual(derivative,out['gradient'][w][j],places=7)

    def test_native_equivalent_gold_variants_not_forced_to_one_text(self):
        c=np.asarray([[0],[1],[2]]);u=np.asarray([1.,1.,0.]);o=structured_loss(c,u,[[0.,2.,1.]])
        self.assertEqual(o['gold_index'],1);self.assertEqual(o['loss'],0.);self.assertEqual(o['gradient'],[[0.,0.,0.]])

    def test_budget_is_not_imposed_and_empty_is_success(self):
        c,P,u=enumerate_programs([[0,2]],[[[0],[0]]],[0]);self.assertEqual(u.tolist(),[1.,0.])
        o=structured_loss(c,u,[[1.,0.]]);self.assertEqual(o['prediction_utility'],1.)
        with self.assertRaises(ValueError):enumerate_programs([[0,1]]*3,[[[0],[1]]]*3,[3],limit=7)


if __name__=='__main__':unittest.main()
