"""Exact native proposals and scale-separated, candidate-level supervision."""
from bisect import bisect_left
from fractions import Fraction as F
import numpy as np
from event_common import require


def normalize_language(language):
    value = language.astype(np.float64)
    value -= value.mean(0)
    rms = max(1e-6, float(np.sqrt(np.mean(value*value))))
    return value/rms


def weighted_pca(sources):
    require(len(sources) == 25, 'PCA fitted to exactly25 public training sources')
    matrices = [normalize_language(x['language']) for x in sources]
    x = np.concatenate([v/np.sqrt(len(v)) for v in matrices])
    mean = sum(v.mean(0) for v in matrices)/len(matrices)
    # Each source has one unit of covariance mass; never fit to diagnostic or
    # formal features. The fixed randomized range finder avoids a full4096 SVD.
    rng = np.random.default_rng(20261018)
    omega = rng.standard_normal((4096, 40))
    q, _ = np.linalg.qr(x@omega, mode='reduced')
    for _ in range(2):
        z, _ = np.linalg.qr(x.T@q, mode='reduced')
        q, _ = np.linalg.qr(x@z, mode='reduced')
    _, singular, vectors = np.linalg.svd(q.T@x, full_matrices=False)
    components = vectors[:32].copy()
    # Canonicalize arbitrary SVD signs for an explicit persisted basis.
    for row in components:
        if row[np.argmax(np.abs(row))] < 0:
            row *= -1
    require(components.shape == (32,4096) and np.isfinite(components).all(), 'Actual PCA32 finite basis')
    return dict(pca_mean=mean, pca_components=components), singular[:32]


def proposals(clock, baseline, inside=None):
    pts = list(map(F, clock['normalized_exact_pts']))
    end = F(clock['physical_end_exact'])
    require(len(pts) == len(baseline) and len(pts) > 0 and pts[0] == 0, 'Full native clock/mask denominator')
    require(all(a < b for a,b in zip(pts,pts[1:])) and pts[-1] < end, 'Strict native PTS and positive final duration')
    if inside is None:
        inside = np.ones(len(pts), bool)
    require(inside.shape == baseline.shape, 'Native source-field availability')
    missing = ~baseline
    pref = np.r_[0, np.cumsum(missing)]
    bad = np.r_[0, np.cumsum(missing & ~inside)]
    native_new = np.flatnonzero(missing)
    run_starts = np.flatnonzero(missing & ~np.r_[False,missing[:-1]])
    run_ends = np.flatnonzero(missing & ~np.r_[missing[1:],False])+1
    candidates = []
    seen = set()
    lengths = [F(x) for x in (2,4,8) if x <= end]
    if not lengths:
        lengths = [end]
    for length in lengths:
        starts = {F(t) for t in range(int(end-length)+1)}
        starts.add(end-length)
        for a in sorted(starts):
            b = a+length
            left, right = bisect_left(pts,a), bisect_left(pts,b)
            count = int(pref[right]-pref[left])
            if count == 0 or bad[right] != bad[left]:
                continue
            lnew = int(np.searchsorted(native_new,left))
            rnew = int(np.searchsorted(native_new,right))
            first, last = int(native_new[lnew]), int(native_new[rnew-1])
            key = first,last
            if key in seen:
                continue
            runs = []
            for x,y in zip(run_starts,run_ends):
                u,v = max(left,int(x)),min(right,int(y))
                if u < v:
                    stop = pts[v] if v < len(pts) else end
                    runs.append(dict(first_ordinal=u,last_ordinal=v-1,frames=v-u,start_exact=str(pts[u]),end_exact=str(stop),duration_exact=str(stop-pts[u])))
            duration = sum((F(x['duration_exact']) for x in runs),F(0))
            longest = max((F(x['duration_exact']) for x in runs),default=F(0))
            # Fix the old tiny-action failure at the action definition, before
            # any new fitting or diagnostic: envelope length alone is insufficient.
            if duration < 2 or longest < 1:
                continue
            seen.add(key)
            candidates.append(dict(left=left,right=right,start_exact=str(a),end_exact=str(b),duration_exact=str(length),added_frames=count,first_new_frame=first,last_new_frame=last,added_duration_exact=str(duration),longest_new_run_exact=str(longest),new_runs=runs))
    return candidates


def projected(language, pca):
    return (normalize_language(language)-pca['pca_mean'])@pca['pca_components'].T


