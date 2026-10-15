"""Deferred paired BASE boundary calls and independent output-only replay.

The main owns protocol/registration/admission/deployment and gpu_run.py. This
driver never launches that wrapper, prepares an input, or computes a GT metric.
"""
import argparse
import json
import math
import os
from pathlib import Path
import time
import traceback

import bd_contract as c
import bd_io as io


def final_weights(runtime, model, config, expected, names):
    """One full post-job base hash and all288 adapter values, not per call."""
    base = runtime.b_engine.frozen_identity(model, config)
    adapter = runtime.b_engine.adapter_identity(model, config)
    c.require(base == expected['base'] and adapter == expected['adapter'], 'Frozen original base/288 adapter values changed')
    return dict(base=base, adapter=adapter, inventory=c.inventory(model), layer_state=c.layer_state(model, False, names),
                gradients=c.frozen_gradients(model), weight_check_strategy=c.WEIGHT_CHECK_STRATEGY,
                full_base_and_288_adapter_verified=True, optimizer_updates=0)


def generation_arguments(contract, grammar):
    return dict(do_sample=False, max_new_tokens=contract.MAX_OUTPUT_TOKENS,
                prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)


def output_denominator(raw, proof, eos, max_tokens, done=None):
    ids, scores = raw['output_token_ids'], raw['selected_token_scores']
    c.require(0 < len(ids) <= max_tokens and all(type(t) is int and t >= 0 for t in ids) and
              len(ids) == len(scores) == raw['generated_score_count'] == raw['output_tokens'] and
              all(type(s) in (int, float) and math.isfinite(s) for s in scores) and
              raw['input_tokens'] == proof['input_tokens'] and raw['eos_token_ids'] == eos and
              raw['actual_model_call'] is True and raw['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and
              raw['activated_base_parameters'] == c.BASE_PARAMETERS,
              'New actual BASE output token/finite-score/input denominator failed; keep raw')
    if done is not None:
        c.require(done['output_tokens'] == len(ids) and done['input_tokens'] == proof['input_tokens'],
                  'Accepted token count differs from actual untouched raw')
    return ids


def infer(base):
    io.host(cpu=False)
    bundle = io.admitted(base)
    base, protocol, admission = bundle['base'], bundle['protocol'], bundle['admission']
    rows, counts = bundle['rows'], bundle['denominators']
    c.require(rows, 'This admitted BASE job needs actual callable endpoints; structural-only cases need no BASE job')
    oldio, contract, grammar_module = (bundle['helpers'][k] for k in ('io', 'contract', 'grammar'))
    runtime, runtime_files = oldio.legacy_runtime()
    c.require(runtime_files == bundle['cpu']['bindings']['original_b_processor_runtime']['runtime_files'],
              'Original frozen CPU/GPU runtime differs')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    c.require(io.read(io.HOME/'improvement_round1/active_gpu_job.json')['name'] == protocol['gpu_job_name'],
              'Current shared reservation is not this unique BASE job')
    io.deadline(protocol)
    import torch
    out = base/'gpu_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), job_name=protocol['gpu_job_name'],
        gpu_admission_sha256=bundle['gpu_admission_sha256'], source_lock_sha256=bundle['source_lock_sha256'],
        actual_model_call_budget=len(rows), **counts, prior_TIME_completed=True,
        prior_successful_input_replays_reused=True, new_media_decodes=0, new_input_processor_encodes=0, new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    entries, begun, current = [], 0, None
    model = identity = config = names = None
    try:
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        model, processor, identity = runtime.b_engine.load_model(config)
        oldio.verify_model(model, identity)
        c.require(identity == bundle['original_model_identity'], 'Actual newly loaded base/TIME values differ from successful TIME')
        inventory = c.inventory(model)
        initial = c.layer_state(model, False)
        names = initial['layer_names']
        assets = bundle['cpu']['bindings']['original_b_processor_runtime']['processor_assets']
        c.require(all(io.sha(path) == digest for path, digest in assets.items()), 'Original tokenizer/processor assets changed')
        io.save(out/'model_identity.json', dict(identity=identity, inventory=inventory, initial_enabled_layer_state=initial,
            gradients=c.frozen_gradients(model), weight_check_strategy=c.WEIGHT_CHECK_STRATEGY,
            full_engine_load_before_job=True, loaded_adapter_tensors=288, adapter_unloaded=False,
            actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS,
            adapter_disabled_only_in_each_call=True, new_optimizer_updates=0))
        initial_sha = io.sha(out/'model_identity.json')
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        strings = tuple(sorted({s for _, _, meta, _, _ in rows for s in contract.response_strings(meta)}))
        allowed = grammar_module.candidates(processor.tokenizer, strings)
        for entry, proof, meta, old_done, old_replay in rows:
            current = entry['request_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            cache_path = oldio.checked_ref(dict(path=proof['encoded_tensor_path'], sha256=proof['encoded_tensor_sha256']),
                                           roots=(bundle['source'],))
            encoded = oldio.load_tensor_cache(cache_path)
            c.require(set(encoded) == {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'} and
                      all(isinstance(v, torch.Tensor) and v.device.type == 'cpu' for v in encoded.values()) and
                      runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'],
                      'Exact accepted old CPU cache keys/dtype/bytes/signature differ')
            prefix = int(encoded['input_ids'].shape[1])
            c.require(prefix == proof['input_tokens'] and prefix <= contract.MAX_INPUT_TOKENS, 'Accepted input-token count changed')
            grammar = grammar_module.BoundaryConstraint(processor.tokenizer, prefix, meta, eos, allowed)
            gpu = {key: value.to('cuda') for key, value in encoded.items()}
            c.require(runtime.tensor_signature(gpu) == proof['input_evidence']['tensor_signature'], 'CPU/GPU tensor equality failed')
            io.save(folder/'gpu_input.json', dict(status='PASS_UNCHANGED_CPU_GPU_TENSOR_EQUALITY',
                tensor_signature=proof['input_evidence']['tensor_signature'], encoded_tensor_sha256=proof['encoded_tensor_sha256'],
                encoded_tensor_format=proof['encoded_tensor_format']))
            before = dict(layer_state=c.layer_state(model, False, names), gradients=c.frozen_gradients(model),
                verified_engine_load_checkpoint_sha256=initial_sha, weight_check_strategy=c.WEIGHT_CHECK_STRATEGY)
            io.save(folder/'activation_before.json', before)
            io.save(folder/'request.json', dict(request_id=current, event_id=meta['event_id'], side=meta['side'],
                original_case_id=meta['original_case_id'], original_segment_index=meta['original_segment_index'],
                original_interval_exact=meta['original_interval_exact'], window_start=meta['window_start'], window_end=meta['window_end'],
                prompt=meta['prompt'], input_path=proof['input_path'], input_sha256=proof['input_sha256'],
                CPU_proof_sha256=entry['proof_sha256'], encoded_tensor_sha256=proof['encoded_tensor_sha256'],
                encoded_tensor_format=proof['encoded_tensor_format'], input_evidence=proof['input_evidence'],
                finite_response_strings=contract.response_strings(meta), reference_labels_read=False,
                adapter_activation_only_changed=True, independent_prefill=True,
                prior_outputs_supplied_as_context=False, past_key_values_supplied=False,
                prior_TIME_done_path=str(bundle['source']/'gpu_01'/current/'done.json'),
                prior_TIME_done_sha256=io.sha(bundle['source']/'gpu_01'/current/'done.json'),
                prior_input_replay_path=str(bundle['source']/'replay_01'/(current+'.json')),
                prior_input_replay_sha256=io.sha(bundle['source']/'replay_01'/(current+'.json')),
                generation_arguments=dict(do_sample=False, max_new_tokens=contract.MAX_OUTPUT_TOKENS,
                                          return_dict_in_generate=True, output_scores=True)))
            try:
                with model.disable_adapter():
                    inside = dict(layer_state=c.layer_state(model, True, names), gradients=c.frozen_gradients(model),
                        actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS,
                        loaded_adapter_tensors=288, adapter_unloaded=False)
                    io.save(folder/'activation_disabled.json', inside)
                    io.deadline(protocol)
                    c.require(begun < admission['actual_model_call_budget'], 'Frozen actual BASE call budget exceeded')
                    begun += 1
                    io.append(out/'attempts.jsonl', dict(event='BEGIN_MODEL_CALL', call_id=begun, request_id=current,
                        raw_path=str(folder/'raw.json'), utc=io.utc()))
                    started = time.monotonic()
                    # Every call begins from its full saved input. No returned KV is
                    # carried to a later call or supplied as generation arguments.
                    with torch.inference_mode():
                        generated = model.generate(**gpu, **generation_arguments(contract, grammar))
                    torch.cuda.synchronize()
                    ids = generated.sequences[0, prefix:]
                    raw_text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
                    scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
                    raw = dict(raw_output=raw_text, output_token_ids=ids.tolist(),
                        selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                        generated_score_count=len(generated.scores), input_tokens=prefix, output_tokens=len(ids),
                        generation_seconds=time.monotonic()-started, input_evidence=proof['input_evidence'],
                        constraint_stats=grammar.stats, eos_token_ids=eos, actual_model_call=True,
                        activation_disabled_sha256=io.sha(folder/'activation_disabled.json'),
                        actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS)
                    io.save(folder/'raw.json', raw)  # untouched raw BEFORE token/schema/parser checks
                    c.layer_state(model, True, names)
                    c.frozen_gradients(model)
            finally:
                # PEFT re-enable can expose trainable adapters. Restore first,
                # record the actual pre/post counts, then verify all144 enabled.
                restored = c.restore_frozen_gradients(model)
                io.save(folder/'gradient_restoration.json', restored)
                after = dict(layer_state=c.layer_state(model, False, names), gradients=c.frozen_gradients(model),
                    gradient_restoration_sha256=io.sha(folder/'gradient_restoration.json'),
                    verified_engine_load_checkpoint_sha256=initial_sha, weight_check_strategy=c.WEIGHT_CHECK_STRATEGY,
                    all_144_states_restored=True)
                io.save(folder/'activation_after.json', after)
            c.validate_restoration(before, inside, after, restored, names)
            output_denominator(raw, proof, eos, contract.MAX_OUTPUT_TOKENS)
            decision = grammar.assert_complete(ids)
            c.require(json.dumps(decision, separators=(',', ':')) == raw_text, 'Actual token IDs/raw JSON decision differ')
            endpoint = contract.resolve_endpoint(decision, meta)
            endpoint.update(actual_model_call=True, predeclared_skip=False, decision_origin='MODEL_OUTPUT')
            done_path = folder/'done.json'
            io.save(done_path, dict(status='PASS_BASE_PAIRED_LOCAL_BOUNDARY_DECISION_NOT_QUALITY',
                request_id=current, event_id=meta['event_id'], side=meta['side'], decision=decision, endpoint_result=endpoint,
                raw_sha256=io.sha(folder/'raw.json'), request_sha256=io.sha(folder/'request.json'),
                activation_before_sha256=io.sha(folder/'activation_before.json'),
                activation_disabled_sha256=io.sha(folder/'activation_disabled.json'), activation_after_sha256=io.sha(folder/'activation_after.json'),
                gradient_restoration_sha256=io.sha(folder/'gradient_restoration.json'),
                input_tokens=prefix, output_tokens=len(ids), input_evidence=proof['input_evidence'], new_optimizer_updates=0))
            accepted = dict(request_id=current, event_id=meta['event_id'], side=meta['side'],
                            done_path=str(done_path), done_sha256=io.sha(done_path))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED_MODEL_CALL', call_id=begun, **accepted, utc=io.utc()))
            entries.append(accepted)
            print(json.dumps(dict(accepted_calls=len(entries), total_calls=len(rows), request_id=current,
                                 applied_decision=endpoint['applied_decision'], quality_claim=False)), flush=True)
            del gpu, encoded, generated, ids
        c.require(begun == len(entries) == len(rows), 'Complete new BASE actual denominator failed')
        final = final_weights(runtime, model, config, identity, names)
        io.save(out/'model_final_weights.json', final)
        c.validate_journal(io.read_journal(out/'attempts.jsonl'), [r[0]['request_id'] for r in rows], entries)
        io.save(out/'completion.json', dict(status='PASS_ALL_BASE_PAIRED_CALLS_NOT_QUALITY', requests=len(rows),
            events=len(bundle['events']), actual_model_calls=begun, entries=entries, **counts,
            attempts_sha256=io.sha(out/'attempts.jsonl'), model_identity_sha256=initial_sha,
            model_final_weights_sha256=io.sha(out/'model_final_weights.json'),
            gpu_admission_sha256=bundle['gpu_admission_sha256'], source_lock_sha256=bundle['source_lock_sha256'],
            registration_sha256=bundle['registration_sha256'], source_TIME_export_sha256=io.sha(bundle['source']/'boundary_prediction_export.json'),
            structural_skips_sha256=io.sha(bundle['source']/'plan_01/structural_skips.json'),
            actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS,
            weight_check_strategy=c.WEIGHT_CHECK_STRATEGY, independent_prefill_per_call=True,
            reference_labels_read=False, new_media_decodes=0, new_input_processor_encodes=0, new_optimizer_updates=0, utc=io.utc()))
    except BaseException as error:
        final_error = None
        if model is not None and names is not None and not (out/'model_final_weights.json').exists():
            try:
                model.requires_grad_(False)
                io.save(out/'failure_final_weights.json', final_weights(runtime, model, config, identity, names))
            except BaseException as check_error:
                final_error = repr(check_error)
        io.save(out/'failure.json', dict(status='FAILED_BASE_PAIR_KEEP_RAW_AND_SUCCESS_NO_UNKNOWN_FALLBACK',
            request_id=current, actual_started_model_calls=begun, successful_entries=entries, error=repr(error),
            final_weight_check_error=final_error, traceback=traceback.format_exc(), new_optimizer_updates=0, utc=io.utc()))
        raise


def replay(base):
    io.host(cpu=True)
    bundle = io.admitted(base)
    base, rows, counts = bundle['base'], bundle['rows'], bundle['denominators']
    oldio, contract, grammar_module, independent = (bundle['helpers'][k] for k in ('io', 'contract', 'grammar', 'replay'))
    resource, resource_sha = oldio.terminal_resource(bundle['protocol']['gpu_job_name'])
    gpu = base/'gpu_01'
    complete = io.read(gpu/'completion.json')
    c.require(complete['status'] == 'PASS_ALL_BASE_PAIRED_CALLS_NOT_QUALITY' and
              complete['requests'] == complete['actual_model_calls'] == len(rows) and
              complete['events'] == len(bundle['events']) and all(complete[k] == v for k, v in counts.items()) and
              complete['attempts_sha256'] == io.sha(gpu/'attempts.jsonl') and
              complete['model_identity_sha256'] == io.sha(gpu/'model_identity.json') and
              complete['model_final_weights_sha256'] == io.sha(gpu/'model_final_weights.json') and
              complete['gpu_admission_sha256'] == bundle['gpu_admission_sha256'] and
              complete['source_lock_sha256'] == bundle['source_lock_sha256'] and
              complete['registration_sha256'] == bundle['registration_sha256'] and
              complete['source_TIME_export_sha256'] == io.sha(bundle['source']/'boundary_prediction_export.json') and
              complete['structural_skips_sha256'] == io.sha(bundle['source']/'plan_01/structural_skips.json'),
              'Naturally complete unique BASE execution/frozen source closure required')
    c.validate_journal(io.read_journal(gpu/'attempts.jsonl'), [r[0]['request_id'] for r in rows], complete['entries'])
    initial, final = io.read(gpu/'model_identity.json'), io.read(gpu/'model_final_weights.json')
    identity = bundle['original_model_identity']
    names = initial['initial_enabled_layer_state']['layer_names']
    c.serialized_state(initial['initial_enabled_layer_state'], False, names)
    c.serialized_state(final['layer_state'], False, names)
    c.require(initial['identity'] == identity and final['base'] == identity['base'] and final['adapter'] == identity['adapter'] and
              final['inventory'] == initial['inventory'] and final['full_base_and_288_adapter_verified'] is True and
              final['weight_check_strategy'] == initial['weight_check_strategy'] == c.WEIGHT_CHECK_STRATEGY and
              final['gradients'] == initial['gradients'] == dict(trainable_tensor_count=0, trainable_parameters=0, trainable_tensor_names=[]),
              'Full job before/after base/288 adapter or frozen gradient identity differs')
    out = base/'replay_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'),
        prior_successful_input_replays_reused=True, new_model_calls=0, new_media_decodes=0, new_processor_encodes=0,
        cache_tensors_loaded=0, RGB_arrays_loaded=0, processor_instantiated=False))
    current, proofs, endpoints, comparisons = None, [], {}, []
    try:
        # Tokenizer only: no AutoProcessor, runtime.encode, tensor cache load or RGB read.
        import torch
        from transformers import AutoTokenizer
        c.require(not torch.cuda.is_initialized(), 'Output-only CPU replay initialized CUDA')
        assets = bundle['cpu']['bindings']['original_b_processor_runtime']['processor_assets']
        c.require(all(io.sha(path) == digest for path, digest in assets.items()), 'Original tokenizer assets changed')
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
        eos = io.read(Path(config['model_dir'])/'generation_config.json')['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        strings = tuple(sorted({s for _, _, meta, _, _ in rows for s in contract.response_strings(meta)}))
        allowed = grammar_module.candidates(tokenizer, strings)
        for accepted, (entry, proof, meta, old_done, old_replay) in zip(complete['entries'], rows):
            current = entry['request_id']
            folder = gpu/current
            c.require(accepted['done_path'] == str(folder/'done.json') and
                      accepted['done_sha256'] == io.sha(folder/'done.json'), 'Unique accepted BASE done path changed')
            done, raw, request = [io.read(folder/name) for name in ('done.json', 'raw.json', 'request.json')]
            c.require(done['status'] == 'PASS_BASE_PAIRED_LOCAL_BOUNDARY_DECISION_NOT_QUALITY' and
                      done['request_id'] == request['request_id'] == current and
                      done['event_id'] == request['event_id'] == meta['event_id'] and
                      done['side'] == request['side'] == meta['side'] and
                      request['original_case_id'] == meta['original_case_id'] and
                      request['original_segment_index'] == meta['original_segment_index'] and
                      request['original_interval_exact'] == meta['original_interval_exact'] and
                      request['window_start'] == meta['window_start'] and request['window_end'] == meta['window_end'] and
                      done['raw_sha256'] == io.sha(folder/'raw.json') and done['request_sha256'] == io.sha(folder/'request.json') and
                      request['input_path'] == proof['input_path'] and request['input_sha256'] == proof['input_sha256'] and
                      request['CPU_proof_sha256'] == entry['proof_sha256'] and
                      request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
                      request['encoded_tensor_format'] == proof['encoded_tensor_format'] == oldio.TENSOR_CACHE_FORMAT and
                      request['prompt'] == meta['prompt'] == contract.prompt(meta) and
                      request['finite_response_strings'] == list(contract.response_strings(meta)) and
                      request['prior_TIME_done_path'] == str(bundle['source']/'gpu_01'/current/'done.json') and
                      request['prior_TIME_done_sha256'] == io.sha(request['prior_TIME_done_path']) and
                      request['prior_input_replay_path'] == str(bundle['source']/'replay_01'/(current+'.json')) and
                      request['prior_input_replay_sha256'] == io.sha(request['prior_input_replay_path']) and
                      request['past_key_values_supplied'] is False and request['prior_outputs_supplied_as_context'] is False and
                      request['independent_prefill'] is True and request['adapter_activation_only_changed'] is True and
                      request['reference_labels_read'] is False and
                      proof['input_evidence'] == old_replay['input_evidence'] == request['input_evidence'] ==
                      raw['input_evidence'] == done['input_evidence'], 'BASE raw/input/TIME replay/role pair binding differs')
            before, inside, after, restored = [io.read(folder/name) for name in
                ('activation_before.json', 'activation_disabled.json', 'activation_after.json', 'gradient_restoration.json')]
            for filename, key in (('activation_before.json', 'activation_before_sha256'),
                                  ('activation_disabled.json', 'activation_disabled_sha256'),
                                  ('activation_after.json', 'activation_after_sha256'),
                                  ('gradient_restoration.json', 'gradient_restoration_sha256')):
                c.require(done[key] == io.sha(folder/filename), 'New per-call activation/gradient SHA changed')
            c.require(after['gradient_restoration_sha256'] == io.sha(folder/'gradient_restoration.json') and
                      raw['activation_disabled_sha256'] == io.sha(folder/'activation_disabled.json') and
                      before['verified_engine_load_checkpoint_sha256'] == after['verified_engine_load_checkpoint_sha256'] ==
                      io.sha(gpu/'model_identity.json') and
                      before['weight_check_strategy'] == after['weight_check_strategy'] == c.WEIGHT_CHECK_STRATEGY and
                      inside['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and
                      inside['activated_base_parameters'] == c.BASE_PARAMETERS and inside['loaded_adapter_tensors'] == 288 and
                      inside['adapter_unloaded'] is False and after['all_144_states_restored'] is True,
                      'Actual disabled context/checkpoint/restore evidence differs')
            c.validate_restoration(before, inside, after, restored, names)
            transfer = io.read(folder/'gpu_input.json')
            c.require(transfer['status'] == 'PASS_UNCHANGED_CPU_GPU_TENSOR_EQUALITY' and
                      transfer['tensor_signature'] == proof['input_evidence']['tensor_signature'] and
                      transfer['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
                      transfer['encoded_tensor_format'] == proof['encoded_tensor_format'], 'Actual new CPU/GPU transfer differs')
            ids = output_denominator(raw, proof, eos, contract.MAX_OUTPUT_TOKENS, done)
            decoded = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            grammar = grammar_module.BoundaryConstraint(tokenizer, proof['input_tokens'], meta, eos, allowed)
            decision = grammar.assert_complete(ids)
            c.require(decoded == raw['raw_output'] == json.dumps(decision, separators=(',', ':')) and decision == done['decision'],
                      'Independent new BASE output token/finite grammar parser differs')
            clock = oldio.extract_clock(io.read(io.checked_ref(meta['original_evidence']['clock'])), meta['clock_object_keys'])
            endpoint = independent.independent_endpoint(decision, meta, clock)
            endpoint.update(actual_model_call=True, predeclared_skip=False, decision_origin='MODEL_OUTPUT')
            c.require(endpoint == done['endpoint_result'], 'Independent same-V4 native conversion/UNKNOWN retention differs')
            endpoints[current] = endpoint
            proof_path = out/(current+'.json')
            io.save(proof_path, dict(status='PASS_INDEPENDENT_BASE_OUTPUT_TOKEN_GRAMMAR_NATIVE_REPLAY_NOT_QUALITY',
                request_id=current, event_id=meta['event_id'], side=meta['side'], CPU_only=True,
                done_sha256=io.sha(folder/'done.json'), raw_sha256=io.sha(folder/'raw.json'),
                prior_first_input_replay_path=request['prior_input_replay_path'],
                prior_first_input_replay_sha256=request['prior_input_replay_sha256'], input_evidence=proof['input_evidence'],
                endpoint_result=endpoint, all_144_activation_and_gradient_states_verified=True,
                new_media_decodes=0, new_processor_encodes=0, cache_tensors_loaded=0, RGB_arrays_loaded=0,
                new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(request_id=current, proof_path=str(proof_path), proof_sha256=io.sha(proof_path)))
            comparisons.append(dict(request_id=current, TIME_decision=old_done['decision'], BASE_decision=decision,
                TIME_endpoint_exact=old_done['endpoint_result']['endpoint_exact'], BASE_endpoint_exact=endpoint['endpoint_exact'],
                same_input_sha256=proof['input_sha256'], changed_output_is_not_quality_evidence=True))
            print(json.dumps(dict(completed_new_output_replays=len(proofs), total_requests=len(rows))), flush=True)
        structural_proofs = []
        for skip in bundle['skips']:
            ref = skip['independent_geometry_proof']
            geometry = io.read(io.checked_ref(ref, roots=(bundle['source'],)))
            c.require(geometry['endpoint_result'] == skip['endpoint_result'], 'Original structural geometry endpoint changed')
            endpoints[skip['request_id']] = geometry['endpoint_result']
            # Direct reference, no fake call/raw/token replay or repeated geometry computation.
            structural_proofs.append(dict(request_id=skip['request_id'], proof_path=ref['path'], proof_sha256=ref['sha256'],
                                          directly_reused_first_geometry_proof=True))
        c.require(len(proofs) == counts['actionable_requests'] and len(endpoints) == counts['nominal_endpoints'] and
                  not torch.cuda.is_initialized(), 'Full actionable/structural CPU output denominator or CUDA check failed')
        exported = [independent.independent_event(event, endpoints) for event in bundle['events']]
        io.save(out/'completion.json', dict(status='PASS_ALL_BASE_PAIRED_OUTPUT_REPLAYS_NOT_QUALITY', requests=len(proofs),
            events=len(exported), proofs=proofs, structural_proofs=structural_proofs, **counts,
            CPU_only=True, CUDA_initialized=False, gpu_completion_sha256=io.sha(gpu/'completion.json'),
            resource_terminal_sha256=resource_sha, prior_TIME_replay_completion_sha256=io.sha(bundle['source']/'replay_01/completion.json'),
            new_media_decodes=0, new_processor_encodes=0, cache_tensors_loaded=0, RGB_arrays_loaded=0,
            processor_instantiated=False, new_model_calls=0, new_optimizer_updates=0))
        io.save(base/'boundary_prediction_export.json', dict(status='PASS_LOCAL_BOUNDARY_EXECUTION_REPLAY_NOT_QUALITY',
            schema=c.SCHEMA, role=bundle['role'], events=exported, **counts, full_endpoint_results=len(endpoints),
            actual_model_calls=len(rows), actual_independent_model_replays=len(proofs),
            structural_geometry_proof_count=len(structural_proofs), structural_skip_does_not_remove_event=True,
            original_b_model_parameters=c.PHYSICAL_PARAMETERS, actual_physical_parameters=c.PHYSICAL_PARAMETERS,
            activated_base_parameters=c.BASE_PARAMETERS, boundary_activation='BASE_TIME_ADAPTER_DISABLED_PER_CALL',
            independent_replay_completion_sha256=io.sha(out/'completion.json'),
            TIME_paired_export_path=str(bundle['source']/'boundary_prediction_export.json'),
            TIME_paired_export_sha256=io.sha(bundle['source']/'boundary_prediction_export.json'),
            source_endpoint_availability_path=str(bundle['source']/'plan_01/endpoint_availability.json'),
            source_endpoint_availability_sha256=io.sha(bundle['source']/'plan_01/endpoint_availability.json'),
            reference_labels_read=False, retained_events=len(exported), newly_created_events=0, removed_events=0,
            new_model_calls=0, new_optimizer_updates=0, SCI=False, quality_claim=False))
        io.save(base/'paired_behavior_export.json', dict(status='PAIRED_TIME_BASE_BEHAVIOR_ONLY_NOT_QUALITY',
            role=bundle['role'], comparisons=comparisons, **counts, events=len(exported), actual_gpu_seconds=resource['charged_seconds'],
            BASE_export_sha256=io.sha(base/'boundary_prediction_export.json'),
            TIME_export_sha256=io.sha(bundle['source']/'boundary_prediction_export.json'),
            changed_output_is_not_quality_evidence=True, quality_selection_by_this_driver=False,
            confirm_metrics_sealed_until_frozen_development_selection=True, SCI=False))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_BASE_OUTPUT_REPLAY_KEEP_RAW_AND_SUCCESS_NO_UNKNOWN_FALLBACK',
            request_id=current, successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(),
            new_model_calls=0, new_optimizer_updates=0, utc=io.utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('infer', 'replay'))
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    if args.operation == 'replay':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    (infer if args.operation == 'infer' else replay)(args.base)
