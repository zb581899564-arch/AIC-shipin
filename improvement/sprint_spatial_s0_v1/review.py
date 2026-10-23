"""First independent saved-score selection, legal geometry and static IoU review."""
import json
import math
import numpy as np
import torch
from control import ROOT, read, checked, write, reference, signature, geometry


def intersection_over_union(box, original):
    x, y, width = box
    height = width * 9 / 16
    a, b, w, h = original
    intersection = max(0., min(x + width, a + w) - max(x, a)) * max(0., min(y + height, b + h) - max(y, b))
    return intersection / (width * height + w * h - intersection)


def original_placement(item, fraction):
    W, H = item['source_width'], item['source_height']
    width = max(1, min(W, H * 16 // 9) * fraction // 1000)
    x = round(max(0., min(item['center'][0] * W - width / 2, W - width)))
    y = round(max(0., min(item['center'][1] * H - width * 9 / 32, math.floor(H - width * 9 / 16 + 1e-9))))
    return [x, y, width]


def main():
    inputs = {r['item_id']: r for r in read(ROOT / 'inputs.json')}
    references = {r['item_id']: r['original_xywh'] for r in read(ROOT / 'references.json')}
    predictions = [json.loads(s) for s in (ROOT / 'predictions.jsonl').read_text().splitlines()]
    if len(predictions) != 80 or {r['item_id'] for r in predictions} != set(inputs) or set(inputs) != set(references):
        raise ValueError('Expected unique80 complete identities; missing is not empty output')
    raw = {r['item_id']: r for r in map(json.loads, (ROOT / 'raw_journal.jsonl').read_text().splitlines())}
    if len(raw) != 80 or set(raw) != set(inputs):
        raise ValueError('Every successful model output needs original raw')
    protocol = read(ROOT / 'protocol.json')
    base, candidate, widths, upper, details = [], [], [], [], []
    for result in predictions:
        identity = result['item_id']
        item = inputs[identity]
        tensor = torch.load(checked(item['input']), map_location='cpu', weights_only=True)
        if any(signature(v) != item['signatures'][k] for k, v in tensor.items()):
            raise ValueError('Independent real input signature mismatch')
        expected = []
        for fraction in protocol['relative_widths']:
            box = original_placement(item, fraction)
            if box not in expected:
                expected.append(box)
        if expected != item['candidates'] or raw[identity]['input'] != item['input']:
            raise ValueError('Independent source-center geometry/identity differs')
        sx = tensor['image'].shape[-1] / item['source_width']
        sy = tensor['image'].shape[-2] / item['source_height']
        expected_rois = torch.tensor([[0., math.floor(x * sx), math.floor(y * sy),
            math.ceil((x + width) * sx), math.ceil((y + width * 9 / 16) * sy)] for x, y, width in expected], dtype=torch.float32)
        if not torch.equal(tensor['rois'], expected_rois) or result['raw'] != raw[identity]['output']:
            raise ValueError('Independent exact author ROI coordinates or raw binding differ')
        values = np.load(checked(raw[identity]['output']), allow_pickle=False).reshape(-1)
        if len(values) != len(expected) or not np.isfinite(values).all() or values.tolist() != result['scores']:
            raise ValueError('Raw scores differ or execution failed')
        index = sorted(range(len(values)), key=lambda k: (float(values[k]), expected[k][2]), reverse=True)[0]
        if index != result['chosen_index'] or expected[index] != result['chosen_box']:
            raise ValueError('Independent widest-tie argmax differs')
        native_ref = references[identity]
        control = intersection_over_union(item['baseline_box'], native_ref)
        score = intersection_over_union(result['chosen_box'], native_ref)
        relative = round(result['chosen_box'][2] / item['baseline_box'][2] * 1000)
        base.append(control);candidate.append(score);widths.append(relative)
        upper.append(max(intersection_over_union(box, native_ref) for box in expected))
        details.append(dict(item_id=identity, original_IoU=control, candidate_IoU=score, delta=score - control,
            chosen_width=result['chosen_box'][2], original_width=item['baseline_box'][2], candidate_count=len(expected)))
    summary = geometry().risk_summary(base, candidate, widths)
    changed = sum(r['chosen_width'] != r['original_width'] for r in details)
    summary['gates'].update(invalid_zero=True, changes_at_least3=changed >= 3)
    summary.update(changed_images=changed, invalid=0, passed=all(summary['gates'].values()),
        finite_grid_oracle_mean_IoU=float(np.mean(upper)), oracle_is_not_model_performance=True)
    write(ROOT / 'independent_cpu_audit.json', dict(status='PASS80_SAVED_INPUT_RAW_SCORE_GEOMETRY_SELECTION',
        source_predictions=reference(ROOT / 'predictions.jsonl'), research_model_calls_repeated=0, source_images_reencoded=0))
    write(ROOT / 'review.json', dict(status='STATIC_DEV_EFFECT_SEPARATE_NEW_CONFIRM_REQUIRED' if summary['passed'] else 'STOP_FIXED_S0_DEV_RISK_OR_NO_EFFECT',
        summary=summary, rows=details, static_file_level_only=True, metrics_historically_exposed=True,
        source_or_pretraining_independence='UNKNOWN', official_joint_score='UNKNOWN',
        production_admitted=False, thresholds_or_candidate_grid_tuned=False))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
