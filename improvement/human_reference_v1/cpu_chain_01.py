"""One CPU preparation chain; stops before any GPU/model invocation."""
import datetime
import json
import os
import shutil
import socket
import subprocess
import time
import traceback
from pathlib import Path

from map_sources_remote import BASE, save, sha

PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
OUT = BASE/'cpu_chain_01'


def state(stage, **extra):
    temp = OUT/'state.json.pending'
    temp.write_text(json.dumps(dict(stage=stage, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), new_model_calls=0, new_optimizer_updates=0, **extra), indent=2))
    temp.replace(OUT/'state.json')


def run_stage(name, script, *args):
    env = dict(os.environ)
    env['CUDA_VISIBLE_DEVICES'] = ''
    argv = [PYTHON, '-u', str(BASE/'code'/script), *map(str, args)]
    resource = dict(memory_available=[x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')], disk_free_bytes=shutil.disk_usage(BASE).free, load=os.getloadavg())
    with (OUT/(name+'.log')).open('xb') as log:
        p = subprocess.Popen(argv, cwd=str(BASE/'code'), env=env, stdout=log, stderr=subprocess.STDOUT)
        state(name+'_RUNNING', child_pid=p.pid, argv=argv, resources=resource)
        rc = p.wait()
    save(OUT/(name+'.terminal.json'), dict(exit_code=rc, argv=argv, utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    if rc:
        raise RuntimeError(name+' failed; retain raw/log and all successful outputs')


def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json', dict(pid=os.getpid(), argv=[PYTHON, '-u', str(Path(__file__))], script_sha256=sha(Path(__file__)), new_model_calls=0))
    try:
        state('WAITING_EXISTING_EXPLICIT_DOWNLOAD_RESUME')
        while not (BASE/'download_resume_terminal_01.json').exists():
            time.sleep(15)
        terminal = json.loads((BASE/'download_resume_terminal_01.json').read_text())
        assert terminal['exit_code'] == 0 and terminal['status'] == 'COMPLETED_RESUME'
        run_stage('SOURCE_ISOLATION', 'source_isolation_remote.py')
        run_stage('NATIVE_MAPPING', 'map_sources_remote.py', BASE/'human_source_registration_01.json', BASE/'NATIVE_MAPPING_CONTRACT_V2.md')
        # Estimate the maximum raw RGB cache footprint from actually measured geometry/windows.
        mapped = json.loads((BASE/'mapping_01/completion.json').read_text())
        raw_cache = 0
        for row in mapped['rows']:
            bundle = json.loads(Path(row['bundle_path']).read_text())
            raw_cache += len(bundle['windows'])*64*bundle['clock']['width']*bundle['clock']['height']*3
        assert raw_cache < shutil.disk_usage(BASE).free, 'Actual measured uncompressed caches exceed current storage capacity'
        run_stage('NATIVE_RGB', 'prepare_rgb_remote.py', BASE/'human_source_registration_01.json')
        run_stage('CPU_PROCESSOR', 'prepare_processor_remote.py', BASE/'human_source_registration_01.json', BASE/'EVALUATION_POLICY.md', BASE/'NATIVE_MAPPING_CONTRACT_V2.md')
        acceptance = BASE/'native_input_acceptance.json'
        assert acceptance.exists()
        save(OUT/'completion.json', dict(status='CPU_INPUTS_COMPLETE_PENDING_NEW_GPU_SOURCE_LOCK_AND_WRAPPER', native_input_acceptance_sha256=sha(acceptance), new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False))
        state('CPU_INPUTS_COMPLETE_GPU_NOT_STARTED')
    except BaseException as error:
        save(OUT/'failure.json', dict(status='CPU_CHAIN_FAILED_PRESERVE_SUCCESS_NO_AUTOMATIC_RETRY', error=repr(error), traceback=traceback.format_exc(), new_model_calls=0, new_optimizer_updates=0))
        state('FAILED_KEEP_ALL_SUCCESS_AND_RAW')
        raise


if __name__ == '__main__':
    main()
