"""First frozen-BASE centers for train/dev/confirm, with no human geometry read."""
import time
import torch
from common import ROOT, RUN, checked, read, ref, write, append, runtime_paths, signatures


def main():
    runtime_paths()
    from spatial_baseline import Qwen3VL, parse_focus_norm, compute_crop_size, center_to_box
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    cfg = read(RUN / 'b_score_aligned_package_v4/config.json')
    wrapper = Qwen3VL(cfg['model_dir'], max_pixels=131072, device_map={'': 'cuda:0'}, attn_implementation='sdpa')
    model, processor = wrapper.model, wrapper.processor
    model.eval().requires_grad_(False)
    if sum(p.numel() for p in model.parameters()) != 8767123696:
        raise ValueError('Exact protected BASE parameter inventory')
    # A label-free input manifest exposes only geometry dimensions and the shared pixels.
    dimensions = read(ROOT / 'center_dimensions.json')
    by_id = {r['item_id']: r for r in dimensions}
    inputs = read(ROOT / 'pixel_acceptance.json')['rows']
    results = []
    started = time.monotonic()
    for index, item in enumerate(inputs):
        value = torch.load(checked(item['tensor']), map_location='cpu', weights_only=True)
        if signatures(value) != item['signature']:
            raise ValueError('BASE input mismatch')
        t0 = time.monotonic()
        with torch.inference_mode():
            output = model.generate(**{k: v.cuda() for k, v in value.items()}, max_new_tokens=96,
                do_sample=False, num_beams=1, use_cache=True)
        ids = output[0, value['input_ids'].shape[1]:].cpu().tolist()
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        append(ROOT / 'center_raw.jsonl', dict(item_id=item['item_id'], input=item['tensor'], ids=ids, raw=raw,
                                              seconds=time.monotonic() - t0))
        size = by_id[item['item_id']]
        center = parse_focus_norm(raw, size['width'], size['height'])
        if center is None:
            raise ValueError('BASE center parse failure; do not replace with annotation or default')
        width, height = compute_crop_size(size['width'], size['height'], 16, 9)
        row = dict(item_id=item['item_id'], center=list(center), baseline_box=center_to_box(*center, size['width'], size['height'], width, height))
        append(ROOT / 'center_predictions.jsonl', row)
        results.append(row)
        if index == 7:
            write(ROOT / 'center_throughput8.json', dict(first8_seconds=time.monotonic() - started, outputs=8,
                 training_updates_frozen_after_cost_profile=50, no_quality_labels_read=True))
        if (index + 1) % 40 == 0:
            print('BASE_CENTERS', index + 1, flush=True)
    write(ROOT / 'center_completion.json', dict(status='PASS762_FIRST_FROZEN_BASE_CENTERS', outputs=len(results),
          actual_generations=len(results), actual_training_updates=0, parameters=8767123696,
          raw=ref(ROOT / 'center_raw.jsonl'), predictions=ref(ROOT / 'center_predictions.jsonl'),
          peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
