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
ROOT = MAIN/'relative_confirm'
PY = HOME/'env/qwen3vl_isolated_20260910/bin/python'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
REF = MAIN/'reference_code_v3'
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


def verify_deployment(state):
    archive = MAIN/'policy_and_prodCPU_control_07.zip'
    require(archive.stat().st_size == 116324 and sha(archive) == CONTROL07_SHA, 'Previously received control07 archive byte identity differs')
    verified = {}
    with zipfile.ZipFile(archive) as bundle:
        require(bundle.testzip() is None, 'Control07 CRC failed')
        manifest = json.loads(bundle.read('manifest.json'))
        require(set(bundle.namelist()) == set(manifest) | {'manifest.json'}, 'Control07 archive member denominator differs')
        for name, digest in manifest.items():
            require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and hashlib.sha256(bundle.read(name)).hexdigest() == digest, 'Unsafe or changed control07 member')
            if name.startswith(('reference_code_v3/', 'relative_confirm/')):
                require(sha(MAIN/name) == digest, 'Deployed reference/confirmation code differs from received control07')
                verified[str(MAIN/name)] = digest
    oldrank = read(MAIN/'relative_dev_03/registration.json')
    for path, digest in oldrank['code_files'].items():
        checked(dict(path=path, sha256=digest)); verified[path] = digest
    selected = read(MAIN/'policy_comparison_08_selection.json'); result = read(checked(selected['result_ref']))
    require(selected['protocol_ref'] == ref(MAIN/'policy_protocol_07.json') and selected['selected_policies'] ==
        ['ALL_WINDOW_WORST', 'PAIR_ONLY'] and selected['passed_arms'] == result['passed_arms'] ==
        dict(ALL_WINDOW_WORST=True, BUDGET_TWO_THIRDS=False, PAIR_ONLY=True)
        and selected['selected_predictions_genuinely_distinct'] is True and selected['confirm_metrics_examined'] is False,
        'Exact frozen passing two-policy selection required')
    save(state/'deployment_verification.json', dict(status='PASS_CONTROL07_BYTES_SHA_CRC_MEMBERS_AND_ACTUAL_DEPLOYED_FILES',
        archive_ref=ref(archive), files=verified, policy_selection_ref=ref(MAIN/'policy_comparison_08_selection.json'), utc=utc()))


def current_routes(state, candidates):
    import requests
    class NoCredentials(requests.auth.AuthBase):
        def __call__(self, request):
            return request
    routes = []
    for row in candidates['selection']+candidates['ordered_engineering_reserves']:
        url = row['provider']['video_url']
        response = requests.head(url, allow_redirects=True, timeout=(10, 45), auth=NoCredentials(), headers={'Accept-Encoding': 'identity'})
        history = [dict(status=value.status_code, url=value.url, location=value.headers.get('Location')) for value in response.history]
        for value in [*response.history, response]:
            location = urlparse(value.url)
            require(location.scheme == 'https' and location.username is None and location.password is None
                and (location.hostname == 'huggingface.co' or location.hostname.endswith('.cdn.hf.co')), 'HEAD escaped normal public publisher route')
        route = dict(video_id=row['video_id'], initial_public_url=url, metadata_only=True,
            bytes=row['provider']['size_bytes'], checked_utc=utc(), head_status=response.status_code, head_history=history)
        if response.status_code == 404:
            route['status'] = 'PUBLIC_OBJECT_404'
        else:
            location = urlparse(response.url)
            require(response.status_code == 200 and location.hostname.endswith('.cdn.hf.co')
                and int(response.headers['Content-Length']) == row['provider']['size_bytes'] and response.headers.get('ETag'),
                'Current HEAD version/bytes/ETag mismatch; stop without retry or replacement')
            route.update(status='PINNED_NORMAL_PUBLIC_REDIRECT', publisher_redirect_url=response.url, etag=response.headers['ETag'])
        routes.append(route)
        print(json.dumps(dict(stage='HEAD', source=row['video_id'], status=route['status'], bytes=route['bytes'])), flush=True)
    save(ROOT/'public_routes.json', dict(windows_video_body_bytes=0, requests_method='HEAD', routes=routes, utc=utc(),
        anonymous_no_credentials=True, no_retry=True, source_candidates_ref=ref(ROOT/'source_candidates.json')))


