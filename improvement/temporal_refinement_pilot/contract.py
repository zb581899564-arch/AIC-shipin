"""Explicit candidate-only rejection/refinement, with no parser recovery."""
from bisect import bisect_left
from fractions import Fraction


def floor64(first, stop):
    if type(first) is not int or type(stop) is not int or not 0 <= first < stop:
        raise ValueError('invalid native domain')
    n = stop-first
    return list(range(first, stop)) if n <= 64 else [first+i*(n-1)//63 for i in range(64)]


def intersection(proposals, candidates):
    """Registered selection rule: verifier may remove/trim, never add candidates."""
    result = []
    for a, b in proposals:
        for c, d in candidates:
            x, y = max(a, c), min(b, d)
            if x < y:
                result.append([x, y])
    result.sort()
    merged = []
    for a, b in result:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def context_domain(candidates, window_start, window_end):
    if not candidates:
        return None
    lo, hi = Fraction(window_start), Fraction(window_end)
    return max(lo, lo+Fraction(str(candidates[0][0]))-3), min(hi, lo+Fraction(str(candidates[-1][1]))+3)


def selected(segments, point):
    return any(Fraction(str(a)) <= point < Fraction(str(b)) for a, b in segments)


def sample_domain(exact_pts, lo, hi):
    points = [Fraction(x) for x in exact_pts]
    first, stop = bisect_left(points, lo), bisect_left(points, hi)
    return floor64(first, stop)
