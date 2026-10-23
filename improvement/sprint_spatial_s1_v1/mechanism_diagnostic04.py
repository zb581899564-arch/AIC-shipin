"""One post-result dev-only diagnostic, not a new admission or tuned candidate.

Permute saved relative widths by a single fixed source-identity hash cycle. The
width distribution is unchanged; no generation, fitting, threshold or grid scan.
This cannot alter the original PASS or authorize production.
"""
from collections import Counter
import hashlib
import json
import numpy as np
from common import ROOT, read, ref, write
from geometry import box_for_width, iou


def main():
    selected = read(ROOT / 'selected.json')['arm']
    items = {r['item_id']: r for r in read(ROOT / 'conditioned_eval.json') if r['role'] == 'dev'}
    references = {r['item_id']: r['reference_xywh'] for r in read(ROOT / 'external_reference.json') if r['role'] == 'dev'}
    predictions = {r['item_id']: r for r in map(json.loads, (ROOT / f'dev_{selected}_predictions.jsonl').read_text().splitlines())}
    identities = sorted(items, key=lambda name: hashlib.sha256(('S1_WIDTH_DEV_NULL04:' + name).encode()).digest())
    if len(identities) != 80 or set(predictions) != set(items) or any(p['status'] != 'VALID' for p in predictions.values()):
        raise ValueError('Completed valid dev outputs required; do not replace missing data')
    original, shifted, baseline = [], [], []
    changes = []
    for index, identity in enumerate(identities):
        item = items[identity]
        donor = predictions[identities[(index + 1) % len(identities)]]['width_relative']
        shifted_box = box_for_width(item['width'], item['height'], item['center'], donor)
        original.append(iou(predictions[identity]['box'], references[identity]))
        shifted.append(iou(shifted_box, references[identity]))
        baseline.append(iou(item['baseline_box'], references[identity]))
        changes.append(item['baseline_box'][2] - predictions[identity]['box'][2])
    delta = np.asarray(original) - np.asarray(shifted)
    result = dict(status='POST_RESULT_DEV_ONLY_MECHANISM_DIAGNOSTIC_NOT_NEW_GATE', arm=selected, rows=80,
        fixed_control='One SHA-ordered cyclic shift of saved relative widths; same80 width multiset',
        source_development_predictions=ref(ROOT / f'dev_{selected}_predictions.jsonl'),
        original_mean_IoU=float(np.mean(original)), shifted_mean_IoU=float(np.mean(shifted)),
        base_mean_IoU=float(np.mean(baseline)), original_minus_shifted_mean=float(delta.mean()),
        original_beats_shifted=sum(delta > 0).item(), original_ties_shifted=sum(delta == 0).item(),
        relative_width_histogram=dict(sorted(Counter(p['width_relative'] for p in predictions.values()).items())),
        width_reduction_pixels_histogram=dict(sorted(Counter(changes).items())),
        confirm_not_recomputed=True, original_risk_PASS_unchanged=True,
        research_GPU_calls=0, new_training_updates=0, new_official_candidates=0, production_allowed=False)
    write(ROOT / 'mechanism_diagnostic04.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
