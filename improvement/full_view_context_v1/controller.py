"""One bounded first input/encoder/review chain; never retries or produces ZIPs."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
from common import ROOT, WORK, PY, WRAPPER, RESOURCE, LEDGER, JOB, checked, read, ref, write


def stage(name, gpu=False):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    command = [str(PY), '-u', '-B', str(ROOT / 'code' / f'{name}.py')]
    if gpu:
        from resources import live_reason
        reason = live_reason()
        assert not (RESOURCE / f'{JOB}.resource.json').exists()
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '600',
                   '--planned-output-bytes', str(read(ROOT / 'protocol.json')['planned_output_bytes']),
                   '--capacity-reason', reason, '--queue-seconds', '0', '--'] + command
    start = time.monotonic()
    with (ROOT / f'{name}.log').open('x') as log:
        process = subprocess.Popen(command, env=env, cwd=ROOT, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT)
        ticks = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        write(ROOT / f'{name}_launch.json', dict(pid=process.pid, start_ticks=ticks, argv=command))
        exit_code = process.wait()
    write(ROOT / f'{name}_terminal.json', dict(exit_code=exit_code, seconds=time.monotonic() - start))
    assert exit_code == 0, f'{name} naturally failed; preserve all successful outputs'


def main():
    write(ROOT / 'controller_claim.json', dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat()))
    baseline = WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
    baseline_before = ref(baseline)
    protocol = read(ROOT / 'protocol.json')
    assert baseline_before['sha256'] == protocol['protected_sha256'] and baseline_before['bytes'] == 384630
    stage('prepare')
    inputs = read(ROOT / 'input_acceptance.json')
    if inputs['status'] == 'STOP_INSUFFICIENT_FIXED_POINT_SUPPORT':
        write(ROOT / 'completion.json', dict(status=inputs['status'], support=inputs['support'], new_model_calls=0,
              baseline_unchanged=True, new_zip=0, production_allowed=False))
        return
    write(ROOT / 'source_input_lock.json', dict(protocol=ref(ROOT / 'protocol.json'),
          code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))}, input=ref(ROOT / 'input_acceptance.json'),
          wrapper=ref(WRAPPER), baseline=baseline_before))
    assert ref(WRAPPER)['sha256'] == protocol['wrapper_sha256']
    stage('infer', True)
    resource = read(RESOURCE / f'{JOB}.resource.json')
    ledger = [json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
    assert resource['status'] == 'completed' and resource['exit_code'] == 0
    assert [r for r in ledger if r.get('name') == JOB] == [resource]
    stage('review')
    stage('audit')
    result, inference = read(ROOT / 'review.json'), read(ROOT / 'inference_completion.json')
    assert ref(baseline) == baseline_before
    assert ref(checked(inputs['weight'])) == inputs['weight']
    lock = read(ROOT / 'source_input_lock.json')
    for code in lock['code'].values():
        checked(code)
    receipt = dict(status=result['status'], tests=result['tests'], macro_AP=result['macro_AP'],
          full_minus_center=result['full_minus_center'], improved_sources=result['improved_sources'], support=result['support'],
          sources=[dict(sid=s['sid'], AP=s['AP'], full_minus_center=s['full_minus_center']) for s in result['sources']],
          charged_seconds=resource['charged_seconds'], sampled_peak_mib=resource.get('sampled_peak_memory_mib'),
          torch_peak_allocated_bytes=inference['peak_allocated_bytes'], new_image_forward_batches=inference['image_forward_batches'],
          new_image_embeddings=112, reused_text_embeddings=26, new_text_calls=0, new_inverses=49, adopted_inverse7=7,
          combined_model_parameters=inference['combined_with_baseline'], new_decode=0, new_training=0,
          review=ref(ROOT / 'review.json'), audit=ref(ROOT / 'independent_cpu_audit.json'),
          input=ref(ROOT / 'input_acceptance.json'), lock=ref(ROOT / 'source_input_lock.json'),
          resource=ref(RESOURCE / f'{JOB}.resource.json'), baseline_unchanged=True, new_zip=0,
          production_allowed=False, completed_utc=datetime.now(timezone.utc).isoformat())
    write(ROOT / 'completion.json', receipt)
    write(ROOT / 'short_result.json', receipt)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'failure.json', dict(status='ACTUAL_FAILURE_PRESERVED', traceback=traceback.format_exc()))
        raise