def register_media(candidates):
    required = {}
    def add(value):
        path = checked(value); required[str(path)] = value['sha256']
    helper = HOME/'recall_positive_admission_verify40_46_20261015_v1/fresh_01/media_code/positive_media.py'
    for path in list((ROOT/'media_code').glob('*.py'))+[ROOT/'source_candidates.json', ROOT/'public_routes.json',
        MAIN/'policy_protocol_07.json', MAIN/'policy_comparison_08_selection.json', MAIN/'policy_comparison_08.json',
        MAIN/'USER_AUTHORIZATION.json', helper, HOME/'videoxum_reference_iteration_20261013_v1/code/native_profile_01.py',
        HOME/'videoxum_reference_iteration_20261013_v1/code/native_profile_04.py']:
        add(ref(path))
    for key in ('id_export_ref', 'provider_prefix_ref', 'known_exclusions_ref', 'annotation_file_ref',
                'latest_ROLE_media_completion_ref', 'prior_ROLE_candidates_ref'):
        add(candidates[key])
    for value in candidates['prior22_media_receipts']+candidates['source_scope_refs']:
        add(value)
    require(candidates['maximum_pool_bytes'] == 81950179 and candidates['selected_media_bytes'] == 57088527, 'Exact approved new source payload changed')
    reg = dict(schema='MIDNIGHT_RELATIVE_FIRST_FRESH_MEDIA_REGISTRATION_V1', status='REGISTERED_MIDNIGHT_RELATIVE_FIRST_FRESH_MEDIA_NATIVE',
        group='confirm', expected_accepted_sources=4, maximum_media_pool_bytes=81950179, windows_video_body_bytes=0,
        production_admitted=False, protocol_ref=ref(MAIN/'policy_protocol_07.json'), authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
        development_selection_ref=ref(MAIN/'policy_comparison_08_selection.json'), source_candidates_ref=ref(ROOT/'source_candidates.json'),
        public_routes_ref=ref(ROOT/'public_routes.json'), media_helper_ref=ref(helper), required_files=required,
        registered_before_first_media_GET=True, registered_utc=utc())
    save(ROOT/'media_registration.json', reg)


def register_inputs(state):
    sys.path.insert(0, str(CODE)); import model_common as io
    from source_plan import source_document, unique_view_plan
    media = read(ROOT/'reference_01/completion.json')
    clocks = {row['video_id']: read(row['clock_path']) for row in media['accepted']}
    plan = unique_view_plan(source_document(media['accepted'], clocks, 'confirm'), 'confirm')
    require(plan['actual_input_count'] == 8 and all(view['view_roles'] == ['baseline'] for view in plan['unique_views']),
        'Actual new native clocks must yield eight original baseline-only windows; do not alter source/windows')
    old = read(HOME/'recall_adapter_role_verify40_46_20261015_v1/fresh_01/positive_fresh_registration.json')
    paths = set(io.runtime_dependencies()) | set(io.processor_assets()) | {str(io.CONFIG), str(io.RUNTIME)}
    paths.update(str(path) for path in CODE.glob('*.py'))
    paths.update(str(io.CV_CODE/name) for name in ('cv_contract.py', 'cv_tokens.py', 'cv_grammar.py'))
    paths.add(old['capacity_contract']['processor_source_path'])
    paths.update(read(ROOT/'media_registration.json')['required_files'])
    paths.update(str(path) for path in (ROOT/'media_registration.json', ROOT/'reference_01/completion.json'))
    for row in media['accepted']:
        paths.update((row['media']['path'], row['clock_path'], row['reference_path'], str(Path(row['media']['path']).parent/'media_receipt.json'), str(Path(row['media']['path']).parent/'route.json')))
    required = {str(Path(path).resolve()): sha(path) for path in paths}
    reg = dict(status='REGISTERED_MIDNIGHT_RELATIVE_FIRST_FRESH_INPUTS_V1', group='confirm', model_parameters=8782459120,
        optimizer_updates=0, source_scope='EXTERNAL_NONTEST_ONLY', reference_available_to_inference=False, production_admitted=False,
        protocol_ref=ref(MAIN/'policy_protocol_07.json'), authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
        dev_selection_ref=ref(MAIN/'policy_comparison_08_selection.json'), dev_result_ref=ref(MAIN/'policy_comparison_08.json'),
        source_registration_ref=ref(ROOT/'media_registration.json'), source_candidates_ref=ref(ROOT/'source_candidates.json'),
        reference_completion_ref=ref(ROOT/'reference_01/completion.json'), required_files=required, capacity_contract=old['capacity_contract'],
        deadline=DEADLINE, gpu_budget=dict(B0=dict(max_actual_calls=8, max_seconds=1200, gpu_job_name='midnight_relative_fresh4_b0_20261015_v1'),
        VERIFY=dict(max_actual_calls=40, max_seconds=1800, gpu_job_name='midnight_relative_fresh4_verify_20261015_v1')),
        registered_before_first_RGB_or_processor=True, registered_utc=utc())
    save(ROOT/'positive_fresh_registration.json', reg)
    save(state/'measured_baseline_plan.json', plan)
    return io, reg


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


