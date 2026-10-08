"""Read-only native-nearest monitor with exact original success counts."""
import datetime as dt
import importlib.util
import json
import zipfile
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ENTRY='native_round_alignment_v1'

def prior_commands(entry):
    values=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace').strip()
            if str(ROOT/entry) in cmd and '.py' in cmd:values.append({'pid':int(p.name),'full_command':cmd})
        except OSError:pass
    return values

def capture():
    spec=importlib.util.spec_from_file_location('nr_readonly_capture',ROOT/'controller/inspect_context_advisory_v1.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ENTRY=ENTRY
    value=m.capture();here=ROOT/ENTRY
    for name in ('cpu_acceptance.json','first_real_acceptance.json','developer_01/developer.completion.json',
        'developer_01/report.json','nontest_01/replay_acceptance.json','developer_01/replay_acceptance.json',
        'nontest_01/temporal.stage.json','nontest_01/spatial.stage.json','nontest_01/schedule.stage.json',
        'nontest_01/cache_reuse_receipt.json','rematch_01/temporal.stage.json','rematch_01/spatial.stage.json',
        'rematch_01/schedule.stage.json','rematch_01/cache_reuse_receipt.json'):
        if (here/name).is_file():
            data=m.read(here/name)
            if isinstance(data,dict) and 'proofs' in data:
                proofs=data['proofs'];data={k:v for k,v in data.items() if k!='proofs'}
                data['actual_proof_count']=len(proofs)
                if name=='cpu_acceptance.json':
                    data['actual_nearest_sample_counts']=sorted({r['dense_sample_count'] for r in proofs})
                    data['spatial_grid_changed_windows']=sum(r['base_grid']!=r['dense_grid'] for r in proofs)
                data['full_private_receipt_sha256']=m.sha(here/name)
            if name=='first_real_acceptance.json':data['private_receipt_sha256']=m.sha(here/name)
            value['stages'][name]=data;value['stage_read_utc'][name]=dt.datetime.now(dt.timezone.utc).isoformat()
    models={n:{'path':str(here/n),'sha256':m.sha(here/n),'model_identity':m.read(here/n)}
        for n in ('nontest_01/model.json','developer_01/model.json','rematch_01/model.json') if (here/n).is_file()}
    value['model_receipts']=models
    for row in value['done']:
        data=m.read(row['path'])
        row['model_identity_matches_actual_receipt']=bool(models) and all(data['model_identity']==r['model_identity'] for r in models.values())
        row['physical_sample_count']=len(data['window']['planned_source_frame_ordinals'])
        a=data['window']['baseline_floor64_ordinals'];b=data['window']['planned_source_frame_ordinals']
        row['registered_same_count_endpoints_pass']=len(a)==len(b)<=64 and a[0]==b[0] and a[-1]==b[-1]
        row['actual_video_grid_thw']=data['video_identity']['video_grid_thw']
    value['all_done_model_identity_matches_actual_receipts']=all(r['model_identity_matches_actual_receipt'] for r in value['done'])
    value['all_done_registered_sampling_pass']=all(r['registered_same_count_endpoints_pass'] for r in value['done'])
    value['actual_archives']={}
    for scope in ('nontest','rematch'):
        folder=here/(scope+'_01');archive=folder/'candidate_NATIVE_ROUND_ALIGNMENT_8B.zip'
        if not archive.is_file():continue
        pack=m.read(folder/'package.stage.json') or {};strict=m.read(folder/'independent_validation.json') or {}
        digest=m.sha(archive)
        with zipfile.ZipFile(archive) as z:
            names=z.namelist();crc=z.testzip()
            raw_equal=names==['predictions.jsonl'] and z.read('predictions.jsonl')==(folder/'predictions.jsonl').read_bytes()
        value['actual_archives'][scope]={'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest,
            'archive_names':names,'CRC_failure':crc,'raw_predictions_bytes_equal':raw_equal,
            'package_and_independent_SHA_match':digest==pack.get('actual_zip_sha256')==strict.get('zip_sha256'),
            'actual_size_matches_package':archive.stat().st_size==pack.get('actual_zip_bytes'),
            'read_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    value['local_done_by_arm']={'Q':sum(r['arm']=='Q' for r in value['done'])}
    value['done_by_scope']={s:sum('/'+s+'/' in r['path'] for r in value['done']) for s in ('nontest_01','developer_01','rematch_01')}
    resume=m.read(here/'input_01/resume_manifest.json')
    if resume:
        value['resume_counts']=resume['counts'];value['registered_changed_windows']=resume['changed_windows'];value['original_preserved_density_successes']=len(resume['preserved_upstream_success'])
        value['all_original_resume_bindings_SHA_pass']=all(m.sha(r['path'])==r['sha256'] and
            all(m.sha(p)==s for p,s in r['bound_files'].items()) for r in resume['rows']+resume['preserved_upstream_success'])
        value['original_resume_manifest_sha256']=m.sha(here/'input_01/resume_manifest.json')
    value['resources']={n:{'resource':m.read(ROOT/'controller'/('aic_NRA_v1_'+n+'.resource.json')),
        'queue':m.read(ROOT/'controller'/('aic_NRA_v1_'+n+'.queue.json'))} for n in ('nontest','developer','rematch')}
    ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    rows=[json.loads(s) for s in ledger.read_text().splitlines() if s.strip()]
    value['GPU_ledger']={'lines':len(rows),'sha256':m.sha(ledger),'historical_offset':7200,
        'owned_rows':[x for x in rows if x.get('name','').startswith('aic_NRA_v1_')]}
    upstream=ROOT/'nested_density_v1'
    value['upstream_density']={'actual_owned_commands':prior_commands('nested_density_v1'),
        'scientific_stop_sha256':m.sha(upstream/'scientific_stop.json'),
        'report':m.read(upstream/'developer_01/report.json'),
        'replay_status':m.read(upstream/'developer_01/replay_acceptance.json')['status'],
        'resource':m.read(ROOT/'controller/aic_ND_v1_developer.resource.json')}
    value['actual_original_aliases']={'count':0,'all_bound_SHA_pass':True}
    handoff=m.read(here/'rematch_01/alias_handoff.json')
    if handoff:
        value['actual_original_aliases']={'count':len(handoff['aliases']),
            'all_bound_SHA_pass':all(m.sha(x['path'])==x['sha256'] for x in handoff['aliases']) and
                m.sha(ROOT/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl')==handoff['original_temporal_sha256'],
            'new_model_calls':handoff['new_model_calls'],'handoff_sha256':m.sha(here/'rematch_01/alias_handoff.json')}
    value['prior_routes']={}
    for entry,files in (('b_prompt_recovery_v1',('scientific_stop.json','developer_01/report.json')),('context_advisory_v1',('scientific_stop.json','developer_01/full.completion.json')),
        ('b_boundary_diagnostic_v1',('diagnostic_completion.json','inference_completion.json')),
        ('teacher_student_autopilot_v14',('completion.json','final_acceptance.json'))):
        receipts={}
        for name in files:
            path=ROOT/entry/name
            if path.is_file():
                data=m.read(path)
                receipts[name]={'sha256':m.sha(path),**{k:data.get(k) for k in ('status','utc')}}
        value['prior_routes'][entry]={'actual_owned_commands':prior_commands(entry),'receipts':receipts}
    progress=value['stages'].get('progress.json') or {};start=value['stages'].get('start.json') or {}
    phase=progress.get('stage')
    if phase=='CPU_ROUND_ALIGNMENT_ACTUAL_INPUTS' and value['stages'].get('cpu_acceptance.json') and start and any(
        p['pid']==start.get('pid') and str(here/'controller.py') in p['full_command'] for p in value['processes']):
        phase='CONTROLLER_SOURCE_PREFLIGHT_CPU_ACTUAL_COMMAND_AND_IO'
    elif phase=='CPU_ROUND_ALIGNMENT_ACTUAL_INPUTS' and value['stages'].get('cpu_acceptance.json') and not start:
        phase='SINGLE_LAUNCH_SOURCE_PREFLIGHT_CPU' if any(str(here/'launch.py') in p['full_command'] for p in value['processes']) else 'FROZEN_PREFLIGHT_COMPLETE_SINGLE_LAUNCH_PENDING'
    value['actual_execution_stage']=phase
    value['historical_progress_component_retained']=phase!=progress.get('stage')
    value['current_control_logs']={str(p.relative_to(here)):{'bytes':p.stat().st_size,
        'mtime_ns':p.stat().st_mtime_ns,'tail':p.read_text(errors='replace')[-1800:]}
        for p in here.glob('control_*.log')}
    return value

if __name__=='__main__':print(json.dumps(capture(),ensure_ascii=False))
