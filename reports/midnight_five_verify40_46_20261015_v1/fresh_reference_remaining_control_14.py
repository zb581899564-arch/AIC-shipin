"""Explicit remaining recovery after control09 failed before its first HEAD.

Six first successful current HEADs were performed on Windows as authorized.
Reuse the successful source selection; direct Linux GET/native/first CPU QA.
Production_unique_09 has strict GPU priority and must finish successfully.
"""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

HOME = Path('/home/inspur/aic_video_work')
MAIN = HOME/'midnight_five_verify40_46_20261015_v1'
ROOT = MAIN/'relative_confirm'
REF = MAIN/'reference_code_v3'
CODE = ROOT/'code'
PY = HOME/'env/qwen3vl_isolated_20260910/bin/python'
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PRODUCTION = MAIN/'production_unique_09'
JOB = 'midnight_three_semantic_recall_rank_aux518_20261015_v1'


def module():
    spec = importlib.util.spec_from_file_location('_frozen_failed_control09_helpers', ROOT/'control_09.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def wait_production(state, h):
    registration = h.read(PRODUCTION/'registration.json')
    h.require(registration['stage'] == 'production_unique_09' and registration['gpu_job_name'] == JOB, 'Exact main production dependency required')
    h.save(state/'production_dependency_waiting.json', dict(status='WAIT_MAIN_PRODUCTION_SUCCESS_BEFORE_ANY_FRESH_GPU',
        UTC=h.utc(), registration_ref=h.ref(PRODUCTION/'registration.json'), gpu_job_name=JOB,
        no_fresh_GPU_started=True, poll_is_background_readonly=True, frozen_new_call_deadline=h.DEADLINE))
    print(json.dumps(dict(stage='WAIT_PRODUCTION_UNIQUE_09', UTC=h.utc(), fresh_GPU_calls=0)), flush=True)
    resource_path = RUN/'controller'/(JOB+'.resource.json')
    while True:
        h.require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(h.DEADLINE.replace('Z', '+00:00')),
            'Frozen16Z deadline reached while waiting; no new fresh calls')
        for name in ('chain_failure.json', 'infer_failure.json', 'prepare_failure.json', 'output_qa_failure.json'):
            h.require(not (PRODUCTION/name).exists(), 'Main production real failure; stop new reference dependency: '+name)
        if resource_path.exists():
            terminal = h.read(resource_path)
            h.require(terminal['status'] == 'completed' and terminal['exit_code'] == 0, 'Main production GPU failed; no fresh launch')
            if (PRODUCTION/'chain_completion.json').exists():
                chain = h.read(PRODUCTION/'chain_completion.json'); complete = h.read(PRODUCTION/'completion.json')
                ledger = [json.loads(line) for line in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
                h.require(chain['status'] == 'NATURAL_COMPLETE_NEW_STAGE'
                    and complete['actual_model_calls'] == 518 and complete['first_input_QA_complete'] is True
                    and complete['first_output_QA_complete'] is True and [row for row in ledger if row['name'] == JOB] == [terminal],
                    'Entire actual main production first-QA/natural terminal and unique ledger required')
                h.save(state/'production_dependency_pass.json', dict(status='PASS_MAIN_PRODUCTION_NATURAL_AND_UNIQUE_LEDGER', UTC=h.utc(),
                    registration_ref=h.ref(PRODUCTION/'registration.json'), chain_completion_ref=h.ref(PRODUCTION/'chain_completion.json'),
                    output_completion_ref=h.ref(PRODUCTION/'completion.json'), terminal_ref=h.ref(resource_path)))
                print(json.dumps(dict(stage='MAIN_PRODUCTION_DEPENDENCY_PASS', UTC=h.utc())), flush=True)
                return
        time.sleep(15)


def main():
    h = module(); state = ROOT/'control_14'; state.mkdir(exist_ok=False); stage = 'BIND_EXPLICIT_REMAINING_RECOVERY'
    h.require(Path(__file__).resolve() == ROOT/'control_14.py', 'Exact new remaining controller required')
    h.save(state/'started.json', dict(UTC=h.utc(), pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split()[21],
        argv=Path('/proc/self/cmdline').read_bytes().decode().split('\0')[:-1], new_control_ref=h.ref(__file__),
        old_control_failure_ref=h.ref(ROOT/'control_09/failure.json'), old_successful_selection_ref=h.ref(ROOT/'source_candidates.json'),
        old_control_helpers_ref=h.ref(ROOT/'control_09.py'), current_windows_HEAD_routes_ref=h.ref(ROOT/'public_routes.json'),
        original_control_restarted=False, successful_source_selection_repeated=False, no_network_configuration_changes=True,
        parent_CUDA=os.environ.get('CUDA_VISIBLE_DEVICES')))
    try:
        failure = h.read(ROOT/'control_09/failure.json'); prior = h.read(ROOT/'control_09/deployment_verification.json')
        h.require(failure['stage'] == 'CURRENT_SIX_HEAD_ROUTES' and failure['status'] == 'FAILED_FIRST_REAL_STAGE_NO_RETRY'
            and not (ROOT/'reference_01').exists() and not (ROOT/'confirm').exists(), 'Only remaining first new media/input may run; never duplicate a successful stage')
        for path, digest in prior['files'].items():
            h.checked(dict(path=path, sha256=digest))
        routes = h.read(ROOT/'public_routes.json'); candidates = h.read(ROOT/'source_candidates.json')
        h.require(routes['source_candidates_ref'] == h.ref(ROOT/'source_candidates.json')
            and routes['prior_failed_control_ref'] == h.ref(ROOT/'control_09/failure.json')
            and routes['windows_video_body_bytes'] == 0 and len(routes['routes']) == 6
            and routes['actual_HTTP_retries'] == 0 and routes['network_configuration_changes'] == 0,
            'Actual current six anonymous metadata-only Windows HEADs must bind the exact existing selection and original failure')
        h.snapshot(state, 'initial_with_production_priority')
        h.register_media(candidates); stage = 'NEW_MEDIA_NATIVE_DIRECT_CDN'
        h.child(state, stage, [PY, '-B', ROOT/'media_code/confirm_media.py', '--root', ROOT])
        media = h.read(ROOT/'reference_01/completion.json'); h.require(len(media['accepted']) == 4, 'All new4 media/native sources required')
        print(json.dumps(dict(stage='NEW4_MEDIA_NATIVE_COMPLETE', actual_bytes=media['actual_new_media_payload_bytes'],
            source_names=[row['video_id'] for row in media['accepted']], UTC=h.utc())), flush=True)
        io, reg = h.register_inputs(state)
        stage = 'PRIMARY_NATIVE64'; h.child(state, stage, [PY, '-B', CODE/'prepare_inputs.py', '--root', ROOT])
        stage = 'FIRST_NATIVE64_QA'; h.child(state, stage, [PY, '-B', CODE/'first_input_qa.py', '--root', ROOT])
        stage = 'WAIT_MAIN_PRODUCTION_SUCCESS'; wait_production(state, h)
        stage = 'B0'; h.run_gpu(state, io, reg, 'B0')
        stage = 'VERIFY_PREPARE'; h.child(state, stage, [PY, '-B', CODE/'pilot_verify.py', 'prepare', '--root', ROOT, '--group', 'confirm'])
        stage = 'VERIFY_FIRST_INPUT_QA'; h.child(state, stage, [PY, '-B', CODE/'verify_input_qa.py', '--root', ROOT])
        stage = 'VERIFY'; h.run_gpu(state, io, reg, 'VERIFY')
        stage = 'MAP_COMPLETED_NEW_BASELINE'
        h.child(state, stage, [PY, '-B', REF/'map_confirm_completed.py', '--root', ROOT, '--output', ROOT/'rank_mapping_01'])
        mapping = h.read(ROOT/'rank_mapping_01/inference_entries.json'); h.require(len(mapping['entries']) == 8, 'Exactly planned8 new classifier views required')
        rank_root = MAIN/'relative_confirm_rank_10'; rank_root.mkdir(exist_ok=False)
        original = h.read(MAIN/'relative_dev_03/registration.json')
        rankreg = dict(original, stage='relative_confirm_rank_10', requests_ref=h.ref(ROOT/'rank_mapping_01/inference_entries.json'),
            protocol_ref=h.ref(MAIN/'policy_protocol_07.json'), authorization_ref=h.ref(MAIN/'USER_AUTHORIZATION.json'),
            gpu_job_name='midnight_relative_fresh4_rank8_20261015_v1', max_GPU_seconds=900, deadline=h.DEADLINE,
            development_selection_ref=h.ref(MAIN/'policy_comparison_08_selection.json'), original_prompt_protocol_ref=h.ref(MAIN/'relative_protocol_03.json'),
            first_fresh_external_confirmation=True, production_admitted=False)
        h.save(rank_root/'registration.json', rankreg); h.snapshot(state, 'RANK_before_GPU'); stage = 'NEW_RELATIVE_RANK8'
        h.child(state, stage, [PY, '-B', MAIN/'relative_code_v1/controller.py', '--stage', 'relative_confirm_rank_10'], h.GPU_ENV)
        stage = 'FIRST_FRESH_FROZEN_POLICY_COMPARISON'
        h.child(state, stage, [PY, '-B', REF/'policy_evaluate.py', '--protocol', MAIN/'policy_protocol_07.json',
            '--manifest', ROOT/'rank_mapping_01/first_fresh_evaluation_manifest.json', '--decisions', rank_root/'completion.json',
            '--development-selection', MAIN/'policy_comparison_08_selection.json', '--output', ROOT/'policy_fresh_comparison.json'], allowed=(0, 5))
        comparison = h.read(ROOT/'policy_fresh_comparison.json'); terminals = {}
        for name in ('midnight_relative_fresh4_b0_20261015_v1', 'midnight_relative_fresh4_verify_20261015_v1', 'midnight_relative_fresh4_rank8_20261015_v1'):
            path = RUN/'controller'/(name+'.resource.json'); terminal = h.read(path)
            ledger = [json.loads(line) for line in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
            h.require(terminal['status'] == 'completed' and terminal['exit_code'] == 0 and [row for row in ledger if row['name'] == name] == [terminal],
                'All actual new GPU jobs must naturally complete with unique exact ledger terminal')
            terminals[name] = dict(ref=h.ref(path), terminal=terminal)
        h.save(state/'completion.json', dict(status='NATURAL_COMPLETE_FIRST_FRESH_TWO_FROZEN_POLICIES', UTC=h.utc(),
            comparison_ref=h.ref(ROOT/'policy_fresh_comparison.json'), passed_policies=comparison['passed_policies'],
            selected_policies=comparison['selected_policies'], full_source_count=comparison['full_source_count'],
            actual_media_payload_bytes=media['actual_new_media_payload_bytes'], B0_calls=h.read(ROOT/'confirm/B0/gpu_01/completion.json')['calls'],
            VERIFY_calls=h.read(ROOT/'confirm/VERIFY/gpu_01/completion.json')['calls'], rank_calls=h.read(rank_root/'completion.json')['actual_model_calls'],
            three_unique_GPU_terminals=terminals, original_control09_failure_preserved=True, successful_selection_repeated=False,
            production_dependency_ref=h.ref(state/'production_dependency_pass.json'), old_successful_stages_repeated=0,
            production_admitted=False, quality_admission_owned_by_main=True, official_improvement='UNKNOWN'))
        print(json.dumps(dict(status='COMPLETE', passed=comparison['passed_policies'], selected=comparison['selected_policies'], UTC=h.utc())), flush=True)
    except BaseException as error:
        h.save(state/'failure.json', dict(status='FAILED_EXPLICIT_REMAINING_STAGE_NO_RETRY', stage=stage, UTC=h.utc(),
            error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True, automatic_retry=False, production_admitted=False))
        print(json.dumps(dict(status='FAILED', stage=stage, error=repr(error))), flush=True)
        raise


if __name__ == '__main__':
    main()
