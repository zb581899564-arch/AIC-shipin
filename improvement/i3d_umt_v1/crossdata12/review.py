"""First held-dataset review after freezing, with matched coverage and controls."""
import numpy as np
import torch
from common import ENGINEERING, ROOT, checked, clock, mean_pair_f1, rank_mask, read, reference, write_new
from runtime import make_models, score_features
from train import load_features


def example(row):
    with np.load(checked(row['comparison_ref']),allow_pickle=False) as data:
        baseline = data['baseline'].astype(bool)
        labels = data['labels'].astype(bool)
    c,pts,_ = clock(row)
    inherited = read(checked(row['comparison_clock_ref']))
    assert inherited['source_sha256'] == row['media']['sha256']
    assert inherited['original_exact_pts'] == c['original_exact_pts']
    assert labels.shape[0] == len(pts) == len(baseline)
    groups = np.load(ROOT/'inputs'/row['sid']/'groups.npy',allow_pickle=False)
    return baseline,labels,groups


def fit_ridge(sources):
    """A fixed source-equal simple content baseline, not a tuned alternative arm."""
    xx,yy,ww = [],[],[]
    for s in sources:
        if s['role'] != 'train':
            continue
        x = load_features(s,'cpu')[0].numpy().astype(np.float64)
        y = np.load(ROOT/'inputs'/s['sid']/'target.npy').astype(np.float64)
        groups = np.load(ROOT/'inputs'/s['sid']/'groups.npy')
        w = np.bincount(groups)/len(groups)/20
        xx.append(x); yy.append(y); ww.append(w)
    x,y,w = np.concatenate(xx),np.concatenate(yy),np.concatenate(ww)
    mx,my = np.sum(x*w[:,None],axis=0),float(np.sum(y*w))
    xc,yc = x-mx,y-my
    coef = np.linalg.solve(xc.T@(xc*w[:,None])+np.eye(x.shape[1]),xc.T@(w*yc))
    np.savez(ROOT/'ridge_control.npz',coef=coef,mx=mx,my=my,lambda_value=1.0)
    return coef,mx,my


def review_one(row,model,ridge):
    sid = row['sid']
    x = load_features(row)
    valid = torch.ones(x.shape[:2],dtype=torch.bool,device='cuda')
    with torch.inference_mode():
        real = score_features(model,x,valid).numpy()[0]
        shifted = score_features(model,torch.roll(x,x.shape[1]//2,dims=1),valid).numpy()[0]
    # Persist real outputs before first access to the held annotations.
    np.savez(ROOT/'outputs'/f'{sid}.npz',real=real,shifted=shifted)
    b,y,g = example(row)
    coef,mx,my = ridge
    linear = (x[0].cpu().numpy()-mx)@coef+my
    count = int(b.sum())
    masks = dict(umt=rank_mask(real,g,count),content_shift=rank_mask(shifted,g,count),
                 ridge=rank_mask(linear,g,count),inherited_external_control=b)
    metrics = {k:mean_pair_f1(m,y) for k,m in masks.items()}
    return dict(sid=sid,role=row['role'],native_frames=len(g),reviewers=y.shape[1],
                selected=count,metrics=metrics,changed_frames=int((masks['umt']!=b).sum()),
                score_range=float(np.ptp(real)),not_official_joint_score=True)


def main():
    frozen = read(ROOT/'frozen_final.json')
    checkpoint = checked(frozen['checkpoint'])
    sources = read(ROOT/'registration.json')['sources']
    ridge = fit_ridge(sources)
    (ROOT/'outputs').mkdir()
    unused,model,_ = make_models(ENGINEERING)
    del unused
    model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['model'],strict=True)
    model.cuda().eval().requires_grad_(False)
    # Development first, without selecting a different checkpoint or dose.
    dev = [review_one(s,model,ridge) for s in sources if s['role']=='dev']
    write_new(ROOT/'dev_review.json',dict(results=dev,checkpoint=frozen['checkpoint'],tuning_after_review=False))
    held = [review_one(s,model,ridge) for s in sources if s['role']=='held_dataset']
    assert len(held)==8
    means = {k:float(np.mean([r['metrics'][k] for r in held])) for k in held[0]['metrics']}
    gains = [r['metrics']['umt']-r['metrics']['inherited_external_control'] for r in held]
    gate = read(ROOT/'protocol.json')['review_gate']
    tests = dict(
        existing=means['umt']-means['inherited_external_control']>=gate['held_macro_F1_gain_over_existing_control'],
        ridge=means['umt']-means['ridge']>=gate['held_macro_F1_gain_over_ridge'],
        content=means['umt']-means['content_shift']>=gate['held_macro_F1_gain_over_content_shift'],
        sources=sum(v>0 for v in gains)>=gate['held_sources_improved_over_existing'],
        worst=min(gains)>=-gate['max_per_source_F1_loss'],
        noncollapse=all(r['score_range']>1e-6 and r['selected']>0 for r in held))
    write_new(ROOT/'review.json',dict(status='ELIGIBLE_FOR_PRODUCTION_REVIEW' if all(tests.values()) else 'STOP_CROSS_DATASET_TRANSFER',
              tests=tests,macro_mean_pair_F1=means,results=held,dev=dev,
              checkpoint=frozen['checkpoint'],ridge=reference(ROOT/'ridge_control.npz'),
              exact_4047_external_reconstruction=False,official_score_unknown=True,
              automatic_production=False,held_dataset_not_globally_unseen=True))


if __name__ == '__main__':
    main()
