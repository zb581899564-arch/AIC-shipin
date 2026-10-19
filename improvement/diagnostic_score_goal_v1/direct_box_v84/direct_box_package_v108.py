"""Conditional CPU package108 for qualified final105; never execute a model.

CLI --root ROOT --registration ROOT/direct_box_package_registration_108.json.
See DIRECT_BOX_PACKAGE_CONTRACT_108.md for the exact registration contract.
Only accepted109 metadata is replayed. Original raw first QA and inherited
complete spatial-field computation are adopted, never repeated.
"""
import argparse
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
import zipfile

SCHEMA='DIRECT_BOX105_EXACT_NATIVE_PACKAGE_V108'
PARAMETERS=8790237452
BASELINE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
SOURCE='DIRECT_BOX105_EXACT_NATIVE_OBSERVATION'
ARMS=('DIRECT','ANCHORED_HALF')
NATIVE_PASS='PASS_DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS'
CONFIRM_PASS='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS'
FORMAL_QA='PASS_DIRECT_BOX109_FORMAL_FIRST_RAW_HEAD_PTS_CPU_QA'


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def ref(path):
    p=Path(path).resolve();return dict(path=str(p),sha256=file_sha(p))


def reference(value):
    require(isinstance(value,dict) and isinstance(value.get('path'),str)
        and Path(value['path']).is_absolute() and re.fullmatch('[0-9a-f]{64}',value.get('sha256','')),
        'Explicit absolute path/SHA256 reference required')
    return value


def bound(value):
    reference(value);p=Path(value['path']).resolve()
    require(p.is_file() and file_sha(p)==value['sha256'],'Missing or changed bound artifact: '+str(p));return p


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def load(value):return read(bound(value))
def lines(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def write_lines(path,rows):
    with Path(path).open('x',encoding='utf-8') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
        f.flush();os.fsync(f.fileno())


def canonical(rows):
    return digest([{k:r[k] for k in ('video_id','targetRatioWH','predictions')}
        for r in sorted(rows,key=lambda r:r['video_id'])])


def history_digests(registry):
    """Adopt explicit existing metadata only; do not open old ZIP/archive paths."""
    values=registry.get('canonical_sha256',registry.get('canonical_receipts'))
    require(isinstance(values,(dict,list)) and values and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in values),
        'Nonempty SHA-bound historical canonical registry required')
    return set(values)


