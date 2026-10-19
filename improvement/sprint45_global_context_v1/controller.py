"""Unique new-input QA -> shared GPU -> output QA -> two risk ZIPs."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    import hashlib
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(8 << 20), b''):
            h.update(part)
    return h.hexdigest()


def save(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main(root):
    p = read(root / 'protocol.json')
    require(p['schema'] == 'GLOBAL_LOCAL_BINARY_CONTEXT_EXPLORATION_V1' and
            os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'New protocol / physical parent GPU index')
    save(root / 'chain_started.json', dict(pid=os.getpid(),
         start_ticks=Path('/proc/self/stat').read_text().split()[21], argv=sys.argv, utc=utc()))

    def cpu(script, phase=None, extra=None):
        env = os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        cmd = [sys.executable, str(root / 'code' / script)]
        if phase is not None:
            cmd += ['--root', str(root), '--phase', phase]
        if extra:
            cmd += extra
        subprocess.run(cmd, env=env, check=True)

    cpu('prepare.py', 'prepare')
    cpu('prepare.py', 'input-qa')
    manifest = read(root / 'input_manifest.json')
    qa = read(root / 'input_qa.json')
    require(qa['status'] == 'PASS_ALL426_INDEPENDENT_GLOBAL_LOCAL_INPUT_QA' and
            qa['input_manifest_sha256'] == sha(root / 'input_manifest.json') and
            manifest['unique_inputs'] == qa['unique_inputs'], 'All real new inputs before GPU')
    name = 'sprint45_global_local_two_masks_20261016_v1'
    reg = dict(schema='GLOBAL_LOCAL_BINARY_CONTEXT_GENERATION_REGISTRATION_V1',
        protocol_sha256=sha(root / 'protocol.json'), input_manifest_sha256=sha(root / 'input_manifest.json'),
        input_qa_sha256=sha(root / 'input_qa.json'), unique_inputs=qa['unique_inputs'],
        cases=qa['cases'], sources=426, shared_gpu_job_name=name, budget_seconds=10800,
        stop_reserve_seconds=180)
    save(root / 'generation_registration.json', reg)
    save(root / 'generation_source_lock.json', dict(**reg,
         code={str(f): sha(f) for f in (root / 'code').glob('*.py')},
         new_image_processors=0, new_decoders=0, no_offline_effect_gate=True))
    run = Path(p['run_root'])
    command = [sys.executable, str(run / 'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', name, '--max-seconds', '10800', '--planned-output-bytes', str(256 << 20),
        '--capacity-reason', 'Existing frozen8B BASE; exact unique global/local16-image cases, short forced binary outputs; 256MiB new outputs, no full pixel cache or model checkpoint',
        '--queue-seconds', '7200', '--', sys.executable, str(root / 'code/infer.py'),
        '--root', str(root), '--phase', 'infer']
    save(root / 'GPU_launch.json', dict(name=name, command=command, utc=utc(),
         generation_source_lock_sha256=sha(root / 'generation_source_lock.json')))
    subprocess.run(command, check=True)
    resource = read(run / 'controller' / (name + '.resource.json'))
    rows = [json.loads(l) for l in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
    terminal = [r for r in rows if r.get('name') == name and r.get('status') in
                ('completed', 'failed', 'timeout', 'terminated')]
    require(resource.get('status') == 'completed' and resource.get('exit_code') == 0 and
            len(terminal) == 1 and terminal[0] == resource, 'Unique matching natural shared-GPU terminal')
    save(root / 'GPU_resource.json', resource)
    save(root / 'unique_resource_verified.json', dict(unique_terminal_count=1,
         resource_sha256=sha(root / 'GPU_resource.json'), name=name))
    cpu('infer.py', 'output-qa')
    mask = read(root / 'output_acceptance.json')
    require(mask['status'] == 'PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA' and
            len(mask['sources']) == 426, 'Complete actual token/native mask QA')
    out = root / 'packages_01'
    out.mkdir()
    package = dict(p['package_registration_template'], out_root=str(out), model_root=str(root))
    path = root / 'package_registration.json'
    save(path, package)
    cpu('package_global.py', extra=['--model-root', str(root), '--out-root', str(out),
                                  '--registration', str(path)])
    done = read(out / 'completion.json')
    save(root / 'chain_completion.json', dict(status='GLOBAL_LOCAL_TWO_RISK_DIRECTIONS_NATURAL_COMPLETE',
         utc=utc(), packages_completion_sha256=sha(out / 'completion.json'),
         actual_new_ZIPs=done['actual_new_ZIPs'], GPU_resource_sha256=sha(root / 'GPU_resource.json'),
         new_fivefold=False, new_proxy_effect_gate=False, online_effect='UNKNOWN', website_submitted=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    root = Path(parser.parse_args().root)
    try:
        main(root)
    except Exception as error:
        import traceback
        if not (root / 'chain_failure.json').exists():
            save(root / 'chain_failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                 utc=utc(), preserve_success=True, no_automatic_restart=True))
        raise
