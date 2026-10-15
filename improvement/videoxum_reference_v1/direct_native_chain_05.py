"""Direct public-media batch and native CPU profile; never starts a model."""
import argparse
import os
import socket
import subprocess
import sys
import traceback
from pathlib import Path

from stage_common_04 import BASE, check_file, read, save, sha, utc


def main(registration_path):
    if socket.gethostname() != 'inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU-only Linux direct-media chain required')
    reg_path = Path(registration_path)
    reg = read(reg_path)
    for name,digest in reg['required_files'].items():
        check_file(BASE/name, digest)
    out = BASE/reg['chain_directory']
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=sha(reg_path)))
    try:
        with (out/'download.log').open('xb') as log:
            subprocess.run([sys.executable,'-B',str(BASE/'code/download_direct_media_05.py'),str(reg_path)],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        media_completion = BASE/reg['output_directory']/'completion.json'
        cpu_registration = dict(status='REGISTERED_DIRECT_NATIVE64_CPU_ONLY_BEFORE_REAL_DECODE', utc=utc(),
            media_directory=reg['output_directory'], media_completion_sha256=sha(media_completion),
            output_directory=reg['cpu_directory'], required_files=reg['required_files'],
            selection_path=reg['selection_path'], reference_path=reg['reference_path'],
            fixed_native_frames=64, maximum_window_seconds=30, min_pixels=131072, max_pixels=131072,
            max_input_tokens=16384, model_params_b='8.78245912', GPU_launch_admitted=False)
        path=out/'cpu_registration.json'
        save(path,cpu_registration)
        with (out/'cpu.log').open('xb') as log:
            subprocess.run([sys.executable,'-B',str(BASE/'code/prepare_media_batch_05.py'),str(path)],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        save(out/'completion.json',dict(status='PASS_DIRECT_BATCH_AND_NATIVE64_CPU_INPUTS_NOT_ALL20_OR_GPU_ADMISSION',
            utc=utc(),media_completion_sha256=sha(media_completion),
            cpu_completion_sha256=sha(BASE/reg['cpu_directory']/'completion.json'),
            new_model_calls=0,new_optimizer_updates=0))
    except BaseException:
        save(out/'failure.json',dict(status='FAILED_DIRECT_CHAIN_KEEP_MEDIA_AND_SUCCESSFUL_NATIVE_EVIDENCE',
            utc=utc(),traceback=traceback.format_exc(),new_model_calls=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('registration')
    main(parser.parse_args().registration)
