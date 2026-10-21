"""Finite explicit PR3 stages. No automatic production, retries or downloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback

W = Path('/home/inspur/aic_video_work')
R = W / 'content_choice_20261019_v1'
ROOT = R / 'code'
CODE = ROOT / 'improvement/content_choice_v1'
PY = W / 'env/qwen3vl_isolated_20260910/bin/python'
ASSETS = W / 'native_preference_20261019_v1/assets.private.json'
CFG = R / 'config.json'
OLD = W / 'native_preference_20261019_v1'
BASELINE = W / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'


def utc():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def ref(path):
    path = Path(path).resolve(strict=True)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def capture(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    return dict(exit_code=p.returncode, stdout=p.stdout.strip(), stderr=p.stderr.strip())


def resources():
    return dict(utc=utc(), host=socket.gethostname(), cpus=os.cpu_count(), load=os.getloadavg(),
        memory=[line for line in Path('/proc/meminfo').read_text().splitlines()
                if line.startswith(('MemTotal:', 'MemAvailable:'))],
        disk=shutil.disk_usage(W)._asdict(),
        gpu=capture(['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader']),
        gpu_apps=capture(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader']))


def stage(name, argv, seconds, *, gpu=False, scientific_stop=False):
    argv = list(map(str, argv))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT), TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='4' if gpu else '1', MKL_NUM_THREADS='4' if gpu else '1',
        OPENBLAS_NUM_THREADS='1')
    started = time.monotonic()
    with (R / (name + '.log')).open('x', encoding='utf-8') as log:
        p = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        save(R / (name + '_started.json'), dict(utc=utc(), pid=p.pid, argv=argv,
            start_ticks=Path('/proc/' + str(p.pid) + '/stat').read_text().rsplit(')', 1)[1].split()[19]))
        try:
            rc = p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL); p.wait(timeout=15)
            raise
    save(R / (name + '_terminal.json'), dict(utc=utc(), exit_code=rc,
        elapsed_seconds=time.monotonic() - started, argv=argv))
    if rc and not (scientific_stop and rc == 3):
        raise RuntimeError(name + ' exited ' + str(rc))
    return rc


def cli(which, *args):
    return [PY, '-B', CODE / 'run.py', '--stage', which, '--config', CFG,
            '--assets', ASSETS, *args]


def required_cpu():
    assert load(R / 'cpu_control_completion.json')['status'] == 'PASS_NEW_CPU_ASSET_PLAN'
    for path, status in [('linux_synthetic_cpu.json', 'PASS_SYNTHETIC_CPU'),
                         ('torch_cpu_checks.json', 'PASS'),
                         ('plan/plan.json', 'READY_FOR_EXPLICIT_BOUNDED_STAGES')]:
        assert load(R / path)['status'] == status, path
    assert (R / 'execution_review_admission.json').is_file(), 'Read-only implementation review must precede new GPU'
    gate = load(R / 'execution_review_admission.json')
    assert gate['approved_check_collection'] is True
    assert gate['code_manifest_ref'] == ref(CODE / 'code_manifest.json')


def gpu(name, command, seconds):
    required_cpu()
    snap = resources(); save(R / (name + '_resources.json'), snap)
    assert snap['host'] == 'inspur-NP5570M5'
    assert snap['gpu_apps']['exit_code'] == 0 and not snap['gpu_apps']['stdout'], 'External GPU conflict; no queue/repeated launcher'
    # Compare this actual remaining output allowance, not a hard-coded machine free-space threshold.
    output = sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
    maximum = load(CFG)['max_output_bytes']
    remaining = max(0, maximum - output)
    assert output < maximum and snap['disk']['free'] > remaining, 'Actual output budget cannot fit remaining capacity'
    asset = load(ASSETS)
    wrapper = Path(asset['gpu_wrapper_ref']['path'])
    job = 'content_choice_20261019_v1_' + name
    controller = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'
    assert not (controller/(job+'.resource.json')).exists(), 'Existing job must be inspected, never repeated'
    stage(name, [PY, '-B', wrapper, '--name', job, '--max-seconds', seconds,
        '--planned-output-bytes', remaining, '--capacity-reason',
        'Exact PR3 frozen stage, Linux resident reuse, no external GPU conflict. Current resources=' + json.dumps(snap),
        '--queue-seconds', '0', '--', *command], seconds + 120, gpu=True)
    result = load(controller / (job + '.resource.json'))
    ledger = W/'improvement_round1/gpu_ledger.jsonl'
    records = [json.loads(s) for s in ledger.read_text().splitlines() if s.strip()]
    records = [row for row in records if row.get('name') == job]
    assert result['status'] == 'completed' and result['exit_code'] == 0 and records == [result]
    return ref(controller / (job + '.resource.json'))


def main(mode):
    name = mode + '_control'
    phase = 'CLAIM'
    try:
        save(R / (name + '_started.json'), dict(utc=utc(), pid=os.getpid(), argv=sys.argv,
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
            parent_cuda=os.environ.get('CUDA_VISIBLE_DEVICES'), automatic_production=False))
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '0'
        snap = resources(); save(R / (name + '_resources.json'), snap)
        assert snap['host'] == 'inspur-NP5570M5'
        if mode == 'cpu':
            phase = 'SYNTHETIC'
            stage('cpu_synthetic', [PY, '-B', CODE / 'check_cpu.py', '--output', R / 'linux_synthetic_cpu.json'], 300)
            phase = 'TORCH'
            stage('torch_cpu', [PY, '-B', '-m', 'improvement.content_choice_v1.torch_checks',
                '--output', R / 'torch_cpu_checks.json'], 300)
            phase = 'PREFLIGHT'
            stage('preflight', cli('preflight'), 1860)
            phase = 'PLAN'
            stage('plan', cli('plan'), 1860)
            phase = 'DPO_DIAGNOSIS'
            stage('diagnose_dpo', cli('diagnose-dpo', '--dpo-completion', OLD / 'pilot/completion.json',
                '--dpo-review', OLD / 'review/review.json'), 1860)
            value = dict(status='PASS_NEW_CPU_ASSET_PLAN', new_qwen_calls=0,
                code_manifest_ref=ref(CODE / 'code_manifest.json'),
                synthetic_ref=ref(R / 'linux_synthetic_cpu.json'), torch_ref=ref(R / 'torch_cpu_checks.json'),
                plan_ref=ref(R / 'plan/plan.json'), dpo_diagnostic_ref=ref(R / 'diagnose_dpo/diagnostic.json'))
        elif mode == 'check':
            phase = 'COLLECT_CHECK'
            resource = gpu('collect_check', cli('collect', '--partition', 'check', '--plan', R / 'plan/plan.json',
                '--torch-checks', R / 'torch_cpu_checks.json'), 3600)
            phase = 'REVIEW_CONTRAST'
            rc = stage('review_contrast', cli('review', '--candidate', 'contrast', '--plan', R / 'plan/plan.json',
                '--collect-check', R / 'collect_check/completion.json'), 1860, scientific_stop=True)
            value = dict(status='CHECK_COLLECTION_AND_CONTRAST_REVIEW_COMPLETE', resource_ref=resource,
                collection_ref=ref(R / 'collect_check/completion.json'),
                review_ref=ref(R / 'review_contrast/review.json'), scientific_stop=(rc == 3))
        elif mode == 'observation':
            phase = 'OBSERVATION'
            resource = gpu('observation', cli('observation', '--plan', R / 'plan/plan.json',
                '--collect-check', R / 'collect_check/completion.json', '--torch-checks', R / 'torch_cpu_checks.json'), 2700)
            phase = 'REVIEW_OBSERVATION'
            rc = stage('review_observation', cli('review', '--candidate', 'observation', '--plan', R / 'plan/plan.json',
                '--collect-check', R / 'collect_check/completion.json',
                '--observation-run', R / 'observation/completion.json'), 1860, scientific_stop=True)
            value = dict(status='OBSERVATION_AND_REVIEW_COMPLETE', resource_ref=resource,
                review_ref=ref(R / 'review_observation/review.json'), scientific_stop=(rc == 3))
        elif mode == 'train_fit':
            assert load(R / 'critic_train_admission.json')['approved'] is True
            phase = 'COLLECT_TRAIN'
            resource = gpu('collect_train', cli('collect', '--partition', 'train', '--plan', R / 'plan/plan.json',
                '--collect-check', R / 'collect_check/completion.json', '--torch-checks', R / 'torch_cpu_checks.json'), 7200)
            phase = 'FIT'
            stage('fit', cli('fit', '--plan', R / 'plan/plan.json',
                '--collect-train', R / 'collect_train/completion.json'), 1860)
            phase = 'REVIEW_CRITIC'
            rc = stage('review_critic', cli('review', '--candidate', 'critic', '--plan', R / 'plan/plan.json',
                '--collect-check', R / 'collect_check/completion.json', '--fit-run', R / 'fit/completion.json'),
                1860, scientific_stop=True)
            value = dict(status='TRAIN_COLLECTION_FIT_AND_REVIEW_COMPLETE', resource_ref=resource,
                fit_ref=ref(R / 'fit/completion.json'), review_ref=ref(R / 'review_critic/review.json'), scientific_stop=(rc == 3))
        else:
            raise ValueError('Unknown finite control mode')
        baseline = ref(BASELINE)
        assert baseline['bytes'] == 384630
        assert baseline['sha256'] == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
        save(R / (name + '_completion.json'), dict(utc=utc(), **value,
            baseline_ref=baseline, automatic_production=False, new_zip=0))
    except BaseException as exc:
        save(R / (name + '_failure.json'), dict(utc=utc(), phase=phase, error=str(exc),
            error_type=type(exc).__name__, traceback=traceback.format_exc(), automatic_retry=False,
            failed_output_to_empty=False, automatic_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['cpu','check','observation','train_fit'], required=True)
    main(parser.parse_args().mode)
