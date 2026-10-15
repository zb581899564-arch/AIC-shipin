"""Pure local-boundary contracts. No media, processor or model imports.

The proposed boundary is always identified by its original B case/segment.
Decisions cannot add/remove events. UNKNOWN and KEEP preserve exact old seconds.
"""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import re

SCHEMA = 'LOCAL_BOUNDARY_NATIVE64_V2_REVISION03'
CONTRACT_REVISION = 'SOURCE_EDGE_INWARD_REVISION_03'
MODEL_PARAMETERS = 8782459120
ORIGINAL_EMPTY_PROMPT_SHA256 = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'
MAX_INPUT_TOKENS = 16384
MAX_OUTPUT_TOKENS = 256
NATIVE_FRAMES = 64
HALF_WINDOW = F(3)


def canonical_sha(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def fraction(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, F)):
        raise ValueError('Finite explicit exact seconds required')
    return value if isinstance(value, F) else F(str(value))


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value):
        raise ValueError('An explicit stable safe case/event ID is required')
    return value


def normalized_clock(clock):
    """Use the accepted raw clock and its measured origin, never duration/fps."""
    raw = [fraction(p) for p in clock['original_exact_pts']]
    origin = fraction(clock['first_original_pts_exact'])
    points = [fraction(p) for p in clock.get('normalized_exact_pts',
                                           clock['original_exact_pts'])]
    if (not raw or len(raw) != len(points) or raw[0] != origin or points[0] != 0 or
            any(a >= b for a, b in zip(raw, raw[1:])) or
            any(a-origin != b for a, b in zip(raw, points))):
        raise ValueError('Accepted complete original/normalized PTS binding failed')
    n = clock.get('n_frames', clock.get('native_frames'))
    if type(n) is not int or n != len(points):
        raise ValueError('Complete native-frame denominator changed')
    end = fraction(clock['physical_end_exact'])
    # The SumMe contract explicitly stores a normalized physical endpoint.
    # A zero-origin original clock needs no normalization. Unknown origins stop.
    if 'normalized_exact_pts' not in clock and origin != 0:
        raise ValueError('Original-only clock has no independently accepted normalization')
    if end <= points[-1]:
        raise ValueError('Positive measured last-frame duration required')
    evidence = clock.get('physical_endpoint_evidence')
    if evidence is not None:
        if (evidence['kind'] != 'LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION' or
                fraction(evidence['last_normalized_pts_exact']) != points[-1] or
                fraction(evidence['last_frame_duration_exact']) <= 0 or
                points[-1]+fraction(evidence['last_frame_duration_exact']) != end):
            raise ValueError('Accepted actual last-frame endpoint evidence changed')
    elif (fraction(clock['last_frame_duration_exact']) <= 0 or
          raw[-1]+fraction(clock['last_frame_duration_exact']) != end):
        raise ValueError('Original native endpoint is not measured PTS plus duration')
    return points, raw, origin, end


