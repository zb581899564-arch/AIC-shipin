"""Register and dispatch ONE explicitly admitted STAR72 phase; no import actions.

Only the first six external stages are implemented. Production stages require
separate measured admissions and currently STOP before any write or launch.
"""
from __future__ import annotations
import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'pair_code_17'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pair_common import WORK, bound, read, ref, require, save, sha, utc
import star_identity_v72 as identity

DEADLINE = '2026-10-18T03:22:24Z'
STAGES = ('reference_screen','CPU_resized20','GPU_resized20','reference_confirm',
          'CPU_resized19','GPU_resized19','CPU_pilot32','CPU_remaining','GPU_production','package')
FIRST_SIX = STAGES[:6]
LABELS = Path('/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1/reference/labels.json')
CODEDIR = 'star_profile_code_72/star_profile_v72'


class Artifacts:
    def __init__(self, root, deployment):
        self.root=Path(root); self.deployment=deployment

    def file(self, relative):
        r=self.reference(relative); return r,read(bound(r))

    def reference(self, relative):
        r=ref(self.root/relative); bound(r); return r

    def load(self, r): return read(bound(r))

    def code(self, name):
        path=self.root/CODEDIR/name; entry=self.deployment['members']['star_profile_v72/'+name]
        require(path.stat().st_size==entry['size'] and sha(path)==entry['sha256'], 'Frozen72 code bytes changed: '+name)
        return dict(path=str(path.resolve()),sha256=entry['sha256'])


def validate_admission(root, stage, admission, deployment, now=None):
    require(stage in FIRST_SIX, 'STOP: production requires a later measured explicit implementation/admission')
    require(admission['schema']=='STAR_SINGLE_SCOPE_LAUNCH_V73' and admission['stage']==stage
        and admission['launch_approved'] is True and admission['deadline_utc']==DEADLINE,
        'One exact-stage human-authorized launch admission required')
    require(bound(admission['register_code'])==Path(__file__).resolve(), 'Exact registered73 source bytes required')
    require(deployment['status']=='STAR72_CODE_READY_NO_REAL_SCOPE_ADMITTED'
        and deployment['actual_test_exit_code']==0
        and Path(deployment['code_directory']).resolve()==(Path(root)/CODEDIR).resolve(),
        'Adopt exact naturally tested frozen72 deployment')
    budget=900 if stage.startswith('GPU_') else 600
    current=now or dt.datetime.now(dt.timezone.utc)
    require((dt.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))-current).total_seconds()>budget+120,
        'Keep this scope and independent inspection within original Goal deadline')
    if stage.startswith('GPU_'):
        require(type(admission['planned_output_bytes']) is int and admission['planned_output_bytes']>0
            and isinstance(admission['capacity_reason'],str) and bool(admission['capacity_reason'].strip()),
            'GPU payload estimate and current capacity reason come from main admission')
    return budget


def load_context(io):
    r69,c69=io.file('utility_star_GPU_registration_69.json')
    _,c68=io.file('utility_star_CPU_registration_68.json')
    c55=io.load(c69['original_GPU55']); cpu55=io.load(c55['CPU_registration'])
    training_ref,training=io.file('utility_star_model_69/completion.json')
    quality_ref,quality=io.file('utility_star_comparison_70/result.json')
    require(c69['CPU_registration']==io.file('utility_star_CPU_registration_68.json')[0], 'Exact68 registration, no version discovery')
    common=dict(identity_code=io.code('star_identity_v72.py'), star_GPU69_code=c69['GPU_code'],
        star_GPU69_registration=r69, training_completion=training_ref, training_quality_admission=quality_ref,
        frozen_GPU55_code=c69['frozen_GPU55_code'], frozen_GPU55_registration=c69['original_GPU55'],
        adapter_weights=training['adapter_weights'], value_weights=training['value_weights'],
        **{k:c69[k] for k in ('old55_STOP','old55_completion','old55_progress','old55_adapter_weights',
            'old55_value_weights','model_config','old_TIME','old_PAIR','old_CROP')})
    identity.check(common)
    terminal_ref,terminal=io.file('utility_star_remaining796_terminal_70.json')
    require(terminal['status']=='REGISTERED_STAR_PHASE_NATURAL_COMPLETE_EXIT0' and terminal['exit_code']==0
        and [e['stage'] for e in terminal['entries']]==['GPU','first_output_QA'], 'Actual full69/70 natural terminal required')
    for entry in terminal['entries']:
        _,launch=io.file('utility_star_remaining796_'+entry['stage']+'_launch_70.json')
        _,done=io.file('utility_star_remaining796_'+entry['stage']+'_exit_70.json')
        require(launch==entry and done['entry']==entry and done['actual_exit_code']==0,
            'Actual69/70 parent must bind owned launches and successful exits')
    qa_ref,qa=io.file('utility_star_final_output_acceptance_70.json')
    require(qa['status']=='PASS_STAR_FINAL1300_SCREEN_FIRST_RAW_QA' and qa['registration']==r69
        and qa['training_completion']==training_ref and qa['adapter_weights']==common['adapter_weights']
        and qa['value_weights']==common['value_weights'] and quality['screen_output_acceptance']==qa_ref,
        'Actual exact STAR1300 first raw QA and70 quality association required')
    result35_ref,result35=io.file('observation_feasibility_35/result.json')
    require(result35['status']=='PASS_RESIZED_OBSERVATION_LAYOUT_FEASIBILITY_ONLY'
        and isinstance(result35['receipts'],list), 'Actual35 resized recovery receipts required')
    reg35=io.load(result35['registration'])
    for r in result35['receipts']: bound(r)
    require(c69['image_code']==c68['image_code'], 'Actual68/69 image implementation differs')
    return dict(common=common,c69=c69,c68=c68,c55=c55,cpu55=cpu55,qa=qa_ref,
        recovery_code=reg35['recovery_code'],recovery_receipts=result35['receipts'],
        native_terminal=terminal_ref,recovery_result=result35_ref)


