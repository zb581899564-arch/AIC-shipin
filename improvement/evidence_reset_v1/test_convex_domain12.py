import importlib.util
from pathlib import Path
import unittest

import numpy as np
import torch

s=importlib.util.spec_from_file_location('domain12',Path(__file__).with_name('domain_run12.py'))
api=importlib.util.module_from_spec(s);s.loader.exec_module(api)


class ConvexTests(unittest.TestCase):
    def test_gradient_with_independent_torch_autograd(self):
        rng=np.random.default_rng(12);X=rng.normal(size=(36,9));y=rng.uniform(.05,.95,36)
        w,r=api.convex_fit(np,X,y)
        z=torch.tensor(w,dtype=torch.float64,requires_grad=True)
        loss=torch.nn.functional.binary_cross_entropy_with_logits(torch.tensor(X)@z,torch.tensor(y))+.5*r['lambda_value']*(z@z)
        loss.backward();self.assertLess(z.grad.abs().max().item(),1e-10)
        trace=r['training_only_trace'];self.assertTrue(all(b['objective']<=a['objective'] for a,b in zip(trace,trace[1:])))

    def test_swapping_pair_and_complementing_target_preserves_fit(self):
        X=np.array([[1.,0.],[0.,1.],[1.,1.],[-1.,1.]])
        y=np.array([.9,.1,.7,.2]);w,_=api.convex_fit(np,X,y);other,_=api.convex_fit(np,-X,1-y)
        self.assertTrue(np.allclose(w,other,atol=1e-10,rtol=0))

    def test_train_feature_scale_policy_is_invariant(self):
        rng=np.random.default_rng(18);X=rng.normal(size=(12,7));y=rng.uniform(.1,.9,12)
        w,_=api.convex_fit(np,X,y);scaled,_=api.convex_fit(np,3*X,y)
        self.assertTrue(np.allclose(X@w,3*X@scaled,atol=1e-9,rtol=0))

    def test_rank_deficient_and_hard_targets_remain_finite(self):
        X=np.array([[1.,1.,0.],[1.,1.,0.],[-1.,-1.,0.],[-1.,-1.,0.]])
        w,r=api.convex_fit(np,X,np.array([1.,1.,0.,0.]))
        self.assertTrue(np.isfinite(w).all());self.assertEqual(w[2],0.);self.assertEqual(r['span_dimension'],1)
        self.assertTrue(np.all(X@w*np.array([1,1,-1,-1])>0))

    def test_zero_signal_is_not_successful_fit(self):
        with self.assertRaises(ValueError):api.convex_fit(np,np.zeros((4,3)),np.array([0.,1.,0.,1.]))


if __name__=='__main__':unittest.main(verbosity=2)
