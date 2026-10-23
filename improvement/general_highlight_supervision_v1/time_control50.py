"""Bounded original-TIME reference before any production admission for routed experts."""
import os
from pathlib import Path
import json
import subprocess
import traceback

from time_control50_common import ROOT,ADMISSION,WORK,RUN,PY,WRAPPER,JOB,SPORT,read,ref,save,checked

CODE=Path(__file__).parent


def run(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/name)]
    if gpu:
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('Protect external GPU task; no competing launch')
        save(ROOT/'resource_admission.json',dict(actual_compute_apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'],text=True),RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            reason='Only original8B on12 first external diving windows; previous original native64 peak21890MiB, no external compute, cached CPU inputs accepted; Java protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','600','--planned-output-bytes','16000000',
            '--capacity-reason','One actual external held sport, first originalTIME native64 reference, no training or production, bounded12 calls',
            '--queue-seconds','0','--']+command
    stage='gpu' if gpu else ('prepare' if 'prepare' in name else 'review')
    with (ROOT/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(stage+'_launch.json'),dict(command=command,pid=process.pid,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(stage+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual reference stage failed: '+stage)


def main():
    ROOT.mkdir()
    if read(ADMISSION/'semantic_route48/completion.json')['state']!='ROUTING_SIGNAL_REQUIRES_EXACT40_47_BRIDGE':
        raise ValueError('No prior actual narrow routing evidence')
    source=next(row for row in read(SPORT/'registration.json')['sources'] if row['role']=='held_sport')
    baseline=read(ADMISSION/'media24/registration.json')['protected_baseline'];checked(baseline)
    save(ROOT/'protocol.json',dict(source=source['source'],purpose='First stronger originalTIME native64 benchmark for routed athlete expert',
        original_B0_and_frozen_D8_controls=True,not_exact40_47_yet=True,
        missing_full_baseline='Original VERIFY/dual-refinement and context-semantic additions',
        unique_new_calls_max=12,GPU_seconds_max=600,no_training=True,no_automatic_production=True,
        source_roles_and_all_old_STOPs_unchanged=True,
        selection_before_any_human_known_mask=True,no_query_GT_in_inference=True,
        existing_frozen_router_and_expert_no_threshold_changes=True))
    save(ROOT/'registration.json',dict(source=source,protected_baseline=baseline,
        original_sport=ref(SPORT/'registration.json'),routing=ref(ADMISSION/'semantic_route48/completion.json'),
        preparation_budget_reason='Only12 original native64 windows, compressed lossless cache; failed LVSum7 RGB retired by immutable exact manifest, other media/proofs kept',
        retirement=ref(ADMISSION/'retire_failed_rgb49/completion.json')))
    run('time_control50_prepare.py')
    completion=read(ROOT/'CPU_completion.json')
    if not 0<completion['windows']<=12:raise ValueError('Actual native window budget differs')
    names=['common.py','time_control50_common.py','time_control50_prepare.py','time_control50_gpu.py','time_control50_review.py','time_control50.py']
    save(ROOT/'source_input_lock.json',dict(code={name:ref(CODE/name) for name in names},
        protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),CPU=ref(ROOT/'CPU_completion.json'),
        original_runtime=ref(WORK/'temporal_refinement_pilot_20261011/dev_01/runtime.py'),
        original_config=ref(RUN/'b_score_aligned_package_v4/config.json'),wrapper=ref(WRAPPER)))
    run('time_control50_gpu.py',True)
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Unique natural reference GPU ledger differs')
    run('time_control50_review.py');checked(baseline)
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        GPU_seconds=record['charged_seconds'],actual_new_calls=completion['windows'],baseline_unchanged=True,new_ZIP=0))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_all_success_and_raw=True))
        raise
