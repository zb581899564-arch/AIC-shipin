"""Explicit B0 recovery: adopt one completed pre-GPU input QA without re-encoding.

The original inference body and all output token/grammar/parser/native gates
are unchanged. Original failed evidence and primary tensors are retained.
"""
import argparse
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import time
import traceback

import model_common as io


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
        io.save(out/'completion.json', dict(status='PASS_ALL_RECALL_B0_CALLS_NOT_QUALITY', calls=begun,
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


FIRST_QA_STATUS = 'PASS_FIRST_INDEPENDENT_RECALL_INPUT_REPLAY_RECOVERY_02'


def adopt_pre_gpu_input_qa(root, group, cpu, files, entry, proof, meta, runtime, cached):
    """Accept only the exact locked recovery QA; never perform another encode."""
    case = entry['case_id']
    io.require(proof['pre_GPU_first_input_replay_done'] is True and
        case in cpu['pre_GPU_first_input_replay_cases'] and
        proof['input_evidence_origin'] == 'FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU' and
        proof['primary_encode_evidence_was_not_saved'] is True and
        proof['primary_processor_encodes_original_attempt'] == 1 and
        proof['new_primary_processor_encodes_in_recovery'] == 0,
        'Only the exact completed first input QA can replace this post-GPU input encode')
    registration_path = root/'input_recovery_registration_02.json'
    registration_path = io.locked_ref(str(registration_path), files[str(registration_path)], files)
    reg = io.read(registration_path)
    own = str(Path(__file__).resolve())
    io.require(reg['status'] == 'REGISTERED_EXPLICIT_RECALL_INPUT_RECOVERY_V2' and reg['group'] == group and
        reg['retained_actual_case_id'] == case and reg['retained_source_name'] == meta['source_name'] and
        reg['known_successful_primary_encodes'] == reg['known_successful_source_RGB_decodes'] == 1 and
        reg['known_successful_first_input_replays'] == 0 and
        reg['required_code_files'][own] == files[own] == io.sha(own),
        'New recovery implementation or the sole retained input scope is not frozen')
    for name in ('retained_input_ref', 'retained_tensor_ref', 'retained_frames_ref', 'original_failure_ref'):
        ref = reg[name]
        io.locked_ref(ref['path'], ref['sha256'], files)
    io.require(reg['retained_input_ref']['path'] == entry['input_path'] and
        reg['retained_input_ref']['sha256'] == entry['input_sha256'] and
        reg['retained_tensor_ref']['path'] == proof['encoded_tensor_path'] and
        reg['retained_tensor_ref']['sha256'] == proof['encoded_tensor_sha256'] and
        reg['retained_frames_ref']['path'] == meta['frame_array_path'] and
        reg['retained_frames_ref']['sha256'] == meta['frame_array_sha256'],
        'Recovery metadata/cache/RGB differs from exact retained primary artifacts')
    qa_path = io.locked_ref(proof['pre_GPU_first_input_replay_path'], proof['pre_GPU_first_input_replay_sha256'], files)
    qa_root = root/group/'first_input_replay_recovery_02'
    io.require(qa_path == qa_root/'proof.json', 'First input QA path escaped its independent fixed recovery stage')
    qa = io.read(qa_path)
    io.require(qa['status'] == FIRST_QA_STATUS and qa['case_id'] == meta['case_id'] == proof['case_id'] == case and
        qa['source_name'] == proof['source_name'] == meta['source_name'] and qa['group'] == proof['group'] == group and
        qa['input_path'] == entry['input_path'] and qa['input_sha256'] == entry['input_sha256'] and
        qa['retained_tensor_path'] == proof['encoded_tensor_path'] and qa['retained_tensor_sha256'] == proof['encoded_tensor_sha256'] and
        qa['frame_array_sha256'] == meta['frame_array_sha256'] and
        qa['input_evidence'] == proof['input_evidence'] and
        qa['input_evidence_origin'] == 'FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU_NOT_OLD_PRIMARY_RECEIPT' and
        qa['full_serialization_signature'] == proof['full_serialization_signature'] and
        qa['retained_primary_and_independent_tensors_bit_equal'] is True and
        qa['original_primary_evidence_was_not_saved'] is True and qa['old_failure_ref'] == reg['original_failure_ref'] and
        qa['old_primary_processor_encodes'] == 1 and qa['new_primary_processor_encodes'] == 0 and
        qa['actual_first_independent_input_replays'] == qa['actual_new_vision_processor_calls'] == 1 and
        qa['post_GPU_vision_processor_replay_for_this_view_forbidden'] is True and
        qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
        qa['media_decodes'] == qa['new_model_calls'] == qa['new_optimizer_updates'] == 0,
        'Strict successful first independent input QA/cache/evidence accounting differs')
    evidence_path = io.locked_ref(qa['encode_evidence_path'], qa['encode_evidence_sha256'], files)
    io.require(evidence_path == qa_root/'encode_evidence.json' and io.read(evidence_path) == qa['input_evidence'],
        'First independently observed encode evidence is not the exact immutable saved payload')
    input_evidence_path = io.locked_ref(proof['input_evidence_path'], proof['input_evidence_sha256'], files)
    io.require(io.read(input_evidence_path) == qa['input_evidence'] and
        runtime.tensor_signature(cached) == qa['input_evidence']['tensor_signature'] and
        int(cached['input_ids'].shape[1]) == proof['input_tokens'],
        'Current actual cached tensor/input tokens differ from first independent QA')
    completion_path = qa_root/'completion.json'
    completion_path = io.locked_ref(str(completion_path), files[str(completion_path)], files)
    completion = io.read(completion_path)
    io.require(completion['status'] == FIRST_QA_STATUS and completion['group'] == group and completion['case_id'] == case and
        completion['proof_path'] == str(qa_path) and completion['proof_sha256'] == proof['pre_GPU_first_input_replay_sha256'] and
        completion['old_failure_preserved'] is True and completion['old_cache_modified'] is False and
        completion['primary_encode_repeated'] is False and completion['actual_first_independent_input_replays'] == 1 and
        completion['new_model_calls'] == 0, 'Incomplete or altered first independent input QA completion')
    return qa['input_evidence'], dict(proof_path=str(qa_path), proof_sha256=proof['pre_GPU_first_input_replay_sha256'],
        encode_evidence_path=str(evidence_path), encode_evidence_sha256=qa['encode_evidence_sha256'],
        retained_tensor_sha256=qa['retained_tensor_sha256'], adopted_completed_first_independent_input_replay=True,
        additional_media_decodes=0, additional_vision_processor_calls=0)


def replay(root, group, cpu_path=None, lock_path=None):
    io.host(cpu=True)
    gate, cpu, files, values, gate_path, _, _ = io.accepted_b0(root, group, cpu_path, lock_path)
    _, resource_sha = io.terminal(gate)
    gpu = root/group/'B0/gpu_01'
    complete, by_id = io.completed_job(gpu, gate, gate_path, len(values), 'B0')
    io.require(list(by_id) == [entry['case_id'] for entry, _, _ in values], 'Registered B0 order differs from actual model calls')
    out = root/group/'B0/replay_01'
    out.mkdir(parents=True, exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group, CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'), new_model_calls=0))
    current, proofs, adopted_cases = None, [], []
    try:
        expected_pre_qa = cpu['pre_GPU_first_input_replay_cases']
        actual_pre_qa = [entry['case_id'] for entry, proof, _ in values if proof.get('pre_GPU_first_input_replay_done') is True]
        io.require(len(expected_pre_qa) == 1 and expected_pre_qa == actual_pre_qa and
            cpu['post_GPU_first_input_replay_pending_cases'] == [entry['case_id'] for entry, proof, _ in values
                if proof.get('pre_GPU_first_input_replay_done') is not True],
            'Recovery requires the exact one completed pre-GPU QA and complete remaining input replay denominator')
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
            cached = io.load_cache(proof['encoded_tensor_path'])
            frames, encoded, adoption = None, None, None
            if proof.get('pre_GPU_first_input_replay_done') is True:
                evidence, adoption = adopt_pre_gpu_input_qa(root, group, cpu, files, entry, proof, meta, runtime, cached)
                adopted_cases.append(current)
            else:
                io.require(proof['pre_GPU_first_input_replay_done'] is False and
                    proof['pre_GPU_first_input_replay_path'] is None and proof['pre_GPU_first_input_replay_sha256'] is None and
                    proof['input_evidence_origin'] == 'NEW_PRIMARY_ENCODE' and proof['primary_encode_evidence_was_not_saved'] is False,
                    'A pending first input replay must not impersonate completed pre-GPU QA')
                frames = runtime.baseline_frames(meta)
                encoded, evidence = runtime.encode(processor, meta, frames, F(meta['window_start']), runtime.EMPTY_PROMPT)
            io.require(evidence == proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'] and
                       runtime.tensor_signature(cached) == evidence['tensor_signature'], 'First independent real RGB/native-processor/cache replay differs')
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
            io.save(path, dict(status='PASS_INDEPENDENT_RECALL_B0_TENSOR_TOKEN_GRAMMAR_PARSER_NATIVE_REPLAY',
                case_id=current, group=group, source_name=meta['source_name'], window_role=meta['window_role'],
                view_roles=meta.get('view_roles', [meta['window_role']]),
                CPU_only=True, input_evidence=evidence, done_path=str(folder/'done.json'), done_sha256=io.sha(folder/'done.json'),
                raw_sha256=io.sha(folder/'raw.json'), segments=segments, native_ranges=done['native_ranges'],
                first_independent_input_replay_adopted_pre_GPU=adoption is not None,
                pre_GPU_first_input_replay_adoption=adoption,
                post_GPU_additional_vision_processor_calls=0 if adoption is not None else 1,
                post_GPU_additional_media_decodes=0, new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(case_id=current, proof_path=str(path), proof_sha256=io.sha(path)))
            print(json.dumps(dict(stage='B0_REPLAY', group=group, completed=len(proofs), expected=len(values))), flush=True)
            del encoded, cached, frames
        import torch
        io.require(not torch.cuda.is_initialized(), 'Independent B0 replay initialized CUDA')
        io.require(adopted_cases == expected_pre_qa, 'Every registered pre-GPU first QA must be adopted exactly once')
        io.save(out/'completion.json', dict(status='PASS_ALL_RECALL_B0_INDEPENDENT_REPLAYS_NOT_QUALITY', group=group,
            proofs=proofs, calls=len(proofs), resource_terminal_sha256=resource_sha,
            gpu_completion_sha256=io.sha(gpu/'completion.json'), CPU_only=True, CUDA_initialized=False,
            first_independent_input_replays_adopted_pre_GPU=adopted_cases,
            post_GPU_additional_vision_processor_calls=len(values)-len(adopted_cases),
            adopted_pre_GPU_input_additional_vision_processor_calls=0,
            post_GPU_additional_media_decodes=0, total_first_independent_input_replays=len(values),
            new_model_calls=0, new_optimizer_updates=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_B0_REPLAY_KEEP_RAW_AND_SUCCESS', current=current,
            successful_proofs=proofs, error=repr(error), traceback=traceback.format_exc(), do_not_repeat_success=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('infer', 'replay'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--group', required=True, choices=('dev', 'confirm'))
    parser.add_argument('--cpu-acceptance')
    parser.add_argument('--source-lock')
    args = parser.parse_args()
    if args.stage == 'replay':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    globals()[args.stage](io.root_path(args.root), args.group, args.cpu_acceptance, args.source_lock)


if __name__ == '__main__':
    main()
