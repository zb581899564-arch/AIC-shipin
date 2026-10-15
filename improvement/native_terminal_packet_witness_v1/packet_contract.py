"""Exact compressed-packet terminal evidence; never frame decode or inference."""
from fractions import Fraction as F

SCHEMA = 'NATIVE_TERMINAL_PACKET_WITNESS_V1'


class PacketUnavailable(ValueError):
    pass


def require(ok, why):
    if not ok:
        raise PacketUnavailable(why)


def exact(value):
    require(not isinstance(value, (bool, float)), 'Exact integer/rational packet clock required')
    return F(value)


def packet_row(pts, duration, time_base, size, stream_index, packet_sha256=None):
    require(type(pts) is int and type(duration) is int and type(size) is int and size >= 0,
            'Packet timestamp/duration/size must be actual integers')
    tick = exact(time_base)
    require(tick > 0, 'Packet time base must be positive')
    return dict(pts=pts, duration=duration, time_base_exact=str(tick), size=size,
                stream_index=stream_index, raw_display_pts_exact=str(pts*tick),
                duration_seconds_exact=str(duration*tick), compressed_packet_sha256=packet_sha256)


def resolve(matches, max_display_pts, old_raw_last_pts, origin, old_raw_end=None):
    last, zero = exact(old_raw_last_pts), exact(origin)
    require(len(matches) == 1, 'Expected exactly one packet at the last original FRAME PTS')
    row = matches[0]
    require(exact(row['raw_display_pts_exact']) == last and exact(max_display_pts) == last,
            'Last original frame PTS must equal the maximum display packet PTS')
    duration = exact(row['duration_seconds_exact'])
    require(row['duration'] > 0 and duration > 0 and row['size'] > 0,
            'Matching compressed packet must have actual positive duration and payload size')
    end = last-zero+duration
    require(last >= zero and end > last-zero, 'Positive physical terminal domain unavailable')
    if old_raw_end is not None:
        require(last+duration == exact(old_raw_end), 'Measured packet end differs from old explicit native end ticks')
    return dict(schema=SCHEMA, status='PASS_MATCHING_MAX_DISPLAY_PACKET_POSITIVE_DURATION_NOT_FRAME_DECODE',
                physical_end_exact=str(end), last_normalized_pts_exact=str(last-zero),
                last_packet_duration_exact=str(duration), original_raw_last_frame_pts_exact=str(last),
                original_raw_origin_exact=str(zero), max_packet_display_pts_exact=str(last),
                matching_packet_count=1, matching_packet=row,
                evidence_kind='COMPRESSED_PACKET_AT_ORIGINAL_LAST_FRAME_PTS_PLUS_POSITIVE_DURATION',
                old_explicit_end_equal=old_raw_end is not None,
                old_CFR_N_div_FPS_used_for_physical_end=False,
                new_full_frame_PTS_measured=False, actual_frame_decode_calls=0,
                future_full_frame_decode_and_duration_equality_required=True)
