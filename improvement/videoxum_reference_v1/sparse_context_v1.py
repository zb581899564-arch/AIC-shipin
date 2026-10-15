"""Density-conditioned context, separate from failed unconditional lead/gap rules."""
from fractions import Fraction as F

from reference_intervals import rational, merged, measure

ARMS = ('SPARSE50_PRE025', 'SPARSE50_POST025')


def window_spans(windows, arm):
    if arm not in ('D8_BASELINE', *ARMS):
        raise ValueError('Undeclared sparse-context recipe')
    result = []
    for window in windows:
        origin, stop = rational(window['start_exact']), rational(window['end_exact'])
        if not 0 <= origin < stop:
            raise ValueError('Invalid original window')
        raw = [[rational(a), rational(b)] for a, b in window['segments']]
        if any(not 0 <= a < b <= stop-origin for a, b in raw):
            raise ValueError('Original segment violates its exact window')
        sparse = 2 * measure(raw) <= stop-origin
        for start, end in raw:
            long = end-start >= 8
            before = F(3, 4)
            after = F(3, 4) if long else F(1, 2)
            if sparse and long:
                if arm == 'SPARSE50_PRE025':
                    before += F(1, 4)
                elif arm == 'SPARSE50_POST025':
                    after += F(1, 4)
            result.append([max(origin, origin+start-before), min(stop, origin+end+after)])
    return merged(result)


def targeted_checks():
    sparse = [dict(start_exact='0', end_exact='30', segments=[[10, 20]])]
    assert window_spans(sparse, 'D8_BASELINE') == [[F(37, 4), F(83, 4)]]
    assert window_spans(sparse, 'SPARSE50_PRE025') == [[F(9), F(83, 4)]]
    assert window_spans(sparse, 'SPARSE50_POST025') == [[F(37, 4), F(21)]]
    dense = [dict(start_exact='0', end_exact='30', segments=[[1, 20]])]
    for arm in ARMS:
        assert window_spans(dense, arm) == window_spans(dense, 'D8_BASELINE')
    overlapping = [dict(start_exact='0', end_exact='30', segments=[[10, 20], [12, 20]])]
    assert window_spans(overlapping, ARMS[0]) == [[F(9), F(83, 4)]]
    short = [dict(start_exact='0', end_exact='30', segments=[[10, 14]])]
    for arm in ARMS:
        assert window_spans(short, arm) == window_spans(short, 'D8_BASELINE')
    print('PASS exact sparse/dense gating, union coverage, original D8 and short-span preservation')


if __name__ == '__main__':
    targeted_checks()
