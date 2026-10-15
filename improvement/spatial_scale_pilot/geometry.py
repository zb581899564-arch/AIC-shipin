"""Finite crop candidates in source coordinates; no labels or model imports."""
import json
from fractions import Fraction

SCALES = (100, 85, 70, 55)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def max_width(width, height, ratio):
    require(type(width) is int and type(height) is int and min(width, height) > 0,
            'invalid source dimensions')
    tw, th = ratio
    require(type(tw) is int and type(th) is int and min(tw, th) > 0, 'invalid ratio')
    result = min(width, height * tw // th)
    require(result >= 1, 'no positive legal integer crop')
    return result


def legal(box, width, height, ratio):
    if len(box) != 3 or any(type(v) is not int for v in box):
        return False
    x, y, w = box
    tw, th = ratio
    return w > 0 and min(x, y) >= 0 and x + w <= width and (y * tw + w * th) <= height * tw


def place(center, crop_width, width, height, ratio):
    require(len(center) == 2 and all(type(v) is int and 0 <= v <= 1000 for v in center),
            'center must be integer 0..1000')
    require(type(crop_width) is int and 1 <= crop_width <= max_width(width, height, ratio),
            'illegal width')
    tw, th = ratio
    crop_height = Fraction(crop_width * th, tw)
    px = Fraction(center[0] * width, 1000) - Fraction(crop_width, 2)
    py = Fraction(center[1] * height, 1000) - crop_height / 2
    x = round(max(Fraction(0), min(px, Fraction(width - crop_width))))
    max_y = (height * tw - crop_width * th) // tw
    y = round(max(Fraction(0), min(py, Fraction(max_y))))
    result = [x, y, crop_width]
    require(legal(result, width, height, ratio), 'placement produced illegal geometry')
    return result


def strict_object(raw, keys):
    # No fence stripping, regex recovery, numeric coercion, or boolean-as-int.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    obj = json.loads(raw, object_pairs_hook=unique)
    require(type(obj) is dict and set(obj) == set(keys), 'unexpected JSON fields')
    return obj


def parse_proposal(raw):
    obj = strict_object(raw, ('center', 'scale'))
    center, scale = obj['center'], obj['scale']
    require(type(center) is list and len(center) == 2 and
            all(type(v) is int and 0 <= v <= 1000 for v in center), 'invalid proposal center')
    require(type(scale) is int and scale in SCALES, 'scale outside registered finite set')
    return center, scale


def parse_choice(raw, count):
    choice = strict_object(raw, ('choice',))['choice']
    require(type(choice) is int and 0 <= choice < count, 'choice outside actual candidate IDs')
    return choice


def candidates(baseline_box, baseline_center, proposed_center, proposed_scale, width, height, ratio):
    require(legal(baseline_box, width, height, ratio), 'illegal original baseline')
    cw = max_width(width, height, ratio)
    require(baseline_box[2] == cw, 'baseline no longer has original max-width geometry')
    result = [dict(id=0, origins=['ORIGINAL_BASELINE'], box=baseline_box)]
    variants = [(f'BASELINE_CENTER_SCALE_{s}', baseline_center, s) for s in SCALES[1:]]
    variants += [('MODEL_JOINT_PROPOSAL', proposed_center, proposed_scale),
                 ('MODEL_CENTER_ORIGINAL_WIDTH', proposed_center, 100)]
    for origin, center, scale in variants:
        box = place(center, max(1, cw * scale // 100), width, height, ratio)
        duplicate = next((v for v in result if v['box'] == box), None)
        if duplicate is not None:
            duplicate['origins'].append(origin)
        else:
            result.append(dict(id=len(result), origins=[origin], box=box))
    return result


def iou_xyw(prediction, reference_xywh, ratio):
    x, y, w = prediction
    h = w * ratio[1] / ratio[0]
    rx, ry, rw, rh = reference_xywh
    intersection = max(0.0, min(x + w, rx + rw) - max(x, rx)) * \
                   max(0.0, min(y + h, ry + rh) - max(y, ry))
    return intersection / (w * h + rw * rh - intersection)
