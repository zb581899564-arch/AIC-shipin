"""Future Linux metadata-only bootstrap IO. No prepare/GPU permission issuer."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sys

from pb_contract import SCHEMA,require

HOME=Path('/home/inspur/aic_video_work');CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_production_bootstrap_v1'
INPUT=CAMPAIGN/'temporal_production_inputs_v4';RUNTIME=CAMPAIGN/'temporal_production_runtime_v4'
CONTROL=CAMPAIGN/'temporal_production_control_v3';RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.flush();os.fsync(f.fileno())


def ref(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))


def bound(value,roots=(CAMPAIGN,RUN)):
    path=Path(value['path']).resolve()
    require(any(path.is_relative_to(root) for root in roots) and path.is_file() and sha(path)==value['sha256'],
        'Frozen metadata/code escaped or changed');return path


def retain(value,target):
    source=bound(value);data=source.read_bytes();target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    require(sha(target)==value['sha256'],'Retained leaf evidence changed');return ref(target)


def module(name,path):
    path=Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,'Bootstrap module shadowed');return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def host():
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
        'Linux metadata child must hide only its own CUDA')


def snapshot():
    mem=next(int(row.split()[1])*1024 for row in Path('/proc/meminfo').read_text().splitlines() if row.startswith('MemAvailable:'))
    return dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),mem_available_bytes=mem,disk_available_bytes=shutil.disk_usage(CAMPAIGN).free,
        affinity_cpus=len(os.sched_getaffinity(0)),load_1min=os.getloadavg()[0])


def config(path):
    path=Path(path).resolve();require(path.is_relative_to(BASE),'Independent bootstrap root required');value=read(path)
    require(value['schema']==SCHEMA and value['metadata_build_approved'] is True and value['formal_prepare_or_GPU_execution_by_builder'] is False and
        value['test_GT_read'] is False and value['whole_graph_batch_roles_frozen_before_first_model'] is True,
        'Root metadata-only bootstrap authorization required')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(value['deadline'].replace('Z','+00:00')),'Deadline: no new bootstrap')
    for name,digest in value['required_code_files'].items():require(sha(name)==digest,'Frozen builder/config dependency changed')
    for file in Path(__file__).parent.glob('*.py'):
        require(value['required_code_files'].get(str(file.resolve()))==sha(file),'Every actual bootstrap code file must be frozen')
    return value
