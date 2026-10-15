"""Fail closed on original annotation/native-clock alignment, without length repair."""
from fractions import Fraction as F


def validate_mapping(registration_row, clock):
    expected = registration_row['annotation_frames']
    points = [F(value) for value in clock['normalized_exact_pts']]
    if (type(expected) is not int or not points or len(points) != expected or
            clock['n_frames'] != expected):
        raise ValueError('Original human/native frame count mismatch; no padding, truncation or interpolation')
    if points[0] != 0 or any(first >= second for first, second in zip(points, points[1:])):
        raise ValueError('Native normalized clock must start at zero and be strictly increasing')
    if clock['source_name'] != registration_row['source_name']:
        raise ValueError('Original source-name binding changed')
    if clock['source_bytes'] != registration_row['member']['bytes']:
        raise ValueError('Original source file size changed')
    if clock['source_crc32'] != registration_row['member']['crc32']:
        raise ValueError('Original ZIP member CRC changed')
    digest = clock['source_sha256']
    if len(digest) != 64 or any(character not in '0123456789abcdef' for character in digest):
        raise ValueError('Missing accepted media SHA256')
    end = F(clock['physical_end_exact'])
    if end <= points[-1]:
        raise ValueError('Missing positive physical final-frame duration')
    # A sanity check of timing metadata, not a repair or precise human cut-point claim.
    period = 1 / F(str(registration_row['annotation_fps']))
    nominal_span = expected * period
    reported_span = F(str(registration_row['annotation_duration']))
    if abs(end - nominal_span) > 2 * period or abs(end - reported_span) > 2 * period:
        raise ValueError('Native/annotation duration mapping is ambiguous beyond two nominal frames')
    return dict(status='PASS_ORIGINAL_MEMBER_ORDINAL_CLOCK_MAPPING', source_name=clock['source_name'],
                native_frames=len(points), human_frames=expected, source_sha256=digest,
                nominal_period_exact=str(period), physical_end_exact=str(end),
                nominal_span_difference_exact=str(end-nominal_span),
                reported_span_difference_exact=str(end-reported_span),
                labels_are_original_ordinal_selections=True, label_interpolation=False,
                timing_tolerance_is_not_endpoint_adjustment=True)
