"""One explicitly authorized new4 confirmation chain; no retries/resume."""
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import traceback
from urllib.parse import urlparse
import zipfile

HOME = Path('/home/inspur/aic_video_work')
MAIN = HOME/'midnight_five_verify40_46_20261015_v1'
ROOT = HOME/'midnight_pair_applicability_20261015_v1'
PY = HOME/'env/qwen3vl_isolated_20260910/bin/python'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
REF = ROOT/'reference'
CODE = ROOT/'code'
DEADLINE = '2026-10-15T16:00:00Z'
CONTROL07_SHA = 'b6426c9dc359e2ae6e6411ee8cca0976075627501043cbd7241e30a4eac75709'
CPU_ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
GPU_ENV = dict(CPU_ENV, CUDA_VISIBLE_DEVICES='0')


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha(path))


def checked(value):
    path = Path(value['path']).resolve()
    require(path.is_relative_to(HOME) and path.is_file() and sha(path) == value['sha256'], 'Frozen file changed: '+str(path))
    return path


def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def snapshot(state, name):
    observations = []
    for argv in (['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,args'],
        ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
        ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader,nounits']):
        value = subprocess.run(argv, capture_output=True, text=True)
        require(value.returncode == 0, 'Read-only resource observation failed')
        observations.append(dict(argv=argv, stdout=value.stdout, stderr=value.stderr))
    save(state/(name+'_resources.json'), dict(host=socket.gethostname(), utc=utc(), observations=observations,
        meminfo=Path('/proc/meminfo').read_text(), disk=dict(zip(('total', 'used', 'free'), shutil.disk_usage(ROOT))),
        no_external_process_stopped=True, no_fixed_utilization_threshold=True))


def child(state, name, argv, env=CPU_ENV, allowed=(0,)):
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(DEADLINE.replace('Z', '+00:00')), 'No new stage after frozen deadline')
    save(state/(name+'_launch.json'), dict(utc=utc(), argv=list(map(str, argv)), CUDA_VISIBLE_DEVICES=env.get('CUDA_VISIBLE_DEVICES')))
    with (state/(name+'.log')).open('x') as log:
        process = subprocess.Popen(list(map(str, argv)), env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        save(state/(name+'_process.json'), dict(pid=process.pid, start_ticks=Path('/proc/'+str(process.pid)+'/stat').read_text().split()[21],
            actual_cmdline=[value.decode() for value in Path('/proc/'+str(process.pid)+'/cmdline').read_bytes().split(b'\0') if value], argv=list(map(str, argv)), utc=utc()))
        returncode = process.wait()
    save(state/(name+'_terminal.json'), dict(utc=utc(), returncode=returncode))
    require(returncode in allowed, 'Actual new stage failed; do not repeat success: '+name)
    print(json.dumps(dict(stage=name, returncode=returncode, utc=utc())), flush=True)
    return returncode


def run_gpu(state, io, reg, stage):
    from fresh_registration import input_QA
    qa_path, qa = input_QA(ROOT, stage)
    cpu_path = ROOT/'cpu_acceptance_confirm.json' if stage == 'B0' else ROOT/'confirm/VERIFY/cpu_01/completion.json'
    cpu = read(cpu_path); budget = reg['gpu_budget'][stage]
    require(0 < qa['calls'] == len(cpu['entries']) <= budget['max_actual_calls'], 'Complete actual stage input/first-QA denominator within frozen budget required')
    lock_path = ROOT/('source_lock_confirm_'+stage+'.json')
    io.validate_lock(lock_path, set(io.code_files()) | {str(cpu_path), str(qa_path)})
    require(not (RUN/'controller'/(budget['gpu_job_name']+'.resource.json')).exists(), 'Unique new GPU job already has evidence; never repeat')
    gate = dict(status=io.ADMISSION_STATUS, group='confirm', stage=stage, expected_input_count=len(cpu['entries']),
        gpu_job_name=budget['gpu_job_name'], max_seconds=budget['max_seconds'], deadline=DEADLINE,
        cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=sha(cpu_path), source_lock_path=str(lock_path), source_lock_sha256=sha(lock_path),
        first_input_QA_sha256=sha(qa_path), fresh_registration_sha256=sha(ROOT/'positive_fresh_registration.json'),
        model_parameters=8782459120, optimizer_updates=0, source_scope='EXTERNAL_NONTEST_ONLY', reference_available_to_inference=False, production_admitted=False)
    gate_path = ROOT/('gpu_admission_confirm_'+stage+'.json'); save(gate_path, gate)
    snapshot(state, stage+'_before_GPU')
    script = CODE/('pilot_runtime.py' if stage == 'B0' else 'pilot_verify.py')
    child(state, stage+'_GPU', [PY, '-B', RUN/'resource_unlimited_v1_20261007/gpu_run.py', '--name', budget['gpu_job_name'],
        '--max-seconds', str(budget['max_seconds']), '--planned-output-bytes', str(32 << 20), '--capacity-reason',
        'New4 original baseline-only native64 first independent inputs accepted; unique bounded actual calls and output-only QA',
        '--queue-seconds', '60', '--', PY, '-B', script, 'infer', '--root', ROOT, '--group', 'confirm'], GPU_ENV)
    io.terminal(gate)
    child(state, stage+'_OUTPUT_QA', [PY, '-B', script, 'replay', '--root', ROOT, '--group', 'confirm'])


