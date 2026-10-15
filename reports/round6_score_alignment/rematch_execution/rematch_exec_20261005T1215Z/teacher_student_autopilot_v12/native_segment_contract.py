"""Shared dev/production physical realization of a positive interval."""
from bisect import bisect_left
from fractions import Fraction
import math


def native_segment_ranges(segments, source_pts, window_start, duration):
    from contracts import validate_segments
    validate_segments(segments, duration)
    if not source_pts or any(not math.isfinite(p) for p in source_pts) or any(b <= a for a,b in zip(source_pts,source_pts[1:])):
        raise ValueError("strict actual native source PTS required for frame realizability")
    ranges = []
    for a,b in segments:
        first = bisect_left(source_pts, float(Fraction(str(window_start)) + Fraction(str(a))))
        stop = bisect_left(source_pts, float(Fraction(str(window_start)) + Fraction(str(b))))
        if not 0 <= first < stop <= len(source_pts):
            raise ValueError("nonempty segment contains no actual source frame")
        ranges.append((first,stop))
    return ranges
