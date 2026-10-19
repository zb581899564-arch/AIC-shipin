"""Conditional one-package exact-observation spatial overlay, CPU only.

Original40.47 times/other boxes/full native field remain authoritative. New
selected observation choices are replayed from accepted scalar outputs; this
does not re-run a successful model, processor, input QA or old raw first QA.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK,RUN,read,save,ref,bound,require,utc

PARAMETERS=8790229268
BASELINE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
NEW_SOURCE='UTILITY_EXACT_NATIVE_OBSERVATION'


def lines(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s]


def write_lines(path,rows):
    with Path(path).open('x',encoding='utf-8') as stream:
        for row in rows:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
        stream.flush();os.fsync(stream.fileno())


def canonical(rows):
    return hashlib.sha256(json.dumps([{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(rows,key=lambda r:r['video_id'])],
        sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def replay_choices(observations,pairs,values,beta,geometry):
    """Separate primary-only scalar/geometry selection; no fitted controls."""
    beta=np.asarray(beta,dtype=np.float64);require(beta.shape==(11,) and np.isfinite(beta).all(),'Exact final geometry11')
    owners={s['source_id']:[] for s in observations}
    for pair in pairs:
        require(pair['source_id'] in owners,'Unexpected candidate owner');owners[pair['source_id']].append(pair)
    outputs=[];used=set()
    for s in observations:
        pool=s['pool'];g=np.stack([geometry(b,s['width'],s['height']) for b in pool]);geometric=(g-g[0])[:,1:12]@beta
        visual=np.full(len(pool),np.nan);raw_owners={}
        for pair in owners[s['source_id']]:
            i=pair['candidate_index'];require(type(i)==int and 0<=i<len(pool) and i not in raw_owners,'Exact unique native pool')
            f,r=values[pair['first_id']],values[pair['reverse_id']]
            require(all(v['source_id']==s['source_id'] and v['source_sha256']==s['source_sha256'] for v in (f,r)),'Accepted scalar owner')
            require((i==0 and pair['same_crop'] is True and pair['first_id']==pair['reverse_id']) or
                (i>0 and pair['same_crop'] is False and pair['first_id']!=pair['reverse_id']),'Exact same/dual-order policy')
            visual[i]=.5*(float(f['CPU_value'])-float(r['CPU_value']));raw_owners[i]=[pair['first_id'],pair['reverse_id']];used.update(raw_owners[i])
        gains=visual+geometric
        require(set(raw_owners)==set(range(len(pool))) and np.isfinite(gains).all() and gains[0]==0.,'Complete finite exact BASE-zero gains')
        i=max(range(len(pool)),key=lambda j:(float(gains[j]),j==0,-j))
        outputs.append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],predicted_gains=dict(UTILITY=gains.tolist()),
            choices=dict(UTILITY=i),selected_native_box=pool[i],raw_pair_owners={str(k):v for k,v in raw_owners.items()}))
    require(used==set(values),'All accepted scalar outputs must be used')
    return outputs


def patch_protected(base,observations,choices,legal):
    require(len(base)==len({r['video_id'] for r in base})==426 and {r['video_id'] for r in base}=={str(i) for i in range(426)},'Complete protected426')
    result=copy.deepcopy(base);byvideo={r['video_id']:r for r in result};before={};after={}
    for r in result:
        require(r['predictions'],'Protected nonempty source')
        r['model_params_b']=PARAMETERS/1e9
        previous=-1
        for p in r['predictions']:
            require(type(p['frame'])==int and p['frame']>previous,'Unique ordered original nativeframes')
            previous=p['frame'];before[r['video_id'],p['frame']]=copy.deepcopy(p['bboxes']);after[r['video_id'],p['frame']]=p
    require(len(before)==123506,'Exact protected40.47 frame collection')
    sources={s['source_id']:s for s in observations}
    require(len(sources)==len(observations)==len(choices) and {c['source_id'] for c in choices}==set(sources),'Exact frozen observation policy scope')
    changed=[];seen=set()
    for choice in choices:
        s=sources[choice['source_id']];vid=s['video_id'];frame=s['native_ordinal'];key=(vid,frame)
        require(s['source_id']=='official:%s:native:%d'%(vid,frame) and key in before and key not in seen
            and byvideo[vid]['targetRatioWH']==[16,9] and s['targetRatioWH']==[16,9]
            and s['source_sha256']==choice['source_sha256'] and s['baseline_box']==before[key] and s['pool'][0]==before[key]
            and type(s['observation_index'])==int and s['observation_index']%2==0,'Exact native even-observation subset and protected BASE')
        seen.add(key);g=choice['predicted_gains']['UTILITY']
        require(len(g)==len(s['pool']) and all(isinstance(v,(int,float)) and not isinstance(v,bool) and np.isfinite(v) for v in g) and g[0]==0.,'Complete finite accepted gains')
        index=max(range(len(g)),key=lambda i:(g[i],i==0,-i));box=s['pool'][index]
        require(index==choice['choices']['UTILITY'] and box==choice['selected_native_box']
            and legal(box,s['width'],s['height']),'Independent chosen native pool index/legality')
        after[key]['bboxes']=list(box)
        if box!=before[key]:changed.append(dict(video_id=vid,source_frame=frame,source_id=s['source_id'],source_sha256=s['source_sha256'],
            native_PTS=s['native_pts_exact'],box_xyw=list(box),old_box_xyw=before[key],candidate_index=index,
            pair_owners=choice['raw_pair_owners'][str(index)],spatial_source=NEW_SOURCE,legal=True))
    actual={(r['video_id'],p['frame']):p['bboxes'] for r in result for p in r['predictions']}
    require(actual.keys()==before.keys() and len(actual)==123506,'No new/deleted/changed native frame identity')
    require({k for k in actual if actual[k]!=before[k]}=={(p['video_id'],p['source_frame']) for p in changed},'No change outside exact registered observations')
    require(all(actual[k]==v for k,v in before.items() if byvideo[k[0]]['targetRatioWH']==[9,16]),'All9:16 boxes protected')
    return result,changed


def module(reference,name):
    spec=importlib.util.spec_from_file_location(name,bound(reference));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def run(root,rp):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only conditional new package')
    reg=read(rp);require(reg['schema']=='UTILITY_EXACT_OBSERVATION_PACKAGE_V64' and bound(reg['code'])==Path(__file__).resolve(),'Explicit utility64 registration')
    prod=read(bound(reg['production_admission']));require(prod['production_admitted'] is True and prod['whole426_preserved'] is True,'Actual separate spatial production admission')
    qualities=[]
    for name,status in [('profile_quality','PASS_UTILITY_RESIZED20_PROFILE_ONLY'),('confirm_quality','PASS_UTILITY_RESIZED19_CONFIRM_ONLY')]:
        q=read(bound(reg[name]));require(q['status']==status and q['quality']['admitted'] is True,'Actual fixed qualified external scope')
        qualities.append(q)
    rules=read(bound(reg['official_rule_check']));require(rules['status']=='PASS_CURRENT_UTILITY_PACKAGE_RULE_SCOPE','Current reviewed rules before package')
    qa=read(bound(reg['production_output_acceptance']));require(qa['status']=='PASS_UTILITY59_FIRST_OUTPUT_QA' and qa['scope']=='production','All first production output QA')
    prepared=read(bound(reg['prepared']));gate=read(bound(reg['input_acceptance']))
    require(gate['status']=='PASS_UTILITY61_ALL_SELECTED_OBSERVATIONS_FIRST_CPU_QA' and gate['prepared']==reg['prepared']
        and prepared['selection']=='OBS_INDEX_EVEN' and prepared['official_source_count']==426,'All actual first production inputs complete')
    top=read(bound(qa['top_completion']));require(top['inventory']['pipeline']==PARAMETERS and top['new_optimizer_updates']==0
        and top['training_completion']==qa['training_completion'] and qa['adapter_weights']==top['adapter_weights']
        and qa['value_weights']==top['value_weights'],'Actual model identity/count and immutable output weights')
    gpu=read(bound(qa['registration']))
    require(top['GPU_registration']==qa['registration'] and top['prepared']==reg['prepared']
        and top['input_acceptance']==reg['input_acceptance']
        and all(gpu[k]==reg[k] for k in ('prepared','input_acceptance','production_admission'))
        and gpu['profile_quality_admission']==reg['profile_quality'] and gpu['confirm_quality_admission']==reg['confirm_quality']
        and all(v['adapter_weights']==qa['adapter_weights'] and v['value_weights']==qa['value_weights'] for v in [prod,prepared,*qualities])
        and prod['expected_sources']==prod['observations']==prepared['sources']
        and prod['official_source_count']==prepared['official_source_count']==426,'One exact GPU/input/pool/quality/weight lineage')
    resource=read(bound(qa['resource']));record=resource['record']
    ledger=[json.loads(s) for s in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
        if s.strip() and json.loads(s).get('name')==gpu['GPU_job']]
    require(ledger==[record] and record['name']==gpu['GPU_job'] and record['status']=='completed' and record['exit_code']==0,
        'Unique actual same production GPU terminal')
    baseline=bound(reg['protected_baseline']);require(reg['protected_baseline']['sha256']==BASELINE_SHA,'Protected40.47 only')
    with zipfile.ZipFile(baseline) as z:base=[json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s]
    # The original complete field and its accepted baseline composition are
    # inherited, not recomputed or labelled as newly inferred.
    inherited=read(bound(reg['inherited_baseline_completion']));require(inherited['sha256']==BASELINE_SHA and inherited['frames']==123506 and inherited['independent11strict'] is True,'Adopt original accepted baseline composition')
    field=read(bound(reg['source_field_inputs']))
    for source in field['source_field_files'].values():bound(source)
    bound(field['source_manifest']);bound(field['source_clocks'])
    catalog=read(bound(prepared['source_catalog']));plan=read(bound(prepared['case_plan']))
    require(plan['GT_used_for_input_or_pair_choice'] is False,'Frozen label-free candidate scope')
    policy33=module(reg['policy33_code'],'_utility64_original_geometry')
    import torch
    state=torch.load(bound(qa['value_weights']),map_location='cpu',weights_only=True)
    beta=state['geometry_beta'].double().numpy()
    values={p['id']:dict(source_id=p['source_id'],source_sha256=p['source_sha256'],CPU_value=p['CPU_value']) for p in qa['predictions']}
    choices=replay_choices(catalog['sources'],plan['pair_index'],values,beta,policy33.geometry_features)
    previous=read(bound(reg['production_policy']));require(previous['output_acceptance']==reg['production_output_acceptance'] and previous['GT_read'] is False,'Same actual CPU-only policy receipt')
    prior={p['source_id']:p for p in previous['predictions']};require(set(prior)=={s['source_id'] for s in catalog['sources']},'Exact policy observation scope')
    for choice in choices:
        p=prior[choice['source_id']]
        require(choice['choices']['UTILITY']==p['choices']['UTILITY'] and choice['selected_native_box']==p['selected_native_box']
            and np.allclose(choice['predicted_gains']['UTILITY'],p['predicted_gains']['UTILITY'],rtol=0.,atol=1e-12),
            'Independent primary-only numerical policy replay differs')
    proof=dict(sources=len(choices),independent_scalar_policy_replay=True,invalid=0,selfzero=len(choices),old_controls_used_for_prediction=False)
    geometry=module(reg['geometry31_code'],'_utility64_legality31')
    predictions,changed=patch_protected(base,catalog['sources'],choices,geometry.legal)
    digest=canonical(predictions)
    if not changed or digest==canonical(base) or digest in reg['historical_canonical_sha256']:
        save(root/'utility_package_no_new_candidate_STOP_64.json',dict(status='STOP_VALID_PRODUCTION_WITHOUT_NEW_DISTINCT_CANDIDATE',
            utc=utc(),changed_boxes=len(changed),canonical_sha256=digest,source_QA=reg['production_output_acceptance'],
            registration=ref(rp),no_execution_failure=True,new_ZIP=0,baseline_not_renamed=True))
        return
    oldprovenance=lines(bound(reg['inherited_provenance']));prov={(p['video_id'],p['source_frame']):p for p in oldprovenance}
    actual={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
    require(len(prov)==len(oldprovenance)==123506 and {k:p['box_xyw'] for k,p in prov.items()}==actual,'Exact inherited baseline provenance')
    for row in changed:prov[row['video_id'],row['source_frame']]=row
    out=root/'utility_package_64';out.mkdir(exist_ok=False)
    try:
        write_lines(out/'predictions.jsonl',predictions);write_lines(out/'provenance.jsonl',[prov[k] for k in sorted(prov)])
        save(out/'complete_source_field_overlay.json',dict(schema='INHERITED_COMPLETE_NATIVE_FIELD_PLUS_EXACT_OBSERVATION_OVERLAY_V64',
            inherited_source_field_inputs=reg['source_field_inputs'],inherited_baseline=reg['protected_baseline'],
            overlay=changed,complete_native_domain_inherited=True,no_new_interpolation=True,all_other_native_frame_boxes_inherited=True,
            original_native_PTS_unchanged=True,official_sources=426,proof=proof,policy_raw_QA=reg['production_output_acceptance']))
        pending=out/'candidate_UTILITY_EXACT_OBSERVATION.PENDING.zip'
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(out/'predictions.jsonl','predictions.jsonl')
        original=bound(reg['original_independent_validator']);text=original.read_text();needle='{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}'
        require(text.count(needle)==1,'Exact original strict validator source allowlist')
        validator=out/'independent_validate_utility64.py';validator.write_text(text.replace(needle,'{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION", "UTILITY_EXACT_NATIVE_OBSERVATION"}'))
        argv=[sys.executable,'-B',str(validator),'--strict-loader-root',reg['strict_loader_root'],'--metadata',str(bound(reg['metadata'])),
            '--selected',str(bound(reg['inherited_selected'])),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(pending),'--report',str(out/'independent11.json')]
        subprocess.run(argv,check=True,stdout=subprocess.DEVNULL)
        require(len(read(out/'independent11.json')['checks'])==11 and all(read(out/'independent11.json')['checks'].values()),'Independent11strict actual pass')
        with zipfile.ZipFile(pending) as z:
            require(z.namelist()==['predictions.jsonl'] and z.testzip() is None
                and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==ref(out/'predictions.jsonl')['sha256'],'Single member/CRC/member SHA')
        final=out/'candidate_UTILITY_EXACT_OBSERVATION.zip';pending.rename(final)
        save(out/'completion.json',dict(status='PASS_ENGINEERING_EXTERNAL_STATIC_QUALIFIED_ONLINE_UNKNOWN',zip=str(final),
            bytes=final.stat().st_size,sha256=ref(final)['sha256'],member_sha256=ref(out/'predictions.jsonl')['sha256'],canonical_sha256=digest,
            official_sources=426,nonempty_sources=426,native_frames=123506,added=0,removed=0,changed_boxes=len(changed),
            changed_video_sources=len({c['video_id'] for c in changed}),all_9_16_unchanged=True,all_outside_exact_scope_unchanged=True,
            complete_source_field=ref(out/'complete_source_field_overlay.json'),actual_all_parameters=PARAMETERS,independent11strict=True,
            registration=ref(rp),official_score='UNKNOWN',automatic_website_submission=False))
    except BaseException as e:
        save(out/'failure.json',dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),preserve_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.registration)
