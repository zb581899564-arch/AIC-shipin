"""One first S0 engineering/profile and fixed external development comparison."""
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import traceback
from control import ROOT, WORK, PY, RUN, WRAPPER, RESOURCE, LEDGER, read, write, reference, checked


def run_cpu(name, script):
    command = [str(PY), '-u', '-B', str(ROOT / 'code_run' / script)]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(ROOT / 'code_v2') + ':' + str(ROOT / 'code'),
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    with (ROOT / (name + '.log')).open('x') as log:
        done = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    write(ROOT / (name + '_terminal.json'), dict(exit_code=done.returncode, argv=command))
    if done.returncode:
        raise RuntimeError(name + ' actually failed; successful assets are preserved')


def baseline():
    asset = reference(WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    if asset['bytes'] != 384630 or asset['sha256'] != 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3':
        raise ValueError('Protected40.47 baseline changed')
    return asset


def run_gpu():
    import torch
    inputs = read(ROOT / 'inputs.json')
    sizes = [torch.load(checked(r['input']), map_location='cpu', weights_only=True)['image'].numel() * 4 for r in inputs]
    estimate = read(ROOT / 'learned_weight_acceptance.json')['actual_parameters'] * 4 + max(sizes) * 64
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    processes = []
    for row in apps.splitlines():
        process = Path('/proc') / row.split(',')[0].strip()
        if process.exists():
            processes.append(dict(pid=process.name, argv=(process / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace'), stat=(process / 'stat').read_text()))
    resource = dict(host=socket.gethostname(), GPU=gpu, outside_tasks=processes, disk_free=shutil.disk_usage(ROOT).free,
        model_and_registered_activation_estimate_bytes=estimate, output_budget_bytes=134217728,
        available_memory=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
    write(ROOT / 'resource_admission.json', resource)
    if resource['host'] != 'inspur-NP5570M5' or int(gpu.split(',')[0]) * 1024**2 < estimate or resource['disk_free'] < resource['output_budget_bytes']:
        raise ValueError('Current shared resources cannot hold this particular small job')
    name = 's0_author_gaic80_dev_20261021_v1'
    if (RESOURCE / (name + '.resource.json')).exists():
        raise FileExistsError('Unique S0 scorer job already exists')
    import json
    command = [str(PY), '-B', str(WRAPPER), '--name', name, '--max-seconds', '600', '--planned-output-bytes', str(resource['output_budget_bytes']),
        '--capacity-reason', json.dumps(resource, separators=(',', ':')), '--queue-seconds', '0', '--',
        str(PY), '-u', '-B', str(ROOT / 'code_run/score80.py')]
    with (ROOT / 'GPU.log').open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='0'),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        write(ROOT / 'GPU_launch.json', dict(pid=process.pid, argv=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        code = process.wait()
    write(ROOT / 'GPU_terminal.json', dict(exit_code=code))
    record = read(RESOURCE / (name + '.resource.json'))
    matches = [r for r in map(json.loads, LEDGER.read_text().splitlines()) if r.get('name') == name]
    if code or record['status'] != 'completed' or record['exit_code'] != 0 or matches != [record]:
        raise ValueError('Actual S0 GPU failure or unique terminal/ledger mismatch')
    return record


def main():
    write(ROOT / 'controller_claim.json', dict(pid=os.getpid(), UTC=datetime.now(timezone.utc).isoformat()))
    before = baseline()
    deadline = datetime.fromisoformat(read(ROOT / 'registration.json')['compatibility_deadline_UTC'])
    if datetime.now(timezone.utc).timestamp() + 600 > deadline.timestamp():
        raise ValueError('Remaining compatibility window cannot fit the bounded first profile')
    run_cpu('strict_weight', 'load_weight.py')
    run_cpu('first_inputs', 'make_inputs.py')
    write(ROOT / 'source_lock.json', dict(protocol=reference(ROOT / 'protocol.json'),
        weight=reference(ROOT / 'learned_weight_acceptance.json'), inputs=reference(ROOT / 'input_acceptance.json'),
        code={str(p.relative_to(ROOT)): reference(p) for folder in ['code_run', 'code_v2', 'code'] for p in sorted((ROOT / folder).glob('*.py'))},
        baseline=before, upstream_manifest=reference(ROOT / 'source_files.jsonl'), compatibility=reference(ROOT / 'compat_cpu_acceptance_v2.json')))
    record = run_gpu()
    run_cpu('independent_review', 'review.py')
    if baseline() != before:
        raise ValueError('Protected baseline changed during S0')
    for entry in read(ROOT / 'source_lock.json')['code'].values():
        checked(entry)
    result = dict(status=read(ROOT / 'review.json')['status'], summary=read(ROOT / 'review.json')['summary'],
        GPU_charged_seconds=record['charged_seconds'], wrapper_peak_MiB=record['sampled_peak_memory_mib'],
        model=read(ROOT / 'model_completion.json'), original_baseline_unchanged=True, new_ZIP=0,
        automatic_production=False, original_source_independence='UNKNOWN', completed_UTC=datetime.now(timezone.utc).isoformat())
    write(ROOT / 'completion.json', result)
    write(ROOT / 'short_result.json', result)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'controller_failure.json', dict(status='ACTUAL_FAILURE_SUCCESS_AND_RAW_PRESERVED', traceback=traceback.format_exc()))
        raise
