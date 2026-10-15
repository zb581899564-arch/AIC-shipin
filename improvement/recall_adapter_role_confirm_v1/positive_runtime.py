"""Immutable new prompt tokens, pre-GPU first input QA, one call, output-only QA."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback

import positive_contract as c
import positive_grammar as grammar_module
import positive_io as io


def base(root, group):
    return root/group/'POSITIVE'


def failure(out, stage, error, **values):
    io.save(out/'failure.json', dict(status='FAILED_POSITIVE_BLOCK_NO_REPAIR_OR_FALLBACK',
        stage=stage, error=repr(error), traceback=traceback.format_exc(),
        preserve_all_old_and_new_success=True, do_not_repeat_success=True,
        implicit_resume=False, UNKNOWN_fallback=False, production_admitted=False, **values))


def prepare(root, group):
    io.host(cpu=True)
    reg, _, reg_path = io.registration(root, group)
    adopted = io.adopted(root, group, reg)
    out = base(root, group)/'cpu_01'; out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(),
        registration_ref=io.ref(reg_path), CPU_only=True, new_model_calls=0,
        old_model_calls_repeated=0, old_QA_repeated=0, vision_processor_calls=0, media_decodes=0))
    current, entries = None, []
    try:
        requests = adopted['requests']
        io.save(out/'requests.json', requests)
        io.save(out/'denominator.json', dict(source_names=adopted['source_names'],
            old_event_count=len(adopted['events']), actual_new_call_count=len(requests),
            complete_old_event_audit=adopted['denominator_audit'],
            native_baseline_subset_is_the_only_no_effect_skip=True,
            reference_labels_read=False, selection_by_reference=False))
        legacy = io.legacy(reg); token_module = io.tokens_module(reg)
        if requests:
            runtime, processor = legacy.cpu_processor()
        for req in requests:
            current = req['request_id']; folder = out/current; folder.mkdir(exist_ok=False)
            original = legacy.load_cache(io.checked(req['original_vision_cache_path'], req['original_vision_cache_sha256']))
            io.require(runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'],
                       'Original independently accepted vision/input cache differs')
            tokens, combined, evidence = token_module.retarget(original, processor.tokenizer,
                runtime.EMPTY_PROMPT, req['prompt'], runtime.tensor_signature)
            path = folder/'prompt_tokens.pt.gz'; legacy.save_cache(path, tokens)
            restored = legacy.load_cache(path)
            io.require(runtime.tensor_signature(restored) == runtime.tensor_signature(tokens), 'Lossless new prompt tokens failed reload')
            actual_evidence = dict(req['original_input_evidence'], case_id=current,
                original_case_id=req['original_case_id'], prompt_sha256=hashlib.sha256(req['prompt'].encode()).hexdigest(),
                input_tokens=evidence['input_tokens'], tensor_signature=evidence['full_tensor_signature'],
                unchanged_vision_tensor_signature=evidence['unchanged_vision_tensor_signature'],
                vision_processor_calls=0, media_decodes=0, prompt_tokens_only_new=True)
            input_path, proof_path = folder/'input.json', folder/'cpu_input.json'
            actual = dict(req, input_evidence=actual_evidence, retarget_evidence=evidence,
                token_cache_path=str(path), token_cache_sha256=io.sha(path), token_cache_format=legacy.CACHE_FORMAT)
            io.save(input_path, actual)
            io.save(proof_path, dict(status='PASS_POSITIVE_NEW_PROMPT_TOKENS_PREPARED',
                case_id=current, group=group, input_ref=io.ref(input_path), token_cache_ref=io.ref(path),
                input_evidence=actual_evidence, retarget_evidence=evidence,
                CPU_only=True, CUDA_initialized=False, new_model_calls=0,
                new_optimizer_updates=0, vision_processor_calls=0, media_decodes=0))
            entries.append(dict(case_id=current, input_ref=io.ref(input_path), preparation_ref=io.ref(proof_path)))
            print(json.dumps(dict(stage='POSITIVE_PREPARE', prepared=len(entries), expected=len(requests))), flush=True)
            del tokens, original, combined, restored
        import torch
        io.require(not torch.cuda.is_initialized(), 'Prompt preparation initialized CUDA')
        io.save(out/'completion.json', dict(status=io.CPU_STATUS, group=group,
            entries=entries, expected_input_count=len(entries), registration_ref=io.ref(reg_path),
            requests_ref=io.ref(out/'requests.json'), denominator_ref=io.ref(out/'denominator.json'),
            adopted_files=adopted['adopted_files'], code_files=io.code_files(),
            CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0,
            media_decodes=0, vision_processor_calls=0, old_QA_repeated=0))
    except BaseException as error:
        failure(out, 'NEW_PROMPT_PREPARATION', error, current=current, successful_entries=entries)
        raise


def prepared(root, group, reg):
    out = base(root, group)/'cpu_01'; completion = io.read(out/'completion.json')
    io.require(completion['status'] == io.CPU_STATUS and completion['group'] == group and
        completion['expected_input_count'] == len(completion['entries']) and
        completion['code_files'] == io.code_files() and completion['CPU_only'] is True and
        completion['CUDA_initialized'] is False and completion['media_decodes'] == completion['vision_processor_calls'] ==
        completion['new_model_calls'] == completion['new_optimizer_updates'] == completion['old_QA_repeated'] == 0,
        'Complete actual new prompt-only preparation required')
    reg_path = root/('registration.json' if group == 'dev' else 'registration_confirm.json')
    io.require(io.checked_ref(completion['registration_ref']) == reg_path, 'Preparation registration changed')
    requests = io.read(io.checked_ref(completion['requests_ref']))
    current_adoption = io.adopted(root, group, reg)
    io.require(requests == current_adoption['requests'] and completion['adopted_files'] == current_adoption['adopted_files'],
               'Full deterministic old-KEEP denominator or immutable prior evidence changed')
    io.checked_ref(completion['denominator_ref'])
    io.require([e['case_id'] for e in completion['entries']] == [r['request_id'] for r in requests], 'Prepared request denominator/order differs')
    values = []
    for entry, planned in zip(completion['entries'], requests):
        req = io.read(io.checked_ref(entry['input_ref']))
        proof = io.read(io.checked_ref(entry['preparation_ref']))
        io.require(all(req[key] == value for key, value in planned.items()) and req['prompt'] == c.prompt(req), 'Exact new prompt/request changed')
        io.require(proof['input_ref'] == entry['input_ref'] and proof['input_evidence'] == req['input_evidence'] and
            proof['status'] == 'PASS_POSITIVE_NEW_PROMPT_TOKENS_PREPARED' and proof['case_id'] == entry['case_id'] == req['request_id'],
            'Prepared actual input/cache evidence differs')
        io.require(proof['token_cache_ref'] == dict(path=req['token_cache_path'], sha256=req['token_cache_sha256']), 'New token cache binding differs')
        io.checked_ref(proof['token_cache_ref'])
        values.append((entry, req, proof))
    return completion, values


def independent_tokens(original, tokenizer, original_prompt, prompt, signature, vision_keys):
    """First independent token construction uses partition + encode, not retarget."""
    import torch
    text = tokenizer.decode(original['input_ids'][0].tolist(), skip_special_tokens=False,
                            clean_up_tokenization_spaces=False)
    before, marker, after = text.partition(original_prompt)
    io.require(marker == original_prompt and original_prompt not in after, 'Original prompt partition not unique')
    expanded = before+prompt+after
    ids = tokenizer.encode(expanded, add_special_tokens=False)
    new_ids = torch.tensor([ids], dtype=original['input_ids'].dtype, device='cpu')
    tokens = dict(input_ids=new_ids, attention_mask=torch.ones(new_ids.shape,
        dtype=original['attention_mask'].dtype, device='cpu'))
    # Implement the original expanded visual-prefix observation independently.
    end_id = tokenizer.convert_tokens_to_ids('<|vision_end|>')
    pad_id = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    def prefix(value):
        sequence = value[0].tolist(); endings = [i for i, token in enumerate(sequence) if token == end_id]
        io.require(endings and pad_id in sequence, 'Independent native expanded visual block missing')
        data = value[:, :endings[-1]+1]
        return data, dict(tokens=int(data.shape[1]),
            sha256=hashlib.sha256(data.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest(),
            vision_end_count=len(endings), video_pad_count=sequence.count(pad_id))
    old_prefix, old_evidence = prefix(original['input_ids']); new_prefix, new_evidence = prefix(new_ids)
    io.require(torch.equal(old_prefix, new_prefix) and old_evidence == new_evidence,
               'Independent new text changed native timestamps/expanded visual prefix')
    io.require(0 < len(ids) <= c.MAX_INPUT_TOKENS, 'Independent actual new input token budget exceeded')
    combined = {**tokens, **{key: original[key] for key in vision_keys}}
    return tokens, combined, dict(original_expanded_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        new_expanded_text_sha256=hashlib.sha256(expanded.encode()).hexdigest(), vision_prefix=old_evidence,
        unchanged_vision_tensor_signature=signature({key: original[key] for key in vision_keys}),
        full_tensor_signature=signature(combined), input_tokens=len(ids))


def input_qa(root, group):
    io.host(cpu=True); reg, _, reg_path = io.registration(root, group)
    completion, values = prepared(root, group, reg)
    out = base(root, group)/'input_qa_01'; out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(),
        CPU_only=True, first_independent_new_prompt_input_QA=True,
        preparation_completion_ref=io.ref(base(root, group)/'cpu_01/completion.json'),
        old_first_input_QA_purely_adopted=True, media_decodes=0, vision_processor_calls=0))
    current, proofs = None, []
    try:
        legacy = io.legacy(reg); token_module = io.tokens_module(reg)
        if values:
            runtime, processor = legacy.cpu_processor()
        io.require(io.read(base(root, group)/'cpu_01/launch_claim.json')['pid'] != os.getpid(),
                   'First new-token input QA must run in a distinct process')
        for entry, req, proof in values:
            current = entry['case_id']
            original = legacy.load_cache(io.checked(req['original_vision_cache_path'], req['original_vision_cache_sha256']))
            cached = legacy.load_cache(req['token_cache_path'])
            io.require(runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'], 'Old first-QA-admitted vision cache changed')
            tokens, combined, observed = independent_tokens(original, processor.tokenizer, runtime.EMPTY_PROMPT,
                req['prompt'], runtime.tensor_signature, token_module.VISION_KEYS)
            io.require(runtime.tensor_signature(tokens) == runtime.tensor_signature(cached) and
                all(proof['retarget_evidence'][key] == value for key, value in observed.items()) and
                runtime.tensor_signature(combined) == req['input_evidence']['tensor_signature'],
                'First independent actual new prompt-token input QA failed')
            path = out/(current+'.json')
            io.save(path, dict(status=io.QA_STATUS, case_id=current, group=group,
                input_ref=entry['input_ref'], preparation_ref=entry['preparation_ref'],
                token_cache_ref=proof['token_cache_ref'], original_vision_cache_ref=dict(
                    path=req['original_vision_cache_path'], sha256=req['original_vision_cache_sha256']),
                original_first_input_QA_ref=req['original_evidence']['old_input_QA'],
                input_evidence=req['input_evidence'], independent_token_evidence=observed,
                CPU_only=True, CUDA_initialized=False, media_decodes=0, vision_processor_calls=0,
                actual_new_prompt_input_QA=1, old_QA_repeated=0, new_model_calls=0))
            proofs.append(dict(case_id=current, proof_ref=io.ref(path)))
            print(json.dumps(dict(stage='POSITIVE_FIRST_INPUT_QA', completed=len(proofs), expected=len(values))), flush=True)
            del original, cached, tokens, combined
        import torch
        io.require(not torch.cuda.is_initialized(), 'First new-input QA initialized CUDA')
        io.save(out/'completion.json', dict(status=io.QA_STATUS, group=group, proofs=proofs,
            calls=len(proofs), preparation_completion_ref=io.ref(base(root, group)/'cpu_01/completion.json'),
            registration_ref=io.ref(reg_path), CPU_only=True, CUDA_initialized=False,
            media_decodes=0, vision_processor_calls=0, old_QA_repeated=0, new_model_calls=0,
            new_optimizer_updates=0, actual_first_independent_new_prompt_input_QA=len(proofs)))
    except BaseException as error:
        failure(out, 'FIRST_NEW_PROMPT_INPUT_QA_PRE_GPU', error, current=current, successful_proofs=proofs)
        raise


def qa_accepted(root, group, reg):
    complete, values = prepared(root, group, reg)
    qa_path = base(root, group)/'input_qa_01/completion.json'; qa = io.read(qa_path)
    io.require(qa['status'] == io.QA_STATUS and qa['group'] == group and
        qa['calls'] == qa['actual_first_independent_new_prompt_input_QA'] == len(values) == len(qa['proofs']) and
        qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
        qa['media_decodes'] == qa['vision_processor_calls'] == qa['new_model_calls'] == qa['old_QA_repeated'] == 0 and
        qa['preparation_completion_ref'] == io.ref(base(root, group)/'cpu_01/completion.json'),
        'Complete first independent actual new input QA before GPU required')
    io.require([e['case_id'] for e in qa['proofs']] == [e['case_id'] for e, _, _ in values], 'First QA full ordered denominator differs')
    for row, (entry, req, _) in zip(qa['proofs'], values):
        proof = io.read(io.checked_ref(row['proof_ref']))
        io.require(proof['status'] == io.QA_STATUS and proof['input_ref'] == entry['input_ref'] and
                   proof['input_evidence'] == req['input_evidence'], 'First new input QA binding changed')
    return complete, qa, values


def admit(root, group):
    io.host(cpu=True); reg, _, reg_path = io.registration(root, group)
    complete, qa, values = qa_accepted(root, group, reg)
    legacy = io.legacy(reg); budget = reg['gpu_budget'][group]
    io.require(len(values) <= budget['max_actual_calls'], 'Frozen actual candidate denominator exceeds new budget')
    dependencies = legacy.runtime_dependencies() | legacy.processor_assets() | {str(legacy.CONFIG)}
    io.require(dependencies <= set(reg['required_files']), 'Actual runtime/processor/config dependency closure must be registered before work')
    files = dict(reg['required_files']); files.update(complete['adopted_files'])
    def add(path, digest=None):
        path = io.checked(path, digest); actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Frozen source/input dependency changed')
        files[str(path)] = actual
    add(reg_path); add(reg['protocol_ref']['path'], reg['protocol_ref']['sha256'])
    add(reg['authorization_ref']['path'], reg['authorization_ref']['sha256'])
    for path in (base(root, group)/'cpu_01/completion.json', base(root, group)/'cpu_01/requests.json',
                 base(root, group)/'cpu_01/denominator.json', base(root, group)/'input_qa_01/completion.json'):
        add(path)
    for entry, req, proof in values:
        for value in (entry['input_ref'], entry['preparation_ref'], proof['token_cache_ref']):
            add(value['path'], value['sha256'])
    for row in qa['proofs']:
        add(row['proof_ref']['path'], row['proof_ref']['sha256'])
    lock_path = root/('source_lock_'+group+'_POSITIVE.json')
    io.save(lock_path, dict(status='FROZEN_POSITIVE_SOURCE_CODE_INPUT_LOCK', group=group, files=files, utc=io.utc()))
    io.require(not (io.RUN/'controller'/(budget['gpu_job_name']+'.resource.json')).exists(),
               'New job already has terminal evidence; no repeated call')
    gate = dict(status=io.ADMISSION_STATUS, group=group, stage='POSITIVE',
        expected_input_count=len(values), gpu_job_name=budget['gpu_job_name'], max_seconds=budget['max_seconds'],
        deadline=budget['deadline'], registration_ref=io.ref(reg_path), source_lock_ref=io.ref(lock_path),
        cpu_completion_ref=io.ref(base(root, group)/'cpu_01/completion.json'),
        first_input_QA_ref=io.ref(base(root, group)/'input_qa_01/completion.json'),
        model_parameters=c.MODEL_PARAMETERS, optimizer_updates=0, source_scope='EXTERNAL_NONTEST_ONLY',
        reference_available_to_inference=False, production_admitted=False,
        zero_candidates_require_no_gpu_job=not values)
    io.save(root/('gpu_admission_'+group+'_POSITIVE.json'), gate)


def accepted(root, group):
    reg, _, reg_path = io.registration(root, group)
    gate_path = root/('gpu_admission_'+group+'_POSITIVE.json'); gate = io.read(gate_path)
    complete, qa, values = qa_accepted(root, group, reg)
    io.require(gate['status'] == io.ADMISSION_STATUS and gate['group'] == group and gate['stage'] == 'POSITIVE' and
        gate['registration_ref'] == io.ref(reg_path) and gate['cpu_completion_ref'] == io.ref(base(root, group)/'cpu_01/completion.json') and
        gate['first_input_QA_ref'] == io.ref(base(root, group)/'input_qa_01/completion.json') and
        gate['expected_input_count'] == len(values) and gate['model_parameters'] == c.MODEL_PARAMETERS and
        gate['reference_available_to_inference'] is False and gate['production_admitted'] is False,
        'Independent first-input-QA-bound new GPU admission differs')
    io.validate_lock(io.checked_ref(gate['source_lock_ref']), set(io.code_files()) | {str(reg_path)})
    legacy = io.legacy(reg); runtime = legacy.runtime_only(); tm = io.tokens_module(reg)
    # Inspect every accepted actual cache before any model is loaded. This
    # checks saved signatures only, never repeats the independent token encode.
    for _, req, _ in values:
        tokens = legacy.load_cache(req['token_cache_path']); original = legacy.load_cache(req['original_vision_cache_path'])
        io.require(set(tokens) == set(tm.TOKEN_KEYS) and set(original) == set(tm.TOKEN_KEYS+tm.VISION_KEYS), 'Actual cache keys changed')
        combined = {**tokens, **{key: original[key] for key in tm.VISION_KEYS}}
        io.require(runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'] and
            runtime.tensor_signature(combined) == req['input_evidence']['tensor_signature'] and
            runtime.tensor_signature({key: original[key] for key in tm.VISION_KEYS}) == req['input_evidence']['unchanged_vision_tensor_signature'] and
            0 < int(combined['input_ids'].shape[1]) == req['input_evidence']['input_tokens'] <= c.MAX_INPUT_TOKENS,
            'Actual complete accepted token/vision cache differs')
        del tokens, original, combined
    return reg, gate, gate_path, values


def infer(root, group):
    io.host(cpu=False); reg, gate, gate_path, values = accepted(root, group)
    io.require(values, 'Zero candidates require no GPU model load or job')
    legacy = io.legacy(reg); legacy.deadline(gate); legacy.gpu_reservation(gate)
    runtime = legacy.runtime_only(); tm = io.tokens_module(reg)
    role = io.load_module('_frozen_role_dev_runtime', reg['role_runtime_ref']); ac = role.activation_contract(reg, io)
    import torch
    out = base(root, group)/'gpu_01'; out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group,
        admission_ref=io.ref(gate_path), expected_input_count=len(values),
        old_model_calls_repeated=0, new_optimizer_updates=0, parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES']))
    with (out/'attempts.jsonl').open('x'):
        pass
    current, begun, entries = None, 0, []
    try:
        config = io.read(legacy.CONFIG); model, processor, identity = runtime.b_engine.load_model(config)
        legacy.verify_model(model, identity)
        initial = ac.layer_state(model, False); names = initial['layer_names']; ac.inventory(model); ac.frozen_gradients(model)
        io.save(out/'model_identity.json', dict(identity=identity, initial=initial, activation_role=role.ROLE, adapter_enabled_for_all_calls=False, physical_parameters=role.PARAMETERS, optimizer_updates=0))
        eos = legacy.eos_ids(model); candidates = grammar_module.candidate_tokens(processor.tokenizer, c.responses())
        for entry, req, _ in values:
            current = entry['case_id']; folder = out/current; folder.mkdir(exist_ok=False)
            tokens = legacy.load_cache(req['token_cache_path']); original = legacy.load_cache(req['original_vision_cache_path'])
            combined = {**tokens, **{key: original[key] for key in tm.VISION_KEYS}}
            gpu = {key: value.to('cuda') for key, value in combined.items()}
            evidence = req['input_evidence']; prefix = int(gpu['input_ids'].shape[1])
            io.require(runtime.tensor_signature(combined) == runtime.tensor_signature(gpu) == evidence['tensor_signature'],
                       'Actual CPU/GPU input equality failed')
            before = dict(layer_state=ac.layer_state(model, False, names), gradients=ac.frozen_gradients(model))
            io.save(folder/'activation_before.json', before)
            grammar = grammar_module.PositiveConstraint(processor.tokenizer, prefix, req, eos, candidates)
            io.save(folder/'request.json', dict(case_id=current, input_ref=entry['input_ref'],
                first_input_QA_completion_ref=gate['first_input_QA_ref'], prompt=req['prompt'],
                original_interval_exact=req['original_interval_exact'], input_evidence=evidence,
                allowed_responses=c.responses(req), reference_labels_read=False, audio_observed=False))
            begun += 1; io.append(out/'attempts.jsonl', dict(event='BEGIN', case_id=current, call_id=begun, utc=io.utc()))
            started = time.monotonic()
            try:
                with model.disable_adapter():
                    inside = dict(layer_state=ac.layer_state(model, True, names), gradients=ac.frozen_gradients(model))
                    io.save(folder/'activation_inside.json', inside)
                    with torch.inference_mode():
                        generated = model.generate(**gpu, do_sample=False, max_new_tokens=c.MAX_OUTPUT_TOKENS,
                            prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
                    torch.cuda.synchronize(); ac.layer_state(model, True, names); ac.frozen_gradients(model)
            finally:
                restored = ac.restore_frozen_gradients(model)
                after = dict(layer_state=ac.layer_state(model, False, names), gradients=ac.frozen_gradients(model))
                io.save(folder/'activation_after.json', dict(after=after, restored=restored))
            ac.validate_restoration(before, inside, after, restored, names)
            disabled = inside['layer_state']['disable_adapters']
            ids = generated.sequences[0, prefix:]
            text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
            io.save(folder/'raw.json', dict(raw_output=text, output_token_ids=ids.tolist(),
                selected_token_scores=[score if math.isfinite(score) else str(score) for score in scores],
                generated_score_count=len(generated.scores), output_tokens=len(ids), input_tokens=prefix,
                generation_seconds=time.monotonic()-started, eos_token_ids=eos, actual_model_call=True,
                input_evidence=evidence, adapter_disabled_layers=disabled, constraint_stats=grammar.stats, activation_role=role.ROLE, actual_physical_parameters=role.PARAMETERS, activated_base_parameters=role.BASE_PARAMETERS))
            role.role_output(io.read(folder/'raw.json'))
            parsed = grammar.assert_complete(ids)
            io.require(json.dumps(parsed, separators=(',', ':')) == text, 'Generated token/canonical raw mismatch; no repair')
            result = c.resolve(text, req, execution_status='MODEL_OK')
            io.save(folder/'done.json', dict(status='PASS_POSITIVE_DECISION_NOT_QUALITY', case_id=current,
                group=group, decision_result=result, raw_ref=io.ref(folder/'raw.json'),
                request_ref=io.ref(folder/'request.json'), activation_before_ref=io.ref(folder/'activation_before.json'), activation_inside_ref=io.ref(folder/'activation_inside.json'), activation_after_ref=io.ref(folder/'activation_after.json'), input_evidence=evidence, input_tokens=prefix,
                output_tokens=len(ids), optimizer_updates=0))
            receipt = dict(case_id=current, done_ref=io.ref(folder/'done.json'))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED', call_id=begun, utc=io.utc(), **receipt)); entries.append(receipt)
            print(json.dumps(dict(stage='POSITIVE', accepted=len(entries), expected=len(values), decision=result['decision'])), flush=True)
            del tokens, original, combined, gpu, generated, ids
        io.require(begun == len(entries) == len(values), 'Unique actual complete new call denominator failed')
        io.require(runtime.b_engine.frozen_identity(model, config) == identity['base'] and
            runtime.b_engine.adapter_identity(model, config) == identity['adapter'], 'Actual base/adapter changed during calls')
        io.save(out/'completion.json', dict(status=io.GPU_STATUS, group=group, calls=begun, entries=entries,
            admission_ref=io.ref(gate_path), attempts_ref=io.ref(out/'attempts.jsonl'),
            model_identity_ref=io.ref(out/'model_identity.json'), model_parameters=c.MODEL_PARAMETERS,
            old_model_calls_repeated=0, new_optimizer_updates=0))
    except BaseException as error:
        failure(out, 'UNIQUE_POSITIVE_GPU_CALLS', error, current=current, begun=begun, successful_entries=entries)
        raise


def completed(root, group, reg, gate, gate_path, values):
    out = base(root, group)/'gpu_01'; complete = io.read(out/'completion.json')
    io.require(complete['status'] == io.GPU_STATUS and complete['group'] == group and
        complete['calls'] == len(complete['entries']) == len(values) and complete['admission_ref'] == io.ref(gate_path),
        'Complete actual new model stage required')
    identity = io.read(io.checked_ref(complete['model_identity_ref']))
    io.legacy(reg).verify_identity(identity['identity'])
    journal = io.rows(io.checked_ref(complete['attempts_ref']))
    io.require(len(journal) == 2*len(values) and [e['case_id'] for e in complete['entries']] == [e['case_id'] for e, _, _ in values],
               'Complete unique actual new call order/attempt denominator differs')
    for index, receipt in enumerate(complete['entries'], 1):
        first, last = journal[2*(index-1):2*index]
        io.require(first['event'] == 'BEGIN' and last['event'] == 'ACCEPTED' and
            first['call_id'] == last['call_id'] == index and first['case_id'] == last['case_id'] == receipt['case_id'] and
            last['done_ref'] == receipt['done_ref'], 'Actual unique BEGIN/ACCEPTED journal changed')
        io.require(io.checked_ref(receipt['done_ref']) == out/receipt['case_id']/'done.json', 'Accepted output escaped its case')
    return complete


def independent_result(req, text):
    """Independent finite parser/native observation, not infer's resolver."""
    meta = io.read(io.checked_ref(req['original_evidence']['input']))
    done = io.read(io.checked_ref(req['original_evidence']['done']))
    old_verify = io.read(io.checked_ref(req['original_evidence']['old_VERIFY_done']))
    interval = [str(c.exact(meta['window_start'])+c.exact(value))
                for value in done['segments'][req['original_segment_index']]]
    io.require(interval == req['original_interval_exact'] and meta['case_id'] == req['original_case_id'] and
        old_verify['decision_result']['decision'] == 'KEEP' and
        old_verify['decision_result']['original_interval_exact'] == interval and
        meta['source_sha256'] == req['source_sha256'], 'Independent immutable candidate/oldKEEP binding differs')
    first, last = map(c.exact, interval)
    observed = sum(first <= c.exact(p) < last for p in meta['sample_exact_pts'])
    decisions = ('KEEP', 'UNKNOWN', 'DROP') if all(req['novel_visible_sample_counts']) else ('UNKNOWN', 'DROP')
    io.require(tuple(req['allowed_decisions']) == decisions and observed == req['candidate_visible_sample_count'] > 0 and
        text in tuple('{"decision":"'+value+'"}' for value in decisions),
        'Independent canonical parser/actual shown sampling gate failed')
    value = json.loads(text)['decision']
    result = dict(event_id=req['event_id'], request_id=req['request_id'], old_event_id=req['old_event_id'],
        original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
        source_sha256=req['source_sha256'], original_interval_exact=interval, decision=value,
        eligible_for_new_addition=value == 'KEEP', admitted_interval_exact=interval if value == 'KEEP' else None,
        boundaries_changed=False, new_candidate_created=False, baseline_deletion_authorized=False,
        uncertainty_is_ordinary_truth=False, successful_model_call_required=True)
    members = [i for i, point in enumerate(map(c.exact, meta['all_source_exact_pts'])) if first <= point < last]
    io.require(members and members == list(range(members[0], members[-1]+1)), 'Independent native membership invalid')
    return result, [members[0], members[-1]+1]


