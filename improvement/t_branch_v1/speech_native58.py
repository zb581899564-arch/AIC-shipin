"""First audio-only decode for two sources; adopt all successful visual clocks."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
import math
import time

import numpy as np

from speech_scope58 import OUT, WAVE, NEW, check, identity, original_helpers, read, save, selected_sources


def chunk_mapping(helpers, values, offsets, starts, lo, hi, folder, index):
    wave, observed, mapping = helpers.clip_from_frames(values, offsets, starts, lo, hi)
    visited = np.zeros(len(wave), dtype=bool)
    for item in mapping:
        frame, first, stop = item['frame'], item['frame_first'], item['frame_stop']
        positions = np.arange(item['grid_first'], item['grid_first'] + stop - first)
        fresh = ~visited[positions]
        if not np.array_equal(wave[positions[fresh]], values[offsets[frame] + first:offsets[frame] + stop][fresh]):
            raise ValueError('Independent original sample-to-window audio mapping differs')
        visited[positions[fresh]] = True
    if not np.array_equal(visited, observed) or wave[~observed].any():
        raise ValueError('Unknown audio samples changed into observed silence')
    path = folder / ('chunk_%03d.npz' % index)
    with path.open('xb') as stream:
        np.savez_compressed(stream, wave=wave, observed=observed)
    with np.load(path, allow_pickle=False) as restored:
        if not np.array_equal(restored['wave'], wave) or not np.array_equal(restored['observed'], observed):
            raise ValueError('First audio chunk serialization differs')
    return dict(index=index, wave=identity(path), start_exact=str(lo), end_exact=str(hi),
        observed_fraction=float(observed.mean()), observed_samples=int(observed.sum()), samples=len(wave),
        observed_silence_distinct_from_missing=True, max_grid_error_seconds='1/16000')


def prepare(source, module, helpers):
    sid = source['sid']; folder = WAVE / sid; folder.mkdir()
    clock = read(check(source['clock']))
    origin = Fraction(clock['first_PTS_exact'])
    end = Fraction(clock['physical_end_exact']) - origin
    check(source['media'])
    values, offsets, starts, original = module.audio_frames(source['media'], origin, folder)
    if time.monotonic() >= float(os.environ['AIC_SPEECH58_DEADLINE']):
        raise TimeoutError('CPU information budget elapsed; original audio frames retained')
    chunks = [chunk_mapping(helpers, values, offsets, starts, Fraction(first),
        min(Fraction(first + 30), end), folder, index)
        for index, first in enumerate(range(0, math.ceil(float(end)), 30))]
    record = dict(sid=sid, source=source, original_clock=source['clock'], original_audio_frames=original,
        chunks=chunks, physical_duration_exact=str(end), native_audio_mapping_PASS=True,
        repeated_video_decode=0, repeated_processor_calls=0, labels_read=False)
    path = OUT / (sid + '_native.json'); save(path, record)
    print('SPEECH58_FIRST_NATIVE_PASS', sid, len(chunks), flush=True)
    return identity(path)


def main():
    module, helpers, helper_ref = original_helpers()
    sources = selected_sources()
    accepted = [prepare(sources[sid], module, helpers) for sid in NEW]
    save(OUT / 'native_completion.json', dict(state='TWO_FIRST_NATIVE_AUDIO_INPUTS_PASS',
        accepted=accepted, original_helpers=helper_ref, labels_read=False, new_GPU_calls=0,
        no_repeated_video_clock_decode_or_successful_audio=True))


if __name__ == '__main__':
    main()
