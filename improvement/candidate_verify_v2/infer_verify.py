"""Deferred unique same-B VERIFY inference; main's shared wrapper must launch."""
import json
import math
import os
import time
import traceback

import cv_contract as c
import cv_io as io
from cv_grammar import VerifyConstraint, candidate_tokens
from cv_tokens import VISION_KEYS, TOKEN_KEYS


def main():
    io.check_host(cpu=False)
    reg, admission, cpu, rows = io.admitted()
    runtime, runtime_files = io.runtime_only()
    if runtime_files != cpu['bindings']['original_b_processor_runtime']['runtime_files']:
        raise ValueError('Frozen runtime differs from accepted token preparation')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    if io.read(io.HOME_ROOT/'improvement_round1/active_gpu_job.json')['name'] != admission['gpu_job_name']:
        raise ValueError('Shared reservation is not this unique admitted VERIFY job')
    import torch
    out = io.BASE/'gpu_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(),
        gpu_admission_sha256=io.sha(io.BASE/'gpu_admission.json'), actual_model_call_budget=len(rows),
        original_B0_calls_repeated=0, new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    current, begun, accepted = None, 0, []
    try:
        model, processor, identity = runtime.b_engine.load_model(io.read(io.RUN/'b_score_aligned_package_v4/config.json'))
        io.model_identity(identity)
        if model.active_adapter != 'default':
            raise ValueError('Original time adapter was disabled')
        for filename, digest in cpu['bindings']['original_b_processor_runtime']['processor_assets'].items():
            if io.sha(filename) != digest:
                raise ValueError('Original processor/tokenizer assets changed')
        io.save(out/'model_identity.json', dict(identity=identity, new_optimizer_updates=0))
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        choices = candidate_tokens(processor.tokenizer, c.responses())
        for entry, proof, req in rows:
            current = entry['request_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            token_path = io.checked(dict(path=proof['token_cache_path'], sha256=proof['token_cache_sha256']), roots=(io.BASE,))
            vision_path = io.checked(dict(path=proof['original_vision_cache_path'], sha256=proof['original_vision_cache_sha256']))
            tokens, original = io.load_tensor_cache(token_path), io.load_tensor_cache(vision_path)
            if set(tokens) != set(TOKEN_KEYS) or set(original) != set(TOKEN_KEYS+VISION_KEYS):
                raise ValueError('Actual token-only/original vision cache keys differ')
            combined = {**tokens, **{key: original[key] for key in VISION_KEYS}}
            evidence = proof['input_evidence']
            if runtime.tensor_signature(combined) != evidence['tensor_signature'] or runtime.tensor_signature(
                    {key: original[key] for key in VISION_KEYS}) != evidence['unchanged_vision_tensor_signature']:
                raise ValueError('Actual unchanged original vision/new token tensor signature differs')
            prefix = int(combined['input_ids'].shape[1])
            if prefix != proof['input_tokens'] or prefix > c.MAX_INPUT_TOKENS:
                raise ValueError('Actual VERIFY input token budget changed')
            grammar = VerifyConstraint(processor.tokenizer, prefix, req, eos, choices)
            gpu = {key: value.to('cuda') for key, value in combined.items()}
            if runtime.tensor_signature(gpu) != evidence['tensor_signature']:
                raise ValueError('Accepted CPU/GPU tensor transfer differs')
            io.save(folder/'gpu_input.json', dict(status='PASS_VERIFY_CPU_GPU_TENSOR_EQUALITY',
                tensor_signature=evidence['tensor_signature']))
            io.save(folder/'request.json', dict(request_id=current, event_id=req['event_id'],
                original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
                original_interval_exact=req['original_interval_exact'], prompt=req['prompt'],
                input_path=proof['input_path'], input_sha256=proof['input_sha256'],
                CPU_proof_sha256=entry['proof_sha256'], input_evidence=evidence,
                original_vision_cache_sha256=proof['original_vision_cache_sha256'],
                token_cache_sha256=proof['token_cache_sha256'], allowed_responses=c.responses(req),
                reference_labels_read=False, audio_observed=False))
            if begun >= reg['actual_model_call_budget']:
                raise ValueError('Frozen actual VERIFY call budget exceeded')
            begun += 1
            io.append(out/'attempts.jsonl', dict(event='BEGIN_MODEL_CALL', call_id=begun,
                request_id=current, raw_path=str(folder/'raw.json'), utc=io.utc()))
            started = time.monotonic()
            with torch.inference_mode():
                result = model.generate(**gpu, do_sample=False, max_new_tokens=c.MAX_OUTPUT_TOKENS,
                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = result.sequences[0, prefix:]
            raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(score[0, int(token)]) for score, token in zip(result.scores, ids)]
            io.save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(),
                selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                generated_score_count=len(result.scores), input_tokens=prefix, output_tokens=len(ids),
                generation_seconds=time.monotonic()-started, input_evidence=evidence,
                actual_model_call=True, constraint_stats=grammar.stats, eos_token_ids=eos))
            if not 0 < len(ids) <= c.MAX_OUTPUT_TOKENS or len(scores) != len(ids) or not all(map(math.isfinite, scores)):
                raise ValueError('Actual VERIFY token/finite-score denominator failed')
            parsed = grammar.assert_complete(ids)
            if json.dumps(parsed, separators=(',', ':')) != raw:
                raise ValueError('Generated tokens/canonical raw parser differ')
            decision = c.resolve(raw, req, execution_status='MODEL_OK')
            done_path = folder/'done.json'
            io.save(done_path, dict(status='PASS_VERIFY_DECISION_NOT_QUALITY', request_id=current,
                event_id=req['event_id'], decision_result=decision,
                raw_path=str(folder/'raw.json'), raw_sha256=io.sha(folder/'raw.json'),
                request_sha256=io.sha(folder/'request.json'), input_evidence=evidence,
                input_tokens=prefix, output_tokens=len(ids), new_optimizer_updates=0))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED_MODEL_CALL', call_id=begun,
                request_id=current, done_path=str(done_path), done_sha256=io.sha(done_path), utc=io.utc()))
            accepted.append(dict(request_id=current, event_id=req['event_id'],
                done_path=str(done_path), done_sha256=io.sha(done_path)))
            print(json.dumps(dict(completed_calls=len(accepted), total_calls=len(rows),
                request_id=current, decision=decision['decision'])), flush=True)
            del tokens, original, combined, gpu, result, ids
        io.save(out/'completion.json', dict(status='PASS_ALL_EXTERNAL_VERIFY_CALLS_NOT_QUALITY',
            actual_model_calls=begun, entries=accepted, requests=len(rows), model_parameters=c.MODEL_PARAMETERS,
            attempts_sha256=io.sha(out/'attempts.jsonl'), model_identity_sha256=io.sha(out/'model_identity.json'),
            gpu_admission_sha256=io.sha(io.BASE/'gpu_admission.json'), reference_labels_read=False,
            original_B0_calls_repeated=0, new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_KEEP_RAW_BLOCK_NO_UNKNOWN_FALLBACK',
            request_id=current, actual_started_calls=begun, successful_entries=accepted,
            error=repr(error), traceback=traceback.format_exc(), new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    main()
