"""Explicit-root, immutable receipts for a new external visual-only cohort."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import sys

MODEL_PARAMETERS = 8782459120
BASE_PARAMETERS = 8767123696
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
TIME_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
SCHEMA = 'CALIBRATED_CONFIRM_NEW_EXTERNAL_V1'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            value.update(block)
    return value.hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(value):
    path = Path(value['path'])
    require(path.is_file() and sha(path) == value['sha256']
            and ('bytes' not in value or path.stat().st_size == value['bytes']), 'Bound file changed: '+str(path))
    return path


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def leaf(name, path):
    """Canonical old imports are guarded, never silently alias another runtime."""
    path = Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve() == path, 'Namespace collision: '+name)
        return sys.modules[name]
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Run:
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        self.c = read(self.config_path)
        require(self.c['schema'] == SCHEMA, 'Explicit confirmation config schema')
        for value in self.c['implementation_refs'].values():
            bound(value)
        self.root = Path(self.c['root']).resolve()
        self.ram = Path(self.c['ram_root']).resolve()
        allowed_ram = Path('/dev/shm/aic_calibrated_confirm4_20261018_v1')
        require(self.ram == allowed_ram or allowed_ram in self.ram.parents, 'Task-owned RAM root required')
        require(self.ram != Path('/dev/shm'), 'No shared-root ownership')
        self.sources = []
        for registered in self.c['sources']:
            source = dict(registered)
            if 'media_ref' in source:
                require('media' not in source or source['media'] == source['media_ref'], 'Ambiguous media aliases')
                source['media'] = source['media_ref']
            require('media' in source, 'Explicit source media_ref required')
            self.sources.append(source)
        ids = [s['sid'] for s in self.sources]
        require(ids == self.c['source_ids'] and len(ids) == self.c['source_count']
                and 0 < len(ids) <= 4 and len(set(ids)) == len(ids), 'Frozen source IDs/count/order')
        require(all(re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', s) for s in ids), 'Safe source IDs')
        require(len({s['media']['sha256'] for s in self.sources}) == len(ids), 'No duplicate source media')
        require(self.c['labels_available_to_pipeline'] is False, 'Visual pipeline must not read references')
        require(self.c['model_parameters'] == MODEL_PARAMETERS, 'Original B/TIME parameter budget')
        require(self.c['maximum_source_seconds'] > 0, 'Explicit fixed cohort duration cap')
        names = [self.c['gpu_stages'][family]['name'] for family in ('b0', 'verify', 'context')]
        require(len(set(names)) == 3 and all(re.fullmatch(r'[A-Za-z0-9_.-]{1,150}', name) for name in names),
                'Three explicit unique safe GPU job names')
        self.dependencies = self.c['dependency_refs']

    def dependency(self, name):
        return bound(self.dependencies[name])

    def module(self, name):
        if name == 'native_profile_04':
            self.module('native_profile_01')
        if name in ('cv_tokens', 'cv_grammar'):
            self.module('cv_contract')
        if name in ('prepare_v3', 'prepare_v5'):
            self.module('sr_common')
        if name == 'prepare_v5':
            self.module('prepare_v3')
        return leaf(name, self.dependency(name))

    def runtime(self):
        for name in ('engine', 'common', 'contracts', 'bw_video', 'exact_pts', 'native_frames'):
            if name in sys.modules:
                require(Path(sys.modules[name].__file__).resolve() == bound(self.dependencies[name]).resolve(),
                        'Pre-existing historical namespace collision: '+name)
        rt = self.module('runtime')
        # These files are imported by the historical runtime under global names.
        for name in ('engine', 'common', 'contracts', 'bw_video', 'exact_pts', 'native_frames'):
            require(name in sys.modules, 'Historical runtime dependency missing: '+name)
            expected = self.dependencies.get(name)
            require(expected is not None and Path(sys.modules[name].__file__).resolve() == bound(expected).resolve(),
                    'Historical runtime dependency collision: '+name)
        return rt

    def model_config(self):
        return read(self.dependency('model_config'))

    def cpu(self):
        require(socket.gethostname() == self.c['hostname'] and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
                'Only this CPU child may hide CUDA; host must match registration')

    def deadline(self):
        require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(self.c['deadline_utc'].replace('Z', '+00:00')),
                'Registered work window ended')

    def stage_dir(self, stage):
        return self.root/'stages'/stage

    def begin(self, stage):
        self.deadline()
        path = self.stage_dir(stage)
        path.mkdir(parents=True, exist_ok=False)
        save(path/'started.json', dict(stage=stage, config_ref=ref(self.config_path), pid=os.getpid(), utc=utc()))
        return path

    def receipt(self, stage):
        value = read(self.stage_dir(stage)/'completion.json')
        require(value['status'] == 'PASS' and value['config_sha256'] == sha(self.config_path), 'Unaccepted stage '+stage)
        return value

    def finish(self, stage, **values):
        save(self.stage_dir(stage)/'completion.json', dict(status='PASS', stage=stage, config_sha256=sha(self.config_path),
             source_ids=self.c['source_ids'], source_count=len(self.sources), labels_read=False, utc=utc(), **values))

    def lock(self, family, producer, qa, expected_calls):
        refs = {name: value for name, value in self.dependencies.items()}
        refs.update({'processor_'+name: value for name, value in self.c['processor_asset_refs'].items()})
        refs['external_native_admission'] = self.native_admission()
        for path in sorted(Path(__file__).parent.glob('*.py')):
            refs['new_'+path.name] = ref(path)
        save(self.root/'locks'/(family+'.json'), dict(config_ref=ref(self.config_path), producer_ref=ref(self.stage_dir(producer)/'completion.json'),
             input_qa_ref=ref(self.stage_dir(qa)/'completion.json'), code_refs=refs, expected_calls=expected_calls,
             source_ids=self.c['source_ids'], gpu=self.c['gpu_stages'][family], labels_read=False))

    def native_admission(self):
        """Read only the external PASS/binding receipt; never original intervals."""
        path = Path(self.c['native_admission_path'])
        value = read(path)
        expected = {source['sid']: source['clock_ref']['sha256'] for source in self.receipt('b0_prepare')['sources']}
        require(value['status'] == 'PASS' and value['source_ids'] == self.c['source_ids']
                and value['clock_sha256_by_sid'] == expected and value['original_endpoints_fit'] is True
                and value['no_label_resizing'] is True and value['labels_provided_to_model'] is False,
                'External unmodified native/reference endpoint admission receipt must match these exact new clocks')
        return ref(path)

    def accepted(self, family):
        lock = read(self.root/'locks'/(family+'.json'))
        bound(lock['config_ref']); bound(lock['producer_ref']); bound(lock['input_qa_ref'])
        for item in lock['code_refs'].values():
            bound(item)
        require(lock['source_ids'] == self.c['source_ids'] and lock['gpu'] == self.c['gpu_stages'][family], 'GPU stage lock drift')
        return lock

    def terminal(self, family):
        spec = self.c['gpu_stages'][family]
        path = Path(self.c['resource_directory'])/(spec['name']+'.resource.json')
        terminal = read(path)
        matching = [json.loads(line) for line in Path(self.c['gpu_ledger']).read_text().splitlines()
                    if line.strip() and json.loads(line).get('name') == spec['name']]
        require(matching == [terminal] and terminal['name'] == spec['name'] and terminal['status'] == 'completed'
                and terminal.get('exit_code', terminal.get('returncode')) == 0, 'Unique successful shared GPU terminal required')
        return ref(path)


def verify_model(model, identity):
    require(identity['logical_parameters'] == MODEL_PARAMETERS and identity['base']['parameters'] == BASE_PARAMETERS
            and identity['base']['sha256'] == BASE_SHA and identity['adapter']['sha256'] == TIME_SHA
            and identity['adapter']['tensors'] == 288 and identity['adapter']['actual_saved_values_equal']
            and identity['adapter']['adapter_enabled'] and model.active_adapter == 'default', 'Actual unchanged B/TIME identity')


def launch_spec(run, family):
    require(os.environ.get('CUDA_VISIBLE_DEVICES'), 'Controller parent CUDA visibility must remain nonempty')
    lock = run.accepted(family)
    spec = run.c['gpu_stages'][family]
    require(spec['max_seconds'] > 0 and spec['planned_output_bytes'] >= 0 and spec['capacity_reason'], 'Explicit dynamic GPU cost/capacity registration')
    return [run.c['python'], str(run.dependency('gpu_runner')), '--name', spec['name'], '--max-seconds', str(spec['max_seconds']),
            '--planned-output-bytes', str(spec['planned_output_bytes']), '--capacity-reason', spec['capacity_reason'],
            '--queue-seconds', str(spec['queue_seconds']), '--', run.c['python'], '-B', str(Path(__file__).parent/'pipeline.py'),
            str(run.config_path), family+'_gpu']
