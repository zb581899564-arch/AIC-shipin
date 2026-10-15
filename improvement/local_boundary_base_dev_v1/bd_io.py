"""Metadata closure and frozen V4 helper imports; never prepares source inputs."""
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sys

import bd_contract as c

HOME = Path('/home/inspur/aic_video_work')
CAMPAIGN = HOME/'twenty_hour_five_20261014_v1'
BASE = CAMPAIGN/'local_boundary_base_dev_v1'
SOURCE = CAMPAIGN/'local_boundary_v4'
SOURCE_CODE = SOURCE/'code'
METRIC = CAMPAIGN/'charades_boundary_metric_v1'
CONTROLS = CAMPAIGN/'local_boundary_base_dev_control_v1'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CODE = Path(__file__).resolve().parent
ROOTS = (BASE, SOURCE, METRIC, CONTROLS, CAMPAIGN/'local_boundary_v4_metadata', CAMPAIGN/'charades_boundary_v1',
         CAMPAIGN/'charades_boundary_v2', CAMPAIGN/'charades_coarse_v1',
         HOME/'temporal_refinement_pilot_20261011/dev_01', RUN)


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


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def host(cpu=False):
    c.require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux', 'Linux-only research host required')
    c.require((os.environ.get('CUDA_VISIBLE_DEVICES') == '') if cpu else
              (os.environ.get('CUDA_VISIBLE_DEVICES') != ''), 'CPU child or GPU CUDA visibility differs')


def base_path(value):
    value = Path(value).resolve()
    c.require(value in (BASE.resolve(), (BASE/'dev').resolve(), (BASE/'confirm').resolve()),
              'A separate explicit paired role root is required')
    return value


def checked_ref(ref, roots=ROOTS):
    path = Path(ref['path']).resolve()
    c.require(any(path.is_relative_to(Path(root).resolve()) for root in roots), 'Frozen evidence escaped admitted roots')
    c.require(sha(path) == ref['sha256'], 'Frozen evidence changed: '+str(path))
    return path


def own_code_files():
    return {str(path.resolve()): sha(path) for path in sorted(CODE.glob('*.py'))}


def old_helpers(files):
    expected = {str(path.resolve()) for path in SOURCE_CODE.glob('*.py')}
    c.require(set(files) == expected and expected, 'Exact frozen V4 code inventory required')
    for path, digest in files.items():
        checked_ref(dict(path=path, sha256=digest), roots=(SOURCE_CODE,))
    sys.path.insert(0, str(SOURCE_CODE))
    names = ('lb_contract', 'lb_structural', 'lb_io', 'lb_grammar', 'replay_local_boundaries')
    for name in names:
        if name in sys.modules:
            c.require(Path(sys.modules[name].__file__).resolve() == SOURCE_CODE/(name+'.py'),
                      'Original helper module name unexpectedly shadowed: '+name)
    modules = {name: importlib.import_module(name) for name in names}
    for name, module in modules.items():
        c.require(Path(module.__file__).resolve() == SOURCE_CODE/(name+'.py'), 'Wrong frozen V4 module: '+name)
    return dict(io=modules['lb_io'], contract=modules['lb_contract'], grammar=modules['lb_grammar'],
                replay=modules['replay_local_boundaries'])


def deadline(protocol):
    c.require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(protocol['deadline'].replace('Z', '+00:00')),
              'No new BASE model call after the frozen deadline')


