"""Independent recovery chain after the actual v2 metadata-clock failure."""
import datetime
import json
import os
import shutil
import socket
import subprocess
import traceback
from pathlib import Path

from map_sources_remote import BASE, read, save, sha

PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
OUT = BASE/'cpu_chain_02'


def state(stage, **extra):
    path = OUT/'state.json.pending'
    path.write_text(json.dumps(dict(stage=stage, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        new_model_calls=0, new_optimizer_updates=0, **extra)), encoding='utf-8')
    path.replace(OUT/'state.json')


def run(name, script, *args):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    argv = [PYTHON, '-u', str(BASE/'code'/script), *map(str, args)]
    resources = dict(disk_free_bytes=shutil.disk_usage(BASE).free, load=os.getloadavg(),
        memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
    with (OUT/(name+'.log')).open('xb') as log:
        child = subprocess.Popen(argv, cwd=BASE/'code', env=env, stdout=log, stderr=subprocess.STDOUT)
        state(name+'_RUNNING', child_pid=child.pid, argv=argv, resources=resources)
        rc = child.wait()
    save(OUT/(name+'.terminal.json'), dict(exit_code=rc, argv=argv,
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    if rc:
        raise RuntimeError(name+' failed; preserve all measurements/success and require independent recovery')


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Unexpected host')
    registration = read(BASE/'native_mapping_recovery_02.json')
    for path, digest in registration['frozen_files'].items():
        if sha(path) != digest:
            raise ValueError('Recovery frozen input/code changed: '+path)
    if (read(BASE/'cpu_chain_01/state.json')['stage'] != 'FAILED_KEEP_ALL_SUCCESS_AND_RAW' or
            read(BASE/'source_isolation_acceptance.json')['status'] != 'PASS_KNOWN_SOURCE_IDENTITY_AND_BYTE_SEPARATION'):
        raise ValueError('Actual failed chain and original successful isolation receipt required')
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json', dict(pid=os.getpid(), argv=[PYTHON, '-u', str(Path(__file__))],
        recovery_registration_sha256=sha(BASE/'native_mapping_recovery_02.json'),
        script_sha256=sha(__file__), new_model_calls=0))
    try:
        state('ORIGINAL_SOURCE_ISOLATION_REUSED_NO_NEW_AUDIT')
        run('NATIVE_MAPPING_V3', 'map_sources_v3.py')
        mapped = read(BASE/'mapping_02/completion.json')
        raw_bytes = 0
        for item in mapped['rows']:
            bundle = read(item['bundle_path'])
            raw_bytes += len(bundle['windows'])*64*bundle['clock']['width']*bundle['clock']['height']*3
        # Dynamic capacity against measured inputs, without arbitrary utilization/free-GiB thresholds.
        if raw_bytes >= shutil.disk_usage(BASE).free:
            raise ValueError('Measured uncompressed RGB footprint exceeds current free storage')
        save(OUT/'actual_cache_capacity.json', dict(raw_upper_bound_bytes=raw_bytes,
            actual_free_bytes=shutil.disk_usage(BASE).free))
        run('NATIVE_RGB', 'prepare_rgb_v3.py', BASE/'human_source_registration_01.json')
        run('CPU_PROCESSOR', 'prepare_processor_v3.py', BASE/'human_source_registration_01.json',
            BASE/'EVALUATION_POLICY.md', BASE/'NATIVE_MAPPING_CONTRACT_V3.md')
        acceptance = BASE/'native_input_acceptance.json'
        if read(acceptance)['status'] != 'PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS':
            raise ValueError('Actual complete input admission missing')
        save(OUT/'completion.json', dict(status='CPU_INPUTS_COMPLETE_PENDING_NEW_GPU_SOURCE_LOCK_AND_WRAPPER',
            native_input_acceptance_sha256=sha(acceptance), new_model_calls=0,
            new_optimizer_updates=0, GPU_launch_admitted=False))
        state('CPU_INPUTS_COMPLETE_GPU_NOT_STARTED')
    except BaseException as error:
        save(OUT/'failure.json', dict(status='CPU_RECOVERY_CHAIN_FAILED_KEEP_ALL_SUCCESS', error=repr(error),
            traceback=traceback.format_exc(), new_model_calls=0, new_optimizer_updates=0))
        state('FAILED_KEEP_ALL_SUCCESS_AND_RAW')
        raise


if __name__ == '__main__':
    main()
