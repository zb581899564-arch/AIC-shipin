"""Unchanged previously verified full-native-clock measurement algorithm."""
from fractions import Fraction as F
from new5_common import MEDIA

def measured_clock(row, actual, container, stream, av):
    points, geometry, last_duration = [], None, None
    for frame in container.decode(stream):
        if frame.pts is None or frame.time_base is None:
            raise ValueError('Native frame lacks exact PTS/time base')
        point = F(frame.pts)*F(frame.time_base)
        if points and point <= points[-1]:
            raise ValueError('Original native PTS are not strictly increasing')
        points.append(point)
        current = (frame.width, frame.height)
        if geometry is None:
            geometry = current
        if current != geometry or min(current) <= 0:
            raise ValueError('Original frame geometry changed')
        duration = getattr(frame, 'duration', None)
        last_duration = F(duration)*F(frame.time_base) if duration is not None else None
    if not points or last_duration is None or last_duration <= 0:
        raise ValueError('Native ending lacks positive final-frame duration')
    origin = points[0]
    normalized = [p-origin for p in points]
    rate = stream.average_rate
    if rate is None or rate <= 0:
        raise ValueError('Original stream lacks declared positive average rate')
    return dict(source_name=row['source_name'], source_bytes=actual['bytes'],
        source_crc32=actual['crc32'], source_sha256=actual['sha256'], n_frames=len(points),
        normalized_exact_pts=list(map(str, normalized)), original_exact_pts=list(map(str, points)),
        first_original_pts_exact=str(origin), physical_end_exact=str(normalized[-1]+last_duration),
        width=geometry[0], height=geometry[1], source_path=str(MEDIA/(row['source_name']+'.webm')),
        fps_num=rate.numerator, fps_den=rate.denominator, decoder='PyAV', decoder_version=av.__version__,
        video_stream_index=stream.index,
        container_duration_microseconds=container.duration,
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
            last_normalized_pts_exact=str(normalized[-1]), last_frame_duration_exact=str(last_duration),
            duration_source='PyAV decoded final VideoFrame.duration * VideoFrame.time_base'))
