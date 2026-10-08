"""Read-only native-density monitor, including prefreeze CPU admission."""
import datetime as dt
import importlib.util
import json
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ENTRY='nested_density_v1'

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
    spec=importlib.util.spec_from_file_location('nd_readonly_capture',ROOT/'controller/inspect_context_advisory_v1.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ENTRY=ENTRY
    value=m.capture();here=ROOT/ENTRY
    for name in ('cpu_acceptance.json','first_real_acceptance.json','developer_01/developer.completion.json',
        'developer_01/report.json','nontest_01/replay_acceptance.json','developer_01/replay_acceptance.json',
        'nontest_01/temporal.stage.json','nontest_01/spatial.stage.json','nontest_01/scheduling.stage.json',
        'rematch_01/temporal.stage.json','rematch_01/spatial.stage.json','rematch_01/scheduling.stage.json'):
        if (here/name).is_file():
            data=m.read(here/name)
            if isinstance(data,dict) and 'proofs' in data:
                proofs=data['proofs'];data={k:v for k,v in data.items() if k!='proofs'}
                data['actual_proof_count']=len(proofs)
                if name=='cpu_acceptance.json':
                    data['actual_density_sample_counts']=sorted({r['dense_sample_count'] for r in proofs})
                    data['spatial_grid_changed_windows']=sum(r['base_grid']!=r['dense_grid'] for r in proofs)
                data['full_private_receipt_sha256']=m.sha(here/name)
            value['stages'][name]=data;value['stage_read_utc'][name]=dt.datetime.now(dt.timezone.utc).isoformat()
    models={n:{'path':str(here/n),'sha256':m.sha(here/n),'model_identity':m.read(here/n)}
        for n in ('nontest_01/model.json','developer_01/model.json','rematch_01/model.json') if (here/n).is_file()}
    value['model_receipts']=models
    for row in value['done']:
        data=m.read(row['path'])
        row['model_identity_matches_actual_receipt']=bool(models) and all(data['model_identity']==r['model_identity'] for r in models.values())
        row['physical_sample_count']=len(data['window']['planned_source_frame_ordinals'])
        row['old64_subset_preserved']=set(data['window']['baseline_floor64_ordinals'])<=set(data['window']['planned_source_frame_ordinals'])
        row['actual_video_grid_thw']=data['video_identity']['video_grid_thw']
    value['all_done_model_identity_matches_actual_receipts']=all(r['model_identity_matches_actual_receipt'] for r in value['done'])
    value['all_done_registered_subset_pass']=all(r['old64_subset_preserved'] for r in value['done'])
    value['local_done_by_arm']={'D':sum(r['arm']=='D' for r in value['done'])}
    value['done_by_scope']={s:sum('/'+s+'/' in r['path'] for r in value['done']) for s in ('nontest_01','developer_01','rematch_01')}
    resume=m.read(here/'input_01/resume_manifest.json')
    if resume:
        value['resume_counts']=resume['counts'];value['original_preserved_B1_successes']=len(resume['preserved_upstream_success'])
        value['all_original_resume_bindings_SHA_pass']=all(m.sha(r['path'])==r['sha256'] and
            all(m.sha(p)==s for p,s in r['bound_files'].items()) for r in resume['rows']+resume['preserved_upstream_success'])
        value['original_resume_manifest_sha256']=m.sha(here/'input_01/resume_manifest.json')
    value['resources']={n:{'resource':m.read(ROOT/'controller'/('aic_ND_v1_'+n+'.resource.json')),
        'queue':m.read(ROOT/'controller'/('aic_ND_v1_'+n+'.queue.json'))} for n in ('nontest','developer','rematch')}
    ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    rows=[json.loads(s) for s in ledger.read_text().splitlines() if s.strip()]
    value['GPU_ledger']={'lines':len(rows),'sha256':m.sha(ledger),'historical_offset':7200,
        'owned_rows':[x for x in rows if x.get('name','').startswith('aic_ND_v1_')]}
    upstream=ROOT/'b_prompt_recovery_v1'
    value['upstream_B1']={'actual_owned_commands':prior_commands('b_prompt_recovery_v1'),
        'scientific_stop_sha256':m.sha(upstream/'scientific_stop.json'),
        'report':m.read(upstream/'developer_01/report.json'),
        'replay_status':m.read(upstream/'developer_01/replay_acceptance.json')['status'],
        'resource':m.read(ROOT/'controller/aic_BREC_v1_developer.resource.json')}
    progress=value['stages'].get('progress.json') or {};start=value['stages'].get('start.json') or {}
    phase=progress.get('stage')
    if phase=='CPU_DENSITY_ACTUAL_INPUTS' and value['stages'].get('cpu_acceptance.json') and start and any(
        p['pid']==start.get('pid') and str(here/'controller.py') in p['full_command'] for p in value['processes']):
        phase='CONTROLLER_SOURCE_PREFLIGHT_CPU_ACTUAL_COMMAND_AND_IO'
    value['actual_execution_stage']=phase
    value['historical_progress_component_retained']=phase!=progress.get('stage')
    value['current_control_logs']={str(p.relative_to(here)):{'bytes':p.stat().st_size,
        'mtime_ns':p.stat().st_mtime_ns,'tail':p.read_text(errors='replace')[-1800:]}
        for p in here.glob('control_*.log')}
    return value

if __name__=='__main__':print(json.dumps(capture(),ensure_ascii=False))