def read_journal(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def source_bundle(source, role):
    """Only completed TIME metadata and its first input proofs; no tensors/RGB.

    Returns a small-file closure the main can freeze. This is never an encoder,
    source replay, comparison, or launcher. It refuses a partially completed TIME.
    """
    source = Path(source).resolve()
    c.require(source == (SOURCE/role).resolve(), 'Unchanged original V4 source role root required')
    cpu_path = source/'cpu_01/completion.json'
    cpu = read(cpu_path)
    c.require(cpu['status'] == 'PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION' and
              cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and
              cpu['new_model_calls'] == cpu['new_optimizer_updates'] == 0,
              'The original accepted V4 CPU completion is not complete')
    helpers = old_helpers(cpu['bindings']['own_code_files'])
    oldio = helpers['io']
    plan, events, requests, skips, denominators = oldio.plan_partition(source)
    c.require(c.counts(events, requests, skips) == denominators and cpu['events'] == len(events) and
              cpu['requests'] == len(requests) and all(cpu[k] == v for k, v in denominators.items()) and
              cpu['plan_partition_sha256'] == sha(source/'plan_01/endpoint_records.json') and
              sha(plan['registration_path']) == plan['registration_sha256'] and
              cpu['bindings']['registration_sha256'] == plan['registration_sha256'] and
              cpu['bindings']['plan_completion_sha256'] == sha(source/'plan_01/completion.json'),
              'Original accepted input and full nominal partition differ')
    source_registration = read(plan['registration_path'])
    c.require(all(e['source_role'] == role for e in events) and
              source_registration['validation_scope'] == ('EXTERNAL_DEVELOPMENT_DIAGNOSTIC' if role == 'dev' else
                                                          'EXTERNAL_CONFIRMATION_DIAGNOSTIC') and
              source_registration['source_scope'] == ('EXTERNAL_NONTEST_DEVELOPMENT_ONLY' if role == 'dev' else
                                                      'EXTERNAL_NONTEST_CONFIRMATION_ONLY'),
              'Original source role changed')
    permit_path = source/'gpu_admission.json'
    permit = read(permit_path)
    c.require(permit['status'] == 'PASS_INDEPENDENT_LOCAL_BOUNDARY_GPU_ADMISSION' and
              permit['cpu_completion_sha256'] == sha(cpu_path) and permit['actual_model_call_budget'] == len(requests) and
              permit['registration_sha256'] == plan['registration_sha256'] and
              permit['model_parameters'] == c.PHYSICAL_PARAMETERS and permit['optimizer_updates'] == 0,
              'Original TIME GPU admission differs from accepted inputs')
    resource, resource_sha = oldio.terminal_resource(permit['gpu_job_name'])
    gpu, replay = source/'gpu_01', source/'replay_01'
    complete, independent = read(gpu/'completion.json'), read(replay/'completion.json')
    c.require(complete['status'] == 'PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY' and
              complete['requests'] == complete['actual_model_calls'] == len(requests) and
              complete['events'] == len(events) and all(complete[k] == v for k, v in denominators.items()) and
              complete['gpu_admission_sha256'] == sha(permit_path) and
              complete['attempts_sha256'] == sha(gpu/'attempts.jsonl') and
              complete['model_identity_sha256'] == sha(gpu/'model_identity.json') and
              complete['structural_skips_sha256'] == sha(source/'plan_01/structural_skips.json') and
              independent['status'] == 'PASS_ALL_NEW_LOCAL_BOUNDARY_INDEPENDENT_REPLAYS_NOT_QUALITY' and
              independent['requests'] == len(requests) and independent['events'] == len(events) and
              independent['CPU_only'] is True and independent['CUDA_initialized'] is False and
              independent['new_model_calls'] == independent['new_optimizer_updates'] == 0 and
              independent['gpu_completion_sha256'] == sha(gpu/'completion.json') and
              independent['resource_terminal_sha256'] == resource_sha and
              all(independent[k] == v for k, v in denominators.items()),
              'TIME must naturally finish every call and first independent input replay before BASE')
    c.validate_journal(read_journal(gpu/'attempts.jsonl'), [x['request_id'] for x in cpu['proofs']], complete['entries'])
    model = read(gpu/'model_identity.json')['identity']
    oldio.verify_model(type('LoadedIdentity', (), {'active_adapter': 'default'})(), model)
    export_path = source/'boundary_prediction_export.json'
    exported = read(export_path)
    c.require(exported['status'] == 'PASS_LOCAL_BOUNDARY_EXECUTION_REPLAY_NOT_QUALITY' and
              exported['independent_replay_completion_sha256'] == sha(replay/'completion.json') and
              exported['retained_events'] == len(events) and exported['full_endpoint_results'] == 2*len(events) and
              exported['actual_model_calls'] == exported['actual_independent_model_replays'] == len(requests) and
              exported['structural_geometry_proof_count'] == len(skips) and
              [x['event_id'] for x in exported['events']] == [x['event_id'] for x in events] and
              exported['newly_created_events'] == exported['removed_events'] == 0,
              'Complete original TIME nominal event export required')
    required = {}
    def bind(path, digest=None):
        path = Path(path).resolve()
        digest = sha(path) if digest is None else digest
        checked_ref(dict(path=str(path), sha256=digest))
        c.require(str(path) not in required or required[str(path)] == digest, 'Contradictory prior metadata binding')
        required[str(path)] = digest
        return path
    for path in (cpu_path, permit_path, plan['registration_path'], gpu/'completion.json', gpu/'attempts.jsonl',
                 gpu/'model_identity.json', replay/'completion.json', export_path,
                 RUN/'controller'/(permit['gpu_job_name']+'.resource.json')):
        bind(path)
    for path in (source/'plan_01').glob('*.json'):
        bind(path)
    for path, digest in cpu['bindings']['own_code_files'].items():
        bind(path, digest)
    runtime_binding = cpu['bindings']['original_b_processor_runtime']
    bind(RUN/'b_score_aligned_package_v4/config.json', runtime_binding['original_config_sha256'])
    for mapping in ('runtime_files', 'processor_assets'):
        for path, digest in runtime_binding[mapping].items():
            bind(path, digest)
    for name in ('protocol', 'official_rule_check'):
        bind(source_registration[name+'_path'], source_registration[name+'_sha256'])
    by_done = {x['request_id']: x for x in complete['entries']}
    by_replay = {x['request_id']: x for x in independent['proofs']}
    by_request = {x['request_id']: x for x in requests}
    c.require(len(by_done) == len(by_replay) == len(by_request) == len(requests) and
              set(by_done) == set(by_replay) == set(by_request), 'Every original callable endpoint needs its real first input replay')
    rows = []
    for entry in cpu['proofs']:
        rid = entry['request_id']
        proof_path = bind(entry['proof_path'], entry['proof_sha256'])
        proof = read(proof_path)
        meta_path = bind(proof['input_path'], proof['input_sha256'])
        meta = read(meta_path)
        done_path = bind(by_done[rid]['done_path'], by_done[rid]['done_sha256'])
        replay_path = bind(by_replay[rid]['proof_path'], by_replay[rid]['proof_sha256'])
        c.require(done_path == gpu/rid/'done.json' and replay_path == replay/(rid+'.json'),
                  'Original TIME unique output/replay paths differ')
        old_done, old_replay = read(done_path), read(replay_path)
        raw_path, request_path = bind(gpu/rid/'raw.json'), bind(gpu/rid/'request.json')
        raw, request = read(raw_path), read(request_path)
        c.require(proof['status'].startswith('PASS_CPU_LOCAL_BOUNDARY_') and proof['bindings'] == cpu['bindings'] and
                  proof['request_id'] == meta['request_id'] == rid and
                  proof['input_sha256'] == entry['input_sha256'] and
                  meta['event_id'] == by_request[rid]['event_id'] and meta['side'] == by_request[rid]['side'] and
                  all(meta[key] == by_request[rid][key] for key in ('source_id', 'source_bytes', 'source_total_frames',
                      'source_frame_ordinals', 'sample_exact_pts', 'all_source_exact_pts', 'window_start', 'window_end',
                      'original_evidence', 'clock_object_keys')) and
                  meta['original_case_id'] == by_request[rid]['original_case_id'] and
                  meta['original_segment_index'] == by_request[rid]['original_segment_index'] and
                  meta['original_interval_exact'] == by_request[rid]['original_interval_exact'] and
                  meta['source_sha256'] == by_request[rid]['source_sha256'] and
                  proof['encoded_tensor_format'] == oldio.TENSOR_CACHE_FORMAT and
                  proof['encoded_tensor_compression_level'] == 1 and
                  old_done['status'] == 'PASS_LOCAL_BOUNDARY_DECISION_NOT_QUALITY' and
                  old_done['request_id'] == rid and old_done['event_id'] == meta['event_id'] and old_done['side'] == meta['side'] and
                  old_done['raw_sha256'] == sha(raw_path) and
                  old_done['request_sha256'] == sha(request_path) and
                  old_replay['status'] == 'PASS_INDEPENDENT_CPU_BOUNDARY_TENSOR_TOKEN_NATIVE_REPLAY' and
                  old_replay['request_id'] == rid and old_replay['event_id'] == meta['event_id'] and
                  old_replay['side'] == meta['side'] and old_replay['CPU_only'] is True and
                  old_replay['new_model_calls'] == old_replay['new_optimizer_updates'] == 0 and
                  old_replay['done_sha256'] == sha(done_path) and old_replay['raw_sha256'] == sha(raw_path) and
                  old_replay['endpoint_result'] == old_done['endpoint_result'] and
                  request['CPU_proof_sha256'] == entry['proof_sha256'] and
                  request['event_id'] == meta['event_id'] and request['side'] == meta['side'] and
                  request['original_case_id'] == meta['original_case_id'] and
                  request['original_segment_index'] == meta['original_segment_index'] and
                  request['original_interval_exact'] == meta['original_interval_exact'] and
                  request['window_start'] == meta['window_start'] and request['window_end'] == meta['window_end'] and
                  request['input_sha256'] == proof['input_sha256'] and
                  request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
                  request['prompt'] == meta['prompt'] == helpers['contract'].prompt(meta) and
                  request['finite_response_strings'] == list(helpers['contract'].response_strings(meta)) and
                  meta['reference_available_to_inference'] is False and meta['audio_observed'] is False and
                  request['reference_labels_read'] is False and raw['actual_model_call'] is True and
                  proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] ==
                  old_done['input_evidence'] == old_replay['input_evidence'],
                  'Original source/proof/input/TIME/raw/first input replay pairing differs')
        for name in ('clock', 'source_separation'):
            ref = meta['original_evidence'][name]
            bind(ref['path'], ref['sha256'])
        rows.append((entry, proof, meta, old_done, old_replay))
    for skip in skips:
        bind(skip['independent_geometry_proof']['path'], skip['independent_geometry_proof']['sha256'])
        bind(skip['original_evidence']['clock']['path'], skip['original_evidence']['clock']['sha256'])
    c.require([r[0]['request_id'] for r in rows] == [x['request_id'] for x in complete['entries']],
              'Same accepted original TIME request order required')
    return dict(cpu=cpu, helpers=helpers, plan=plan, events=events, requests=requests, skips=skips,
                denominators=denominators, rows=rows, original_model_identity=model,
                required_metadata_files=required, TIME_export=exported, TIME_resource_sha256=resource_sha)


