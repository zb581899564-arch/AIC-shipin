"""BASE37 control scope, small-file receipts and current shared resources."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

HOME = Path('/home/inspur/aic_video_work')
CAMPAIGN = HOME/'twenty_hour_five_20261014_v1'
BASE = CAMPAIGN/'local_boundary_base_dev_v1'
TIME = CAMPAIGN/'local_boundary_v4/dev'
CONTROL = CAMPAIGN/'local_boundary_base_dev_control_v1'
CODE = CONTROL/'code'
DRIVER_CODE = BASE/'code'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = HOME/'env/qwen3vl_isolated_20260910/bin/python'
NAME = 'aic20h_charades_dev37_base_boundary_20261014_v1'
COUNTS = dict(nominal_endpoints=40, actionable_requests=37, structural_skips=3)
SCOPE_SCHEMA = 'BASE37_TIME_THEN_BASE_UNIQUE_CONTROLLER_V1'
SCOPE_STATUS = 'FROZEN_BASE37_CONTROLLER_WAIT_TIME_NATURAL_AND_FIRST_REPLAY_V1'
MAX_GPU_SECONDS = 1500
PLANNED_OUTPUT_BYTES = 8 << 20


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def host(cpu=False):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux', 'Verified Linux host required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ('' if cpu else '0'), 'Parent GPU0/CPU-child-only empty CUDA required')


def own_code_files():
    return {str(path.resolve()): sha(path) for path in sorted(Path(__file__).resolve().parent.glob('*.py'))}


def ref(value, roots):
    path = Path(value['path']).resolve()
    require(any(path.is_relative_to(Path(root).resolve()) for root in roots), 'Control reference escaped explicit roots')
    require(sha(path) == value['sha256'], 'Frozen controller/reference changed: '+str(path))
    return path


def validate_scope(value, deadline_value, own_files, driver_files):
    require(value['schema'] == SCOPE_SCHEMA and value['status'] == SCOPE_STATUS and value['role'] == 'dev' and
            value['base_root'] == str(BASE) and value['source_root'] == str(TIME) and
            value['actual_model_call_budget'] == 37 and value['events'] == 20 and
            all(value[k] == v for k, v in COUNTS.items()) and value['gpu_job_name'] == NAME and
            value['max_gpu_seconds'] == MAX_GPU_SECONDS and value['planned_output_bytes'] == PLANNED_OUTPUT_BYTES and
            value['new_input_processor_encodes'] == value['new_media_decodes'] == value['optimizer_updates'] == 0 and
            value['deadline'] == deadline_value and value['controller_code_files'] == own_files and
            value['driver_code_files'] == driver_files and value['no_successful_TIME_or_input_stage_repeat'] is True and
            value['quality_selection_or_production_by_controller'] is False,
            'Root frozen exact20/40/37/3 single-job control scope required')


def scope(path):
    path = Path(path).resolve()
    require(path == CONTROL/'control_scope_01.json', 'One explicit root-frozen controller scope path required')
    value = read(path)
    deadline_path = ref(value['deadline_ref'], roots=(TIME,))
    require(deadline_path == TIME/'protocol.json', 'Read the real frozen TIME campaign deadline')
    deadline_value = read(deadline_path)['deadline']
    driver_files = {str(p.resolve()): sha(p) for p in sorted(DRIVER_CODE.glob('*.py'))}
    require(len(driver_files) == 4, 'Frozen BASE driver must have exact4py')
    validate_scope(value, deadline_value, own_code_files(), driver_files)
    official = ref(value['official_rule_check_ref'], roots=(TIME,))
    require(official == TIME/'official_rule_check.json', 'Current campaign rule copy must bind the accepted TIME rule receipt')
    controller_launch = ref(value['TIME_controller_launch_ref'], roots=(TIME,))
    require(controller_launch == TIME/'controller_launch_01.json', 'The already started unique TIME controller must be bound')
    for path_text, digest in value['controller_code_files'].items():
        ref(dict(path=path_text, sha256=digest), roots=(CODE,))
    for path_text, digest in value['driver_code_files'].items():
        ref(dict(path=path_text, sha256=digest), roots=(DRIVER_CODE,))
    return path, value


def check_deadline(value):
    deadline = dt.datetime.fromisoformat(value['deadline'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'Campaign deadline reached; do not launch new BASE work')
    return deadline


def unique_job_absent():
    require(not (RUN/'controller'/(NAME+'.resource.json')).exists(), 'BASE job already has a terminal; never repeat it')
    ledger = HOME/'improvement_round1/gpu_ledger.jsonl'
    if ledger.exists():
        require(not any(json.loads(s)['name'] == NAME for s in ledger.read_text().splitlines() if s.strip()),
                'BASE job already exists in the shared ledger; never repeat it')
    active = HOME/'improvement_round1/active_gpu_job.json'
    if active.exists():
        require(read(active).get('name') != NAME, 'This BASE job is already active; never submit it twice')


def time_failure_paths():
    return [TIME/'controller_failure_01.json', TIME/'chain_01/failure.json', TIME/'gpu_01/failure.json', TIME/'replay_01/failure.json']


def time_terminal(tolerate_incomplete=False):
    """No PID guess or incomplete count can stand for the natural TIME end."""
    for path in time_failure_paths():
        if path.exists():
            raise RuntimeError('TIME failed; preserve evidence and do not run BASE: '+str(path))
    complete_path = TIME/'chain_01/completion.json'
    if not complete_path.exists():
        return None
    try:
        value = read(complete_path)
    except json.JSONDecodeError:
        if tolerate_incomplete:
            return None  # create-x writer has not closed its JSON yet.
        raise
    require(value['status'] == 'COMPLETE_REAL_DEV37_TIME_AND_FIRST_INDEPENDENT_CPU_REPLAY_NOT_QUALITY' and
            value['actual_model_calls'] == 37 and value['nominal_endpoints'] == 40 and value['structural_skips'] == 3 and
            value['gpu_completion_sha256'] == sha(TIME/'gpu_01/completion.json') and
            value['independent_replay_completion_sha256'] == sha(TIME/'replay_01/completion.json') and
            value['export_sha256'] == sha(TIME/'boundary_prediction_export.json'),
            'Natural TIME37 chain closure or first input/output replay binding differs')
    return dict(path=str(complete_path), sha256=sha(complete_path))


def resource_snapshot():
    """Read actual CPU/GPU/argv/memory/disk; no machine changes or fixed GB gate."""
    result = dict(host=socket.gethostname(), utc=utc(), pid=os.getpid(), parent_pid=os.getppid(),
                  CPU_count=os.cpu_count(), CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'))
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, _, rest = line.partition(':')
        if key in ('MemTotal', 'MemAvailable', 'SwapFree'):
            memory[key+'_bytes'] = int(rest.strip().split()[0])*1024
    result['memory'] = memory
    usage = shutil.disk_usage(BASE)
    result['disk'] = dict(total_bytes=usage.total, used_bytes=usage.used, free_bytes=usage.free)
    commands = dict(processes=['ps', '-eo', 'pid,ppid,pcpu,pmem,args'],
        GPU=['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader'],
        GPU_processes=['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'])
    for name, argv in commands.items():
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=20)
        require(proc.returncode == 0, 'Current resource query failed: '+name)
        output = proc.stdout
        if name == 'processes':
            output = '\n'.join(line for line in output.splitlines() if any(word in line for word in
                ('java', 'gpu_run.py', 'local_boundary', 'candidate_verify', 'training', 'Charades')))
        result[name] = output
    active = HOME/'improvement_round1/active_gpu_job.json'
    result['shared_active_job'] = read(active) if active.exists() else None
    require(result['disk']['free_bytes'] >= PLANNED_OUTPUT_BYTES,
            'Actual free disk cannot fit this registered8MiB output; wait or explicit recovery, no cleanup')
    return result


def driver_modules():
    sys.path.insert(0, str(DRIVER_CODE))
    import bd_contract
    import bd_io
    require(Path(bd_contract.__file__).resolve() == DRIVER_CODE/'bd_contract.py' and
            Path(bd_io.__file__).resolve() == DRIVER_CODE/'bd_io.py', 'BASE driver module name shadowed')
    return bd_contract, bd_io


def child_env(cpu=False):
    env = os.environ.copy()
    if cpu:
        env['CUDA_VISIBLE_DEVICES'] = ''
    env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env