def terminal(io, phase, scope):
    prefix='star_'+phase+'_'+scope+'_72'
    r,t=io.file(prefix+'_terminal.json')
    expected=['GPU','output_QA'] if phase=='GPU' else ['reference' if phase=='reference' else 'CPU']
    require(t['status']=='REGISTERED_STAR_SCOPE_NATURAL_COMPLETE_EXIT0' and t['exit_code']==0
        and t['phase']==phase and t['scope']==scope and [e['stage'] for e in t['entries']]==expected,
        'Actual preceding single-scope natural terminal required')
    for e in t['entries']:
        _,launch=io.file(prefix+'_'+e['stage']+'_launch.json')
        _,exit_record=io.file(prefix+'_'+e['stage']+'_exit.json')
        require(launch==e and exit_record['entry']==e and exit_record['actual_exit_code']==0
            and type(e['pid']) is int and e['pid']>0 and str(e['start_ticks']).isdigit(),
            'Preceding actual argv/pid/startticks/exit ownership required')
    return r


def scope_quality(io, context, scope):
    terminal(io,'GPU',scope)
    r,q=io.file('star_review_72/'+scope+'/result.json')
    expected='PASS_STAR_RESIZED20_PROFILE_ONLY' if scope=='resized20' else 'PASS_STAR_RESIZED19_CONFIRM_ONLY'
    c=context['common']
    require(q['status']==expected and q['scope']==scope and q['primary']=='UTILITY' and q['quality']['admitted'] is True
        and q['fixed_final_checkpoint'] is True and q['adapter_weights']==c['adapter_weights']
        and q['value_weights']==c['value_weights'] and q['training_completion']==c['training_completion']
        and q['star_GPU69_registration']==c['star_GPU69_registration'], 'Actual preceding fixed1300 scope quality PASS required')
    reg_ref,gpu=io.file('star_GPU_registration_72_'+scope+'.json')
    qa_ref,qa=io.file('star_review_72/'+scope+'/output_acceptance.json')
    require(q['registration']==reg_ref and q['output_acceptance']==qa_ref and qa['registration']==reg_ref
        and qa['status']=='PASS_STAR72_FIRST_OUTPUT_QA' and qa['scope']==scope
        and qa['training_completion']==c['training_completion']
        and gpu['adapter_weights']==c['adapter_weights'] and gpu['value_weights']==c['value_weights'],
        'Same actual GPU registration and independently first-QAd scope outputs required')
    return r


def reference_registration(io, context):
    c=context['common']; old=context['cpu55']; root=io.root
    # Registration binds fixed old files without parsing any19 metadata/labels
    # before resized20 qualification. Actual19 identity checks stay in CPU72.
    excluded_ref=io.reference('roi_confirm_inputs_10/C00.json')
    return dict(c,schema='STAR_FIXED_PROFILE_REFERENCE_METADATA_V72',
        code=io.code('star_reference_compile_v72.py'), controller_code=io.code('star_scope_control_v72.py'),
        original_screen_catalog=old['old_catalog'],original_screen_targets=old['original_targets'],
        original_screen_case_plan=old['old_case_plan'],
        confirm_pure_code=ref(root/'utility_profile_code_58/crop_confirm_prepare_v36.py'),
        geometry_code=context['c68']['geometry_code'],deadline_utc=DEADLINE,max_seconds=600,
        original_confirm_prepared=io.reference('roi_confirm_inputs_10/prepared.json'),
        original_confirm_input_acceptance=io.reference('roi_confirm_inputs_10/input_acceptance.json'),
        remaining19_output_acceptance=io.reference('roi_confirm_remaining19_output_acceptance_12.json'),
        remaining19_completion=io.reference('roi_confirm_remaining19_GPU_12/completion.json'),
        original_confirm_labels=ref(LABELS),excluded_source=dict(item_id='gnmc:test:006575.jpeg',input=excluded_ref))


