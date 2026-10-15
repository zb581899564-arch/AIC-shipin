"""Independent new-token/raw/native replay; no media/vision processor/model call."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import math
import os
import traceback

import cv_contract as c
import cv_io as io
from cv_grammar import VerifyConstraint, candidate_tokens
from cv_tokens import VISION_KEYS, TOKEN_KEYS, vision_prefix


def independent_tokens(original, tokenizer, original_prompt, new_prompt, signature):
    """Partition/encode independently from prepare's batch-tokenizer replacement."""
    import torch
    text = tokenizer.decode(original['input_ids'][0].tolist(), skip_special_tokens=False,
                            clean_up_tokenization_spaces=False)
    before, marker, after = text.partition(original_prompt)
    if marker != original_prompt or original_prompt in after:
        raise ValueError('Independent original EMPTY_PROMPT partition is not unique')
    expanded = before+new_prompt+after
    ids = tokenizer.encode(expanded, add_special_tokens=False)
    new_ids = torch.tensor([ids], dtype=original['input_ids'].dtype, device='cpu')
    tokens = dict(input_ids=new_ids,
                  attention_mask=torch.ones(new_ids.shape, dtype=original['attention_mask'].dtype, device='cpu'))
    old_prefix, old_prefix_evidence = vision_prefix(original['input_ids'], tokenizer)
    new_prefix, new_prefix_evidence = vision_prefix(new_ids, tokenizer)
    if not torch.equal(old_prefix, new_prefix) or old_prefix_evidence != new_prefix_evidence:
        raise ValueError('Independent retarget changes the original expanded vision/native timestamp prefix')
    combined = {**tokens, **{key: original[key] for key in VISION_KEYS}}
    return tokens, combined, dict(
        original_expanded_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        new_expanded_text_sha256=hashlib.sha256(expanded.encode()).hexdigest(),
        vision_prefix=old_prefix_evidence,
        unchanged_vision_tensor_signature=signature({key: original[key] for key in VISION_KEYS}),
        full_tensor_signature=signature(combined), input_tokens=len(ids))


def independent_event(req, raw):
    original = io.read(io.checked(req['original_evidence']['input']))
    done = io.read(io.checked(req['original_evidence']['done']))
    start = F(done['source_start_exact'])
    interval = [str(start+F(str(value))) for value in done['segments'][req['original_segment_index']]]
    if (interval != req['original_interval_exact'] or original['case_id'] != req['original_case_id'] or
            original['source_sha256'] != req['source_sha256'] or
            original['reference_available_to_inference'] is not False or original['audio_observed'] is not False):
        raise ValueError('Independent original exact case/segment/source event binding differs')
    first, last = map(F, interval)
    observed = sum(first <= F(point) < last for point in original['sample_exact_pts'])
    if observed != req['candidate_visible_sample_count']:
        raise ValueError('Independent original candidate sampled-evidence gate differs')
    legal = ('KEEP', 'UNKNOWN', 'DROP') if observed else ('UNKNOWN',)
    choices = tuple('{"decision":"'+name+'"}' for name in legal)
    if raw not in choices:
        raise ValueError('Independent strict canonical decision/evidence parser rejected raw')
    decision = json.loads(raw)['decision']
    points = list(map(F, original['all_source_exact_pts']))
    lo, hi = bisect_left(points, first), bisect_left(points, last)
    if not lo < hi:
        raise ValueError('Independent original positive event contains no native frame')
    result = dict(event_id=req['event_id'], request_id=req['request_id'],
        original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
        source_sha256=req['source_sha256'], original_interval_exact=interval,
        decision=decision, candidate_kept=decision != 'DROP',
        retained_interval_exact=interval if decision != 'DROP' else None,
        boundaries_changed=False, new_candidate_created=False,
        uncertainty_gate='NONE' if observed else 'NO_SHOWN_SAMPLE_IN_CANDIDATE',
        successful_model_call_required=True)
    return result, [lo, hi]


