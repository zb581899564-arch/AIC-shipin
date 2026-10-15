"""New two-call adapter-disabled boundary infer and output-only CPU replay.

admit never grants GPU execution. Main must supply an independent GPU admission
and shared gpu_run.py reservation. No input encoder or media decoder is called.
"""
import argparse
import datetime as dt
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import time
import traceback

import aa_contract as c
import aa_io as io


def frozen_weights(runtime, model, config, expected):
    base = runtime.b_engine.frozen_identity(model,config)
    adapter = runtime.b_engine.adapter_identity(model,config)
    c.require(base == expected['base'] and adapter == expected['adapter'], 'Frozen original base/TIME adapter values changed')
    return dict(base=base,adapter=adapter,inventory=c.parameter_inventory(model))


def gpu_permission(admission,p):
    permitpath = io.BASE/'gpu_admission.json'
    permit = io.read(permitpath)
    c.require(permit['status'] == 'PASS_INDEPENDENT_REMAINING_END_ACTIVATION_GPU_ADMISSION' and
        permit['source_lock_sha256'] == io.sha(io.BASE/'source_lock.json') and
        permit['input_admission_sha256'] == io.sha(io.BASE/'admission.json') and
        permit['actual_model_call_budget'] == c.MAX_CALLS and permit['gpu_job_name'] == p['gpu_job_name'] and
        permit['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and permit['activated_base_parameters'] == c.BASE_PARAMETERS and
        permit['optimizer_updates'] == 0, 'Main independent activation GPU permission missing or changed')
    c.require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(p['deadline'].replace('Z','+00:00')),
              'No new activation model call after frozen deadline')
    return permitpath,permit


