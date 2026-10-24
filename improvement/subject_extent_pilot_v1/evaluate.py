"""First CPU parser/geometry review and unchanged preregistered human-IoU gates."""
import hashlib
import json
import statistics
import sys
from common import ROOT, paths, read, checked, signature, write, ref


def iou(box, gt, width, height):
    a = [box[0], box[1], box[0] + box[2], box[1] + box[2] * 9 / 16]
    b = [gt[0] * width, gt[1] * height, gt[2] * width, gt[3] * height]
    area = lambda v: max(0, v[2] - v[0]) * max(0, v[3] - v[1])
    inter = area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])
    return inter / (area(a) + area(b) - inter)


def main(role):
    paths()
    import numpy as np
    import torch
    from transformers import AutoProcessor, GenerationConfig
    from improvement.final_sprint_v1.grounding_grammar import GroundingGrammar
    from improvement.final_sprint_v1.spatial import SpatialConfig, SubjectTracker, parse_grounding, pixel_subjects, crop_from_subjects, validate_box
    protocol = read(ROOT / 'protocol.json')
    config = SpatialConfig(**protocol['spatial_config'])
    tracker = SubjectTracker(config)
    tokenizer = AutoProcessor.from_pretrained(read(ROOT / 'model_spec.json')['model_dir'], local_files_only=True).tokenizer
    grammar = GroundingGrammar(tokenizer)
    eos = GenerationConfig.from_pretrained(read(ROOT / 'model_spec.json')['model_dir'], local_files_only=True).eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    rows = read(ROOT / (role + '_rows.json'))
    outputs = [json.loads(s) for s in (ROOT / (role + '_accepted.jsonl')).read_text().splitlines()]
    if len(rows) != 20 or len(outputs) != 20 or {r['item_id'] for r in rows} != {r['item_id'] for r in outputs}:
        raise ValueError('Full20 paired denominator mismatch')
    by_id = {r['item_id']: r for r in outputs}
    groundings = [parse_grounding(by_id[r['item_id']]['raw']) for r in rows]
    comparisons = []
    for i, row in enumerate(rows):
        out = by_id[row['item_id']]
        encoded = torch.load(checked(out['tensor']), map_location='cpu', weights_only=True)
        if signature(encoded) != out['signature']:
            raise ValueError('Independent first CPU tensor identity mismatch')
        raw = tokenizer.decode(out['output_token_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        if raw != out['raw'] or parse_grounding(raw) != out['grounding']:
            raise ValueError('Independent token/raw/parser mismatch')
        if grammar.validate_output(out['output_token_ids'], eos) != out['grounding']:
            raise ValueError('Independent token-level grammar replay mismatch')
        rgb = np.load(checked(row['rgb']), allow_pickle=False)
        if hashlib.sha256(rgb.tobytes()).hexdigest() != row['RGB_sha256']:
            raise ValueError('Native image witness mismatch')
        width, height = row['width'], row['height']
        baseline = out['baseline']['baseline_box']
        validate_box(baseline, width, height, [16, 9])
        def box_for(grounding):
            subjects = pixel_subjects(grounding, width, height)
            refined, support = tracker.foreground_support(rgb, subjects)
            box, witness = crop_from_subjects(refined, width, height, [16, 9], baseline, config)
            validate_box(box, width, height, [16, 9])
            return box, witness, support
        actual, witness, support = box_for(groundings[i])
        shifted, _, _ = box_for(groundings[(i + 1) % 20])
        gt = row['original_normalized_xyxy']
        b, c, s = [iou(box, gt, width, height) for box in (baseline, actual, shifted)]
        comparisons.append(dict(item_id=row['item_id'], baseline=baseline, candidate=actual, shifted=shifted,
            baseline_iou=b, candidate_iou=c, shifted_iou=s, delta=c-b,
            witness=witness, foreground=support, unchanged=actual == baseline))
    delta = [r['delta'] for r in comparisons]
    result = dict(baseline_mean_iou=statistics.mean(r['baseline_iou'] for r in comparisons),
        candidate_mean_iou=statistics.mean(r['candidate_iou'] for r in comparisons),
        mean_delta=statistics.mean(delta), median_delta=statistics.median(delta),
        content_minus_shift=statistics.mean(r['candidate_iou']-r['shifted_iou'] for r in comparisons),
        losses_over_010=sum(d < -.10 for d in delta), changed=sum(not r['unchanged'] for r in comparisons), invalid=0)
    gates = protocol['quality_gates']
    passes = (result['mean_delta'] >= gates['mean_delta_min'] and result['median_delta'] >= 0
        and result['content_minus_shift'] >= gates['content_minus_shift_min']
        and result['losses_over_010'] <= gates['losses_over_010_max'] and result['changed'] >= gates['changed_min'])
    write(ROOT / (role + '_first_cpu_review.json'), dict(status='PASS20_FIRST_CPU_TOKEN_INPUT_PARSER_NATIVE_GEOMETRY',
        full_numeric_CPU_logits_not_claimed=True, no_model_calls=True, rows=comparisons))
    write(ROOT / (role + '_result.json'), dict(status='PASS_EXTERNAL_NATIVE16_ONLY' if passes else 'STOP_FIXED_SUBJECT_EXTENT',
        metrics=result, fixed_gates=gates, rows=20, dev_exposed=role == 'dev',
        original_source_independence='UNKNOWN', video_tracking_quality='NOT_TESTED', production_admitted=False,
        review=ref(ROOT / (role + '_first_cpu_review.json'))))
    print(json.dumps(dict(role=role, pass_fixed=passes, **result)), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
