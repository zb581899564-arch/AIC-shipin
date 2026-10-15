"""Main-controller admission and unique external20 VERIFY job, no fallback."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CAMPAIGN = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
CODE = CAMPAIGN/'candidate_verify_v2/code'
sys.path.insert(0, str(CODE))
import cv_io as io


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') not in ('', None) and io.ROLE == 'dev'
    state = io.BASE/'chain_01'; state.mkdir(exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), controller_sha256=io.sha(__file__), role=io.ROLE, utc=io.utc()))
    try:
        deadline = dt.datetime.fromisoformat(io.read(io.BASE/'protocol.json')['deadline'].replace('Z', '+00:00'))
        while not (io.BASE/'cpu_01/completion.json').exists():
            if (io.BASE/'cpu_01/failure.json').exists():
                raise ValueError('Actual new token preparation failed; preserve successful inputs')
            if dt.datetime.now(dt.timezone.utc) >= deadline:
                raise ValueError('No new job after Goal deadline')
            time.sleep(5)
        reg, reg_sha = io.registration()
        cpu = io.read(io.BASE/'cpu_01/completion.json')
        assert cpu['requests'] == 20 and cpu['status'] == 'PASS_ALL_EXTERNAL_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION'
        files = {}
        def add(path, expected=None):
            path = Path(path).resolve(); digest = io.sha(path)
            if expected is not None and expected != digest:
                raise ValueError('Actual frozen input changed: '+str(path))
            files[str(path)] = digest
        for path, digest in reg['required_files'].items():
            add(path, digest)
        for name in ['registration.json', 'cpu_01/completion.json', 'plan_01/completion.json', 'plan_01/requests.json']:
            add(io.BASE/name)
        identity = cpu['bindings']['original_b_processor_runtime']
        for name in ['runtime_files', 'processor_assets']:
            for path, digest in identity[name].items():
                add(path, digest)
        add(io.RUN/'b_score_aligned_package_v4/config.json', identity['original_config_sha256'])
        add(io.RUN/'temporal_sft8b_v1/sft_contract.py')
        for entry in cpu['proofs']:
            add(entry['proof_path'], entry['proof_sha256']); proof = io.read(entry['proof_path'])
            add(proof['input_path'], proof['input_sha256']); req = io.read(proof['input_path'])
            add(proof['token_cache_path'], proof['token_cache_sha256'])
            add(proof['original_vision_cache_path'], proof['original_vision_cache_sha256'])
            for ref in req['original_evidence'].values():
                add(ref['path'], ref['sha256'])
        io.save(io.BASE/'input_source_lock_01.json', dict(files=files, controller_sha256=io.sha(__file__), original_vision_processor_calls=0))
        job = 'aic20h_charades_dev20_original_b_verify_20261014_v1'
        io.save(io.BASE/'gpu_admission.json', dict(status='PASS_INDEPENDENT_VERIFY_GPU_ADMISSION',
            registration_sha256=reg_sha, cpu_completion_sha256=io.sha(io.BASE/'cpu_01/completion.json'),
            actual_model_call_budget=20, gpu_job_name=job, source_input_lock_files=files,
            current_rule_check_sha256=reg['official_rule_check_sha256'], actual_parameters=8782459120,
            optimizer_updates=0, controller_sha256=io.sha(__file__), independent_input_consumer_gate_before_wrapper=True))
        admitted = io.admitted()
        assert len(admitted[3]) == 20 and dt.datetime.now(dt.timezone.utc) < deadline
        io.save(io.BASE/'consumer_admission_01.json', dict(status='PASS_REAL20_TOKEN_INPUTS_AND_UNCHANGED_VISION_CONSUMER',
            actual_inputs=20, admission_sha256=io.sha(io.BASE/'gpu_admission.json'), new_model_calls=0, new_vision_processor_calls=0))
        env = dict(os.environ, AIC_VERIFY_ROLE='dev', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        cmd = [sys.executable, str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'), '--name', job,
            '--max-seconds', '900', '--planned-output-bytes', str(4 << 20), '--capacity-reason',
            '20 external candidate VERIFY calls. Reuses original Charades accepted exact vision caches; only prompt tokens new. Same B measured22GiB peak, serialized by shared lock, raw/tokens/proofs retained, no source decode or vision encode.',
            '--queue-seconds', '900', '--', sys.executable, '-u', str(CODE/'infer_verify.py')]
        io.save(io.BASE/'gpu_launch_01.json', dict(argv=cmd, job_name=job, actual_model_calls=20))
        subprocess.run(cmd, env=env, check=True)
        subprocess.run([sys.executable, '-u', str(CODE/'replay_verify.py')], env=dict(env, CUDA_VISIBLE_DEVICES=''), check=True)
        io.save(state/'completion.json', dict(status='COMPLETE_NEW_EXTERNAL20_VERIFY_AND_TOKEN_OUTPUT_REPLAYS_NOT_QUALITY',
            actual_model_calls=20, original_B0_calls_repeated=0, new_media_decodes=0, new_vision_processor_calls=0,
            gpu_completion_sha256=io.sha(io.BASE/'gpu_01/completion.json'), replay_completion_sha256=io.sha(io.BASE/'replay_01/completion.json'),
            verification_export_sha256=io.sha(io.BASE/'verification_export.json')))
    except BaseException as error:
        io.save(state/'failure.json', dict(error=repr(error), preserve_all_success=True, no_failure_to_UNKNOWN=True, do_not_repeat_calls=True))
        raise


if __name__ == '__main__':
    main()
