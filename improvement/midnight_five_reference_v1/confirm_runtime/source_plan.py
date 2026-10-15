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
    from confirm_mapping import baseline_only_plan
    return baseline_only_plan(document, group)
