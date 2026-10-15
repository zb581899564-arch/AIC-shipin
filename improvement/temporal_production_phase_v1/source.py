"""Explicit future SOURCE adapter; original INPUT5 modules remain unchanged.

This file is the actual new writer, not a claim that the original prepare.py
directly executed with its original cache implementation.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import sys
from types import FunctionType

HOME = Path('/home/inspur/aic_video_work')
CAMPAIGN = HOME/'twenty_hour_five_20261014_v1'
BASE = CAMPAIGN/'temporal_production_phase_v1'
INPUT = CAMPAIGN/'temporal_production_inputs_v5'
CONTROL = CAMPAIGN/'temporal_production_control_v6'
BACKEND = CAMPAIGN/'prospective_cache_backend_v1'
HANDOFF = CAMPAIGN/'prospective_cache_handoff_01'
SCHEMA = 'TEMPORAL_PRODUCTION_SOURCE_PHASE_V1'
STATUS = 'MAIN_APPROVED_PROSPECTIVE_SOURCE_PHASE_AFTER_QUIESCENT_HANDOFF'
EXECUTION_KIND = 'EXPLICIT_FUNCTION_GLOBALS_COPY_UNCHANGED_FROZEN_BYTECODE'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            value.update(block)
    return value.hexdigest()


def checked(ref, roots):
    path = Path(ref['path']).absolute()
    require(any(path.is_relative_to(root) for root in roots) and path.is_file(),
            'Phase reference escaped its exact declared owner')
    require(all(not p.is_symlink() for p in (path, *path.parents)), 'Phase reference follows a link')
    require(re.fullmatch(r'[0-9a-f]{64}', ref['sha256']) and sha(path) == ref['sha256'],
            'Phase/code/metadata reference changed')
    if 'bytes' in ref:
        require(path.stat().st_size == ref['bytes'], 'Phase evidence size changed')
    return path


def file_ref(path):
    path = Path(path).absolute()
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def frozen_module(name, path):
    """Unique unchanged owner, without importing processor or decoder code."""
    path = Path(path).absolute()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).absolute() == path,
                'Original INPUT5 import namespace shadowed: '+name)
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def admission(path, registration_path, source_id):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux' and
            os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this Linux CPU child may prepare SOURCE')
    path = Path(path).absolute()
    require(path.is_relative_to(CONTROL) or path.is_relative_to(BASE), 'Independent phase admission owner required')
    own = file_ref(Path(__file__).absolute())
    require(Path(own['path']).parent == BASE/'code', 'Actual SOURCE wrapper must have its registered new owner')
    value = read(checked(file_ref(path), (CONTROL, BASE)))
    require(value['schema'] == SCHEMA and value['status'] == STATUS and
            value['no_old_writer_active'] is True and value['model_calls_authorized'] == 0 and
            value['first_normal_processor_replay_required'] is True and
            value['original_graph_membership_and_roles_unchanged'] is True and
            value['source_algorithm_changed'] is False and value['phase_code_ref'] == own,
            'Separate main-approved SOURCE phase/code/first-QA gate is required')
    for key, roots in (('input_registration_ref', (INPUT,)),
                       ('whole_plan_ref', (INPUT/'plan_01',)),
                       ('original_preparation_code_ref', (INPUT/'code',)),
                       ('backend_code_ref', (BACKEND/'code',)),
                       ('backend_admission_ref', (CONTROL, BACKEND)),
                       ('controller_registration_ref', (CONTROL,)),
                       ('quiescent_handoff_ref', (CONTROL, HANDOFF))):
        checked(value[key], roots)
    handoff = read(value['quiescent_handoff_ref']['path'])
    require(handoff['schema'] == 'CONTROLLED_REMAINING_HANDOFF_V1' and
            handoff['status'] == 'MAIN_CONTROLLED_HANDOFF_STOP' and
            handoff['all_begun_owned_children_naturally_terminal'] is True and
            handoff['active_old_writer_count'] == 0 and handoff['old_parent_scheduling_stopped'] is True and
            handoff['old_failure_promoted_to_success'] is False,
            'Parent hold alone cannot admit a SOURCE writer before real quiescence')
    require(Path(value['input_registration_ref']['path']).absolute() == Path(registration_path).absolute() and
            Path(value['original_preparation_code_ref']['path']).absolute() == INPUT/'code/prepare_source.py' and
            Path(value['backend_code_ref']['path']).absolute() == BACKEND/'code/backend.py' and
            Path(value['whole_plan_ref']['path']).absolute() == INPUT/'plan_01/full_plan.json',
            'Original source plan/prepare/registration or actual backend owner changed')
    for ref in value['required_code_refs']:
        checked(ref, (INPUT/'code', BASE/'code', BACKEND/'code', CONTROL/'code'))
    refs = {ref['path']: ref['sha256'] for ref in value['required_code_refs']}
    for ref in (own, value['original_preparation_code_ref'], value['backend_code_ref']):
        require(refs.get(ref['path']) == ref['sha256'], 'Actual producer code absent from phase closure')
    control = read(value['controller_registration_ref']['path'])
    require(control['prospective_source_phase_code_ref'] == own and
            Path(control['prospective_source_phase_admission_path']).absolute() == path and
            control['prospective_backend_code_ref'] == value['backend_code_ref'] and
            Path(control['prospective_backend_admission_path']).absolute() ==
            Path(value['backend_admission_ref']['path']).absolute() and control['deadline'] == value['deadline'],
            'SOURCE adapter/admission must be explicit in the frozen new controller')
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(value['deadline'].replace('Z', '+00:00')),
            'No new SOURCE may begin after the frozen deadline')
    remaining = value['remaining_source_ids']
    successful = value['original_successful_source_completion_refs']
    require(isinstance(remaining, list) and len(set(remaining)) == len(remaining) and source_id in remaining and
            isinstance(successful, dict) and not set(remaining) & set(successful),
            'Only predeclared unstarted SOURCE may use the new producer')
    backend = read(value['backend_admission_ref']['path'])
    require(backend['controller_registration_ref'] == value['controller_registration_ref'] and
            backend['quiescent_handoff_ref'] == value['quiescent_handoff_ref'] and
            backend['no_old_writer_active'] is True and
            any(ref['path'] == value['backend_code_ref']['path'] and
                ref['sha256'] == value['backend_code_ref']['sha256'] for ref in backend['required_code_refs']),
            'Source and backend must share the actual quiescent handoff and code identity')
    value['_phase_admission_ref'] = file_ref(path)
    value['_backend_admission'] = backend
    return value


def unstarted_source(plan, reg, value, source_id):
    """Names only; no old media, tensor, RGB or completed proof body is read."""
    order = [source['source_id'] for source in plan['sources']]
    require(len(order) == len(set(order)) and value['remaining_source_ids'] ==
            [sid for sid in order if sid in set(value['remaining_source_ids'])],
            'Remaining source membership/order differs from the original graph')
    source = next(source for source in plan['sources'] if source['source_id'] == source_id)
    rows = [row for row in plan['requests'] if row['source_id'] == source_id]
    groups = {key: row for key, row in plan['RGB_groups'].items() if row['source_id'] == source_id}
    consumers = [row['request_id'] for row in rows if row['execution'] == 'MODEL']
    require(set(consumers) <= set(value['_backend_admission']['producer_consumers']),
            'A frozen SOURCE consumer is not admitted for the new backend')
    base = Path(reg['cache_root']).absolute()
    require(value['_backend_admission']['cache_root'] == str(base), 'Backend cache owner changed')
    relative = ['permanent/proofs/source_'+source_id+'_'+suffix+'.json'
                for suffix in ('launch', 'completion', 'failure')]
    relative += ['permanent/proofs/'+kind+'_'+source_id+'.json'
                 for kind in ('native_measurement', 'RGB_checkpoint', 'clock')]
    for row in rows:
        rid = row['request_id']
        relative += ['permanent/proofs/'+rid+'_CPU_input.json',
                     'permanent/proofs/'+rid+'_structural_unknown.json',
                     'permanent/proofs/'+rid+'_producer_provenance.json',
                     'permanent/inputs/'+rid+'.json', 'permanent/inputs/'+rid+'.private.pt.gz']
    for key, group in groups.items():
        relative += [group['rgb_relative'], 'permanent/leases/'+key+'.json']
    require(all(not (base/name).exists() for name in relative),
            'SOURCE already begun or partial evidence exists; retain all and require explicit recovery')
    return source, rows, groups


class ProducerStore:
    """New writer provenance is included before each first metadata commit."""
    def __init__(self, store, provenance, actual_code):
        self._store = store
        self._provenance = provenance
        self._actual_code = actual_code
        self._structural_provenance = {}

    def __getattr__(self, name):
        return getattr(self._store, name)

    def decorate(self, value):
        result = dict(value)
        for key, item in self._provenance.items():
            require(key not in result or result[key] == item, 'Conflicting actual producer provenance')
            result[key] = item
        return result

    def write_metadata(self, relative, value):
        if relative.endswith('_structural_unknown.json'):
            # Frozen PR5 requires exact equality with the original typed result.
            # Bind the new writer with an independent first-written companion.
            companion = relative[:-len('_structural_unknown.json')]+'_producer_provenance.json'
            proof = self._store.write_metadata(companion, self.decorate(dict(
                status='PREDECLARED_STRUCTURAL_BODY_PRODUCER_BINDING_NO_MODEL_OR_PIXEL_CALL',
                structural_result_relative=relative, structural_result=value,
                structural_body_has_unchanged_frozen_schema=True, actual_model_call=False)))
            self._structural_provenance[relative] = proof
            return self._store.write_metadata(relative, value)
        result = self.decorate(value)
        if relative.endswith('_completion.json') or relative.endswith('_failure.json'):
            result['structural_producer_provenance_refs'] = dict(self._structural_provenance)
        return self._store.write_metadata(relative, result)

    def save_input(self, consumer, encoded, visual_keys, identity, metadata):
        identity = dict(identity, preprocessing_code=dict(identity['preprocessing_code']))
        for path, digest in self._actual_code.items():
            require(path not in identity['preprocessing_code'] or identity['preprocessing_code'][path] == digest,
                    'Original preprocessing code map was overwritten')
            identity['preprocessing_code'][path] = digest
        metadata = dict(metadata)
        metadata['provenance'] = self.decorate(metadata.get('provenance', {}))
        return self._store.save_input(consumer, encoded, visual_keys, identity, metadata)


class CacheFacade:
    def __init__(self, original, backend, value, provenance):
        self._original = original
        self._backend = backend
        self._value = value
        self._provenance = provenance

    def __getattr__(self, name):
        return getattr(self._original, name)

    def LeaseStore(self, cache_root):
        actual_code = {self._value[key]['path']: self._value[key]['sha256']
                       for key in ('phase_code_ref', 'backend_code_ref')}
        store = self._backend.open_store(self._original.LeaseStore, cache_root,
                                        self._value['backend_admission_ref']['path'])
        return ProducerStore(store, self._provenance, actual_code)


class IOFacade:
    def __init__(self, original, backend, value, provenance):
        self._original = original
        self._backend = backend
        self._value = value
        self._provenance = provenance

    def __getattr__(self, name):
        return getattr(self._original, name)

    def libraries(self, reg, cpu=False):
        result = dict(self._original.libraries(reg, cpu=cpu))
        result['cache'] = CacheFacade(result['cache'], self._backend, self._value, self._provenance)
        return result


def prepare_adapter(original, io_facade):
    """Copy the function namespace, never assign to frozen module globals."""
    namespace = dict(original.__dict__)
    namespace['io'] = io_facade
    for name, value in original.__dict__.items():
        if isinstance(value, FunctionType) and value.__globals__ is original.__dict__:
            clone = FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            clone.__kwdefaults__ = value.__kwdefaults__
            clone.__annotations__ = dict(value.__annotations__)
            namespace[name] = clone
    require(namespace['prepare'].__code__ is original.prepare.__code__ and
            original.__dict__['io'] is not io_facade, 'Frozen SOURCE module was mutated')
    return namespace['prepare']


def run(registration_path, source_id, phase_admission_path):
    value = admission(phase_admission_path, registration_path, source_id)
    original_reg = read(value['input_registration_ref']['path'])
    for name in ('tp_contract.py', 'tp_io.py', 'prepare_source.py'):
        path = INPUT/'code'/name
        require(original_reg['required_code_files'].get(str(path)) == sha(path),
                'Frozen INPUT5 import/code owner changed')
    frozen_module('tp_contract', INPUT/'code/tp_contract.py')
    original_io = frozen_module('tp_io', INPUT/'code/tp_io.py')
    original = frozen_module('_prospective_unchanged_input5_prepare', INPUT/'code/prepare_source.py')
    backend = frozen_module('_prospective_source_exact_backend', value['backend_code_ref']['path'])
    reg = original_io.registration(registration_path)
    original_io.actual_permission(reg)
    plan, complete = original.load_plan(reg)
    require(complete['full_plan_sha256'] == value['whole_plan_ref']['sha256'], 'Frozen SOURCE graph changed')
    unstarted_source(plan, reg, value, source_id)
    provenance = dict(prospective_phase_ref=value['phase_code_ref'],
        prospective_backend_ref=value['backend_admission_ref'],
        prospective_backend_code_ref=value['backend_code_ref'],
        prospective_source_phase_admission_ref=value['_phase_admission_ref'],
        original_preparation_code_ref=value['original_preparation_code_ref'],
        actual_source_writer_execution_kind=EXECUTION_KIND,
        original_source_math_bytecode_unchanged=True, original_input_registration_ref=value['input_registration_ref'])
    provenance['prospective_producer_provenance'] = dict(provenance)
    facade = IOFacade(original_io, backend, value, provenance)
    prepare_adapter(original, facade)(reg, source_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', required=True, type=Path)
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--phase-admission', required=True, type=Path)
    args = parser.parse_args()
    # CPU child only. The parent controller/GPU environment is untouched.
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.dont_write_bytecode = True
    run(args.registration, args.source_id, args.phase_admission)
