"""Original presentation clock; no inferred offset, duration or label resizing."""
from fractions import Fraction as F

from native_profile_01 import native64_windows, validate_reference_endpoints


def measure_original_video(path, av):
    points, geometry, last_duration = [], None, None
    with av.open(str(path)) as container:
        if len(container.streams.video) != 1 or container.start_time not in (0, None):
            raise ValueError('Ambiguous video stream or unverifiable original seconds origin')
        stream = container.streams.video[0]
        if stream.start_time not in (0, None) or stream.time_base is None:
            raise ValueError('Original video stream has a nonzero or invalid presentation origin')
        rate = stream.average_rate
        if rate is None or F(rate) <= 0:
            raise ValueError('Missing original nominal frame rate; never infer the final duration from it')
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('Native frame has no exact presentation timestamp')
            point = F(frame.pts) * F(frame.time_base)
            if point < 0 or (points and point <= points[-1]):
                raise ValueError('Native presentation timestamps are not strictly increasing')
            points.append(point)
            current = (frame.width, frame.height)
            if geometry is None:
                geometry = current
            if current != geometry or min(current) <= 0:
                raise ValueError('Native frame geometry changed')
            duration = getattr(frame, 'duration', None)
            last_duration = F(duration) * F(frame.time_base) if duration is not None else None
        # None start_time plus a positive first PTS is not evidence for an origin at zero.
        if not points or last_duration is None or last_duration <= 0:
            raise ValueError('Actual positive final frame duration required')
        return dict(original_exact_pts=[str(point) for point in points],
            physical_end_exact=str(points[-1] + last_duration),
            first_original_pts_exact=str(points[0]), last_frame_duration_exact=str(last_duration),
            native_frames=len(points), width=geometry[0], height=geometry[1],
            fps_num=F(rate).numerator, fps_den=F(rate).denominator, video_stream_index=stream.index,
            stream_time_base_exact=str(F(stream.time_base)), stream_start_time=stream.start_time,
            container_start_time_microseconds=container.start_time,
            container_duration_microseconds_diagnostic_only=container.duration,
            decoder_version=av.__version__, timeline_shift_applied=False,
            original_zero_origin_verified=points[0] == 0)


def validate_original_origin(clock):
    if not clock['original_zero_origin_verified'] or F(clock['first_original_pts_exact']) != 0:
        raise ValueError('Original zero origin unverified; do not subtract a guessed offset')
