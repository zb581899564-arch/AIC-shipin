from confirm_run_common_04 import SOURCE_COUNT
"""One unchanged trained-B answer per accepted external native64 window."""
import math
import os
import time
import traceback
from fractions import Fraction as F
from pathlib import Path
import confirm_run_common_04 as r


def main():
    r.verify_lock()
    acceptance, complete, rows = r.inputs()
    rt = r.runtime()
    from sft_contract import verify_live_gpu_reservation
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    import torch
    verify_live_gpu_reservation()
    r.GPU.mkdir(exist_ok=False)
    r.save(r.GPU/'launch_claim.json', dict(source_lock_sha256=r.sha(r.BASE/'new_confirm_source_lock_04.json'),
        native_input_acceptance_sha256=r.sha(r.BASE/'new_confirm_input_acceptance_04.json'),
        actual_call_budget=len(rows), pid=os.getpid(), utc=r.utc(), new_optimizer_updates=0))
    with (r.GPU/'attempts.jsonl').open('x'):
        pass
    begun, entries, current = 0, [], None
    try:
        model, processor, identity = rt.b_engine.load_model(r.read(r.RUN/'b_score_aligned_package_v4/config.json'))
        if (identity['logical_parameters'] != 8782459120 or identity['base']['parameters'] != 8767123696 or
                identity['base']['sha256'] != '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' or
                identity['adapter']['sha256'] != '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' or
                identity['adapter']['tensors'] != 288 or not identity['adapter']['actual_saved_values_equal'] or
                not identity['adapter']['adapter_enabled'] or model.active_adapter != 'default'):
            raise ValueError('Actual original trained B model/adapter identity changed')
        r.save(r.GPU/'model_identity.json', dict(identity=identity, new_optimizer_updates=0))
        candidates = ascii_token_candidates(processor.tokenizer)
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        for entry, proof, meta in rows:
            current = entry['case_id']
            folder = r.GPU/current
            folder.mkdir(exist_ok=False)
            lo, hi = F(meta['window_start']), F(meta['window_end'])
            frames = rt.baseline_frames(meta)
            encoded, evidence = rt.encode(processor, meta, frames, lo, rt.EMPTY_PROMPT)
            if evidence != proof['input_evidence']:
                raise ValueError('Actual model request differs from accepted CPU processor evidence')
            prefix = int(encoded['input_ids'].shape[1])
            if prefix != proof['input_tokens']:
                raise ValueError('Actual original input-token budget changed')
            grammar = make_prefix_constraint(processor.tokenizer, prefix, hi-lo,
                candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            gpu = encoded.to('cuda')
            if rt.tensor_signature(gpu) != evidence['tensor_signature']:
                raise ValueError('Actual CPU and GPU input tensors differ')
            r.save(folder/'gpu_input.json', dict(status='PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY',
                tensor_signature=evidence['tensor_signature']))
            r.save(folder/'request.json', dict(case_id=current, source_name=meta['source_name'],
                input_path=proof['input_path'], input_sha256=proof['input_sha256'],
                CPU_proof_sha256=entry['proof_sha256'], source_start_exact=str(lo), source_end_exact=str(hi),
                prompt=rt.EMPTY_PROMPT, input_evidence=evidence, reference_labels_read=False))
            if begun >= len(rows):
                raise ValueError('Fixed actual call budget exceeded')
            begun += 1
            r.append(r.GPU/'attempts.jsonl', dict(event='BEGIN_MODEL_CALL', call_id=begun,
                case_id=current, raw_path=str(folder/'raw.json'), utc=r.utc()))
            start = time.monotonic()
            with torch.inference_mode():
                result = model.generate(**gpu, do_sample=False, max_new_tokens=256,
                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = result.sequences[0, prefix:]
            raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(s[0, int(token)]) for s, token in zip(result.scores, ids)]
            r.save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(),
                selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                generated_score_count=len(result.scores), input_tokens=prefix, output_tokens=len(ids),
                generation_seconds=time.monotonic()-start, input_evidence=evidence,
                constraint_stats=grammar.stats, eos_token_ids=eos, actual_model_call=True))
            # Untouched raw exists before every acceptance check.
            if not 0 < len(ids) <= 256 or len(scores) != len(ids) or not all(math.isfinite(s) for s in scores):
                raise ValueError('Generated token/finite-score denominator failed')
            grammar.assert_complete(ids)
            segments, errors, warnings = rt.parse_segments(raw, hi-lo, allow_empty=True)
            if segments is None or errors:
                raise ValueError('Original strict parser rejected '+repr(errors))
            native = r.ranges(segments, meta['all_source_exact_pts'], lo)
            done_path = folder/'done.json'
            r.save(done_path, dict(status='MODEL_OK' if segments else 'LEGAL_EMPTY', case_id=current,
                source_name=meta['source_name'], segments=segments, parse_errors=errors,
                parse_warnings=warnings, native_ranges=native, raw_path=str(folder/'raw.json'),
                raw_sha256=r.sha(folder/'raw.json'), request_sha256=r.sha(folder/'request.json'),
                source_start_exact=str(lo), source_end_exact=str(hi), input_evidence=evidence,
                input_tokens=prefix, output_tokens=len(ids), new_optimizer_updates=0))
            r.append(r.GPU/'attempts.jsonl', dict(event='ACCEPTED_MODEL_CALL', call_id=begun,
                case_id=current, done_path=str(done_path), done_sha256=r.sha(done_path), utc=r.utc()))
            entries.append(dict(case_id=current, source_name=meta['source_name'],
                done_path=str(done_path), done_sha256=r.sha(done_path)))
            print(__import__('json').dumps(dict(case_id=current, completed_windows=len(entries),
                total_windows=len(rows), status='MODEL_OK' if segments else 'LEGAL_EMPTY')), flush=True)
            del gpu, encoded, frames, result, ids
        events = [__import__('json').loads(s) for s in (r.GPU/'attempts.jsonl').read_text().splitlines()]
        if len(entries) != len(rows) or begun != len(rows) or len(events) != 2*len(rows):
            raise ValueError('Complete unique actual-call denominator changed')
        r.save(r.GPU/'completion.json', dict(status='PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY',
            registered_sources=SOURCE_COUNT, successful_windows=len(rows), actual_model_calls=begun, entries=entries,
            source_lock_sha256=r.sha(r.BASE/'new_confirm_source_lock_04.json'),
            native_input_acceptance_sha256=r.sha(r.BASE/'new_confirm_input_acceptance_04.json'),
            attempts_sha256=r.sha(r.GPU/'attempts.jsonl'), model_identity_sha256=r.sha(r.GPU/'model_identity.json'),
            model_parameters=8782459120, reference_labels_read=False, new_optimizer_updates=0, utc=r.utc()))
    except BaseException as error:
        r.save(r.GPU/'failure.json', dict(status='FAILED_EXTERNAL_B_KEEP_RAW_NO_EMPTY_FALLBACK',
            case_id=current, actual_started_model_calls=begun, successful_windows=len(entries),
            successful_entries=entries, error=repr(error), traceback=traceback.format_exc(), utc=r.utc()))
        raise


if __name__ == '__main__':
    main()
