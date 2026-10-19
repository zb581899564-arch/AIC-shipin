"""Pure v31 native16 crop geometry and single-editor-derived pair labels.

Candidates never receive a reference. Integer placement chooses the nearest
legal center, with exact half-way cases going to the smaller coordinate.
"""
from __future__ import annotations

from fractions import Fraction
import math
from numbers import Integral, Real

TIE_MARGIN = 0.02
CLASS_ORDER = ('A', 'B', 'TIE')


def require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value):
    require(isinstance(value, Integral) and not isinstance(value, bool), 'Integer native coordinate required')
    return int(value)


def _number(value):
    require(isinstance(value, (Real, Fraction)) and not isinstance(value, bool)
            and math.isfinite(value), 'Finite real coordinate required')
    return Fraction(str(value))


def dimensions(width, height):
    width, height = _integer(width), _integer(height)
    require(min(width, height) > 0, 'Positive original dimensions required')
    return width, height


def largest_width(width, height):
    width, height = dimensions(width, height)
    return min(width, 16*height//9)


def legal(box, width, height):
    width, height = dimensions(width, height)
    if not isinstance(box, (list, tuple)) or len(box) != 3:
        return False
    if not all(isinstance(v, Integral) and not isinstance(v, bool) for v in box):
        return False
    x, y, w = map(int, box)
    return x >= 0 and y >= 0 and w > 0 and x+w <= width and 16*y+9*w <= 16*height


def _nearest_tie_floor(value):
    floor, remainder = divmod(value.numerator, value.denominator)
    return floor + int(2*remainder > value.denominator)


def place_crop(width, height, crop_width, center_xy_pixels):
    """Place a specified integer width at an original-pixel center; clamp legally."""
    width, height = dimensions(width, height)
    w = _integer(crop_width)
    require(1 <= w <= largest_width(width, height), 'Requested width must already be legal')
    require(len(center_xy_pixels) == 2, 'Original-pixel center XY required')
    cx, cy = map(_number, center_xy_pixels)
    max_x, max_y = width-w, (16*height-9*w)//16
    x = _nearest_tie_floor(min(Fraction(max_x), max(Fraction(0), cx-Fraction(w, 2))))
    y = _nearest_tie_floor(min(Fraction(max_y), max(Fraction(0), cy-Fraction(9*w, 32))))
    result = [x, y, w]
    require(legal(result, width, height), 'Illegal generated implicit-height crop')
    return result


def candidate_pool(width, height, baseline_box=None):
    """Six GT-free geometries; optionally prepend an observed BASE (at most7).

    Order: largest centered; floor(.8*largest) centered, left/right, up/down.
    Displacements use .1*largest and .1*(9*largest/16), not source W/H.
    A zero-width .8 proposal on a one-pixel source is omitted, never padded.
    """
    width, height = dimensions(width, height)
    maximum = largest_width(width, height)
    center = (Fraction(width, 2), Fraction(height, 2))
    proposals = []
    if baseline_box is not None:
        require(legal(baseline_box, width, height), 'Saved observed BASE must be legal; no repair')
        proposals.append(list(map(int, baseline_box)))
    proposals.append(place_crop(width, height, maximum, center))
    small = 4*maximum//5
    if small:
        dx, dy = Fraction(maximum, 10), Fraction(9*maximum, 160)
        for ox, oy in ((0, 0), (-dx, 0), (dx, 0), (0, -dy), (0, dy)):
            proposals.append(place_crop(width, height, small, (center[0]+ox, center[1]+oy)))
    result, seen = [], set()
    for box in proposals:
        if tuple(box) not in seen:
            result.append(box)
            seen.add(tuple(box))
    return result


def validate_reference(reference, width=None, height=None):
    require(len(reference) == 4, 'Original floating XYWH required')
    x, y, w, h = map(_number, reference)
    require(x >= 0 and y >= 0 and w > 0 and h > 0, 'Positive original reference; never repair')
    require((width is None) == (height is None), 'Both source dimensions or neither required')
    if width is not None:
        width, height = dimensions(width, height)
        require(x+w <= width and y+h <= height, 'Original reference lies outside source; never clip')
    return tuple(map(float, (x, y, w, h)))


def reference_from_normalized(reference_xyxy, width, height):
    width, height = dimensions(width, height)
    require(len(reference_xyxy) == 4, 'Original normalized XYXY required')
    x1, y1, x2, y2 = map(_number, reference_xyxy)
    require(0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1, 'Original normalized reference invalid')
    # Preserve the established original floating XYXY->XYWH arithmetic; exact
    # fractions are for candidate placement, never for rewriting human boxes.
    x1, y1, x2, y2 = map(float, reference_xyxy)
    return [x1*width, y1*height, (x2-x1)*width, (y2-y1)*height]


def crop_iou(candidate, reference_xywh):
    require(isinstance(candidate, (list, tuple)) and len(candidate) == 3,
            'Integer native crop triplet required')
    x, y, w = map(_integer, candidate)
    require(x >= 0 and y >= 0 and w > 0, 'Positive native candidate required')
    u, v, rw, rh = validate_reference(reference_xywh)
    h = 9*w/16
    intersection = max(0., min(x+w, u+rw)-max(x, u))*max(0., min(y+h, v+rh)-max(y, v))
    return intersection/(w*h+rw*rh-intersection)


def preference_label(iou_a, iou_b):
    """0=A,1=B,2=TIE; fixed inclusive .02 margin, not human preference votes."""
    a, b = _number(iou_a), _number(iou_b)
    require(0 <= a <= 1 and 0 <= b <= 1, 'IoU values must lie in[0,1]')
    return 2 if abs(a-b) <= Fraction(1, 50) else (0 if a > b else 1)


def swap_class(label):
    label = _integer(label)
    require(label in (0, 1, 2), 'Three-class label required')
    return (1, 0, 2)[label]


def pair_target(box_a, box_b, reference_xywh):
    """Return class int, not a one-hot vector or direct human preference vote."""
    a, b = crop_iou(box_a, reference_xywh), crop_iou(box_b, reference_xywh)
    return preference_label(a, b)
