"""Pure unchanged native64 baseline formula, independently frozen short cohort."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
from reference_common import require

def baseline_only_plan(document, group='confirm'):
    """Same ceil(T/30) equal windows and ordinal formula; no overlap views."""
    require(document['schema'] == 'RECALL_SOURCE_CLOCKS_V1' and len(document['sources']) == 4
        and group == 'confirm', 'Complete first fresh four-source clock document required')
    views, source_rows, aliases, names = [], [], [], set()
    for source in document['sources']:
        name = source['video_id']; require(name not in names, 'Repeated baseline source'); names.add(name)
        points = list(map(F, source['normalized_exact_pts'])); end = F(source['physical_end_exact'])
        require(len(points) == source['n_frames'] and points[0] == 0 and points == sorted(set(points))
            and 0 < end <= 30 and end > points[-1], 'Complete positive zero-origin native clock required')
        count = (end.numerator+30*end.denominator-1)//(30*end.denominator); windows = []
        for index in range(count):
            a, b = end*index/count, end*(index+1)/count
            first, limit = bisect_left(points, a), bisect_left(points, b); number = limit-first
            require(number >= 64 and 0 < b-a <= 30, 'Unchanged baseline window cannot supply64 distinct native observations')
            ordinals = [first+i*(number-1)//63 for i in range(64)]; samples = [str(points[i]) for i in ordinals]
            identity = dict(source_sha256=source['source_sha256'], video_id=name, window_start_exact=str(a),
                window_end_exact=str(b), source_frame_ordinals=ordinals, sample_exact_pts=samples)
            key = 'view_'+hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            window = dict(case_id=name+'.baseline%04d'%index, index=index, start_exact=str(a), end_exact=str(b),
                eligible_first=first, eligible_stop=limit, source_frame_ordinals=ordinals, sample_exact_pts=samples, input_view_key=key)
            windows.append(window); views.append(dict(window, group=group, source_name=name, video_id=name,
                source_sha256=source['source_sha256'], window_role='baseline', view_roles=['baseline']))
            aliases.append(dict(video_id=name, role='baseline', planned_case_id=window['case_id'], actual_case_id=window['case_id'], input_view_key=key))
        source_rows.append(dict(video_id=name, source_sha256=source['source_sha256'], physical_end_exact=str(end),
            n_frames=source['n_frames'], windows=windows))
    baseline = dict(schema='RECALL_BASELINE_EQUAL_PLAN_V1', mode='baseline', native_frames=64,
        interval_policy='EXACT_HALF_OPEN_NO_PADDING', source_count=4, window_count=len(views), sources=source_rows,
        window_policy='EQUAL_NONOVERLAP_CEIL_PHYSICAL_END_DIV_30', maximum_window_seconds_exact='30')
    return dict(schema='MIDNIGHT_BASELINE_ONLY_UNIQUE_ACTUAL_VIEW_PLAN_V1', group=group, baseline_plan=baseline,
        unique_views=views, role_aliases=aliases, actual_input_count=len(views), baseline_alias_count=len(views),
        overlap_alias_count=0, shared_actual_inputs=0, maximum_possible_VERIFY_calls=5*len(views),
        same_view_actual_calls=1, scientific_quality_pass=False, GPU_admitted=False, model_calls=0)


