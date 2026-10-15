"""One same-B coarse pass on frozen new Charades inputs, then CPU replay.

No data acquisition, source selection, reference evaluation or automatic GPU
launcher is included. A separate main-agent admission binds every real input.
"""
import argparse
from bisect import bisect_left
import datetime as dt
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import sys
import time
import traceback

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CAMPAIGN = ROOT/'twenty_hour_five_20261014_v1'
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
PROMPT_SHA = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def save(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())


def append(p, value):
    with Path(p).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        f.flush()
        os.fsync(f.fileno())


def require(value, reason):
    if not value:
        raise ValueError(reason)


def runtime():
    p = ROOT/'temporal_refinement_pilot_20261011/dev_01/runtime.py'
    spec = importlib.util.spec_from_file_location('_charades_coarse_original_runtime', p)
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    helper_path = CAMPAIGN/'local_boundary_v1/code/lb_io.py'
    # The two cache functions are immutable helpers; import their frozen module
    # while retaining its own contract import path, rather than shadowing common.
    sys.path.insert(0, str(helper_path.parent))
    spec = importlib.util.spec_from_file_location('_charades_original_gzip_helper', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(hashlib.sha256(rt.EMPTY_PROMPT.encode()).hexdigest() == PROMPT_SHA, 'Original B0 prompt changed')
    return rt, helper


def checked_base(value):
    root = Path(value).resolve()
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux', 'Linux host required')
    require(root == CAMPAIGN/'charades_coarse_v1', 'Independent fixed coarse output root required')
    return root


def accepted_inputs(root):
    admission = read(root/'gpu_admission.json')
    require(admission['status'] == 'PASS_INDEPENDENT_CHARADES_REAL_CPU_COARSE_ADMISSION', 'No actual CPU admission')
    require(admission['model_parameters'] == 8782459120 and admission['optimizer_updates'] == 0, 'Original same-B scope changed')
    require(admission['reference_available_to_inference'] is False, 'References must not enter inference')
    require(admission['source_input_lock_sha256'] == sha(root/'source_input_lock.json'), 'Input lock changed')
    lock = read(root/'source_input_lock.json')['files']
    require({str(Path(__file__).resolve()), str(root/'coarse_inputs.json'),
             str(root/'protocol.json'), str(root/'official_rule_check.json'),
             str(RUN/'b_score_aligned_package_v4/config.json')} <= set(lock),
            'Input/code/protocol/rules/model-config dependencies must be frozen')
    dependency_roots = (RUN/'b_score_aligned_package_v4',
                        ROOT/'temporal_refinement_pilot_20261011/dev_01',
                        CAMPAIGN/'local_boundary_v1/code')
    required_code = {str(p.resolve()) for directory in dependency_roots for p in directory.glob('*.py')}
    require(required_code <= set(lock), 'Frozen original runtime/cache/helper implementation required')
    model_dir = Path(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'])
    assets = {str(p.resolve()) for p in model_dir.iterdir() if p.is_file() and p.suffix in ('.json', '.txt', '.jinja')}
    require(assets and assets <= set(lock), 'Frozen original processor/tokenizer assets required')
    for p, digest in lock.items():
        require(Path(p).resolve().is_relative_to(ROOT), 'Evidence path escaped project root')
        require(sha(p) == digest, 'Frozen evidence changed: '+p)
    entries = read(root/'coarse_inputs.json')
    require(len(entries) == admission['actual_model_call_budget'] and len({e['case_id'] for e in entries}) == len(entries), 'Exact input denominator changed')
    result = []
    allowed_roots = (CAMPAIGN/'charades_boundary_v1', CAMPAIGN/'charades_boundary_v2')
    for entry in entries:
        for name, digest_name in [('proof_path', 'proof_sha256'), ('input_path', 'input_sha256')]:
            require(any(Path(entry[name]).resolve().is_relative_to(p) for p in allowed_roots), 'Non-admitted media input')
            require(sha(entry[name]) == entry[digest_name], 'CPU input evidence changed')
        cpu, meta = read(entry['proof_path']), read(entry['input_path'])
        require(cpu['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and cpu['CPU_only'] and
                cpu['case_id'] == meta['case_id'] == entry['case_id'] and cpu['source_name'] == meta['source_name'], 'Actual original CPU processor proof required')
        require(cpu['input_sha256'] == entry['input_sha256'] and cpu['input_tokens'] <= 16384 and
                cpu['input_evidence']['physical_frames'] == 64 and len(set(meta['source_frame_ordinals'])) == 64, 'Native64 input budget')
        require(meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
                cpu['input_evidence']['prompt_sha256'] == PROMPT_SHA, 'Fixed no-reference input prompt')
        require(sha(meta['frame_array_path']) == meta['frame_array_sha256'] and
                sha(cpu['encoded_tensor_path']) == cpu['encoded_tensor_sha256'], 'Actual cached RGB/tensors changed')
        require(cpu['encoded_tensor_format'] == 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1', 'Lossless accepted cache required')
        require({entry['proof_path'], entry['input_path'], meta['frame_array_path'],
                 cpu['encoded_tensor_path']} <= set(lock), 'Actual input files absent from source lock')
        result.append((entry, cpu, meta))
    return admission, result


def native_ranges(segments, meta):
    pts = list(map(F, meta['all_source_exact_pts']))
    lo, hi = F(meta['window_start']), F(meta['window_end'])
    require(len(pts) == meta['source_total_frames'] and pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:])), 'Complete original clock')
    output = []
    for a, b in segments:
        a, b = F(str(a)), F(str(b))
        require(0 <= a < b <= hi-lo, 'Parser interval outside its original window')
        first, end = bisect_left(pts, lo+a), bisect_left(pts, lo+b)
        require(first < end and list(range(first, end)) == [i for i, p in enumerate(pts) if lo+a <= p < lo+b], 'Exact nonempty native membership')
        output.append([first, end])
    return output


def infer(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') != '', 'GPU parent must retain actual CUDA index')
    admission, values = accepted_inputs(root)
    deadline = dt.datetime.fromisoformat(admission['deadline'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'New job after deadline')
    rt, helper = runtime()
    from sft_contract import verify_live_gpu_reservation
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    import torch
    verify_live_gpu_reservation()
    require(read(ROOT/'improvement_round1/active_gpu_job.json')['name'] == admission['gpu_job_name'], 'Wrong unique shared GPU job')
    out = root/'gpu_01'
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(pid=os.getpid(), admission_sha256=sha(root/'gpu_admission.json'), new_optimizer_updates=0))
    with (out/'attempts.jsonl').open('x'):
        pass
    entries, begun, current = [], 0, None
    try:
        config = read(RUN/'b_score_aligned_package_v4/config.json')
        model, processor, identity = rt.b_engine.load_model(config)
        require(identity['logical_parameters'] == 8782459120 and identity['base']['sha256'] == BASE_SHA and identity['adapter']['sha256'] == ADAPTER_SHA, 'Actual original B weights/parameter identity')
        helper.verify_model(model, identity)
        save(out/'model_identity.json', dict(identity=identity, adapter_enabled_for_all_calls=True, optimizer_updates=0))
        candidates = ascii_token_candidates(processor.tokenizer)
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        for entry, cpu, meta in values:
            current = entry['case_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            encoded = helper.load_tensor_cache(cpu['encoded_tensor_path'])
            require(rt.tensor_signature(encoded) == cpu['input_evidence']['tensor_signature'], 'Cached actual CPU tensor signature')
            prefix = int(encoded['input_ids'].shape[1])
            require(prefix == cpu['input_tokens'], 'Actual input token budget')
            gpu = {k: v.to('cuda') for k, v in encoded.items()}
            require(rt.tensor_signature(gpu) == cpu['input_evidence']['tensor_signature'], 'Actual CPU/GPU tensor equality')
            disabled = [bool(m.disable_adapters) for m in model.modules() if hasattr(m, 'disable_adapters') and hasattr(m, 'lora_A')]
            require(disabled == [False]*144, 'Original time adapter must be enabled')
            lo, hi = F(meta['window_start']), F(meta['window_end'])
            grammar = make_prefix_constraint(processor.tokenizer, prefix, hi-lo, candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            save(folder/'request.json', dict(case_id=current, source_name=meta['source_name'],
                input_path=entry['input_path'], input_sha256=entry['input_sha256'], CPU_proof_sha256=entry['proof_sha256'],
                prompt=rt.EMPTY_PROMPT, input_evidence=cpu['input_evidence'], reference_labels_read=False,
                encoded_tensor_sha256=cpu['encoded_tensor_sha256'], adapter_enabled=True))
            append(out/'attempts.jsonl', dict(event='BEGIN', case_id=current, call_id=begun+1))
            begun += 1
            started = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(**gpu, do_sample=False, max_new_tokens=256, prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
            torch.cuda.synchronize()
            ids = generated.sequences[0, prefix:]
            raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            scores = [float(s[0, int(t)]) for s, t in zip(generated.scores, ids)]
            save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(), selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                generated_score_count=len(generated.scores), output_tokens=len(ids), input_tokens=prefix, generation_seconds=time.monotonic()-started,
                eos_token_ids=eos, actual_model_call=True, input_evidence=cpu['input_evidence'], adapter_disabled_layers=disabled))
            require(0 < len(ids) <= 256 and len(scores) == len(ids) and all(map(math.isfinite, scores)), 'Finite real output token denominator')
            grammar.assert_complete(ids)
            segments, errors, warnings = rt.parse_segments(raw, hi-lo, allow_empty=True)
            require(segments is not None and not errors, 'Original parser rejects raw')
            done = dict(status='MODEL_OK' if segments else 'LEGAL_EMPTY', case_id=current, source_name=meta['source_name'],
                segments=segments, parse_errors=errors, parse_warnings=warnings, native_ranges=native_ranges(segments, meta),
                source_start_exact=str(lo), source_end_exact=str(hi), raw_path=str(folder/'raw.json'), raw_sha256=sha(folder/'raw.json'),
                request_sha256=sha(folder/'request.json'), input_evidence=cpu['input_evidence'], input_tokens=prefix, output_tokens=len(ids), new_optimizer_updates=0)
            save(folder/'done.json', done)
            receipt = dict(case_id=current, done_path=str(folder/'done.json'), done_sha256=sha(folder/'done.json'))
            append(out/'attempts.jsonl', dict(event='ACCEPTED', call_id=begun, **receipt))
            entries.append(receipt)
            print(json.dumps(dict(accepted=len(entries), budget=len(values), case_id=current)), flush=True)
            del gpu, encoded, generated, ids
        require(begun == len(entries) == len(values), 'Unique complete actual calls')
        require(rt.b_engine.frozen_identity(model, config) == identity['base'], 'Original base changed during inference')
        require(rt.b_engine.adapter_identity(model, config) == identity['adapter'], 'Original trained adapter changed during inference')
        save(out/'completion.json', dict(status='PASS_NEW_CHARADES_COARSE_CALLS_NOT_QUALITY', calls=begun, entries=entries,
            attempts_sha256=sha(out/'attempts.jsonl'), admission_sha256=sha(root/'gpu_admission.json'), model_identity_sha256=sha(out/'model_identity.json')))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), current=current, begun=begun, successful_entries=entries, do_not_repeat_success=True))
        raise


