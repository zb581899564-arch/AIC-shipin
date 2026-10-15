"""Control-only helpers and immutable bootstrap. No pixels/GT/model loader."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from pc_contract import SCHEMA,require

HOME=Path('/home/inspur/aic_video_work');CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_production_control_v6';INPUT=CAMPAIGN/'temporal_production_inputs_v5'
RUNTIME=CAMPAIGN/'temporal_production_runtime_v5'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ORIGINAL_CONTROL=CAMPAIGN/'temporal_production_control_v4'
IMPORT_DIRECTORIES=tuple(RUN/name for name in ('b_score_aligned_package_v4','baseline_a_pts_v1',
    'baseline_a_pts_v1/vendor','balanced_two_window_risk_v3','temporal_sft8b_v1','resource_unlimited_v1_20261007'))


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())


def append(path,row):
    with Path(path).open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())


def rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def bound(ref,roots):
    path=Path(ref['path']).resolve();require(any(path.is_relative_to(root) for root in roots) and path.is_file() and sha(path)==ref['sha256'],
        'Frozen bootstrap path/SHA changed or escaped');return path


def official_rule_leaf(ref):
    inherited=CAMPAIGN/'temporal_production_inputs_v4/bindings/official_rules.json'
    if Path(ref['path']).resolve()==inherited:
        require(ref['sha256']=='b3dc2b7c080145efa3d72f413f4bb6fa8081f55b00bda97000fe83ed8284945b' and
            inherited.is_file() and sha(inherited)==ref['sha256'],
            'Only the exact successful original official-rule leaf may be inherited')
        return inherited
    return bound(ref,(BASE,INPUT,RUNTIME))


def module(name,path):
    path=Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,'Control import namespace shadowed');return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value


def load(registration_path,child=False):
    from handoff import load_context
    return load_context(sys.modules[__name__],registration_path,child=child)

def host(parent=False):
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5','Linux actual control host required')
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')) if parent else os.environ.get('CUDA_VISIBLE_DEVICES')=='',
        'Parent CUDA nonempty; CPU child alone hides CUDA')


def before_new_operation(reg):
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline'].replace('Z','+00:00')),
        'Deadline reached: no new source/processor/job; existing jobs must finish naturally')
    from handoff import old_parent_exclusive
    old_parent_exclusive(read(bound(reg['quiescent_handoff_ref'],(CAMPAIGN/'prospective_cache_handoff_01',))))


def snapshot(cache_root):
    import shutil
    mem={line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=utc(),mem_available_bytes=mem['MemAvailable'],disk_available_bytes=shutil.disk_usage(cache_root).free,
        affinity_cpus=len(os.sched_getaffinity(0)),load_1min=os.getloadavg()[0])
