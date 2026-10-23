"""Independent all-reviewer native-frame evaluation of the one frozen new model."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np
from pilot_common28 import ROOT,ENGINEERING,read,ref,save,checked,native_reference


def paired_f1(chosen,labels):
    if labels.dtype!=np.bool_ or labels.ndim!=2 or len(labels)!=len(chosen):
        raise ValueError('Reference is not original binary per-reviewer selection')
    true=labels[chosen].sum(axis=0);denom=int(chosen.sum())+labels.sum(axis=0)
    vector=np.divide(2*true,denom,out=np.zeros(len(denom),dtype=float),where=denom>0)
    selected=set(np.flatnonzero(chosen).tolist());independent=[]
    for i in range(labels.shape[1]):
        human=set(np.flatnonzero(labels[:,i]).tolist());d=len(selected)+len(human)
        independent.append(2*len(selected&human)/d if d else 0.)
    if not np.allclose(vector,independent,atol=1e-12,rtol=0):raise ValueError('Independent all-reviewer F1 differs')
    return float(vector.mean())


def select(scores,groups,count):
    if scores.ndim!=1 or not np.isfinite(scores).all() or len(scores)!=int(groups.max())+1:
        raise ValueError('First temporal outputs do not match native cells')
    chosen=np.zeros(len(groups),dtype=bool)
    chosen[np.argsort(-scores[groups],kind='stable')[:count]]=True
    return chosen


def source_metrics(source):
    labels,durations=native_reference(source)
    accepted=read(checked(source['input']))
    rgb=np.load(checked(accepted['rgb']),mmap_mode='r',allow_pickle=False)
    groups=np.load(checked(accepted['groups']),allow_pickle=False)
    if rgb.dtype!=np.uint8 or rgb.shape!=(accepted['cells'],8,224,224,3):
        raise ValueError('Accepted real I3D input serialization changed')
    if not np.array_equal(groups,np.arange(len(labels))//64):raise ValueError('Native groups changed')
    count=round(len(labels)*read(ROOT/'protocol.json')['coverage'])
    metrics={};duration_metrics={};changed={};selections={}
    for condition in ['old_summary','sport_control','new_noncompetitive','new_halfshift']:
        scores=np.load(ROOT/'outputs'/(source['sid']+'_'+condition+'.npy'),allow_pickle=False)
        chosen=select(scores,groups,count);selections[condition]=chosen
        metrics[condition]=paired_f1(chosen,labels)
        true=(labels*durations[:,None])[chosen].sum(axis=0)
        denom=durations[chosen].sum()+(labels*durations[:,None]).sum(axis=0)
        duration_metrics[condition]=float(np.divide(2*true,denom,out=np.zeros(len(denom)),where=denom>0).mean())
    changed=int(np.logical_xor(selections['new_noncompetitive'],selections['old_summary']).sum())
    return dict(sid=source['sid'],role=source['role'],publisher=source['publisher'],
        original_reviewers=labels.shape[1],native_frames=len(labels),selected=count,
        macro_reviewer_frame_F1=metrics,macro_reviewer_duration_F1=duration_metrics,
        changed_vs_old_summary=changed,summary_unselected_is_preference_not_explicit_NHL=True)


def bridge_metrics(row):
    source=row['source'];sid=source['sid']
    with np.load(checked(source['comparison_ref']),allow_pickle=False) as data:
        baseline=data['baseline'];raw=data['labels']
        if not np.isin(baseline,[0,1]).all() or not np.isin(raw,[0,1]).all():raise ValueError('Unknown original bridge labels')
        baseline=baseline.astype(bool);labels=raw.astype(bool)
    groups=np.load(checked(row['groups']),allow_pickle=False)
    if not np.array_equal(groups,np.arange(len(labels))//64):raise ValueError('External native groups changed')
    metrics=dict(external_TIME=paired_f1(baseline,labels));selected=int(baseline.sum())
    old=next(r for r in read(ENGINEERING/'crossdata12/review.json')['results'] if r['sid']==sid)
    if abs(metrics['external_TIME']-old['metrics']['inherited_external_control'])>1e-12:
        raise ValueError('Original external control metric differs')
    metrics['old_summary']=old['metrics']['umt']
    for condition in ['new_noncompetitive','new_halfshift']:
        scores=np.load(ROOT/'outputs'/(sid+'_'+condition+'.npy'),allow_pickle=False)
        metrics[condition]=paired_f1(select(scores,groups,selected),labels)
    return dict(sid=sid,native_frames=len(labels),reviewers=labels.shape[1],selected=selected,metrics=metrics)


def main():
    registration=read(ROOT/'registration.json');frozen=read(ROOT/'frozen_final.json');checked(frozen['checkpoint'])
    train={s['sid'] for s in registration['sources'] if s['role']=='development'}
    if set(frozen['training_sources'])!=train:raise ValueError('Held source leaked into actual training')
    journal=[__import__('json').loads(x) for x in (ROOT/'training_journal.jsonl').read_text().splitlines()]
    if len(journal)!=200 or {r['sid'] for r in journal}!=train:raise ValueError('Actual fixed training budget or roles differ')
    sources=[source_metrics(s) for s in registration['sources']]
    held=[s for s in sources if s['role']=='held_recording']
    held_macro={k:float(np.mean([s['macro_reviewer_frame_F1'][k] for s in held])) for k in held[0]['macro_reviewer_frame_F1']}
    bridge=[bridge_metrics(r) for r in registration['external_bridge']]
    bridge_macro={k:float(np.mean([s['metrics'][k] for s in bridge])) for k in bridge[0]['metrics']}
    held_pass=(held_macro['new_noncompetitive']>max(held_macro[k] for k in ['old_summary','sport_control','new_halfshift'])
        and all(s['macro_reviewer_frame_F1']['new_noncompetitive']>=s['macro_reviewer_frame_F1']['old_summary'] for s in held))
    bridge_pass=bridge_macro['new_noncompetitive']>max(bridge_macro['external_TIME'],bridge_macro['old_summary'],bridge_macro['new_halfshift'])
    result=dict(state='NEW_NONCOMPETITIVE_SIGNAL_REQUIRES_EXACT_BASELINE_BRIDGE' if held_pass and bridge_pass else 'STOP_FIXED_NONCOMPETITIVE_SUPERVISION_PROFILE',
        held_recording_signal=held_pass,general_transfer_signal=bridge_pass,results=sources,
        held_all_reviewer_frame_F1=held_macro,external8_historical_bridge_results=bridge,
        external8_historical_macro_F1=bridge_macro,all_original_reviewers=True,
        independent_set_arithmetic_pass=True,held_quality_metrics_not_seen_before_freeze=True,
        old8_historically_exposed_not_blind=True,source_independence_beyond_known_bytes='UNKNOWN',
        native_ms_and_PTS_no_clipping_stretch_or_padding=True,
        exact40_47_external_control=False,no_official_score_prediction=True,
        no_automatic426_or_ZIP=True,baseline_unchanged=True)
    save(ROOT/'review.json',result)
    save(ROOT/'independent_CPU_audit.json',dict(state='PASS_NATIVE_INPUT_OUTPUT_AND_ALL_REVIEWER_ARITHMETIC',
        sources=len(sources),bridge_sources=len(bridge),new8B_calls=0,model_calls_not_repeated=True))
    print('REVIEW',result['state'],held_macro,bridge_macro,flush=True)


if __name__=='__main__':main()