def build_stage(io, context, stage, admission):
    """Return exact registration and one supervisor command; do not mutate."""
    require(stage in FIRST_SIX, 'STOP: production registration awaits measured explicit continuation')
    c=context['common']; root=io.root
    if stage in ('reference_screen','reference_confirm'):
        scope='screen' if stage=='reference_screen' else 'confirm'
        if scope=='confirm': scope_quality(io,context,'resized20')
        reg=reference_registration(io,context); path=root/'star_reference_registration_72.json'; phase='reference'
    elif stage.startswith('CPU_'):
        scope=stage[len('CPU_'):]; metadata_scope='screen' if scope=='resized20' else 'confirm'
        terminal(io,'reference',metadata_scope)
        metadata_ref,metadata=io.file('star_profile_reference_72/'+metadata_scope+'/completion.json')
        require(metadata['status']=='COMPLETE_STAR_PROFILE_REFERENCE_METADATA_V72' and metadata['scope']==metadata_scope
            and metadata['sources']==(20 if scope=='resized20' else 19)
            and metadata['registration']==io.file('star_reference_registration_72.json')[0], 'Exact complete fixed source metadata required')
        catalog=io.load(metadata['source_catalog']); ids=[s['source_id'] for s in catalog['sources']]
        require(len(ids)==len(set(ids))==metadata['sources'] and 'gnmc:test:006575.jpeg' not in ids, 'Exact source count; never retry missing first source')
        profile=scope_quality(io,context,'resized20') if scope=='resized19' else None
        reg=dict(c,schema='STAR_CONDITIONAL_PROFILE_CPU_V72',scope=scope,
            preparation_code=io.code('star_profile_prepare_v72.py'),controller_code=io.code('star_scope_control_v72.py'),
            input_code=context['c69']['image_code'],geometry_code=context['c68']['geometry_code'],
            recovery_code=context['recovery_code'],recovery_receipts=context['recovery_receipts'],
            quality_result70=c['training_quality_admission'],source_catalog=metadata['source_catalog'],case_plan=metadata['case_plan'],
            CPU_targets=metadata['CPU_targets'],expected_source_ids=ids,deadline_utc=DEADLINE,max_seconds=600,
            native_prepared=context['c69']['screen_prepared'] if scope=='resized20' else None,
            native_input_acceptance=context['c69']['screen_input_acceptance'] if scope=='resized20' else None,
            native_output_acceptance=context['qa'] if scope=='resized20' else None,profile_acceptanceRef=profile,
            adopted_metadata_completion=metadata_ref)
        path=root/('star_profile_CPU_registration_72_'+scope+'.json'); phase='CPU'
    else:
        scope=stage[len('GPU_'):]; terminal(io,'CPU',scope)
        cpu_ref,cpu=io.file('star_profile_CPU_registration_72_'+scope+'.json')
        prepared_ref,prepared=io.file('star_profile_inputs_72/'+scope+'/prepared.json')
        gate_ref,gate=io.file('star_profile_inputs_72/'+scope+'/input_acceptance.json')
        require(gate['status']=='PASS_STAR72_NEW_PROFILE_INPUTS_FIRST_CPU_QA' and gate['registration']==cpu_ref
            and gate['prepared']==prepared_ref and prepared['schema']=='STAR_PROFILE_PREPARED_V72'
            and prepared['scope']==scope and prepared['sources']==(20 if scope=='resized20' else 19)
            and all(prepared[k]==c[k] for k in ('adapter_weights','value_weights','training_completion','star_GPU69_registration')),
            'Actual first CPU-QAd exact fixed1300 inputs required')
        reg=dict(c,schema='STAR_FROZEN_PROFILE_INFERENCE_V72',scope=scope,model_role='UTILITY_STAR_'+scope,
            GPU_code=io.code('star_inference_gpu_v72.py'),review_code=io.code('star_inference_review_v72.py'),
            controller_code=io.code('star_scope_control_v72.py'),reader_code=io.code('star_profile_prepare_v72.py'),
            reader_class='ProfileInputs',image_code=context['c69']['image_code'],CPU_registration=cpu_ref,
            input_acceptance=gate_ref,prepared=prepared_ref,expected_inputs=len(prepared['inference_inputs']),
            expected_sources=prepared['sources'],profile='RESIZED_OBSERVATION_PLANE',
            output_directory=str(root/'star_inference_72'/scope),adapter_directory=str(Path(c['adapter_weights']['path']).parent),
            adapter_config=ref(Path(c['adapter_weights']['path']).parent/'adapter_config.json'),
            frozen_review56_code=context['c55']['review_code'],policy_math_code=io.code('star_scope_math_v72.py'),
            frozen_policy33_code=context['c69']['policy_code'],old_gain_state=context['c69']['old_gain_state'],
            old_geometry_control=context['c69']['old_geometry_control'],adopted_output_acceptances=[context['qa']],
            training_quality_binding=io.file('star_profile_reference_72/screen/native_qualification_binding.json')[0],
            old55_STOP_binding=io.file('star_profile_reference_72/screen/old55_STOP_binding.json')[0],
            GPU_job='diagnostic_star72_'+scope+'_readonly_v73',deadline_utc=DEADLINE,max_seconds=900,
            planned_output_bytes=admission['planned_output_bytes'],capacity_reason=admission['capacity_reason'])
        if scope=='resized19':
            reg['profile_quality_admission']=scope_quality(io,context,'resized20')
            reg['adopted_output_acceptances'].append(io.file('star_review_72/resized20/output_acceptance.json')[0])
        path=root/('star_GPU_registration_72_'+scope+'.json'); phase='GPU'
    argv=[sys.executable,'-B','-u',str(bound(io.code('star_scope_control_v72.py'))),'--root',str(root),
        '--scope',scope,'--phase',phase,'--registration',str(path)]
    return path,reg,argv


