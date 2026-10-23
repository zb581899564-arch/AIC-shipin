"""First independent native/unknown/all-reviewer arithmetic; no model reruns."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from fractions import Fraction
import json
import math
import numpy as np

from qv_common47 import ROOT,ENGINEERING,read,ref,save,checked
from qv_targets47 import query_metrics,source_queries

ARMS=['frozen_visual','late_visual']


def independent_query(scores, query, actual):
    order=sorted(range(len(query['ids'])),key=lambda i:(-float(scores[query['ids'][i]]),i))
    values=[]
    for reviewer in range(3):
        gains=[2**row[reviewer]-1 for row in query['votes']]
        maximum=sum(g/math.log2(i+2) for i,g in enumerate(sorted(gains,reverse=True)))
        if maximum:values.append(sum(gains[j]/math.log2(i+2) for i,j in enumerate(order))/maximum)
    expected=sum(values)/len(values) if values else None
    if (expected is None)!=(actual['all_reviewer_NDCG'] is None):raise ValueError('Unknown reviewer handling differs')
    if expected is not None and abs(expected-actual['all_reviewer_NDCG'])>1e-12:
        raise ValueError('Independent all-rater DCG differs')
    return expected


def source_result(source):
    groups=np.load(checked(source['groups']),allow_pickle=False)
    clock=read(checked(source['clock']));origin=Fraction(clock['first_PTS_exact'])
    expected=np.asarray([int((Fraction(p)-origin)//2) for p in clock['PTS']])
    if not np.array_equal(groups,expected):raise ValueError('Independent original 2-second mapping differs')
    with np.load(checked(source['rgb']),allow_pickle=False) as data:
        rgb=data['rgb'];indices=data['native_indices']
        if rgb.dtype!=np.uint8 or rgb.shape!=(source['cells'],8,224,224,3):raise ValueError('Actual CPU input shape differs')
        if not np.array_equal(groups[indices],np.repeat(np.arange(len(rgb))[:,None],8,axis=1)):
            raise ValueError('Actual RGB sample is outside native cell')
    if source_queries(source)!=source['queries']:raise ValueError('Original human queries or pairs changed')
    metrics={}
    for condition in ['initial']+sum(([arm,arm+'_halfshift'] for arm in ARMS),[]):
        scores=np.load(ROOT/'outputs'/(source['sid']+'_'+condition+'.npy'),allow_pickle=False)
        if scores.shape!=(source['cells'],) or not np.isfinite(scores).all():raise ValueError('Output scores invalid')
        rows=[]
        for query in source['queries']:
            row=query_metrics(scores,query);independent_query(scores,query,row);rows.append(row)
        metrics[condition]={name:float(np.mean([q[name] for q in rows if q[name] is not None]))
                            if any(q[name] is not None for q in rows) else None
                            for name in ['all_reviewer_NDCG','confident_pair_accuracy']}
    return dict(sid=source['sid'],role=source['role'],youtube_id=source['youtube_id'],metrics=metrics,
        actual_native_frames=len(groups),actual_cells=source['cells'],queries=len(source['queries']))


def frame_f1(chosen, labels):
    if labels.dtype!=np.bool_ or labels.ndim!=2 or len(chosen)!=len(labels):raise ValueError('Original reviewers invalid')
    selected=set(np.flatnonzero(chosen).tolist());scores=[]
    for reviewer in range(labels.shape[1]):
        human=set(np.flatnonzero(labels[:,reviewer]).tolist());den=len(selected)+len(human)
        scores.append(2*len(selected&human)/den if den else 0.)
    intersections=labels[chosen].sum(0);denom=int(chosen.sum())+labels.sum(0)
    vector=np.divide(2*intersections,denom,out=np.zeros(labels.shape[1]),where=denom>0)
    if not np.allclose(vector,scores,atol=1e-12,rtol=0):raise ValueError('Independent set F1 differs')
    return float(np.mean(scores))


def bridge_result(row):
    source=row['source'];sid=source['sid']
    with np.load(checked(source['comparison_ref']),allow_pickle=False) as data:
        baseline=data['baseline'];labels=data['labels']
        if not np.isin(baseline,[0,1]).all() or not np.isin(labels,[0,1]).all():raise ValueError('Original bridge labels invalid')
        baseline=baseline.astype(bool);labels=labels.astype(bool)
    groups=np.load(checked(row['groups']),allow_pickle=False)
    if not np.array_equal(groups,np.arange(len(labels))//64):raise ValueError('Original bridge input groups differ')
    count=int(baseline.sum());metrics=dict(external_TIME=frame_f1(baseline,labels))
    old=next(r for r in read(ENGINEERING/'crossdata12/review.json')['results'] if r['sid']==sid)
    if abs(metrics['external_TIME']-old['metrics']['inherited_external_control'])>1e-12:
        raise ValueError('Adopted original TIME F1 changed')
    metrics['old_summary']=old['metrics']['umt']
    for arm in ARMS:
        for condition in [arm,arm+'_halfshift']:
            scores=np.load(ROOT/'outputs'/(sid+'_'+condition+'.npy'),allow_pickle=False)
            if len(scores)!=int(groups.max())+1 or not np.isfinite(scores).all():raise ValueError('Bridge score domain differs')
            chosen=np.zeros(len(groups),dtype=bool)
            chosen[np.argsort(-scores[groups],kind='stable')[:count]]=True
            metrics[condition]=frame_f1(chosen,labels)
    return dict(sid=sid,metrics=metrics,coverage_original_TIME=count,native_frames=len(groups))


def main():
    registration=read(ROOT/'registration.json');protocol=read(ROOT/'protocol.json')
    train={s['sid'] for s in registration['sources'] if s['role']=='development' and any(q['pairs'] for q in s['queries'])}
    for arm in ARMS:
        frozen=read(ROOT/(arm+'_frozen.json'));checked(frozen['checkpoint'])
        journal=[json.loads(line) for line in (ROOT/(arm+'_training.jsonl')).read_text().splitlines()]
        if (len(journal)!=protocol['updates_per_arm'] or set(frozen['training_sources'])!=train
                or not {r['sid'] for r in journal}<=train):raise ValueError('Actual update/source-role budget differs')
    sources=[source_result(s) for s in registration['sources']]
    held=[s for s in sources if s['role']=='held_recording'];macro={}
    for condition in held[0]['metrics']:
        macro[condition]={metric:float(np.mean([s['metrics'][condition][metric] for s in held
                                               if s['metrics'][condition][metric] is not None]))
                          for metric in ['all_reviewer_NDCG','confident_pair_accuracy']}
    bridges=[bridge_result(row) for row in registration['external_bridge']]
    bridge_macro={name:float(np.mean([row['metrics'][name] for row in bridges])) for name in bridges[0]['metrics']}
    signals={}
    for arm in ARMS:
        better=sum(s['metrics'][arm]['all_reviewer_NDCG']>s['metrics']['initial']['all_reviewer_NDCG'] for s in held)
        worst=min(s['metrics'][arm]['all_reviewer_NDCG']-s['metrics']['initial']['all_reviewer_NDCG'] for s in held)
        held_pass=all(macro[arm][metric]>max(macro['initial'][metric],macro[arm+'_halfshift'][metric]) for metric in macro[arm]) and better>=2 and worst>=-.10
        signals[arm]=dict(held_content_signal=held_pass,held_sources_improved=better,worst_held_NDCG_delta=worst,
            general_macro_F1_delta_vs_TIME=bridge_macro[arm]-bridge_macro['external_TIME'],
            general_macro_F1_delta_vs_old_UMT=bridge_macro[arm]-bridge_macro['old_summary'],
            general_beats_own_shift=bridge_macro[arm]>bridge_macro[arm+'_halfshift'])
    visual_effect=all(macro['late_visual'][metric]>macro['frozen_visual'][metric] for metric in macro['late_visual'])
    candidate_signal=any(s['held_content_signal'] and s['general_macro_F1_delta_vs_TIME']>0 and s['general_beats_own_shift'] for s in signals.values())
    state='NEW_REAL_PREFERENCE_SIGNAL_REQUIRES_EXACT40_47_BRIDGE' if candidate_signal else 'STOP_FIXED_AUTHOR_QV47_PROFILE'
    result=dict(state=state,held_all_reviewer_macro=macro,historical_external8_macro_F1=bridge_macro,
        arm_signals=signals,late_visual_exceeds_same_supervision_frozen_control=visual_effect,
        sources=sources,external_sources=bridges,query_conditional_not_generic_dense_HL=True,
        no_test_labels=True,no_official_joint_score=True,old8_not_blind=True,
        no_automatic426_or_package=True,baseline_unchanged=True)
    save(ROOT/'review.json',result)
    save(ROOT/'independent_CPU_audit.json',dict(state='PASS',sources=len(sources),held=len(held),
        native_mapping_and_actual_input=True,all_original_reviewers=True,unknown_excluded=True,
        independent_DCG_and_set_F1=True,all_model_outputs_adopted_not_repeated=True))
    print('QV47_REVIEW',state,macro,bridge_macro,signals,flush=True)


if __name__=='__main__':main()
