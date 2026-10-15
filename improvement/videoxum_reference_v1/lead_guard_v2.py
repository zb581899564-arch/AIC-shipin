"""Independent follow-up after LONG8_LEAD025's factual rejection; no old result edit."""
from fractions import Fraction

from reference_intervals import merged, rational

ARMS = {'L16': Fraction(16), 'L32': Fraction(32)}


def window_spans(windows, arm):
    if arm not in {'D8_BASELINE', *ARMS}:
        raise ValueError('Undeclared follow-up arm')
    result = []
    for window in windows:
        origin, stop = rational(window['start_exact']), rational(window['end_exact'])
        for raw_start, raw_end in window['segments']:
            start, end = rational(raw_start), rational(raw_end)
            if not (0 <= start < end <= stop - origin):
                raise ValueError('Original interval violates its window')
            duration = end - start
            before = Fraction(3, 4)
            after = Fraction(1, 2) + (Fraction(1, 4) if duration >= 8 else 0)
            if arm in ARMS and duration >= ARMS[arm]:
                before += Fraction(1, 4)
            result.append([max(origin, origin + start - before), min(stop, origin + end + after)])
    return merged(result)
