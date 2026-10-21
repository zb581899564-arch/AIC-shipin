"""New metadata-only inventory: remaining same-task sources and pair readiness.

Adopts prior identity/native/RGB receipts; no media read, decode, image encode,
model, fitting, or old scientific comparison is rerun.
"""
import argparse
import bisect
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import numpy as np


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(p,v):
    with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)


def require(ok,msg):
    if not ok:raise ValueError(msg)


def main(root):
    started=time.monotonic();N=Path(root).resolve(strict=True);R=N.parent;W=R.parent
    reg=json.loads((N/'registration10.json').read_text());require(reg['code_ref']==ref(__file__),'Bound new inventory implementation')
    m=json.loads((W/'native_preference_20261019_v1/assets.private.json').read_text())
    check={s['name']:s for s in m['scopes']['check']['sources']}
    definitions=[];prior_refs=[]
    for path in [W/'videoxum_reference_iteration_20261013_v1/direct_cohort_06/completion.json',W/'sparse_context_iteration_20261013_v1/new_confirm_CPU_02/completion.json']:
        value=json.loads(path.read_text());require(len(value['accepted']) in (20,8),'Explicit prior accepted source cohort')
        definitions.extend(value['accepted']);prior_refs.append(ref(path))
    require(len(definitions)==28 and len({d['video_id'] for d in definitions})==28 and set(check)<={d['video_id'] for d in definitions},'Actual28 unique known sources/check8 subset')
    spec=json.loads((R/'fixed_budget05/registration05.json').read_text());pair_code=Path(spec['code_ref']['path'])
    require(ref(pair_code)==spec['code_ref'],'Adopt actual frozen relative-pair construction')
    pair_api=module(pair_code,'original_fixed_duration_pairs10')
    protocol=json.loads(Path(spec['protocol_ref']['path']).read_text())
    rows=[];records=[];check_labels=0;known_shas=set();record_refs=[]
    for a in definitions:
        sid=a['video_id'];cp=Path(a['cpu_completion_path']).parent/sid;clock_path=cp/'clock.json';mapping_path=cp/'mapping.json'
        clock=json.loads(clock_path.read_text());mapping=json.loads(mapping_path.read_text())
        require(mapping['status']=='PASS_UNMODIFIED_REFERENCE_SECONDS_IN_NATIVE_DOMAIN' and mapping['clock_sha256']==ref(clock_path)['sha256'],'Adopted successful unmodified native mapping/clock binding')
        source_sha=clock['source_sha256'];require(source_sha not in known_shas,'Duplicate source media bytes');known_shas.add(source_sha)
        pts=list(map(Fraction,clock['original_exact_pts']));end=Fraction(clock['physical_end_exact'])
        require(len(pts)==clock['native_frames'] and pts[0]==0 and all(a<b for a,b in zip(pts,pts[1:])) and Fraction(clock['last_frame_duration_exact'])>0 and pts[-1]+Fraction(clock['last_frame_duration_exact'])==end,'Exact source clock invariants')
        rp=Path(a['reference_path']);require(ref(rp)['sha256']==a['reference_sha256'],'Original human annotation binding')
        original=json.loads(rp.read_text());require(len(original)==1 and original[0]['video_id']==sid,'One declared original author source')
        intervals=original[0]['annotator_intervals_exact_seconds'];require(isinstance(intervals,list) and intervals,'Actual complete reviewer axis')
        labels=np.zeros((len(pts),len(intervals)),dtype=bool)
        for col,segments in enumerate(intervals):
            for pair in segments:
                lo,hi=map(Fraction,pair);require(0<=lo<hi<=end,'Keep original human endpoints, no stretch or clip')
                labels[bisect.bisect_left(pts,lo):bisect.bisect_left(pts,hi),col]=True
        samples={};window_refs=[];all_cache_bytes=0
        for proof in a['proofs']:
            ip=Path(proof['input_path']);require(ref(ip)['sha256']==proof['input_sha256'],'Actual old accepted source input metadata')
            v=json.loads(ip.read_text());require(v['source_sha256']==source_sha and v['all_source_exact_pts']==clock['original_exact_pts'],'Whole native source identity/PTS')
            require(v['bindings']['mapping_sha256']==ref(mapping_path)['sha256'],'Adopt source mapping associated with successful original RGB input')
            fp=Path(v['frame_array_path']);exists=fp.is_file();all_cache_bytes+=fp.stat().st_size if exists else 0
            require(exists,'Previously retained RGB cache unavailable; no automatic re-decode')
            require(len(v['source_frame_ordinals'])==len(v['sample_exact_pts'])==len(v['pixel_sha256']),'Every physical observation has native time/pixel ownership')
            ir=ref(ip);window_refs.append(dict(input_ref=ir,proof_ref=ref(proof['proof_path']),RGB_path=str(fp),RGB_sha256=v['frame_array_sha256'],RGB_bytes=fp.stat().st_size))
            for offset,(ordinal,t,pixel_sha) in enumerate(zip(v['source_frame_ordinals'],v['sample_exact_pts'],v['pixel_sha256'])):
                require(pts[ordinal]==Fraction(t),'Original native sample time')
                if ordinal in samples:require(samples[ordinal]['pixel_sha256']==pixel_sha,'Repeated native observation must have identical retained pixels')
                else:samples[ordinal]=dict(ordinal=ordinal,window=len(window_refs)-1,offset=offset,pixel_sha256=pixel_sha)
        ordered=sorted(samples);require(len(ordered)>=64,'Native64 whole-source Overview without padding')
        overview=[ordered[i] for i in np.linspace(0,len(ordered)-1,64).round().astype(int)]
        blocks=[]
        for index in range(int(end//8)):
            lo=Fraction(index*8);hi=lo+8;a0=bisect.bisect_left(pts,lo);b0=bisect.bisect_left(pts,hi)
            avail=[i for i,o in enumerate(ordered) if lo<=pts[o]<hi]
            if b0<=a0 or len(avail)<12:continue
            indices=[avail[k] for k in np.linspace(0,len(avail)-1,12).round().astype(int)]
            ordinals=[ordered[k] for k in indices]
            require(len(set(ordinals))==12,'No duplicate/fake excerpt observations')
            blocks.append(dict(index=index,start_exact=str(lo),end_exact=str(hi),start_ordinal=a0,stop_ordinal=b0,
                observations=indices,native_observation_ordinals=ordinals,native_frames=b0-a0,observation_exact_pts=[str(pts[o]) for o in ordinals]))
        pairs,potential=pair_api.relative_pairs(blocks,labels,source_sha,protocol)
        is_check=sid in check
        if is_check:
            s=check[sid];require(s['source_sha256']==source_sha,'Check8 author-ID and native source-byte identity')
            with np.load(s['supervision_ref']['path'],allow_pickle=False) as z:
                require(np.array_equal(z[s['supervision_contract']['labels_key']],labels),'New raw-annotation interpretation must equal previously adopted full-native all-reviewer labels')
            check_labels+=1
        record=dict(video_id=sid,source_sha256=source_sha,check8=is_check,clock_ref=ref(clock_path),mapping_ref=ref(mapping_path),
            original_reference_ref=ref(rp),reviewers=len(intervals),native_count=len(pts),source_end_exact=str(end),
            original_ID_and_byte_isolation_adopted_not_global_provenance=True,old_scope='Private noncommercial research external summary proxy; no blanket media rights or new production authority',
            cache_windows=window_refs,sample_catalog=[samples[o] for o in ordered],overview_ordinals=overview,
            blocks=blocks,selected_pairs=pairs,potential_pairs=potential,all_historical_exposed=True,
            old_model_or_reference_compare_rerun=False,new_model_calls=0,new_media_decode=0,new_image_processor=0)
        path=N/(sid+'_record10.json');save(path,record);record_refs.append(ref(path))
        rows.append(dict(video_id=sid,check8=is_check,source_sha256=source_sha,reviewers=len(intervals),blocks=len(blocks),
            pairs=len(pairs),retained_RGB_cache_bytes=all_cache_bytes,samples=len(ordered),record_ref=record_refs[-1]))
    require(check_labels==8,'All8 original supervision mappings reconciled')
    remaining=[r for r in rows if not r['check8']]
    ready=[r for r in remaining if r['pairs']==2]
    ready=sorted(ready,key=lambda r:hashlib.sha256(('AIC_DOMAIN_RANK11:'+r['source_sha256']).encode()).hexdigest())
    # Match population and budget using only training eligibility; never check quality.
    feasible=json.loads((R/'fixed_budget05/completion05.json').read_text())
    summe=[]
    for reference in feasible['source_refs']:
        if not Path(reference['path']).name.startswith('train_'):continue
        source=json.loads(Path(reference['path']).read_text())
        if len(source['selected_pairs'])==2:summe.append(dict(source_id=source['source_id'],source_sha256=source['source_sha256'],record_ref=reference))
    summe=sorted(summe,key=lambda r:hashlib.sha256(('AIC_DOMAIN_RANK11:'+r['source_sha256']).encode()).hexdigest())
    n=min(20,len(ready),len(summe));require(len(remaining)==20,'Actual total28 minus check8 gives20, never guessed original20 disjointness')
    result=dict(status='READY_FOR_SEPARATE_MATCHED_DOMAIN_CPU_HEAD_REVIEW' if n>=12 else 'STOP_INSUFFICIENT_MATCHED_TRAINING_SOURCES',
        all_sources=28,check_sources=8,remaining_sources=20,remaining_with2pairs=len(ready),matched_sources_per_arm=n,matched_pairs_per_arm=2*n,
        selected_VideoXum=ready[:n],selected_SumMe=summe[:n],check_native_label_reconciliation='8/8_EXACT',
        all_source_rows=rows,prior_completion_refs=prior_refs,new_model_calls=0,new_updates=0,new_media_decode=0,new_image_processor=0,
        seconds=time.monotonic()-started,automatic_training_or_GPU=False,automatic_production=False,
        licensing_inference_not_blanket_permission='No new media/rights inferred. The existing provider card permits reproducible research and retains uploader ownership; a new training-use review is separate from earlier validation-only scope.')
    save(N/'completion10.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['selected_VideoXum','selected_SumMe','all_source_rows','prior_completion_refs']}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args();main(args.run_root)
