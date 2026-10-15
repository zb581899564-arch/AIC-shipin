"""First BASE37 registration and independent metadata-only consumer admission."""
import argparse
import os
from pathlib import Path
import sys
import traceback

import cc_common as cc


def register(scope_path):
    cc.host(cpu=True)
    scope_path, scope = cc.scope(scope_path)
    cc.check_deadline(scope)
    cc.unique_job_absent()
    terminal = cc.time_terminal()
    cc.require(terminal is not None, 'Registration waits for the already running TIME natural chain terminal')
    c, io = cc.driver_modules()
    bundle = io.source_bundle(cc.TIME, 'dev')
    cc.require(bundle['denominators'] == cc.COUNTS and len(bundle['events']) == 20 and len(bundle['rows']) == 37,
               'Unchanged20 events/40 endpoints/37 accepted inputs and3 typed skips required')
    for name in ('registration_01.json', 'protocol.json', 'official_rule_check.json', 'source_lock.json', 'gpu_admission.json'):
        cc.require(not (cc.BASE/name).exists(), 'A prior partial registration cannot be silently retried: '+name)
    out = cc.BASE/'registration_stage_01'
    out.mkdir(exist_ok=False)
    cc.save(out/'launch_claim.json', dict(pid=os.getpid(), argv=sys.argv, utc=cc.utc(), CPU_only=True,
        TIME_chain_completion=terminal, new_model_calls=0, new_processor_encodes=0, new_media_decodes=0))
    try:
        cc.save(out/'resource_before_registration.json', cc.resource_snapshot())
        source_rule = cc.ref(scope['official_rule_check_ref'], roots=(cc.TIME,))
        rule_path = cc.BASE/'official_rule_check.json'
        with rule_path.open('xb') as stream:
            stream.write(source_rule.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        cc.require(cc.sha(rule_path) == scope['official_rule_check_ref']['sha256'], 'Exact existing current-rule copy changed')
        protocol_path = cc.BASE/'protocol.json'
        protocol = dict(schema=c.SCHEMA, role='dev', source_root=str(cc.TIME),
            hypothesis='SAME_INPUT_LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION', events=20,
            actual_model_call_budget=37, **cc.COUNTS, actual_physical_parameters=c.PHYSICAL_PARAMETERS,
            activated_base_parameters=c.BASE_PARAMETERS, disable_time_adapter_layers=144, optimizer_updates=0,
            new_input_processor_encodes=0, new_media_decodes=0, prior_TIME_completed_and_first_input_replay_required=True,
            same_prompt_grammar_native_conversion=True, independent_prefill_per_call=True,
            weight_check_strategy=c.WEIGHT_CHECK_STRATEGY, quality_claim_or_selection_by_this_driver=False,
            gpu_job_name=cc.NAME, deadline=scope['deadline'], max_gpu_seconds=cc.MAX_GPU_SECONDS,
            planned_output_bytes=cc.PLANNED_OUTPUT_BYTES, TIME_chain_completion=terminal,
            actual_deadline_ref=scope['deadline_ref'], controller_scope_ref=dict(path=str(scope_path), sha256=cc.sha(scope_path)),
            confirmation_metrics_sealed_until_development_selection_frozen=True, source_semantics='AUTHOR_ACTION_ENDPOINT_PROXY_NOT_HIGHLIGHT_GT',
            current_known_identity_scope_only=True, pretraining_overlap='UNKNOWN', created_utc=cc.utc())
        c.protocol(protocol, 'dev', cc.TIME, cc.COUNTS)
        cc.save(protocol_path, protocol)
        required = dict(bundle['required_metadata_files'])
        required.update(io.own_code_files())
        required.update(cc.own_code_files())
        required.update({str(protocol_path): cc.sha(protocol_path), str(rule_path): cc.sha(rule_path),
                         str(scope_path): cc.sha(scope_path), terminal['path']: terminal['sha256'],
                         scope['deadline_ref']['path']: scope['deadline_ref']['sha256'],
                         scope['TIME_controller_launch_ref']['path']: scope['TIME_controller_launch_ref']['sha256']})
        wrapper = cc.RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        required[str(wrapper)] = cc.sha(wrapper)
        # Existing byte signatures are quoted from already accepted CPU/input
        # replay. Stat can establish that referenced files still exist and fit;
        # no tensor/RGB load, processor or media decode is repeated here.
        binary_refs = []
        for entry, proof, meta, old_done, old_replay in bundle['rows']:
            tensor = Path(proof['encoded_tensor_path']).resolve()
            rgb = Path(meta['frame_array_path']).resolve()
            cc.require(tensor.is_relative_to(cc.TIME) and rgb.is_relative_to(cc.TIME) and
                       tensor.stat().st_size == proof['encoded_tensor_file_bytes'] and
                       rgb.stat().st_size == proof['rgb_npz_file_bytes'], 'Original cache/RGB reference size/path changed')
            binary_refs.append(dict(request_id=entry['request_id'], input_tokens=proof['input_tokens'],
                tensor_path=str(tensor), tensor_sha256=proof['encoded_tensor_sha256'], tensor_bytes=tensor.stat().st_size,
                tensor_format=proof['encoded_tensor_format'], RGB_path=str(rgb), RGB_sha256=meta['frame_array_sha256'],
                RGB_bytes=rgb.stat().st_size, prior_first_input_replay_path=str(cc.TIME/'replay_01'/(entry['request_id']+'.json')),
                prior_first_input_replay_sha256=cc.sha(cc.TIME/'replay_01'/(entry['request_id']+'.json')),
                independent_input_replay_reused=True, repeated_binary_read_or_encoder=False))
        reference_path = out/'accepted_binary_references.json'
        cc.save(reference_path, dict(status='BOUND_ORIGINAL_INPUT_BYTES_AND_FIRST_INPUT_REPLAYS_WITHOUT_REENCODING',
            entries=binary_refs, requests=37, new_binary_hash_pass=False, new_tensor_loads=0,
            new_RGB_reads=0, new_processor_encodes=0, new_media_decodes=0, new_model_calls=0))
        required[str(reference_path)] = cc.sha(reference_path)
        registration = dict(schema=c.SCHEMA, status=c.REGISTRATION_STATUS, role='dev', source_root=str(cc.TIME),
            events=20, actual_model_call_budget=37, **cc.COUNTS,
            actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS,
            optimizer_updates=0, own_code_files=io.own_code_files(), required_files=required,
            protocol_path=str(protocol_path), protocol_sha256=cc.sha(protocol_path),
            official_rule_check_path=str(rule_path), official_rule_check_sha256=cc.sha(rule_path),
            old_successful_TIME_and_input_replays_reused=True, no_GT_read_or_source_selection=True,
            original_structural_geometry_reused=True, registered_before_new_BASE_calls=True, created_utc=cc.utc())
        cc.save(cc.BASE/'registration_01.json', registration)
        cc.save(cc.BASE/'source_lock.json', dict(status='FROZEN_BASE_PAIRED_SOURCE_INPUT_CLOSURE', role='dev',
            source_root=str(cc.TIME), files=required, accepted_binary_reference_sha256=cc.sha(reference_path),
            input_bytes_reused_from_TIME_first_independent_proofs=True, created_utc=cc.utc()))
        admission = dict(status=c.ADMISSION_STATUS, registration_sha256=cc.sha(cc.BASE/'registration_01.json'),
            source_lock_sha256=cc.sha(cc.BASE/'source_lock.json'), actual_model_call_budget=37,
            gpu_job_name=cc.NAME, actual_physical_parameters=c.PHYSICAL_PARAMETERS,
            activated_base_parameters=c.BASE_PARAMETERS, optimizer_updates=0, deadline=scope['deadline'],
            TIME_chain_completion=terminal, **cc.COUNTS, new_input_processor_encodes=0, new_media_decodes=0,
            accepted_binary_reference_sha256=cc.sha(reference_path), independent_consumer_check_still_required=True, created_utc=cc.utc())
        cc.save(cc.BASE/'gpu_admission.json', admission)
        cc.save(out/'completion.json', dict(status='FIRST_BASE37_REGISTRATION_AND_METADATA_ADMISSION_CREATED_NOT_GPU_LAUNCHED',
            registration_sha256=cc.sha(cc.BASE/'registration_01.json'), gpu_admission_sha256=cc.sha(cc.BASE/'gpu_admission.json'),
            new_model_calls=0, new_processor_encodes=0, new_media_decodes=0, utc=cc.utc()))
    except BaseException as error:
        cc.save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            preserve_all_partial_and_success=True, no_automatic_retry=True, utc=cc.utc()))
        raise


