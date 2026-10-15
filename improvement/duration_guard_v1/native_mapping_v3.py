"""Original author ordinal vectors on original WebM decode order.

Reported container duration is diagnostic, not a video-frame label clock. The
v2 failure is retained; no label, timestamp or frame-count repair occurs here.
"""
from fractions import Fraction as F


def validate_mapping(registration_row, clock):
    expected = registration_row['annotation_frames']
    points = [F(value) for value in clock['normalized_exact_pts']]
    raw = [F(value) for value in clock['original_exact_pts']]
    if (type(expected) is not int or not points or len(points) != expected or
            len(raw) != expected or clock['n_frames'] != expected):
        raise ValueError('Original human/native frame count mismatch; no padding, truncation or interpolation')
    if points[0] != 0 or any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError('Native normalized clock must start at zero and be strictly increasing')
    origin = F(clock['first_original_pts_exact'])
    if raw[0] != origin or any(a-origin != b for a, b in zip(raw, points)):
        raise ValueError('Native raw and normalized PTS differ')
    if clock['source_name'] != registration_row['source_name']:
        raise ValueError('Original source-name binding changed')
    if clock['source_bytes'] != registration_row['member']['bytes']:
        raise ValueError('Original source file size changed')
    if clock['source_crc32'] != registration_row['member']['crc32']:
        raise ValueError('Original ZIP member CRC changed')
    digest = clock['source_sha256']
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Missing accepted media SHA256')
    end = F(clock['physical_end_exact'])
    evidence = clock['physical_endpoint_evidence']
    if (end <= points[-1] or evidence['kind'] != 'LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION' or
            F(evidence['last_normalized_pts_exact']) != points[-1] or
            F(evidence['last_frame_duration_exact']) <= 0 or
            points[-1] + F(evidence['last_frame_duration_exact']) != end):
        raise ValueError('Physical ending requires actual positive final-frame duration')
    period = 1 / F(str(registration_row['annotation_fps']))
    reported = F(str(registration_row['annotation_duration']))
    if period <= 0 or reported <= 0:
        raise ValueError('Invalid original timing metadata')
    return dict(status='PASS_ORIGINAL_MEMBER_ORDINAL_CLOCK_MAPPING_V3',
        source_name=clock['source_name'], native_frames=expected, human_frames=expected,
        source_sha256=digest, physical_end_exact=str(end), nominal_period_exact=str(period),
        nominal_span_difference_exact=str(end-expected*period),
        reported_span_difference_exact=str(end-reported),
        reported_duration_within_v2_tolerance=abs(end-reported) <= 2*period,
        reported_duration_is_diagnostic_only=True, labels_are_original_ordinal_selections=True,
        label_interpolation=False, label_padding=False, label_truncation=False,
        normalized_pts_are_actual_original_pts=True)
