"""One separately admitted original B0 pass and its first independent CPU replay."""
import argparse
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import time
import traceback

import facts_common as io
from registration import completed_job


def infer(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=False)
    gate, cpu, files, values, gate_path, _, _ = io.accepted_b0(root, group, cpu_path, lock_path)
    io.deadline(gate)
    runtime = io.runtime_only()
    io.gpu_reservation(gate)
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    import torch
    out = root/group/'B0/gpu_01'
    out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, stage='B0',
        admission_sha256=io.sha(gate_path), expected_input_count=len(values), new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    entries, begun, current = [], 0, None
    try:
        config = io.read(io.CONFIG)
        model, processor, identity = runtime.b_engine.load_model(config)
        io.verify_model(model, identity)
        io.save(out/'model_identity.json', dict(identity=identity, adapter_enabled_for_all_calls=True, optimizer_updates=0))
        candidates, eos = ascii_token_candidates(processor.tokenizer), io.eos_ids(model)
        for entry, proof, meta in values:
            current = entry['case_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            encoded = io.load_cache(proof['encoded_tensor_path'])
            evidence = proof['input_evidence']
            io.require(runtime.tensor_signature(encoded) == evidence['tensor_signature'], 'Actual accepted CPU tensor cache changed')
            prefix = int(encoded['input_ids'].shape[1])
            io.require(prefix == proof['input_tokens'] and prefix <= 16384, 'Actual B0 input token budget differs')
            gpu = {key: value.to('cuda') for key, value in encoded.items()}
            io.require(runtime.tensor_signature(gpu) == evidence['tensor_signature'], 'Actual CPU/GPU tensors differ')
            disabled = io.enabled_layers(model)
            duration = F(meta['window_end'])-F(meta['window_start'])
            grammar = make_prefix_constraint(processor.tokenizer, prefix, duration,
                candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            io.save(folder/'request.json', dict(case_id=current, group=group, window_role=meta['window_role'],
                view_roles=meta.get('view_roles', [meta['window_role']]),
                source_name=meta['source_name'], input_path=entry['input_path'], input_sha256=entry['input_sha256'],
                CPU_proof_sha256=entry['proof_sha256'], prompt=runtime.EMPTY_PROMPT, input_evidence=evidence,
                encoded_tensor_sha256=proof['encoded_tensor_sha256'], reference_labels_read=False,
                audio_observed=False, adapter_enabled=True, grammar_allow_empty=True))
            begun += 1
            io.append(out/'attempts.jsonl', dict(event='BEGIN', case_id=current, call_id=begun, utc=io.utc()))
            started = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(**gpu, do_sample=False, max_new_tokens=256,
                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = generated.sequences[0, prefix:]
            raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
            io.save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(),
                selected_token_scores=[score if math.isfinite(score) else str(score) for score in scores],
                generated_score_count=len(generated.scores), output_tokens=len(ids), input_tokens=prefix,
                generation_seconds=time.monotonic()-started, eos_token_ids=eos, actual_model_call=True,
                input_evidence=evidence, adapter_disabled_layers=disabled))
            io.output_tokens(io.read(folder/'raw.json'))
            grammar.assert_complete(ids)
            segments, errors, warnings = runtime.parse_segments(raw, duration, allow_empty=True)
            io.require(segments is not None and not errors, 'Original B0 parser rejected untouched raw')
            done = dict(status='MODEL_OK' if segments else 'LEGAL_EMPTY', case_id=current, group=group,
                window_role=meta['window_role'], view_roles=meta.get('view_roles', [meta['window_role']]),
                source_name=meta['source_name'], source_sha256=meta['source_sha256'],
                segments=segments, parse_errors=errors, parse_warnings=warnings,
                native_ranges=io.native_ranges(segments, meta), source_start_exact=meta['window_start'],
                source_end_exact=meta['window_end'], raw_path=str(folder/'raw.json'), raw_sha256=io.sha(folder/'raw.json'),
                request_sha256=io.sha(folder/'request.json'), input_evidence=evidence, input_tokens=prefix,
                output_tokens=len(ids), new_optimizer_updates=0)
            io.save(folder/'done.json', done)
            receipt = dict(case_id=current, done_path=str(folder/'done.json'), done_sha256=io.sha(folder/'done.json'))
            io.append(out/'attempts.jsonl', dict(event='ACCEPTED', call_id=begun, utc=io.utc(), **receipt))
            entries.append(receipt)
            print(json.dumps(dict(stage='B0', group=group, accepted=len(entries), expected=len(values), case_id=current)), flush=True)
            del encoded, gpu, generated, ids
        io.require(begun == len(entries) == len(values), 'Incomplete unique actual B0 calls')
        io.require(runtime.b_engine.frozen_identity(model, config) == identity['base'] and
                   runtime.b_engine.adapter_identity(model, config) == identity['adapter'], 'Actual base/adapter changed during B0 calls')
        io.save(out/'completion.json', dict(status='PASS_POSITIVE_FIXED40_B0_NEW_CALLS_NOT_FACT_QUALITY', calls=begun,
            group=group, entries=entries, attempts_sha256=io.sha(out/'attempts.jsonl'),
            admission_sha256=io.sha(gate_path), model_identity_sha256=io.sha(out/'model_identity.json'),
            model_parameters=io.MODEL_PARAMETERS, new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_B0_NO_RETRY_OR_EMPTY_FALLBACK', current=current,
            begun=begun, successful_entries=entries, error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success=True, do_not_repeat_success=True))
        raise


def independent_native(segments, meta):
    """Replay source membership by direct clock enumeration, not infer's bisect."""
    points = list(map(F, meta['all_source_exact_pts']))
    origin, end = F(meta['window_start']), F(meta['window_end'])
    result = []
    for first, last in segments:
        first, last = F(str(first)), F(str(last))
        io.require(0 <= first < last <= end-origin, 'Independent raw segment escaped its original native window')
        members = [i for i, point in enumerate(points) if origin+first <= point < origin+last]
        io.require(members and members == list(range(members[0], members[-1]+1)), 'Independent exact segment membership differs')
        result.append([members[0], members[-1]+1])
    return result


def replay(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=True)
    gate, cpu, files, values, gate_path, _, _ = io.accepted_b0(root, group, cpu_path, lock_path)
    _, resource_sha = io.terminal(gate)
    gpu = root/group/'B0/gpu_01'
    complete, by_id = completed_job(gpu, gate, gate_path, len(values))
    io.require(list(by_id) == [entry['case_id'] for entry, _, _ in values], 'Registered B0 order differs from actual model calls')
    out = root/group/'B0/replay_01'
    out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'), new_model_calls=0))
    current, proofs = None, []
    try:
        runtime, processor = io.cpu_processor()
        from constrained_json import ascii_token_candidates, make_prefix_constraint
        candidates = ascii_token_candidates(processor.tokenizer)
        from pathlib import Path
        generation = io.read(Path(io.read(io.CONFIG)['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        for entry, proof, meta in values:
            current = entry['case_id']
            folder = gpu/current
            io.require(Path(by_id[current]['done_path']).resolve() == (folder/'done.json').resolve() and
                       io.sha(folder/'done.json') == by_id[current]['done_sha256'], 'Actual accepted B0 answer changed')
            done, raw, request = [io.read(folder/name) for name in ('done.json', 'raw.json', 'request.json')]
            io.require(done['raw_sha256'] == io.sha(folder/'raw.json') and done['request_sha256'] == io.sha(folder/'request.json') and
                request['CPU_proof_sha256'] == entry['proof_sha256'] and request['input_sha256'] == entry['input_sha256'] and
                request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and request['prompt'] == runtime.EMPTY_PROMPT and
                request['reference_labels_read'] is False and request['audio_observed'] is False and
                done['window_role'] == request['window_role'] == meta['window_role'] and done['source_sha256'] == meta['source_sha256'],
                'Actual B0 raw/input/no-reference/original-role binding differs')
            io.require(done['view_roles'] == request['view_roles'] == meta.get('view_roles', [meta['window_role']]),
                       'Actual shared-view role aliases changed')
            first = io.read(io.locked_ref(proof['first_input_QA_path'], proof['first_input_QA_sha256'], files))
            cached = io.load_cache(proof['encoded_tensor_path'])
            evidence = first['input_evidence']
            io.require(first['status'] == 'PASS_FIRST_INDEPENDENT_POSITIVE_FIXED40_INPUT_QA_PRE_GPU' and
                evidence == proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'] and
                runtime.tensor_signature(cached) == evidence['tensor_signature'], 'Completed pre-GPU input QA/cache binding differs')
            ids = io.output_tokens(raw, done)
            io.require(raw['input_tokens'] == done['input_tokens'] == proof['input_tokens'] and raw['eos_token_ids'] == eos,
                       'Actual original B0 input/EOS denominator differs')
            io.require(processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) == raw['raw_output'],
                       'Independent B0 output ID decoding differs')
            duration = F(meta['window_end'])-F(meta['window_start'])
            grammar = make_prefix_constraint(processor.tokenizer, proof['input_tokens'], duration,
                candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            grammar.assert_complete(ids)
            segments, errors, warnings = runtime.parse_segments(raw['raw_output'], duration, allow_empty=True)
            io.require(segments is not None and not errors and segments == done['segments'] and warnings == done['parse_warnings'] and
                done['status'] == ('MODEL_OK' if segments else 'LEGAL_EMPTY') and
                done['source_start_exact'] == meta['window_start'] and done['source_end_exact'] == meta['window_end'] and
                independent_native(segments, meta) == done['native_ranges'], 'Independent grammar/parser/native result differs')
            path = out/(current+'.json')
            io.save(path, dict(status='PASS_POSITIVE_FIXED40_B0_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA',
                case_id=current, group=group, source_name=meta['source_name'], window_role=meta['window_role'],
                view_roles=meta.get('view_roles', [meta['window_role']]),
                CPU_only=True, input_evidence=evidence, first_input_QA_sha256=proof['first_input_QA_sha256'], post_GPU_vision_processor_calls=0, done_path=str(folder/'done.json'), done_sha256=io.sha(folder/'done.json'),
                raw_sha256=io.sha(folder/'raw.json'), segments=segments, native_ranges=done['native_ranges'],
                new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(case_id=current, proof_path=str(path), proof_sha256=io.sha(path)))
            print(json.dumps(dict(stage='B0_REPLAY', group=group, completed=len(proofs), expected=len(values))), flush=True)
            del cached
        import torch
        io.require(not torch.cuda.is_initialized(), 'Independent B0 replay initialized CUDA')
        io.save(out/'completion.json', dict(status='PASS_POSITIVE_FIXED40_B0_NEW_OUTPUT_QA_NOT_FACT_QUALITY', group=group,
            proofs=proofs, calls=len(proofs), resource_terminal_sha256=resource_sha,
            gpu_completion_sha256=io.sha(gpu/'completion.json'), CPU_only=True, CUDA_initialized=False,
            new_model_calls=0, new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_B0_REPLAY_KEEP_RAW_AND_SUCCESS', current=current,
            successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(), do_not_repeat_success=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('infer', 'replay'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--group', required=True, choices=('facts',))
    parser.add_argument('--cpu-acceptance')
    parser.add_argument('--source-lock')
    args = parser.parse_args()
    if args.stage == 'replay':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    globals()[args.stage](io.root_path(args.root), args.group, args.cpu_acceptance, args.source_lock)


if __name__ == '__main__':
    main()
