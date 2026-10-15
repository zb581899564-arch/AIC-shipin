"""Generic original-video clock and native64 window plan for this new reference only."""
from bisect import bisect_left
from fractions import Fraction


def measure_original_video(path, av):
    points = []
    geometry = None
    last_duration = None
    with av.open(str(path)) as container:
        if container.start_time not in (0, None):
            raise ValueError('Original seconds origin is not verifiable; do not subtract a guessed offset')
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('Frame has no original exact presentation timestamp')
            point = Fraction(frame.pts) * Fraction(frame.time_base)
            if point < 0 or (points and point <= points[-1]):
                raise ValueError('Invalid original presentation clock')
            points.append(point)
            current = (frame.width, frame.height)
            if geometry is None:
                geometry = current
            if current != geometry or min(current) <= 0:
                raise ValueError('Native frame geometry inconsistent')
            frame_duration = getattr(frame, 'duration', None)
            last_duration = (Fraction(frame_duration) * Fraction(frame.time_base)
                             if frame_duration is not None else None)
        if not points or last_duration is None or last_duration <= 0:
            raise ValueError('Last original decoded frame has no positive duration')
        result = {'original_exact_pts': [str(point) for point in points],
                  'physical_end_exact': str(points[-1] + last_duration),
                  'first_original_pts_exact': str(points[0]),
                  'last_frame_duration_exact': str(last_duration),
                  'native_frames': len(points), 'width': geometry[0], 'height': geometry[1],
                  'container_start_time_microseconds': container.start_time,
                  'container_duration_microseconds_diagnostic_only': container.duration,
                  'decoder_version': av.__version__, 'timeline_shift_applied': False}
    return result


def validate_reference_endpoints(clock, original_references):
    end = Fraction(clock['physical_end_exact'])
    if len(original_references) != 10:
        raise ValueError('All ten original summary references required')
    for reference in original_references:
        for raw_start, raw_end in reference:
            start, stop = Fraction(raw_start), Fraction(raw_end)
            if not (0 <= start < stop <= end):
                raise ValueError('Unmodified original manual interval exceeds actual native video presentation domain')
    return {'all_original_intervals_fit_real_native_domain': True,
            'source_end_exact': str(end), 'author_nominal_duration_used_as_clock': False,
            'original_label_resizing_or_endpoint_repair': False}


def native64_windows(clock):
    points = [Fraction(value) for value in clock['original_exact_pts']]
    end = Fraction(clock['physical_end_exact'])
    if not points or points[0] < 0 or points[-1] >= end or any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError('Incomplete or invalid original clock')
    count = (end.numerator + 30 * end.denominator - 1) // (30 * end.denominator)
    result = []
    for index in range(count):
        start, stop = end * index / count, end * (index + 1) / count
        first, limit = bisect_left(points, start), bisect_left(points, stop)
        if limit - first < 64:
            raise ValueError('Fewer than64 actual frames; no padding or repeat fallback')
        ordinals = [first + sample * (limit - first - 1) // 63 for sample in range(64)]
        if len(set(ordinals)) != 64 or stop - start > 30:
            raise ValueError('Invalid frozen native64 sampling or window duration')
        result.append({'index': index, 'start_exact': str(start), 'end_exact': str(stop),
                       'source_frame_ordinals': ordinals,
                       'sample_exact_pts': [str(points[ordinal]) for ordinal in ordinals],
                       'eligible_first': first, 'eligible_stop': limit})
    return result
