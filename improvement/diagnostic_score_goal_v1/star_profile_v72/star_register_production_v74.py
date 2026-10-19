"""Explicit one-phase STAR production registration; no work occurs on import."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'pair_code_17'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pair_common import WORK,RUN,bound,read,ref,require,save,sha,utc
import star_register_stage_v73 as stage73
import star_inference_gpu_v72 as gpu72

STAGES=('CPU_pilot32','CPU_remaining','GPU_production','package')
PRODUCTION=WORK/'semantic_context_production_20261016_v1'
ACCEPTED=dict(path=str(PRODUCTION/'cpu_acceptance.json'),sha256='9e5e76284ba45528033b80308848ecc413a9075be507fb24ea3fc2975412c726')
METADATA=dict(path=str(PRODUCTION/'metadata.json'),sha256='c3612851513f83b2ea1968f3149bf64fbdd57a6d654370ecb31f15c817768936')
BASELINE=dict(path=str(PRODUCTION/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3')
SELECTION='OBS_INDEX_EVEN'


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def future_ref(path,value):
    """Exactly pair_common.save bytes, allowing pure multi-artifact planning."""
    encoded=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').replace('\n',os.linesep).encode('utf-8')
    return dict(path=str(Path(path).resolve()),sha256=hashlib.sha256(encoded).hexdigest())


def validate_admission(root,stage,admission,deployment,now=None):
    require(stage in STAGES and admission['schema']=='STAR_SINGLE_PRODUCTION_STAGE_LAUNCH_V74'
        and admission['stage']==stage and admission['launch_approved'] is True
        and admission['deadline_utc']==stage73.DEADLINE,'One exact explicit production-stage admission required')
    require(bound(admission['register_code'])==Path(__file__).resolve()
        and bound(admission['stage73_code'])==Path(stage73.__file__).resolve(),'Exact74 and inherited frozen73 source bytes')
    require(deployment['status']=='STAR72_CODE_READY_NO_REAL_SCOPE_ADMITTED' and deployment['actual_test_exit_code']==0
        and Path(deployment['code_directory']).resolve()==(Path(root)/stage73.CODEDIR).resolve(),'Actual tested frozen72 deployment')
    seconds=600 if stage=='CPU_pilot32' else admission['max_seconds']
    require(type(seconds) is int and seconds>0,'Explicit bounded stage runtime from actual main admission')
    current=now or dt.datetime.now(dt.timezone.utc)
    require((dt.datetime.fromisoformat(stage73.DEADLINE.replace('Z','+00:00'))-current).total_seconds()>seconds+120,
        'Original Goal deadline includes this computation and independent inspection')
    if stage=='CPU_remaining':
        require(type(admission['max_additional_bytes']) is int and admission['max_additional_bytes']>0,
            'Main must supply measured additional-write budget; no guessed compression or capacity threshold')
    if stage=='GPU_production':
        require(type(admission['planned_output_bytes']) is int and admission['planned_output_bytes']>0
            and isinstance(admission['capacity_reason'],str) and bool(admission['capacity_reason'].strip()),
            'Main supplies actual GPU cost/output/capacity admission after measured CPU production')
    if stage=='package':
        require('official_rule_check' in admission and isinstance(admission['historical_canonical_sha256'],list)
            and len(set(admission['historical_canonical_sha256']))==len(admission['historical_canonical_sha256'])
            and all(isinstance(s,str) and len(s)==64 and set(s)<=set('0123456789abcdef')
                for s in admission['historical_canonical_sha256']), 'Explicit current rule ref and historical canonical list required')
    return seconds


def actual_classes(io,context):
    cpu_ref,_=io.file('star_profile_CPU_registration_72_resized20.json')
    prep_ref,p=io.file('star_profile_inputs_72/resized20/prepared.json')
    gate_ref,g=io.file('star_profile_inputs_72/resized20/input_acceptance.json')
    _,gpu=io.file('star_GPU_registration_72_resized20.json')
    require(g['status']=='PASS_STAR72_NEW_PROFILE_INPUTS_FIRST_CPU_QA' and g['prepared']==prep_ref
        and g['registration']==cpu_ref and gpu['prepared']==prep_ref and gpu['input_acceptance']==gate_ref
        and all(p[k]==context['common'][k] for k in ('adapter_weights','value_weights','training_completion','star_GPU69_registration')),
        'Actual fixed1300 resized20 accepted preparation class identity')
    ids=p['class_token_ids'];require(isinstance(ids,list) and len(ids)==len(set(ids))==3 and all(type(i) is int and i>=0 for i in ids),
        'Actual three digit class token IDs, no fabricated constants')
    return ids


def cpu_terminal(io,phase):
    prefix='star_production_'+phase+'_72'
    r,t=io.file(prefix+'_terminal.json');_,launch=io.file(prefix+'_launch.json');_,exit_record=io.file(prefix+'_exit.json')
    e=t['entry']
    require(t['status']=='EXPLICIT_STAR_CPU_NATURAL_COMPLETE_EXIT0' and t['exit_code']==0
        and e==launch==exit_record['entry'] and exit_record['actual_exit_code']==0 and e['CPU_child'] is True
        and type(e['pid']) is int and e['pid']>0 and str(e['start_ticks']).isdigit(),
        'Actual owned CPU phase argv/pid/startticks/natural exit required')
    return r


def pilot_domain(io,context):
    cpu_terminal(io,'pilot32')
    original_ref,original=io.file('star_production_CPU_registration_72.json')
    pilot_ref,pilot=io.file('star_production_inputs_72/pilot_acceptance.json')
    domain_ref,domain=io.file('star_production_inputs_72/domain.json')
    catalog_ref,catalog=io.file('star_production_inputs_72/source_catalog.json')
    plan_ref,plan=io.file('star_production_inputs_72/case_plan.json')
    require(pilot['status']=='PASS_STAR72_CPU_CAPACITY_PILOT32_ONLY' and pilot['registration']==original_ref
        and pilot['capacity_only'] is True and pilot['observations']==32 and pilot['production_admitted'] is False
        and pilot['domain']==domain_ref and pilot['source_catalog']==catalog_ref and pilot['case_plan']==plan_ref,
        'Actual32 capacity result must bind original frozen domain/catalog/case-plan')
    selected=domain['selected_D']; ids=[s['source_id'] for s in selected]
    require(domain['selection']==SELECTION and domain['official_source_count']==426
        and type(domain['affected_video_count']) is int and 0<domain['affected_video_count']<=303
        and len(ids)==len(set(ids))==domain['selected_D_count'] and len(ids)>=32
        and domain['pilot_source_ids']==ids[:32] and domain['remaining_source_ids']==ids[32:]
        and digest(selected)==domain['selected_D_sha256'] and digest(domain['all_D'])==domain['all_D_sha256']
        and domain['selected_D_sha256']==pilot['selected_D_sha256'] and catalog['sources']==selected
        and plan['GT_used_for_input_or_pair_choice'] is False and domain['protected_baseline_sha256']==BASELINE['sha256'],
        'Same actual immutable even-index/native-frame intersection, never guess observation count')
    require(original['schema']=='STAR_PRODUCTION_OBSERVATION_CPU_V72' and original['selection']==SELECTION
        and original['protected_baseline']==BASELINE
        and all(original[k]==context['common'][k] for k in ('adapter_weights','value_weights','training_completion','star_GPU69_registration')),
        'Actual32 used exact qualified1300 model and protected40.47')
    proofs=[io.load(r) for r in pilot['observation_acceptances']]
    require(len(proofs)==32 and [p['source_id'] for p in proofs]==ids[:32]
        and all(p['status']=='PASS_STAR72_OBSERVATION_FIRST_CPU_INPUT_QA'
            and p['source_metadata_sha256']==digest(s) for p,s in zip(proofs,selected[:32])),
        'Adopt all32 original successful source proofs without processor/raw rerun')
    return dict(original_ref=original_ref,original=original,pilot_ref=pilot_ref,pilot=pilot,domain_ref=domain_ref,
        domain=domain,catalog_ref=catalog_ref,plan_ref=plan_ref)


def complete_inputs(io,context):
    cpu_terminal(io,'remaining'); data=pilot_domain(io,context)
    admission_ref,admission=io.file('star_production_spatial_admission_74.json')
    continuation_ref,continuation=io.file('star_production_remaining_admission_72.json')
    prepared_ref,prepared=io.file('star_production_inputs_72/prepared.json')
    gate_ref,gate=io.file('star_production_inputs_72/input_acceptance.json')
    d=data['domain'];c=context['common']
    require(admission['status']=='ADMIT_STAR_EXACT_NATIVE_PTS_SPATIAL_ONLY' and admission['production_admitted'] is True
        and admission['expected_sources']==admission['observations']==d['selected_D_count']
        and admission['affected_video_count']==d['affected_video_count'] and admission['official_source_count']==426
        and continuation['original_registration']==data['original_ref'] and continuation['pilot_acceptance']==data['pilot_ref']
        and continuation['domain']==data['domain_ref'] and continuation['production_admission']==admission_ref,
        'Explicit measured continuation and exact same production domain admission required')
    require(gate['status']=='PASS_STAR72_ALL_SELECTED_OBSERVATIONS_FIRST_CPU_QA' and gate['prepared']==prepared_ref
        and gate['registration']==data['original_ref'] and prepared['schema']=='STAR_PRODUCTION_PREPARED_V72'
        and prepared['sources']==gate['sources']==d['selected_D_count'] and prepared['official_source_count']==426
        and prepared['affected_video_count']==d['affected_video_count'] and prepared['selection']==SELECTION
        and prepared['source_catalog']==data['catalog_ref'] and prepared['case_plan']==data['plan_ref']
        and prepared['selected_D_sha256']==d['selected_D_sha256'] and prepared['CPU_targets'] is None
        and all(prepared[k]==c[k] for k in ('adapter_weights','value_weights','training_completion','star_GPU69_registration')),
        'All actual first CPU inputs, no GT, original32 adopted, same1300 production pipeline')
    data.update(admission_ref=admission_ref,admission=admission,continuation_ref=continuation_ref,
        prepared_ref=prepared_ref,prepared=prepared,gate_ref=gate_ref,gate=gate)
    return data


def production_admission(context,q20,q19,*,pilot,domain=None):
    common=context['common']
    result=dict(status='ADMIT_STAR_PRODUCTION_CPU_PILOT32_ONLY' if pilot else 'ADMIT_STAR_EXACT_NATIVE_PTS_SPATIAL_ONLY',
        production_prepare_approved=True,production_admitted=not pilot,whole426_preserved=True,selection=SELECTION,
        resized20_quality=q20,resized19_quality=q19,profile_quality_admission=q20,confirm_quality_admission=q19,
        adapter_weights=common['adapter_weights'],value_weights=common['value_weights'],
        training_completion=common['training_completion'],star_GPU69_registration=common['star_GPU69_registration'],
        official_source_count=426,all_times_preserved=True,all_9_16_preserved=True,all_outside_D_boxes_preserved=True,
        protected_baseline=BASELINE,no_nearest_or_interpolation=True)
    if domain is not None: result.update(expected_sources=domain['selected_D_count'],observations=domain['selected_D_count'],
        affected_video_count=domain['affected_video_count'],selected_D_sha256=domain['selected_D_sha256'])
    return result


def build_stage(io,context,stage,admission):
    """Plan exclusive registrations and ONE controller; no pixel/tensor reads."""
    require(stage in STAGES,'Only one explicit production stage')
    q20=stage73.scope_quality(io,context,'resized20');q19=stage73.scope_quality(io,context,'resized19')
    c=context['common'];root=io.root; writes=[]
    if stage=='CPU_pilot32':
        ids=actual_classes(io,context)
        adm_path=root/'star_production_pilot_CPU_admission_74.json'
        adm=production_admission(context,q20,q19,pilot=True); adm_ref=future_ref(adm_path,adm);writes.append((adm_path,adm))
        reg=dict(c,schema='STAR_PRODUCTION_OBSERVATION_CPU_V72',scope='production',selection=SELECTION,
            preparation_code=io.code('star_production_prepare_v72.py'),controller_code=io.code('star_production_control_v72.py'),
            profile_code=io.code('star_profile_prepare_v72.py'),geometry_code=context['c68']['geometry_code'],
            image_code=context['c69']['image_code'],recovery_code=context['recovery_code'],
            recovery_receipts=context['recovery_receipts'],accepted_production=ACCEPTED,production_metadata=METADATA,
            protected_baseline=BASELINE,accepted_root=str(PRODUCTION),resized20_quality=q20,resized19_quality=q19,
            production_admission=adm_ref,class_token_ids=ids,deadline_utc=stage73.DEADLINE,max_seconds=600)
        path=root/'star_production_CPU_registration_72.json';phase='pilot32'
    elif stage=='CPU_remaining':
        data=pilot_domain(io,context);d=data['domain']
        require(admission['pilot_acceptance']==data['pilot_ref'] and admission['domain']==data['domain_ref'],
            'Main measured budget must bind this actual32 receipt and immutable domain')
        adm_path=root/'star_production_spatial_admission_74.json'
        adm=production_admission(context,q20,q19,pilot=False,domain=d);adm_ref=future_ref(adm_path,adm);writes.append((adm_path,adm))
        reg=dict(schema='STAR_PRODUCTION_REMAINING_CPU_V72',controller_code=io.code('star_production_control_v72.py'),
            original_registration=data['original_ref'],pilot_acceptance=data['pilot_ref'],domain=data['domain_ref'],
            source_catalog=data['catalog_ref'],case_plan=data['plan_ref'],remaining_source_ids=d['remaining_source_ids'],
            production_admission=adm_ref,expected_sources=d['selected_D_count'],observations=d['selected_D_count'],
            official_source_count=426,affected_video_count=d['affected_video_count'],selection=SELECTION,
            max_additional_bytes=admission['max_additional_bytes'],max_seconds=admission['max_seconds'],deadline_utc=stage73.DEADLINE)
        path=root/'star_production_remaining_admission_72.json';phase='remaining'
    elif stage=='GPU_production':
        data=complete_inputs(io,context);p=data['prepared'];d=data['domain']
        require(admission['prepared']==data['prepared_ref'] and admission['input_acceptance']==data['gate_ref'],
            'Main GPU budget must bind actual fully prepared first-QAd production inputs')
        reg=dict(c,schema='STAR_FROZEN_PROFILE_INFERENCE_V72',scope='production',model_role='UTILITY_STAR_production',
            GPU_code=io.code('star_inference_gpu_v72.py'),review_code=io.code('star_inference_review_v72.py'),
            controller_code=io.code('star_scope_control_v72.py'),reader_code=io.code('star_production_prepare_v72.py'),
            reader_class='ProductionInputs',image_code=context['c69']['image_code'],CPU_registration=data['original_ref'],
            input_acceptance=data['gate_ref'],input_acceptance_status='PASS_STAR72_ALL_SELECTED_OBSERVATIONS_FIRST_CPU_QA',
            prepared=data['prepared_ref'],expected_inputs=len(p['inference_inputs']),expected_sources=d['selected_D_count'],
            official_source_count=426,affected_video_count=d['affected_video_count'],profile='RESIZED_OBSERVATION_PLANE',
            output_directory=str(root/'star_inference_72/production'),adapter_directory=str(Path(c['adapter_weights']['path']).parent),
            adapter_config=ref(Path(c['adapter_weights']['path']).parent/'adapter_config.json'),
            frozen_review56_code=context['c55']['review_code'],policy_math_code=io.code('star_scope_math_v72.py'),
            frozen_policy33_code=context['c69']['policy_code'],old_gain_state=context['c69']['old_gain_state'],
            old_geometry_control=context['c69']['old_geometry_control'],
            adopted_output_acceptances=[context['qa'],io.file('star_review_72/resized20/output_acceptance.json')[0],
                io.file('star_review_72/resized19/output_acceptance.json')[0]],
            training_quality_binding=io.file('star_profile_reference_72/screen/native_qualification_binding.json')[0],
            old55_STOP_binding=io.file('star_profile_reference_72/screen/old55_STOP_binding.json')[0],
            profile_quality_admission=q20,confirm_quality_admission=q19,production_admission=data['admission_ref'],
            GPU_job='diagnostic_star72_production_readonly_v74',deadline_utc=stage73.DEADLINE,
            max_seconds=admission['max_seconds'],planned_output_bytes=admission['planned_output_bytes'],capacity_reason=admission['capacity_reason'])
        path=root/'star_GPU_registration_72_production.json';phase='GPU'
        gpu72.validate_prepared(reg,data['gate'],p)
        gpu72.validate_reader_identity(reg,data['original'],'production')
    else:
        data=complete_inputs(io,context);stage73.terminal(io,'GPU','production')
        gpu_ref,gpu=io.file('star_GPU_registration_72_production.json')
        qa_ref,qa=io.file('star_review_72/production/output_acceptance.json')
        top_ref,top=io.file('star_inference_72/production/completion.json')
        policy_ref,policy=io.file('star_review_72/production/policy.json')
        require(admission['production_output_acceptance']==qa_ref,'Main package admission must bind actual full production first raw QA')
        require(qa['status']=='PASS_STAR72_FIRST_OUTPUT_QA' and qa['scope']=='production'
            and qa['registration']==gpu_ref and qa['top_completion']==top_ref
            and top['status']=='COMPLETE_STAR_V72_READONLY_SCOPE_NOT_QUALITY' and top['GPU_registration']==gpu_ref
            and top['prepared']==data['prepared_ref'] and top['input_acceptance']==data['gate_ref']
            and top['inventory']['pipeline']==8790229268 and top['new_optimizer_updates']==0
            and all(qa[k]==top[k]==c[k] for k in ('adapter_weights','value_weights','training_completion'))
            and gpu['production_admission']==data['admission_ref'] and gpu['profile_quality_admission']==q20
            and gpu['confirm_quality_admission']==q19 and policy['output_acceptance']==qa_ref and policy['GT_read'] is False,
            'Actual full production GPU, first independent CPU raw QA and same-model policy required')
        rules=io.load(admission['official_rule_check'])
        require(rules['status']=='PASS_CURRENT_STAR_PACKAGE_RULE_SCOPE','Main must supply a NEW current official rule check; no old PASS fallback')
        reg=dict(c,schema='STAR_EXACT_OBSERVATION_PACKAGE_V72',code=io.code('star_package_v72.py'),
            controller_code=io.code('star_production_control_v72.py'),production_admission=data['admission_ref'],
            profile_quality=q20,confirm_quality=q19,official_rule_check=admission['official_rule_check'],
            production_output_acceptance=qa_ref,prepared=data['prepared_ref'],input_acceptance=data['gate_ref'],
            protected_baseline=BASELINE,inherited_baseline_completion=ref(PRODUCTION/'package/completion.json'),
            inherited_provenance=ref(PRODUCTION/'package/provenance.jsonl'),inherited_selected=ref(PRODUCTION/'package/selected.jsonl'),
            source_field_inputs=ref(WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'),
            original_independent_validator=ref(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            strict_loader_root=str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),metadata=METADATA,
            policy33_code=context['c69']['policy_code'],geometry31_code=context['c68']['geometry_code'],
            production_policy=policy_ref,historical_canonical_sha256=admission['historical_canonical_sha256'],
            max_seconds=admission['max_seconds'],deadline_utc=stage73.DEADLINE)
        path=root/'star_package_registration_72.json';phase='package'
    writes.append((path,reg))
    controller='star_scope_control_v72.py' if phase=='GPU' else 'star_production_control_v72.py'
    argv=[sys.executable,'-B','-u',str(bound(io.code(controller))),'--root',str(root),'--phase',phase,'--registration',str(path)]
    if phase=='GPU': argv+=['--scope','production']
    return writes,argv


def run(root,stage,admission_path):
    root=Path(root).resolve();require(sys.platform=='linux' and root.is_relative_to(WORK),'Authorized Linux work root only')
    admission_path=Path(admission_path).resolve();require(admission_path.is_relative_to(root),'Explicit same-root production-stage admission')
    admission=read(admission_path)
    require(bound(admission['deployment_receipt'])==(root/'star_conditional_code_deployment_72.json').resolve(),'Exact frozen72 deployment receipt')
    deployment=read(bound(admission['deployment_receipt']));validate_admission(root,stage,admission,deployment)
    io=stage73.Artifacts(root,deployment)
    for name in deployment['members']:
        require(name.startswith('star_profile_v72/') and '/' not in name[len('star_profile_v72/'):],'Exact frozen72 member namespace')
        io.code(name[len('star_profile_v72/'):])
    context=stage73.load_context(io)
    for r in (ACCEPTED,METADATA,BASELINE):bound(r)
    require(bound(BASELINE).stat().st_size==384630,'Original protected40.47 ZIP size')
    writes,argv=build_stage(io,context,stage,admission)
    for path,_ in writes: require(not path.exists(),'Exclusive new production registration; never overwrite or revive')
    if stage=='CPU_pilot32':require(not (root/'star_production_inputs_72').exists(),'Never redo original32 preparation')
    if stage=='CPU_remaining':require(not (root/'star_production_inputs_72/remaining_claim.json').exists(),'No repeat remaining phase')
    if stage=='GPU_production':require(not (root/'star_inference_72/production').exists() and not (root/'star_review_72/production').exists(),'No repeat production forward/QA')
    if stage=='package':require(not (root/'star_package_72').exists() and not (root/'star_package_no_new_candidate_STOP_72.json').exists(),'No repackage/rename after successful or validSTOP production')
    claim=root/('star_production_stage_'+stage+'_claim_74.json')
    save(claim,dict(utc=utc(),stage=stage,admission=ref(admission_path),argv=argv,helper_pid=os.getpid(),automatic_next_stage=False))
    try:
        for path,value in writes:
            save(path,value); require(ref(path)==future_ref(path,value),'New registered bytes must equal planned cross-artifact refs')
        registration=ref(writes[-1][0]);logpath=root/('star_production_stage_'+stage+'_parent_74.log')
        cuda='0' if stage=='GPU_production' else ''
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=cuda,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with logpath.open('xb') as stream:
            process=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            ticks=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]
            save(root/('star_production_stage_'+stage+'_launch_74.json'),dict(stage=stage,argv=argv,pid=process.pid,
                start_ticks=ticks,registration=registration,admission=ref(admission_path),stdout_log=str(logpath),
                parent_CUDA_VISIBLE_DEVICES=cuda,no_wait_or_poll=True,automatic_next_stage=False))
        print('REGISTERED_ONE_STAR_PRODUCTION_PHASE',stage,process.pid,ticks,flush=True)
    except BaseException as error:
        save(root/('star_production_stage_'+stage+'_failure_74.json'),dict(utc=utc(),stage=stage,error=repr(error),
            traceback=traceback.format_exc(),preserve_all_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--stage',choices=STAGES,required=True);parser.add_argument('--admission',type=Path,required=True)
    args=parser.parse_args();run(args.root,args.stage,args.admission)