def plan_endpoint(event, side, clock):
    """Fixed +/-3s clip, floor64, original candidate identity and inner anchor."""
    valid_id(event['event_id'])
    valid_id(event['original_case_id'])
    if side not in ('start', 'end'):
        raise ValueError('Only the same original start/end may be reviewed')
    points, _, origin, physical_end = normalized_clock(clock)
    start, end = map(fraction, event['original_interval_exact'])
    if not 0 <= start < end <= physical_end:
        raise ValueError('Original B interval must lie on the accepted physical clock')
    pivot = start if side == 'start' else end
    lo, hi = max(F(0), pivot-HALF_WINDOW), min(physical_end, pivot+HALF_WINDOW)
    first, limit = bisect_left(points, lo), bisect_left(points, hi)
    if limit-first < NATIVE_FRAMES:
        raise ValueError('Short context has fewer than 64 actual frames; no wider/padded fallback')
    ordinals = [first+i*(limit-first-1)//(NATIVE_FRAMES-1)
                for i in range(NATIVE_FRAMES)]
    if len(set(ordinals)) != NATIVE_FRAMES:
        raise ValueError('Local native64 samples repeated original frames')
    samples = [points[i] for i in ordinals]
    # A start names the first included frame. An end names the last included
    # frame and applies its *next* native PTS (or measured physical last end).
    boundaries = samples if side == 'start' else [
        points[i+1] if i+1 < len(points) else physical_end for i in ordinals]
    # An inner anchor is part of the same supplied candidate, not a new label.
    # Keep it visibly inside the short clip and at most one second from the pivot.
    distance = min(F(1), (end-start)/2)
    anchor = pivot+distance if side == 'start' else pivot-distance
    if not lo <= anchor < hi:
        raise ValueError('Same-candidate inner anchor is absent from the short clip')
    allowed = [i for i, p in enumerate(boundaries)
               if (p < anchor if side == 'start' else p > anchor)]
    if not allowed:
        raise ValueError('No native sample can preserve the original inner anchor')
    source_boundary = ('SOURCE_START' if side == 'start' and pivot == 0 else
                       'SOURCE_PHYSICAL_END' if side == 'end' and pivot == physical_end else 'INTERIOR')
    visible = {}
    for i, cut in enumerate(boundaries):
        if i in (0, NATIVE_FRAMES-1):
            visible[str(i)] = False
        elif side == 'start':
            # One shown sample before the first included frame; the next shown
            # sample is after it. These are geometric visibility only.
            visible[str(i)] = lo <= samples[i-1] < cut < samples[i+1] < hi
        else:
            # End is exclusive. The first outside shown frame may start exactly
            # at the chosen cut, so <= is essential rather than strict <.
            visible[str(i)] = lo <= samples[i] < cut <= samples[i+1] < hi
    return dict(schema=SCHEMA, contract_revision=CONTRACT_REVISION,
        request_id=event['event_id']+'.'+side,
        event_id=event['event_id'], original_case_id=event['original_case_id'],
        original_segment_index=event['original_segment_index'], side=side,
        original_interval_exact=[str(start), str(end)], original_endpoint_exact=str(pivot),
        same_candidate_inner_anchor_exact=str(anchor),
        window_start=str(lo), window_end=str(hi),
        original_clock_origin_exact=str(origin),
        original_endpoint_context_exact=str(pivot-lo),
        same_candidate_inner_anchor_context_exact=str(anchor-lo),
        has_original_outside_context=(lo < pivot if side == 'start' else pivot < hi),
        has_original_outside_context_is_diagnostic_only=True,
        original_endpoint_kind=source_boundary,
        source_boundary_refinement_direction='INWARD_ONLY' if source_boundary != 'INTERIOR' else 'CONTEXT_BOUNDED',
        selected_cut_has_two_sided_visible_samples=visible,
        geometric_context_does_not_establish_same_event_transition=True,
        normalized_source_start_exact='0', normalized_source_physical_end_exact=str(physical_end),
        source_frame_ordinals=ordinals, sample_exact_pts=[str(p) for p in samples],
        sample_context_exact_pts=[str(p-lo) for p in samples],
        sample_boundary_exact=[str(p) for p in boundaries],
        sample_boundary_context_exact=[str(p-lo) for p in boundaries],
        endpoint_semantics=('FIRST_INCLUDED_FRAME_PTS' if side == 'start' else
                            'LAST_INCLUDED_FRAME_NEXT_NATIVE_PTS_OR_MEASURED_PHYSICAL_END'),
        original_endpoint_cut_ordinal=bisect_left(points, pivot),
        allowed_sample_indices=allowed, half_window_exact=str(HALF_WINDOW),
        semantic_event_identity='SAME_ORIGINAL_B_CANDIDATE_NO_NEW_EVENT',
        reference_available_to_inference=False, audio_observed=False)


def response_strings(request):
    return ('{"decision":"KEEP"}', '{"decision":"UNKNOWN"}') + tuple(
        '{"decision":"REFINE","sample_index":'+str(i)+'}'
        for i in request['allowed_sample_indices'])