def main():
    io.check_host(cpu=True)
    reg, admission, cpu, rows = io.admitted()
    resource, resource_sha = io.resource_terminal(admission['gpu_job_name'])
    gpu = io.BASE/'gpu_01'
    complete = io.read(gpu/'completion.json')
    if (complete['status'] != 'PASS_ALL_EXTERNAL_VERIFY_CALLS_NOT_QUALITY' or
            complete['actual_model_calls'] != len(rows) or complete['requests'] != len(rows) or
            complete['attempts_sha256'] != io.sha(gpu/'attempts.jsonl') or
            complete['model_identity_sha256'] != io.sha(gpu/'model_identity.json') or
            complete['gpu_admission_sha256'] != io.sha(io.BASE/'gpu_admission.json')):
        raise ValueError('Complete actual unique VERIFY model execution is not accepted')
    io.model_identity(io.read(gpu/'model_identity.json')['identity'])
    journal = [json.loads(line) for line in (gpu/'attempts.jsonl').read_text().splitlines() if line.strip()]
    if len(journal) != 2*len(rows):
        raise ValueError('Actual unique VERIFY started/accepted ledger is incomplete')
    for index, (entry, _, _) in enumerate(rows, 1):
        begun, accepted = journal[2*(index-1):2*index]
        if (begun['event'] != 'BEGIN_MODEL_CALL' or accepted['event'] != 'ACCEPTED_MODEL_CALL' or
                begun['call_id'] != index or accepted['call_id'] != index or
                begun['request_id'] != entry['request_id'] or accepted['request_id'] != entry['request_id']):
            raise ValueError('Actual registered VERIFY request order changed')
    by_id = {entry['request_id']: entry for entry in complete['entries']}
    if len(by_id) != len(rows):
        raise ValueError('Complete accepted actual VERIFY cases duplicated/missing')
    out = io.BASE/'replay_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'),
        new_model_calls=0, media_decodes=0, vision_processor_calls=0))
    current, proofs, exported = None, [], []
    try:
        import torch
        runtime, processor, identity = io.cpu_processor()
        if identity != cpu['bindings']['original_b_processor_runtime']:
            raise ValueError('Independent original CPU tokenizer/runtime assets changed')
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        from pathlib import Path
        generation = io.read(Path(config['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        choices = candidate_tokens(processor.tokenizer, c.responses())
        for entry, proof, req in rows:
            current = entry['request_id']
            accepted = by_id[current]
            done_path = io.checked(dict(path=accepted['done_path'], sha256=accepted['done_sha256']), roots=(gpu,))
            if done_path != gpu/current/'done.json':
                raise ValueError('Actual accepted VERIFY done path differs')
            done = io.read(done_path)
            raw_path, request_path = gpu/current/'raw.json', gpu/current/'request.json'
            raw, request = io.read(raw_path), io.read(request_path)
            if (done['raw_sha256'] != io.sha(raw_path) or done['request_sha256'] != io.sha(request_path) or
                    done['status'] != 'PASS_VERIFY_DECISION_NOT_QUALITY' or
                    request['CPU_proof_sha256'] != entry['proof_sha256'] or
                    request['input_sha256'] != proof['input_sha256'] or request['prompt'] != req['prompt'] or
                    req['prompt'] != c.prompt(req) or request['reference_labels_read'] is not False or
                    request['audio_observed'] is not False or raw['actual_model_call'] is not True or
                    request['original_case_id'] != req['original_case_id'] or
                    request['original_segment_index'] != req['original_segment_index'] or
                    request['original_interval_exact'] != req['original_interval_exact'] or
                    request['original_vision_cache_sha256'] != proof['original_vision_cache_sha256'] or
                    request['token_cache_sha256'] != proof['token_cache_sha256']):
                raise ValueError('Actual untouched VERIFY raw/request/CPU proof binding differs')
            original_path = io.checked(dict(path=proof['original_vision_cache_path'],
                                            sha256=proof['original_vision_cache_sha256']))
            original = io.load_tensor_cache(original_path)
            if runtime.tensor_signature(original) != req['original_input_evidence']['tensor_signature']:
                raise ValueError('Independent original full vision/token cache differs')
            tokens, combined, token_evidence = independent_tokens(original, processor.tokenizer,
                runtime.EMPTY_PROMPT, req['prompt'], runtime.tensor_signature)
            cached_tokens = io.load_tensor_cache(io.checked(dict(path=proof['token_cache_path'],
                sha256=proof['token_cache_sha256']), roots=(io.BASE,)))
            if runtime.tensor_signature(tokens) != runtime.tensor_signature(cached_tokens):
                raise ValueError('Independent new token IDs/mask differ from accepted token-only cache')
            for key, value in token_evidence.items():
                if proof['retarget_evidence'][key] != value:
                    raise ValueError('Independent full native prefix/pixel/grid evidence differs: '+key)
            evidence = proof['input_evidence']
            if (runtime.tensor_signature(combined) != evidence['tensor_signature'] or
                    not evidence == request['input_evidence'] == raw['input_evidence'] == done['input_evidence']):
                raise ValueError('Independent full new-token/unchanged-vision tensor signature differs')
            if io.read(gpu/current/'gpu_input.json')['tensor_signature'] != evidence['tensor_signature']:
                raise ValueError('Actual accepted CPU/GPU equality proof changed')
            ids, scores = raw['output_token_ids'], raw['selected_token_scores']
            if (not 0 < len(ids) <= c.MAX_OUTPUT_TOKENS or any(type(i) is not int or i < 0 for i in ids) or
                    len(ids) != len(scores) or len(ids) != raw['generated_score_count'] or
                    len(ids) != raw['output_tokens'] or len(ids) != done['output_tokens'] or
                    any(type(s) not in (float, int) or not math.isfinite(s) for s in scores) or
                    raw['input_tokens'] != token_evidence['input_tokens'] or raw['input_tokens'] != proof['input_tokens'] or
                    raw['eos_token_ids'] != eos):
                raise ValueError('Independent actual token/finite-score denominator differs')
            text = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            if text != raw['raw_output']:
                raise ValueError('Actual generated IDs do not decode to untouched raw')
            grammar = VerifyConstraint(processor.tokenizer, proof['input_tokens'], req, eos, choices)
            parsed = grammar.assert_complete(ids)
            if json.dumps(parsed, separators=(',', ':')) != text:
                raise ValueError('Independent actual finite decision grammar differs')
            decision, native = independent_event(req, text)
            if decision != done['decision_result']:
                raise ValueError('Independent exact original-candidate KEEP/UNKNOWN/DROP membership differs')
            proof_path = out/(current+'.json')
            io.save(proof_path, dict(status='PASS_INDEPENDENT_VERIFY_TOKEN_RAW_GRAMMAR_NATIVE_REPLAY',
                request_id=current, event_id=req['event_id'], decision_result=decision,
                original_native_range=native, raw_sha256=io.sha(raw_path), done_sha256=io.sha(done_path),
                unchanged_vision_tensor_signature=evidence['unchanged_vision_tensor_signature'],
                full_tensor_signature=evidence['tensor_signature'], CPU_only=True,
                new_model_calls=0, media_decodes=0, vision_processor_calls=0))
            proofs.append(dict(request_id=current, proof_path=str(proof_path), proof_sha256=io.sha(proof_path)))
            exported.append(dict(source_name=req['source_name'], source_sha256=req['source_sha256'],
                event_id=req['event_id'], original_case_id=req['original_case_id'],
                original_segment_index=req['original_segment_index'], decision_result=decision))
            del original, tokens, combined, cached_tokens
        if torch.cuda.is_initialized():
            raise ValueError('Independent VERIFY replay initialized CUDA')
        io.save(out/'completion.json', dict(status='PASS_ALL_EXTERNAL_VERIFY_INDEPENDENT_REPLAYS_NOT_QUALITY',
            proofs=proofs, requests=len(proofs), gpu_completion_sha256=io.sha(gpu/'completion.json'),
            resource_terminal_sha256=resource_sha, CPU_only=True, CUDA_initialized=False,
            new_model_calls=0, media_decodes=0, vision_processor_calls=0))
        io.save(io.BASE/'verification_export.json', dict(status='PASS_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY',
            events=exported, independent_replay_completion_sha256=io.sha(out/'completion.json'),
            automatic_union_renderer='cv_contract.render_retained_union; main freezes padding/space separately',
            source_scope='EXTERNAL_NONTEST_ONLY', original_B0_calls_repeated=0,
            model_parameters=c.MODEL_PARAMETERS, new_optimizer_updates=0,
            reference_labels_read=False, media_decodes=0, vision_processor_calls=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_REPLAY_BLOCK_KEEP_RAW_AND_SUCCESS',
            request_id=current, successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(),
            new_model_calls=0, media_decodes=0, vision_processor_calls=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main()
