"""Finite Linux sequence: INIT43 -> explicit remaining555 -> TRAINED43 -> CPU review.

No retries, model selection, threshold scan, production426, packaging or scheduler.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

W = Path('/home/inspur/aic_video_work')
R = W/'bottleneck_24h_20261019_v1'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = str(W/'env/qwen3vl_isolated_20260910/bin/python')


def read(p):return json.loads(Path(p).read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def ref(p):return dict(path=str(Path(p)),bytes=Path(p).stat().st_size,sha256=sha(p))


def bound(r):
    p = Path(r['path']).resolve()
    assert p.is_relative_to(W) and p.is_file() and sha(p) == r['sha256']
    return p


def save(p,x):
    with Path(p).open('x') as f:
        json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.flush();os.fsync(f.fileno())


def event(stage, **data):
    with (R/'summary_sequence_12.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),stage=stage,**data))+'\n')
        f.flush();os.fsync(f.fileno())


def terminal(job):
    p = RUN/'controller'/(job+'.resource.json'); row = read(p)
    matches = [json.loads(x) for x in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
               if x.strip() and json.loads(x).get('name') == job]
    assert matches == [row] and row['status'] == 'completed' and row['exit_code'] == 0
    return ref(p)


def launch_gpu(stage, job, args, maximum, planned, reason):
    # Scientific budget, current job conflict and estimated outputs are examined
    # for this stage; no fixed utilization/memory/disk admission threshold.
    assert datetime.now(timezone.utc) < datetime(2026,10,19,11,52,37,tzinfo=timezone.utc)
    assert not (RUN/'controller'/(job+'.resource.json')).exists()
    assert not any(json.loads(x).get('name') == job for x in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip())
    resource = dict(host=os.uname().nodename,load=os.getloadavg(),disk_free=shutil.disk_usage(W).free,
        meminfo=Path('/proc/meminfo').read_text().splitlines()[:3],
        gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip(),
        gpu_apps=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip())
    assert resource['host'] == 'inspur-NP5570M5'
    assert not resource['gpu_apps'], 'External GPU app appeared; STOP without touching it or silently launching'
    assert resource['disk_free'] > planned, 'Actual planned output does not fit currently available disk'
    command = [PY,str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',job,
        '--max-seconds',str(maximum),'--planned-output-bytes',str(planned),'--capacity-reason',
        reason+' Actual dynamic resources: '+json.dumps(resource),'--queue-seconds','120','--',PY,'-B',*map(str,args)]
    save(R/(stage+'_launch.json'),dict(command=command,resource=resource,utc=datetime.now(timezone.utc).isoformat()))
    event('BEGIN_'+stage,job=job)
    with (R/(stage+'_wrapper.log')).open('xb') as log:
        process = subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1'))
    assert process.returncode == 0, stage+' wrapper failed; no automatic retry'
    resource_ref = terminal(job); event('COMPLETE_'+stage,resource_ref=resource_ref)
    return resource_ref


def cpu(stage,args):
    with (R/(stage+'.log')).open('xb') as log:
        process = subprocess.run([PY,'-B',*map(str,args)],stdin=subprocess.DEVNULL,stdout=log,
            stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    assert process.returncode == 0,stage+' CPU failed; preserve all successes and stop'


def main():
    reg = read(R/'summary_sequence_registration_12.json')
    for r in reg['code'].values():bound(r)
    bound(reg['generation_registration']); bound(reg['remaining_registration'])
    save(R/'summary_sequence_claim_12.json',dict(pid=os.getpid(),registration=ref(R/'summary_sequence_registration_12.json'),
        utc=datetime.now(timezone.utc).isoformat(),automatic_retries=False,production_or_package=False))
    gen = read(bound(reg['generation_registration']))
    generation = bound(gen['code']['summary_generate.py']); qa = bound(gen['code']['summary_output_qa.py'])
    init_resource = launch_gpu('summary_init43_12',gen['job_names']['INIT_TIME'],[generation,'--role','INIT_TIME'],1200,16777216,
        'First same-new-input originalTIME43 frozen control. No labels/training. Existing retained context RAM inputs, no media/processor. Pilot engineering completed21402MiB. Only raw tokens/JSON and receipts saved.')
    cpu('summary_init43_first_QA_12',[qa,'--role','INIT_TIME'])
    init_qa = R/'summary_generation_10/INIT_TIME/first_independent_output_QA.json'
    assert read(init_qa)['status'] == 'PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA'
    # No labels or metrics are read before/during the fixed final559 training.
    pilot = read(R/'summary_model_06/pilot_completion.json')
    assert pilot['status'] == 'PASS_SUMMARY_PILOT4_ENGINEERING_ONLY' and pilot['completed_updates'] == 4 and pilot['successful_micro'] == 16
    assert sha(R/'summary_model_06/progress.pt') == pilot['progress_ref']['sha256']
    remaining = read(bound(reg['remaining_registration']))
    admission = dict(status='ADMIT_EXPLICIT_SUMMARY_REMAINING',registration_ref=reg['remaining_registration'],
        pilot_completion_ref=ref(R/'summary_model_06/pilot_completion.json'),progress_ref=pilot['progress_ref'],
        completed_updates=4,remaining_updates=555,schedule_sha256=pilot['schedule_sha256'],
        max_gpu_seconds=9000,deadline_utc='2026-10-19T15:52:37Z',same_input_INIT43_completed=init_resource,
        same_input_INIT43_output_QA=ref(init_qa),dev_labels_or_metrics_read=False,
        reason='Pilot278.47s incl model/base hash/reload; 16backward~45s and4 updates persisted. Remaining2220micro expected~2h plus fixed overhead, within9000s and original24h. No checkpoint/quality selection.',
        utc=datetime.now(timezone.utc).isoformat())
    save(R/'summary_remaining_admission.json',admission)
    remaining_code = bound(remaining['code']['summary_gpu.py'])
    final_resource = launch_gpu('summary_remaining555_12',reg['remaining_job'],[remaining_code,'--root',R,'--phase','remaining'],
        9000,reg['remaining_planned_output_bytes'],
        'Only2220 not-yet-trained micro/555 updates; adopt actual step4 optimizer/RNG and immutablepilot, never rerun16. Fixed full2236 epoch. Actual pilot peak21.4GB, all tensors/reload exact; rolling checkpoint+onefinal adapter only. Protect CONTROL5 STOP, no external GPU conflict.')
    completion = R/'summary_model_06/remaining_completion.json'; final = read(completion)
    assert final['status'] == 'PASS_SUMMARY_FINAL559_SINGLE_EPOCH' and final['completed_updates'] == 559 and final['successful_micro'] == 2236
    bound(final['adapter_weights_ref'])
    save(R/'summary_final_weights_frozen_10.json',dict(status='FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS',
        final_adapter_ref=final['adapter_weights_ref'],training_completion_ref=ref(completion),resource_ref=final_resource,
        original_recipe_final_only=True,dev_labels_or_metrics_read=False,utc=datetime.now(timezone.utc).isoformat()))
    trained_resource = launch_gpu('summary_trained43_12',gen['job_names']['TRAINED'],[generation,'--role','TRAINED'],1200,16777216,
        'Once-only fixed final559 model on same43 new inputs; no adaptation/checkpoint selection. Frozen base and originalTIME retained. Natural valid empty allowed, failure never empty; same grammar/native contract as INIT.')
    cpu('summary_trained43_first_QA_12',[qa,'--role','TRAINED'])
    records = {role:read(R/'summary_generation_10'/role/'completion.json') for role in ['INIT_TIME','TRAINED']}
    manifest = dict(dev_prepared_ref=read(bound(gen['first_dev_input_acceptance_ref']))['prepared'],
        baseline_human_adoption_ref=gen['baseline_human_adoption_ref'],
        role_output_refs={role:x['outputs'] for role,x in records.items()},
        role_completion_refs={role:ref(R/'summary_generation_10'/role/'completion.json') for role in records},
        role_resource_refs=dict(INIT_TIME=init_resource,TRAINED=trained_resource),
        role_output_QA_refs={role:ref(R/'summary_generation_10'/role/'first_independent_output_QA.json') for role in records},
        initial_TIME_ref=gen['initial_TIME_ref'],final_adapter_ref=final['adapter_weights_ref'],
        frozen_selection_ref=ref(R/'summary_final_weights_frozen_10.json'))
    save(R/'summary_evaluation_manifest_12.json',manifest)
    cpu('summary_evaluation_12',[bound(gen['code']['evaluate_summary.py']),'--root',R,'--generation-manifest',R/'summary_evaluation_manifest_12.json'])
    save(R/'summary_sequence_completion_12.json',dict(status='COMPLETE_FIXED_FINAL559_MATCHED_DEV8_ONCE_REQUIRES_MAIN_REVIEW',
        evaluation_result=ref(R/'evaluation_10/result.json'),resources=dict(INIT_TIME=init_resource,TRAINING=final_resource,TRAINED=trained_resource),
        automatic_production=False,automatic_package=False,quality_or_official_improvement_not_asserted=True,
        utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    try:main()
    except BaseException as e:
        p = R/'summary_sequence_failure_12.json'
        if not p.exists():save(p,dict(error=repr(e),traceback=traceback.format_exc(),
            automatic_retry=False,preserve_all_successes=True,production_or_package=False,
            utc=datetime.now(timezone.utc).isoformat()))
        raise
