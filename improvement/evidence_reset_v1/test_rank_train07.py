"""Small real-Torch checks for the new pairwise objective/checkpoint path."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import torch

s=importlib.util.spec_from_file_location('rank07',Path(__file__).with_name('rank_train07.py'))
api=importlib.util.module_from_spec(s);s.loader.exec_module(api)


class RankTests(unittest.TestCase):
    def test_preference_sign_swap_and_tie(self):
        a=torch.tensor(.3,requires_grad=True);b=torch.tensor(-.2,requires_grad=True)
        loss=api.pair_loss(torch,a,b,.8);loss.backward()
        self.assertLess(a.grad.item(),0);self.assertGreater(b.grad.item(),0)
        self.assertTrue(torch.allclose(loss,api.pair_loss(torch,b,a,.2)))
        x=torch.tensor(0.,requires_grad=True)
        api.pair_loss(torch,x,torch.tensor(0.),.5).backward()
        self.assertEqual(x.grad.item(),0.)

    def test_equal_source_weight_and_singleton(self):
        counts=[2]*24+[1]
        totals=[sum(api.pair_weight({'source_pair_count':n}) for _ in range(n)) for n in counts]
        self.assertTrue(all(abs(v-.98)<1e-12 for v in totals))
        self.assertAlmostEqual(sum(totals),49/2)

    def test_zero_head_then_actual_adapter_signal(self):
        torch.manual_seed(7)
        a=torch.nn.Parameter(torch.randn(2,4));b=torch.nn.Parameter(torch.zeros(4,2))
        head=torch.nn.Parameter(torch.zeros(4))
        x=torch.tensor([1.,2.,-1.,.5]);y=torch.tensor([-.5,1.,2.,-1.])
        def features(v):return v+2*b@(a@v)
        api.pair_loss(torch,head@features(x),head@features(y),.9).backward()
        self.assertGreater(head.grad.norm().item(),0)
        self.assertEqual(b.grad.norm().item(),0.)
        with torch.no_grad():head.add_(head.grad,alpha=-.001)
        for v in [a,b,head]:v.grad=None
        api.pair_loss(torch,head@features(x),head@features(y),.9).backward()
        self.assertGreater(b.grad.norm().item(),0.)
        self.assertEqual(a.grad.norm().item(),0.)

    def test_mutable_progress_preserves_odd_gradient_and_rng(self):
        with tempfile.TemporaryDirectory(prefix='aic_rank07_') as d:
            out=Path(d);value=dict(cursor=1,gradients={'lora_B':torch.tensor([.1,-.7])},
                head_gradient=torch.tensor([.3]),torch_rng=torch.get_rng_state())
            api.durable_progress(out,value,torch)
            adopted=torch.load(out/'latest_progress.pt',map_location='cpu',weights_only=True)
            self.assertEqual(adopted['cursor'],1)
            self.assertTrue(torch.equal(adopted['gradients']['lora_B'],value['gradients']['lora_B']))
            self.assertTrue(torch.equal(adopted['torch_rng'],value['torch_rng']))
            value.update(cursor=2,head_gradient=None)
            api.durable_progress(out,value,torch)
            self.assertEqual(torch.load(out/'latest_progress.pt',weights_only=True)['cursor'],2)
            self.assertFalse((out/'latest_progress.tmp.pt').exists())

    def test_fixed_normalization_and_head_save_reload(self):
        torch.manual_seed(8);x=torch.randn(4096)
        f=torch.nn.functional.layer_norm(x,(4096,),eps=1e-5)
        self.assertAlmostEqual(f.mean().item(),0.,places=6)
        head=torch.nn.Linear(4096,1,bias=False)
        state=api.cpu_tree(head.state_dict(),torch)
        actual=head(f).detach().clone()
        with tempfile.TemporaryDirectory(prefix='aic_rank07_head_') as d:
            p=Path(d)/'head.pt';torch.save(state,p)
            other=torch.nn.Linear(4096,1,bias=False)
            other.load_state_dict(torch.load(p,weights_only=True))
            self.assertTrue(torch.equal(actual,other(f).detach()))


if __name__=='__main__':unittest.main(verbosity=2)
