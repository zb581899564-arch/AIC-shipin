import unittest
import torch
from mps_deepstack import deepstack_fp32,placeholder_mask
from types import SimpleNamespace
def original(x,mask,visual):
    x=x.clone();x[mask,:]=x[mask,:].clone()+visual.to(x.dtype);return x
class Equivalence(unittest.TestCase):
    def test_cpu_bf16_forward_and_backward(self):self.check(torch.bfloat16,'cpu')
    def test_cpu_fp16_forward_and_backward(self):self.check(torch.float16,'cpu')
    def test_mps_bf16_forward_and_backward(self):self.check(torch.bfloat16,'mps')
    def check(self,dtype,device):
        torch.manual_seed(33)
        values=torch.randn(2,19,8).to(dtype);mask=torch.zeros(2,19,dtype=torch.bool);mask[:,1::3]=True
        visual=torch.randn(int(mask.sum()),8).to(dtype)
        a=values.clone().requires_grad_();b=values.to(device).requires_grad_()
        expected=original(a,mask,visual);actual=deepstack_fp32(None,b,mask.to(device),visual.to(device))
        self.assertTrue(torch.equal(expected,actual.detach().cpu()))
        expected.float().square().mean().backward();actual.float().square().mean().backward()
        self.assertTrue(torch.equal(a.grad,b.grad.cpu()))
        self.assertTrue(bool(torch.isfinite(b.grad).all()))
class Placeholder(unittest.TestCase):
    def test_cpu_mask_and_strict_count(self):self.check('cpu')
    def test_mps_mask_and_strict_count(self):self.check('mps')
    def check(self,device):
        obj=SimpleNamespace(config=SimpleNamespace(image_token_id=8,video_token_id=9))
        ids=torch.ones(1,2488,dtype=torch.long);ids[:,100:1892]=9
        embeds=torch.zeros(1,2488,4096,dtype=torch.bfloat16)
        features=torch.zeros(1792,4096,dtype=torch.bfloat16)
        masks=placeholder_mask(obj,ids.to(device),embeds.to(device),video_features=features.to(device))
        for mask,token in zip(masks,(8,9)):
            expected=(ids==token).unsqueeze(-1).expand_as(embeds)
            self.assertTrue(mask.is_contiguous());self.assertTrue(torch.equal(mask.cpu(),expected))
            self.assertEqual(int(mask.sum().cpu()),int((ids==token).sum())*4096)
        with self.assertRaises(ValueError):placeholder_mask(obj,ids.to(device),embeds.to(device),video_features=features[:-1].to(device))
if __name__=='__main__':unittest.main()
