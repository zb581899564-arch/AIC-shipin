"""Fix checkpoint/source-version mismatch before the first learned forward.

Adopt the exact downloaded checkpoint and successful operator parity. All old
failures/code remain; candidate method and quality gates are not changed.
"""
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import subprocess
import traceback
from control import ROOT, PY, read, checked, write, reference


def original_controller():
    spec = importlib.util.spec_from_file_location('original_s0_stages', ROOT / 'code_run/controller.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def cpu(name, script):
    paths = ':'.join(str(ROOT / d) for d in ['code_v7', 'code_run', 'code_v2', 'code'])
    code = "import sys,runpy;sys.path.insert(0,'" + str(ROOT / 'code_v7') + "');runpy.run_path('" + str(script) + "',run_name='__main__')"
    command = [str(PY), '-u', '-B', '-c', code]
    with (ROOT / (name + '.log')).open('x') as stream:
        done = subprocess.run(command, cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=paths,
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'), stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT)
    write(ROOT / (name + '_terminal.json'), dict(exit_code=done.returncode, argv=command))
    if done.returncode:
        raise RuntimeError(name + ' actually failed; no successful operation repeated')


def main():
    write(ROOT / 'remaining07_claim.json', dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat()))
    previous = (ROOT / 'strict_weight.log').read_text()
    comparison = read(ROOT / 'author_runtime07_comparison.json')
    if 'Unexpected key(s)' not in previous or 'FC_layers.0.1.running_mean' not in previous:
        raise ValueError('Not the registered source/checkpoint BatchNorm version mismatch')
    if not comparison['roi_forward_kernel_body_identical'] or not comparison['rod_forward_kernel_body_identical']:
        raise ValueError('Cannot adopt operator parity for a changed kernel')
    if (ROOT / 'input_acceptance.json').exists() or (ROOT / 'GPU_launch.json').exists():
        raise ValueError('This recovery only precedes first successful real inputs/model calls')
    write(ROOT / 'remaining07_registration.json', dict(reason='Use same exact author-linked commit as checkpoint, including its BatchNorm head; strict load stays strict',
        prior_failure=reference(ROOT / 'controller_failure.json'), original_log=reference(ROOT / 'strict_weight.log'),
        checkpoint=reference(ROOT / 'weight_acceptance06.json'), author_network=reference(ROOT / 'author_runtime07/croppingModel.py'),
        source_semantics_comparison=reference(ROOT / 'author_runtime07_comparison.json'),
        preprocessing_difference='Only explicit float casts to image_size/min dimension; first author-specific synthetic check occurs before any real inputs',
        candidate_grid_or_gates_changed=False, first_research_forward_calls_before_recovery=0, old_failure_preserved=True))
    original = original_controller()
    before = original.baseline()
    deadline = datetime.fromisoformat(read(ROOT / 'registration.json')['compatibility_deadline_UTC'])
    if datetime.now(timezone.utc).timestamp() + 600 > deadline.timestamp():
        raise ValueError('Compatibility window cannot fit fixed first profile')
    cpu('strict_weight07', ROOT / 'code_v7/load_weight.py')
    cpu('first_inputs07', ROOT / 'code_run/make_inputs.py')
    write(ROOT / 'source_lock.json', dict(protocol=reference(ROOT / 'protocol.json'),
        engineering_amendment=reference(ROOT / 'remaining07_registration.json'),
        weight=reference(ROOT / 'learned_weight_acceptance.json'), inputs=reference(ROOT / 'input_acceptance.json'),
        code={str(p.relative_to(ROOT)): reference(p) for folder in ['code_v7', 'code_run', 'code_v2', 'code', 'author_runtime07']
              for p in sorted((ROOT / folder).rglob('*.py'))}, baseline=before,
        operator_parity=reference(ROOT / 'compat_cpu_acceptance_v2.json'), author_source_manifest=reference(ROOT / 'source_runtime07.jsonl')))
    record = original.run_gpu()
    cpu('independent_review07', ROOT / 'code_run/review.py')
    if original.baseline() != before:
        raise ValueError('Protected40.47 modified')
    for item in read(ROOT / 'source_lock.json')['code'].values():
        checked(item)
    result = dict(status=read(ROOT / 'review.json')['status'], summary=read(ROOT / 'review.json')['summary'],
        GPU_charged_seconds=record['charged_seconds'], wrapper_peak_MiB=record['sampled_peak_memory_mib'],
        model=read(ROOT / 'model_completion.json'), original_baseline_unchanged=True, new_ZIP=0,
        automatic_production=False, original_source_independence='UNKNOWN',
        actual_author_network_commit='f6f925dadaf3c975f84c422ad575e0c92dc87320',
        prior_controller_failure_adopted_not_overwritten=True, completed_UTC=datetime.now(timezone.utc).isoformat())
    write(ROOT / 'completion.json', result)
    write(ROOT / 'short_result.json', result)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'remaining07_failure.json', dict(status='ACTUAL_REMAINING_FAILURE_KEEP_SUCCESS', traceback=traceback.format_exc()))
        raise
