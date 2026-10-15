"""Preregistered equal <=30-second windows and native integer-floor64 sampling."""
from bisect import bisect_left
from fractions import Fraction as F


def plan_windows(clock):
    points = [F(value) for value in clock['normalized_exact_pts']]
    end = F(clock['physical_end_exact'])
    if (not points or points[0] != 0 or end <= points[-1] or
            any(a >= b for a, b in zip(points, points[1:]))):
        raise ValueError('Missing valid complete normalized native clock')
    count = (end.numerator + 30 * end.denominator - 1) // (30 * end.denominator)
    result = []
    for index in range(count):
        start, stop = end * index / count, end * (index + 1) / count
        first, limit = bisect_left(points, start), bisect_left(points, stop)
        eligible = limit - first
        if eligible < 64:
            raise ValueError('Fixed native64 window has too few physical frames; no repeat or padding fallback')
        ordinals = [first + sample * (eligible - 1) // 63 for sample in range(64)]
        if len(set(ordinals)) != 64:
            raise ValueError('Integer-floor64 plan repeated an original source frame')
        result.append(dict(index=index, start_exact=str(start), end_exact=str(stop),
                           eligible_first=first, eligible_stop=limit,
                           source_frame_ordinals=ordinals,
                           sample_exact_pts=[str(points[ordinal]) for ordinal in ordinals]))
    return result
