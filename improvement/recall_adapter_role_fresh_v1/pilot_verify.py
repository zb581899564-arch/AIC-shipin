"""Prompt-only VERIFY preparation, unique inference, and independent CPU replay.

All candidates come from the accepted B0 raw segments. Neither D8 padding nor
an output repair is applied. New additions may use only explicit KEEP decisions.
"""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback

import model_common as io

CPU_STATUS = 'PASS_ALL_RECALL_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION'


def b0_replayed(root, group, values, gate, gate_path):
    gpu, replay = root/group/'B0/gpu_01', root/group/'B0/replay_01'
    _, terminal_sha = io.terminal(gate)
    complete, by_id = io.completed_job(gpu, gate, gate_path, len(values), 'B0')
    replay_complete = io.read(replay/'completion.json')
    io.require(replay_complete['status'] == 'PASS_ALL_RECALL_B0_INDEPENDENT_REPLAYS_NOT_QUALITY' and
        replay_complete['group'] == group and replay_complete['CPU_only'] is True and replay_complete['CUDA_initialized'] is False and
        replay_complete['calls'] == len(values) and replay_complete['gpu_completion_sha256'] == io.sha(gpu/'completion.json') and
        replay_complete['resource_terminal_sha256'] == terminal_sha and replay_complete['new_model_calls'] == 0,
        'First independent complete B0 replay required before any VERIFY preparation')
    replay_by_id = {e['case_id']: e for e in replay_complete['proofs']}
    io.require(list(by_id) == [e['case_id'] for e, _, _ in values] and set(replay_by_id) == set(by_id), 'Complete unique B0 replay denominator changed')
    return gpu, replay, by_id, replay_by_id


