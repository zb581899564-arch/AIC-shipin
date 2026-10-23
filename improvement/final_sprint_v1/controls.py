"""Declared zero-inference controls on complete, real parent predictions."""
from fractions import Fraction
import math

from .contracts import require
from .spatial import validate_box


def maximum_width_at_fixed_center(box, source):
    """Expand scale without translating the parent's actual composition center.

    Expanding to the globally largest ratio crop and clipping the origin moves
    the center near edges, which confounds a scale control. Here a width step
    of 2*ratio_w changes x/y by exact integer ratio_w/ratio_h, preserving both
    center coordinates and avoiding a rounded rational height at the boundary.
    The maximum unused width is less than one such step, disclosed in evidence.
    No baseline, image, model output, or parent file is changed.
    """
    width, height = source["width"], source["height"]
    ratio = source["targetRatioWH"]
    validate_box(box, width, height, ratio)
    x, y, old = map(lambda value: Fraction(str(value)), box)
    rw, rh = ratio
    cx, cy = x + old / 2, y + old * rh / (2 * rw)
    legal = min(2 * cx, 2 * (width - cx), 2 * cy * rw / rh,
                2 * (height - cy) * rw / rh)
    require(legal >= old, "Parent crop is not contained about its claimed center")
    step = 2 * rw
    count = math.floor((legal - old) / step)
    exact = [x - count * rw, y - count * rh, old + count * step]
    result = [int(value) if value.denominator == 1 else float(value) for value in exact]
    validate_box(result, width, height, ratio)
    return result, {"center_x_exact": str(cx), "center_y_exact": str(cy),
                    "maximum_contained_width_exact": str(legal),
                    "actual_width_exact": str(exact[2]), "width_step_pixels": step,
                    "center_translation": False, "new_model_calls": 0}
