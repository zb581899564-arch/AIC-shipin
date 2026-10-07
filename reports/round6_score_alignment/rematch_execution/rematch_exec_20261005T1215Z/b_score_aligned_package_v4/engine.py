"""Actual trained-B LoRA inference with native input shared by acceptance and production."""
from common import *
from fractions import Fraction
import time


def prompt_for(processor):
    temporal = load(BASELINE / 'vendor/temporal_common.py', 'b2_original_temporal_prompt')
    text = processor.apply_chat_template([{'role': 'user', 'content': [{'type': 'text', 'text': temporal.PROMPT}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return text.replace('<|im_start|>user\n', '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>', 1)


def frozen_identity(model, config):
    import torch
    from verify_saved_smoke import canonical_frozen_hash
    value = canonical_frozen_hash(model, torch)
    require(value['sha256'] == config['expected_base_sha256'] and value['parameters'] == config['base_parameters'],
            'B2 actual frozen base differs from trained B')
    return value


def adapter_identity(model, config):
    import torch
    from safetensors.torch import load_file
    from peft import get_peft_model_state_dict
    path = Path(config['b_adapter']) / 'adapter_model.safetensors'
    require(sha(path) == config['b_adapter_sha256'], 'trained B adapter changed')
    saved = load_file(str(path), device='cpu')
    actual = get_peft_model_state_dict(model)
    require(set(actual) == set(saved) and len(actual) == 288, 'B2 adapter tensor inventory differs')
    for name, expected in saved.items():
        value = actual[name].detach().cpu()
        require(torch.equal(value, expected.to(dtype=value.dtype)), 'B2 loaded adapter tensor differs: ' + name)
    require(model.active_adapter == 'default' and not any(p.requires_grad for p in model.parameters()),
            'trained B adapter disabled or a parameter trainable')
    return dict(sha256=config['b_adapter_sha256'], tensors=len(actual), actual_saved_values_equal=True,
                adapter_enabled=True, optimizer_updates=0)


def load_model(config):
    import torch
    import transformers
    import peft
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import unique_parameters
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1' and torch.cuda.is_available(),
            'fixed B2 CUDA runtime required')
    torch.cuda.init()
    base = Qwen3VLForConditionalGeneration.from_pretrained(config['model_dir'], local_files_only=True,
        torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
    model = PeftModel.from_pretrained(base, config['b_adapter'], is_trainable=False).eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    count = sum(parameter.numel() for _, parameter in unique_parameters(model))
    require(count == config['complete_parameters'], 'B2 actual logical parameter count differs')
    evidence = dict(base=frozen_identity(model, config), adapter=adapter_identity(model, config), logical_parameters=count)
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    require(processor.video_processor.size == config['video_size'], 'fixed video size changed')
    return model, processor, evidence


def plan_window(item, clock, start, end, index):
    from native_input import window_from_pts
    arrays = clock['arrays']
    tick = Fraction(arrays['raw_time_base'])
    origin = arrays['raw_first_pts_ticks'] * tick
    points = [float(value * tick) for value in arrays['native_pts_ticks']]
    raw_start, raw_end = float(origin + Fraction(str(start))), float(origin + Fraction(str(end)))
    window = window_from_pts(item['source_path'], item['source_sha256'], points, raw_start, raw_end,
        item['video_id'] + ':B2:' + str(index), height=item['height'], width=item['width'])
    window['window_duration_sec'] = window_duration(start, end)
    return window


def encode_window(processor, window, config):
    import torch
    from native_input import decode_window
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    array, metadata, plan, decoded = decode_window(window)
    with exact_native_pts(processor, plan, metadata['fps']) as native:
        encoded = encode(processor, text=[prompt_for(processor)], videos=[torch.from_numpy(array).permute(0, 3, 1, 2)],
            video_metadata=[metadata], video_size=config['video_size'], max_input=config['max_input_tokens'])
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**decoded, native_processor_identity=native,
                         **identity(processor, encoded, len(array)))


def generate_window(model, processor, encoded, details, duration, candidates):
    import torch
    from constrained_json import make_prefix_constraint, IncompleteConstrainedOutput
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    prefix = int(encoded['input_ids'].shape[1])
    eos = model.generation_config.eos_token_id
    constraint = make_prefix_constraint(processor.tokenizer, prefix, duration,
        candidate_token_ids=candidates, eos_token_ids=[eos] if isinstance(eos, int) else eos, allow_empty=False)
    gpu = encoded.to('cuda')
    with torch.inference_mode():
        generated = model.generate(**gpu, do_sample=False, max_new_tokens=256,
            prefix_allowed_tokens_fn=constraint, return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    ids = generated.sequences[0, prefix:]
    require(len(ids) == len(generated.scores) and all(bool(torch.isfinite(score[0, ids[n]]))
            for n, score in enumerate(generated.scores)), 'nonfinite selected generation score')
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    try:
        constraint.assert_complete(ids)
        parsed, errors, warnings = parse_segments(raw, duration, allow_empty=False)
        if parsed is not None:
            ranges = native_segment_ranges(parsed, details['window_source_pts_sec'],
                                           details['native_processor_identity']['window_start'], duration)
        else:
            ranges = None
    except (IncompleteConstrainedOutput, ValueError) as error:
        parsed, errors, warnings, ranges = None, [type(error).__name__ + ': ' + str(error)], [], None
    return dict(status='MODEL_OK' if parsed is not None else 'PARSE_FAILURE', output_valid=parsed is not None,
        parsed_segments=parsed, parse_errors=errors, parse_warnings=warnings, raw_output=raw,
        video_identity=details, constraint_stats=constraint.stats, generation_time_constraint=True,
        selected_generation_scores_finite=True, adapter_enabled=True, failure_to_empty_conversions=0,
        native_frame_realizability=dict(status='PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY' if parsed is not None else
            'STOP_PARSE_OR_REALIZABILITY', ranges=ranges, not_limited_to_64_samples=True))


def temporal(scope, out):
    config = verify()
    from sft_contract import verify_live_gpu_reservation
    from frame_contract import window_schedule
    from constrained_json import ascii_token_candidates
    verify_live_gpu_reservation()
    _, manifest, clocks = inputs(scope)
    out = Path(out); out.mkdir(exist_ok=True)
    model, processor, model_evidence = load_model(config)
    write(out / 'model_identity.json', model_evidence)
    candidates = ascii_token_candidates(processor.tokenizer)
    started = time.monotonic(); failures = windows = 0
    with (out / 'temporal.jsonl').open('x', encoding='utf-8') as stream:
        for number, item in enumerate(manifest['records'], 1):
            require(sha(item['source_path']) == item['source_sha256'], 'B2 source bytes changed')
            clock = clocks[item['video_id']]
            record = dict(video_id=item['video_id'], targetRatioWH=item['targetRatioWH'], video_path=item['source_path'],
                n_frames=item['n_frames'], fps=item['fps_num'] / item['fps_den'], arm=config['candidate_arm'], windows=[])
            for index, (start, end) in enumerate(window_schedule(item, manifest['kind'], clock)):
                one = time.monotonic(); windows += 1
                try:
                    plan = plan_window(item, clock, start, end, index)
                    encoded, details = encode_window(processor, plan, config)
                    result = generate_window(model, processor, encoded, details, plan['window_duration_sec'], candidates)
                    del encoded
                except Exception as error:
                    result = dict(status='INFERENCE_FAILURE', output_valid=False, parsed_segments=None,
                        parse_errors=[type(error).__name__ + ': ' + str(error)], parse_warnings=[], failure_to_empty_conversions=0)
                result.update(start_sec=start, end_sec=end, index=index, seconds=time.monotonic() - one,
                    clock_branch=clock['branch'], clock_record_sha256=clock['clock_record_sha256'])
                failures += not result['output_valid']; record['windows'].append(result)
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n'); stream.flush()
            progress(out, dict(stage='B2_TEMPORAL', scope=scope, videos=number, total=len(manifest['records']),
                windows=windows, failures=failures, wall_seconds=time.monotonic() - started))
    require(frozen_identity(model, config) == model_evidence['base'], 'frozen base changed during B2 inference')
    write(out / 'temporal.stage.json', dict(status='PASS_TEMPORAL_EXECUTION' if not failures else 'STOP_TEMPORAL_FAILURES',
        videos=len(manifest['records']), windows=windows, invalid_windows=failures,
        output_sha256=sha(out / 'temporal.jsonl'), logical_parameters=config['complete_parameters'],
        adapter_enabled=True, selected_adapter_sha256=config['b_adapter_sha256'], allow_empty=False,
        input_contract=config['b2_input_contract'], source_lock_sha256=sha(HERE / 'source_lock.json'),
        wall_seconds=time.monotonic() - started, optimizer_updates=0, official_score=None))
    require(failures == 0, 'B2 failed windows block package; never convert them to empty')


def probe(scope, out):
    config = verify()
    from sft_contract import verify_live_gpu_reservation
    from constrained_json import ascii_token_candidates
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    import torch
    verify_live_gpu_reservation()
    out = Path(out); out.mkdir(exist_ok=False)
    started = time.monotonic()
    model, processor, model_evidence = load_model(config)
    array = torch.zeros((64, 3, 1080, 1920), dtype=torch.uint8)
    ids = [14 * index for index in range(64)]
    metadata = dict(fps=30, frames_indices=ids, total_num_frames=900, video_backend='synthetic')
    plan = dict(source_frame_ids=ids, source_relative_pts=[index / 30 for index in ids], window_start=0)
    with exact_native_pts(processor, plan, 30) as native:
        encoded = encode(processor, text=[prompt_for(processor)], videos=[array], video_metadata=[metadata],
            video_size=config['video_size'], max_input=config['max_input_tokens'])
        verify_native_encoding(processor, encoded, native)
    details = dict(native_processor_identity=native, window_source_pts_sec=[index / 30 for index in range(900)],
                   **identity(processor, encoded, 64))
    require(8192 < details['input_tokens'] <= 16384, 'long input probe did not exercise old limit')
    torch.cuda.reset_peak_memory_stats()
    result = generate_window(model, processor, encoded, details, 30, ascii_token_candidates(processor.tokenizer))
    require(result['output_valid'] and result['selected_generation_scores_finite'], 'B2 actual long inference failed')
    require(frozen_identity(model, config) == model_evidence['base'], 'base changed during acceptance')
    adapter_identity(model, config)
    write(out / 'probe.stage.json', dict(status='PASS_B2_ACTUAL_TRAINED_ADAPTER_LONG_CUDA_INFERENCE',
        model_identity=model_evidence, input_identity=details, generation=result,
        synthetic_only=True, contest_media_read=False, optimizer_updates=0,
        peak_allocated_mib=torch.cuda.max_memory_allocated() / 2**20, wall_seconds=time.monotonic() - started))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('probe', 'temporal'))
    parser.add_argument('scope'); parser.add_argument('out')
    args = parser.parse_args(); globals()[args.stage](args.scope, args.out)
