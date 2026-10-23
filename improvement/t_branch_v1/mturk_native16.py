"""One native decode: exact presentation clock and conservative duplicate sketches."""
from fractions import Fraction

import av


def difference_hash(frame):
    pixels = frame.reformat(width=9, height=8, format='gray').to_ndarray()
    bits = (pixels[:, 1:] > pixels[:, :-1]).ravel()
    return format(sum(int(value) << index for index, value in enumerate(bits)), '016x')


def native_profile(path, expected):
    expected_count = expected['num_frames']
    anchors = {0, expected_count // 4, expected_count // 2, 3 * expected_count // 4, expected_count - 1}
    points, durations, sketches = [], [], []
    geometry = (expected['width'], expected['height'])
    with av.open(str(path)) as container:
        if len(container.streams.video) != 1:
            raise ValueError('Ambiguous native video stream')
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        for ordinal, frame in enumerate(container.decode(stream)):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('Native presentation timestamp missing')
            point = Fraction(frame.pts) * frame.time_base
            if points and point <= Fraction(points[-1]):
                raise ValueError('Nonmonotone native presentation order')
            if (frame.width, frame.height) != geometry:
                raise ValueError('Mirror geometry and actual native geometry differ')
            duration = getattr(frame, 'duration', None)
            points.append(str(point))
            durations.append(str(Fraction(duration) * frame.time_base) if duration else None)
            if ordinal in anchors:
                sketches.append(dict(ordinal=ordinal, PTS=str(point), dhash64=difference_hash(frame)))
        if len(points) != expected_count or len(sketches) != len(anchors):
            raise ValueError('Actual native frame count differs; no label repair permitted')
        if durations[-1] is None or Fraction(durations[-1]) <= 0:
            raise ValueError('Actual positive last-frame duration is required')
        return dict(PTS=points, frame_durations=durations, native_frames=len(points),
                    physical_end_exact=str(Fraction(points[-1]) + Fraction(durations[-1])),
                    first_PTS_exact=points[0], width=geometry[0], height=geometry[1],
                    stream_time_base=str(stream.time_base), decoder=av.__version__,
                    rate_diagnostic_only=str(stream.average_rate),
                    container_duration_diagnostic_only=container.duration,
                    duplicate_sketches=sketches, no_resampling_or_annotation_repair=True)


def possible_duplicate_pairs(records):
    pairs = []
    for i, left in enumerate(records):
        for right in records[i + 1:]:
            distance = min((int(a['dhash64'], 16) ^ int(b['dhash64'], 16)).bit_count()
                           for a in left['sketches'] for b in right['sketches'])
            if distance <= 4:
                pairs.append(dict(left=left['source_id'], right=right['source_id'],
                                  minimum_hamming_distance=distance,
                                  automatic_identity_or_disjointness_claim=False))
    return pairs