def replay(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU child must hide own CUDA')
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    admission, values = accepted_inputs(root)
    out = root/'gpu_01'
    complete = read(out/'completion.json')
    resource_path = RUN/('controller/'+admission['gpu_job_name']+'.resource.json')
    terminal = read(resource_path)
    ledger = [json.loads(x) for x in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    require([x for x in ledger if x['name'] == admission['gpu_job_name']] == [terminal] and terminal['status'] == 'completed' and terminal['exit_code'] == 0, 'Unique natural GPU terminal')
    require(complete['calls'] == len(values) and complete['attempts_sha256'] == sha(out/'attempts.jsonl') and
            complete['admission_sha256'] == sha(root/'gpu_admission.json') and complete['model_identity_sha256'] == sha(out/'model_identity.json'), 'Complete bound real execution')
    journal = [json.loads(x) for x in (out/'attempts.jsonl').read_text().splitlines() if x.strip()]
    require(len(journal) == 2*len(values), 'Actual call journal denominator')
    rt, helper = runtime()
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    processor = AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    candidates = ascii_token_candidates(processor.tokenizer)
    replay_root = root/'replay_01'
    replay_root.mkdir(exist_ok=False)
    accepted = {e['case_id']: e for e in complete['entries']}
    proofs = []
    for i, (entry, cpu, meta) in enumerate(values):
        case = entry['case_id']
        require(journal[2*i]['event'] == 'BEGIN' and journal[2*i+1]['event'] == 'ACCEPTED' and
                all(e['case_id'] == case and e['call_id'] == i+1 for e in journal[2*i:2*i+2]), 'Unique ordered actual model calls')
        folder = out/case
        require(sha(folder/'done.json') == accepted[case]['done_sha256'], 'Actual accepted answer changed')
        done, raw, request = [read(folder/n) for n in ('done.json', 'raw.json', 'request.json')]
        require(done['raw_sha256'] == sha(folder/'raw.json') and done['request_sha256'] == sha(folder/'request.json') and
                request['CPU_proof_sha256'] == entry['proof_sha256'] and request['input_sha256'] == entry['input_sha256'] and
                request['reference_labels_read'] is False and request['prompt'] == rt.EMPTY_PROMPT and raw['actual_model_call'] is True, 'Original actual raw/input/no-reference binding')
        # This is the first independent replay of these new inputs, not another
        # preparation. All successfully replayed inputs are retained and never rerun.
        frames = rt.baseline_frames(meta)
        encoded, evidence = rt.encode(processor, meta, frames, F(meta['window_start']), rt.EMPTY_PROMPT)
        cached = helper.load_tensor_cache(cpu['encoded_tensor_path'])
        require(evidence == cpu['input_evidence'] == raw['input_evidence'] == request['input_evidence'] == done['input_evidence'] and
                rt.tensor_signature(cached) == evidence['tensor_signature'], 'Independent actual RGB/CPU/cache tensor replay')
        ids, scores = raw['output_token_ids'], raw['selected_token_scores']
        require(0 < len(ids) == len(scores) == raw['output_tokens'] == raw['generated_score_count'] <= 256 and
                all(type(t) is int and t >= 0 for t in ids) and all(type(s) in (int, float) and math.isfinite(s) for s in scores) and
                raw['adapter_disabled_layers'] == [False]*144, 'Actual output token/score/adapter denominator')
        require(processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) == raw['raw_output'], 'Independent output token decoding')
        grammar = make_prefix_constraint(processor.tokenizer, cpu['input_tokens'], F(meta['window_end'])-F(meta['window_start']),
            candidate_token_ids=candidates, eos_token_ids=raw['eos_token_ids'], allow_empty=True)
        grammar.assert_complete(ids)
        segments, errors, warnings = rt.parse_segments(raw['raw_output'], F(meta['window_end'])-F(meta['window_start']), allow_empty=True)
        require(not errors and segments == done['segments'] and warnings == done['parse_warnings'] and native_ranges(segments, meta) == done['native_ranges'], 'Independent parser/native half-open membership')
        p = replay_root/(case+'.json')
        save(p, dict(status='PASS_INDEPENDENT_CPU_TENSOR_TOKEN_PARSER_NATIVE_REPLAY', case_id=case, source_name=meta['source_name'],
            CPU_only=True, input_evidence=evidence, done_sha256=sha(folder/'done.json'), raw_sha256=sha(folder/'raw.json'),
            segments=segments, native_ranges=done['native_ranges'], new_model_calls=0, new_optimizer_updates=0))
        proofs.append(dict(case_id=case, proof_path=str(p), proof_sha256=sha(p)))
        print(json.dumps(dict(completed_replays=len(proofs), total=len(values))), flush=True)
        del encoded, cached, frames
    import torch
    require(not torch.cuda.is_initialized(), 'Independent replay initialized CUDA')
    save(replay_root/'completion.json', dict(status='PASS_ALL_NEW_CHARADES_COARSE_INPUT_OUTPUT_REPLAYS_NOT_QUALITY',
        calls=len(proofs), proofs=proofs, resource_terminal_sha256=sha(resource_path), gpu_completion_sha256=sha(out/'completion.json'), new_model_calls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['infer', 'replay'])
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    output = checked_base(args.root)
    try:
        globals()[args.stage](output)
    except BaseException as error:
        failure = output/(args.stage+'_failure.json')
        if not failure.exists():
            save(failure, dict(stage=args.stage, error=repr(error), traceback=traceback.format_exc(),
                              preserve_all_success=True, successful_stages_must_not_repeat=True))
        raise
