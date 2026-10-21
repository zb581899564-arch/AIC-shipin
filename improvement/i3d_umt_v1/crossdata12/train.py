"""One fixed final UMT fit; full-source training only on registered SumMe sources."""
import time
import numpy as np
import torch
import torch.nn.functional as F

from common import ENGINEERING, ROOT, checked, native_cells, read, reference, write_new
from runtime import make_models, score_features


def temporal_logits(model, features):
    """Upstream test output detaches; retain the identical pre-sigmoid training path."""
    mask = torch.ones(features.shape[:2], dtype=torch.long, device=features.device)
    encoded = model.video_enc(features, mask=mask)
    query = model.query_gen(encoded, None)
    decoded = model.query_dec(query, encoded)
    assert len(decoded) == 1 and len(model.pred_head) == 1
    return model.pred_head[0].saliency_pred(decoded[0]).squeeze(-1)


def load_features(row, device='cuda'):
    a = read(ROOT / 'features' / row['sid'] / 'acceptance.json')
    x = torch.from_numpy(np.load(checked(a['features']), allow_pickle=False)).to(device)
    return F.normalize(x, p=2, dim=-1)[None]


def main():
    protocol = read(ROOT / 'protocol.json')
    torch.manual_seed(protocol['seed'])
    np.random.seed(protocol['seed'])
    sources = read(ROOT / 'registration.json')['sources']
    rows = sorted([s for s in sources if s['role']=='train'],key=lambda r:r['sid'])
    assert len(rows) == 20
    backbone, model, cfg = make_models(ENGINEERING)
    del backbone
    model.cuda().train()
    assert sum(p.numel() for p in model.parameters()) == 6209025
    tensors = []
    for row in rows:
        acc = read(ROOT/'inputs'/row['sid']/'acceptance.json')
        x = load_features(row)
        y = torch.from_numpy(np.load(ROOT/'inputs'/row['sid']/'target.npy')).cuda()[None]
        bounds,_,_ = native_cells(acc['native_frames'])
        weights = x.new_tensor([b-a for a,b in bounds])[None]
        weights /= weights.sum()
        assert y.shape == x.shape[:2] and torch.isfinite(y).all() and y.min() >= 0 and y.max() <= 1
        tensors.append((row['sid'],x,y,weights))
    opt = torch.optim.AdamW(model.parameters(),lr=protocol['learning_rate'],weight_decay=1e-4)
    rng = np.random.default_rng(protocol['seed'])
    order, losses = [], []
    started = time.monotonic()
    with (ROOT/'training_journal.jsonl').open('x') as log:
        import json
        for update in range(protocol['updates']):
            if not order:
                order = list(rng.permutation(len(tensors)))
            sid,x,y,weights = tensors[order.pop()]
            opt.zero_grad(set_to_none=True)
            logits = temporal_logits(model,x)
            loss = (F.binary_cross_entropy_with_logits(logits,y,reduction='none')*weights).sum()
            assert torch.isfinite(loss)
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True)
            assert float(norm) > 0
            opt.step()
            losses.append(float(loss.detach()))
            log.write(json.dumps(dict(update=update+1,sid=sid,loss=losses[-1]))+'\n')
            log.flush()
    checkpoint = ROOT/'umt_final.pt'
    torch.save(dict(model=model.state_dict(),config=cfg,updates=len(losses),seed=protocol['seed']),checkpoint)
    # Freeze the only final checkpoint before any held-dataset labels or metrics.
    model.eval()
    original = score_features(model,tensors[0][1],torch.ones_like(tensors[0][2],dtype=torch.bool))
    state = torch.load(checkpoint,map_location='cuda',weights_only=True)
    model.load_state_dict(state['model'],strict=True)
    reloaded = score_features(model,tensors[0][1],torch.ones_like(tensors[0][2],dtype=torch.bool))
    assert torch.allclose(original,reloaded,atol=1e-7,rtol=1e-6)
    write_new(ROOT/'frozen_final.json',dict(status='ONLY_FINAL_CHECKPOINT_FROZEN_RELOAD_PASS',
              checkpoint=reference(checkpoint),updates=len(losses),seconds=time.monotonic()-started,
              train_sources=[s['sid'] for s in rows],first20_loss=float(np.mean(losses[:20])),
              final20_loss=float(np.mean(losses[-20:])),held_labels_opened=False,
              visual_backbone_updates=0,base_TIME_updates=0,automatic_production=False))


if __name__ == '__main__':
    main()