def replay(root, group):
    io.host(cpu=True); reg, gate, gate_path, values = accepted(root, group)
    resource, resource_sha = io.terminal(gate)
    complete = completed(root, group, reg, gate, gate_path, values)
    out = base(root, group)/'output_qa_01'; out.mkdir(exist_ok=False)
    gpu = base(root, group)/'gpu_01'
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        first_input_QA_purely_referenced=True, no_input_token_reencode=True,
        resource_terminal_sha256=resource_sha, gpu_completion_ref=io.ref(gpu/'completion.json'),
        media_decodes=0, vision_processor_calls=0, new_model_calls=0))
    current, proofs, events = None, [], []
    try:
        legacy = io.legacy(reg)
        role = io.load_module('_frozen_role_dev_runtime', reg['role_runtime_ref']); ac = role.activation_contract(reg, io)
        model_meta = io.read(io.checked_ref(complete['model_identity_ref'])); names = model_meta['initial']['layer_names']
        ac.serialized_state(model_meta['initial'], False, names)
        runtime, processor = legacy.cpu_processor()
        generation = io.read(Path(io.read(legacy.CONFIG)['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']; eos = [eos] if isinstance(eos, int) else list(eos)
        candidates = grammar_module.candidate_tokens(processor.tokenizer, c.responses())
        for receipt, (entry, req, _) in zip(complete['entries'], values):
            current = entry['case_id']; folder = gpu/current
            done = io.read(io.checked_ref(receipt['done_ref']))
            raw = io.read(io.checked_ref(done['raw_ref'])); request = io.read(io.checked_ref(done['request_ref']))
            io.require(done['status'] == 'PASS_POSITIVE_DECISION_NOT_QUALITY' and done['case_id'] == current and
                request['input_ref'] == entry['input_ref'] and request['first_input_QA_completion_ref'] == gate['first_input_QA_ref'] and
                request['prompt'] == req['prompt'] == c.prompt(req) and request['reference_labels_read'] is False and
                request['audio_observed'] is False and request['input_evidence'] == req['input_evidence'] ==
                raw['input_evidence'] == done['input_evidence'], 'Actual unchanged raw/request/firstQA input binding failed')
            before = io.read(io.checked_ref(done['activation_before_ref'])); inside = io.read(io.checked_ref(done['activation_inside_ref'])); after = io.read(io.checked_ref(done['activation_after_ref']))
            ac.validate_restoration(before, inside, after['after'], after['restored'], names)
            ids = role.role_output(raw, done)
            io.require(raw['input_tokens'] == done['input_tokens'] == req['input_evidence']['input_tokens'] and raw['eos_token_ids'] == eos,
                       'Actual output input/EOS denominator differs')
            text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            io.require(text == raw['raw_output'], 'Independent output-token decoding changed actual raw')
            grammar = grammar_module.PositiveConstraint(processor.tokenizer, raw['input_tokens'], req, eos, candidates)
            parsed = grammar.assert_complete(ids)
            io.require(json.dumps(parsed, separators=(',', ':')) == text, 'Independent complete grammar failed')
            decision, native = independent_result(req, text)
            io.require(decision == done['decision_result'], 'Independent finite parser/native result differs')
            path = out/(current+'.json')
            io.save(path, dict(status='PASS_INDEPENDENT_POSITIVE_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA',
                case_id=current, group=group, done_ref=receipt['done_ref'], raw_ref=done['raw_ref'],
                first_input_QA_completion_ref=gate['first_input_QA_ref'], decision_result=decision,
                original_native_range=native, CPU_only=True, media_decodes=0,
                vision_processor_calls=0, input_token_reencodes=0, new_model_calls=0))
            proofs.append(dict(case_id=current, proof_ref=io.ref(path)))
            events.append(dict(source_name=req['source_name'], source_sha256=req['source_sha256'],
                event_id=req['event_id'], old_event_id=req['old_event_id'], original_case_id=req['original_case_id'],
                original_segment_index=req['original_segment_index'], original_interval_exact=req['original_interval_exact'],
                original_native_range=native, decision_result=decision))
            print(json.dumps(dict(stage='POSITIVE_OUTPUT_QA', completed=len(proofs), expected=len(values))), flush=True)
        import torch
        io.require(not torch.cuda.is_initialized(), 'Output-only independent QA initialized CUDA')
        io.save(out/'completion.json', dict(status=io.REPLAY_STATUS, group=group, calls=len(proofs), proofs=proofs,
            gpu_completion_ref=io.ref(gpu/'completion.json'), first_input_QA_completion_ref=gate['first_input_QA_ref'],
            resource_terminal_sha256=resource_sha, CPU_only=True, CUDA_initialized=False,
            media_decodes=0, vision_processor_calls=0, input_token_reencodes=0, new_model_calls=0,
            new_optimizer_updates=0))
        io.save(base(root, group)/'verification_export.json', dict(status=io.EXPORT_STATUS, group=group,
            events=events, output_QA_completion_ref=io.ref(out/'completion.json'),
            model_parameters=c.MODEL_PARAMETERS, old_model_calls_repeated=0,
            new_additions_require_explicit_KEEP=True, UNKNOWN_does_not_add=True,
            reference_labels_read=False, production_admitted=False))
    except BaseException as error:
        failure(out, 'OUTPUT_ONLY_FIRST_QA', error, current=current, successful_proofs=proofs)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'input_qa', 'admit', 'infer', 'replay'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    args = parser.parse_args()
    if args.stage != 'infer':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    globals()[args.stage](io.root_path(args.root), args.group)


if __name__ == '__main__':
    main()
