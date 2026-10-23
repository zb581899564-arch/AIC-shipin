"""Independent full-frame known-mask metrics; no label enters inference."""
import numpy as np
from pilot15_common import ROOT, read, checked, save, ref, original_targets


def average_precision(scores,labels):
    order=np.argsort(-scores,kind='stable');s=scores[order];y=labels[order]
    if y.sum()==0 or y.sum()==len(y):raise ValueError('Uninformative single-class held reference')
    ends=np.r_[np.flatnonzero(s[1:]!=s[:-1]),len(s)-1]
    tp=np.cumsum(y,dtype=np.int64)[ends];counts=ends+1
    return float(np.sum(np.diff(np.r_[0,tp])*tp/counts)/y.sum())


def metrics(scores,labels,coverage):
    known=labels>=0;s=scores[known];y=labels[known]
    if not np.isfinite(s).all() or not set(np.unique(y))<={0,1}:raise ValueError('Bad original known reference')
    count=round(len(s)*coverage);selected=np.zeros(len(s),dtype=bool)
    selected[np.argsort(-s,kind='stable')[:count]]=True
    tp=int(y[selected].sum());denom=count+int(y.sum())
    return dict(AP=average_precision(s,y),equal_training_coverage_F1=2*tp/denom if denom else 0.,
        known_frames=len(s),selected_at_fixed_training_coverage=count,positive_frames=int(y.sum()),
        threshold05_selected=int((s>=.5).sum()),score_min=float(s.min()),score_max=float(s.max()))


def independent_AP(scores,labels):
    total=int(labels.sum())
    if total==0:raise ValueError('No positive reference')
    value=0.
    for threshold in np.unique(scores[labels==1]):
        selected=scores>=threshold
        positive_at_level=int(((scores==threshold)&(labels==1)).sum())
        value+=(positive_at_level/total)*(int(labels[selected].sum())/int(selected.sum()))
    return value


def main():
    registration=read(ROOT/'registration.json');protocol=read(ROOT/'protocol.json')
    frozen=read(ROOT/'frozen_final.json');checked(frozen['checkpoint'])
    if set(frozen['train_sources'])!={s['source'] for s in registration['sources'] if s['role']=='development'}:
        raise ValueError('Held source entered actual training source journal')
    train=[original_targets(s) for s in registration['sources'] if s['role']=='development']
    coverage=sum((x==1).sum() for x in train)/sum((x>=0).sum() for x in train)
    rows=[]
    for source in registration['sources']:
        stem=source['source'];labels=original_targets(source)
        groups=np.load(checked(read(ROOT/'inputs'/stem/'acceptance.json')['groups']),allow_pickle=False)
        if len(groups)!=len(labels) or groups.min()<0 or not np.issubdtype(groups.dtype,np.integer):
            raise ValueError('Original frame/group/known label mapping failed')
        result={}
        for condition in ['old_summary','matched_HL','matched_halfshift']:
            values=np.load(ROOT/'outputs'/(stem+'_'+condition+'.npy'),allow_pickle=False)
            if groups.max()>=len(values):raise ValueError('Group outside first saved score output')
            scores=values[groups];result[condition]=metrics(scores,labels,coverage)
            independent=float(independent_AP(scores[labels>=0],labels[labels>=0]))
            if abs(independent-result[condition]['AP'])>1e-12:raise ValueError('Independent AP formulas differ')
        rows.append(dict(source=stem,role=source['role'],metrics=result))
    held=[row for row in rows if row['role']=='held_sport']
    if len(held)!=1:raise ValueError('Frozen held source count changed')
    value=held[0]['metrics'];gain=value['matched_HL']['AP']-value['old_summary']['AP']
    content=value['matched_HL']['AP']-value['matched_halfshift']['AP']
    f1gain=value['matched_HL']['equal_training_coverage_F1']-value['old_summary']['equal_training_coverage_F1']
    passed=gain>=protocol['held_AP_gain'] and content>=protocol['held_shift_AP_gain'] and f1gain>0
    result=dict(state='NARROW_MATCHED_SUPERVISION_SIGNAL_ONLY' if passed else 'STOP_FIXED_MATCHED_SUPERVISION_PILOT',
        sources=rows,training_known_positive_coverage=float(coverage),held_AP_gain=gain,
        held_AP_gain_over_halfshift=content,held_equal_coverage_F1_gain=f1gain,
        independently_recomputed_frame_metrics=True,uncertainty_never_background=True,
        source_count=4,held_sport_count=1,not_broad_T_cohort=True,
        not_exact40_47_control=True,no_official_joint_score_claim=True,
        no_automatic426_or_ZIP=True,baseline40_47_changed=False)
    save(ROOT/'review.json',result)
    print('REVIEW',result['state'],gain,content,f1gain,flush=True)


if __name__=='__main__':main()
