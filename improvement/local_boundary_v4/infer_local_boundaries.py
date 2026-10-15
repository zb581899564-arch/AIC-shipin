"""Deferred same-B local-boundary inference under main's unique gpu_run.py job.

No wrapper/launcher is implemented here. The main agent must freeze the pilot,
complete actual CPU inputs, independently admit them, and reserve the GPU.
CPU processor encodes are reused from accepted saved tensors, not recomputed.
"""
import argparse
import math
import os
from pathlib import Path
import time
import traceback

from lb_contract import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS, response_strings, resolve_endpoint
from lb_grammar import BoundaryConstraint, candidates
import lb_io as io


def main(base):
    base = io.base_path(base)
    admission, cpu, rows = io.admitted_inputs(base)
    _,_,_,skips,denominators=io.plan_partition(base)
    if not rows:
        io.host(cpu=True)
        out=base/'gpu_01'
        out.mkdir(exist_ok=False)
        io.save(out/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),actual_model_call_budget=0,
            no_model_loaded=True,no_GPU_reservation=True,structural_geometry_only=True))
        with (out/'attempts.jsonl').open('x'):
            pass
        io.save(out/'completion.json',dict(status='PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY',
            requests=0,events=cpu['events'],actual_model_calls=0,entries=[],**denominators,
            attempts_sha256=io.sha(out/'attempts.jsonl'),model_identity_sha256=None,
            gpu_admission_sha256=io.sha(base/'gpu_admission.json'),model_parameters=io.MODEL_PARAMETERS,
            reference_labels_read=False,new_optimizer_updates=0,no_GPU_reservation=True,no_model_loaded=True,
            structural_skips_sha256=io.sha(base/'plan_01/structural_skips.json')))
        return
    io.host(cpu=False)
    runtime, files = io.legacy_runtime()
    if files != cpu['bindings']['original_b_processor_runtime']['runtime_files']:
        raise ValueError('Actual original runtime differs from accepted CPU encoding')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    active = io.read(io.ROOT/'improvement_round1/active_gpu_job.json')
    if active['name'] != admission['gpu_job_name']:
        raise ValueError('Current shared GPU reservation is not this admitted unique job')
    import torch
    out = base/'gpu_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(),
        gpu_admission_sha256=io.sha(base/'gpu_admission.json'),
        actual_model_call_budget=len(rows), job_name=admission['gpu_job_name'],
        new_optimizer_updates=0, accepted_cpu_encodes_reused_without_reencoding=True))
    with (out/'attempts.jsonl').open('x'):
        pass
    current, begun, entries = None, 0, []
    try:
        model, processor, identity = runtime.b_engine.load_model(io.read(io.RUN/'b_score_aligned_package_v4/config.json'))
        io.verify_model(model, identity)
        assets = cpu['bindings']['original_b_processor_runtime']['processor_assets']
        if any(io.sha(path) != digest for path, digest in assets.items()):
            raise ValueError('Original processor/tokenizer assets changed after CPU admission')
        io.save(out/'model_identity.json', dict(identity=identity, new_optimizer_updates=0))
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        strings = tuple(sorted({s for _, _, meta in rows for s in response_strings(meta)}))
        allowed_tokens = candidates(processor.tokenizer, strings)
        for entry, proof, meta in rows:
            current = entry['request_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            tensor_path = io.checked_ref(dict(path=proof['encoded_tensor_path'],
                sha256=proof['encoded_tensor_sha256']), roots=(base,))
            if proof['encoded_tensor_format'] != io.TENSOR_CACHE_FORMAT:
                raise ValueError('Accepted CPU tensor cache format differs')
            encoded = io.load_tensor_cache(tensor_path)
            if (not encoded or any(not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                                   for value in encoded.values()) or
                    runtime.tensor_signature(encoded) != proof['input_evidence']['tensor_signature']):
                raise ValueError('Saved accepted CPU tensor evidence differs')
            prefix = int(encoded['input_ids'].shape[1])
            if prefix != proof['input_tokens'] or prefix > MAX_INPUT_TOKENS:
                raise ValueError('Actual accepted input-token budget changed')
            grammar = BoundaryConstraint(processor.tokenizer, prefix, meta, eos, allowed_tokens)
            gpu = {name: tensor.to('cuda') for name, tensor in encoded.items()}
            if runtime.tensor_signature(gpu) != proof['input_evidence']['tensor_signature']:
                raise ValueError('CPU/GPU input tensor equality failed')
            io.save(folder/'gpu_input.json', dict(status='PASS_ACCEPTED_CPU_GPU_TENSOR_EQUALITY',
                tensor_signature=proof['input_evidence']['tensor_signature'],
                encoded_tensor_sha256=proof['encoded_tensor_sha256'],
                encoded_tensor_format=proof['encoded_tensor_format']))
            io.save(folder/'request.json', dict(request_id=current, event_id=meta['event_id'], side=meta['side'],
                original_case_id=meta['original_case_id'], original_segment_index=meta['original_segment_index'],
                original_interval_exact=meta['original_interval_exact'], window_start=meta['window_start'],
                window_end=meta['window_end'], prompt=meta['prompt'],
                input_path=proof['input_path'], input_sha256=proof['input_sha256'],
                CPU_proof_sha256=entry['proof_sha256'], input_evidence=proof['input_evidence'],
                encoded_tensor_sha256=proof['encoded_tensor_sha256'],
                encoded_tensor_format=proof['encoded_tensor_format'],
                finite_response_strings=response_strings(meta), reference_labels_read=False))
            if begun >= admission['actual_model_call_budget']:
                raise ValueError('Frozen actual model-call budget exceeded')
            begun += 1
            io.append(out/'attempts.jsonl', dict(event='BEGIN_MODEL_CALL', call_id=begun,
                request_id=current, raw_path=str(folder/'raw.json'), utc=io.utc()))
            started = time.monotonic()
            with torch.inference_mode():
                result = model.generate(**gpu, do_sample=False, max_new_tokens=MAX_OUTPUT_TOKENS,
                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = result.sequences[0, prefix:]
            raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(score[0, int(token)]) for score, token in zip(result.scores, ids)]
            io.save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(),
                selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                generated_score_count=len(result.scores), input_tokens=prefix, output_tokens=len(ids),
                generation_seconds=time.monotonic()-started, input_evidence=proof['input_evidence'],
                constraint_stats=grammar.stats, eos_token_ids=eos, actual_model_call=True))
            # The untouched raw exists before any token/parser/conversion checks.
            if not 0 < len(ids) <= MAX_OUTPUT_TOKENS or len(scores) != len(ids) or not all(map(math.isfinite, scores)):
                raise ValueError('Generated actual-token/finite-score denominator failed')
            decision = grammar.assert_complete(ids)
            if __import__('json').dumps(decision, separators=(',', ':')) != raw:
                raise ValueError('Generated token IDs/raw decision differ')
            endpoint = resolve_endpoint(decision, meta)
            endpoint.update(actual_model_call=True,predeclared_skip=False,decision_origin='MODEL_OUTPUT')
            done_path = folder/'done.json'
            io.save(done_path, dict(status='PASS_LOCAL_BOUNDARY_DECISION_NOT_QUALITY',
                request_id=current, event_id=meta['event_id'], side=meta['side'], decision=decision,
                endpoint_result=endpoint, raw_path=str(folder/'raw.json'), raw_sha256=io.sha(folder/'raw.json'),
                request_sha256=io.sha(folder/'request.json'), input_tokens=prefix, output_tokens=len(ids),
                input_evidence=proof['input_evidence'], new_optimizer_updates=0))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED_MODEL_CALL', call_id=begun,
                request_id=current, done_path=str(done_path), done_sha256=io.sha(done_path), utc=io.utc()))
            entries.append(dict(request_id=current, event_id=meta['event_id'], side=meta['side'],
                done_path=str(done_path), done_sha256=io.sha(done_path)))
            print(__import__('json').dumps(dict(request_id=current, accepted_calls=len(entries),
                total_calls=len(rows), decision=endpoint['applied_decision'])), flush=True)
            del gpu, encoded, result, ids
        io.save(out/'completion.json', dict(status='PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY',
            requests=len(rows), events=cpu['events'], actual_model_calls=begun, entries=entries,
            **denominators,structural_skips_sha256=io.sha(base/'plan_01/structural_skips.json'),
            attempts_sha256=io.sha(out/'attempts.jsonl'), model_identity_sha256=io.sha(out/'model_identity.json'),
            gpu_admission_sha256=io.sha(base/'gpu_admission.json'), model_parameters=io.MODEL_PARAMETERS,
            reference_labels_read=False, new_optimizer_updates=0, utc=io.utc()))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_LOCAL_BOUNDARY_KEEP_RAW_NO_EMPTY_FALLBACK',
            request_id=current, actual_started_model_calls=begun, successful_entries=entries,
            error=repr(error), traceback=traceback.format_exc(), utc=io.utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    main(args.base)
