"""One synthetic check: zero-init clamp derivative and width legality, no data."""
import torch
from torch.nn import functional as F
from head import WidthHead,scale,quantized_width


def main():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20261016);model=WidthHead()
    x=torch.zeros((1,4096),dtype=torch.float32)
    assert float(model(x)[0])==0 and int(quantized_width(model(x))[0])==1000
    loss=F.smooth_l1_loss(scale(model(x)),torch.tensor([.5]),beta=.1)
    loss.backward()
    gradient=float(model.network[-1].bias.grad[0])
    assert gradient!=0 and torch.isfinite(model.network[-1].bias.grad).all()
    widths=quantized_width(torch.tensor([-100.,-1.,-.999,0.,.5,100.],dtype=torch.float32))
    assert bool(((widths>=1)&(widths<=1000)).all()) and int(widths[3])==1000
    print({'synthetic_zero_init_width':1000,'target_below_one_output_bias_gradient':gradient,'width_bounds':'1..1000','parameters':sum(p.numel() for p in model.parameters()),'data_or_backbone_calls':0})


if __name__=='__main__':main()
