"""Unbound read-only native process/artifact/receipt monitor; no model imports."""
import datetime as dt
import importlib.util
import json
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ENTRY='b_boundary_diagnostic_v1'


def capture():
    spec=importlib.util.spec_from_file_location('readonly_cad_capture',ROOT/'controller/inspect_context_advisory_v1.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.ENTRY=ENTRY
    result=mod.capture();here=ROOT/ENTRY
    names=['progress.json','start.json','registration.json','prepared.json','preflight.json','cpu_acceptance.json',
        'first_real_acceptance.json','inference_completion.json','diagnostic_completion.json','execution_failure.json',
        'run_01/server/model_receipt.json','run_01/server/server_start_receipt.json','run_01/server/owned_stop.json']
    stages={};times={}
    for name in names:
        if (here/name).is_file():
            stages[name]=mod.read(here/name);times[name]=dt.datetime.now(dt.timezone.utc).isoformat()
    done=[]
    for p in here.rglob('done.json'):
        x=mod.read(p)
        done.append({'path':str(p),'sha256':mod.sha(p),'utc':x.get('utc'),'event_key':x.get('event_key'),
            'variant':x.get('variant'),'status':x.get('status'),'matched_projection':x.get('matched_projection'),
            'input_tokens':x.get('measured',{}).get('input_sequence_length'),'HTTP_wall_seconds':x.get('HTTP_wall_seconds'),
            'teacher_recipe_sha256':x.get('teacher_recipe_sha256'),
            'bound_files_SHA_pass':all(Path(k).is_file() and mod.sha(k)==v for k,v in x.get('bound_files',{}).items())})
    recipe=here/'input_01/teacher_recipe.json'
    failures=[{'path':str(p),'sha256':mod.sha(p),'failure':mod.read(p)} for p in here.rglob('failure.json')]
    ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    rows=[json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    result.update(stages=stages,stage_read_utc=times,done=done,done_count=len(done),done_by_kind={'matched_context':len(done)},
        local_done_by_arm={},model_receipts={},all_done_model_identity_matches_actual_receipts=None,
        all_done_bound_SHA_pass=all(x['bound_files_SHA_pass'] for x in done),failures=failures,
        actual_teacher_recipe_sha256=mod.sha(recipe) if recipe.is_file() else None,
        all_done_teacher_recipe_SHA_match=all(x['teacher_recipe_sha256']==mod.sha(recipe) for x in done) if recipe.is_file() else None,
        resources={'diagnostic':{'resource':mod.read(ROOT/'controller/aic_BBOUND_v1_diagnostic.resource.json'),
            'queue':mod.read(ROOT/'controller/aic_BBOUND_v1_diagnostic.queue.json')}},
        GPU_ledger={'lines':len(rows),'sha256':mod.sha(ledger),'historical_offset':7200,
            'owned_rows':[x for x in rows if x.get('name')=='aic_BBOUND_v1_diagnostic']},
        upstream_C={'progress':mod.read(ROOT/'context_advisory_v1/progress.json'),
            'report':mod.read(ROOT/'context_advisory_v1/developer_01/full.report.json'),
            'resource':mod.read(ROOT/'controller/aic_CAD_v1_full.resource.json'),
            'source_lock_sha256':mod.sha(ROOT/'context_advisory_v1/source_lock.json')})
    return result


if __name__=='__main__':print(json.dumps(capture(),ensure_ascii=False))
