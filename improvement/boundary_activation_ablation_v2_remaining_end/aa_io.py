"""Immutable old smoke evidence and new activation-only metadata admission."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from aa_contract import SCHEMA, MAX_CALLS, REQUEST_IDS, SOURCE_TIME_CALLS, SOURCE_REQUEST_IDS, protocol, require

HOME = Path('/home/inspur/aic_video_work')
BASE = HOME/'twenty_hour_five_20261014_v1/boundary_activation_ablation_v2_remaining_end'
PREVIOUS = HOME/'twenty_hour_five_20261014_v1/boundary_activation_ablation_v1'
SOURCE = HOME/'twenty_hour_five_20261014_v1/local_boundary_v2'
CODE = SOURCE/'code'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
LEGACY = HOME/'temporal_refinement_pilot_20261011/dev_01'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


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


def host(cpu):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux', 'Only verified Linux host may execute')
    visibility = os.environ.get('CUDA_VISIBLE_DEVICES')
    require(visibility == '' if cpu else isinstance(visibility,str) and bool(visibility),
            'CPU child must hide CUDA; GPU child/parent must retain explicit nonempty visibility')


def root(path):
    require(Path(path).resolve() == BASE.resolve(), 'New independent activation root required')
    return BASE


def code_files():
    return {str(path.resolve()):sha(path) for path in sorted(Path(__file__).parent.glob('*.py'))}


def bound(path, digest, files, roots=(SOURCE,)):
    path = Path(path).resolve()
    require(any(path.is_relative_to(Path(folder).resolve()) for folder in roots), 'Artifact escaped its explicit evidence roots')
    require(path.is_file() and sha(path) == digest, 'Frozen evidence changed: '+str(path))
    files[str(path)] = digest
    return path


def source_rows(registration):
    """No media/NPZ read or input processor replay; old replay proves pixels."""
    files = {}
    paths = {name:SOURCE/relative for name, relative in dict(cpu='cpu_01/completion.json',
        plan='plan_01/completion.json', gpu='gpu_01/completion.json', identity='gpu_01/model_identity.json',
        replay='replay_01/completion.json', admission='gpu_admission.json').items()}
    for name in ('cpu','gpu','identity','replay'):
        bound(paths[name], registration['prior_'+name+'_completion_sha256'] if name != 'identity' else
              registration['prior_model_identity_sha256'], files)
    for name in ('plan','admission'):
        files[str(paths[name])] = sha(paths[name])
    cpu, plan, gpu, model, replay, admission = [read(paths[name]) for name in ('cpu','plan','gpu','identity','replay','admission')]
    require(cpu['status'] == 'PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION' and
        cpu['requests'] == SOURCE_TIME_CALLS and cpu['events'] == 1 and cpu['CPU_only'] is True and
        cpu['CUDA_initialized'] is False and cpu['new_model_calls'] == 0 and
        gpu['status'] == 'PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY' and gpu['actual_model_calls'] == SOURCE_TIME_CALLS and
        gpu['requests'] == SOURCE_TIME_CALLS and replay['status'] == 'PASS_ALL_NEW_LOCAL_BOUNDARY_INDEPENDENT_REPLAYS_NOT_QUALITY' and
        replay['requests'] == SOURCE_TIME_CALLS and replay['CPU_only'] is True and replay['CUDA_initialized'] is False and
        replay['new_model_calls'] == 0 and replay['gpu_completion_sha256'] == sha(paths['gpu']) and
        gpu['model_identity_sha256'] == sha(paths['identity']) and gpu['gpu_admission_sha256'] == sha(paths['admission']) and
        admission['cpu_completion_sha256'] == sha(paths['cpu']), 'Complete original two-call CPU/GPU/input-replay chain required')
    require(registration['expected_source_code_files'] == cpu['bindings']['own_code_files'], 'Original revision03 code lock differs')
    for path, digest in cpu['bindings']['own_code_files'].items():
        bound(path, digest, files, roots=(CODE,))
    original_registration = bound(plan['registration_path'], plan['registration_sha256'], files)
    require(read(original_registration)['validation_scope'] == 'ONE_EVENT_INTERFACE_SMOKE' and
            cpu['bindings']['registration_sha256'] == sha(original_registration) and
            cpu['bindings']['plan_completion_sha256'] == sha(paths['plan']), 'Original smoke scope/input registration changed')
    helpers = old_helpers(cpu['bindings']['own_code_files'])
    helpers['io'].verify_model(type('IdentityOnly', (), {'active_adapter':'default'})(), model['identity'])
    resource, digest = helpers['io'].terminal_resource(admission['gpu_job_name'])
    require(replay['resource_terminal_sha256'] == digest, 'Original completed GPU resource/replay/ledger binding differs')
    resourcepath = RUN/'controller'/(admission['gpu_job_name']+'.resource.json')
    files[str(resourcepath)] = digest
    attempts = bound(SOURCE/'gpu_01/attempts.jsonl', gpu['attempts_sha256'], files)
    journal = [json.loads(line) for line in attempts.read_text().splitlines() if line.strip()]
    require(len(journal) == 2*SOURCE_TIME_CALLS and len(gpu['entries']) == SOURCE_TIME_CALLS and
            tuple(entry['request_id'] for entry in cpu['proofs']) == SOURCE_REQUEST_IDS and
            registration['request_ids'] == list(REQUEST_IDS), 'Fixed two-call identity/order denominator changed')
    by_done = {entry['request_id']:entry for entry in gpu['entries']}
    by_replay = {entry['request_id']:entry for entry in replay['proofs']}
    rows = []
    for index, entry in enumerate(cpu['proofs'],1):
        rid = entry['request_id']
        require(journal[2*(index-1)]['event'] == 'BEGIN_MODEL_CALL' and journal[2*(index-1)+1]['event'] == 'ACCEPTED_MODEL_CALL' and
                all(journal[i]['request_id'] == rid and journal[i]['call_id'] == index for i in (2*(index-1),2*(index-1)+1)),
                'Original unique TIME model journal changed')
        proofpath = bound(entry['proof_path'], entry['proof_sha256'], files)
        proof = read(proofpath)
        metapath = bound(proof['input_path'], proof['input_sha256'], files)
        meta = read(metapath)
        bound(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'], files)
        donepath = bound(by_done[rid]['done_path'], by_done[rid]['done_sha256'], files)
        olddone = read(donepath)
        rawpath = bound(SOURCE/'gpu_01'/rid/'raw.json', olddone['raw_sha256'], files)
        requestpath = bound(SOURCE/'gpu_01'/rid/'request.json', olddone['request_sha256'], files)
        raw, request = read(rawpath), read(requestpath)
        transferpath = SOURCE/'gpu_01'/rid/'gpu_input.json'
        files[str(transferpath)] = sha(transferpath)
        transfer = read(transferpath)
        replaypath = bound(by_replay[rid]['proof_path'], by_replay[rid]['proof_sha256'], files)
        oldreplay = read(replaypath)
        require(journal[2*(index-1)+1]['done_path'] == str(donepath) and
                journal[2*(index-1)+1]['done_sha256'] == sha(donepath), 'Original accepted journal/done identity differs')
        require(proof['status'] == 'PASS_CPU_LOCAL_BOUNDARY_NATIVE64_PROCESSOR_INPUT' and proof['CPU_only'] is True and
            proof['CUDA_initialized'] is False and proof['new_model_calls'] == 0 and
            proof['bindings'] == meta['bindings'] == cpu['bindings'] and
            entry['input_path'] == proof['input_path'] and entry['input_sha256'] == proof['input_sha256'] and
            proof['request_id'] == meta['request_id'] == olddone['request_id'] == request['request_id'] == rid and
            meta['side'] == entry['side'] == olddone['side'] and meta['reference_available_to_inference'] is False and
            meta['audio_observed'] is False and request['reference_labels_read'] is False and raw['actual_model_call'] is True and
            proof['encoded_tensor_format'] == helpers['io'].TENSOR_CACHE_FORMAT and
            proof['encoded_tensor_compression_level'] == 1 and request['encoded_tensor_format'] == proof['encoded_tensor_format'] and
            request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
            request['input_sha256'] == proof['input_sha256'] and request['CPU_proof_sha256'] == entry['proof_sha256'] and
            request['prompt'] == meta['prompt'] == helpers['contract'].prompt(meta) and
            request['finite_response_strings'] == list(helpers['contract'].response_strings(meta)) and
            olddone['status'] == 'PASS_LOCAL_BOUNDARY_DECISION_NOT_QUALITY' and
            json.dumps(olddone['decision'],separators=(',',':')) == raw['raw_output'] and
            oldreplay['status'] == 'PASS_INDEPENDENT_CPU_BOUNDARY_TENSOR_TOKEN_NATIVE_REPLAY' and
            oldreplay['CPU_only'] is True and oldreplay['new_model_calls'] == 0 and oldreplay['request_id'] == rid and
            oldreplay['done_sha256'] == sha(donepath) and oldreplay['raw_sha256'] == sha(rawpath) and
            oldreplay['endpoint_result'] == olddone['endpoint_result'] and
            proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == olddone['input_evidence'] == oldreplay['input_evidence'] and
            transfer['status'] == 'PASS_ACCEPTED_CPU_GPU_TENSOR_EQUALITY' and
            transfer['tensor_signature'] == proof['input_evidence']['tensor_signature'] and
            transfer['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
            proof['input_evidence']['physical_frames'] == 64 and 0 < proof['input_tokens'] <= 16384,
            'Original exact prompt/grammar/cache/TIME output/prior successful input replay differs')
        require(proof['input_tokens'] == entry['input_tokens'] == raw['input_tokens'] == olddone['input_tokens'] and
                len(meta['source_frame_ordinals']) == len(set(meta['source_frame_ordinals'])) == 64,
                'Original native64/input-token denominator differs')
        for name, ref in meta['original_evidence'].items():
            # These are clock/JSON proof refs, never source video or NPZ pixels.
            bound(ref['path'], ref['sha256'], files, roots=helpers['io'].EXTERNAL_ROOTS)
        rows.append((entry,proof,meta,olddone,oldreplay))
    for path,digest in cpu['bindings']['original_b_processor_runtime']['runtime_files'].items():
        bound(path,digest,files,roots=(LEGACY,RUN))
    for path,digest in cpu['bindings']['original_b_processor_runtime']['processor_assets'].items():
        bound(path,digest,files,roots=(RUN,))
    configpath = RUN/'b_score_aligned_package_v4/config.json'
    bound(configpath,cpu['bindings']['original_b_processor_runtime']['original_config_sha256'],files,roots=(RUN,))
    # Bind the complete old source lock dictionary via its immutable admission
    # bytes. No successful source media/RGB input replay is repeated here.
    return cpu, [row for row in rows if row[0]['request_id'] in REQUEST_IDS], files, dict(prior_gpu_job_name=admission['gpu_job_name'], prior_gpu_resource=resource,
        inherited_original_source_input_lock_files=admission['source_input_lock_files'],
        original_model_identity=model['identity'], prior_input_replays_reused=True)


def old_helpers(expected):
    for path,digest in expected.items():
        require(Path(path).resolve().parent == CODE.resolve() and sha(path) == digest, 'Frozen v2 helper code changed')
    sys.path.insert(0,str(CODE))
    modules = {}
    for label,name in [('contract','lb_contract'),('io','lb_io'),('grammar','lb_grammar'),('replay','replay_local_boundaries')]:
        if name in sys.modules:
            require(Path(sys.modules[name].__file__).resolve() == (CODE/(name+'.py')).resolve(), 'Frozen helper was shadowed')
            module = sys.modules[name]
        else:
            spec = importlib.util.spec_from_file_location(name,CODE/(name+'.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        modules[label] = module
    return modules


def prior_failure_recovery(value,files):
    """Bind failed v1 and its already-generated START without accepting it."""
    require(value['schema'] == SCHEMA and value['original_failure_root'] == str(PREVIOUS) and
            value['prior_start_status'] == 'UNACCEPTED_POST_STATE_PROOF' and
            value['remaining_request_ids'] == list(REQUEST_IDS) and value['remaining_model_call_budget'] == 1 and
            value['old_failed_status_preserved'] is True and value['no_repeat_started_start_call'] is True,
            'Explicit failed-v1/remaining-END recovery declaration required')
    folder = PREVIOUS/'gpu_01'/SOURCE_REQUEST_IDS[0]
    artifacts = {'failure':PREVIOUS/'gpu_01/failure.json','raw':folder/'raw.json',
        'request':folder/'request.json','gpu_input':folder/'gpu_input.json',
        'activation_before':folder/'activation_before.json','activation_disabled':folder/'activation_disabled.json',
        'model_identity':PREVIOUS/'gpu_01/model_identity.json','attempts':PREVIOUS/'gpu_01/attempts.jsonl',
        'source_lock':PREVIOUS/'source_lock.json','admission':PREVIOUS/'admission.json',
        'gpu_admission':PREVIOUS/'gpu_admission.json','protocol':PREVIOUS/'protocol.json','registration':PREVIOUS/'registration.json'}
    for name,path in artifacts.items():
        bound(path,value['prior_artifact_sha256'][name],files,roots=(PREVIOUS,))
    failure,raw,request = [read(artifacts[name]) for name in ('failure','raw','request')]
    require(failure['status'] == 'FAILED_ACTIVATION_KEEP_RAW_AND_SUCCESS_NO_UNKNOWN_FALLBACK' and
            failure['actual_started_model_calls'] == 1 and failure['successful_entries'] == [] and
            failure['request_id'] == SOURCE_REQUEST_IDS[0] and
            'trained B adapter disabled or a parameter trainable' in failure['error'] and
            raw['actual_model_call'] is True and request['request_id'] == SOURCE_REQUEST_IDS[0] and
            not (folder/'done.json').exists() and not (folder/'activation_after.json').exists() and
            not (PREVIOUS/'gpu_01/completion.json').exists(),
            'Prior START is generated but post-state proof remains unaccepted; no acceptance fabrication')
    journal = [json.loads(line) for line in artifacts['attempts'].read_text().splitlines() if line.strip()]
    require(len(journal) == 1 and journal[0]['event'] == 'BEGIN_MODEL_CALL' and
            journal[0]['request_id'] == SOURCE_REQUEST_IDS[0] and journal[0]['call_id'] == 1,
            'Prior v1 only started START once; END must never have begun')
    oldp = read(artifacts['protocol'])
    resourcepath = RUN/'controller'/(oldp['gpu_job_name']+'.resource.json')
    bound(resourcepath,value['prior_gpu_resource_sha256'],files,roots=(RUN,))
    resource = read(resourcepath)
    ledger = [json.loads(line) for line in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    require(resource['name'] == oldp['gpu_job_name'] and resource['status'] == 'failed' and resource['exit_code'] == 1 and
            [row for row in ledger if row['name'] == resource['name']] == [resource] and
            value['preserve_prior_charged_seconds'] == resource['charged_seconds'],
            'Failed v1 unique ledger/fee/status must remain unchanged')
    return dict(prior_gpu_job_name=resource['name'],prior_gpu_resource=resource,
        prior_gpu_resource_sha256=value['prior_gpu_resource_sha256'],
        prior_start_raw_sha256=value['prior_artifact_sha256']['raw'],prior_start_status='UNACCEPTED_POST_STATE_PROOF',
        old_failed_status_preserved=True,no_repeat_started_start_call=True,
        prior_started_calls=1,prior_accepted_calls=0,remaining_request_ids=list(REQUEST_IDS))


def admitted(rootpath):
    root(rootpath)
    registration, p = read(BASE/'registration.json'), read(BASE/'protocol.json')
    protocol(p,SOURCE)
    require(registration['schema'] == SCHEMA and registration['status'] == 'FROZEN_ONLY_REMAINING_END_AFTER_V1_STARTED_START_FAILURE' and
        registration['source_root'] == str(SOURCE) and registration['protocol_sha256'] == sha(BASE/'protocol.json') and
        registration['code_files'] == code_files(), 'Main-agent frozen new protocol/code/source registration required')
    rulepath = bound(registration['official_rule_check_path'],registration['official_rule_check_sha256'],{},roots=(BASE,))
    cpu, rows, files, prior = source_rows(registration)
    recoverypath = BASE/'remaining_recovery.json'
    bound(recoverypath,registration['remaining_recovery_sha256'],files,roots=(BASE,))
    recovery = prior_failure_recovery(read(recoverypath),files)
    prior['v1_failed_recovery'] = recovery
    require(len(rows) == MAX_CALLS and tuple(row[0]['request_id'] for row in rows) == REQUEST_IDS,
            'Only the never-started original end may enter new inference')
    require(p['gpu_job_name'] != recovery['prior_gpu_job_name'],'New recovery cannot reuse the failed v1 GPU job name')
    require(p['gpu_job_name'] != prior['prior_gpu_job_name'], 'New activation job cannot reuse the successful TIME job name')
    files.update(code_files())
    for path in (BASE/'registration.json',BASE/'protocol.json',rulepath):
        files[str(path)] = sha(path)
    return p, registration, cpu, rows, files, prior


def admit(rootpath):
    host(cpu=True)
    p,registration,cpu,rows,files,prior = admitted(rootpath)
    require(not (BASE/'source_lock.json').exists() and not (BASE/'admission.json').exists(), 'Already admitted; do not repeat')
    save(BASE/'source_lock.json',dict(files=files,prior=prior,request_ids=list(REQUEST_IDS),
        new_model_calls=0,new_input_processor_encodes=0,new_media_decodes=0,quality_gate_admitted=False))
    save(BASE/'admission.json',dict(status='PASS_REMAINING_END_INPUT_REUSE_NOT_GPU_PERMISSION_OR_QUALITY',
        source_lock_sha256=sha(BASE/'source_lock.json'),requests=MAX_CALLS,gpu_job_name=p['gpu_job_name'],
        prior_cpu_input_replays_reused=True,new_model_calls=0,new_input_processor_encodes=0,new_media_decodes=0,utc=utc()))


def verify_lock(rootpath):
    root(rootpath)
    admission, lock = read(BASE/'admission.json'), read(BASE/'source_lock.json')
    require(admission['status'] == 'PASS_REMAINING_END_INPUT_REUSE_NOT_GPU_PERMISSION_OR_QUALITY' and
            admission['source_lock_sha256'] == sha(BASE/'source_lock.json'), 'New activation input admission changed')
    for path,digest in lock['files'].items():
        require(sha(path) == digest,'Frozen paired input/runtime/code evidence changed: '+path)
    p,registration,cpu,rows,files,prior = admitted(rootpath)
    require(files == lock['files'] and prior == lock['prior'] and admission['gpu_job_name'] == p['gpu_job_name'],
            'Complete paired activation evidence denominator changed')
    return admission,p,cpu,rows,prior
