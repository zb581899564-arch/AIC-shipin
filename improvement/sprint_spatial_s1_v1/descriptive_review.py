"""Supplement frozen S1 decisions with full-image and aspect diagnostics only.

Run after dev review. No new quality gate, fitting, generation or confirmation
label access. All calculations use already saved dev predictions and references.
"""
import json
import math
import numpy as np
from common import ROOT, read, ref, write
from geometry import conditioned_target


def rectangle_iou(first, second):
    x, y, w, h = first
    a, b, c, d = second
    area = max(0., min(x + w, a + c) - max(x, a)) * max(0., min(y + h, b + d) - max(y, b))
    return area / (w * h + c * d - area)


def mean(values):
    return float(np.mean(values)) if values else None


def main():
    review = read(ROOT / 'dev_review.json')
    inputs = {r['item_id']: r for r in read(ROOT / 'conditioned_eval.json') if r['role'] == 'dev'}
    references = {r['item_id']: r for r in read(ROOT / 'external_reference.json') if r['role'] == 'dev'}
    if len(inputs) != 80 or set(inputs) != set(references):
        raise ValueError('Only registered80 dev rows may enter descriptive review')
    controls = {}
    for identity, item in inputs.items():
        reference = references[identity]['reference_xywh']
        relative, _, bound = conditioned_target(item['width'], item['height'], item['center'], reference)
        controls[identity] = dict(full_image=rectangle_iou([0, 0, item['width'], item['height']], reference),
            original_frame_aspect=item['width'] / item['height'],
            aspect_group='wider_or_equal_16_9' if item['width'] * 9 >= item['height'] * 16 else 'taller_than_16_9',
            fixed_center_oracle_IoU=bound, fixed_center_oracle_relative=relative)
    arms = []
    by_arm = {}
    for result in review['arms']:
        detail = result['rows']
        if {r['item_id'] for r in detail} != set(inputs) or len(detail) != 80:
            raise ValueError('Frozen development review identity mismatch')
        by_arm[result['arm']] = {r['item_id']: r for r in detail}
        grouped = {}
        for aspect in ['wider_or_equal_16_9', 'taller_than_16_9']:
            rows = [r for r in detail if controls[r['item_id']]['aspect_group'] == aspect]
            grouped[aspect] = dict(n=len(rows), baseline_IoU=mean([r['baseline_IoU'] for r in rows]),
                candidate_IoU=mean([r['candidate_IoU'] for r in rows]),
                delta=mean([r['delta'] for r in rows]),
                full_image_IoU=mean([controls[r['item_id']]['full_image'] for r in rows]))
        plan = read(ROOT / 'arms' / result['arm'] / 'draw_plan.json')
        initialization = read(ROOT / 'arms' / result['arm'] / 'initialization.json')
        arms.append(dict(arm=result['arm'], original_risk_summary=result['summary'], by_source_aspect=grouped,
            sampled_human_bins=plan['bins'], actual_adapter_parameters=initialization['adapter_parameters'],
            complete_pipeline_parameters=initialization['combined_pipeline_parameters']))
    paired = {}
    for other, interpretation in [('W10', 'conditioned_target_effect_at_file_equal_sampling'),
                                  ('W01', 'file_equal_sampling_effect_with_conditioned_target')]:
        deltas = [by_arm['W11'][i]['candidate_IoU'] - by_arm[other][i]['candidate_IoU'] for i in inputs]
        paired['W11_minus_' + other] = dict(interpretation=interpretation, mean=mean(deltas),
            median=float(np.median(deltas)), improved=sum(x > 0 for x in deltas), denominator=80)
    result = dict(status='DESCRIPTIVE_ONLY_NO_SELECTION_OR_GATE_CHANGE', dev_rows=80,
        dev_review=ref(ROOT / 'dev_review.json'), all_image_mean_IoU=mean([r['full_image'] for r in controls.values()]),
        fixed_center_width_oracle_mean_IoU=mean([r['fixed_center_oracle_IoU'] for r in controls.values()]),
        oracle_is_not_model_performance=True, historical_W00_not_matched_factorial=True,
        arms=arms, paired=paired, original_train_human_bins=[100, 172, 330],
        confirm_labels_read=False, no_new_model_calls=True, no_new_fitting=True,
        static_file_not_video_or_official_joint_score=True, original_source_independence='UNKNOWN')
    write(ROOT / 'dev_descriptive_review03.json', result)
    short = {k: v for k, v in result.items() if k not in ['dev_review']}
    print(json.dumps(short, ensure_ascii=False))


if __name__ == '__main__':
    main()
