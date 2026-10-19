"""Explicit conditional artifact registrar; no model/processor/launcher calls.

Every command is separate and exclusive. --plan is an immutable JSON listing
all exact refs/budgets; no latest discovery. This module does nothing on import.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import zipfile

WORK=Path('/home/inspur/aic_video_work')
PLAN='DIRECT_BOX_CONDITIONAL_REGISTRATION_PLAN_V100'
FREEZE='FROZEN_DIRECT_BOX105_NATIVE20_AND_IDENTICAL_SOURCE_ONLY_DOMAIN_V100'
NATIVE='PASS_DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS'
CONFIRM='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS'
BASELINE='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
ARMS=('DIRECT','ANCHORED_HALF')
EXCLUDED='gnmc:test:006575.jpeg'
MODEL_KEYS=('training_completion','adapter_weights','head_weights')
FIXED_KEYS=('registrar_code','deadline_utc','native20_quality_result','frozen_GPU105_registration','frozen_GPU105_code','math_code',
    'frozen_math84_code','frozen_GPU93_code','frozen_math93_code','frozen_review105_code','frozen_review93_code','frozen_review84_code','base_input_code87','preparation_code',
    'GPU_code','conditional_review_code','geometry_code','policy_code','protocol','metadata_builder_code36',
    'original_confirm_prepared','original_confirm_input_acceptance','remaining19_output_acceptance',
    'remaining19_completion','original_confirm_labels','protected_baseline','accepted_production','production_metadata')


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def reference(path):
    p=Path(path).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return dict(path=str(p),sha256=h.hexdigest())


def qualify(actual,*,native=None,native_ref=None):
    """No metric tuning: require exactly the passing predeclared arm subset."""
    require(actual['fixed_final_checkpoint'] is True and actual['new_updates']==778
        and actual['total_adopted_plus_new_updates']==798
        and actual['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS','Only actual105 final778-new identity')
    allowed=list(ARMS) if native is None else list(native['admitted_arm_names'])
    require(set(actual['arms'])==set(allowed),'Every predeclared eligible arm must be reported')
    passing=[a for a in allowed if actual['arms'][a]['quality']['admitted'] is True]
    require(passing and actual['admitted_arm_names']==passing
        and actual['status']==(NATIVE if native is None else CONFIRM),'Actual passing arms in original order, no posthoc switch')
    if native is not None:
        require(actual['native20_quality_result']==native_ref and actual['frozen_admitted_arm_names']==allowed
            and all(actual[k]==native[k] for k in MODEL_KEYS),'Same frozen model and native-qualified arms on actual19')
    return passing


def summary(actual,result_ref):
    return dict({k:actual[k] for k in ('status','admitted_arm_names',*MODEL_KEYS)},result=result_ref)


class Context:
    def __init__(self,root,plan_path):
        self.root=Path(root).resolve();self.plan_ref=reference(plan_path)
        self.plan=self.read(self.plan_ref)
        require(self.plan['schema']==PLAN and self.bind(self.plan['registrar_code'])==Path(__file__).resolve(),
            'Explicit immutable100 registrar plan/code')
        require(self.plan['root']==str(self.root),'Plan belongs to this exact root')
        self.meta=self.root/'direct_box_scope_registration_100'
        self.meta.mkdir(exist_ok=True);self.modules={}

    def bind(self,r):
        require(isinstance(r,dict) and set(r)=={'path','sha256'},'Exact file ref, not directory/latest')
        p=Path(r['path']).resolve()
        require(p.is_relative_to(WORK) and p.is_file() and reference(p)==r,'Bound file missing, changed or outside work root')
        return p

    def read(self,r):return json.loads(self.bind(r).read_text(encoding='utf-8-sig'))

    def write(self,path,value):
        p=Path(path).resolve();require(p.is_relative_to(self.root),'Registration output cannot escape root')
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
        return reference(p)

    def module(self,key):
        r=self.plan[key];p=self.bind(r)
        if key not in self.modules:
            name='_direct100_'+key+'_'+r['sha256'][:12]
            sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location(name,p)
            m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);self.modules[key]=m
        return self.modules[key]

    def budget(self,key):
        b=dict(self.plan['budgets'][key])
        require(type(b['max_seconds']) in (int,float) and b['max_seconds']>0,'Explicit positive time budget')
        require((dt.datetime.fromisoformat(self.plan['deadline_utc'].replace('Z','+00:00'))-
            dt.datetime.now(dt.timezone.utc)).total_seconds()>=b['max_seconds'],'Registered budget fits the remaining Goal deadline')
        b['deadline_utc']=self.plan['deadline_utc']
        return b

    def frozen(self):
        r=self.plan['native20_freeze'];require(self.bind(r)==self.meta/'native20_freeze.json','Explicit original freeze, never latest')
        f=self.read(r)
        require(f['status']==FREEZE and all(self.plan[k]==v for k,v in f['frozen_plan_bindings'].items()),
            'Child plan preserves all original frozen code/model/source/protocol bindings')
        native=self.read(f['native20_quality_result']);qualify(native)
        require(f['native20_quality_summary']==summary(native,f['native20_quality_result']), 'Frozen original native qualification unchanged')
        return f,native


def freeze_native20(c):
    require(not (c.meta/'native20_freeze.json').exists(),'Never repeat an already frozen native20 registration')
    p=c.plan;native=c.read(p['native20_quality_result']);qualify(native)
    trained=c.read(native['training_completion']);old=c.read(p['frozen_GPU105_registration'])
    require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY'
        and trained['completed_updates']==778 and trained['successful_micro']==trained['actual_training_forwards']==3112
        and trained['original_successful_updates']==20 and trained['original_successful_forwards']==88
        and trained['total_adopted_plus_new_updates']==798
        and trained['optimizer_reset'] is True and trained['GPU_registration']==native['registration']==p['frozen_GPU105_registration']
        and trained['original93_progress']==old['original93_progress']
        and trained['adapter_reload_all288_exact'] is True and trained['head_reload_all2_exact'] is True
        and all(native[k]==trained[k] for k in ('adapter_weights','head_weights')),'Actual completed/reloaded final778 and inherited84 identity')
    require(old['GPU_code']==p['frozen_GPU105_code'] and old['math_code']==p['math_code']
        and old['frozen_math84_code']==p['frozen_math84_code'] and old['preparation_code']==p['base_input_code87'],
        'New106 domain must adopt exact successful87 source-only compiler, not old failure qualification')
    require(all(old[k]==p[k] for k in ('frozen_GPU93_code','frozen_math93_code')),
        'Only exact105 inherited pure93 runtime dependencies')
    qa=c.read(native['output_acceptance']);prepared=c.read(old['prepared']);gate=c.read(old['input_acceptance'])
    require(qa['status']=='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA'
        and qa['registration']==p['frozen_GPU105_registration'] and qa['training_completion']==native['training_completion']
        and qa['completion']==trained['TRAINED_completion'] and all(qa[k]==native[k] for k in ('adapter_weights','head_weights'))
        and gate['status']=='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA' and gate['prepared']==old['prepared']
        and gate['registration']==old['CPU_registration'],
        'Adopt actual successful native20 raw/input QA, never repeat it')
    entries=prepared['screen_inputs'];predictions=qa['predictions']
    require(len(entries)==len(predictions)==20 and len({e['source_id'] for e in entries})==len({e['source_sha256'] for e in entries})==20,'Complete historical20 scope')
    requests=[]
    for e,q in zip(entries,predictions):
        require(all(e[k]==q[k] for k in ('id','source_id','source_sha256','input')),'Original screen input/output order')
        request=c.read(e['input'])
        require(all(request[k]==e[k] for k in ('id','source_id','source_sha256'))
            and request['role']=='screen' and request['actual_input_domain']=='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH'
            and request['reference_or_target_in_prompt'] is False and len(request['image_grid_thw'])==1
            and set(request['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'},
            'Already accepted single-source F4 is the106 observation profile')
        requests.append(dict(input=e['input'],source_id=e['source_id'],source_sha256=e['source_sha256'],
            input_signature=request['input_signature'],image_grid_thw=request['image_grid_thw']))
    adapter=c.bind(native['adapter_weights']);directory=Path(trained['adapter_directory']).resolve()
    require(adapter.parent==directory,'Final adapter directory owns exact weights')
    config=reference(directory/'adapter_config.json');c.bind(config)
    for key in ('preparation_code','GPU_code','conditional_review_code','math_code','frozen_math84_code',
        'frozen_review105_code','frozen_review93_code','frozen_review84_code','frozen_GPU93_code','frozen_math93_code','base_input_code87','geometry_code','policy_code','protocol'):
        c.bind(p[key])
    return c.write(c.meta/'native20_freeze.json',dict(status=FREEZE,plan=c.plan_ref,
        frozen_plan_bindings={k:p[k] for k in FIXED_KEYS},
        native20_quality_result=p['native20_quality_result'],native20_quality_summary=summary(native,p['native20_quality_result']),
        **{k:native[k] for k in MODEL_KEYS},adapter_directory=str(directory),adapter_config=config,
        admitted_arm_names=native['admitted_arm_names'],native_output_acceptance=native['output_acceptance'],
        source_only_domain=dict(status='ADOPT_EXACT_ACCEPTED_SOURCE_ONLY_F4_NOT_NEW_PROFILE_TEST',sources=20,
            actual_profile='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',requests=requests,
            accepted_input_gate=old['input_acceptance'],new_model_calls=0,new_first_QA=0,independent_quality_evidence=False,
            compiler87=p['base_input_code87'],compiler106=p['preparation_code']),
        historical_not_blind=True,automatic_prepare=False,automatic_GPU=False))


def base_cpu(c,f,native,phase,source_catalog,targets,budget):
    old=c.read(c.plan['frozen_GPU105_registration'])
    reg=dict(schema='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_CPU_V106',phase=phase,
        preparation_code=c.plan['preparation_code'],base_input_code=c.plan['base_input_code87'],model_config=old['model_config'],
        source_catalog=source_catalog,CPU_targets=targets,native20_quality_result=f['native20_quality_result'],
        native20_quality_summary=f['native20_quality_summary'],protocol=c.plan['protocol'],
        admitted_arm_names=list(f['admitted_arm_names']),**{k:f[k] for k in MODEL_KEYS},**budget)
    require(type(reg['max_new_bytes']) is int and reg['max_new_bytes']>0,'Explicit bounded CPU bytes; no fixed GiB assumption')
    return reg


def register_confirm19(c):
    f,native=c.frozen();p=c.plan
    original=c.read(p['original_confirm_prepared']);entries=original['entries'];rows=[c.read(r) for r in entries]
    gate=c.read(p['original_confirm_input_acceptance']);qa=c.read(p['remaining19_output_acceptance']);done=c.read(p['remaining19_completion'])
    require(len(entries)==20 and rows[0]['item_id']==EXCLUDED
        and gate['status']=='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS'
        and gate['prepared']==p['original_confirm_prepared'] and gate['actual_sources']==20
        and qa['status']=='PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE'
        and qa['completion']==p['remaining19_completion'] and qa['actual_sources']==19
        and done['status']=='COMPLETE_REMAINING19_BASE_AND_VISION_ORIGINAL20_INCOMPLETE'
        and done['first_new_BASE_generations']==done['first_new_vision_readouts']==19
        and len(done['entries'])==len(done['base_calls'])==19,'Exact successful19 and permanently missing first source')
    baseline=[]
    for er,rr,raw in zip(entries[1:],done['entries'],done['base_calls']):
        result=c.read(rr);br=result['original_BASE'];b=c.read(br)
        require(result['source']==er and result['source_sha256']==b['source_sha256']
            and result['item_id']==b['item_id'] and b['original_BASE_raw']==raw,'Exact old19 BASE raw/source order')
        baseline.append(dict(reference=br,value=b))
    geom=c.module('geometry_code');builder=c.module('metadata_builder_code36')
    proofs={r['item_id']:c.read(r['original_proof']) for r in rows[1:]}
    sources=builder.build_confirm_catalog(entries,rows,baseline,proofs,dict(item_id=EXCLUDED,input=entries[0]),geom)
    require([s['original_entry'] for s in sources]==entries[1:]
        and all(s['source_vision']==row['new_vision'] for s,row in zip(sources,rows[1:])), 'Old new_vision refs adopted; no tensor/RGB read')
    # Human references are consumed only after the fixed GT-free19 catalog exists in memory.
    labels=c.read(p['original_confirm_labels']);lookup={r['item_id']:r for r in labels}
    require(len(lookup)==len(labels),'Unique original reference owners')
    math93=c.module('math_code');targets=[]
    for s in sources:
        h=lookup[s['source_id']]
        require(h['role']=='confirm' and h['source_sha256']==s['source_sha256'],'Only original unmodified19 human references')
        original=list(h['reference_xywh']);math93.target_xywh(original,s['width'],s['height'])
        targets.append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],role='confirm',
            width=s['width'],height=s['height'],
            original_reference_xywh=original,reference_modified=False,baseline_index=0,
            candidate_ious=[math93.crop_iou(box,original,s['width'],s['height']) for box in s['pool']]))
    directory=c.meta/'confirm19';require(not directory.exists(),'Never recreate a prior19 registration')
    catalog=c.write(directory/'source_catalog.json',dict(sources=sources,original20_complete=False,historical_not_blind=True,
        excluded_source=EXCLUDED,GT_included=False,original_confirm_prepared=p['original_confirm_prepared']))
    target_ref=c.write(directory/'CPU_targets.json',dict(sources=targets,reference_modified=False,CPU_only=True,historical_not_blind=True))
    reg=base_cpu(c,f,native,'confirm19',catalog,target_ref,c.budget('confirm19_cpu'))
    reg.update(expected_sources=19,original_confirm_prepared=p['original_confirm_prepared'],original20_complete=False,
        original_confirm_input_acceptance=p['original_confirm_input_acceptance'],remaining19_output_acceptance=p['remaining19_output_acceptance'],
        remaining19_completion=p['remaining19_completion'],excluded_source=EXCLUDED,metadata_builder_code36=p['metadata_builder_code36'])
    return c.write(c.root/'direct_box_scope_CPU_registration_106_confirm19.json',reg)


def actual_confirm(c,f,native):
    result_ref=c.plan['confirm19_quality_result'];actual=c.read(result_ref)
    qualify(actual,native=native,native_ref=f['native20_quality_result'])
    qa=c.read(actual['output_acceptance'])
    require(qa['status']=='PASS_DIRECT_BOX109_CONFIRM19_FIRST_RAW_HEAD_CPU_QA'
        and qa['registration']==actual['registration'] and qa['phase']=='confirm19'
        and len(qa['predictions'])==19 and all(qa[k]==f[k] for k in MODEL_KEYS),'Actual successful19 first raw QA and exact model')
    return actual,result_ref


def register_formal_cpu_pilot32(c):
    f,native=c.frozen();confirm,confirm_ref=actual_confirm(c,f,native);p=c.plan
    require(p['protected_baseline']['sha256']==BASELINE,'Original40.47 identity only')
    accepted=c.read(p['accepted_production']);metadata=c.read(p['production_metadata'])
    accepted_root=c.bind(p['accepted_production']).parent;clocks={};source_refs={}
    metas={r['video_id']:r for r in metadata['records']}
    for s in accepted['sources']:
        if metas[s['id']]['targetRatioWH']!=[16,9]:continue
        directory=accepted_root/'inputs'/s['id'];clock=dict(path=str(directory/'clock.json'),sha256=s['clock_sha256'])
        clocks[s['id']]=c.read(clock);ar=reference(directory/'acceptance.json')
        require(c.read(ar)==s,'Exact original accepted source metadata')
        source_refs[s['id']]=dict(clock=clock,acceptance=ar)
    with zipfile.ZipFile(c.bind(p['protected_baseline'])) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None,'Original baseline ZIP/member/CRC')
        baseline=[json.loads(row) for row in z.read('predictions.jsonl').splitlines() if row]
    domain=c.module('preparation_code').compile_formal_domain(accepted,metadata,baseline,clocks,source_refs)
    sources=domain['selected_D'];directory=c.meta/'formal';require(not directory.exists(),'Never recompile a frozen formal domain')
    domain_ref=c.write(directory/'domain.json',domain)
    catalog=c.write(directory/'source_catalog.json',dict(sources=sources,official_source_count=426,
        affected_video_count=domain['affected_video_count'],GT_included=False,protected_baseline=p['protected_baseline'],
        all_other_baseline_frames_and_boxes_unchanged=True))
    reg=base_cpu(c,f,native,'formal',catalog,None,c.budget('formal_cpu_pilot32'))
    reg.update(expected_sources=len(sources),official_source_count=426,affected_video_count=domain['affected_video_count'],
        domain=domain_ref,protected_baseline=p['protected_baseline'],selection='OBS_INDEX_EVEN',
        admitted_arm_names=list(confirm['admitted_arm_names']),confirm19_quality_result=confirm_ref,
        confirm19_quality_summary=summary(confirm,confirm_ref),production_GPU_admitted=False)
    return c.write(c.root/'direct_box_scope_CPU_registration_106_formal.json',reg)


def remaining_capacity(pilot,domain,capacity,budget,pilot_ref):
    """Measured resource evidence, no fixed disk/video-count admission constants."""
    require(pilot['status']=='PASS_DIRECT_BOX106_FORMAL_CPU_PILOT32_ONLY' and pilot['sources']==32
        and len(pilot['entries'])==len(pilot['first_QA'])==32
        and [e['source_id'] for e in pilot['entries']]==domain['pilot_source_ids'], 'Actual successful exact first32 only')
    count=len(domain['remaining_source_ids'])
    require(count>0 and type(pilot['new_bytes_before_acceptance']) is int and pilot['new_bytes_before_acceptance']>0
        and math.isfinite(pilot['elapsed_seconds']) and pilot['elapsed_seconds']>0,'Actual32 measured bytes/time')
    byte_estimate=math.ceil(pilot['new_bytes_before_acceptance']*count/32)
    time_estimate=pilot['elapsed_seconds']*count/32
    require(capacity['schema']=='EXPLICIT_DIRECT_BOX106_REMAINING_CAPACITY_ADMISSION_V100'
        and capacity['pilot_acceptance']==pilot_ref and capacity['capacity_sufficient'] is True
        and capacity['external_task_conflict'] is False and capacity['projected_additional_bytes']>=byte_estimate
        and capacity['projected_additional_seconds']>=time_estimate
        and capacity['available_disk_bytes']>=budget['max_new_bytes']>=capacity['projected_additional_bytes']
        and capacity['available_seconds']>=budget['max_seconds']>=capacity['projected_additional_seconds']
        and capacity['available_ram_bytes']>=capacity['measured_peak_rss_bytes']>0,
        'Explicit live capacity approval must cover measured32 projection and shared-resource usage')
    now=dt.datetime.now(dt.timezone.utc)
    require(dt.datetime.fromisoformat(capacity['measured_at_utc'].replace('Z','+00:00'))<=now
        <=dt.datetime.fromisoformat(capacity['valid_until_utc'].replace('Z','+00:00')),'Explicit current capacity evidence validity interval')
    return dict(pilot_measured_bytes=pilot['new_bytes_before_acceptance'],pilot_measured_seconds=pilot['elapsed_seconds'],
        remaining_sources=count,linear_bytes_projection=byte_estimate,linear_seconds_projection=time_estimate,
        projection_is_not_a_guarantee=True)


def register_remaining(c):
    f,native=c.frozen();actual_confirm(c,f,native)
    path=c.root/'direct_box_scope_CPU_registration_106_formal.json';reg_ref=reference(path);reg=c.read(reg_ref)
    pilot_ref=reference(c.root/'direct_box_scope_inputs_106/formal/pilot_acceptance.json');pilot=c.read(pilot_ref)
    domain=c.read(reg['domain']);budget=c.budget('formal_cpu_remaining');capacity_ref=c.plan['remaining_capacity_admission'];capacity=c.read(capacity_ref)
    require(pilot['registration']==reg_ref and pilot['domain']==reg['domain'],'Same actual32 CPU registration/domain')
    proof=remaining_capacity(pilot,domain,capacity,budget,pilot_ref)
    for item in pilot['first_QA']:c.bind(item)
    return c.write(c.root/'direct_box_scope_remaining_admission_106_formal.json',dict(
        schema='DIRECT_BOX106_FORMAL_REMAINING_CPU_ADMISSION',original_registration=reg_ref,pilot_acceptance=pilot_ref,
        domain=reg['domain'],source_catalog=reg['source_catalog'],remaining_source_ids=domain['remaining_source_ids'],
        capacity_admission=capacity_ref,capacity_projection=proof,production_GPU_admitted=False,**budget))


def register_inference(c,phase):
    require(phase in ('confirm19','formal'),'One explicit inference registration')
    f,native=c.frozen();p=c.plan
    cpu_ref=reference(c.root/('direct_box_scope_CPU_registration_106_'+phase+'.json'));cpu=c.read(cpu_ref)
    out=c.root/'direct_box_scope_inputs_106'/phase
    prepared_ref=reference(out/'prepared.json');gate_ref=reference(out/'input_acceptance.json')
    prepared=c.read(prepared_ref);gate=c.read(gate_ref)
    require(gate['status']=='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA' and gate['registration']==cpu_ref
        and gate['prepared']==prepared_ref and prepared['schema']=='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106'
        and prepared['source_catalog']==cpu['source_catalog'],'Actual complete106 input gate before any GPU registration')
    sources=c.read(cpu['source_catalog'])['sources'];original=c.read(p['frozen_GPU105_registration'])
    reg=dict(schema='FROZEN_DIRECT_BOX107_L2_SINGLE_IMAGE_INFERENCE',phase=phase,inference_admitted=True,
        **{k:p[k] for k in ('GPU_code','frozen_GPU105_code','frozen_GPU105_registration','frozen_math84_code','math_code',
            'frozen_GPU93_code','frozen_math93_code',
            'preparation_code','conditional_review_code','frozen_review105_code','frozen_review93_code','frozen_review84_code','geometry_code','policy_code')},
        **{k:original[k] for k in ('model_config','old_TIME','old_PAIR','old_CROP')},
        **{k:f[k] for k in (*MODEL_KEYS,'adapter_directory','adapter_config','native20_quality_result','native20_quality_summary')},
        CPU_registration=cpu_ref,prepared=prepared_ref,input_acceptance=gate_ref,
        prepared_schema='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106',input_acceptance_status='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA',
        expected_inputs=len(sources),expected_sources=len(sources),output_directory=str(c.root/'direct_box_inference_107'/phase),
        admitted_arm_names=list(f['admitted_arm_names']),old_control_result70=native['control_result70'],
        adopted_output_acceptances=[f['native_output_acceptance']],**c.budget(phase+'_GPU'))
    if phase=='confirm19':reg['expected_source_ids']=[s['source_id'] for s in sources]
    else:
        confirm,confirm_ref=actual_confirm(c,f,native);videos=sorted({s['video_id'] for s in sources})
        reg.update(confirm19_quality_result=confirm_ref,confirm19_quality_summary=summary(confirm,confirm_ref),
            admitted_arm_names=list(confirm['admitted_arm_names']),production_admitted=True,official_source_count=426,
            affected_video_count=len(videos),expected_affected_videos=len(videos),affected_video_ids=videos,
            whole426_preserved=True,time_selection_unchanged=True,selection='OBS_INDEX_EVEN',protected_baseline=p['protected_baseline'])
        reg['adopted_output_acceptances'].append(confirm['output_acceptance'])
    inference=c.module('GPU_code')
    rp=c.root/('direct_box_inference_registration_107_'+phase+'.json')
    inference.validate_admission(c.root,phase,rp,reg);inference.validate_inputs(reg,prepared,gate)
    if phase=='formal':
        reg['production_admission']=c.write(c.meta/'production_admission.json',dict(
            status='ADMIT_DIRECT_BOX105_EXACT_NATIVE_PTS_SPATIAL_ONLY',production_admitted=True,
            **{k:f[k] for k in MODEL_KEYS},admitted_arm_names=reg['admitted_arm_names'],expected_inputs=len(sources),
            official_source_count=426,affected_video_count=reg['affected_video_count'],whole426_preserved=True,
            time_selection_unchanged=True,selection='OBS_INDEX_EVEN',native20_quality_result=f['native20_quality_result'],
            confirm19_quality_result=confirm_ref,domain=cpu['domain'],input_acceptance=gate_ref))
    return c.write(rp,reg)


def register_package(c):
    """Register108 only after real109 formal raw/overlay QA; never create a ZIP."""
    f,native=c.frozen();confirm,confirm_ref=actual_confirm(c,f,native)
    qa_ref=reference(c.root/'direct_box_formal_output_acceptance_109.json');qa=c.read(qa_ref)
    require(qa['status']=='PASS_DIRECT_BOX109_FORMAL_FIRST_RAW_HEAD_PTS_CPU_QA'
        and all(qa[k]==f[k] for k in MODEL_KEYS) and qa['confirm19_quality_result']==confirm_ref
        and qa['official_source_count']==426 and qa['all_times_preserved'] is True,
        'Actual same-model formal first raw QA and whole426 overlay before packaging handoff')
    require(set(qa['arm_overlays'])==set(confirm['admitted_arm_names']),'Exact same qualified arm overlays only')
    for r in qa['arm_overlays'].values():c.bind(r)
    gpu_reg_ref=reference(c.root/'direct_box_inference_registration_107_formal.json');gpu_reg=c.read(gpu_reg_ref)
    require(qa['registration']==gpu_reg_ref and qa['protected_baseline']==c.plan['protected_baseline'], 'Exact registered107/109 formal identity')
    explicit=c.plan['package_refs']
    required=('code','inherited_baseline_completion','inherited_provenance','inherited_selected','source_field_inputs','metadata',
        'original_independent_validator','historical_registry','resource_receipt','gpu_ledger','official_rule_check')
    for key in required:c.bind(explicit[key])
    require(explicit['strict_loader_code_refs'] and explicit['cost_evidence_refs'],'Explicit original loader locks and all cost evidence')
    loader_root=Path(explicit['strict_loader_root']).resolve()
    for r in explicit['strict_loader_code_refs']:require(c.bind(r).is_relative_to(loader_root),'Original loader code is inside registered loader root')
    for r in explicit['cost_evidence_refs']:c.bind(r)
    rules=c.read(explicit['official_rule_check']);require(rules['status']=='PASS_CURRENT_DIRECT_BOX108_PACKAGE_RULE_SCOPE','Actual current package-scope rules check')
    formal_out=Path(gpu_reg['output_directory'])
    return c.write(c.root/'direct_box_package_registration_108.json',dict(schema='DIRECT_BOX105_EXACT_NATIVE_PACKAGE_V108',
        **{k:explicit[k] for k in (*required,'strict_loader_root','strict_loader_code_refs','cost_evidence_refs')},
        **{k:f[k] for k in MODEL_KEYS},native20_quality_result=f['native20_quality_result'],confirm19_quality_result=confirm_ref,
        formal_output_acceptance=qa_ref,admitted_arm_names=confirm['admitted_arm_names'],arm_overlays=qa['arm_overlays'],
        protected_baseline=c.plan['protected_baseline'],formal_GPU_registration=gpu_reg_ref,
        formal_completion=reference(formal_out/'completion.json'),formal_model_integrity=reference(formal_out/'model_integrity.json'),
        production_admission=gpu_reg['production_admission'],prepared=gpu_reg['prepared'],input_acceptance=gpu_reg['input_acceptance'],
        frozen_math84_code=c.plan['frozen_math84_code'],deadline_utc=c.plan['deadline_utc'],
        physical_parameters=8774803699,pipeline_parameters=8790237452,automatic_package=False,automatic_upload=False))


COMMANDS={'freeze_native20':freeze_native20,'register_confirm19':register_confirm19,
    'register_formal_cpu_pilot32':register_formal_cpu_pilot32,'register_remaining':register_remaining,
    'register_package':register_package}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--command',choices=[*COMMANDS,'register_inference'],required=True);p.add_argument('--phase',choices=['confirm19','formal'])
    a=p.parse_args();require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only metadata registrar')
    c=Context(a.root,a.plan)
    require(c.root.is_relative_to(WORK),'Authorized Linux work root only')
    result=register_inference(c,a.phase) if a.command=='register_inference' else COMMANDS[a.command](c)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
