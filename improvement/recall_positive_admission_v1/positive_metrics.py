"""Exact independent metrics and unchanged original 40.46-style proxy baseline."""
from bisect import bisect_left
from fractions import Fraction as F
from positive_contract import require


def merged(spans):
    out = []
    for first, last in sorted((F(a), F(b)) for a, b in spans):
        require(0 <= first < last, 'Invalid exact positive interval')
        if out and first <= out[-1][1]:
            out[-1][1] = max(last, out[-1][1])
        else:
            out.append([first, last])
    return out


def measure(spans):
    return sum((b-a for a, b in merged(spans)), F(0))


def metrics(pred, ref):
    pred, ref = merged(pred), merged(ref)
    p, r = measure(pred), measure(ref)
    overlap = sum((max(F(0), min(b, d)-max(a, c)) for a, b in pred for c, d in ref), F(0))
    return dict(f1=F(0) if not p+r else 2*overlap/(p+r),
        recall=F(0) if not r else overlap/r, precision=F(0) if not p else overlap/p)


def frames(spans, pts):
    result = set()
    for first, last in merged(spans):
        result.update(range(bisect_left(pts, first), bisect_left(pts, last)))
    return result


def baseline_prediction(events, inputs):
    """Original evaluate_pilot.source_prediction baseline arm, exactly.

    Keep original baseline non-DROP decisions, padding and source empty guard.
    No overlap additions and no new positive decision affect this protected arm.
    """
    baseline, old_d8, seen = [], [], set()
    for event in events:
        require(event['event_id'] not in seen, 'Duplicate immutable old VERIFY event')
        seen.add(event['event_id'])
        result = event['decision_result']; decision = result['decision']
        require(decision in ('KEEP', 'UNKNOWN', 'DROP') and result['successful_model_call_required'],
                'Actual complete old model decision required')
        meta = inputs[event['original_case_id']]
        roles = meta.get('view_roles', [meta['window_role']])
        a, b = map(F, result['original_interval_exact'])
        lo, hi = F(meta['window_start']), F(meta['window_end'])
        require(lo <= a < b <= hi, 'Original interval escaped immutable window')
        if 'baseline' in roles:
            padded = [max(lo, a-F(3, 4)), min(hi, b+F(1, 2)+(F(1, 4) if b-a >= 8 else F(0)))]
            old_d8.append(padded)
            if decision != 'DROP':
                baseline.append(padded)
    if old_d8 and not baseline:
        baseline = old_d8
    return merged(baseline)