def prepare(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=True)
    gate, cpu, files, values, gate_path, actual_cpu_path, actual_lock_path = io.accepted_b0(root, group, cpu_path, lock_path)
    io.require({str(io.CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py')} <= set(files),
               'Exact original VERIFY contract/grammar/retarget code must be frozen before CPU token work')
    gpu, replay, by_id, replay_by_id = b0_replayed(root, group, values, gate, gate_path)
    contract, _, tokens_module = io.cv_modules()
    out = root/group/'VERIFY/cpu_01'
    out.mkdir(parents=True, exist_ok=False)
    bindings = dict(code_files=io.code_files(), b0_cpu_acceptance_path=str(actual_cpu_path),
        b0_cpu_acceptance_sha256=io.sha(actual_cpu_path), b0_source_lock_path=str(actual_lock_path),
        b0_source_lock_sha256=io.sha(actual_lock_path), b0_admission_path=str(gate_path), b0_admission_sha256=io.sha(gate_path),
        b0_gpu_completion_path=str(gpu/'completion.json'), b0_gpu_completion_sha256=io.sha(gpu/'completion.json'),
        b0_replay_completion_path=str(replay/'completion.json'), b0_replay_completion_sha256=io.sha(replay/'completion.json'))
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, CPU_only=True,
        new_model_calls=0, media_decodes=0, vision_processor_calls=0, bindings=bindings))
    current, entries, planned = None, [], []
    try:
        # Freeze the complete deterministic event denominator before token work.
        for entry, proof, meta in values:
            case = entry['case_id']
            done_ref, replay_ref = by_id[case], replay_by_id[case]
            done_path = io.checked(done_ref['done_path'], done_ref['done_sha256'])
            replay_path = io.checked(replay_ref['proof_path'], replay_ref['proof_sha256'])
            io.require(done_path == gpu/case/'done.json' and replay_path == replay/(case+'.json'), 'B0 accepted/replayed output escaped its case')
            done, replay_proof = io.read(done_path), io.read(replay_path)
            io.require(done['case_id'] == case and done['source_sha256'] == meta['source_sha256'] and
                replay_proof['done_sha256'] == done_ref['done_sha256'] and replay_proof['segments'] == done['segments'] and
                replay_proof['native_ranges'] == done['native_ranges'], 'Actual B0 segment/replay binding changed')
            for index, segment in enumerate(done['segments']):
                interval = [str(F(meta['window_start'])+F(str(value))) for value in segment]
                event_id = group+'.B0.'+hashlib.sha256(case.encode()).hexdigest()[:24]+'.seg'+str(index)
                event = dict(event_id=event_id, original_segment_index=index, original_interval_exact=interval)
                request = contract.request(event, meta)
                request.update(group=group, window_role=meta['window_role'], prompt=contract.prompt(request),
                    view_roles=meta.get('view_roles', [meta['window_role']]),
                    original_vision_cache_path=proof['encoded_tensor_path'], original_vision_cache_sha256=proof['encoded_tensor_sha256'],
                    original_input_evidence=proof['input_evidence'], original_evidence=dict(
                        input=dict(path=entry['input_path'], sha256=entry['input_sha256']),
                        proof=dict(path=entry['proof_path'], sha256=entry['proof_sha256']),
                        done=dict(path=str(done_path), sha256=done_ref['done_sha256']),
                        replay=dict(path=str(replay_path), sha256=replay_ref['proof_sha256'])))
                planned.append(request)
        from fresh_registration import registration
        maximum = registration(root, group)['gpu_budget']['VERIFY']['max_actual_calls']
        io.require(len(planned) <= maximum, 'Complete conservative VERIFY denominator exceeds fresh budget')
        io.save(out/'requests.json', planned)
        if planned:
            runtime, processor = io.cpu_processor()
        for request in planned:
            current = request['request_id']
            io.safe_id(current)
            folder = out/current
            folder.mkdir(exist_ok=False)
            original = io.load_cache(io.checked(request['original_vision_cache_path'], request['original_vision_cache_sha256']))
            io.require(runtime.tensor_signature(original) == request['original_input_evidence']['tensor_signature'], 'Actual accepted B0 tensor cache differs')
            tokens, combined, retarget_evidence = tokens_module.retarget(original, processor.tokenizer,
                runtime.EMPTY_PROMPT, request['prompt'], runtime.tensor_signature)
            token_path = folder/'prompt_tokens.pt.gz'
            io.save_cache(token_path, tokens)
            restored = io.load_cache(token_path)
            io.require(runtime.tensor_signature(restored) == runtime.tensor_signature(tokens), 'Lossless new prompt-token cache differs')
            evidence = dict(request['original_input_evidence'], case_id=current,
                original_case_id=request['original_case_id'], input_tokens=retarget_evidence['input_tokens'],
                prompt_sha256=hashlib.sha256(request['prompt'].encode()).hexdigest(),
                tensor_signature=retarget_evidence['full_tensor_signature'],
                unchanged_vision_tensor_signature=retarget_evidence['unchanged_vision_tensor_signature'],
                vision_processor_calls=0, media_decodes=0, prompt_tokens_only_new=True)
            input_path, proof_path = folder/'input.json', folder/'cpu_input.json'
            actual = dict(request, input_evidence=evidence, retarget_evidence=retarget_evidence,
                token_cache_path=str(token_path), token_cache_sha256=io.sha(token_path), token_cache_format=io.CACHE_FORMAT)
            io.save(input_path, actual)
            io.save(proof_path, dict(status='PASS_CPU_RECALL_VERIFY_PROMPT_ONLY_UNCHANGED_VISION',
                case_id=current, request_id=current, event_id=request['event_id'], group=group,
                input_path=str(input_path), input_sha256=io.sha(input_path), input_evidence=evidence,
                input_tokens=retarget_evidence['input_tokens'], retarget_evidence=retarget_evidence,
                token_cache_path=str(token_path), token_cache_sha256=io.sha(token_path), token_cache_format=io.CACHE_FORMAT,
                original_vision_cache_path=request['original_vision_cache_path'],
                original_vision_cache_sha256=request['original_vision_cache_sha256'], CPU_only=True, CUDA_initialized=False,
                vision_processor_calls=0, media_decodes=0, new_model_calls=0, new_optimizer_updates=0))
            import torch
            io.require(not torch.cuda.is_initialized(), 'VERIFY token preparation initialized CUDA')
            entries.append(dict(case_id=current, request_id=current, event_id=request['event_id'], group=group,
                input_path=str(input_path), input_sha256=io.sha(input_path), proof_path=str(proof_path), proof_sha256=io.sha(proof_path)))
            print(json.dumps(dict(stage='VERIFY_PREPARE', group=group, prepared=len(entries), expected=len(planned))), flush=True)
            del original, tokens, combined, restored
        io.save(out/'completion.json', dict(status=CPU_STATUS, group=group, expected_input_count=len(entries), entries=entries,
            requests_path=str(out/'requests.json'), requests_sha256=io.sha(out/'requests.json'), bindings=bindings,
            CPU_only=True, CUDA_initialized=False, vision_processor_calls=0, media_decodes=0,
            new_model_calls=0, new_optimizer_updates=0,
            zero_candidate_stage_requires_no_gpu_job=not bool(entries)))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_PREPARE_NO_REENCODE_OR_FALLBACK', request_id=current,
            successful_entries=entries, error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True, do_not_repeat_success=True))
        raise


