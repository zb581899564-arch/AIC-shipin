"""Freeze center-conditioned token inputs, training targets and tail masks."""
import json
import numpy as np
import torch
from common import ROOT, RUN, ARMS, checked, read, ref, write, append, runtime_paths
from geometry import box_for_width, conditioned_target, human_width_target


def pixel_reference(row):
    normalized = row['original_normalized_xyxy']
    x1, y1, x2, y2 = normalized
    return [x1 * row['width'], y1 * row['height'], (x2 - x1) * row['width'], (y2 - y1) * row['height']]


def prompt_for(row, center):
    maximum = min(row['width'], row['height'] * 16 // 9)
    return ('Choose the width of a professional16:9 crop around the supplied frozen focal center. '
        'Preserve important subjects and context without unnecessary zoom. '
        f'Source pixels W={row["width"]}, H={row["height"]}; ratio=16:9; maximum legal width={maximum}. '
        f'Deployment center normalized[0,1]={json.dumps(center,separators=(",",":"))}. '
        'The deployed box is centered there and clamped inside the source. '
        'Return only JSON {"width":integer}, from1 to1000 relative to maximum legal width;1000 keeps the maximum.')


def token_input(processor, row, center, count, answer=None):
    messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt_for(row, center)}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    if text.count('<|image_pad|>') != 1:
        raise ValueError('One fixed image placeholder required')
    text = text.replace('<|image_pad|>', '<|image_pad|>' * count)
    suffix = '' if answer is None else json.dumps(dict(width=answer), separators=(',', ':')) + '<|im_end|>\n'
    values = processor.tokenizer([text + suffix], padding=True, truncation=False, add_special_tokens=False, return_tensors='pt')
    if values['input_ids'].shape[1] >= 2048:
        raise ValueError('Conditioned text overflow; no truncation')
    return values, suffix


def main():
    runtime_paths()
    from transformers import AutoProcessor
    from sft_contract import assistant_labels
    from spatial_baseline import center_to_box, compute_crop_size
    cfg = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    cohort = read(ROOT / 'cohort.json')['rows']
    centers = {r['item_id']: r for r in map(json.loads, (ROOT / 'center_predictions.jsonl').read_text().splitlines())}
    pixels = {r['item_id']: r for r in read(ROOT / 'pixel_acceptance.json')['rows']}
    train, evaluation, cases = [], [], []
    for row in cohort:
        identity = row['item_id']
        center = centers[identity]['center']
        width, height = compute_crop_size(row['width'], row['height'], 16, 9)
        original = center_to_box(*center, row['width'], row['height'], width, height)
        if original != centers[identity]['baseline_box'] or original != box_for_width(row['width'], row['height'], center, 1000):
            raise ValueError('New geometry differs from original deployed center/max-width')
        base = pixels[identity]
        tensor = torch.load(checked(base['tensor']), map_location='cpu', weights_only=True)
        prefix, _ = token_input(processor, row, center, base['image_token_count'])
        image_id = processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')
        if int((prefix['input_ids'] == image_id).sum()) != base['image_token_count']:
            raise ValueError('Image tokens must match the accepted native grid')
        if base['image_token_count'] != int(tensor['image_grid_thw'].prod()) // 4:
            raise ValueError('Visual patch merge/token contract')
        item = dict(item_id=identity, role=row['role'], width=row['width'], height=row['height'], center=center,
            baseline_box=original, pixels=base['tensor'], pixel_signature={k: v for k, v in base['signature'].items() if k in ('pixel_values', 'image_grid_thw')},
            input_ids=prefix['input_ids'][0].tolist(), attention_mask=prefix['attention_mask'][0].tolist(),
            image_tokens=base['image_token_count'], human_bin=0, source_group_basis='author file; original source unknown')
        human = human_width_target(row['width'], row['height'], row['original_normalized_xyxy'])
        item['human_bin'] = 0 if human <= 750 else 1 if human <= 950 else 2
        if row['role'] == 'train':
            optimum, _, bound = conditioned_target(row['width'], row['height'], center, pixel_reference(row))
            targets = dict(W10=human, W01=optimum, W11=optimum)
            encoded = {}
            for value in sorted(set(targets.values())):
                full, suffix = token_input(processor, row, center, base['image_token_count'], value)
                mask = assistant_labels(full['input_ids'][0].tolist(), full['attention_mask'][0].tolist(), item['input_ids'], item['attention_mask'])
                if processor.tokenizer.decode(mask['assistant_token_ids'], skip_special_tokens=False,
                        clean_up_tokenization_spaces=False) != suffix:
                    raise ValueError('Assistant suffix alignment failure')
                encoded[str(value)] = dict(input_ids=full['input_ids'][0].tolist(), attention_mask=full['attention_mask'][0].tolist(),
                    tail_labels=mask['tail_labels'], logits_to_keep=mask['logits_to_keep'], assistant_token_ids=mask['assistant_token_ids'])
            item.update(targets=targets, target_tokens=encoded, conditioned_upper_bound=bound)
            train.append(item)
        else:
            evaluation.append(item)
        cases.append(dict(item_id=identity, role=row['role'], reference_xywh=pixel_reference(row), human_width=human))
        append(ROOT / 'conditioned_input_journal.jsonl', item)
    if len(train) != 602 or len(evaluation) != 160:
        raise ValueError('Registered S1 denominator')
    write(ROOT / 'conditioned_train.json', train)
    write(ROOT / 'conditioned_eval.json', evaluation)
    write(ROOT / 'external_reference.json', cases)
    bins = [sum(r['human_bin'] == i for r in train) for i in range(3)]
    if bins != [100, 172, 330]:
        raise ValueError('Historical602 width prior differs')
    if torch.cuda.is_initialized():
        raise ValueError('CPU-only conditioned input creation')
    write(ROOT / 'conditioned_input_acceptance.json', dict(status='PASS_ALL762_CONDITIONED_TOKENS_PIXELS_AND602_TARGETS',
         train=602, dev=80, confirm=80, human_width_bins=bins, train_inputs=ref(ROOT / 'conditioned_train.json'),
         eval_inputs=ref(ROOT / 'conditioned_eval.json'), reference=ref(ROOT / 'external_reference.json'),
         real_processor_repeated=0, new_visual_encodings=0, human_center_in_inputs=False,
         deployment_centers=ref(ROOT / 'center_predictions.jsonl'), CUDA_initialized=torch.cuda.is_initialized()))


if __name__ == '__main__':
    main()