def descriptors(language, semantic_score, groups, clock, baseline, pca, candidates):
    p = projected(language,pca)
    require(groups.min() == 0 and groups.max()+1 == len(p), 'Occupied original2Hz groups, not invented half-second positions')
    require(len(groups) == len(baseline) == len(clock['normalized_exact_pts']), 'Native feature/time alignment')
    native = p[groups]
    missing = (~baseline).astype(float)
    ps = np.vstack([np.zeros(32),np.cumsum(native,axis=0)])
    newps = np.vstack([np.zeros(32),np.cumsum(native*missing[:,None],axis=0)])
    sqps = np.vstack([np.zeros(32),np.cumsum(native*native*missing[:,None],axis=0)])
    score = semantic_score[groups].astype(float)
    scoreps = np.r_[0.,np.cumsum(score*missing)]
    change = np.linalg.norm(p-np.vstack([p[:1],p[:-1]]),axis=1)[groups]
    changeps = np.r_[0.,np.cumsum(change*missing)]
    pts = list(map(F,clock['normalized_exact_pts']))
    physical_end = F(clock['physical_end_exact'])
    rows = []
    for c in candidates:
        l,r,k = c['left'],c['right'],c['added_frames']
        mean = (newps[r]-newps[l])/k
        std = np.sqrt(np.maximum(0.,(sqps[r]-sqps[l])/k-mean*mean))
        a,b,length = F(c['start_exact']),F(c['end_exact']),F(c['duration_exact'])
        ol,orr = bisect_left(pts,max(F(0),a-length)),bisect_left(pts,min(physical_end,b+length))
        outside = (l-ol)+(orr-r)
        context = ((ps[l]-ps[ol])+(ps[orr]-ps[r]))/outside if outside else p.mean(0)
        index = np.flatnonzero(~baseline[l:r])+l
        scalars = [(scoreps[r]-scoreps[l])/k,float(score[index].max()),(changeps[r]-changeps[l])/k,float(baseline[l:r].mean()),float(baseline.mean()),float(np.log1p(float(length)))]
        rows.append(np.r_[mean,mean-context,std,scalars])
    x = np.asarray(rows,dtype=np.float64).reshape(-1,102)
    require(np.isfinite(x).all(), 'Finite102-dimensional new descriptor')
    return x


def targets(baseline, labels, candidates):
    require(labels.dtype == np.bool_ and labels.ndim == 2 and len(labels) == len(baseline), 'Original full native all-rater labels')
    b = int(baseline.sum())
    g = labels.sum(0,dtype=np.float64)
    tp = labels[baseline].sum(0,dtype=np.float64)
    f0 = np.divide(2*tp,b+g,out=np.zeros_like(tp),where=(b+g)>0)
    support = labels*(~baseline)[:,None]
    ps = np.vstack([np.zeros(labels.shape[1]),np.cumsum(support,axis=0)])
    quality, gains = [],[]
    for c in candidates:
        k = c['added_frames']
        added_tp = ps[c['right']]-ps[c['left']]
        inverse = 1/(b+k+g)
        q = float(np.sum(inverse*(added_tp/k-f0/2))/inverse.sum())
        gain = float(np.mean(2*(tp+added_tp)/(b+k+g)-f0))
        require(abs(gain-2*k*inverse.mean()*q) < 1e-12, 'Exact marginal quality/F1 identity')
        quality.append(q)
        gains.append(gain)
    return np.asarray(quality),np.asarray(gains)


def metric(mask, labels):
    p = int(mask.sum())
    g = labels.sum(0)
    tp = labels[mask].sum(0)
    return dict(f1=float(np.mean(2*tp/np.maximum(1,p+g))),precision=float(np.mean(tp/max(1,p))),recall=float(np.mean(tp/np.maximum(1,g))),selected=p)


def rank(x, candidates, baseline, model):
    q = ((x-model['mean'])/model['std'])@model['coef']+float(model['bias'])
    require(np.isfinite(q).all(), 'Finite signed-quality inference')
    # Mathematical range of reviewer precision minus baseline F1/2; retain raw
    # range diagnostics separately so clipping never hides extrapolation.
    q = np.clip(q,-.5,1.)
    k = np.asarray([c['added_frames'] for c in candidates],float)
    gains = 2*k*q/(baseline.sum()+k+len(baseline)*float(model['rho_train']))
    if len(gains) == 0 or float(gains.max()) <= 0:
        return None,q,gains
    return int(np.argmax(gains)),q,gains


def knapsack(actions, budget):
    """One already selected action per source, indivisible native-frame budget."""
    require(budget >= 0 and len({a['sid'] for a in actions}) == len(actions), 'Unique per-source actions')
    score = np.zeros(budget+1,np.float64)
    take = np.zeros((len(actions),budget+1),bool)
    for i,a in enumerate(actions):
        k = int(a['added_frames'])
        require(k > 0 and np.isfinite(a['predicted_gain']) and a['predicted_gain'] > 0,'Positive indivisible proposal')
        if k > budget:
            continue
        candidate = score[:-k]+a['predicted_gain']
        better = candidate > score[k:]
        take[i,k:] = better
        score[k:] = np.where(better,candidate,score[k:])
    remaining = budget
    chosen = set()
    for i in range(len(actions)-1,-1,-1):
        if take[i,remaining]:
            chosen.add(actions[i]['sid'])
            remaining -= int(actions[i]['added_frames'])
    require(sum(a['added_frames'] for a in actions if a['sid'] in chosen) <= budget,'Actual unique new native frame exposure cap')
    return chosen
