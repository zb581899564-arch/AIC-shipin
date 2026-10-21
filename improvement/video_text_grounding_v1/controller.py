"""One bounded pilot; no automatic retries, production or model selection."""
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
from common import ROOT, WORK, ref, read, write

PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = WRAPPER.parent.parent / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'
JOB = 'independent_video_text_xclip8_20261021_v1'


def stage(name, script, gpu=False):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '',
          PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    command = [str(PY), '-u', '-B', str(ROOT / 'code' / script)]
    if gpu:
        from resource_context06 import live_reason
        capacity_reason = live_reason()
        assert not (RESOURCE / f'{JOB}.resource.json').exists()
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1200',
              '--planned-output-bytes', '90000000', '--capacity-reason',
              capacity_reason,
              '--queue-seconds', '0', '--'] + command
    started = time.monotonic()
    with (ROOT / f'{name}.log').open('x') as log:
        child = subprocess.Popen(command, env=env, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT)
        ticks = Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        write(ROOT / f'{name}_launch.json', dict(pid=child.pid, start_ticks=ticks, argv=command))
        code = child.wait()
    write(ROOT / f'{name}_terminal.json', dict(exit_code=code, seconds=time.monotonic() - started))
    if code:
        raise RuntimeError(f'{name} naturally failed; retain all successful results, no retry')


def main():
    write(ROOT / 'controller_claim.json', dict(pid=os.getpid(), first_fixed_video_semantic_pilot=True))
    for name, script in [('assets', 'assets.py'), ('model_gate', 'model_io.py'),
                         ('torch', 'contracts.py'), ('input', 'prepare.py')]:
        stage(name, script)
    write(ROOT / 'source_input_lock.json', dict(protocol=ref(ROOT / 'protocol.json'),
          code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))},
          assets=ref(ROOT / 'download_acceptance.json'), model=ref(ROOT / 'model_acceptance.json'),
          torch=ref(ROOT / 'torch_contracts.json'), input=ref(ROOT / 'input_acceptance.json'),
          wrapper=ref(WRAPPER)))
    stage('gpu', 'infer.py', True)
    record = read(RESOURCE / f'{JOB}.resource.json')
    ledger = [json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
    assert record['status'] == 'completed' and record['exit_code'] == 0
    assert [r for r in ledger if r.get('name') == JOB] == [record]
    stage('review', 'review.py')
    stage('audit', 'audit.py')
    result = read(ROOT / 'review.json')
    baseline = WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
    assert ref(baseline)['sha256'] == read(ROOT / 'protocol.json')['protected_sha256']
    identity = read(ROOT / 'model_acceptance.json')
    inference = read(ROOT / 'inference_completion.json')
    write(ROOT / 'completion.json', dict(status=result['status'], tests=result['tests'],
          source_macro_AP=result['source_macro_AP'], static_clip_macro=result['static_clip_macro'],
          parameters=identity['parameters'], combined_parameters=identity['with_protected_baseline'],
          charged_seconds=record['charged_seconds'], wrapper_sampled_peak_mib=record.get('sampled_peak_memory_mib'),
          peak_allocated_bytes=inference['peak_allocated_bytes'],
          video_forward_batches=inference['actual_video_forward_batches'],
          text_forward_batches=1, real_cells=512, reverse_cells=512,
          review=ref(ROOT / 'review.json'), audit=ref(ROOT / 'independent_cpu_audit.json'),
          baseline_unchanged=True, new_updates=0, new_zip=0, production_allowed=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'failure.json', dict(status='ACTUAL_FAILURE_PRESERVED', traceback=traceback.format_exc()))
        raise
