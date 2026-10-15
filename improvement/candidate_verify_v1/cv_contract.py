"""Conservative existing-candidate verification; no model/media dependencies."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import re

SCHEMA = 'CANDIDATE_VERIFY_V1'
MODEL_PARAMETERS = 8782459120
EMPTY_PROMPT_SHA256 = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'
MAX_INPUT_TOKENS = 16384
MAX_OUTPUT_TOKENS = 256
DECISIONS = ('KEEP', 'UNKNOWN', 'DROP')


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def exact(value):
    if isinstance(value, bool):
        raise ValueError('Explicit finite exact seconds required')
    return value if isinstance(value, F) else F(str(value))


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value):
        raise ValueError('Stable safe original-candidate identity required')
    return value


def request(event, meta):
    safe_id(event['event_id'])
    safe_id(meta['case_id'])
    first, last = map(exact, event['original_interval_exact'])
    lo, hi = exact(meta['window_start']), exact(meta['window_end'])
    if not 0 <= lo <= first < last <= hi or hi-lo > 30:
        raise ValueError('VERIFY must use the complete accepted original <=30s B0 window')
    if (len(meta['source_frame_ordinals']) != 64 or len(set(meta['source_frame_ordinals'])) != 64 or
            len(meta['sample_exact_pts']) != 64 or meta['audio_observed'] is not False or
            meta['reference_available_to_inference'] is not False):
        raise ValueError('Unchanged original native64 visual-only evidence required')
    samples = list(map(exact, meta['sample_exact_pts']))
    if any(a >= b for a, b in zip(samples, samples[1:])) or not all(lo <= p < hi for p in samples):
        raise ValueError('Original visible samples are not on the accepted exact native window')
    observed = sum(first <= point < last for point in samples)
    return dict(schema=SCHEMA, request_id=event['event_id']+'.verify', event_id=event['event_id'],
        original_case_id=meta['case_id'], original_segment_index=event['original_segment_index'],
        source_name=meta['source_name'], source_sha256=meta['source_sha256'],
        original_interval_exact=[str(first), str(last)],
        original_window_start_exact=str(lo), original_window_end_exact=str(hi),
        candidate_window_local_exact=[str(first-lo), str(last-lo)],
        candidate_visible_sample_count=observed,
        allowed_decisions=list(DECISIONS) if observed else ['UNKNOWN'],
        uncertainty_gate='NONE' if observed else 'NO_SHOWN_SAMPLE_IN_CANDIDATE',
        source_frame_ordinals=meta['source_frame_ordinals'], sample_exact_pts=meta['sample_exact_pts'],
        reference_labels_read=False, audio_observed=False,
        action_completion_required=False, silent_lecture_or_static_landscape_is_ordinary=False,
        new_candidate_created=False)


def prompt(req):
    first, last = req['candidate_window_local_exact']
    return (
        'Review ONLY the existing visual candidate '+req['event_id']+' / original B case '+
        req['original_case_id']+' / segment '+str(req['original_segment_index'])+'. '
        'The complete original silent video window is shown with its original sampled frames. '
        'The supplied candidate occupies ['+str(float(exact(first)))+','+
        str(float(exact(last)))+') seconds from THIS window start. '
        'KEEP when there is identifiable distinctive content, an interesting scene, a '
        'meaningful visual result, or another visually supported reason to retain it. '
        'DROP ONLY if clear positive visual evidence shows this whole candidate is ordinary '
        'uneventful or redundant and it contains NO identifiable content worth retaining. '
        'A sparse sampling gap or absence of evidence is not positive evidence of ordinary '
        'content. Do not assume a highlight must contain a complete action or a completed '
        'result. Static scenery, a lecture, speaking without audio, unfinished activity, '
        'unclear candidate identity, or insufficient visible evidence cannot automatically '
        'be called ordinary; use UNKNOWN when you cannot judge them. UNKNOWN retains the '
        'original candidate. Do not select another event or change its boundaries. '
        'No labels, audio, or external event descriptions are supplied. '
        'Return ONLY one canonical JSON object from '+', '.join(responses(req))+'. No explanation.')


def responses(req=None):
    values = DECISIONS if req is None else tuple(req['allowed_decisions'])
    if not values or any(value not in DECISIONS for value in values):
        raise ValueError('Finite conservative verification decisions required')
    return tuple('{"decision":"'+value+'"}' for value in values)


def resolve(text, req, *, execution_status):
    if execution_status != 'MODEL_OK':
        raise ValueError('Input/parser/model failure blocks verification; never UNKNOWN fallback')
    if text not in responses(req):
        raise ValueError('Incomplete/noncanonical raw verification decision; no output repair')
    decision = json.loads(text)['decision']
    return dict(event_id=req['event_id'], request_id=req['request_id'],
        original_case_id=req['original_case_id'], original_segment_index=req['original_segment_index'],
        source_sha256=req['source_sha256'], original_interval_exact=req['original_interval_exact'],
        decision=decision, candidate_kept=decision != 'DROP',
        retained_interval_exact=req['original_interval_exact'] if decision != 'DROP' else None,
        boundaries_changed=False, new_candidate_created=False,
        uncertainty_gate=req['uncertainty_gate'], successful_model_call_required=True)


def render_retained_union(events, decisions, native_pts, physical_end):
    """Remove only each DROP candidate contribution; retain all overlapping KEEP."""
    points = list(map(exact, native_pts))
    end = exact(physical_end)
    if (not points or points[0] != 0 or end <= points[-1] or
            any(a >= b for a, b in zip(points, points[1:]))):
        raise ValueError('Accepted complete normalized native clock required')
    if len({e['event_id'] for e in events}) != len(events) or set(decisions) != {e['event_id'] for e in events}:
        raise ValueError('Renderer requires the complete unique registered decision denominator')
    original, retained, dropped = set(), set(), set()
    kept_ids, drop_ids = [], []
    for event in events:
        decision = decisions[event['event_id']]
        if decision not in DECISIONS:
            raise ValueError('A failed/unassessed candidate cannot be rendered as UNKNOWN')
        first, last = map(exact, event.get('render_interval_exact', event['original_interval_exact']))
        if not 0 <= first < last <= end:
            raise ValueError('Registered render interval escaped the actual native source')
        lo, hi = bisect_left(points, first), bisect_left(points, last)
        if not lo < hi:
            raise ValueError('Registered positive render interval contains no native frame')
        frames = set(range(lo, hi))
        original.update(frames)
        if decision == 'DROP':
            dropped.update(frames)
            drop_ids.append(event['event_id'])
        else:
            retained.update(frames)
            kept_ids.append(event['event_id'])
    ranges = []
    for ordinal in sorted(retained):
        if ranges and ranges[-1][1] == ordinal:
            ranges[-1][1] += 1
        else:
            ranges.append([ordinal, ordinal+1])
    return dict(retained_candidate_ids=kept_ids, dropped_candidate_ids=drop_ids,
        native_ranges=ranges, original_union_frames=len(original), retained_union_frames=len(retained),
        actually_removed_frames=len(original-retained),
        dropped_overlap_protected_by_other_retained_candidates=len(dropped & retained),
        frame_deletion_is_difference_of_unions=True)
