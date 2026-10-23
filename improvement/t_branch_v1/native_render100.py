"""Render actual discrete model choices to original native supports, no repair."""
from fractions import Fraction
import hashlib

import numpy as np


def render(source, case, cells, selected):
    if selected.dtype != bool or selected.shape != (32,) or len(cells) != 32:
        raise ValueError('Complete32 actual binary native actions required')
    points = source.timeline.points; size = len(points)
    mask = np.zeros(size, dtype=bool); segments = []; runs = []
    for chosen, pair in zip(selected, cells):
        a, b = pair
        if not 0 <= a < b <= size:
            raise ValueError('Actual native action has no valid original frame support')
        if chosen:
            mask[a:b] = True
            if runs and runs[-1][1] == a:
                runs[-1][1] = b
            else:
                runs.append([a, b])
    origin = Fraction(case.meta['window_start'])
    for a, b in runs:
        first, last = points[a], points[b] if b < size else source.timeline.end
        segments.append([str(first - origin), str(last - origin)])
    reconstructed = source.timeline.intervals([(origin + Fraction(a), origin + Fraction(b)) for a, b in segments])
    if not np.array_equal(reconstructed, mask):
        raise ValueError('Discrete native cells and rendered exact native interval union differ')
    return dict(segments=segments, selected_cells=selected.tolist(),
        status='MODEL_OK' if mask.any() else 'LEGAL_EMPTY', native_frames=int(mask.sum()),
        native_mask_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),
        no_float_time_generation_or_support_repair=True)
