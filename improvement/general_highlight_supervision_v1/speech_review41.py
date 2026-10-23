"""Whole-source human-summary information test, not production or official-score qualification."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import hashlib
import numpy as np

from common import ROOT,read,ref,save
from pilot_common28 import checked,interval_mask
from pilot_review28 import paired_f1
from score_contract39 import ScorePattern

TARGET=ROOT/'speech_rank42'


def reference(source):
    clock=read(checked(source['clock']));origin=Fraction(clock['first_PTS_exact'])
    points=[Fraction(p)-origin for p in clock['PTS']]
    annotations=read(checked(source['annotations']));labels=[]
    for a in annotations:
        spans=[(Fraction(str(s['start_time']))/1000,Fraction(str(s['end_time']))/1000) for s in a['summary_timestamps']]
        labels.append(interval_mask(points,spans))
    return points,np.stack(labels,axis=1)


def choose(scores,known,groups,count):
    scores=np.asarray(scores,dtype=float);known=np.asarray(known,dtype=bool)
    valid=known[groups]&(scores[groups]>0)
    indices=np.flatnonzero(valid);order=indices[np.argsort(-scores[groups[indices]],kind='stable')]
    chosen=np.zeros(len(groups),dtype=bool);chosen[order[:count]]=True
    return chosen


def source_result(source,reg,tokenizer):
    points,labels=reference(source)
    bounds=[Fraction(c['start_exact']) for c in source['chunks']]
    groups=np.asarray([max(0,bisect_left(bounds,p) if p in bounds else bisect_left(bounds,p)-1) for p in points])
    if groups.min()<0 or groups.max()>=len(source['chunks']):raise ValueError('Native frame/audio chunk mapping failed')
    frame_budget=round(len(points)*.15);metrics={};counts={};saved={}
    for condition in ['correct','halfshift']:
        raw=read(TARGET/'outputs'/(source['sid']+'_'+condition+'.json'))
        case=read(checked(raw['input']));ids=raw['generated_token_ids']
        if not raw['EOS_observed'] or ids[-1]!=151645:raise ValueError('Missing actual EOS')
        decoded=tokenizer.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if decoded!=raw['decoded_text']:raise ValueError('Independent saved token/text replay differs')
        scores=ScorePattern(case['known']).parse(decoded);saved[condition]=scores
        selected=choose(scores,case['known'],groups,frame_budget)
        metrics[condition]=paired_f1(selected,labels);counts[condition]=int(selected.sum())
        if condition=='correct':known=case['known']
    null=[1+int(hashlib.sha256((source['sid']+'/fixed_null/'+str(i)).encode()).hexdigest(),16)/(2**256)
          for i in range(len(source['chunks']))]
    selected=choose(null,known,groups,frame_budget)
    metrics['fixed_temporal_null_same_observed_mask']=paired_f1(selected,labels)
    counts['fixed_temporal_null_same_observed_mask']=int(selected.sum())
    known_values=[s for s,k in zip(saved['correct'],known) if k]
    return dict(sid=source['sid'],native_frames=len(points),reviewers=labels.shape[1],metrics=metrics,
        actual_selected_frames=counts,frame_budget=frame_budget,source_duration=source['physical_duration_exact'],
        known_speech_chunks=sum(known),all_chunks=len(known),scores=saved,
        content_ranking_nonconstant=len(set(known_values))>1,
        coarse_time_only='Exact30sec source intervals; word boundaries unavailable',
        successful_reject_not_failure=all(s==0 for s in saved['correct']))


def main():
    from transformers import AutoTokenizer
    reg=read(TARGET/'registration.json');cfg=read(checked(reg['model_config']))
    tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    sources=[read(checked(r)) for r in read(ROOT/'speech36/input_acceptance.json')['accepted']]
    rows=[source_result(s,reg,tokenizer) for s in sources]
    macro={k:float(np.mean([s['metrics'][k] for s in rows])) for k in rows[0]['metrics']}
    wins=sum(s['metrics']['correct']>s['metrics']['halfshift'] for s in rows)
    varied=sum(s['content_ranking_nonconstant'] for s in rows)
    passed=macro['correct']>max(macro['halfshift'],macro['fixed_temporal_null_same_observed_mask']) and wins>=3 and varied>=3
    result=dict(state='WHOLE_SOURCE_SPEECH_SIGNAL_REQUIRES_VISUAL_BASELINE_COMPARISON' if passed else 'STOP_FIXED_WHOLE_SOURCE_SPEECH_RANK',
        sources=rows,macro_all_reviewer_F1=macro,correct_wins_over_shift_sources=wins,
        nonconstant_content_ranking_sources=varied,native_masks_and_all_reviewers_replayed=True,
        actual_visual_TIME_comparison=False,exact40_47_control=False,
        no_production_admission=True,no_official_joint_score_claim=True,
        raw_transcript_semantic_correctness='UNKNOWN_NO_INDEPENDENT_ASR_TRANSCRIPT_GT',
        old_local_ASR_and_PANN_STOP_unchanged=True,new_ZIP=0,baseline_unchanged=True)
    save(TARGET/'review.json',result)
    print('WHOLE_SPEECH_REVIEW',result['state'],macro,flush=True)


if __name__=='__main__':main()
