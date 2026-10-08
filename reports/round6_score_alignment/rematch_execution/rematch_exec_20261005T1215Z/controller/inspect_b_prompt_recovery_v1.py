"""Unbound read-only exact cache, current process and terminal monitor."""
import datetime as dt
import importlib.util
from pathlib import Path
import json

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ENTRY='b_prompt_recovery_v1'

def old_commands():
    values=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace').strip()
            if str(ROOT/'b_boundary_diagnostic_v1') in cmd and '.py' in cmd:
                values.append({'pid':int(p.name),'full_command':cmd})
        except OSError:pass
    return values

def capture():
    spec=importlib.util.spec_from_file_location('brec_readonly_capture',ROOT/'controller/inspect_context_advisory_v1.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ENTRY=ENTRY
    value=m.capture();here=ROOT/ENTRY
    for name in ('cpu_acceptance.json','first_real_acceptance.json','developer_01/developer.completion.json',
        'developer_01/report.json','developer_01/replay_acceptance.json','developer_01/model.json','rematch_01/model.json'):
        if (here/name).is_file():
            data=m.read(here/name)
            if name.endswith('replay_acceptance.json'):data={k:v for k,v in data.items() if k!='remaining_proofs'}
            value['stages'][name]=data;value['stage_read_utc'][name]=dt.datetime.now(dt.timezone.utc).isoformat()
    actual_models={n:{'path':str(here/n),'sha256':m.sha(here/n),'model_identity':m.read(here/n)}
        for n in ('developer_01/model.json','rematch_01/model.json') if (here/n).is_file()}
    value['model_receipts']=actual_models
    for row in value['done']:
        data=m.read(row['path'])
        row['model_identity_matches_actual_receipt']=bool(actual_models) and all(data['model_identity']==r['model_identity'] for r in actual_models.values())
    value['all_done_model_identity_matches_actual_receipts']=all(r['model_identity_matches_actual_receipt'] for r in value['done'])
    resume=m.read(here/'input_01/resume_manifest.json')
    if resume:
        rows=resume['rows'];value['resume_counts']=resume['counts']
        value['all_original_resume_bindings_SHA_pass']=all(m.sha(r['path'])==r['sha256'] and
            all(m.sha(p)==s for p,s in r['bound_files'].items()) for r in rows)
        value['original_resume_manifest_sha256']=m.sha(here/'input_01/resume_manifest.json')
    value['resources']={n:{'resource':m.read(ROOT/'controller'/('aic_BREC_v1_'+n+'.resource.json')),
        'queue':m.read(ROOT/'controller'/('aic_BREC_v1_'+n+'.queue.json'))} for n in ('developer','rematch')}
    ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    rows=[json.loads(s) for s in ledger.read_text().splitlines() if s.strip()]
    value['GPU_ledger']={'lines':len(rows),'sha256':m.sha(ledger),'historical_offset':7200,
        'owned_rows':[x for x in rows if x.get('name','').startswith('aic_BREC_v1_')]}
    value['upstream_boundary']={
        'diagnostic_completion_sha256':m.sha(ROOT/'b_boundary_diagnostic_v1/diagnostic_completion.json'),
        'status':m.read(ROOT/'b_boundary_diagnostic_v1/diagnostic_completion.json')['status'],
        'actual_old_owned_commands':old_commands(),
        'resource':m.read(ROOT/'controller/aic_BBOUND_v1_diagnostic.resource.json')}
    return value

if __name__=='__main__':print(json.dumps(capture(),ensure_ascii=False))
