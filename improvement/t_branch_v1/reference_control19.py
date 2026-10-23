"""Unique original-reference correction: accepted prefixes ->14 tasks -> independent QA."""
import os
from pathlib import Path
import subprocess
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'reference_control19'
CODE = Path(__file__).parent
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
JOB = 'T_first_correct_VERIFY_prompt14_20261022_v19'


def execute(name, gpu):
    command = [str(PY), '-B', '-u', str(CODE / name)]
    if gpu:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                        '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute exists; accepted inputs remain preserved')
        save(OUT / 'resource_admission.json', dict(compute_apps=apps,
            processes=subprocess.check_output(['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,args'], text=True),
            GPU=subprocess.check_output(['nvidia-smi'], text=True),
            RAM=subprocess.check_output(['free', '-b'], text=True),
            disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True),
            basis='One frozen8B original TIME,14 first correct prompts; prior actual22.1GB peak, no backward; adopt74BASE and10B0; no media or tensors copied'))
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '600',
            '--planned-output-bytes', '4000000', '--capacity-reason',
            'Correct14 external task prefixes; no repeated old tasks/BASE/B0, no training or test data; actual new CPU prompt acceptance complete',
            '--queue-seconds', '0', '--'] + command
    label = Path(name).stem
    with (OUT / (label + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (label + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        code = process.wait()
    save(OUT / (label + '_terminal.json'), dict(exit_code=code))
    if code:
        raise RuntimeError('Actual correction stage failed: ' + label)


def main():
    inputs = read(ROOT / 'reference_input18/CPU_completion.json')
    if inputs['state'] != 'PASS_FIRST_CORRECT_TASK_PREFIX14' or len(inputs['cases']) != 14:
        raise ValueError('All14 first correct task inputs must pass before model admission')
    OUT.mkdir()
    old = WORK / 'general_highlight_supervision_20261021_v1/baseline_bridge57'
    baseline = read(old / 'registration.json')['protected_baseline']
    check(baseline)
    save(OUT / 'registration.json', dict(
        purpose='Fix a proved external-reference prompt defect, no new candidate or training',
        original_inputs=identity(ROOT / 'reference_input18/CPU_completion.json'),
        protected_baseline=baseline, original_source=read(old / 'registration.json')['source'],
        first_correct_VERIFY_calls=14, repeated_wrong_task_calls=0,
        BASE_batches_adopted=74, repeated_BASE_or_B0_calls=0, GPU_max_seconds=600,
        all_old_raw_failures_costs_and_receipts_preserved=True,
        no_automatic426_or_package=True))
    names = ['reference_control19.py', 'reference_gpu19.py', 'reference_review20.py',
             'reference_data18.py', 'prompt_contract13.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={n: identity(CODE / n) for n in names},
        original_frozen_source_lock=identity(old / 'source_input_lock.json'),
        CPU=identity(ROOT / 'reference_input18/CPU_completion.json'),
        registration=identity(OUT / 'registration.json'), wrapper=identity(WRAPPER)))
    execute('reference_gpu19.py', True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [__import__('json').loads(line) for line in
              (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0 or
            [r for r in ledger if r.get('name') == JOB] != [resource]):
        raise ValueError('Unique natural GPU terminal or fee ledger differs')
    execute('reference_review20.py', False)
    audit = read(OUT / 'independent_CPU_audit.json')
    if audit['state'] != 'PASS' or audit['CUDA_initialized'] or audit['cases'] != 14:
        raise ValueError('Independent first corrected task review failed')
    check(baseline)
    save(OUT / 'completion.json', dict(state='CORRECTED_EXTERNAL_REFERENCE_COMPLETE',
        review=identity(OUT / 'review.json'), independent_CPU=identity(OUT / 'independent_CPU_audit.json'),
        GPU_seconds=resource['charged_seconds'], first_correct_model_calls=14,
        adopted_BASE_batches=74, training_updates=0, new_ZIP=0, protected_baseline_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                all_successful_inputs_calls_and_raw_preserved=True, no_automatic_retry=True))
        raise