def prompt(request):
    side = request['side']
    table = ', '.join(str(i)+'='+str(float(fraction(p)))
                      for i, p in enumerate(request['sample_context_exact_pts']))
    return (
        'Review ONLY the '+side+' boundary of the SAME supplied visual candidate. '
        'This is a silent clip; do not infer speech or object identities. '
        'Original candidate ID '+request['event_id']+' / B case '+request['original_case_id']+
        ' / segment '+str(request['original_segment_index'])+'. '
        'All seconds below are from this context clip start. '
        'The proposed '+side+' is '+str(float(fraction(request['original_endpoint_context_exact'])))+
        ' seconds. Its original candidate INSIDE direction is '+
        ('AFTER' if side == 'start' else 'BEFORE')+' this endpoint; the inner anchor is '+
        str(float(fraction(request['same_candidate_inner_anchor_context_exact'])))+' seconds. '
        'Locate where the visible content continuous with that INNER anchor begins/ends. '
        'A shot change or another unrelated action is not itself this candidate boundary. '
        'Do not reselect highlights, reject the event, add a new event, or prefer a clip edge. '
        'REFINE only when both the same candidate content and the outside transition at the '
        'NEW chosen cut are visually clear. Geometric timestamp continuity is not semantic '
        'evidence. At a supplied source start/end, only an inward cut with a clearly visible '
        'inside/outside transition in this clip is allowed; do not claim an unseen real '
        'action onset/end outside the source. A more intense phase of the same ongoing '
        'content is not itself an outside transition. If this identity/transition is uncertain, '
        'the NEW chosen cut lacks visible context on both sides, '
        'or a boundary falls at the first/last sample, return UNKNOWN. KEEP means the original '
        'endpoint is supported; UNKNOWN also preserves it. '
        'Sample indices and their actual context-local timestamps: '+table+'. '+
        ('A start sample is the first included frame. ' if side == 'start' else
         'An end sample is the LAST included frame; code converts it to the NEXT '
         'actual native PTS, or the measured positive last-frame ending. ')+
        'Return ONLY {"decision":"KEEP"} or {"decision":"UNKNOWN"} or '
        '{"decision":"REFINE","sample_index":N}. Valid N values are '+
        ','.join(map(str, request['allowed_sample_indices']))+'. No explanation.')


def parse_decision(text, request):
    if text not in response_strings(request):
        raise ValueError('Noncanonical/incomplete decision; no repair or empty fallback')
    return json.loads(text)


def resolve_endpoint(decision, request):
    """Explicit semantic no-change decisions, never exception fallback."""
    if decision not in [json.loads(s) for s in response_strings(request)]:
        raise ValueError('Decision is outside the frozen finite response grammar')
    old = fraction(request['original_endpoint_exact'])
    reason = decision['decision']
    new = old
    if reason == 'REFINE':
        index = decision['sample_index']
        if index in (0, NATIVE_FRAMES-1):
            reason = 'UNKNOWN_EDGE_SAMPLE'
        elif request['selected_cut_has_two_sided_visible_samples'].get(str(index)) is not True:
            reason = 'UNKNOWN_CHOSEN_CUT_VISIBLE_CONTEXT'
        elif request.get('original_endpoint_continuity_verified') is not True:
            reason = 'UNKNOWN_ORIGINAL_ENDPOINT_NATIVE_DOMAIN'
        elif request.get('continuity_by_sample', {}).get(str(index)) is not True:
            reason = 'UNKNOWN_SAMPLE_CONTINUITY'
        else:
            new = fraction(request['sample_boundary_exact'][index])
            if ((request['original_endpoint_kind'] == 'SOURCE_START' and not new > old) or
                    (request['original_endpoint_kind'] == 'SOURCE_PHYSICAL_END' and not new < old)):
                reason, new = 'UNKNOWN_SOURCE_BOUNDARY_OUTWARD_OR_UNCHANGED', old
    return dict(request_id=request['request_id'], event_id=request['event_id'],
        side=request['side'], raw_decision=decision, applied_decision=reason,
        original_endpoint_exact=str(old), endpoint_exact=str(new),
        displacement_exact=str(new-old), changed=new != old)


