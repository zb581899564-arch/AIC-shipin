"""B2 owns all helper identities and receipts; existing experiments stay frozen."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = Path(os.environ.get('AIC_WORK_ROOT', '/home/inspur/aic_video_work'))
BASELINE = RUN / 'baseline_a_pts_v1'
sys.path[:0] = [str(HERE), str(BASELINE), str(BASELINE / 'vendor'), str(RUN / 'temporal_sft8b_v1')]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_rows(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        for row in values:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def progress(out, value):
    path = Path(out) / 'progress.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(dict(utc=utc(), **value), ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(path)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def load(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def bind_helpers():
    names = ('contracts', 'constrained_json', 'package_contract', 'frame_contract', 'field_contract',
             'video_contract', 'native_segment_contract', 'native_input')
    for name in names:
        expected = HERE / (name + '.py')
        module = sys.modules.get(name)
        if module is None or Path(module.__file__).resolve() != expected:
            load(expected, name)
        require(Path(sys.modules[name].__file__).resolve() == expected, 'B2 helper owner mismatch: ' + name)
    return {name: str(Path(sys.modules[name].__file__).resolve()) for name in names}


def settings():
    config = read(HERE / 'config.json')
    require(config['temporal_adapter_enabled'] is True and config['new_optimizer_updates'] == 0 and
            config['new_T_training_started'] is False, 'B2 must use trained B, not untrained Z or fake T')
    return config


def verify():
    require(read(HERE / 'cpu_acceptance.json')['status'] == 'PASS_B2_CPU_CONTRACTS', 'B2 CPU gate missing')
    require(read(HERE / 'processor_acceptance.json')['status'] == 'PASS_B2_REAL_PROCESSOR_AND_NATIVE_SOURCE',
            'B2 actual processor gate missing')
    lock = read(HERE / 'source_lock.json')
    for path, digest in lock['files'].items():
        require(sha(path) == digest, 'B2 registered file changed: ' + path)
    bind_helpers()
    return settings()


def inputs(scope):
    item = settings()['inputs'][scope]
    require(sha(item['manifest']) == item['manifest_sha256'], 'input manifest changed')
    from frame_contract import load_clocks
    manifest = read(item['manifest'])
    clocks = load_clocks(manifest, item['registry'], item['registry_sha256'])
    return item, manifest, clocks
