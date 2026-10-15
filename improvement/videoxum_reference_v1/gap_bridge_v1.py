"""Separate short-gap continuity hypothesis; frozen D8 endpoints stay unchanged."""
from fractions import Fraction as F

from lead_guard_v2 import window_spans as original_window_spans


def bridge_spans(baseline):
    result = []
    for start, end in baseline:
        if result and 0 < start - result[-1][1] <= F(1):
            result[-1][1] = end
        else:
            result.append([start, end])
    return result


def window_spans(windows, arm):
    baseline = original_window_spans(windows, 'D8_BASELINE')
    if arm == 'D8_BASELINE':
        return baseline
    if arm != 'GAP100':
        raise ValueError('Unregistered gap-continuity arm')
    return bridge_spans(baseline)


def targeted_checks():
    baseline = [[F(0), F(2)], [F(3), F(4)], [F(21, 4), F(6)]]
    assert bridge_spans(baseline) == [[F(0), F(4)], [F(21, 4), F(6)]]
    assert baseline == [[F(0), F(2)], [F(3), F(4)], [F(21, 4), F(6)]]
    assert bridge_spans([]) == []
    assert bridge_spans([[F(1), F(2)]]) == [[F(1), F(2)]]
    assert bridge_spans([[F(0), F(1)], [F(7, 4), F(2)], [F(5, 2), F(3)]]) == [[F(0), F(3)]]
    print('PASS exact <=1-second bridge, larger-gap rejection, baseline immutability and empty/single checks')


if __name__ == '__main__':
    targeted_checks()