def resolve_event(event, start_result, end_result):
    """Crossed endpoints/anchor conflicts preserve both and remain visible."""
    if (start_result['event_id'] != event['event_id'] or start_result['side'] != 'start' or
            end_result['event_id'] != event['event_id'] or end_result['side'] != 'end'):
        raise ValueError('Endpoint pair is not the same original candidate identity')
    old_start, old_end = map(fraction, event['original_interval_exact'])
    start, end = fraction(start_result['endpoint_exact']), fraction(end_result['endpoint_exact'])
    conflict = start >= end
    if conflict:
        start, end = old_start, old_end
    return dict(event_id=event['event_id'], original_case_id=event['original_case_id'],
        original_segment_index=event['original_segment_index'],
        original_interval_exact=[str(old_start), str(old_end)],
        refined_interval_exact=[str(start), str(end)],
        changed=(start, end) != (old_start, old_end),
        pair_conflict_preserved_original=conflict,
        endpoint_results=[start_result, end_result],
        new_event_created=False, original_event_removed=False)


def verification_responses():
    """Draft candidate verification grammar; not registered in the pilot CLI."""
    return ('{"decision":"KEEP"}', '{"decision":"UNKNOWN"}', '{"decision":"DROP"}')


def verification_prompt(event, context_start, context_end):
    """Draft only. A highlight need not contain a complete physical action."""
    lo, hi = fraction(context_start), fraction(context_end)
    start, end = map(fraction, event['original_interval_exact'])
    if not 0 <= lo <= start < end <= hi:
        raise ValueError('Candidate verification requires its complete supplied interval in context')
    return (
        'Review ONLY the existing visual candidate '+event['event_id']+' / B case '+
        event['original_case_id']+' / segment '+str(event['original_segment_index'])+'. '
        'Its interval in seconds from this silent context start is ['+
        str(float(start-lo))+','+str(float(end-lo))+'). '
        'KEEP if the supplied content has visible distinctiveness, a meaningful visual result, '
        'an interesting scene, or another visually supported reason to retain it. '
        'DROP only with positive clear visual evidence that this whole supplied candidate is '
        'ordinary uneventful waiting, redundant repetition with no distinct new content, or '
        'visibly unsupported material. Missing evidence from sparse sampling is not evidence '
        'of ordinary content. Never require a complete action, a person, an action onset, or '
        'a completed result for a highlight. A landscape may itself be distinctive. '
        'For uncertain landscapes, speaking without audio, partial/incomplete activity, '
        'unclear temporal coverage, or insufficient context, return UNKNOWN. '
        'UNKNOWN preserves the candidate. Do not refine boundaries or select another event. '
        'Return ONLY {"decision":"KEEP"}, {"decision":"UNKNOWN"}, or '
        '{"decision":"DROP"}. No explanation.')


def parse_verification(text):
    if text not in verification_responses():
        raise ValueError('Invalid verification decision; no repair or DROP fallback')
    return json.loads(text)


def resolve_verification(text, event):
    decision = parse_verification(text)
    return dict(event_id=event['event_id'], original_case_id=event['original_case_id'],
        original_segment_index=event['original_segment_index'],
        original_interval_exact=event['original_interval_exact'],
        verification_decision=decision['decision'], candidate_kept=decision['decision'] != 'DROP',
        unknown_preserves_original=decision['decision'] == 'UNKNOWN',
        frame_removal_not_performed=True,
        requires_union_of_other_retained_candidates_before_any_frame_removal=True,
        implementation_scope='DRAFT_NOT_ADMITTED_NOT_REGISTERED_IN_CURRENT_PILOT')
