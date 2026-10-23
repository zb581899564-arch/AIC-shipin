"""First remaining native64 decode by exact original ordinal, without seek assumptions."""
from fractions import Fraction
import hashlib

import av
import numpy as np

from t_io import identity, save


def sequential_window(source, clock, points, window, folder):
    ordinals = window['source_frame_ordinals']
    wanted = set(ordinals)
    origin = Fraction(clock['first_PTS_exact'])
    pictures = {}
    with av.open(source['media']['path']) as container:
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        for ordinal, frame in enumerate(container.decode(stream)):
            if ordinal > ordinals[-1]:
                break
            if frame.pts is None or Fraction(frame.pts) * frame.time_base != points[ordinal] + origin:
                raise ValueError('Actual first sequential native frame differs from accepted clock')
            if ordinal in wanted:
                pictures[ordinal] = frame.to_ndarray(format='rgb24')
    if set(pictures) != wanted:
        raise ValueError('Exact sequential scan did not contain all registered64 original ordinals')
    arrays = np.stack([pictures[index] for index in ordinals])
    path = folder / 'frames.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, rgb=arrays)
    rate = Fraction(clock['rate_diagnostic_only'])
    meta = dict(case_id=folder.name, source_name=source['source'], source_path=source['media']['path'],
        source_sha256=source['media']['sha256'], source_bytes=source['media']['bytes'],
        source_total_frames=clock['native_frames'], width=clock['width'], height=clock['height'],
        fps_num=rate.numerator, fps_den=rate.denominator,
        all_source_exact_pts=list(map(str, points)), original_clock_origin_exact=str(origin),
        window_start=window['start_exact'], window_end=window['end_exact'],
        source_frame_ordinals=ordinals, sample_exact_pts=window['sample_exact_pts'],
        pixel_sha256=[hashlib.sha256(image.tobytes()).hexdigest() for image in arrays],
        frame_array_path=str(path), frame_array_sha256=identity(path)['sha256'],
        reference_available_to_inference=False, audio_observed=False)
    save(folder / 'input.json', meta)
    return meta