def main():
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux' and Path(__file__).resolve() == ROOT/'control_09.py', 'Exact independent host/root/control required')
    state = ROOT/'control_09'; state.mkdir(exist_ok=False); stage = 'VERIFY_DEPLOYMENT'
    save(state/'started.json', dict(utc=utc(), pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split()[21],
        argv=Path('/proc/self/cmdline').read_bytes().decode().split('\0')[:-1], own_control_ref=ref(__file__), no_retry=True, parent_CUDA=os.environ.get('CUDA_VISIBLE_DEVICES')))
    try:
        snapshot(state, 'initial'); verify_deployment(state)
        stage = 'SELECT_NEW_SOURCES'
        child(state, stage, [PY, '-B', REF/'confirm_mapping.py', 'select', '--id-export', ROOT/'original_id_export.json',
            '--provider-prefix', ROOT/'provider_prefix.json', '--role-root', HOME/'recall_adapter_role_verify40_46_20261015_v1/fresh_01',
            '--protocol', MAIN/'policy_protocol_07.json', '--development-selection', MAIN/'policy_comparison_08_selection.json', '--output', ROOT/'source_candidates.json'])
        candidates = read(ROOT/'source_candidates.json'); stage = 'CURRENT_SIX_HEAD_ROUTES'; current_routes(state, candidates)
        register_media(candidates); stage = 'NEW_MEDIA_NATIVE'
        child(state, stage, [PY, '-B', ROOT/'media_code/confirm_media.py', '--root', ROOT])
        media = read(ROOT/'reference_01/completion.json'); require(len(media['accepted']) == 4, 'Complete new4 source stage required')
        print(json.dumps(dict(stage='NEW4_MEDIA_NATIVE_COMPLETE', actual_bytes=media['actual_new_media_payload_bytes'], source_names=[row['video_id'] for row in media['accepted']])), flush=True)
        io, reg = register_inputs(state)
        stage = 'PRIMARY_NATIVE64'; child(state, stage, [PY, '-B', CODE/'prepare_inputs.py', '--root', ROOT])
        stage = 'FIRST_NATIVE64_QA'; child(state, stage, [PY, '-B', CODE/'first_input_qa.py', '--root', ROOT])
        stage = 'B0'; run_gpu(state, io, reg, 'B0')
        stage = 'VERIFY_PREPARE'; child(state, stage, [PY, '-B', CODE/'pilot_verify.py', 'prepare', '--root', ROOT, '--group', 'confirm'])
        stage = 'VERIFY_FIRST_INPUT_QA'; child(state, stage, [PY, '-B', CODE/'verify_input_qa.py', '--root', ROOT])
        stage = 'VERIFY'; run_gpu(state, io, reg, 'VERIFY')
        stage = 'MAP_COMPLETED_NEW_BASELINE'
        child(state, stage, [PY, '-B', REF/'map_confirm_completed.py', '--root', ROOT, '--output', ROOT/'rank_mapping_01'])
        mapping = read(ROOT/'rank_mapping_01/inference_entries.json'); require(len(mapping['entries']) == 8, 'Exact planned eight classifier inputs required')
        rank_root = MAIN/'relative_confirm_rank_10'; rank_root.mkdir(exist_ok=False)
        oldreg = read(MAIN/'relative_dev_03/registration.json')
        rankreg = dict(oldreg, stage='relative_confirm_rank_10', requests_ref=ref(ROOT/'rank_mapping_01/inference_entries.json'),
            protocol_ref=ref(MAIN/'policy_protocol_07.json'), authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
            gpu_job_name='midnight_relative_fresh4_rank8_20261015_v1', max_GPU_seconds=900, deadline=DEADLINE,
            development_selection_ref=ref(MAIN/'policy_comparison_08_selection.json'), original_prompt_protocol_ref=ref(MAIN/'relative_protocol_03.json'),
            first_fresh_external_confirmation=True, production_admitted=False)
        save(rank_root/'registration.json', rankreg)
        snapshot(state, 'RANK_before_GPU'); stage = 'NEW_RELATIVE_RANK8'
        child(state, stage, [PY, '-B', MAIN/'relative_code_v1/controller.py', '--stage', 'relative_confirm_rank_10'], GPU_ENV)
        stage = 'FIRST_FRESH_FROZEN_POLICY_COMPARISON'
        child(state, stage, [PY, '-B', REF/'policy_evaluate.py', '--protocol', MAIN/'policy_protocol_07.json',
            '--manifest', ROOT/'rank_mapping_01/first_fresh_evaluation_manifest.json', '--decisions', rank_root/'completion.json',
            '--development-selection', MAIN/'policy_comparison_08_selection.json', '--output', ROOT/'policy_fresh_comparison.json'], allowed=(0, 5))
        comparison = read(ROOT/'policy_fresh_comparison.json')
        terminals = {}
        for name in ('midnight_relative_fresh4_b0_20261015_v1', 'midnight_relative_fresh4_verify_20261015_v1', 'midnight_relative_fresh4_rank8_20261015_v1'):
            path = RUN/'controller'/(name+'.resource.json'); terminal = read(path)
            require(terminal['status'] == 'completed' and terminal['exit_code'] == 0, 'All three new GPU jobs must complete naturally')
            ledger = [json.loads(line) for line in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
            require([row for row in ledger if row['name'] == name] == [terminal], 'Unique actual terminal ledger equality required')
            terminals[name] = dict(ref=ref(path), terminal=terminal)
        save(state/'completion.json', dict(status='NATURAL_COMPLETE_FIRST_FRESH_TWO_FROZEN_POLICIES', utc=utc(), comparison_ref=ref(ROOT/'policy_fresh_comparison.json'),
            passed_policies=comparison['passed_policies'], selected_policies=comparison['selected_policies'], full_source_count=comparison['full_source_count'],
            actual_media_payload_bytes=media['actual_new_media_payload_bytes'], B0_calls=read(ROOT/'confirm/B0/gpu_01/completion.json')['calls'],
            VERIFY_calls=read(ROOT/'confirm/VERIFY/gpu_01/completion.json')['calls'], rank_calls=read(rank_root/'completion.json')['actual_model_calls'],
            three_unique_GPU_terminals=terminals, old_successful_stages_repeated=0, production_admitted=False, official_improvement='UNKNOWN'))
        print(json.dumps(dict(status='COMPLETE', passed=comparison['passed_policies'], selected=comparison['selected_policies'])), flush=True)
    except BaseException as error:
        save(state/'failure.json', dict(status='FAILED_FIRST_REAL_STAGE_NO_RETRY', stage=stage, utc=utc(), error=repr(error),
            traceback=traceback.format_exc(), preserve_all_success=True, automatic_retry=False, production_admitted=False))
        print(json.dumps(dict(status='FAILED', stage=stage, error=repr(error))), flush=True)
        raise


if __name__ == '__main__':
    main()
