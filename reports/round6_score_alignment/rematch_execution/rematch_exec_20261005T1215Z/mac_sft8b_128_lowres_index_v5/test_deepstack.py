import unittest
import torch
from mps_deepstack import deepstack_fp32
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
if __name__=='__main__':unittest.main()
