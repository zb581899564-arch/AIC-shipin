"""Exact, half-open boundary context; stdlib only, no media/model operations."""
from fractions import Fraction as F
from bisect import bisect_left


def merged(values):
    result = []
    for lo, hi in sorted((F(str(a)), F(str(b))) for a, b in values):
        if lo >= hi:
            raise ValueError('Empty or reversed interval')
        if result and lo <= result[-1][1]:
            result[-1] = (result[-1][0], max(hi, result[-1][1]))
        else:
            result.append((lo, hi))
    return result


def duration(values):
    return sum((hi-lo for lo, hi in merged(values)), F(0))


def overlap(first, second):
    a, b = merged(first), merged(second)
    return sum((max(F(0), min(y, v)-max(x, u))
                for x, y in a for u, v in b), F(0))


def expanded_windows(windows, before, after):
    before, after = F(before), F(after)
    if before < 0 or after < 0:
        raise ValueError('Negative context')
    output = []
    for window in windows:
        start, stop = F(window['start_exact']), F(window['end_exact'])
        if start >= stop:
            raise ValueError('Invalid window domain')
        for raw_lo, raw_hi in window['segments']:
            lo, hi = F(str(raw_lo)), F(str(raw_hi))
            if not (F(0) <= lo < hi <= stop-start):
                raise ValueError('Invalid untouched original interval')
            output.append((max(start, start+lo-before),
                           min(stop, start+hi+after)))
    return merged(output)


def native_membership(points, intervals, field_domain=None):
    points = [F(p) for p in points]
    if not points or any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError('Native clock must be nonempty and strictly increasing')
    if field_domain is None:
        field_domain = (0, len(points))
    first_allowed, end_allowed = field_domain
    if (type(first_allowed) is not int or type(end_allowed) is not int or
            not (0 <= first_allowed < end_allowed <= len(points))):
        raise ValueError('Invalid frozen contiguous source field domain')
    chosen = set()
    for lo, hi in merged(intervals):
        a = max(first_allowed, bisect_left(points, lo))
        b = min(end_allowed, bisect_left(points, hi))
        chosen.update(range(a, b))
    independent = {i for i, p in enumerate(points)
                   if first_allowed <= i < end_allowed and
                   any(lo <= p < hi for lo, hi in intervals)}
    if chosen != independent:
        raise ValueError('Independent native timestamp predicate differs')
    return chosen