def run(root,stage,admission_path):
    root=Path(root).resolve(); require(sys.platform=='linux' and root.is_relative_to(WORK), 'Linux authorized root only')
    require(stage in FIRST_SIX, 'STOP: production stage has no measured explicit implementation yet')
    admission_path=Path(admission_path).resolve(); require(admission_path.is_relative_to(root), 'Exact admission inside this root')
    admission=read(admission_path)
    require(bound(admission['deployment_receipt'])==(root/'star_conditional_code_deployment_72.json').resolve(),
        'Only the exact frozen72 deployment receipt, no latest/discovery fallback')
    deployment=read(bound(admission['deployment_receipt']))
    validate_admission(root,stage,admission,deployment)
    io=Artifacts(root,deployment)
    for name in deployment['members']:
        require(name.startswith('star_profile_v72/') and '/' not in name[len('star_profile_v72/'):], 'Exact flat frozen72 member namespace')
        io.code(name[len('star_profile_v72/'):])
    context=load_context(io); path,reg,argv=build_stage(io,context,stage,admission)
    phase,scope=stage.split('_',1)
    output=root/({'reference':'star_profile_reference_72','CPU':'star_profile_inputs_72','GPU':'star_inference_72'}[phase])/scope
    require(not output.exists() and not (phase=='GPU' and (root/'star_review_72'/scope).exists()),
        'Existing successful/failed output is immutable; no repeat or automatic retry')
    if path.exists():
        require(stage=='reference_confirm' and read(path)==reg, 'Exclusive new registration; only unchanged reference registration may be adopted')
    claim=root/('star_stage_'+stage+'_claim_73.json')
    save(claim,dict(utc=utc(),stage=stage,admission=ref(admission_path),register_code=ref(Path(__file__)),
        argv=argv,helper_pid=os.getpid(),automatic_next_scope=False))
    try:
        if not path.exists(): save(path,reg)
        logpath=root/('star_stage_'+stage+'_parent_73.log')
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with logpath.open('xb') as stream:
            process=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            ticks=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]
            entry=dict(stage=stage,argv=argv,pid=process.pid,start_ticks=ticks,registration=ref(path),
                admission=ref(admission_path),stdout_log=str(logpath),parent_CUDA_VISIBLE_DEVICES='0',
                CPU_children_masked_by_registered_supervisor=True,automatic_next_scope=False,no_wait_or_poll=True)
            save(root/('star_stage_'+stage+'_launch_73.json'),entry)
        print('REGISTERED_ONE_STAR_SCOPE',stage,process.pid,ticks,flush=True)
    except BaseException as error:
        save(root/('star_stage_'+stage+'_failure_73.json'),dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),
            stage=stage,registration=str(path),preserve_all_success=True,no_automatic_retry=True)); raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--stage',choices=STAGES,required=True);parser.add_argument('--admission',type=Path,required=True)
    args=parser.parse_args();run(args.root,args.stage,args.admission)
