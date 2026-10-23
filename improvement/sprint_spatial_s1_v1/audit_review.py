"""First independent input/token/grammar/geometry QA followed by fixed risk review."""
import argparse
import json
import math
import numpy as np
import torch
from common import ROOT, RUN, ARMS, checked, read, ref, write, runtime_paths, signatures
from geometry import risk_summary


def raw_iou(box, reference):
    x, y, width = box
    height = width * 9 / 16
    x1, y1, rw, rh = reference
    x2, y2 = x1 + rw, y1 + rh
    overlap = max(0., min(x + width, x2) - max(x, x1)) * max(0., min(y + height, y2) - max(y, y1))
    return overlap / (width * height + rw * rh - overlap)


def independent_box(item, relative):
    width = max(1, min(item['width'], int(item['height'] * 16 // 9)) * relative // 1000)
    height = width * 9 / 16
    px = item['center'][0] * item['width'] - width * .5
    py = item['center'][1] * item['height'] - height * .5
    return [int(round(max(0., min(px, item['width'] - width)))),
            int(round(max(0., min(py, math.floor(item['height'] - height + 1e-9))))), width]


def audit_arm(arm, role, tokenizer, evaluation, references):
    rows = [r for r in evaluation if r['role'] == role]
    predictions = [json.loads(s) for s in (ROOT / f'{role}_{arm}_predictions.jsonl').read_text().splitlines()]
    raw = [json.loads(s) for s in (ROOT / f'{role}_{arm}_raw.jsonl').read_text().splitlines()]
    if len(rows) != 80 or len(predictions) != 80 or len(raw) != 80:
        raise ValueError('Missing outputs cannot turn into empty crop')
    expected_ids = {r['item_id'] for r in rows}
    if {r['item_id'] for r in predictions} != expected_ids or {r['item_id'] for r in raw} != expected_ids:
        raise ValueError('Duplicate or missing evaluation identity')
    by_id = {r['item_id']: r for r in rows}
    by_raw = {r['item_id']: r for r in raw}
    losses, candidates, widths, bins, detail = [], [], [], [], []
    for prediction in predictions:
        identity = prediction['item_id']
        item, output = by_id[identity], by_raw[identity]
        saved = torch.load(checked(item['pixels']), map_location='cpu', weights_only=True)
        shared = {k: saved[k] for k in ('pixel_values', 'image_grid_thw')}
        if signatures(shared) != item['pixel_signature']:
            raise ValueError('QA accepted image tensor changed')
        if tokenizer.decode(output['output_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False) != output['raw']:
            raise ValueError('Independent saved output ids decode mismatch')
        if output['prefix_tokens'] != len(item['input_ids']) or item['pixels'] != output['image']:
            raise ValueError('Output tied to different prefix/image')
        if prediction['status'] == 'VALID':
            obj = json.loads(output['raw'].strip())
            if not isinstance(obj, dict) or set(obj) != {'width'} or type(obj['width']) is not int or not 1 <= obj['width'] <= 1000:
                raise ValueError('Independent width grammar')
            if obj['width'] != prediction['width_relative'] or independent_box(item, obj['width']) != prediction['box']:
                raise ValueError('Independent original-center geometry mismatch')
            value, relative = raw_iou(prediction['box'], references[identity]['reference_xywh']), obj['width']
        else:
            value, relative = 0., 1000
        baseline = raw_iou(item['baseline_box'], references[identity]['reference_xywh'])
        losses.append(baseline)
        candidates.append(value)
        widths.append(relative)
        bins.append(item['human_bin'])
        detail.append(dict(item_id=identity, baseline_IoU=baseline, candidate_IoU=value, delta=value - baseline,
            invalid=prediction['status'] != 'VALID', predicted_relative=prediction['width_relative'],
            original_human_relative=references[identity]['human_width']))
    summary = risk_summary(losses, candidates, widths, bins)
    invalid = sum(r['invalid'] for r in detail)
    summary.update(invalid=invalid, changed=sum(p['box'] != by_id[p['item_id']]['baseline_box'] for p in predictions),
        severe_overshrink_descriptive=sum(r['predicted_relative'] is not None and
            r['predicted_relative'] < .75 * r['original_human_relative'] and r['delta'] < -.25 for r in detail) / len(detail))
    summary['gates']['invalid_zero'] = invalid == 0
    summary['passed'] = all(summary['gates'].values())
    write(ROOT / f'{role}_{arm}_audit.json', dict(status='PASS_FIRST80_TENSOR_TOKEN_GEOMETRY_QA',
        outputs=80, raw=ref(ROOT / f'{role}_{arm}_raw.jsonl'), invalid_outputs_preserved=invalid,
        original_processor_repeated=False, original_model_calls_repeated=False))
    return dict(arm=arm, role=role, summary=summary, rows=detail)


def main(role):
    runtime_paths()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    evaluation = read(ROOT / 'conditioned_eval.json')
    references = {r['item_id']: r for r in read(ROOT / 'external_reference.json')}
    arms = ARMS if role == 'dev' else [read(ROOT / 'selected.json')['arm']]
    reviews = [audit_arm(arm, role, tokenizer, evaluation, references) for arm in arms]
    write(ROOT / f'{role}_review.json', dict(status='S1_FIXED_RISK_REVIEW_COMPLETE', arms=reviews,
        static_file_level_not_video_quality=True, original_source_independence='UNKNOWN',
        old_width200_STOP_unchanged=True, official_joint_score='UNKNOWN', production_allowed=False))
    if role == 'dev':
        eligible = [r for r in reviews if r['summary']['passed']]
        if eligible:
            priority = {'W11': 0, 'W10': 1, 'W01': 2}
            selected = min(eligible, key=lambda r: (-r['summary']['mean_candidate'], priority[r['arm']]))
            arm = selected['arm']
            write(ROOT / 'selected.json', dict(status='FROZEN_AFTER_DEV_BEFORE_CONFIRM', arm=arm,
                review=ref(ROOT / 'dev_review.json'), adapter=read(ROOT / 'arms' / arm / 'completion.json')['adapter'],
                recipe=ref(ROOT / 'training_recipe.json'), confirm_not_scored=True))
        else:
            write(ROOT / 'development_stop.json', dict(status='STOP_ALL3_SPATIAL_ARMS_FIXED_DEV_RISKS',
                review=ref(ROOT / 'dev_review.json'), confirm_model_calls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', required=True, choices=['dev', 'confirm'])
    main(parser.parse_args().role)