def accepted(root, group, cpu_path=None, lock_path=None):
    gate, cpu, files, gate_path, actual_cpu_path, actual_lock_path = io.admission(root, group, 'VERIFY', cpu_path, lock_path)
    io.require(cpu['status'] == CPU_STATUS and cpu['expected_input_count'] == len(cpu['entries']) == gate['expected_input_count'] and
        cpu['vision_processor_calls'] == cpu['media_decodes'] == 0 and cpu['bindings']['code_files'] == io.code_files(),
        'All prompt-only actual VERIFY CPU inputs must pass before calls')
    bindings = cpu['bindings']
    for prefix in ('b0_cpu_acceptance', 'b0_source_lock', 'b0_admission', 'b0_gpu_completion', 'b0_replay_completion'):
        io.locked_ref(bindings[prefix+'_path'], bindings[prefix+'_sha256'], files)
    replay_complete = io.read(bindings['b0_replay_completion_path'])
    io.require(replay_complete['status'] == 'PASS_ALL_RECALL_B0_INDEPENDENT_REPLAYS_NOT_QUALITY' and
               replay_complete['group'] == group and replay_complete['gpu_completion_sha256'] == bindings['b0_gpu_completion_sha256'], 'B0 replay completion changed')
    b0_gate = io.read(bindings['b0_admission_path'])
    io.require(b0_gate['group'] == group and b0_gate['stage'] == 'B0', 'Cross-group B0 replay binding')
    _, b0_resource_sha = io.terminal(b0_gate)
    io.require(replay_complete['resource_terminal_sha256'] == b0_resource_sha, 'B0 resource natural completion changed')
    planned = io.read(io.locked_ref(cpu['requests_path'], cpu['requests_sha256'], files))
    planned_by_id = {r['request_id']: r for r in planned}
    io.require(len(planned_by_id) == len(planned) == len(cpu['entries']), 'Complete unique planned VERIFY denominator differs')
    contract, _, _ = io.cv_modules()
    values = []
    for entry in cpu['entries']:
        current = io.safe_id(entry['case_id'])
        proof = io.read(io.locked_ref(entry['proof_path'], entry['proof_sha256'], files))
        req = io.read(io.locked_ref(entry['input_path'], entry['input_sha256'], files))
        io.require(proof['status'] == 'PASS_CPU_RECALL_VERIFY_PROMPT_ONLY_UNCHANGED_VISION' and
            proof['case_id'] == proof['request_id'] == req['request_id'] == entry['request_id'] == current and
            proof['group'] == req['group'] == entry['group'] == group and proof['CPU_only'] is True and proof['CUDA_initialized'] is False and
            proof['new_model_calls'] == proof['new_optimizer_updates'] == proof['vision_processor_calls'] == proof['media_decodes'] == 0 and
            proof['input_path'] == entry['input_path'] and proof['input_sha256'] == entry['input_sha256'] and
            proof['token_cache_format'] == req['token_cache_format'] == io.CACHE_FORMAT and
            proof['input_tokens'] == proof['input_evidence']['input_tokens'] and 0 < proof['input_tokens'] <= 16384 and
            proof['input_evidence'] == req['input_evidence'] and req['reference_labels_read'] is False and req['audio_observed'] is False,
            'Actual complete VERIFY CPU/input identity changed')
        io.require(all(req[key] == value for key, value in planned_by_id[current].items()), 'Actual request differs from complete frozen plan')
        for prefix in ('token_cache', 'original_vision_cache'):
            io.locked_ref(proof[prefix+'_path'], proof[prefix+'_sha256'], files)
            io.require(proof[prefix+'_path'] == req[prefix+'_path'] and proof[prefix+'_sha256'] == req[prefix+'_sha256'], 'VERIFY accepted cache binding differs')
        for ref in req['original_evidence'].values():
            io.locked_ref(ref['path'], ref['sha256'], files)
        meta = io.read(req['original_evidence']['input']['path'])
        original_proof = io.read(req['original_evidence']['proof']['path'])
        io.validate_native(meta)
        io.locked_ref(meta['source_path'], meta['source_sha256'], files)
        io.locked_ref(meta['frame_array_path'], meta['frame_array_sha256'], files)
        io.require(original_proof['encoded_tensor_path'] == req['original_vision_cache_path'] and
            original_proof['encoded_tensor_sha256'] == req['original_vision_cache_sha256'] and
            original_proof['input_evidence'] == req['original_input_evidence'] and
            req['window_role'] == meta['window_role'] and req['prompt'] == contract.prompt(req), 'Original B0 cache/role/exact VERIFY prompt differs')
        io.require(req['view_roles'] == meta.get('view_roles', [meta['window_role']]), 'Actual shared-view VERIFY role aliases changed')
        regenerated = contract.request(dict(event_id=req['event_id'], original_segment_index=req['original_segment_index'],
            original_interval_exact=req['original_interval_exact']), meta)
        io.require(all(req[key] == value for key, value in regenerated.items()), 'Exact original candidate request/evidence gate differs')
        values.append((entry, proof, req))
    io.require(len({e['case_id'] for e, _, _ in values}) == len(values), 'Duplicate VERIFY input')
    # The entire token/vision cache denominator is checked on CPU before a
    # VERIFY model is loaded, in addition to the later per-call GPU equality.
    runtime = io.runtime_only()
    _, _, token_module = io.cv_modules()
    for _, proof, req in values:
        tokens, original = io.load_cache(proof['token_cache_path']), io.load_cache(proof['original_vision_cache_path'])
        io.require(set(tokens) == set(token_module.TOKEN_KEYS) and
                   set(original) == set(token_module.TOKEN_KEYS+token_module.VISION_KEYS), 'Complete actual VERIFY cache keys differ')
        combined = {**tokens, **{key: original[key] for key in token_module.VISION_KEYS}}
        io.require(runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'] and
            runtime.tensor_signature(combined) == proof['input_evidence']['tensor_signature'] and
            runtime.tensor_signature({key: original[key] for key in token_module.VISION_KEYS}) == proof['input_evidence']['unchanged_vision_tensor_signature'] and
            int(combined['input_ids'].shape[1]) == proof['input_tokens'], 'Complete actual VERIFY cache admission differs')
        del tokens, original, combined
    return gate, cpu, files, values, gate_path


