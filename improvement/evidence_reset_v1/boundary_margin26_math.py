"""Native-action MAP boundary diagnostic; no neural/model interfaces."""
import numpy as np


def F1(tp,count,gt):
    tp=np.asarray(tp,dtype=np.int64);gt=np.asarray(gt,dtype=np.int64);den=count+gt
    if count<0 or tp.shape!=gt.shape or not len(gt)or(tp<0).any()or(tp>gt).any()or(tp>count).any():
        raise ValueError('Complete native all-reviewer count domain')
    return float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())


def diagnose(actions,lengths,overlap,old,new,gt):
    """One native-action swap from the immutable old MAP, all alternatives."""
    assert len(actions)==len(lengths)==len(overlap)==len(old)==len(new)
    groups=[]
    for aa,cc,oo,ll,rr in zip(actions,lengths,overlap,old,new):
        assert len(aa)==len(cc)==len(oo)==len(ll)==len(rr)and np.isfinite(ll).all()and np.isfinite(rr).all()
        native={}
        for j,a in enumerate(aa):
            key=tuple(sorted(a));assert len(key)==cc[j]and len(set(key))==len(key)
            if key in native:assert np.array_equal(oo[j],oo[native[key][0]])
            native.setdefault(key,[]).append(j)
        row=[]
        for key,indices in native.items():
            j=indices[0];row.append(dict(action=key,indices=indices,n=cc[j],tp=np.asarray(oo[j],dtype=np.int64),
                old=max(ll[i]for i in indices),new=max(rr[i]for i in indices)))
        groups.append(row)
    choices=[max(range(len(row)),key=lambda j:row[j]['old'])for row in groups]
    count=sum(row[j]['n']for row,j in zip(groups,choices));tp=sum((row[j]['tp']for row,j in zip(groups,choices)),start=np.zeros(len(gt),dtype=np.int64))
    initial=F1(tp,count,gt);rows=[]
    for w,(row,j)in enumerate(zip(groups,choices)):
        win=row[j]
        for k,alt in enumerate(row):
            if k==j:continue
            after=F1(tp-win['tp']+alt['tp'],count-win['n']+alt['n'],gt)
            m0=alt['old']-win['old'];m1=alt['new']-win['new']
            rows.append(dict(window=w,old_winner_group=j,alternative_group=k,native_count_delta=alt['n']-win['n'],
                F1_if_one_swap=after,delta_utility=after-initial,margin0=m0,margin1=m1,delta_margin=m1-m0,
                original_winner_suffixes=win['indices'],alternative_suffixes=alt['indices']))
    informative=[r for r in rows if abs(r['delta_utility'])>1e-12]
    norm=sum(abs(r['delta_utility'])for r in informative)
    alignment=sum(r['delta_utility']*r['delta_margin']for r in informative)/norm if norm else 0.
    helpful=[r for r in informative if r['delta_utility']>0];harmful=[r for r in informative if r['delta_utility']<0]
    return dict(initial_MAP_F1=initial,initial_MAP_frames=count,unique_native_groups=sum(map(len,groups)),
        alternative_swaps=len(rows),informative_swaps=len(informative),beneficial_swaps=len(helpful),harmful_swaps=len(harmful),
        mean_utility_weighted_margin_alignment=float(alignment),
        beneficial_closer=sum(r['delta_margin']>1e-6 for r in helpful),beneficial_farther=sum(r['delta_margin']< -1e-6 for r in helpful),
        harmful_farther=sum(r['delta_margin']< -1e-6 for r in harmful),harmful_closer=sum(r['delta_margin']>1e-6 for r in harmful),
        rows=rows)
