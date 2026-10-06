#!/usr/bin/env python3
"""Automatic local inference on the frozen AIC test index; no labels or API calls."""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

R5 = Path('/home/inspur/aic_video_work/temporal_round5')
sys.path.insert(0, str(R5 / 'scripts'))
import temporal_common as tc

BASE_MODEL = '/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct'
INDEX = Path('/home/inspur/aic_video_work/inference/test_index.json')
WINDOW_SEC = 30.0  # below the maximum training clip length (32.134 s)


def write_jsonl(f, record):
    f.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
    f.flush()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arm', required=True, choices=['S1_FRESH', 'S2_WARM'])
    p.add_argument('--adapter', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--max-new-tokens', type=int, default=256)
    a = p.parse_args()
    adapter = Path(a.adapter)
    assert (adapter / 'adapter_model.safetensors').is_file()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    items = json.loads(INDEX.read_text())
    assert len(items) == 174 and len({r['video_id'] for r in items}) == 174
    if a.limit:
        items = items[:a.limit]
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                vid = record['video_id']
                if vid in done:
                    raise RuntimeError(f'duplicate existing result: {vid}')
                done.add(vid)
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from peft import PeftModel

    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
        low_cpu_mem_usage=True, attn_implementation='sdpa')
    model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False)
    model.eval()
    processor = AutoProcessor.from_pretrained(BASE_MODEL, min_pixels=tc.MAX_PIXELS,
                                              max_pixels=tc.MAX_PIXELS)
    # Initialize CUDA before loading decord's native video libraries. Importing
    # decord first segfaults this host during Torch's CUDA allocator warmup.
    import decord
    messages = [{'role': 'user', 'content': [{'type': 'text', 'text': tc.PROMPT}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True, enable_thinking=False)
    prompt = prompt.replace('<|im_start|>user\n',
                            '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>', 1)
    with out.open('a', encoding='utf-8') as f:
        for i, item in enumerate(items, 1):
            vid = str(item['video_id'])
            if vid in done:
                continue
            video_path = item['video_path']
            vr = decord.VideoReader(video_path)
            n_frames = len(vr)
            fps = float(vr.get_avg_fps())
            if n_frames <= 1 or fps <= 0:
                raise RuntimeError(f'invalid video metadata for {vid}')
            duration = n_frames / fps
            windows = []
            start = 0.0
            while start < duration - 1e-6:
                end = min(start + WINDOW_SEC, duration)
                if end - start < 0.2:
                    break
                windows.append((start, end))
                start = end
            result = {'video_id': vid, 'arm': a.arm,
                      'targetRatioWH': item['targetRatioWH'],
                      'n_frames': n_frames, 'fps': fps, 'duration_sec': duration,
                      'window_sec': WINDOW_SEC, 'adapter': str(adapter),
                      'windows': []}
            for wi, (start, end) in enumerate(windows):
                w = {'index': wi, 'start_sec': round(start, 6),
                     'end_sec': round(end, 6), 'duration_sec': round(end-start, 6)}
                try:
                    arr, md, info = tc.build_virtual_clip(video_path, start, end)
                    video = torch.from_numpy(arr).permute(0, 3, 1, 2)
                    model_inputs = processor(text=[prompt], videos=[video],
                                             video_metadata=[md], padding=True,
                                             do_sample_frames=False,
                                             return_tensors='pt').to('cuda')
                    torch.cuda.reset_peak_memory_stats()
                    t0 = time.time()
                    with torch.inference_mode():
                        generated = model.generate(**model_inputs, do_sample=False,
                                                   max_new_tokens=a.max_new_tokens)
                    torch.cuda.synchronize()
                    w['seconds'] = round(time.time() - t0, 2)
                    w['peak_memory_mib'] = round(torch.cuda.max_memory_allocated()/2**20, 1)
                    trimmed = [g[len(model_inputs['input_ids'][0]):] for g in generated]
                    raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                                 clean_up_tokenization_spaces=False)[0]
                    parsed, errors, warnings = tc.parse_segments(raw, end-start)
                    w.update(raw_output=raw, parsed_segments=parsed,
                             parse_errors=errors, parse_warnings=warnings,
                             output_valid=parsed is not None,
                             n_sampled=info['n_sampled'])
                except Exception as exc:
                    w.update(raw_output='', parsed_segments=None,
                             parse_errors=[f'{type(exc).__name__}: {exc}'],
                             output_valid=False)
                result['windows'].append(w)
            write_jsonl(f, result)
            done.add(vid)
            print(f'[{i}/{len(items)}] video={vid} windows={len(windows)} '
                  f'valid={sum(w["output_valid"] for w in result["windows"])}', flush=True)
    print(f'completed={len(done)} output={out}', flush=True)


if __name__ == '__main__':
    main()
