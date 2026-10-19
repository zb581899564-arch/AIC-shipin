"""Pure fixed 16:9 crop-pool geometry. No reference enters candidate creation.

Triplets are integer [x,y,w]; their height is always w*9/16. Placement
matches the project's frozen spatial_baseline center_to_box rounding/clamp.
"""
from __future__ import annotations

import hashlib
import math

SCALES_PERMILLE = (1000, 900, 800, 700)
GRID_CENTERS = (1/6, 1/2, 5/6)
SPLIT_SALT = 'GNMC_ROI_SOURCE_SPLIT_V1|'


def require(value, message):
    if not value:
        raise ValueError(message)


def dimensions(width, height):
    require(type(width) is int and type(height) is int and min(width, height) > 0,
            'Positive original integer dimensions required')


def largest_width(width, height):
    dimensions(width, height)
    return max(1, min(width, height*16//9))


def legal(box, width, height):
    dimensions(width, height)
    return (isinstance(box, (tuple, list)) and len(box) == 3
            and all(type(v) is int for v in box)
            and box[0] >= 0 and box[1] >= 0 and box[2] >= 1
            and box[0]+box[2] <= width and box[1]+box[2]*9/16 <= height+1e-9)


def place_crop(width, height, center, scale_permille=1000):
    dimensions(width, height)
    require(type(scale_permille) is int and 1 <= scale_permille <= 1000, 'Integer width permille required')
    require(len(center) == 2 and all(type(v) in (int, float) and math.isfinite(v)
            and 0 <= v <= 1 for v in center), 'Finite normalized center required')
    crop_width = max(1, largest_width(width, height)*scale_permille//1000)
    crop_height = crop_width*9/16
    max_x = max(0, width-crop_width)
    max_y = max(0, math.floor(height-crop_height+1e-9))
    x = min(max_x, int(round(max(0., min(center[0]*width-crop_width/2, float(max_x))))))
    y = min(max_y, int(round(max(0., min(center[1]*height-crop_height/2, float(max_y))))))
    box = [x, y, crop_width]
    require(legal(box, width, height), 'Generated illegal implicit-height crop')
    return box


def candidate_pool(width, height, baseline_box):
    """Original baseline first, then scale/x/y order, dedup final triplets."""
    require(legal(baseline_box, width, height), 'Explicit original baseline must be legal')
    boxes = [list(baseline_box)]
    seen = {tuple(baseline_box)}
    for scale in SCALES_PERMILLE:
        for cx in GRID_CENTERS:
            for cy in GRID_CENTERS:
                box = place_crop(width, height, (cx, cy), scale)
                if tuple(box) not in seen:
                    boxes.append(box); seen.add(tuple(box))
    return boxes


def reference_from_normalized(box, width, height):
    dimensions(width, height)
    require(len(box) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in box), 'Finite original normalized XYXY required')
    x1, y1, x2, y2 = box
    require(0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1, 'Original human normalized reference invalid; no repair')
    result = [x1*width, y1*height, (x2-x1)*width, (y2-y1)*height]
    validate_reference(result, width, height)
    return result


def validate_reference(reference, width, height):
    dimensions(width, height)
    require(len(reference) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in reference), 'Finite original floating XYWH required')
    x, y, w, h = reference
    require(x >= 0 and y >= 0 and w > 0 and h > 0 and x+w <= width+1e-7 and y+h <= height+1e-7,
            'Original human reference outside source; never clip it')
    error = abs(w*9/16-h)
    require(error <= 2+1e-9, 'Original native16:9 reference exceeds registered two-pixel tolerance')
    return error


def crop_iou(candidate, reference):
    require(len(candidate) == 3 and all(type(v) is int for v in candidate) and candidate[2] > 0,
            'Integer candidate triplet required')
    require(len(reference) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in reference)
            and reference[2] > 0 and reference[3] > 0, 'Original finite floating reference required')
    x, y, w = candidate; h = w*9/16
    u, v, rw, rh = reference
    intersection = max(0., min(x+w, u+rw)-max(x, u))*max(0., min(y+h, v+rh)-max(y, v))
    return intersection/(w*h+rw*rh-intersection)


def best_candidate(boxes, reference):
    require(bool(boxes), 'Nonempty fixed candidate pool required')
    scores = [crop_iou(box, reference) for box in boxes]
    index = max(range(len(boxes)), key=lambda i: (scores[i], -i))
    return index, scores[index], scores


def source_split(rows):
    """A fixed 482/120 file-source split, never a new blind reference claim."""
    require(len(rows) == 602, 'Exact original602 training source denominator required')
    require(len({row['id'] for row in rows}) == 602, '602 distinct source identities required')
    hashes = [row['source_sha256'] for row in rows]
    require(len(set(hashes)) == 602 and all(isinstance(v, str) and len(v) == 64
            and all(c in '0123456789abcdef' for c in v) for v in hashes), '602 distinct lowercase source SHA256 values required')
    ordered = sorted(rows, key=lambda row: (hashlib.sha256((SPLIT_SALT+row['source_sha256']).encode('ascii')).hexdigest(), row['source_sha256']))
    return {row['id']: ('train' if i < 482 else 'dev') for i, row in enumerate(ordered)}
