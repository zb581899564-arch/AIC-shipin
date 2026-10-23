"""Shared original model interfaces; human targets are never used in generation."""
from functools import lru_cache
import json
import time
import torch
from common import ROOT, checked, read, append, signatures
from geometry import box_for_width


@lru_cache(maxsize=24)
def pixels(path, sha256, size):
    value = torch.load(checked(dict(path=path, sha256=sha256, bytes=size)), map_location='cpu', weights_only=True)
    return {k: value[k] for k in ('pixel_values', 'image_grid_thw')}


def values(item, arm=None):
    shared = pixels(item['pixels']['path'], item['pixels']['sha256'], item['pixels']['bytes'])
    if signatures(shared) != item['pixel_signature']:
        raise ValueError('Shared image input signature')
    tokens = item if arm is None else item['target_tokens'][str(item['targets'][arm])]
    result = dict(shared, input_ids=torch.tensor([tokens['input_ids']], dtype=torch.long),
                  attention_mask=torch.tensor([tokens['attention_mask']], dtype=torch.long))
    if arm:
        result['labels'] = torch.tensor([tokens['tail_labels']], dtype=torch.long)
    return result, tokens.get('logits_to_keep')


def parse_width(raw):
    value = json.loads(raw.strip())
    if not isinstance(value, dict) or set(value) != {'width'} or type(value['width']) is not int or not 1 <= value['width'] <= 1000:
        raise ValueError('Invalid predicted width grammar')
    return value['width']


def generate(model, processor, item, arm, role):
    data, _ = values(item)
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(**{k: v.cuda() for k, v in data.items()}, do_sample=False, num_beams=1,
                                max_new_tokens=48, use_cache=True)
    suffix = output[0, data['input_ids'].shape[1]:].detach().cpu().tolist()
    raw = processor.tokenizer.decode(suffix, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    record = dict(item_id=item['item_id'], arm=arm, role=role, output_ids=suffix, raw=raw,
                  prefix_tokens=data['input_ids'].shape[1], image=item['pixels'], seconds=time.monotonic() - started)
    append(ROOT / f'{role}_{arm}_raw.jsonl', record)
    try:
        width = parse_width(raw)
        prediction = dict(item_id=item['item_id'], arm=arm, role=role, status='VALID', width_relative=width,
                         box=box_for_width(item['width'], item['height'], item['center'], width))
    except (ValueError, TypeError):
        prediction = dict(item_id=item['item_id'], arm=arm, role=role, status='INVALID_PRESERVED', box=None, width_relative=None)
    append(ROOT / f'{role}_{arm}_predictions.jsonl', prediction)
    return prediction
