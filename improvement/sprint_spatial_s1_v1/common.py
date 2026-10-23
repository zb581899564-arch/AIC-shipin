"""Explicit S1 paths, immutable receipts and bounded shared-stage execution."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1')
WORK = ROOT.parent
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WIDTH = WORK / 'gnmc_width_iteration_20261013_v1'
TRAIN200 = WORK / 'gnmc_width_sft_iteration_20261013_v1'
EXPAND = WORK / 'gnmc_width_sft1000_iteration_20261013_v1'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = WRAPPER.parent.parent / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'
BASELINE = WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
BASELINE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
ARMS = ('W10', 'W01', 'W11')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(WORK):
        raise ValueError('Asset outside project work root')
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def checked(value):
    path = Path(value['path']).resolve(strict=True)
    if not path.is_relative_to(WORK) or digest(path) != value['sha256']:
        raise ValueError('Asset path or bytes changed')
    if 'bytes' in value and path.stat().st_size != value['bytes']:
        raise ValueError('Asset size changed')
    return path


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def runtime_paths():
    sys.path[:0] = [str(RUN / p) for p in ('b_score_aligned_package_v4', 'baseline_a_pts_v1',
                     'baseline_a_pts_v1/vendor', 'temporal_sft8b_v1')]


def signatures(values):
    import torch
    return {key: dict(shape=list(value.shape), dtype=str(value.dtype), sha256=hashlib.sha256(
        value.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
        for key, value in values.items()}


def run_stage(name, script, args=(), gpu_seconds=None):
    command = [str(PY), '-u', '-B', str(ROOT / 'code' / script), *args]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu_seconds else '',
        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    if gpu_seconds:
        from resources import admission
        job = 's1_' + name + '_20261021_v1'
        reason = admission(name)
        if (RESOURCE / f'{job}.resource.json').exists():
            raise FileExistsError('Unique GPU job already exists')
        command = [str(PY), '-B', str(WRAPPER), '--name', job, '--max-seconds', str(gpu_seconds),
            '--planned-output-bytes', str(read(ROOT / 'protocol.json')['remaining_output_budget_bytes']),
            '--capacity-reason', reason, '--queue-seconds', '0', '--'] + command
    start = time.monotonic()
    with (ROOT / f'{name}.log').open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT)
        stat = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
        write(ROOT / f'{name}_launch.json', dict(pid=process.pid, start_ticks=stat[19], argv=command))
        code = process.wait()
    write(ROOT / f'{name}_terminal.json', dict(exit_code=code, seconds=time.monotonic() - start))
    if code:
        raise RuntimeError(f'{name} naturally failed; no successful operation retried')
    if gpu_seconds:
        record = read(RESOURCE / f'{job}.resource.json')
        matches = [r for r in map(json.loads, LEDGER.read_text().splitlines()) if r.get('name') == job]
        if record['status'] != 'completed' or record['exit_code'] != 0 or matches != [record]:
            raise ValueError('Unique GPU terminal/ledger mismatch')
        return record


def baseline_identity():
    value = ref(BASELINE)
    if value['bytes'] != 384630 or value['sha256'] != BASELINE_SHA:
        raise ValueError('Protected baseline changed')
    return value
