"""CPU-only zero-output width residual. No pretrained/backbone parameters here."""
import torch
from torch import nn
from width_common import HEAD_PARAMETERS,require


class WidthHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(4096,8),nn.GELU(),nn.Linear(8,1))
        nn.init.zeros_(self.network[-1].weight); nn.init.zeros_(self.network[-1].bias)
        require(sum(p.numel() for p in self.parameters())==HEAD_PARAMETERS,'Actual tiny-head parameter inventory')

    def forward(self,features):
        require(features.device.type=='cpu' and features.dtype==torch.float32 and features.ndim==2 and features.shape[1]==4096 and
                not features.requires_grad and bool(torch.isfinite(features).all()),'Frozen finite CPU float32 [N,4096] features required')
        return self.network(features).squeeze(-1)


def scale(raw): return torch.clamp(1+raw,min=.001,max=1.)


def quantized_width(raw):
    require(bool(torch.isfinite(raw).all()),'Nonfinite head output cannot become a crop')
    return torch.round(1000*scale(raw)).to(torch.int64).clamp(1,1000)
