"""Exact interval proxy for original human spans, without an invented author frame clock."""
from fractions import Fraction


def rational(value):
    return value if isinstance(value, Fraction) else Fraction(str(value))


def merged(spans):
    result = []
    for start, end in sorted((rational(a), rational(b)) for a, b in spans):
        if start < 0 or end <= start:
            raise ValueError('Invalid original interval')
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def measure(spans):
    return sum((end - start for start, end in merged(spans)), Fraction(0))


def paired_duration_metrics(prediction, reference):
    pred, ref = merged(prediction), merged(reference)
    p_size, r_size = measure(pred), measure(ref)
    overlap = Fraction(0)
    i = j = 0
    while i < len(pred) and j < len(ref):
        a, b = pred[i]
        c, d = ref[j]
        overlap += max(Fraction(0), min(b, d) - max(a, c))
        if b <= d:
            i += 1
        else:
            j += 1
    return {'f1': Fraction(0) if p_size + r_size == 0 else 2 * overlap / (p_size + r_size),
            'recall': Fraction(0) if r_size == 0 else overlap / r_size,
            'precision': Fraction(0) if p_size == 0 else overlap / p_size}


def candidate_spans(original_segments, window_start, window_end, arm):
    """Derive once from raw B endpoints. Preserve the entire D8 selection."""
    if arm not in {'D8_BASELINE', 'LONG8_LEAD025'}:
        raise ValueError('Undeclared arm')
    ws, we = rational(window_start), rational(window_end)
    if ws < 0 or we <= ws:
        raise ValueError('Invalid native window')
    spans = []
    for start, end in original_segments:
        start, end = rational(start), rational(end)
        if not (ws <= start < end <= we):
            raise ValueError('Raw B segment outside its original window')
        long = end - start >= 8
        lead = Fraction(3, 4) + (Fraction(1, 4) if long and arm == 'LONG8_LEAD025' else 0)
        tail = Fraction(1, 2) + (Fraction(1, 4) if long else 0)
        spans.append([max(ws, start - lead), min(we, end + tail)])
    return merged(spans)