def qualified_arms(native,confirm,reg):
    require(native['status']==NATIVE_PASS and confirm['status']==CONFIRM_PASS,
        'Only actual final105 native20 and fixed19 quality may qualify package108')
    for q in (native,confirm):
        require(q['fixed_final_checkpoint'] is True and q['new_updates']==778
            and q['total_adopted_plus_new_updates']==798 and q['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS',
            'Actual final778-new normalized-hidden model required')
        require(all(q[k]==reg[k] for k in ('training_completion','adapter_weights','head_weights')),'Quality/weights identity')
        names=q['admitted_arm_names']
        require(names and len(names)==len(set(names)) and set(names)<=set(ARMS)
            and all(q['arms'][a]['quality']['admitted'] is True for a in names),'Only explicitly qualified arms')
    require(confirm['native20_quality_result']==reg['native20_quality_result']
        and confirm['frozen_admitted_arm_names']==native['admitted_arm_names'],'Same frozen native20 shortlist evaluated on19')
    expected=[a for a in native['admitted_arm_names'] if a in confirm['admitted_arm_names']]
    require(expected and reg['admitted_arm_names']==expected,'Exact same-arm qualification intersection; no added arm')
    return expected


def validate_domain(domain,sources,expected):
    selected=domain['selected_D'];all_d=domain['all_D']
    require(domain['selection']=='OBS_INDEX_EVEN' and domain['protected_baseline_sha256']==BASELINE_SHA
        and domain['official_source_count']==426 and selected==sources
        and domain['selected_D_count']==len(selected)==expected and domain['all_D_count']==len(all_d)
        and domain['selected_D_sha256']==digest(selected) and domain['all_D_sha256']==digest(all_d)
        and domain['no_nearest_or_interpolation'] is True,'Exact predeclared allD/selectedD metadata')
    identity=lambda s:tuple(s[k] for k in ('video_id','source_sha256','native_ordinal','observation_index','native_pts_exact'))
    require(len({identity(s) for s in all_d})==len(all_d)
        and {identity(s) for s in selected}=={identity(s) for s in all_d if s['observation_index']%2==0}
        and len({identity(s) for s in selected})==len(selected),'Exact even original observation intersection, no enlargement')
    require(selected==sorted(selected,key=lambda s:(s['source_sha256'],s['video_id'],s['native_ordinal']))
        and domain['pilot_source_ids']==[s['source_id'] for s in selected[:32]]
        and domain['remaining_source_ids']==[s['source_id'] for s in selected[32:]]
        and domain['affected_video_count']==len({s['video_id'] for s in sources}), 'Fixed immutable domain ordering/counts')


def replay_boxes(sources,predictions,math):
    """Decode accepted persisted GPU-F32 head values copied to CPU metadata.

    CPU_head_raw64 is the independent linear QA value, not the native policy
    input: replacing F32 head values by it can cross an integer boundary.
    """
    require(len(sources)==len(predictions)>0 and len({p['source_id'] for p in predictions})==len(predictions), 'Exact accepted owners')
    by={p['source_id']:p for p in predictions};result={}
    for s in sources:
        p=by[s['source_id']];require(p['source_sha256']==s['source_sha256'],'Accepted head owner')
        direct=math.decode_native(p['GPU_head_raw'],s['width'],s['height'])
        boxes=dict(DIRECT=direct,ANCHORED_HALF=math.blend_native(s['baseline_box'],direct,s['width'],s['height']))
        require(boxes==p['native_boxes'],'Independent native decoder/half arm differs from accepted109 metadata')
        result[s['source_id']]=boxes
    require(set(by)==set(result),'Unexpected accepted owner');return result


def patch_protected(base,sources,boxes,*,arm,clocks,legal):
    require(arm in ARMS and len(base)==len({r['video_id'] for r in base})==426
        and {r['video_id'] for r in base}=={str(i) for i in range(426)},'Complete protected426')
    out=copy.deepcopy(base);videos={r['video_id']:r for r in out};before={};after={}
    for r in out:
        require(r['predictions'] and r['targetRatioWH'] in ([16,9],[9,16]),'Protected nonempty valid-ratio source')
        r['model_params_b']=PARAMETERS/1e9;previous=-1
        for p in r['predictions']:
            n=p['frame'];require(type(n)==int and n>previous,'Unique ordered nativeframes');previous=n
            before[r['video_id'],n]=copy.deepcopy(p['bboxes']);after[r['video_id'],n]=p
    require(len(before)==123506,'Exact protected123506 selected nativeframes')
    require(len({s['source_id'] for s in sources})==len(sources) and set(boxes)=={s['source_id'] for s in sources},'Exact observation owners')
    changes=[];seen=set()
    for s in sources:
        vid=s['video_id'];n=s['native_ordinal'];key=(vid,n);clock=clocks[vid];pts=clock['normalized_exact_pts']
        require(type(n)==int and n>=0 and key in before and key not in seen
            and s['source_id']=='official:%s:native:%d'%(vid,n) and videos[vid]['targetRatioWH']==s['targetRatioWH']==[16,9]
            and s['baseline_box']==before[key] and s['original_BASE_observed'] is True
            and type(s['observation_index'])==int and s['observation_index']>=0 and s['observation_index']%2==0,
            'Only exact native16 even observations selected in protected40.47')
        require(clock['video_id']==vid and clock['source_sha256']==s['source_sha256']
            and clock['n_frames']==len(pts) and n<len(pts) and Fraction(s['native_pts_exact'])==Fraction(pts[n]), 'Exact source/native PTS clock')
        seen.add(key);box=boxes[s['source_id']][arm]
        require(legal(s['baseline_box'],s['width'],s['height']) and legal(box,s['width'],s['height']),'Original/new native box legal')
        after[key]['bboxes']=list(box)
        if box!=before[key]:changes.append(dict(video_id=vid,native_ordinal=n,source_id=s['source_id'],source_sha256=s['source_sha256'],
            native_pts_exact=s['native_pts_exact'],old_box=before[key],box_xyw=list(box),arm=arm))
    actual={(r['video_id'],p['frame']):p['bboxes'] for r in out for p in r['predictions']}
    require(actual.keys()==before.keys() and {k for k in actual if actual[k]!=before[k]}=={(p['video_id'],p['native_ordinal']) for p in changes},'All times and outsideD preserved')
    require(all(actual[k]==v for k,v in before.items() if videos[k[0]]['targetRatioWH']==[9,16]),'All9:16 boxes preserved')
    return out,changes


def replace_provenance(original,base,changes,*,arm,qa_ref,proof_ref):
    actual={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
    rows={(p['video_id'],p['source_frame']):copy.deepcopy(p) for p in original}
    require(len(rows)==len(original)==123506 and {k:p['box_xyw'] for k,p in rows.items()}==actual,'Exact inherited provenance full domain/boxes')
    for c in changes:
        k=c['video_id'],c['native_ordinal']
        rows[k]=dict(video_id=c['video_id'],source_frame=c['native_ordinal'],source_id=c['source_id'],source_sha256=c['source_sha256'],
            native_PTS=c['native_pts_exact'],old_box_xyw=c['old_box'],box_xyw=c['box_xyw'],output_arm=arm,
            spatial_source=SOURCE,legal=True,accepted_raw_QA=qa_ref,independent_overlay_proof=proof_ref)
    return [rows[k] for k in sorted(rows)]


def strict_validator_text(text):
    needle='{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}'
    require(text.count(needle)==1,'Exact frozen original validator allowlist')
    return text.replace(needle,'{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION", "'+SOURCE+'"}')


def disposition(rows,base,changes,historical,previous):
    value=canonical(rows)
    if not changes or value==canonical(base):return 'STOP_ZERO_DISTINCT_BOX_CHANGE',value
    if value in historical:return 'STOP_HISTORICAL_CANONICAL_DUPLICATE',value
    if value in previous:return 'STOP_SAME_AS_OTHER_QUALIFIED_ARM',value
    return 'NEW_DISTINCT_CANDIDATE',value


def module(reference_,name):
    spec=importlib.util.spec_from_file_location(name,bound(reference_));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def validate_lineage(reg,qa,gpu,done,integrity,prepared,gate,trained,production):
    common=('training_completion','adapter_weights','head_weights','admitted_arm_names')
    require(qa['status']==FORMAL_QA and qa['phase']=='formal' and qa['registration']==reg['formal_GPU_registration']
        and qa['completion']==reg['formal_completion'] and qa['model_integrity']==reg['formal_model_integrity']
        and qa['input_prepared']==reg['prepared'] and qa['input_acceptance']==reg['input_acceptance']
        and qa['resource']==reg['resource_receipt'] and qa['native20_quality_result']==reg['native20_quality_result']
        and qa['confirm19_quality_result']==reg['confirm19_quality_result'],'Actual formal109 QA refs')
    require(all(all(v[k]==reg[k] for k in common) for v in (qa,gpu,done,prepared,production)), 'One qualified model/arm lineage')
    require(gpu['schema']=='FROZEN_DIRECT_BOX107_L2_SINGLE_IMAGE_INFERENCE' and gpu['phase']=='formal'
        and gpu['prepared']==reg['prepared'] and gpu['input_acceptance']==reg['input_acceptance']
        and gpu['protected_baseline']==reg['protected_baseline'] and gpu['selection']=='OBS_INDEX_EVEN'
        and gpu['production_admitted'] is True and gpu['whole426_preserved'] is True
        and gpu['native20_quality_result']==reg['native20_quality_result'] and gpu['confirm19_quality_result']==reg['confirm19_quality_result'], 'Actual formal107 scope admission')
    require(done['status']=='COMPLETE_DIRECT_BOX107_FORMAL_RAW_NOT_QUALITY' and done['GPU_registration']==reg['formal_GPU_registration']
        and done['input_prepared']==reg['prepared'] and done['input_acceptance']==reg['input_acceptance']
        and done['CPU_registration']==gpu['CPU_registration'] and done['phase']=='formal' and done['model_role']=='DIRECT_BOX105_formal'
        and done['targets_read'] is False and done['no_training'] is True and done['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS', 'Complete readonly107 model output')
    require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY' and trained['GPU_registration']==gpu['frozen_GPU105_registration']
        and trained['completed_updates']==778 and trained['successful_micro']==trained['actual_training_forwards']==3112
        and trained['original_successful_updates']==20 and trained['original_successful_forwards']==88 and trained['optimizer_reset'] is True
        and trained['total_adopted_plus_new_updates']==798 and trained['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS'
        and trained['adapter_reload_all288_exact'] is True and trained['head_reload_all2_exact'] is True
        and all(trained[k]==reg[k] for k in ('adapter_weights','head_weights')), 'Actual complete105 final778 checkpoint')
    require(integrity['status']=='PASS_DIRECT_BOX107_READONLY_MODEL_BYTE_IDENTITY' and integrity['registration']==reg['formal_GPU_registration']
        and integrity['completion']==reg['formal_completion'] and integrity['training_completion']==reg['training_completion']
        and integrity['inventory']==trained['inventory'] and integrity['base_fingerprint']==trained['base_fingerprint']
        and integrity['inventory']['pipeline']==PARAMETERS and integrity['inventory']['resident']==8774803699
        and all(integrity[k] is True for k in ('adapter_all288_exact','head_all2_exact','all_weights_frozen','no_training'))
        and integrity['targets_read'] is False,'Readonly byte identity and actual whole pipeline parameter count')
    require(prepared['schema']=='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106' and prepared['phase']==gate['phase']=='formal'
        and prepared['CPU_targets'] is None and prepared['selection']=='OBS_INDEX_EVEN'
        and prepared['protected_baseline']==reg['protected_baseline'] and gate['status']=='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA'
        and gate['registration']==gpu['CPU_registration'] and gate['prepared']==reg['prepared']
        and prepared['execution_entries']==prepared['inference_inputs'] and prepared['adopted_success']=={}
        and gate['new_original_decode']==gate['old_source_processor_repeated']==gate['model_calls']==0,'Actual complete106 GT-free first inputs')
    count=prepared['sources'];entries=prepared['inference_inputs']
    require(count==gate['sources']==gate['inputs']==done['sources']==done['expected_inputs']==gpu['expected_inputs']==gpu['expected_sources']==len(entries)==len(done['entries'])==len(qa['predictions'])
        and count>0 and len({e['id'] for e in entries})==len({e['source_id'] for e in entries})==count, 'D owners distinct from official426')
    require(all(all(x[k]==y[k] for k in ('id','source_id','source_sha256','input')) for x,y in zip(entries,done['entries']))
        and all(all(x[k]==y[k] for k in ('id','source_id','source_sha256','input')) for x,y in zip(entries,qa['predictions'])), 'Ordered complete input/raw/QA owners')
    require(done['actual_forward_calls']==qa['actual_new_forwards'] and done['internal_aliases']==qa['internal_aliases']
        and done['external_adopted']==qa['external_adopted'] and sum(qa[k] for k in ('actual_new_forwards','internal_aliases','external_adopted'))==count,'New/alias/adopted partition')
    require(all(v['official_source_count']==426 for v in (prepared,gate,done,gpu,production))
        and done['whole426_preserved'] is True and done['time_selection_unchanged'] is True
        and production['production_admitted'] is True and production['whole426_preserved'] is True
        and production['time_selection_unchanged'] is True and production['selection']=='OBS_INDEX_EVEN'
        and production['expected_inputs']==count,'Explicit same-scope spatial-only production admission')
    for flag in ('all_times_preserved','all_9_16_preserved','all_D_outside_preserved'):require(qa[flag] is True,'Accepted109 protected scope')


def run(root,registration):
    root=Path(root).resolve();rp=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and rp==root/'direct_box_package_registration_108.json','Explicit CPU-only108 namespace')
    reg=read(rp);require(reg['schema']==SCHEMA and bound(reg['code'])==Path(__file__).resolve(),'Exact new108 code registration')
    require(reg['cost_evidence_refs'] and isinstance(reg['cost_evidence_refs'],list),'Explicit training/pilot/adopted-cost evidence refs')
    for r in reg['cost_evidence_refs']:bound(r)
    deadline=datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))
    require(deadline.tzinfo is not None and datetime.now(timezone.utc)<deadline,'Goal deadline already reached')
    for k in ('adapter_weights','head_weights'):bound(reg[k])
    native=load(reg['native20_quality_result']);confirm=load(reg['confirm19_quality_result']);arms=qualified_arms(native,confirm,reg)
    native_qa=load(native['output_acceptance']);training_resource=native_qa['resource'];bound(training_resource)
    require(native_qa['status']=='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA'
        and native_qa['training_completion']==reg['training_completion']
        and all(native_qa[k]==reg[k] for k in ('adapter_weights','head_weights')),'Adopt original105 native20 first output QA and resource')
    qa=load(reg['formal_output_acceptance']);gpu=load(reg['formal_GPU_registration']);done=load(reg['formal_completion'])
    integrity=load(reg['formal_model_integrity']);prepared=load(reg['prepared']);gate=load(reg['input_acceptance']);trained=load(reg['training_completion'])
    production=load(reg['production_admission']);validate_lineage(reg,qa,gpu,done,integrity,prepared,gate,trained,production)
    rules=load(reg['official_rule_check']);require(rules['status']=='PASS_CURRENT_DIRECT_BOX108_PACKAGE_RULE_SCOPE','Current rule scope explicitly reviewed')
    resource=load(reg['resource_receipt']);ledger=[r for r in lines(bound(reg['gpu_ledger'])) if r.get('name')==gpu['GPU_job']]
    require(ledger==[resource] and resource['name']==gpu['GPU_job'] and resource['status']=='completed' and resource['exit_code']==0,'One exact actual shared GPU terminal/cost record')
    require(reg['protected_baseline']['sha256']==BASELINE_SHA,'Only protected40.47 baseline')
    with zipfile.ZipFile(bound(reg['protected_baseline'])) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None,'Protected ZIP single JSONL/CRC')
        base=[json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s]
    inherited=load(reg['inherited_baseline_completion'])
    require(inherited['sha256']==BASELINE_SHA and inherited['frames']==123506 and inherited['records']==426 and inherited['independent11strict'] is True,'Adopt accepted baseline composition')
    field=load(reg['source_field_inputs'])
    require(len(field['source_field_files'])==4,'Inherited complete four-file source spatial field')
    for r in [*field['source_field_files'].values(),field['source_manifest'],field['source_clocks']]:reference(r)
    # Those original successful field files are referenced, not recomputed/rehashed.
    history=history_digests(load(reg['historical_registry']))
    catalog=load(prepared['source_catalog']);sources=catalog['sources'];domain=load(prepared['domain']);validate_domain(domain,sources,prepared['sources'])
    metadata=load(reg['metadata']);native_records={r['video_id']:r for r in metadata['records']}
    require(len(native_records)==len(metadata['records'])==426 and set(native_records)=={str(i) for i in range(426)},'Original complete426 native metadata')
    for s in sources:
        record=native_records[s['video_id']]
        require(all(s[k]==record[k] for k in ('source_sha256','width','height','targetRatioWH'))
            and s['targetRatioWH']==[16,9],'Registered observation retains original video SHA/dimensions/ratio')
    require(qa['domain']==prepared['domain'] and qa['protected_baseline']==reg['protected_baseline']
        and qa['official_source_count']==426 and qa['affected_video_count']==domain['affected_video_count']
        and set(qa['arm_overlays'])==set(arms),'Accepted109 exact domain and arms')
    actual_videos=sorted({s['video_id'] for s in sources})
    require(done['affected_video_ids']==actual_videos and done['affected_video_count']==gpu['affected_video_count']==domain['affected_video_count']
        and gpu['expected_affected_videos']==len(actual_videos) and set(gpu['affected_video_ids'])==set(actual_videos),'Actual video scope without obsolete303 limit')
    clocks={};clockrefs={}
    for s in sources:
        vid=s['video_id']
        if vid not in clocks:
            clocks[vid]=load(s['clock']);clockrefs[vid]=s['clock'];points=clocks[vid]['normalized_exact_pts']
            require(clocks[vid]['n_frames']==native_records[vid]['n_frames']==len(points)
                and Fraction(points[0])==0 and all(Fraction(a)<Fraction(b) for a,b in zip(points,points[1:])),'Strict exact native PTS')
        require(s['clock']==clockrefs[vid],'One clock per original video')
    decoder=module(reg['frozen_math84_code'],'_direct108_native_decoder')
    require(gpu['frozen_math84_code']==reg['frozen_math84_code'],'Same original fixed native decoder')
    boxes=replay_boxes(sources,qa['predictions'],decoder)
    oldprov=lines(bound(reg['inherited_provenance']));bound(reg['inherited_selected']);bound(reg['metadata'])
    loader=Path(reg['strict_loader_root']).resolve();loader_refs=reg['strict_loader_code_refs']
    require(loader_refs and all(bound(r).is_relative_to(loader) for r in loader_refs),'Bound original strict-loader code set')
    validator_text=strict_validator_text(bound(reg['original_independent_validator']).read_text(encoding='utf-8'))
    out=root/'direct_box_packages_108';out.mkdir(exist_ok=False);completed=[];stopped=[];newdigests=set()
    try:
        for arm in arms:
            require(datetime.now(timezone.utc)<deadline,'Deadline before next package')
            predictions,changes=patch_protected(base,sources,boxes,arm=arm,clocks=clocks,legal=decoder.legal_native)
            overlay=load(qa['arm_overlays'][arm]);prior=lines(bound(overlay['predictions']))
            require(overlay['status']=='PASS_DIRECT_BOX109_EXACT_NATIVE_SPATIAL_OVERLAY_ENGINEERING_ONLY'
                and overlay['arm']==arm and overlay['changes']==changes and overlay['changed_boxes']==len(changes)
                and overlay['changed_video_sources']==len({c['video_id'] for c in changes}) and overlay['official_sources']==426
                and overlay['native_frames']==123506 and overlay['added']==overlay['removed']==0 and overlay['new_interpolation'] is False
                and all(overlay[k] is True for k in ('all_times_preserved','all_9_16_preserved','all_D_outside_preserved'))
                and overlay['raw_completion']==reg['formal_completion'] and overlay['domain']==prepared['domain']
                and overlay['protected_baseline']==reg['protected_baseline']
                and all(overlay[k]==reg[k] for k in ('training_completion','adapter_weights','head_weights'))
                and canonical(prior)==canonical(predictions),'Independent108 full426 overlay replay equals109 accepted proof')
            state,sha=disposition(predictions,base,changes,history,newdigests)
            if state!='NEW_DISTINCT_CANDIDATE':
                stop=dict(arm=arm,status=state,changed_boxes=len(changes),canonical_sha256=sha,new_ZIP=0,baseline_not_renamed=True,no_execution_failure=True)
                save(out/(arm+'_STOP.json'),stop);stopped.append(stop);continue
            armout=out/arm;armout.mkdir(exist_ok=False)
            provenance=replace_provenance(oldprov,base,changes,arm=arm,qa_ref=reg['formal_output_acceptance'],proof_ref=qa['arm_overlays'][arm])
            write_lines(armout/'predictions.jsonl',predictions);write_lines(armout/'provenance.jsonl',provenance)
            save(armout/'complete_source_field_overlay.json',dict(schema='INHERITED_COMPLETE_NATIVE_FIELD_PLUS_DIRECT105_OVERLAY_V108',
                inherited_source_field_inputs=reg['source_field_inputs'],inherited_baseline=reg['protected_baseline'],domain=prepared['domain'],overlay=changes,
                complete_native_domain_inherited=True,original_native_PTS_unchanged=True,no_new_interpolation=True,all_other_native_frame_boxes_inherited=True,
                original_field_success_adopted_not_recomputed=True,official_sources=426,accepted_raw_QA=reg['formal_output_acceptance']))
            validator=armout/'independent_validate_direct108.py'
            with validator.open('x',encoding='utf-8') as f:f.write(validator_text)
            pending=armout/('candidate_DIRECT_BOX105_'+arm+'.PENDING.zip')
            with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(armout/'predictions.jsonl','predictions.jsonl')
            argv=[sys.executable,'-B',str(validator),'--strict-loader-root',str(loader),'--metadata',str(bound(reg['metadata'])),
                '--selected',str(bound(reg['inherited_selected'])),'--predictions',str(armout/'predictions.jsonl'),
                '--provenance',str(armout/'provenance.jsonl'),'--zip',str(pending),'--report',str(armout/'independent11.json')]
            subprocess.run(argv,check=True,timeout=max(1,int((deadline-datetime.now(timezone.utc)).total_seconds())),stdout=subprocess.DEVNULL)
            strict=read(armout/'independent11.json');require(len(strict['checks'])==11 and all(v is True for v in strict['checks'].values()),'Independent11strict actual PASS')
            with zipfile.ZipFile(pending) as z:
                require(z.namelist()==['predictions.jsonl'] and z.testzip() is None
                    and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==file_sha(armout/'predictions.jsonl'),'Single member/CRC/memberSHA')
            require(datetime.now(timezone.utc)<deadline,'Deadline before releasing final ZIP')
            final=armout/('candidate_DIRECT_BOX105_'+arm+'.zip');require(not final.exists(),'Exclusive final ZIP');pending.rename(final)
            receipt=dict(status='PASS_DIRECT_BOX108_ENGINEERING_STATIC_QUALIFIED_OFFICIAL_UNKNOWN',arm=arm,zip=ref(final),bytes=final.stat().st_size,
                member_sha256=file_sha(armout/'predictions.jsonl'),canonical_sha256=sha,official_sources=426,nonempty_sources=426,native_frames=123506,
                added=0,removed=0,changed_boxes=len(changes),changed_video_sources=len({c['video_id'] for c in changes}),all_9_16_unchanged=True,
                all_outside_exact_scope_unchanged=True,actual_all_parameters=PARAMETERS,independent11strict=True,source_tag=SOURCE,
                complete_source_field=ref(armout/'complete_source_field_overlay.json'),registration=ref(rp),training_completion=reg['training_completion'],
                adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],native20_quality_result=reg['native20_quality_result'],
                confirm19_quality_result=reg['confirm19_quality_result'],formal_output_acceptance=reg['formal_output_acceptance'],
                formal_resource=reg['resource_receipt'],training_resource=training_resource,inherited_baseline=reg['protected_baseline'],
                cost_evidence_refs=reg['cost_evidence_refs'],cost_aggregation='Evidence refs retained; no fabricated aggregate of prior costs',
                historical_registry=reg['historical_registry'],historical_scope='Explicit registered canonical identities; some old deliveries metadata-only',
                new_model_statement='Fresh UTILITY direct-box LoRA plus biased3 head; frozen final105 only; no package-stage model forward',
                new_model_calls=0,new_processor_calls=0,new_decode_calls=0,official_score='UNKNOWN',automatic_website_submission=False)
            save(armout/'completion.json',receipt);completed.append(ref(armout/'completion.json'));newdigests.add(sha)
        save(out/'completion.json',dict(status='COMPLETE_DIRECT_BOX108_CONDITIONAL_PACKAGE_SCOPE' if completed else 'STOP_VALID_DIRECT_BOX108_NO_DISTINCT_PACKAGE',
            registration=ref(rp),packages=completed,stopped_arms=stopped,new_ZIPs=len(completed),model_calls=0,official_score='UNKNOWN',automatic_website_submission=False))
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.registration)