def admitted(base):
    """Main owns registration, closure, admission, and the unique reservation."""
    base = base_path(base)
    registration_path = base/'registration_01.json'
    registration = read(registration_path)
    role = registration['role']
    c.require((base != BASE or role == 'dev') and (base.name not in ('dev', 'confirm') or base.name == role),
              'Explicit paired output root and registered role differ')
    bundle = source_bundle(registration['source_root'], role)
    denominators = bundle['denominators']
    protocol_path = checked_ref(dict(path=registration['protocol_path'], sha256=registration['protocol_sha256']), roots=(base,))
    protocol = read(protocol_path)
    c.protocol(protocol, role, SOURCE/role, denominators)
    c.require(registration['schema'] == c.SCHEMA and registration['status'] == c.REGISTRATION_STATUS and
              registration['actual_model_call_budget'] == denominators['actionable_requests'] and
              all(registration[k] == v for k, v in denominators.items()) and
              registration['events'] == len(bundle['events']) and
              registration['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and
              registration['activated_base_parameters'] == c.BASE_PARAMETERS and registration['optimizer_updates'] == 0 and
              registration['own_code_files'] == own_code_files(), 'Frozen new paired registration/counts/code differ')
    official = checked_ref(dict(path=registration['official_rule_check_path'],
                               sha256=registration['official_rule_check_sha256']), roots=(base,))
    if role == 'confirm':
        selection_path = checked_ref(registration['frozen_development_selection'], roots=(METRIC,))
        selection = read(selection_path)
        c.require(selection['status'] == 'FROZEN_GLOBAL_REFINER_ROLE_FROM_DEV_DIAGNOSTIC_NOT_SCIENCE_PASS' and
                  selection['chosen_role'] == 'BASE' and selection['confirm_outputs_read'] is False,
                  'Confirmation needs the root metric08 fixed-dev selection frozen before this role')
    admission_path = base/'gpu_admission.json'
    admission = read(admission_path)
    lock_path = base/'source_lock.json'
    lock = read(lock_path)
    c.require(admission['status'] == c.ADMISSION_STATUS and admission['registration_sha256'] == sha(registration_path) and
              admission['source_lock_sha256'] == sha(lock_path) and
              admission['actual_model_call_budget'] == denominators['actionable_requests'] and
              admission['gpu_job_name'] == protocol['gpu_job_name'] and
              admission['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and
              admission['activated_base_parameters'] == c.BASE_PARAMETERS and admission['optimizer_updates'] == 0 and
              lock['status'] == 'FROZEN_BASE_PAIRED_SOURCE_INPUT_CLOSURE' and
              lock['role'] == role and lock['source_root'] == str(SOURCE/role),
              'Main independent new BASE closure/GPU permission missing or changed')
    required = dict(bundle['required_metadata_files'])
    required.update(own_code_files())
    required.update({str(protocol_path): sha(protocol_path), str(official): sha(official)})
    if role == 'confirm':
        required[str(selection_path)] = sha(selection_path)
    c.require(all(lock['files'].get(path) == digest and registration['required_files'].get(path) == digest
                  for path, digest in required.items()), 'Required prior/source/input/native/availability/code/rule closure omitted')
    for path, digest in lock['files'].items():
        checked_ref(dict(path=path, sha256=digest), roots=ROOTS+(CODE,))
    bundle.update(base=base, registration=registration, protocol=protocol, admission=admission,
                  source=SOURCE/role, role=role, gpu_admission_sha256=sha(admission_path),
                  source_lock_sha256=sha(lock_path), registration_sha256=sha(registration_path))
    return bundle
