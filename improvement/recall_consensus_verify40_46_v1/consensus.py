"""Exact two-distinct-view KEEP agreement; never modifies protected baseline."""
from fractions import Fraction as F


def merged(spans):
    out = []
    for a, b in sorted((F(a), F(b)) for a, b in spans):
        if not 0 <= a < b:
            raise ValueError('Positive original exact interval required')
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def agreed_keep(view_spans):
    """One vote per actual window geometry, regardless of candidate count.

    view_spans maps (original_start, original_end) to its accepted KEEP spans.
    Duplicate/overlapping proposals in one view are unioned before counting.
    A point is admitted iff at least two distinct original views support it.
    No reference, model scores, padding, fitted threshold, or labels enter.
    """
    changes = {}
    seen = set()
    for view, spans in view_spans.items():
        if len(view) != 2:
            raise ValueError('Original window geometry required')
        lo, hi = map(F, view)
        if not 0 <= lo < hi or (lo, hi) in seen:
            raise ValueError('Duplicate or invalid original window identity')
        seen.add((lo, hi))
        for a, b in merged(spans):
            if not lo <= a < b <= hi:
                raise ValueError('A KEEP candidate escaped its actual view')
            changes[a] = changes.get(a, 0) + 1
            changes[b] = changes.get(b, 0) - 1
    out, active, previous = [], 0, None
    for instant, delta in sorted(changes.items()):
        if previous is not None and previous < instant and active >= 2:
            out.append([previous, instant])
        active += delta
        if active < 0:
            raise ValueError('Invalid sweep count')
        previous = instant
    if active:
        raise ValueError('Unclosed KEEP evidence')
    return merged(out)
