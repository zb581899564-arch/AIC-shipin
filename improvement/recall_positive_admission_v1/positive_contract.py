"""Strict positive admission of immutable old KEEP candidates; no model imports."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import re

SCHEMA = 'RECALL_POSITIVE_ADMISSION_V1'
DECISIONS = ('KEEP', 'UNKNOWN', 'DROP')
MAX_INPUT_TOKENS = 16384
MAX_OUTPUT_TOKENS = 256
MODEL_PARAMETERS = 8782459120
BASELINE_SHA256 = '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def exact(value):
    require(not isinstance(value, bool), 'Exact finite seconds required')
    return F(str(value))


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def novel_support(event, meta, novel_ordinals):
    """Exact mathematical new-frame runs; never source labels or cropped endpoints."""
    points = list(map(exact, meta['all_source_exact_pts']))
    first, last = map(exact, event['original_interval_exact'])
    require(novel_ordinals and sorted(set(novel_ordinals)) == list(novel_ordinals),
            'Complete sorted unique novel native ordinals required')
    runs = []
    for ordinal in novel_ordinals:
        require(type(ordinal) is int and 0 <= ordinal < len(points) and first <= points[ordinal] < last,
                'Novel native frame escaped original candidate/source')
        if runs and runs[-1][1] == ordinal:
            runs[-1][1] += 1
        else:
            runs.append([ordinal, ordinal+1])
    end = exact(meta['physical_end_exact']); window_start = exact(meta['window_start'])
    spans = [[max(first, points[lo]), min(last, points[hi] if hi < len(points) else end)]
             for lo, hi in runs]
    require(all(a < b for a, b in spans), 'Novel run has no exact native support')
    shown = list(map(exact, meta['sample_exact_pts']))
    shown_ordinals = meta['source_frame_ordinals']
    return dict(novel_native_ranges=runs,
        novel_interval_exact=[[str(a), str(b)] for a, b in spans],
        novel_window_local_exact=[[str(a-window_start), str(b-window_start)] for a, b in spans],
        novel_visible_sample_counts=[sum(a <= p < b for p in shown) for a, b in spans],
        novel_visible_native_samples=[[dict(ordinal=ordinal, source_exact_pts=str(point),
            window_local_exact_pts=str(point-window_start)) for ordinal, point in zip(shown_ordinals, shown)
            if a <= point < b] for a, b in spans])


def request(event, meta, novel_ordinals):
    """New namespace, original full short-view pixels and unmodified endpoints."""
    require(isinstance(event['event_id'], str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', event['event_id']) is not None,
            'Safe immutable old event identity required')
    first, last = map(exact, event['original_interval_exact'])
    lo, hi = exact(meta['window_start']), exact(meta['window_end'])
    roles = meta.get('view_roles', [meta['window_role']])
    require('overlap' in roles and 0 <= lo <= first < last <= hi and hi-lo <= 15,
            'Only exact existing short-view candidates may seek new admission')
    require(meta['audio_observed'] is False and meta['reference_available_to_inference'] is False,
            'Silent visual-only inference without reference required')
    pts = list(map(exact, meta['sample_exact_pts']))
    ordinals = meta['source_frame_ordinals']
    require(len(pts) == len(ordinals) == 64 and len(set(ordinals)) == 64 and
            all(a < b for a, b in zip(pts, pts[1:])) and all(lo <= p < hi for p in pts),
            '64 distinct unchanged native visible samples required')
    shown = sum(first <= p < last for p in pts)
    require(shown > 0, 'An old KEEP candidate without a shown sample is not admissible')
    ident = 'PA1.'+canonical_sha([meta['source_sha256'], event['event_id'],
                               event['original_interval_exact']])[:40]
    support = novel_support(event, meta, novel_ordinals)
    decisions = list(DECISIONS) if all(support['novel_visible_sample_counts']) else ['UNKNOWN', 'DROP']
    return dict(schema=SCHEMA, request_id=ident+'.positive', event_id=ident,
        old_event_id=event['event_id'], original_case_id=meta['case_id'],
        original_segment_index=event['original_segment_index'], source_name=meta['source_name'],
        source_sha256=meta['source_sha256'], original_interval_exact=[str(first), str(last)],
        original_window_start_exact=str(lo), original_window_end_exact=str(hi),
        candidate_window_local_exact=[str(first-lo), str(last-lo)],
        candidate_visible_sample_count=shown, allowed_decisions=decisions,
        source_frame_ordinals=ordinals, sample_exact_pts=meta['sample_exact_pts'],
        reference_labels_read=False, audio_observed=False, old_decision='KEEP',
        action_completion_required=False, static_content_automatically_ordinary=False,
        uncertainty_is_ordinary_truth=False, new_candidate_created=False,
        boundaries_changed=False, baseline_deletion_authorized=False,
        novel_visibility_gate='ALL_NOVEL_RUNS_SHOWN' if all(support['novel_visible_sample_counts']) else 'KEEP_FORBIDDEN_UNSHOWN_NOVEL_RUN',
        **support)


def prompt(req):
    first, last = req['candidate_window_local_exact']
    novel = '; '.join('['+str(float(exact(a)))+','+str(float(exact(b)))+') seconds ('+
        str(count)+' shown samples: '+','.join('native#'+str(item['ordinal'])+'@'+
        str(float(exact(item['window_local_exact_pts'])))+'s' for item in samples)+')'
        for (a, b), count, samples in zip(req['novel_window_local_exact'],
            req['novel_visible_sample_counts'], req['novel_visible_native_samples']))
    return (
        'Decide strict positive admission of the supplied existing visual candidate. '
        'The original silent short window is shown through its original 64 sampled frames. '
        'Candidate '+req['old_event_id']+' / original B case '+req['original_case_id']+
        ' / segment '+str(req['original_segment_index'])+' occupies ['+
        str(float(exact(first)))+','+str(float(exact(last)))+') seconds from THIS window start. '
        'The exact parts whose native frames would be NEW beyond the protected baseline are: '+novel+'. '
        'Judge the supplied complete candidate only from these shown visual samples; '
        'do not infer unseen details, audio, intent, or an unshown event. '
        'KEEP only when EACH listed new part has its own clear positive visual evidence of '
        'a salient event, a meaningful '
        'change, a significant result, or visually distinctive information whose removal '
        'would lose an essential part of what that new part communicates. Existing baseline '
        'highlights elsewhere in the candidate cannot support admission of an uninformative '
        'new part. Assess every listed new part; a sampled gap, an unobservable new part or '
        'uncertainty about any one of them requires UNKNOWN for the whole candidate. '
        'Ordinary motion, repeated routine activity, or the mere presence of an object or '
        'person is insufficient for KEEP. A complete action is not required. Static content '
        'can qualify when the visual evidence itself clearly meets the same positive standard. '
        'If the shown samples do not clearly establish that standard or candidate identity '
        'is uncertain, use UNKNOWN. Use DROP only when the shown evidence clearly supports '
        'routine, redundant, or uninformative content. UNKNOWN is uncertainty and does not '
        'assert ordinary ground truth. Both UNKNOWN and DROP decline this new addition. '
        'Do not change the candidate boundaries or select another interval. The protected '
        'baseline cannot be deleted by this decision. No labels, audio, previous decision, reference '
        'summary, or external event description is supplied. Return ONLY one canonical '
        'JSON object from '+', '.join(responses(req))+'. No explanation.')


def responses(req=None):
    decisions = DECISIONS if req is None else tuple(req['allowed_decisions'])
    require(decisions in (DECISIONS, ('UNKNOWN', 'DROP')), 'Strict finite positive-admission decision subset required')
    return tuple('{"decision":"'+value+'"}' for value in decisions)


def resolve(text, req, *, execution_status):
    require(execution_status == 'MODEL_OK', 'Engineering failure blocks; no UNKNOWN fallback')
    require(text in responses(req), 'Untouched canonical generated JSON required; no repair')
    decision = json.loads(text)['decision']
    return dict(event_id=req['event_id'], request_id=req['request_id'],
        old_event_id=req['old_event_id'], original_case_id=req['original_case_id'],
        original_segment_index=req['original_segment_index'], source_sha256=req['source_sha256'],
        original_interval_exact=req['original_interval_exact'], decision=decision,
        eligible_for_new_addition=decision == 'KEEP',
        admitted_interval_exact=req['original_interval_exact'] if decision == 'KEEP' else None,
        boundaries_changed=False, new_candidate_created=False,
        baseline_deletion_authorized=False, uncertainty_is_ordinary_truth=False,
        successful_model_call_required=True)


def native_range(req, meta):
    points = list(map(exact, meta['all_source_exact_pts']))
    first, last = map(exact, req['original_interval_exact'])
    members = [i for i, point in enumerate(points) if first <= point < last]
    require(members and members == list(range(members[0], members[-1]+1)),
            'Unchanged candidate must have positive contiguous native membership')
    lo, hi = bisect_left(points, first), bisect_left(points, last)
    require([lo, hi] == [members[0], members[-1]+1], 'Independent native enumeration differs')
    return [lo, hi]