def check(scope_path):
    cc.host(cpu=True)
    scope_path, scope = cc.scope(scope_path)
    cc.check_deadline(scope)
    cc.unique_job_absent()
    c, io = cc.driver_modules()
    # Separate process invokes the immutable consuming driver's gate. It reads
    # metadata, not old tensors/RGB and never repeats an input processor call.
    bundle = io.admitted(cc.BASE)
    cc.require(bundle['denominators'] == cc.COUNTS and len(bundle['rows']) == 37 and len(bundle['events']) == 20,
               'Independent new-driver consumer did not accept exact37/20 input references')
    cc.save(cc.BASE/'gpu_admission_independent_check_01.json', dict(status='PASS_BASE37_METADATA_CLOSURE_AND_DRIVER_CONSUMER_NOT_GPU_COMPLETE',
        gpu_admission_sha256=cc.sha(cc.BASE/'gpu_admission.json'), registration_sha256=cc.sha(cc.BASE/'registration_01.json'),
        source_lock_sha256=cc.sha(cc.BASE/'source_lock.json'), control_scope_sha256=cc.sha(scope_path),
        driver_code_files=io.own_code_files(), controller_code_files=cc.own_code_files(), **cc.COUNTS,
        prior_first_input_replays_reused=True, new_tensor_loads=0, new_RGB_reads=0,
        new_processor_encodes=0, new_media_decodes=0, new_model_calls=0, CPU_only=True, utc=cc.utc()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('register', 'check'))
    parser.add_argument('--scope', required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    (register if args.operation == 'register' else check)(args.scope)
