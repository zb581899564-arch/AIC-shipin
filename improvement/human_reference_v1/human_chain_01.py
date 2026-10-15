"""Wait for the existing CPU chain; one new wrapper and independent replay.

This controller never repeats preparation, trains, scores human labels, or
packages test outputs. Later local comparison remains a separate quality gate.
"""
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
import human_run_common as r

OUT = r.BASE/'human_chain_01'


def state(stage, **extra):
    value = dict(stage=stage, utc=r.utc(), **extra)
    path = OUT/'state.json.pending'
    path.write_text(__import__('json').dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    path.replace(OUT/'state.json')
    print(__import__('json').dumps(value), flush=True)


def run(name, argv, gpu=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONNOUSERSITE='1',
        HF_HOME=str(r.RUN/'cache/hf'), XDG_CACHE_HOME=str(r.RUN/'cache'),
        TMPDIR=str(r.RUN/'tmp'), TORCH_HOME=str(r.RUN/'cache/torch'))
    if not gpu:
        env['CUDA_VISIBLE_DEVICES'] = ''
    with (OUT/(name+'.log')).open('xb') as log:
        child = subprocess.Popen(argv, cwd=r.BASE/'code', env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT)
        state(name+'_RUNNING', argv=argv, child_pid=child.pid,
            actual_disk_free_bytes=shutil.disk_usage(r.BASE).free,
            memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
        rc = child.wait()
    r.save(OUT/(name+'.terminal.json'), dict(argv=argv, exit_code=rc, utc=r.utc()))
    if rc:
        raise RuntimeError(name+' failed; retain all raw/success and do not retry this attempt')


def freeze_source_lock(registration):
    acceptance, complete, inputs = r.inputs()
    files = dict(registration['implementation_files'])
    required = [r.BASE/'native_input_acceptance.json', r.BASE/'processor_02/completion.json',
        r.BASE/'rgb_02/inputs.json', r.BASE/'rgb_02/completion.json', r.BASE/'mapping_02/completion.json',
        r.BASE/'source_isolation_acceptance.json', r.BASE/'media_01/completion.json',
        r.BASE/'human_source_registration_01.json', r.BASE/'native_mapping_recovery_02.json',
        r.BASE/'NATIVE_MAPPING_CONTRACT_V3.md', r.BASE/'EVALUATION_POLICY.md',
        r.BASE/'annotation_ordinal_clock_audit_01.json', r.BASE/'human_inference_registration_01.json',
        r.RUN/'b_score_aligned_package_v4/config.json']
    for path, expected in complete['bindings']['original_b_processor_runtime']['runtime_files'].items():
        if r.sha(path) != expected:
            raise ValueError('Original accepted runtime changed')
        files[path] = expected
    for path, expected in complete['bindings']['original_b_processor_runtime']['processor_assets'].items():
        if r.sha(path) != expected:
            raise ValueError('Original accepted processor asset changed')
        files[path] = expected
    recovery = r.read(r.BASE/'native_mapping_recovery_02.json')
    for path, expected in recovery['frozen_files'].items():
        if r.sha(path) != expected:
            raise ValueError('Inherited frozen engineering evidence changed')
        files[path] = expected
    for item in recovery['inherited_clocks']:
        required.append(Path(item['path']))
    mapped = r.read(r.BASE/'mapping_02/completion.json')
    for item in mapped['rows']:
        path = Path(item['bundle_path'])
        if r.sha(path) != item['bundle_sha256']:
            raise ValueError('Original native mapping bundle changed')
        required.append(path)
        bundle = r.read(path)
        required += [Path(bundle['clock']['source_path']), Path(bundle['decode_provenance']['path'])]
    for entry, proof, meta in inputs:
        required += [Path(entry['proof_path']), Path(proof['input_path']), Path(meta['frame_array_path'])]
    # Static code and existing model files, never test labels or a new model download.
    for folder in [r.RUN/'b_score_aligned_package_v4', r.RUN/'baseline_a_pts_v1',
            r.RUN/'baseline_a_pts_v1/vendor', r.RUN/'balanced_two_window_risk_v3',
            r.RUN/'temporal_sft8b_v1']:
        required += list(folder.glob('*.py'))
    config = r.read(r.RUN/'b_score_aligned_package_v4/config.json')
    for folder in [Path(config['model_dir']), Path(config['b_adapter'])]:
        required += [p for p in folder.iterdir() if p.is_file() and
            p.suffix in ('.safetensors', '.json', '.txt', '.jinja')]
    required += list((r.RUN/'resource_unlimited_v1_20261007').glob('*.py'))
    for path in set(required):
        digest = r.sha(path)
        if str(path) in files and files[str(path)] != digest:
            raise ValueError('Source-lock identity conflict: '+str(path))
        files[str(path)] = digest
    r.save(r.BASE/'human_source_lock_01.json', dict(status='FROZEN_ALL_ACTUAL_HUMAN_NATIVE_INPUTS_AND_ORIGINAL_B',
        files=files, registered_sources=20, windows=len(inputs), model_parameters=8782459120,
        optimizer_updates=0, unique_gpu_name=r.NAME, utc=r.utc(), human_reference_labels_not_in_inference=True))
    return len(inputs), len(files)


def main():
    if socket.gethostname() != 'inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') in (None, ''):
        raise ValueError('Chain requires the verified host and a nonempty actual GPU index')
    registration = r.read(r.BASE/'human_inference_registration_01.json')
    if (registration['unique_gpu_name'] != r.NAME or registration['new_optimizer_updates'] != 0 or
            registration['sources'] != 20 or registration['original_B_native64_once'] is not True):
        raise ValueError('New external inference registration differs')
    for path, expected in registration['implementation_files'].items():
        if r.sha(path) != expected:
            raise ValueError('Registered implementation changed before chain launch')
    OUT.mkdir(exist_ok=False)
    r.save(OUT/'launch_claim.json', dict(pid=os.getpid(), script_sha256=r.sha(__file__),
        registration_sha256=r.sha(r.BASE/'human_inference_registration_01.json'), utc=r.utc()))
    try:
        state('WAIT_EXISTING_CPU_CHAIN_02_NO_PREPARE_RESTART')
        while not (r.BASE/'cpu_chain_02/completion.json').exists():
            if (r.BASE/'cpu_chain_02/failure.json').exists():
                raise ValueError('Existing CPU preparation actually failed; GPU must not start')
            time.sleep(15)
        state('FREEZE_ACTUAL_INPUTS_AND_CODE')
        windows, count = freeze_source_lock(registration)
        state('ACTUAL_INPUTS_FROZEN', windows=windows, files=count,
            source_lock_sha256=r.sha(r.BASE/'human_source_lock_01.json'))
        command = [sys.executable, '-B', str(r.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name', r.NAME, '--max-seconds', str(registration['max_gpu_seconds']),
            '--queue-seconds', str(registration['queue_seconds']),
            '--planned-output-bytes', '536870912', '--capacity-reason',
            'All twenty original sources and actual native64 CPU inputs accepted; unchanged B8B with prior measured capacity; dynamic shared no-external-compute lock and actual remaining outputs, no fixed utilization or free-VRAM gate',
            '--', sys.executable, '-B', str(r.BASE/'code/infer_human_01.py')]
        run('EXTERNAL_B_GPU_WRAPPER', command, gpu=True)
        resource, resource_sha = r.resource_terminal()
        state('ALL_EXTERNAL_B_MODEL_CALLS_COMPLETE', resource_terminal_sha256=resource_sha,
            charged_seconds=resource['charged_seconds'])
        run('INDEPENDENT_CPU_REPLAY_EXPORT', [sys.executable, '-B', str(r.BASE/'code/replay_human_01.py')])
        r.save(OUT/'completion.json', dict(status='PASS_EXTERNAL_B_EXPORT_PENDING_LOCAL_HUMAN_QUALITY_COMPARISON',
            registered_sources=20, windows=windows, developer_export_acceptance_sha256=r.sha(r.BASE/'developer_export_acceptance.json'),
            prediction_export_sha256=r.sha(r.BASE/'developer_prediction_export.json'),
            resource_terminal_sha256=resource_sha, charged_seconds=resource['charged_seconds'],
            new_optimizer_updates=0, candidate_package_admitted=False, utc=r.utc()))
        state('EXTERNAL_EXPORT_COMPLETE_PENDING_HUMAN_AND_PARTIAL_FACT_GATES')
    except BaseException as error:
        r.save(OUT/'failure.json', dict(status='FAILED_HUMAN_CHAIN_KEEP_ALL_RAW_SUCCESS_AND_COST',
            error=repr(error), traceback=traceback.format_exc(), utc=r.utc()))
        state('FAILED_PRESERVE_NO_SAME_CHAIN_RESTART', error=repr(error))
        raise


if __name__ == '__main__':
    main()
