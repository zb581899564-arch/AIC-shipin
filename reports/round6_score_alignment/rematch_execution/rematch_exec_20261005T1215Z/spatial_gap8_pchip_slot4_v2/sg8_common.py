"""Independent route I/O. Historical authorities are read-only, never relaunched."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUN = HERE.parent
OLD = RUN / 'b_score_aligned_package_v4'
V14 = RUN / 'teacher_student_autopilot_v14'
BASE = RUN / 'baseline_a_pts_v1'
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
P2J_SHA = 'db660d8afe562f56ade048fc3de57c83354308ce2ca7e12856010b6341d80e6c'
V14_LOCK_SHA = '5295e8bc0f2b6a651e73321a5798b259816ccbe9a0582753dc3c200b5ef080e0'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            value.update(block)
    return value.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value, fresh=True):
    path = Path(path)
    require(HERE == path.parent or HERE in path.parents, 'new route writes must stay in its own directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if fresh:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(path)


def state(stage, **fields):
    value = dict(utc=utc(), stage=stage, pid=os.getpid(), new_optimizer_updates=0,
                 new_32B_calls=0, new_time_calls=0, new_overview_calls=0, **fields)
    save(HERE / 'progress.json', value, fresh=False)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def old_helpers():
    """Use exact old implementations in a dedicated process; no old verify/run."""
    require(sha(BASE / 'vendor/p2j_core.py') == P2J_SHA, 'actual pinned linear implementation changed')
    common = load(OLD / 'common.py', 'sg8_original_b2_common')
    sys.modules['common'] = common
    common.bind_helpers()
    p2j = sys.modules['p2j_core']
    require(Path(p2j.__file__).resolve() == (BASE / 'vendor/p2j_core.py').resolve(), 'p2j module owner mismatch')
    production = load(OLD / 'production.py', 'sg8_original_production')
    return common, p2j, production


def inputs(scope):
    common, _, _ = old_helpers()
    config = read(OLD / 'config.json')
    spec = config['inputs'][scope]
    require(sha(spec['manifest']) == spec['manifest_sha256'], 'original manifest bytes changed')
    manifest = read(spec['manifest'])
    clocks = sys.modules['frame_contract'].load_clocks(manifest, spec['registry'], spec['registry_sha256'])
    return config, manifest, clocks


def verify(full=True):
    lock=read(HERE/'source_lock.json')
    require(lock['route']==HERE.name,'wrong route lock')
    for path,expected in (lock['files'] if full else lock['quick_files']).items():
        require(sha(path)==expected,'frozen dependency changed: '+path)
    return lock


def cached_output(entry):
    """Decode only the metadata-indexed target row; never collect other answers."""
    folder=Path(entry['chosen']['folder'])
    require(sha(folder/'anchor_requests.jsonl')==entry['chosen']['request_index_sha256'] and
        sha(folder/'anchor_output.jsonl')==entry['chosen']['output_sha256'],'exact cache bytes changed')
    requests=rows(folder/'anchor_requests.jsonl')
    positions=[i for i,r in enumerate(requests) if r['anchor_request_sha256']==entry['request_sha256']]
    require(len(positions)==1,'cache target is not unique')
    with (folder/'anchor_output.jsonl').open('rb') as stream:
        for index in range(positions[0]+1):
            raw_line=stream.readline()
    value=json.loads(raw_line)
    require(value['anchor_request_sha256']==entry['request_sha256'],'old request/output ordering differs; no search through answers')
    return value,hashlib.sha256(raw_line).hexdigest()
