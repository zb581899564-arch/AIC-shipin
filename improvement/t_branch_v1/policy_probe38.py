"""Explicit remaining35: original control model succeeded, CPU import fixed by37."""
from pathlib import Path
import time
import traceback

from t_io import ROOT, WORK, identity, read, save

OUT = ROOT / 'policy_probe38'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
JOB = 'T_real_causal_actor_backward_probe_20261022_v35'


def wait_review():
    launch = read(ROOT / 'pilot_review37_launch.json')
    end = time.monotonic() + 1200
    while not (ROOT / 'pilot_review37/completion.json').exists():
        if (ROOT / 'pilot_review37/failure.json').exists():
            raise RuntimeError('Actual remaining CPU37 failure, no GPU launch')
        stat = Path('/proc') / str(launch['pid']) / 'stat'
        if not stat.exists() or stat.read_text().rsplit(')', 1)[1].split()[19] != launch['start_ticks']:
            raise RuntimeError('CPU37 handle missing without terminal, no relaunch')
        if time.monotonic() > end:
            raise TimeoutError('CPU37 wait elapsed; keep its actual process untouched')
        time.sleep(5)


def main():
    old = ROOT / 'policy_probe35'
    failure = read(old / 'failure.json')
    if 'Actual prior-control failure' not in failure['traceback']:
        raise ValueError('Expected original35 pre-GPU failure absent')
    if (old / 'policy_probe34_launch.json').exists() or (RUN / 'controller' / (JOB + '.resource.json')).exists():
        raise ValueError('Existing probe task must be inspected/adopted, never duplicated')
    OUT.mkdir()
    save(OUT / 'registration.json', dict(original_protocol=identity(old / 'registration.json'),
        actual_prior_wait_failure=identity(old / 'failure.json'), original35_GPU_calls=0,
        unchanged_first_TF_calls=4, unchanged_actor_forward=1, backwards=1, optimizer_updates=0,
        unchanged_GPU_seconds_max=600, new_scientific_variant=False,
        only_first_remaining_probe_after_CPU37=True))
    wait_review()
    import policy_probe35 as controller
    controller.OUT = OUT
    names = ['policy_probe38.py', 'policy_probe38_gpu.py', 'policy_probe38_review.py', 'policy_probe35.py',
        'policy_probe34.py', 'policy_forward34.py', 'policy_replay36.py', 'actor_roles33.py', 'policy_contract.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(Path(__file__).parent / name) for name in names},
        original_protocol=identity(old / 'registration.json'), original_control=identity(ROOT / 'pilot_review37/completion.json'),
        registration=identity(OUT / 'registration.json')))
    controller.execute('policy_probe38_gpu.py', True)
    controller.execute('policy_probe38_review.py')
    import json
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Natural unique first probe completion differs')
    save(OUT / 'completion.json', dict(state='REAL8B_CAUSAL_BACKWARD_ENGINEERING_COMPLETE',
        audit=identity(OUT / 'independent_CPU_audit.json'), GPU_seconds=resource['charged_seconds'],
        first_TF_calls=5, first_backward=1, optimizer_updates=0,
        original35_failure_preserved=True, no_quality_or_training_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                preserve_all_raw_successes=True, no_automatic_retry=True))
        raise
