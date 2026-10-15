from new5_common import SOURCE_COUNT
"""Independent CPU tensor/token/parser/native replay and external prediction export."""
import math
import os
import traceback
from fractions import Fraction as F
from pathlib import Path
import new5_run_common as r


def main():
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Independent replay must be CPU-only')
    r.verify_lock()
    _, complete, inputs = r.inputs()
    resource, resource_sha = r.resource_terminal()
    terminal = r.read(r.GPU/'completion.json')
    if (terminal['status'] != 'PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
            terminal['registered_sources'] != SOURCE_COUNT or terminal['actual_model_calls'] != len(inputs) or
            terminal['successful_windows'] != len(inputs) or
            terminal['source_lock_sha256'] != r.sha(r.BASE/'new5_source_lock_01.json') or
            terminal['native_input_acceptance_sha256'] != r.sha(r.BASE/'native_input_acceptance.json') or
            terminal['attempts_sha256'] != r.sha(r.GPU/'attempts.jsonl') or
            terminal['model_identity_sha256'] != r.sha(r.GPU/'model_identity.json')):
        raise ValueError('Actual full B execution is not accepted')
    events = [__import__('json').loads(line) for line in (r.GPU/'attempts.jsonl').read_text().splitlines()]
    if len(events) != 2*len(inputs):
        raise ValueError('Actual unique call ledger incomplete')
    for i, (entry, _, _) in enumerate(inputs, 1):
        begun, accepted = events[2*(i-1):2*i]
        if (begun['event'] != 'BEGIN_MODEL_CALL' or accepted['event'] != 'ACCEPTED_MODEL_CALL' or
                begun['call_id'] != i or accepted['call_id'] != i or
                begun['case_id'] != entry['case_id'] or accepted['case_id'] != entry['case_id']):
            raise ValueError('Unique actual call order differs from registered windows')
    by_id = {entry['case_id']: entry for entry in terminal['entries']}
    if len(by_id) != len(inputs):
        raise ValueError('Duplicate or missing successful model window')
    r.REPLAY.mkdir(exist_ok=False)
    r.save(r.REPLAY/'launch_claim.json', dict(gpu_completion_sha256=r.sha(r.GPU/'completion.json'),
        source_lock_sha256=r.sha(r.BASE/'new5_source_lock_01.json'), resource_terminal_sha256=resource_sha,
        new_model_calls=0, CPU_only=True, utc=r.utc()))
    current, proofs = None, []
    try:
        from processor_new5 import load_cpu_runtime
        rt, processor, cpu_identity = load_cpu_runtime()
        if cpu_identity != complete['bindings']['original_b_processor_runtime']:
            raise ValueError('Independent CPU processor/runtime identity changed')
        from constrained_json import ascii_token_candidates, make_prefix_constraint
        candidates = ascii_token_candidates(processor.tokenizer)
        config = r.read(r.RUN/'b_score_aligned_package_v4/config.json')
        generation = r.read(Path(config['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        exported_windows = {}
        for entry, cpu, meta in inputs:
            current = entry['case_id']
            accepted = by_id[current]
            done_path = Path(accepted['done_path'])
            if r.sha(done_path) != accepted['done_sha256'] or done_path != r.GPU/current/'done.json':
                raise ValueError('Accepted model done identity/path changed')
            done = r.read(done_path)
            raw_path = r.GPU/current/'raw.json'
            raw = r.read(raw_path)
            request_path = r.GPU/current/'request.json'
            request = r.read(request_path)
            if (done['raw_path'] != str(raw_path) or done['raw_sha256'] != r.sha(raw_path) or
                    done['request_sha256'] != r.sha(request_path) or
                    request['CPU_proof_sha256'] != entry['proof_sha256'] or
                    request['input_sha256'] != cpu['input_sha256'] or request['prompt'] != rt.EMPTY_PROMPT or
                    request['reference_labels_read'] or not raw['actual_model_call']):
                raise ValueError('Untouched raw/request/CPU proof binding changed')
            frames = rt.baseline_frames(meta)
            lo, hi = F(meta['window_start']), F(meta['window_end'])
            encoded, evidence = rt.encode(processor, meta, frames, lo, rt.EMPTY_PROMPT)
            if not evidence == cpu['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence']:
                raise ValueError('Independent CPU native RGB/processor/tensor evidence differs')
            transfer = r.read(r.GPU/current/'gpu_input.json')
            if (transfer['status'] != 'PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY' or
                    transfer['tensor_signature'] != evidence['tensor_signature']):
                raise ValueError('Actual accepted GPU input transfer changed')
            ids, scores = raw['output_token_ids'], raw['selected_token_scores']
            if (not 0 < len(ids) <= 256 or any(type(t) is not int or t < 0 for t in ids) or
                    len(ids) != len(scores) or len(ids) != raw['generated_score_count'] or
                    len(ids) != raw['output_tokens'] or len(ids) != done['output_tokens'] or
                    not all(type(s) in (float, int) and math.isfinite(s) for s in scores) or
                    int(encoded['input_ids'].shape[1]) != raw['input_tokens'] or
                    raw['input_tokens'] != done['input_tokens'] or raw['eos_token_ids'] != eos):
                raise ValueError('Independent input/output-token/finite-score budget differs')
            if processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) != raw['raw_output']:
                raise ValueError('Actual generated token IDs do not decode to untouched raw')
            grammar = make_prefix_constraint(processor.tokenizer, raw['input_tokens'], hi-lo,
                candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            grammar.assert_complete(ids)
            segments, errors, warnings = rt.parse_segments(raw['raw_output'], hi-lo, allow_empty=True)
            if (segments is None or errors or segments != done['segments'] or warnings != done['parse_warnings'] or
                    done['status'] != ('MODEL_OK' if segments else 'LEGAL_EMPTY') or
                    done['source_name'] != meta['source_name'] or done['source_start_exact'] != str(lo) or
                    done['source_end_exact'] != str(hi)):
                raise ValueError('Independent strict parser/native request replay differs')
            native = r.ranges(segments, meta['all_source_exact_pts'], lo)
            if native != done['native_ranges']:
                raise ValueError('Independent complete-source native interval membership differs')
            proof_path = r.REPLAY/(current+'.json')
            r.save(proof_path, dict(status='PASS_INDEPENDENT_CPU_TENSOR_TOKEN_PARSER_NATIVE_REPLAY',
                case_id=current, source_name=meta['source_name'], CPU_only=True,
                input_evidence=evidence, done_sha256=r.sha(done_path), raw_sha256=r.sha(raw_path),
                segments=segments, native_ranges=native, new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(case_id=current, proof_path=str(proof_path), proof_sha256=r.sha(proof_path)))
            exported_windows.setdefault(meta['source_name'], []).append(dict(start_exact=str(lo), end_exact=str(hi),
                segments=segments, original_status=done['status'], original_raw_sha256=r.sha(raw_path)))
            print(__import__('json').dumps(dict(completed_replays=len(proofs), total_windows=len(inputs))), flush=True)
            del encoded, frames
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('Independent CPU replay initialized CUDA')
        r.save(r.REPLAY/'completion.json', dict(status='PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS',
            proofs=proofs, registered_sources=SOURCE_COUNT, windows=len(proofs), CPU_only=True, CUDA_initialized=False,
            source_lock_sha256=r.sha(r.BASE/'new5_source_lock_01.json'),
            gpu_completion_sha256=r.sha(r.GPU/'completion.json'), resource_terminal_sha256=resource_sha,
            new_model_calls=0, new_optimizer_updates=0, utc=r.utc()))
        mapping = r.read(r.BASE/'mapping_01/completion.json')
        registered = r.read(r.BASE/'new5_source_registration_01.json')
        clocks = {row['source_name']: r.read(row['bundle_path'])['clock'] for row in mapping['rows']}
        export_rows = [dict(source_name=row['source_name'], native_clock=clocks[row['source_name']],
            windows=exported_windows[row['source_name']]) for row in registered['rows']]
        export_path = r.BASE/'developer_prediction_export.json'
        r.save(export_path, dict(status='PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY',
            registered_sources=SOURCE_COUNT, model_parameters=8782459120, new_optimizer_updates=0,
            started_windows=terminal['actual_model_calls'], successful_windows=len(proofs), rows=export_rows,
            source_lock_sha256=r.sha(r.BASE/'new5_source_lock_01.json'),
            independent_replay_completion_sha256=r.sha(r.REPLAY/'completion.json'), reference_labels_read=False))
        r.save(r.BASE/'developer_export_acceptance.json', dict(status='PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY',
            native_input_acceptance_sha256=r.sha(r.BASE/'native_input_acceptance.json'), registered_sources=SOURCE_COUNT,
            developer_prediction_export_sha256=r.sha(export_path),
            independent_replay_completion_sha256=r.sha(r.REPLAY/'completion.json'),
            unique_resource_terminal_sha256=resource_sha, new_model_calls=0, new_optimizer_updates=0))
    except BaseException as error:
        r.save(r.REPLAY/'failure.json', dict(status='FAILED_CPU_REPLAY_KEEP_RAW_AND_SUCCESSFUL_PROOFS',
            case_id=current, successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(), utc=r.utc()))
        raise


if __name__ == '__main__':
    main()