def infer(rootpath):
    io.host(cpu=False)
    admission,p,cpu,rows,prior = io.verify_lock(rootpath)
    permitpath,permit = gpu_permission(admission,p)
    helpers = io.old_helpers(cpu['bindings']['own_code_files'])
    oldio, contract, grammar_module = helpers['io'],helpers['contract'],helpers['grammar']
    runtime,runtimefiles = oldio.legacy_runtime()
    c.require(runtimefiles == cpu['bindings']['original_b_processor_runtime']['runtime_files'],'Frozen original runtime changed')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    c.require(io.read(io.HOME/'improvement_round1/active_gpu_job.json')['name'] == p['gpu_job_name'], 'Wrong active unique GPU reservation')
    import torch
    out = io.BASE/'gpu_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),gpu_admission_sha256=io.sha(permitpath),
        source_lock_sha256=io.sha(io.BASE/'source_lock.json'),job_name=p['gpu_job_name'],actual_model_call_budget=c.MAX_CALLS,
        prior_successful_input_replays_reused=True,new_input_processor_encodes=0,new_media_decodes=0,new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    entries,begun,current = [],0,None
    try:
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        model,processor,identity = runtime.b_engine.load_model(config)
        oldio.verify_model(model,identity)
        c.require(identity == prior['original_model_identity'], 'New loaded weights differ from prior successful TIME identity')
        inventory = c.parameter_inventory(model)
        initial_state = c.layer_state(model,False)
        io.save(out/'model_identity.json',dict(identity=identity,inventory=inventory,
            initial_enabled_layer_state=initial_state,adapter_loaded_but_disabled_only_in_each_boundary_call=True,
            original_coarse_and_VERIFY_models_unmodified=True,new_optimizer_updates=0))
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos,int) else list(eos)
        strings = tuple(sorted({s for _,_,meta,_,_ in rows for s in contract.response_strings(meta)}))
        allowed = grammar_module.candidates(processor.tokenizer,strings)
        for entry,proof,meta,old_done,old_replay in rows:
            current = entry['request_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            encoded = oldio.load_tensor_cache(proof['encoded_tensor_path'])
            c.require(set(encoded) == {'input_ids','attention_mask','pixel_values_videos','video_grid_thw'} and
                runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'], 'Exact old CPU cache keys/signature changed')
            prefix = int(encoded['input_ids'].shape[1])
            c.require(prefix == proof['input_tokens'] and prefix <= contract.MAX_INPUT_TOKENS,'Original input tokens changed')
            grammar = grammar_module.BoundaryConstraint(processor.tokenizer,prefix,meta,eos,allowed)
            gpu = {key:value.to('cuda') for key,value in encoded.items()}
            c.require(runtime.tensor_signature(gpu) == proof['input_evidence']['tensor_signature'],'Actual reused CPU/GPU tensor equality failed')
            io.save(folder/'gpu_input.json',dict(status='PASS_UNCHANGED_CPU_GPU_TENSOR_EQUALITY',
                tensor_signature=proof['input_evidence']['tensor_signature'],encoded_tensor_sha256=proof['encoded_tensor_sha256']))
            before = c.layer_state(model,False,initial_state['layer_names'])
            # This job has exactly one remaining call. engine.load_model has
            # just performed the full base hash +288 adapter value check.
            # Reuse that real pre-call checkpoint and full-rehash after call.
            before_weights = dict(base=identity['base'],adapter=identity['adapter'],inventory=c.parameter_inventory(model))
            io.save(folder/'activation_before.json',dict(layer_state=before,frozen_weights=before_weights,
                weight_check_strategy=c.WEIGHT_CHECK_STRATEGY,
                verified_engine_load_checkpoint_sha256=io.sha(out/'model_identity.json')))
            io.save(folder/'request.json',dict(request_id=current,event_id=meta['event_id'],side=meta['side'],
                original_case_id=meta['original_case_id'],original_segment_index=meta['original_segment_index'],
                original_interval_exact=meta['original_interval_exact'],prompt=meta['prompt'],
                input_path=proof['input_path'],input_sha256=proof['input_sha256'],CPU_proof_sha256=entry['proof_sha256'],
                encoded_tensor_sha256=proof['encoded_tensor_sha256'],encoded_tensor_format=proof['encoded_tensor_format'],
                input_evidence=proof['input_evidence'],finite_response_strings=contract.response_strings(meta),
                prior_TIME_done_path=str(io.SOURCE/'gpu_01'/current/'done.json'),
                prior_TIME_done_sha256=io.sha(io.SOURCE/'gpu_01'/current/'done.json'),
                prior_input_replay_path=str(io.SOURCE/'replay_01'/(current+'.json')),
                prior_input_replay_sha256=io.sha(io.SOURCE/'replay_01'/(current+'.json')),
                reference_labels_read=False,adapter_activation_only_changed=True,
                generation_arguments=dict(do_sample=False,max_new_tokens=contract.MAX_OUTPUT_TOKENS,
                    return_dict_in_generate=True,output_scores=True),
                prior_outputs_supplied_as_context=False,past_key_values_supplied=False))
            try:
                with model.disable_adapter():
                    inside = c.layer_state(model,True,initial_state['layer_names'])
                    io.save(folder/'activation_disabled.json',dict(layer_state=inside,inventory=c.parameter_inventory(model),
                        actual_physical_parameters=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS,
                        no_parameters_unloaded=True))
                    c.require(begun < c.MAX_CALLS,'Frozen two-call budget exceeded')
                    begun += 1
                    io.append(out/'attempts.jsonl',dict(event='BEGIN_MODEL_CALL',call_id=begun,request_id=current,utc=io.utc()))
                    started = time.monotonic()
                    with torch.inference_mode():
                        generated = model.generate(**gpu,do_sample=False,max_new_tokens=contract.MAX_OUTPUT_TOKENS,
                            prefix_allowed_tokens_fn=grammar,return_dict_in_generate=True,output_scores=True)
                    torch.cuda.synchronize()
                    ids = generated.sequences[0,prefix:]
                    raw = processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    scores = [float(score[0,int(token)]) for score,token in zip(generated.scores,ids)]
                    io.save(folder/'raw.json',dict(raw_output=raw,output_token_ids=ids.tolist(),
                        selected_token_scores=[score if math.isfinite(score) else str(score) for score in scores],
                        generated_score_count=len(generated.scores),input_tokens=prefix,output_tokens=len(ids),
                        generation_seconds=time.monotonic()-started,input_evidence=proof['input_evidence'],
                        constraint_stats=grammar.stats,eos_token_ids=eos,actual_model_call=True,
                        activation_disabled_sha256=io.sha(folder/'activation_disabled.json'),
                        actual_physical_parameters=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS))
                    c.layer_state(model,True,initial_state['layer_names'])
            finally:
                gradients = c.restore_frozen_gradients(model)
                io.save(folder/'gradient_restoration.json',gradients)
                after = c.layer_state(model,False,initial_state['layer_names'])
                after_weights = frozen_weights(runtime,model,config,identity)
                io.save(folder/'activation_after.json',dict(layer_state=after,frozen_weights=after_weights,
                    all_144_states_restored=True,frozen_base_and_adapter_values_unchanged=after_weights == before_weights,
                    gradient_restoration_sha256=io.sha(folder/'gradient_restoration.json'),
                    trainable_tensor_count_after_restore=0,weight_check_strategy=c.WEIGHT_CHECK_STRATEGY))
                c.require(after_weights == before_weights,'Frozen before/after disable-context weights differ')
            c.require(0 < len(ids) <= contract.MAX_OUTPUT_TOKENS and len(scores) == len(ids) and all(map(math.isfinite,scores)),
                      'Actual output token/finite score denominator failed; raw kept')
            decision = grammar.assert_complete(ids)
            c.require(json.dumps(decision,separators=(',',':')) == raw,'Raw decision/generated token IDs differ')
            endpoint = contract.resolve_endpoint(decision,meta)
            donepath = folder/'done.json'
            io.save(donepath,dict(status='PASS_REMAINING_END_ACTIVATION_DECISION_NOT_QUALITY',request_id=current,
                event_id=meta['event_id'],side=meta['side'],decision=decision,endpoint_result=endpoint,
                raw_sha256=io.sha(folder/'raw.json'),request_sha256=io.sha(folder/'request.json'),
                activation_before_sha256=io.sha(folder/'activation_before.json'),
                activation_disabled_sha256=io.sha(folder/'activation_disabled.json'),
                activation_after_sha256=io.sha(folder/'activation_after.json'),
                input_evidence=proof['input_evidence'],input_tokens=prefix,output_tokens=len(ids),new_optimizer_updates=0))
            io.append(out/'attempts.jsonl',dict(event='ACCEPTED_MODEL_CALL',call_id=begun,request_id=current,
                done_path=str(donepath),done_sha256=io.sha(donepath),utc=io.utc()))
            entries.append(dict(request_id=current,event_id=meta['event_id'],side=meta['side'],done_path=str(donepath),done_sha256=io.sha(donepath)))
            print(json.dumps(dict(accepted_calls=len(entries),max_calls=c.MAX_CALLS,request_id=current,
                                 decision=endpoint['applied_decision'],quality_claim=False)),flush=True)
            del gpu,encoded,generated,ids
        c.require(begun == len(entries) == c.MAX_CALLS,'Complete two-call denominator failed')
        io.save(out/'completion.json',dict(status='PASS_ONLY_REMAINING_END_ACTIVATION_CALL_NOT_QUALITY',actual_model_calls=begun,entries=entries,
            attempts_sha256=io.sha(out/'attempts.jsonl'),model_identity_sha256=io.sha(out/'model_identity.json'),
            source_lock_sha256=io.sha(io.BASE/'source_lock.json'),gpu_admission_sha256=io.sha(permitpath),
            original_successful_input_replays_reused=True,new_media_decodes=0,new_input_processor_encodes=0,
            actual_physical_parameters=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS,
            prior_start_status='UNACCEPTED_POST_STATE_PROOF',v1_failed_status_preserved=True,
            new_optimizer_updates=0,quality_gate_or_change_based_selection_admitted=False,utc=io.utc()))
    except BaseException as error:
        io.save(out/'failure.json',dict(status='FAILED_ACTIVATION_KEEP_RAW_AND_SUCCESS_NO_UNKNOWN_FALLBACK',
            request_id=current,actual_started_model_calls=begun,successful_entries=entries,error=repr(error),
            traceback=traceback.format_exc(),new_optimizer_updates=0,utc=io.utc()))
        raise


def replay(rootpath):
    io.host(cpu=True)
    admission,p,cpu,rows,prior = io.verify_lock(rootpath)
    helpers = io.old_helpers(cpu['bindings']['own_code_files'])
    oldio,contract,grammar_module,independent = (helpers[name] for name in ('io','contract','grammar','replay'))
    resource,resource_sha = oldio.terminal_resource(p['gpu_job_name'])
    gpu = io.BASE/'gpu_01'
    complete = io.read(gpu/'completion.json')
    c.require(complete['status'] == 'PASS_ONLY_REMAINING_END_ACTIVATION_CALL_NOT_QUALITY' and complete['actual_model_calls'] == c.MAX_CALLS and
        complete['source_lock_sha256'] == io.sha(io.BASE/'source_lock.json') and
        complete['gpu_admission_sha256'] == io.sha(io.BASE/'gpu_admission.json') and
        complete['attempts_sha256'] == io.sha(gpu/'attempts.jsonl') and
        complete['model_identity_sha256'] == io.sha(gpu/'model_identity.json'),'Complete unique activation GPU execution required')
    model_evidence = io.read(gpu/'model_identity.json')
    c.require(model_evidence['identity'] == prior['original_model_identity'],'Actual new original model identity changed')
    c.serialized_layer_state(model_evidence['initial_enabled_layer_state'],False)
    journal = [json.loads(line) for line in (gpu/'attempts.jsonl').read_text().splitlines() if line.strip()]
    c.require(len(journal) == 2*c.MAX_CALLS and len(complete['entries']) == c.MAX_CALLS,'Actual complete new journal denominator')
    by_done = {entry['request_id']:entry for entry in complete['entries']}
    out = io.BASE/'replay_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json',dict(pid=os.getpid(),CPU_only=True,resource_terminal_sha256=resource_sha,
        old_successful_input_replays_reused=True,new_processor_encodes=0,new_media_decodes=0,new_model_calls=0,utc=io.utc()))
    proofs,comparisons,endpoints,current = [],[],{},None
    try:
        import torch
        runtime,processor,identity = oldio.cpu_runtime()
        c.require(identity == cpu['bindings']['original_b_processor_runtime'],'Original replay tokenizer/runtime assets changed')
        # Successful pixel/input replay is referenced, never encoded again.
        runtime.encode = lambda *args,**kwargs: (_ for _ in ()).throw(ValueError('Forbidden repeated input encoder'))
        runtime.baseline_frames = lambda *args,**kwargs: (_ for _ in ()).throw(ValueError('Forbidden repeated RGB read'))
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        eos = io.read(Path(config['model_dir'])/'generation_config.json')['eos_token_id']
        eos = [eos] if isinstance(eos,int) else list(eos)
        strings = tuple(sorted({s for _,_,meta,_,_ in rows for s in contract.response_strings(meta)}))
        allowed = grammar_module.candidates(processor.tokenizer,strings)
        for index,(entry,proof,meta,old_done,old_replay) in enumerate(rows,1):
            current = entry['request_id']
            c.require(journal[2*(index-1)]['event'] == 'BEGIN_MODEL_CALL' and journal[2*(index-1)+1]['event'] == 'ACCEPTED_MODEL_CALL' and
                all(journal[i]['call_id'] == index and journal[i]['request_id'] == current for i in (2*(index-1),2*(index-1)+1)),
                'Actual activation call order differs')
            folder = gpu/current
            c.require(by_done[current]['done_path'] == str(folder/'done.json') and
                      by_done[current]['done_sha256'] == io.sha(folder/'done.json'),'Actual accepted done binding differs')
            done,raw,request = [io.read(folder/name) for name in ('done.json','raw.json','request.json')]
            c.require(done['raw_sha256'] == io.sha(folder/'raw.json') and done['request_sha256'] == io.sha(folder/'request.json') and
                done['status'] == 'PASS_REMAINING_END_ACTIVATION_DECISION_NOT_QUALITY' and
                request['input_sha256'] == proof['input_sha256'] and request['CPU_proof_sha256'] == entry['proof_sha256'] and
                request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
                request['prompt'] == meta['prompt'] == contract.prompt(meta) and
                request['finite_response_strings'] == list(contract.response_strings(meta)) and
                request['reference_labels_read'] is False and raw['actual_model_call'] is True and
                request['past_key_values_supplied'] is False and request['prior_outputs_supplied_as_context'] is False and
                request['prior_TIME_done_sha256'] == io.sha(io.SOURCE/'gpu_01'/current/'done.json') and
                request['prior_input_replay_sha256'] == io.sha(io.SOURCE/'replay_01'/(current+'.json')) and
                proof['input_evidence'] == old_replay['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'],
                'Paired same-input/raw/token/prior-replay identity differs')
            before,inside,after = [io.read(folder/name) for name in ('activation_before.json','activation_disabled.json','activation_after.json')]
            gradients = io.read(folder/'gradient_restoration.json')
            c.require(after['gradient_restoration_sha256'] == io.sha(folder/'gradient_restoration.json') and
                gradients['trainable_tensor_count_after_restore'] == gradients['trainable_parameters_after_restore'] == 0 and
                gradients['action'] == 'MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT' and
                before['weight_check_strategy'] == after['weight_check_strategy'] == c.WEIGHT_CHECK_STRATEGY and
                before['verified_engine_load_checkpoint_sha256'] == io.sha(gpu/'model_identity.json'),
                'Explicit post-PEFT gradient restoration/pre-call full loaded checkpoint proof differs')
            names = before['layer_state']['layer_names']
            for filename,key in [('activation_before.json','activation_before_sha256'),
                                 ('activation_disabled.json','activation_disabled_sha256'),('activation_after.json','activation_after_sha256')]:
                c.require(done[key] == io.sha(folder/filename),'Activation state SHA differs')
            c.require(raw['activation_disabled_sha256'] == io.sha(folder/'activation_disabled.json'),'Raw activation state binding differs')
            c.serialized_layer_state(before['layer_state'],False,names)
            c.serialized_layer_state(inside['layer_state'],True,names)
            c.serialized_layer_state(after['layer_state'],False,names)
            c.require(before['frozen_weights'] == after['frozen_weights'] and
                before['frozen_weights']['base'] == prior['original_model_identity']['base'] and
                before['frozen_weights']['adapter'] == prior['original_model_identity']['adapter'] and
                before['frozen_weights']['inventory'] == inside['inventory'] == after['frozen_weights']['inventory'] == model_evidence['inventory'] and
                inside['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and inside['activated_base_parameters'] == c.BASE_PARAMETERS and
                raw['actual_physical_parameters'] == c.PHYSICAL_PARAMETERS and raw['activated_base_parameters'] == c.BASE_PARAMETERS and
                after['all_144_states_restored'] is True and after['frozen_base_and_adapter_values_unchanged'] is True,
                'Independent frozen base/adapter or context restoration differs')
            encoded = oldio.load_tensor_cache(proof['encoded_tensor_path'])
            c.require(runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'],'Reused accepted CPU cache signature changed')
            transfer = io.read(folder/'gpu_input.json')
            c.require(transfer['status'] == 'PASS_UNCHANGED_CPU_GPU_TENSOR_EQUALITY' and
                      transfer['tensor_signature'] == proof['input_evidence']['tensor_signature'] and
                      transfer['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'],'Actual new CPU/GPU transfer differs')
            ids,scores = raw['output_token_ids'],raw['selected_token_scores']
            c.require(0 < len(ids) <= contract.MAX_OUTPUT_TOKENS and all(type(t) is int and t >= 0 for t in ids) and
                len(ids) == len(scores) == raw['generated_score_count'] == raw['output_tokens'] == done['output_tokens'] and
                all(type(score) in (int,float) and math.isfinite(score) for score in scores) and
                int(encoded['input_ids'].shape[1]) == raw['input_tokens'] == proof['input_tokens'] and raw['eos_token_ids'] == eos,
                'Independent real output token/score denominator differs')
            decoded = processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            constraint = grammar_module.BoundaryConstraint(processor.tokenizer,raw['input_tokens'],meta,eos,allowed)
            decision = constraint.assert_complete(ids)
            c.require(decoded == raw['raw_output'] == json.dumps(decision,separators=(',',':')) and decision == done['decision'],
                      'Independent finite raw/token parser differs')
            clock = oldio.extract_clock(oldio.read(oldio.checked_ref(meta['original_evidence']['clock'])),meta['clock_object_keys'])
            endpoint = independent.independent_endpoint(decision,meta,clock)
            c.require(endpoint == done['endpoint_result'],'Independent same revision03 native/UNKNOWN conversion differs')
            endpoints[current] = endpoint
            proofpath = out/(current+'.json')
            io.save(proofpath,dict(status='PASS_INDEPENDENT_ACTIVATION_OUTPUT_TOKEN_NATIVE_REPLAY_NOT_QUALITY',
                request_id=current,CPU_only=True,raw_sha256=io.sha(folder/'raw.json'),done_sha256=io.sha(folder/'done.json'),
                old_input_replay_sha256=request['prior_input_replay_sha256'],input_evidence=proof['input_evidence'],
                endpoint_result=endpoint,all_144_context_states_and_frozen_weights_verified=True,
                new_processor_encodes=0,new_media_decodes=0,new_model_calls=0))
            proofs.append(dict(request_id=current,proof_path=str(proofpath),proof_sha256=io.sha(proofpath)))
            comparisons.append(dict(request_id=current,original_TIME_decision=old_done['decision'],
                disabled_BASE_decision=decision,original_TIME_endpoint=old_done['endpoint_result']['endpoint_exact'],
                disabled_BASE_endpoint=endpoint['endpoint_exact'],generation_seconds=raw['generation_seconds'],
                changed_output_is_not_quality_evidence=True))
            del encoded
        c.require(not torch.cuda.is_initialized(),'CPU output replay initialized CUDA')
        io.save(out/'completion.json',dict(status='PASS_ONLY_REMAINING_END_OUTPUT_REPLAY_NOT_QUALITY',requests=len(proofs),proofs=proofs,
            resource_terminal_sha256=resource_sha,gpu_completion_sha256=io.sha(gpu/'completion.json'),CPU_only=True,CUDA_initialized=False,
            prior_successful_input_replays_reused=True,new_input_processor_encodes=0,new_media_decodes=0,new_model_calls=0,utc=io.utc()))
        io.save(io.BASE/'activation_behavior_export.json',dict(status='REMAINING_END_ACTIVATION_BEHAVIOR_ONLY_PRIOR_START_UNACCEPTED',
            comparisons=comparisons,remaining_endpoint_results=list(endpoints.values()),
            prior_start_status='UNACCEPTED_POST_STATE_PROOF',v1_failed_status_preserved=True,paired_two_case_completion=False,
            actual_physical_parameters=c.PHYSICAL_PARAMETERS,activated_base_parameters=c.BASE_PARAMETERS,
            independent_replay_completion_sha256=io.sha(out/'completion.json'),actual_gpu_seconds=resource['charged_seconds'],
            changed_output_is_not_quality_evidence=True,quality_gate_or_change_based_selection_admitted=False,
            new_model_calls=0,new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json',dict(status='FAILED_OUTPUT_REPLAY_KEEP_RAW_AND_SUCCESS_NO_FALLBACK',request_id=current,
            successful_proofs=proofs,error=repr(error),traceback=traceback.format_exc(),new_model_calls=0))
        raise


def audit_start(rootpath):
    """Read saved v1 START tokens/native metadata; never infer or accept it."""
    io.host(cpu=True)
    admission,p,cpu,rows,prior = io.verify_lock(rootpath)
    helpers = io.old_helpers(cpu['bindings']['own_code_files'])
    oldio,contract,grammar_module,independent = (helpers[name] for name in ('io','contract','grammar','replay'))
    rid = c.SOURCE_REQUEST_IDS[0]
    entry = next(row for row in cpu['proofs'] if row['request_id'] == rid)
    proof,meta = io.read(entry['proof_path']),io.read(entry['input_path'])
    folder = io.PREVIOUS/'gpu_01'/rid
    raw,request,transfer,disabled = [io.read(folder/name) for name in
        ('raw.json','request.json','gpu_input.json','activation_disabled.json')]
    old_replay = io.read(io.SOURCE/'replay_01'/(rid+'.json'))
    c.require(raw['actual_model_call'] is True and request['input_sha256'] == proof['input_sha256'] and
        request['CPU_proof_sha256'] == entry['proof_sha256'] and request['prompt'] == meta['prompt'] == contract.prompt(meta) and
        proof['input_evidence'] == raw['input_evidence'] == request['input_evidence'] == old_replay['input_evidence'] and
        transfer['tensor_signature'] == proof['input_evidence']['tensor_signature'] and
        transfer['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
        raw['activation_disabled_sha256'] == io.sha(folder/'activation_disabled.json'),
        'Saved unaccepted START same-input/actual raw evidence differs')
    c.serialized_layer_state(disabled['layer_state'],True)
    out = io.BASE/'prior_start_audit_01'
    out.mkdir(exist_ok=False)
    try:
        import torch
        runtime,processor,identity = oldio.cpu_runtime()
        c.require(identity == cpu['bindings']['original_b_processor_runtime'],'Read-only tokenizer assets changed')
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        eos = io.read(Path(config['model_dir'])/'generation_config.json')['eos_token_id']
        eos = [eos] if isinstance(eos,int) else list(eos)
        ids,scores = raw['output_token_ids'],raw['selected_token_scores']
        c.require(0 < len(ids) <= contract.MAX_OUTPUT_TOKENS and
            all(type(token) is int and token >= 0 for token in ids) and
            len(ids) == len(scores) == raw['output_tokens'] == raw['generated_score_count'] and
            all(type(score) in (float,int) and math.isfinite(score) for score in scores) and
            raw['input_tokens'] == proof['input_tokens'] and raw['eos_token_ids'] == eos,
            'Saved START real token/finite score denominator differs')
        decoded = processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        allowed = grammar_module.candidates(processor.tokenizer,contract.response_strings(meta))
        constraint = grammar_module.BoundaryConstraint(processor.tokenizer,raw['input_tokens'],meta,eos,allowed)
        decision = constraint.assert_complete(ids)
        c.require(decoded == raw['raw_output'] == json.dumps(decision,separators=(',',':')),'Saved START raw/token finite grammar differs')
        clock = oldio.extract_clock(oldio.read(oldio.checked_ref(meta['original_evidence']['clock'])),meta['clock_object_keys'])
        diagnostic_endpoint = independent.independent_endpoint(decision,meta,clock)
        c.require(not torch.cuda.is_initialized(),'Read-only START audit initialized CUDA')
        io.save(out/'audit.json',dict(status='UNACCEPTED_POST_STATE_PROOF',request_id=rid,
            saved_raw_sha256=io.sha(folder/'raw.json'),prior_failure_sha256=io.sha(io.PREVIOUS/'gpu_01/failure.json'),
            output_token_decode_grammar_native_audit_passed=True,raw_decision=decision,
            diagnostic_only_unaccepted_native_conversion=diagnostic_endpoint,accepted_endpoint_result=None,
            missing_post_context_frozen_gradient_and_weights_proof=True,accepted_model_calls_added=0,
            old_v1_failed_status_preserved=True,CPU_only=True,new_input_processor_encodes=0,
            new_media_decodes=0,new_model_calls=0,quality_claim=False,utc=io.utc()))
    except BaseException as error:
        io.save(out/'failure.json',dict(status='FAILED_READ_ONLY_START_AUDIT_KEEP_PRIOR_RAW',error=repr(error),
            traceback=traceback.format_exc(),new_model_calls=0,accepted_model_calls_added=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--stage',choices=('admit','infer','replay','audit-start'),required=True)
    args = parser.parse_args()
    if args.stage in ('admit','replay','audit-start'):
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    {'admit':io.admit,'infer':infer,'replay':replay,'audit-start':audit_start}[args.stage](args.root)
