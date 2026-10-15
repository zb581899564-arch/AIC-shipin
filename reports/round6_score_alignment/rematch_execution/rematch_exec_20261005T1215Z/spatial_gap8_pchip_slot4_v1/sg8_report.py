"""Independent exact reconstruction agreement; no decoder or model repetition."""
from fractions import Fraction
import hashlib
from pathlib import Path

from sg8_common import HERE,V14,read,rows,sha,digest,save,require,utc,old_helpers,inputs,cached_output
from sg8_independent_math import rebuild


def iou(a,b,ratio):
    # Separate evaluator implementation: exact continuous corners and areas.
    x,y,w=a;u,v,z=b;tw,th=ratio
    ah=Fraction(w*th,tw);bh=Fraction(z*th,tw)
    left=max(Fraction(x),Fraction(u));right=min(Fraction(x+w),Fraction(u+z))
    top=max(Fraction(y),Fraction(v));bottom=min(Fraction(y)+ah,Fraction(v)+bh)
    intersection=max(Fraction(0),right-left)*max(Fraction(0),bottom-top)
    return intersection/(w*ah+z*bh-intersection)


def fraction_value(value):
    return dict(numerator=value.numerator,denominator=value.denominator,display_float=float(value))


def reconstruct():
    plan=read(HERE/'input_01/sample_plan.json');sealed=read(HERE/'input_01/sealed_predictions.json')
    complete=read(HERE/'diagnostic_01/inference_completion.json')
    require(complete['observations']==56 and complete['groups']==8 and complete['fresh_calls']==53 and complete['reused_probes']==3,
        'complete frozen observation denominator required')
    require(read(HERE/'input_01/seal_receipt.json')['predictions_sha256']==sha(HERE/'input_01/sealed_predictions.json'),
        'prediction seal changed')
    common,p2j,_=old_helpers();_,manifest,_=inputs('nontest');meta={r['video_id']:r for r in manifest['records']}
    original={(r['video_id'],r['source_frame']):r for r in rows(V14/'nontest_01/anchor_output.jsonl')}
    answers={};accepted={r['request_sha256']:r for r in complete['accepted']}
    require(len(accepted)==56,'duplicate accepted probe identity')
    for obs in plan['requests']:
        if obs['observation_role']!='probe':continue
        req=obs['request'];h=req['anchor_request_sha256'];reference=accepted[h]
        path=Path(reference['path']);require(sha(path)==reference['sha256'],'accepted probe bytes changed')
        value=read(path);require(value['request']==req,'accepted exact native request differs')
        require((req['video_id'],req['source_frame']) not in original,'isolated probe inserted into support authority')
        if value['new_model_calls']==1:
            raw=read(path.parent/'raw.json');proof=read(path.parent/'cpu_replay.json')
            require(sha(path.parent/'raw.json')==value['raw_sha256']==proof['raw_sha256'] and
                sha(path.parent/'cpu_replay.json')==value['cpu_replay_sha256'] and
                sha(HERE/'input_01/observations'/h/'input.json')==value['input_receipt_sha256'] and
                sha(HERE/'diagnostic_01/model.json')==value['model_receipt_sha256']==raw['model_receipt_sha256'],
                'raw/CPU/model/input success binding changed')
            box=value['box_xyw']
        else:
            require(value['status']=='PASS_EXACT_OLD_8B_PROBE_REFERENCE_NO_NEW_CALL' and value['old_cost_preserved'],
                'invalid old cache reference')
            require(sha(Path(value['source_cache']['folder'])/'anchor_output.jsonl')==value['source_cache']['output_sha256'],
                'old cache byte authority changed')
            admission=next(e for e in read(HERE/'input_01/cache_recipe_admission.json')['accepted_probe_caches'] if e['request_sha256']==h)
            actual_old,line_sha=cached_output(admission)
            require(actual_old==value['output'] and line_sha==value['source_raw_line_sha256'] and
                admission['chosen']==value['source_cache'],'independent exact original cache row differs')
            box=value['output']['box_xyw']
        answers[req['video_id'],req['source_frame']]=box
    sealed_map={(r['video_id'],r['source_frame']):r for r in sealed['predictions']}
    result=[];deltas=[]
    for group in plan['groups']:
        vid=group['video_id'];q=group['support_ordinals'];m=meta[vid]
        supports={f:original[vid,f]['box_xyw'] for f in q};phase=[]
        for f in group['probe_ordinals']:
            linear=p2j.interpolate_box(f,supports)[0]
            pchip=[rebuild(q,[supports[n][axis] for n in q],f)[1] for axis in (0,1)]+[supports[q[1]][2]]
            s=sealed_map[vid,f]
            require(s['linear']==linear and s['pchip']==pchip and s['targetRatioWH']==m['targetRatioWH'] and
                s['support_output_sha256']==[digest(original[vid,n]) for n in q],'independent polynomial/sealed support differs')
            answer=answers[vid,f];dl=iou(pchip,answer,m['targetRatioWH'])-iou(linear,answer,m['targetRatioWH'])
            phase.append(dl)
            result.append(dict(group_index=group['group_index'],role=group['role'],video_id=vid,source_frame=f,
                ratio=m['targetRatioWH'],linear=linear,pchip=pchip,probe=answer,delta=fraction_value(dl)))
        require(len(phase)==7,'all seven phases required')
        deltas.append(sum(phase,Fraction(0))/7)
    require(len(deltas)==8 and len(result)==56 and len({g['source_group'] for g in plan['groups']})==8,'registered group denominator differs')
    conf=deltas[2:]
    checks=dict(confirm_at_least4of6_positive=sum(d>0 for d in conf)>=4,
        confirm_mean_positive=sum(conf)>0,all8_mean_positive=sum(deltas)>0,
        all_confirm_leave_one_means_nonnegative=all(sum(conf)-d>=0 for d in conf))
    return dict(status='PASS_G2_NUMERIC_ONLY_G3_PENDING' if all(checks.values()) else 'NO_426_SG8_FIXED_NUMERIC_GATE',
        metric='same_model_framewise_reconstruction_agreement',checks=checks,
        confirmation_positive_groups=sum(d>0 for d in conf),engineering_groups=2,confirmation_groups=6,total_groups=8,phases=56,
        group_deltas=[fraction_value(d) for d in deltas],confirmation_mean=fraction_value(sum(conf)/6),
        all8_mean=fraction_value(sum(deltas)/8),leave_one_confirmation_means=[fraction_value((sum(conf)-d)/5) for d in conf],
        sample_plan_sha256=sha(HERE/'input_01/sample_plan.json'),sealed_predictions_sha256=sha(HERE/'input_01/sealed_predictions.json'),
        inference_completion_sha256=sha(HERE/'diagnostic_01/inference_completion.json'),
        probe_used_as_support=False,new_optimizer_updates=0,official_score=None,composition_truth='UNKNOWN',
        denominator_note='56 phases are not 56 independent source groups',matched_rows=result)


if __name__=='__main__':
    value=reconstruct();value['utc']=utc();save(HERE/'diagnostic_01/report.json',value)