def infer(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=False)
    gate, cpu, files, values, gate_path = accepted(root, group, cpu_path, lock_path)
    io.require(values, 'Zero B0 candidates require no VERIFY GPU job')
    io.deadline(gate)
    runtime = io.runtime_only()
    contract, grammar_module, token_module = io.cv_modules()
    io.gpu_reservation(gate)
    import torch
    out = root/group/'VERIFY/gpu_01'
    out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, stage='VERIFY',
        admission_sha256=io.sha(gate_path), expected_input_count=len(values), original_B0_calls_repeated=0, new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    current, begun, entries = None, 0, []
    try:
        config = io.read(io.CONFIG)
        model, processor, identity = runtime.b_engine.load_model(config)
        io.verify_model(model, identity)
        io.save(out/'model_identity.json', dict(identity=identity, adapter_enabled_for_all_calls=True, optimizer_updates=0))
        eos = io.eos_ids(model)
        candidates = grammar_module.candidate_tokens(processor.tokenizer, contract.responses())
        for entry, proof, req in values:
            current = entry['case_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            tokens, original = io.load_cache(proof['token_cache_path']), io.load_cache(proof['original_vision_cache_path'])
            io.require(set(tokens) == set(token_module.TOKEN_KEYS) and set(original) == set(token_module.TOKEN_KEYS+token_module.VISION_KEYS), 'Actual VERIFY cache keys differ')
            combined = {**tokens, **{key: original[key] for key in token_module.VISION_KEYS}}
            evidence = proof['input_evidence']
            io.require(runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'] and
                runtime.tensor_signature(combined) == evidence['tensor_signature'] and
                runtime.tensor_signature({key: original[key] for key in token_module.VISION_KEYS}) == evidence['unchanged_vision_tensor_signature'],
                'Actual unchanged original vision/new text tensor signature differs')
            prefix = int(combined['input_ids'].shape[1])
            io.require(prefix == proof['input_tokens'] and prefix <= 16384, 'Actual VERIFY token budget differs')
            gpu = {key: value.to('cuda') for key, value in combined.items()}
            io.require(runtime.tensor_signature(gpu) == evidence['tensor_signature'], 'Actual VERIFY CPU/GPU equality failed')
            disabled = io.enabled_layers(model)
            grammar = grammar_module.VerifyConstraint(processor.tokenizer, prefix, req, eos, candidates)
            io.save(folder/'request.json', dict(case_id=current, request_id=current, event_id=req['event_id'], group=group,
                window_role=req['window_role'], view_roles=req['view_roles'], original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
                original_interval_exact=req['original_interval_exact'], prompt=req['prompt'], input_path=entry['input_path'],
                input_sha256=entry['input_sha256'], CPU_proof_sha256=entry['proof_sha256'], input_evidence=evidence,
                original_vision_cache_sha256=proof['original_vision_cache_sha256'], token_cache_sha256=proof['token_cache_sha256'],
                allowed_responses=contract.responses(req), reference_labels_read=False, audio_observed=False))
            begun += 1
            io.append(out/'attempts.jsonl', dict(event='BEGIN', case_id=current, call_id=begun, utc=io.utc()))
            started = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(**gpu, do_sample=False, max_new_tokens=256,
                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = generated.sequences[0, prefix:]
            text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
            io.save(folder/'raw.json', dict(raw_output=text, output_token_ids=ids.tolist(),
                selected_token_scores=[score if math.isfinite(score) else str(score) for score in scores],
                generated_score_count=len(generated.scores), output_tokens=len(ids), input_tokens=prefix,
                generation_seconds=time.monotonic()-started, eos_token_ids=eos, actual_model_call=True,
                input_evidence=evidence, adapter_disabled_layers=disabled, constraint_stats=grammar.stats))
            io.output_tokens(io.read(folder/'raw.json'))
            parsed = grammar.assert_complete(ids)
            io.require(json.dumps(parsed, separators=(',', ':')) == text, 'Actual VERIFY tokens/canonical raw differ')
            decision = contract.resolve(text, req, execution_status='MODEL_OK')
            io.save(folder/'done.json', dict(status='PASS_RECALL_VERIFY_DECISION_NOT_QUALITY', case_id=current,
                request_id=current, event_id=req['event_id'], group=group, window_role=req['window_role'], decision_result=decision,
                view_roles=req['view_roles'],
                raw_path=str(folder/'raw.json'), raw_sha256=io.sha(folder/'raw.json'), request_sha256=io.sha(folder/'request.json'),
                input_evidence=evidence, input_tokens=prefix, output_tokens=len(ids), new_optimizer_updates=0))
            receipt = dict(case_id=current, request_id=current, event_id=req['event_id'],
                done_path=str(folder/'done.json'), done_sha256=io.sha(folder/'done.json'))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED', call_id=begun, utc=io.utc(), **receipt))
            entries.append(receipt)
            print(json.dumps(dict(stage='VERIFY', group=group, accepted=len(entries), expected=len(values), request_id=current, decision=decision['decision'])), flush=True)
            del tokens, original, combined, gpu, generated, ids
        io.require(begun == len(entries) == len(values), 'Incomplete unique actual VERIFY calls')
        io.require(runtime.b_engine.frozen_identity(model, config) == identity['base'] and
                   runtime.b_engine.adapter_identity(model, config) == identity['adapter'], 'Actual base/adapter changed during VERIFY')
        io.save(out/'completion.json', dict(status='PASS_ALL_RECALL_VERIFY_CALLS_NOT_QUALITY', group=group,
            calls=begun, entries=entries, attempts_sha256=io.sha(out/'attempts.jsonl'), admission_sha256=io.sha(gate_path),
            model_identity_sha256=io.sha(out/'model_identity.json'), model_parameters=io.MODEL_PARAMETERS,
            original_B0_calls_repeated=0, new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_NO_UNKNOWN_OR_EMPTY_FALLBACK', current=current, begun=begun,
            successful_entries=entries, error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True, do_not_repeat_success=True))
        raise


def independent_tokens(original, tokenizer, prompt, signature, vision_prefix, vision_keys):
    """Independent partition/encode path, rather than prepare's retarget helper."""
    import torch
    runtime = io.runtime_only()
    text = tokenizer.decode(original['input_ids'][0].tolist(), skip_special_tokens=False, clean_up_tokenization_spaces=False)
    before, marker, after = text.partition(runtime.EMPTY_PROMPT)
    io.require(marker == runtime.EMPTY_PROMPT and runtime.EMPTY_PROMPT not in after, 'Independent EMPTY_PROMPT partition is not unique')
    expanded = before+prompt+after
    ids = tokenizer.encode(expanded, add_special_tokens=False)
    new_ids = torch.tensor([ids], dtype=original['input_ids'].dtype, device='cpu')
    tokens = dict(input_ids=new_ids, attention_mask=torch.ones(new_ids.shape, dtype=original['attention_mask'].dtype, device='cpu'))
    old_prefix, old_evidence = vision_prefix(original['input_ids'], tokenizer)
    new_prefix, new_evidence = vision_prefix(new_ids, tokenizer)
    io.require(torch.equal(old_prefix, new_prefix) and old_evidence == new_evidence, 'Independent retarget changed original vision/native timestamp prefix')
    combined = {**tokens, **{key: original[key] for key in vision_keys}}
    return tokens, combined, dict(original_expanded_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        new_expanded_text_sha256=hashlib.sha256(expanded.encode()).hexdigest(), vision_prefix=old_evidence,
        unchanged_vision_tensor_signature=signature({key: original[key] for key in vision_keys}),
        full_tensor_signature=signature(combined), input_tokens=len(ids))


def independent_decision(req, text):
    meta = io.read(req['original_evidence']['input']['path'])
    done = io.read(req['original_evidence']['done']['path'])
    start = F(done['source_start_exact'])
    interval = [str(start+F(str(value))) for value in done['segments'][req['original_segment_index']]]
    io.require(interval == req['original_interval_exact'] and meta['case_id'] == req['original_case_id'] and
        meta['source_sha256'] == req['source_sha256'] and meta['window_role'] == req['window_role'] and
        meta.get('view_roles', [meta['window_role']]) == req['view_roles'] and
        meta['reference_available_to_inference'] is False and meta['audio_observed'] is False,
        'Independent exact raw B0 candidate/source identity differs')
    first, last = map(F, interval)
    observed = sum(first <= F(point) < last for point in meta['sample_exact_pts'])
    io.require(observed == req['candidate_visible_sample_count'], 'Independent visible-candidate sampling gate differs')
    decisions = ('KEEP', 'UNKNOWN', 'DROP') if observed else ('UNKNOWN',)
    legal = tuple('{"decision":"'+value+'"}' for value in decisions)
    io.require(text in legal, 'Independent canonical decision parser rejected raw; no fallback')
    decision = json.loads(text)['decision']
    points = list(map(F, meta['all_source_exact_pts']))
    members = [i for i, point in enumerate(points) if first <= point < last]
    io.require(members and members == list(range(members[0], members[-1]+1)), 'Independent candidate native membership is invalid')
    result = dict(event_id=req['event_id'], request_id=req['request_id'], original_case_id=req['original_case_id'],
        original_segment_index=req['original_segment_index'], source_sha256=req['source_sha256'], original_interval_exact=interval,
        decision=decision, candidate_kept=decision != 'DROP', retained_interval_exact=interval if decision != 'DROP' else None,
        boundaries_changed=False, new_candidate_created=False,
        uncertainty_gate='NONE' if observed else 'NO_SHOWN_SAMPLE_IN_CANDIDATE', successful_model_call_required=True)
    return result, [members[0], members[-1]+1]


def replay(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=True)
    gate, cpu, files, values, gate_path = accepted(root, group, cpu_path, lock_path)
    _, resource_sha = io.terminal(gate)
    gpu = root/group/'VERIFY/gpu_01'
    complete, by_id = io.completed_job(gpu, gate, gate_path, len(values), 'VERIFY')
    io.require(list(by_id) == [e['case_id'] for e, _, _ in values], 'Actual VERIFY call order differs from accepted CPU inputs')
    out = root/group/'VERIFY/replay_01'
    out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'),
        new_model_calls=0, media_decodes=0, vision_processor_calls=0))
    current, proofs, exported = None, [], []
    try:
        runtime, processor = io.cpu_processor()
        contract, grammar_module, tokens_module = io.cv_modules()
        generation = io.read(Path(io.read(io.CONFIG)['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        candidates = grammar_module.candidate_tokens(processor.tokenizer, contract.responses())
        for entry, proof, req in values:
            current = entry['case_id']
            folder = gpu/current
            io.require(Path(by_id[current]['done_path']).resolve() == (folder/'done.json').resolve() and
                       io.sha(folder/'done.json') == by_id[current]['done_sha256'], 'Actual accepted VERIFY answer changed')
            done, raw, request = [io.read(folder/name) for name in ('done.json', 'raw.json', 'request.json')]
            io.require(done['status'] == 'PASS_RECALL_VERIFY_DECISION_NOT_QUALITY' and
                done['raw_sha256'] == io.sha(folder/'raw.json') and done['request_sha256'] == io.sha(folder/'request.json') and
                request['CPU_proof_sha256'] == entry['proof_sha256'] and request['input_sha256'] == entry['input_sha256'] and
                request['original_case_id'] == req['original_case_id'] and request['original_segment_index'] == req['original_segment_index'] and
                request['original_interval_exact'] == req['original_interval_exact'] and request['prompt'] == req['prompt'] == contract.prompt(req) and
                request['reference_labels_read'] is False and request['audio_observed'] is False and
                request['window_role'] == done['window_role'] == req['window_role'] and
                request['view_roles'] == done['view_roles'] == req['view_roles'] and
                request['original_vision_cache_sha256'] == proof['original_vision_cache_sha256'] and
                request['token_cache_sha256'] == proof['token_cache_sha256'], 'Actual untouched VERIFY raw/request/input bindings differ')
            from fresh_registration import verify_input_QA
            first = verify_input_QA(root, current, entry, req, proof)
            evidence = first['input_evidence']
            token_evidence = first['independent_token_evidence']
            io.require(evidence == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'],
                       'Completed first pre-GPU VERIFY input evidence changed')
            ids = io.output_tokens(raw, done)
            io.require(raw['input_tokens'] == done['input_tokens'] == proof['input_tokens'] == token_evidence['input_tokens'] and
                raw['eos_token_ids'] == eos, 'Actual VERIFY input/EOS token denominator differs')
            text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            io.require(text == raw['raw_output'], 'Independent generated VERIFY token decoding differs')
            grammar = grammar_module.VerifyConstraint(processor.tokenizer, proof['input_tokens'], req, eos, candidates)
            parsed = grammar.assert_complete(ids)
            io.require(json.dumps(parsed, separators=(',', ':')) == text, 'Independent exact finite VERIFY grammar differs')
            decision, native = independent_decision(req, text)
            io.require(decision == done['decision_result'], 'Independent KEEP/UNKNOWN/DROP and exact original candidate differ')
            path = out/(current+'.json')
            io.save(path, dict(status='PASS_INDEPENDENT_RECALL_VERIFY_TOKEN_RAW_GRAMMAR_NATIVE_REPLAY',
                case_id=current, request_id=current, event_id=req['event_id'], group=group, decision_result=decision,
                original_native_range=native, raw_sha256=io.sha(folder/'raw.json'), done_sha256=io.sha(folder/'done.json'),
                unchanged_vision_tensor_signature=evidence['unchanged_vision_tensor_signature'], full_tensor_signature=evidence['tensor_signature'],
                CPU_only=True, new_model_calls=0, media_decodes=0, vision_processor_calls=0))
            proofs.append(dict(case_id=current, request_id=current, proof_path=str(path), proof_sha256=io.sha(path)))
            exported.append(dict(source_name=req['source_name'], source_sha256=req['source_sha256'], event_id=req['event_id'],
                original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
                original_interval_exact=req['original_interval_exact'],
                window_role=req['window_role'], original_native_range=native, decision_result=decision,
                view_roles=req['view_roles'],
                eligible_for_new_addition=decision['decision'] == 'KEEP'))
            print(json.dumps(dict(stage='VERIFY_REPLAY', group=group, completed=len(proofs), expected=len(values))), flush=True)
            del first
        import torch
        io.require(not torch.cuda.is_initialized(), 'Independent VERIFY replay initialized CUDA')
        io.save(out/'completion.json', dict(status='PASS_ALL_RECALL_VERIFY_INDEPENDENT_REPLAYS_NOT_QUALITY', group=group,
            proofs=proofs, calls=len(proofs), resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'),
            CPU_only=True, CUDA_initialized=False, new_model_calls=0, media_decodes=0, vision_processor_calls=0, new_optimizer_updates=0))
        io.save(root/group/'VERIFY/verification_export.json', dict(status='PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY',
            group=group, events=exported, independent_replay_completion_sha256=io.sha(out/'completion.json'),
            model_parameters=io.MODEL_PARAMETERS, original_B0_calls_repeated=0, new_optimizer_updates=0,
            reference_labels_read=False, media_decodes=0, vision_processor_calls=0,
            new_additions_require_explicit_KEEP=True, candidate_kept_does_not_authorize_new_addition=True))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_REPLAY_KEEP_RAW_AND_SUCCESS', current=current,
            successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True, do_not_repeat_success=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'infer', 'replay'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--group', required=True, choices=('dev', 'confirm'))
    parser.add_argument('--cpu-acceptance', help='prepare: B0 CPU acceptance; infer/replay: VERIFY CPU completion')
    parser.add_argument('--source-lock', help='prepare: B0 source lock; infer/replay: VERIFY source lock')
    args = parser.parse_args()
    if args.stage in ('prepare', 'replay'):
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    globals()[args.stage](io.root_path(args.root), args.group, args.cpu_acceptance, args.source_lock)


if __name__ == '__main__':
    main()
