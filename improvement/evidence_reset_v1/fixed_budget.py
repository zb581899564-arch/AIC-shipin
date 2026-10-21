"""Source-native relative target feasibility and fixed-cardinality ceiling."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np


def fixed_cardinality_ceiling(labels, baseline, eligible):
    labels=np.asarray(labels)
    if labels.dtype!=np.bool_ or labels.ndim!=2 or not labels.shape[1]:raise ValueError('Original native/reviewer Boolean matrix required')
    n=len(labels);baseline=set(baseline);eligible=set(eligible)
    if any(type(v)is not int or not 0<=v<n for v in baseline|eligible):raise ValueError('Native domain mismatch')
    total=len(baseline);outside=baseline-eligible;inside_count=total-len(outside)
    gt=labels.sum(axis=0,dtype=np.int64);den=total+gt
    weights=np.divide(labels,den[None,:],out=np.zeros(labels.shape,dtype=float),where=den[None,:]!=0).mean(axis=1)
    possible=sorted(eligible,key=lambda i:(-weights[i],i))
    chosen=outside|set(possible[:inside_count])
    if len(chosen)!=total:raise ValueError('Original source cardinality cannot be realized')
    def utility(s):
        tp=labels[sorted(s)].sum(axis=0,dtype=np.int64)
        return float(np.divide(2.0*tp,len(s)+gt,out=np.ones_like(tp,dtype=float),where=(len(s)+gt)!=0).mean())
    return dict(original_frame_count=total,modeled_budget=inside_count,fixed_outside_frames=len(outside),
        eligible_native_frames=len(eligible),baseline_f1=utility(baseline),oracle_f1=utility(chosen),
        exact=True,reference_assisted_not_predictor=True)


def relative_pairs(blocks, labels, source_sha, protocol):
    result=[]
    for i,a in enumerate(blocks):
        for b in blocks[i+1:]:
            da=labels[a['start_ordinal']:a['stop_ordinal']].mean(axis=0)
            db=labels[b['start_ordinal']:b['stop_ordinal']].mean(axis=0)
            difference=da-db
            preference=float(np.where(difference>0,1.0,np.where(difference<0,0.0,.5)).mean())
            density=float(difference.mean())
            if abs(preference-.5)<protocol['minimum_preference_distance_from_half'] or abs(density)<protocol['minimum_mean_summary_density_difference']:
                continue
            key=hashlib.sha256(('AIC_FIXED_DURATION_PAIR05:'+source_sha+':'+str(a['index'])+':'+str(b['index'])).encode()).hexdigest()
            result.append(dict(left_block=a['index'],right_block=b['index'],preference_left=preference,
                mean_density_difference=density,original_reviewer_count=len(difference),hash_order=key,
                per_reviewer_density_left=da.tolist(),per_reviewer_density_right=db.tolist()))
    chosen=[];used=set()
    for row in sorted(result,key=lambda x:x['hash_order']):
        ids={row['left_block'],row['right_block']}
        if used&ids:continue
        chosen.append(row);used.update(ids)
        if len(chosen)==protocol['maximum_pairs_per_source']:break
    return chosen,len(result)


def run(root):
    root=Path(root).resolve(strict=True);W=root.parent.parent;start=time.monotonic()
    reg=json.loads((root/'registration05.json').read_text())
    spec=importlib.util.spec_from_file_location('diagnostic_api05',root.parent/'diagnostic.py')
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    protocol=api.checked_json(reg['protocol_ref'],W)
    sys.path.insert(0,reg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    manifest=api.checked_json(reg['asset_manifest_ref'],W)
    summaries={};all_refs=[]
    for scope in ['train','check']:
        store=NativeInputStore(manifest,scope);counts=[]
        for sid in sorted(store.source_ids):
            if time.monotonic()-start>protocol['cpu_seconds_budget']:raise TimeoutError('CPU budget')
            human=store.source_supervision(sid);clock=human['clock'];pts=[Fraction(v) for v in clock['normalized_exact_pts']]
            n=len(pts);r=len(human['raters'])
            if not all(len(mask)==n and all(mask) for mask in human['known_masks']):raise ValueError('UNKNOWN not unselected')
            labels=np.zeros((n,r),dtype=bool)
            for col,truth in enumerate(human['raters']):labels[sorted(truth),col]=True
            source=store.sources[sid]
            samples=[o for p in source['patches'] for o in p['samples']]
            if samples!=sorted(set(samples)) or len(samples)!=source['cells']:raise ValueError('Accepted unique real observation catalog required')
            end=Fraction(clock['physical_end_exact']);step=Fraction(protocol['block_duration_exact_seconds'])
            full_count=int(end//step);blocks=[]
            import bisect
            for index in range(full_count):
                lo,hi=index*step,(index+1)*step
                a,b=bisect.bisect_left(pts,lo),bisect.bisect_left(pts,hi)
                available=[k for k,o in enumerate(samples) if lo<=pts[o]<hi]
                if b<=a or len(available)<protocol['observations_per_excerpt']:continue
                take=np.linspace(0,len(available)-1,protocol['observations_per_excerpt']).round().astype(int).tolist()
                positions=[available[k] for k in take]
                if len(set(positions))!=12:raise ValueError('No padded or duplicate observations')
                ordinals=[samples[k] for k in positions]
                blocks.append(dict(index=index,start_exact=str(lo),end_exact=str(hi),start_ordinal=a,stop_ordinal=b,
                    observations=positions,native_observation_ordinals=ordinals,
                    observation_exact_pts=[str(pts[o]) for o in ordinals],native_frames=b-a,
                    video_grid_hw=store.requests[store.by_source[sid][0]]['grid_hw']))
            pairs,potential=relative_pairs(blocks,labels,human['source_sha256'],protocol)
            eligible=set(i for b in blocks for i in range(b['start_ordinal'],b['stop_ordinal']))
            capacity=fixed_cardinality_ceiling(labels,human['baseline'],eligible)
            record=dict(source_id=sid,source_sha256=human['source_sha256'],scope=scope,
                clock_ref=source['clock_ref'],supervision_ref=source['supervision_ref'],
                native_count=n,reviewers=r,complete_blocks=len(blocks),blocks=blocks,
                strong_candidate_pairs=potential,selected_pairs=pairs,fixed_budget_ceiling=capacity,
                historical_exposed=True,summary_omission_is_exhaustive_no_highlight=False)
            dst=root/(scope+'_'+sid+'_pairs05.json');api.save_new(dst,record);all_refs.append(api.reference(dst))
            counts.append(dict(source_id=sid,blocks=len(blocks),eligible_pairs=potential,pairs=len(pairs),**capacity))
        summaries[scope]=dict(registered_sources=len(counts),sources_with_pairs=sum(v['pairs']>0 for v in counts),
            pair_count=sum(v['pairs'] for v in counts),complete_blocks=sum(v['blocks'] for v in counts),
            zero_pair_sources=[v['source_id'] for v in counts if not v['pairs']],
            macro_baseline=sum(v['baseline_f1'] for v in counts)/len(counts),
            macro_fixed_budget_oracle=sum(v['oracle_f1'] for v in counts)/len(counts),per_source=counts)
    reasons=[]
    for scope in ['train','check']:
        for suffix,key in [('sources','sources_with_pairs'),('pairs','pair_count')]:
            if summaries[scope][key]<protocol['minimum_'+scope+'_'+suffix]:reasons.append('INSUFFICIENT_'+scope.upper()+'_'+suffix.upper())
    result=dict(status='READY_FOR_SEPARATE_SMALL_TRAINING_REVIEW' if not reasons else 'STOP_FIXED_PAIR_DATA_INSUFFICIENT',
        stop_reasons=reasons,scopes=summaries,source_refs=all_refs,new_model_calls=0,new_training=0,new_decode=0,
        seconds=time.monotonic()-start,automatic_training=False,automatic_production=False,official_joint_score='UNKNOWN')
    api.save_new(root/'completion05.json',result)
    print(json.dumps({**{k:v for k,v in result.items() if k not in ['scopes','source_refs']},
        'scopes':{s:{k:v for k,v in d.items() if k!='per_source'} for s,d in summaries.items()}}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);a=p.parse_args()
    try:run(a.run_root)
    except BaseException:
        with (Path(a.run_root)/'failure05.json').open('x') as f:json.dump(dict(status='ACTUAL_FAILURE_NO_ZERO_SUBSTITUTION',traceback=traceback.format_exc()),f,indent=2)
        raise
