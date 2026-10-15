"""Independent reserved-five CPU preparation; only children suppress CUDA."""
import json
import os
import socket
import shutil
import subprocess
import sys
import datetime
import traceback
from pathlib import Path
from new5_common import BASE, read, sha, save, check_download_admission

OUT=BASE/'cpu_chain_01'


def state(stage,**extra):
    pending=OUT/'state.json.pending'
    pending.write_text(json.dumps(dict(stage=stage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        new_model_calls=0,new_optimizer_updates=0,**extra),indent=2),encoding='utf-8')
    pending.replace(OUT/'state.json')


def run(stage,script,*args):
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONNOUSERSITE='1')
    argv=[sys.executable,'-B',str(BASE/'code'/script),*map(str,args)]
    with (OUT/(stage+'.log')).open('xb') as log:
        process=subprocess.Popen(argv,cwd=BASE/'code',env=env,stdout=log,stderr=subprocess.STDOUT)
        state(stage+'_RUNNING',child_pid=process.pid,argv=argv,actual_disk_free_bytes=shutil.disk_usage(BASE).free,
            actual_memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
        rc=process.wait()
    save(OUT/(stage+'.terminal.json'),dict(argv=argv,exit_code=rc))
    if rc:
        raise RuntimeError(stage+' actually failed; preserve all successful measurements and require explicit recovery')


def main():
    if socket.gethostname()!='inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') in (None,''):
        raise ValueError('Controller needs verified host/nonempty actual GPU index; CPU children alone suppress CUDA')
    check_download_admission(BASE/'new5_source_registration_01.json')
    registration=read(BASE/'new5_cpu_registration_02.json')
    for path,digest in registration['frozen_files'].items():
        if sha(path)!=digest:
            raise ValueError('Independent new5 CPU source/code changed: '+path)
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json',dict(pid=os.getpid(),script_sha256=sha(__file__),registration_sha256=sha(BASE/'new5_cpu_registration_02.json')))
    try:
        run('NATIVE_MAPPING','map_new5.py')
        mapped=read(BASE/'mapping_01/completion.json')
        raw_upper=0
        for item in mapped['rows']:
            bundle=read(item['bundle_path'])
            raw_upper+=len(bundle['windows'])*64*bundle['clock']['width']*bundle['clock']['height']*3
        free=shutil.disk_usage(BASE).free
        if raw_upper>=free:
            raise ValueError('Measured raw native64 RGB upper footprint exceeds current free storage')
        save(OUT/'measured_cache_capacity.json',dict(raw_upper_bound_bytes=raw_upper,current_free_bytes=free))
        run('NATIVE_RGB','rgb_new5.py',BASE/'new5_source_registration_01.json')
        run('CPU_PROCESSOR','processor_new5.py',BASE/'new5_source_registration_01.json',BASE/'EVALUATION_POLICY.md',BASE/'NATIVE_MAPPING_CONTRACT_V3.md')
        if read(BASE/'native_input_acceptance.json')['status']!='PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS':
            raise ValueError('Actual full reserved-five CPU input receipt missing')
        save(OUT/'completion.json',dict(status='CPU_INPUTS_COMPLETE_PENDING_NEW_GPU_SOURCE_LOCK_AND_WRAPPER',
            native_input_acceptance_sha256=sha(BASE/'native_input_acceptance.json'),new_model_calls=0,new_optimizer_updates=0,GPU_launch_admitted=False))
        state('CPU_INPUTS_COMPLETE_GPU_NOT_STARTED')
    except BaseException as error:
        save(OUT/'failure.json',dict(status='FAILED_NEW5_CPU_CHAIN_KEEP_ALL_SUCCESS',error=repr(error),traceback=traceback.format_exc(),new_model_calls=0))
        state('FAILED_KEEP_ALL_SUCCESS_AND_RAW')
        raise


if __name__=='__main__':
    main()
