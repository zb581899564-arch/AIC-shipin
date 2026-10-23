"""One explicit remaining-only recovery under the unchanged v6 asset/code lock.

The first five CPU sources already succeeded. Their immutable journal entries
are reused, so their adopted historical GPU timings cannot contaminate the next
five fresh CPU samples. The general forecast fix is committed separately in the
same change but is NOT injected into this frozen v6 run.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import time


WORK = Path('/home/inspur/aic_video_work')
REPO = WORK / 'final_sprint_temporal_field_checkout_20261023_v6'
RUN = WORK / 'final_sprint_temporal_r_production_20261023_v6'
OLD = WORK / 'final_sprint_temporal_field_chain_20261023_v6'
CONTROL = WORK / 'final_sprint_r_apex_remaining_recovery_20261023_v7'
COMMIT = '8dcde128be0ffe2df3ccba75d69929b7a9769a6f'
PYTHON = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = 'edb481022ce2407082d7c2a496853ed1'


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    with (CONTROL / name).open('x') as stream:
        json.dump(value, stream, indent=2)


def phase_attempts():
    return {str(p) for p in (RUN / 'journal/tasks').glob('phase_*/attempts/*/claim.json')}


def main():
    prior = read(RUN / 'wrappers' / WRAPPER / 'completion.json')
    assert prior['child_exit_code'] == 1 and prior['work_terminated']
    assert 'Stage wall-time budget exhausted' in (RUN / 'wrappers' / WRAPPER / 'command.log').read_text()
    failed = read(OLD / 'r_time_apex_run_terminal.json')
    assert failed['exit_code'] == 1
    original_start = datetime.fromisoformat(read(OLD / 'r_time_apex_run_started.json')['at'])
    absolute_end = original_start + timedelta(seconds=1800)
    successful = sorted((RUN / 'candidates/r_time_apex/sources').glob('*/result.json'))
    assert len(successful) == 5
    originals = {str(p): p.read_bytes() for p in successful}
    phases = phase_attempts()
    assert read(OLD / 'r_time_event_ready.json')['source_count'] == 426
    save('claim.json', dict(runtime_commit=COMMIT, runtime_unchanged=True,
        old_failed_wrapper=WRAPPER, old_cost_seconds=failed['wall_seconds'],
        original_absolute_end=absolute_end.isoformat(), already_successful_sources=5,
        no_new_inference=True, at=datetime.now(timezone.utc).isoformat(), pid=os.getpid()))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(WORK / 'final_sprint_optional_assets_20261023/python') + os.pathsep + str(REPO))
    common = ['--assets', str(RUN / 'assets.json'), '--expected-commit', COMMIT,
              '--candidate', 'r_time_apex']
    for name, module, action in [('run', 'supervise', ['--action', 'run']),
                                 ('package', 'cli', ['package'])]:
        left = min(1800 - failed['wall_seconds'],
                   (absolute_end - datetime.now(timezone.utc)).total_seconds())
        assert left > (180 if name == 'run' else 0), 'Original CPU control budget exhausted'
        command = [str(PYTHON), '-m', 'improvement.final_sprint_v1.' + module]
        command += action + common if module == 'cli' else common + action
        started = time.monotonic()
        with (CONTROL / (name + '.log')).open('xb') as stream:
            child = subprocess.Popen(command, cwd=REPO, env=env, stdout=stream, stderr=subprocess.STDOUT)
            try:
                code = child.wait(timeout=left - (180 if name == 'run' else 0))
            except subprocess.TimeoutExpired:
                child.terminate()
                code = child.wait(timeout=90)
        save(name + '_terminal.json', dict(exit_code=code, wall_seconds=time.monotonic() - started))
        assert code == 0, name + ' failed'
    assert phase_attempts() == phases, 'A cached-only recovery unexpectedly created inference claims'
    assert all(Path(p).read_bytes() == data for p, data in originals.items())
    delivery = read(RUN / 'candidates/r_time_apex/package/delivery.json')
    assert delivery['source_count'] == 426
    save('completion.json', dict(delivery=delivery, new_model_calls=0,
        old_five_successes_unchanged=True, original_budget_not_extended=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        import traceback
        save('failure.json', dict(traceback=traceback.format_exc()))
        raise
