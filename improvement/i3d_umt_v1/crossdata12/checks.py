"""Only new native-cell and differentiable-readout risks, not old profile replay."""
import numpy as np
import torch
from common import ENGINEERING, ROOT, native_cells, rank_mask, write_new
from runtime import make_models, score_features
from train import temporal_logits


def main():
    b,s,g = native_cells(129)
    assert b[-1] == (128,129) and s[-1].tolist() == [128]*8 and len(g)==129
    assert not rank_mask([1,2,3],g,0).any()
    assert rank_mask([1,2,3],g,129).all()
    torch.manual_seed(7312)
    unused, model, _ = make_models(ENGINEERING)
    del unused
    model.eval()
    x = torch.randn(1,3,2048)
    logits = temporal_logits(model,x)
    expected = score_features(model,x,torch.ones(1,3,dtype=torch.bool))
    assert torch.equal(logits.detach().sigmoid(),expected)
    torch.nn.functional.binary_cross_entropy_with_logits(logits,torch.tensor([[.2,.4,.1]])).backward()
    gradients = [p.grad for n,p in model.named_parameters() if 'video_enc' in n]
    assert any(t is not None and torch.isfinite(t).all() and t.abs().sum()>0 for t in gradients)
    write_new(ROOT/'new_cpu_contracts.json',dict(status='PASS',checks=4,
              synthetic_only=True,old_profile_or_old_CPU_suite_rerun=False,
              cases=['native129_no_label_padding','successful_zero_and_all_selection',
                     'upstream_inference_equivalence','gradient_reaches_UMT_encoder']))


if __name__ == '__main__':
    main()
