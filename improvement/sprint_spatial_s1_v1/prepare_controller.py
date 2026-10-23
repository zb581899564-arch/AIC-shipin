"""Only the registered first S1 preparation and frozen center generation."""
import json
import os
import subprocess
import traceback
from common import ROOT, WORK, PY, append, baseline_identity, checked, read, ref, run_stage, write


def main():
    write(ROOT / 'prepare_claim.json', dict(pid=os.getpid(), user_scope='S1 same-budget three arms, protected40.47'))
    baseline_identity()
    upstream = ROOT / 'upstream/improvement/i3d_umt_v1'
    prior = WORK / 'i3d_umt_cross_domain_20261021_v1/provenance.py'
    with (upstream / 'provenance.py').open('xb') as stream:
        stream.write(prior.read_bytes())
    results = []
    for flags in [[], ['-O']]:
        command = [str(PY), '-B', *flags, str(upstream / 'crossdata12/test_native_metrics.py')]
        done = subprocess.run(command, capture_output=True, text=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        result = dict(argv=command, exit_code=done.returncode, stdout=done.stdout, stderr=done.stderr)
        results.append(result)
        if done.returncode:
            write(ROOT / 'upstream_test_failure.json', result)
            raise ValueError('PR5 exact regressions fail in execution environment')
    write(ROOT / 'upstream_cpu_acceptance.json', dict(status='PASS_FIXED_PR5_NORMAL_AND_OPTIMIZED', results=results,
        provenance_adopted_from=ref(prior), historical_results_recomputed=False))
    run_stage('geometry_contracts', 'test_geometry.py')
    run_stage('cohort', 'cohort.py')
    rows = read(ROOT / 'cohort.json')['rows']
    write(ROOT / 'center_dimensions.json', [dict(item_id=r['item_id'], width=r['width'], height=r['height']) for r in rows])
    run_stage('pixels', 'prepare_pixels.py')
    write(ROOT / 'center_source_lock.json', dict(protocol=ref(ROOT / 'protocol.json'), inputs=ref(ROOT / 'pixel_acceptance.json'),
        dimensions=ref(ROOT / 'center_dimensions.json'), code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))},
        upstream=ref(ROOT / 'upstream_acceptance.json'), baseline=baseline_identity()))
    record = run_stage('centers', 'centers.py', gpu_seconds=2400)
    write(ROOT / 'preparation_completion.json', dict(status='S1_CPU_AND762_FROZEN_CENTERS_READY_FOR_CONDITIONED_TRAINING_INPUTS',
        centers=ref(ROOT / 'center_completion.json'), charged_seconds=record['charged_seconds'],
        training_updates=0, baseline_unchanged=True, auto_training=False, new_ZIP=0))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'prepare_failure.json', dict(status='ACTUAL_FAILURE_KEEP_SUCCESS', traceback=traceback.format_exc()))
        raise
