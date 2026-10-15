"""Uniform native-PTS context restricted to a proven contiguous source-field domain."""
from bisect import bisect_left
from collections import defaultdict
from fractions import Fraction as F


def source_domains(field, expected_ids):
    by_source = defaultdict(list)
    for row in field:
        source, frame = row['video_id'], row['source_frame']
        if not isinstance(source, str) or type(frame) is not int:
            raise ValueError('source-field key type differs')
        by_source[source].append(frame)
    if set(by_source) != set(expected_ids):
        raise ValueError('source-field source identity differs')
    domains = {}
    for source, values in by_source.items():
        ids = sorted(values)
        if not ids or ids != list(range(ids[0], ids[-1] + 1)):
            raise ValueError('source-field domain contains a hole or duplicate')
        domains[source] = (ids[0], ids[-1] + 1)
    return domains


def window_context(window, segments, domain):
    points = [F(x) for x in window['all_source_exact_pts']]
    if any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError('native PTS must be strictly increasing')
    lo, hi = domain
    if not (0 <= lo < hi <= len(points)):
        raise ValueError('source-field domain outside native clock')
    start, end = F(window['exact_raw_start']), F(window['exact_raw_end'])
    core, context = set(), set()
    for a, b in segments:
        a, b = start + F(str(a)), start + F(str(b))
        first, stop = bisect_left(points, a), bisect_left(points, b)
        if not (lo <= first < stop <= hi):
            raise ValueError('accepted core is outside proven source-field domain')
        core.update(range(first, stop))
        lower, upper = max(start, a - F(1, 4)), min(end, b + F(1, 4))
        raw_first, raw_stop = bisect_left(points, lower), bisect_left(points, upper)
        if not (window['eligible_first'] <= raw_first < raw_stop <= window['eligible_stop']):
            raise ValueError('native context escaped registered original window')
        first, stop = max(lo, raw_first), min(hi, raw_stop)
        actual = list(range(first, stop))
        predicate = [i for i, p in enumerate(points) if lo <= i < hi and lower <= p < upper]
        if actual != predicate:
            raise ValueError('independent native PTS and source-domain predicate differs')
        context.update(actual)
    if not core <= context:
        raise ValueError('source-domain context removed accepted core')
    return core, context
