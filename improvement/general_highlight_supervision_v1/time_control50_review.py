"""Real native output selection before unknown-label masking; no oracle mask in inference."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import json
import sys
import numpy as np

from time_control50_common import ROOT,SPORT,WORK,read,ref,save,checked,runtime


def metrics(chosen, labels):
    known=labels>=0
    prediction=set(np.flatnonzero(chosen & known).tolist())
    target=set(np.flatnonzero(labels==1).tolist())
    denominator=len(prediction)+len(target)
    tp=len(prediction & target)
    return dict(F1=2*tp/denominator if denominator else 0.,selected_known=len(prediction),
        selected_total=int(chosen.sum()),TP=tp,FP=len(prediction)-tp,
        positives=len(target),unknown_selected=int((chosen & ~known).sum()))


def raw_control(source):
    rt=runtime();clock=read(checked(source['clock']));origin=Fraction(clock['first_PTS_exact'])
    import torch
    from transformers import AutoTokenizer
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from time_control50_common import RUN
    tokenizer=AutoTokenizer.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True)
    candidates=ascii_token_candidates(tokenizer)
    points=[Fraction(p)-origin for p in clock['PTS']];end=Fraction(clock['physical_end_exact'])-origin
    masks={name:np.zeros(len(points),dtype=bool) for name in ['B0','D8']}
    all_ranges=[]
    for record in read(ROOT/'gpu_completion.json')['outputs']:
        accepted=read(checked(record));raw=read(checked(accepted['raw']))
        lo=Fraction(accepted['source_start']);hi=Fraction(accepted['source_end'])
        if tokenizer.decode(raw['token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)!=raw['raw']:
            raise ValueError('Independent CPU token decoding differs')
        grammar=make_prefix_constraint(tokenizer,raw['prefix'],hi-lo,candidate_token_ids=candidates,eos_token_ids=raw['eos'],allow_empty=True)
        grammar.assert_complete(torch.tensor(raw['token_ids'],dtype=torch.long))
        segments,errors,_=rt.parse_segments(raw['raw'],hi-lo,allow_empty=True)
        if errors or segments!=accepted['segments']:raise ValueError('Independent original raw parse differs')
        for first,stop in segments:
            a=lo+Fraction(str(first));b=lo+Fraction(str(stop));all_ranges.append([str(a),str(b)])
            for name,pre,post in [('B0',Fraction(0),Fraction(0)),('D8',Fraction(3,4),Fraction(1,2)+(Fraction(1,4) if b-a>=8 else 0))]:
                first_index=bisect_left(points,max(Fraction(0),a-pre))
                stop_index=bisect_left(points,min(end,b+post))
                masks[name][first_index:stop_index]=True
    return masks,all_ranges


def main():
    source=read(ROOT/'registration.json')['source'];masks,ranges=raw_control(source)
    sys.path.insert(0,str(SPORT/'code'));from pilot15_common import original_targets
    labels=original_targets(source)
    accepted=read(SPORT/'inputs'/source['source']/'acceptance.json')
    groups=np.load(checked(accepted['groups']),allow_pickle=False)
    expert=np.load(SPORT/'outputs'/(source['source']+'_matched_HL.npy'),allow_pickle=False)
    route=next(row for row in read(WORK/'general_highlight_supervision_20261021_v1/semantic_route48/routing.json')
               if row['sid']=='S_'+source['source'])
    output={};selected={}
    for control,baseline in masks.items():
        replacement=baseline.copy()
        if route['source_routed']:
            replacement[:]=False
            replacement[np.argsort(-expert[groups],kind='stable')[:int(baseline.sum())]]=True
        supplement=baseline | (np.isin(groups,route['routed_cells']) & (expert[groups]>=.5))
        output[control]={name:metrics(chosen,labels) for name,chosen in
                         [('original_TIME',baseline),('source_route',replacement),('cell_supplement',supplement)]}
        for name,value in [('original_TIME',baseline),('source_route',replacement),('cell_supplement',supplement)]:
            selected[control+'_'+name]=value
    with (ROOT/'selections.npz').open('xb') as out:np.savez_compressed(out,**selected)
    # No score or prediction used an unknown/positive label mask before selection.
    gains={name:all(output[c][name]['F1']>output[c]['original_TIME']['F1'] for c in output)
           for name in ['source_route','cell_supplement']}
    save(ROOT/'review.json',dict(state='STRONG_TIME_ROUTING_SIGNAL_REQUIRES_FULL40_47_BRIDGE' if any(gains.values()) else 'STOP_ROUTING_VS_STRONG_TIME_CONTROL50',
        source=source['source'],metrics=output,positive_gain_under_both_frozen_controls=gains,
        all_original_native_frames_selected_before_UNKNOWN_mask=True,exact40_47_control=False,
        still_missing='Original VERIFY/refine and context-semantic additions, if this stronger first gate passes',
        no_new_thresholds=True,no_automatic426_or_package=True))
    save(ROOT/'independent_CPU_audit.json',dict(state='PASS',native_segments=ranges,
        selected_masks=ref(ROOT/'selections.npz'),unknown_not_selector_input=True,
        raw_parser_replayed_without_model=True,all_expected_windows=read(ROOT/'CPU_completion.json')['windows']))


if __name__=='__main__':main()
