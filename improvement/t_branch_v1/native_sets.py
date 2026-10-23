"""Exact native-frame sets; candidate provenance survives overlapping windows."""
from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction

import numpy as np


def exact(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a timestamp')
    return Fraction(str(value))


def bool_mask(value, size):
    result = np.asarray(value)
    if result.dtype != np.bool_ or result.shape != (size,):
        raise ValueError('A complete native boolean mask is required; no casting or padding')
    return result


@dataclass(frozen=True)
class NativeTimeline:
    points: tuple
    end: Fraction

    def __post_init__(self):
        if not self.points or self.points[0] < 0 or self.end <= self.points[-1]:
            raise ValueError('Missing or invalid native time extent')
        if any(a >= b for a, b in zip(self.points, self.points[1:])):
            raise ValueError('Native presentation order must be strictly increasing')

    @classmethod
    def from_clock(cls, clock):
        origin = exact(clock['first_PTS_exact'])
        points = tuple(exact(p) - origin for p in clock['PTS'])
        if len(points) != clock['native_frames']:
            raise ValueError('Native clock denominator differs; never truncate labels')
        return cls(points, exact(clock['physical_end_exact']) - origin)

    def intervals(self, spans):
        result = np.zeros(len(self.points), dtype=bool)
        for start, end in spans:
            lo, hi = exact(start), exact(end)
            if not 0 <= lo < hi <= self.end:
                raise ValueError('Interval outside original media; no silent clipping')
            result[bisect_left(self.points, lo):bisect_left(self.points, hi)] = True
        return result


def accepted_selection(state, value, size):
    if state not in ['MODEL_OK', 'LEGAL_EMPTY']:
        raise ValueError('Execution failure/unreviewed output is not a selection')
    result = bool_mask(value, size)
    if bool(result.any()) != (state == 'MODEL_OK'):
        raise ValueError('Selection state and actual emptiness disagree')
    return result


def union_components(components, size):
    result = np.zeros(size, dtype=bool)
    for mask in components.values():
        result |= bool_mask(mask, size)
    return result


def replace_component(components, name, candidate, allowed):
    size = len(allowed)
    allowed = bool_mask(allowed, size)
    candidate = bool_mask(candidate, size)
    if name not in components:
        raise ValueError('Replacement component has no original provenance')
    if np.any(candidate & ~allowed):
        raise ValueError('Candidate leaves its registered native window')
    replacement = dict(components)
    replacement[name] = candidate
    # Removing a window must not erase frames contributed by another overlapping window.
    return union_components(replacement, size)
