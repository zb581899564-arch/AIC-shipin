"""One registered media batch followed by CPU preparation, without GPU admission."""
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
        raise ValueError('This batch chain is CPU-only and cannot launch a GPU job')
    reg_path = Path(registration_path)
    reg = read(reg_path)
    for relative, digest in reg['required_files'].items():
        check_file(BASE/relative, digest)
    chain = BASE/reg['chain_directory']
    chain.mkdir(exist_ok=False)
    save(chain/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=sha(reg_path)))
    try:
        log = (chain/'download.log').open('xb')
        subprocess.run([sys.executable, '-B', str(BASE/'code/download_media_batch_04.py'), str(reg_path)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
        log.close()
        complete_path = BASE/reg['output_directory']/'completion.json'
        cpu_reg = dict(status='REGISTERED_BATCH_NATIVE64_CPU_ONLY_NOT_ALL20_GPU_ADMISSION',
            utc=utc(), media_directory=reg['output_directory'], media_completion_sha256=sha(complete_path),
            output_directory=reg['cpu_directory'], required_files=reg['required_files'],
            source_registration_sha256=reg['source_registration_sha256'],
            fixed_native_frames=64, maximum_window_seconds=30, min_pixels=131072, max_pixels=131072,
            max_input_tokens=16384, model_params_b='8.78245912', new_model_calls=0,
            all20_real_input_gate_required_before_GPU=True)
        cpu_reg_path = chain/'cpu_registration.json'
        save(cpu_reg_path, cpu_reg)
        log = (chain/'cpu.log').open('xb')
        subprocess.run([sys.executable, '-B', str(BASE/'code/prepare_media_batch_04.py'), str(cpu_reg_path)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
        log.close()
        save(chain/'completion.json', dict(status='PASS_BATCH_MEDIA_AND_CPU_INPUTS_NOT_ALL20_OR_GPU_ADMISSION',
            utc=utc(), media_completion_sha256=sha(complete_path),
            cpu_completion_sha256=sha(BASE/reg['cpu_directory']/'completion.json'),
            new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False))
    except BaseException:
        save(chain/'failure.json', dict(status='FAILED_BATCH_CHAIN_PRESERVE_ALL_SUCCESSFUL_MEMBERS_CLOCKS_INPUTS',
             utc=utc(), traceback=traceback.format_exc(), new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registration')
    main(parser.parse_args().registration)
