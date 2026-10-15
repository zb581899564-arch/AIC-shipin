"""Exact crop geometry diagnostics. No models, scale sweep or quality gate."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path


def number(value):
    if isinstance(value, bool):
        raise ValueError('boolean coordinate')
    return F(str(value))


def integer(value):
    v = number(value)
    if v.denominator != 1:
        raise ValueError('noninteger dimension')
    return int(v)


def maximum_box(width, height, ratio):
    width, height = integer(width), integer(height)
    a, b = map(integer, ratio)
    if min(width, height, a, b) <= 0:
        raise ValueError('nonpositive geometry')
    crop_width = min(width, height * a // b)
    if crop_width == 0:
        raise ValueError('no legal integer-width crop')
    return F(crop_width), F(crop_width * b, a)


def validate_box(box, width, height):
    if len(box) != 4:
        raise ValueError('box must be XYWH')
    x, y, w, h = map(number, box)
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
        raise ValueError('box outside source')
    return x, y, w, h


def iou(left, right):
    x, y, w, h = left
    u, v, s, t = right
    inter = max(F(0), min(x+w, u+s)-max(x, u)) * max(F(0), min(y+h, v+t)-max(y, v))
    return inter / (w*h + s*t - inter)


def placements(origin, reference_length, crop_length, source_length):
    # Overlap is piecewise linear; a maximum over integer origins is attained
    # next to an endpoint or one of these four breakpoints. No scale grid.
    limit = int(F(source_length)-crop_length)
    result = {0, limit}
    for point in (origin-crop_length, origin, origin+reference_length-crop_length,
                  origin+reference_length):
        floor = point.numerator // point.denominator
        for candidate in (floor, floor+1):
            result.add(max(0, min(limit, candidate)))
    return sorted(result)


def best_maximum_box(width, height, ratio, reference):
    reference = validate_box(reference, width, height)
    cw, ch = maximum_box(width, height, ratio)
    xs = placements(reference[0], reference[2], cw, width)
    ys = placements(reference[1], reference[3], ch, height)
    best = None
    for x in xs:
        for y in ys:
            box = (F(x), F(y), cw, ch)
            score = iou(box, reference)
            if best is None or score > best[0]:
                best = score, box
    return best


def metrics(width, height, ratio, reference, actual=None):
    ref = validate_box(reference, width, height)
    cw, ch = maximum_box(width, height, ratio)
    upper, best = best_maximum_box(width, height, ratio, ref)
    # The overlap in each axis is unimodal; its minimum on the legal origin
    # interval is at an endpoint. This is a bound, not a measured model box.
    lower = min(iou((F(x), F(y), cw, ch),ref)
                for x in (0, int(F(width)-cw))
                for y in (0, int(F(height)-ch)))
    actual_score = None
    if actual is not None:
        act = validate_box(actual, width, height)
        if act[2:] != (cw, ch) or any(v.denominator != 1 for v in act[:2]):
            raise ValueError('actual must use production maximum width and integer origins')
        actual_score = iou(act, ref)
        if actual_score > upper:
            raise ValueError('actual IoU exceeds derived ceiling')
    # A same-ratio r^2 ceiling is not substituted for a publisher's slightly
    # non-exact-aspect box. The original box remains unmodified.
    values = dict(maximum_integer_width=cw, maximum_height_exact=ch,
                  reference_width_fraction=ref[2]/cw,
                  reference_area_fraction=ref[2]*ref[3]/(cw*ch),
                  best_position_maxwidth_iou=upper,
                  worst_position_maxwidth_iou=lower,
                  center_position_identifiability_range=upper-lower,
                  geometric_deficit=1-upper,
                  actual_iou=actual_score,
                  center_gap=None if actual_score is None else upper-actual_score,
                  aspect_height_discrepancy_pixels=ref[3]-ref[2]*number(ratio[1])/number(ratio[0]))
    return {k: None if v is None else {'exact': str(v), 'value': float(v)}
            for k, v in values.items()}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_once(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


DEV_IDS = ['gnmc:validation:005995.jpeg', 'gnmc:validation:006034.jpeg',
           'gnmc:validation:007812.jpeg', 'gnmc:validation:003840.jpeg']
DEV_MANIFEST_SHA = 'fa6181818b27d35d4a0130c834f4c7f0fa4948b3ffa87e57240442b65ef746cc'


def run(manifest, output):
    manifest = Path(manifest)
    if sha(manifest) != DEV_MANIFEST_SHA:
        raise ValueError('original developer reference bytes changed')
    records = [json.loads(line) for line in manifest.read_text(encoding='utf-8-sig').splitlines() if line]
    if [r['item_id'] for r in records] != DEV_IDS:
        raise ValueError('only the fixed four already-open dev items are authorized here')
    results = []
    for record in records:
        if record['split'] != 'dev' or record['target_ratio_wh'] != [16, 9]:
            raise ValueError('unexpected split/ratio')
        media = manifest.parent / record['media_rel_path']
        if sha(media) != record['media_sha256']:
            raise ValueError('media identity mismatch')
        if len(record['reference_boxes']) != 1:
            raise ValueError('unexpected reference denominator')
        value = metrics(record['source_width'], record['source_height'],
                        record['target_ratio_wh'], record['reference_boxes'][0])
        results.append(dict(item_id=record['item_id'], media_sha256=record['media_sha256'],
                            source_group=record['source_group'],
                            independence=record['source_group_independence'],
                            usage_scope=record['usage_scope'], metrics=value,
                            actual_production_box='MISSING_SAME_MEDIA_BOUND_OUTPUT'))
    write_once(output, dict(status='DESCRIPTIVE_GNMC_DEV_GEOMETRY_ONLY',
                            manifest_sha256=sha(manifest), records=results,
                            denominator=4, ratios=['16:9'],
                            model_calls=0, optimizer_updates=0,
                            quality_gate_pass=False, training_admitted=False,
                            official_score_inference=False,
                            missing=['dual_ratio_video_composition_reference',
                                     'same_frame_frozen_production_outputs',
                                     'qualified_source_independence']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.manifest, args.output)
