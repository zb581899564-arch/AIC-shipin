"""Unchanged <=30s baseline and 15s/7.5s native64 view plan."""
from fractions import Fraction as F
import model_common as io
from overlap_plan import SOURCE_SCHEMA, plan_baseline_sources, plan_overlapping_sources, validate_sources

def source_document(accepted, clocks, group):
    """Pure conversion: use original zero-origin PTS, never subtract an offset."""
    io.require(group in ('dev', 'confirm') and len(accepted) == 4 and len(clocks) == 4,
               'Complete explicit four-source group required')
    sources = []
    for row in accepted:
        vid = row['video_id']; io.safe_id(vid)
        io.require(row['group'] == group and row['media']['group'] == group and row['media']['video_id'] == vid,
                   'Cross-group or mismatched source media receipt')
        clock = clocks[vid]
        points = clock['original_exact_pts']; end = F(clock['physical_end_exact'])
        io.require(clock['original_zero_origin_verified'] is True and F(clock['first_original_pts_exact']) == 0 and
            points and F(points[0]) == 0 and F(clock['last_frame_duration_exact']) > 0 and
            F(points[-1]) + F(clock['last_frame_duration_exact']) == end and
            clock['timeline_shift_applied'] is False and clock['native_frames'] == len(points),
            'Original accepted clock/positive native endpoint changed; no measurement or repair')
        io.require(type(clock['fps_num']) is int and type(clock['fps_den']) is int and
                   clock['fps_num'] > 0 and clock['fps_den'] > 0, 'Actual positive nominal-rate metadata required')
        sources.append(dict(video_id=vid, source_sha256=row['media']['sha256'], width=clock['width'],
            height=clock['height'], n_frames=clock['native_frames'], targetRatioWH=[16, 9],
            normalized_exact_pts=points, physical_end_exact=str(end), diagnostic_ratio_only=True))
    document = dict(schema=SOURCE_SCHEMA, sources=sources)
    validate_sources(document)
    return document


def unique_view_plan(document, group):
    baseline, overlap = plan_baseline_sources(document), plan_overlapping_sources(document)
    unique, aliases = {}, []
    for role, plan in (('baseline', baseline), ('overlap', overlap)):
        for source in plan['sources']:
            for window in source['windows']:
                key = window['input_view_key']
                if key not in unique:
                    unique[key] = dict(window, case_id=window['case_id'], group=group,
                        source_name=source['video_id'], video_id=source['video_id'],
                        source_sha256=source['source_sha256'], window_role=role, view_roles=[])
                view = unique[key]
                io.require(view['source_name'] == source['video_id'] and
                    view['source_frame_ordinals'] == window['source_frame_ordinals'] and
                    view['sample_exact_pts'] == window['sample_exact_pts'] and
                    view['start_exact'] == window['start_exact'] and view['end_exact'] == window['end_exact'],
                    'Shared view key has inconsistent actual input identity')
                if role not in view['view_roles']:
                    view['view_roles'].append(role)
                aliases.append(dict(video_id=source['video_id'], role=role, planned_case_id=window['case_id'],
                    actual_case_id=view['case_id'], input_view_key=key))
    io.require(0 < len(unique) <= 48, 'Actual unique B0 inputs exceed the frozen group budget; do not change windows/sources')
    return dict(schema='RECALL_UNIQUE_ACTUAL_VIEW_PLAN_V1', group=group, baseline_plan=baseline,
        overlap_plan=overlap, unique_views=list(unique.values()), role_aliases=aliases,
        actual_input_count=len(unique), baseline_alias_count=baseline['window_count'],
        overlap_alias_count=overlap['window_count'], shared_actual_inputs=sum(len(v['view_roles']) == 2 for v in unique.values()),
        maximum_possible_VERIFY_calls=5 * len(unique), same_view_actual_calls=1,
        scientific_quality_pass=False, GPU_admitted=False, model_calls=0)

