"""First native-bandwidth32k audio extraction; no repeated16k cache creation."""
from fractions import Fraction as F
import importlib.util
import math
import numpy as np
import av
from common import ROOT, OLD, read, write, checked, reference


def decoder(media, origin, index):
    pieces, starts = [], []
    with av.open(str(media)) as container:
        stream = next(s for s in container.streams if s.index == index and s.type == 'audio')
        rate = stream.codec_context.sample_rate
        if rate <= 16000:
            raise ValueError('No native high band to recover; do not repeat an equivalent decode')
        resampler = av.AudioResampler(format='fltp', layout='mono', rate=32000)

        def consume(frames):
            for frame in frames:
                if frame.pts is None or frame.time_base is None:
                    raise ValueError('Native resampler lacks exact PTS')
                starts.append(F(frame.pts)*F(frame.time_base)-origin)
                pieces.append(frame.to_ndarray().reshape(-1).copy())

        for packet in container.demux(stream):
            for frame in packet.decode():
                consume(resampler.resample(frame))
        consume(resampler.resample(None))
    if not starts or any(b < a for a,b in zip(starts, starts[1:])):
        raise ValueError('Native audio timestamps empty or nonmonotonic')
    offsets = np.r_[0, np.cumsum([len(x) for x in pieces])].astype(np.int64)
    return np.concatenate(pieces), offsets, starts, rate


def clipper():
    path = OLD/'code/audio_semantic23.py'
    spec = importlib.util.spec_from_file_location('adopted_exact_sample_mapping', path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.RATE = 32000
    return module.clip_from_frames, reference(path)


def high_band(wave, rate=32000):
    fft = np.fft.rfft(wave)
    power = abs(fft)**2
    total = float(power[1:].sum())
    return float(power[np.fft.rfftfreq(len(wave), 1/rate) > 8000].sum()/total) if total else None


def save_clip(item, receipt, values, offsets, starts, source_ref, mapping_function):
    begin, end = F(item['start_exact']), F(item['end_exact'])
    wave, observed, mappings = mapping_function(values, offsets, starts, begin, end)
    if len(wave) != math.ceil((end-begin)*32000) or observed.mean() < .95:
        raise ValueError('Native-bandwidth exact sample/coverage contract failed')
    target = ROOT/'inputs'/(item['uid']+'.npz')
    np.savez_compressed(target, wave=wave, observed=observed)
    with np.load(target, allow_pickle=False) as saved:
        if not np.array_equal(saved['wave'], wave) or not np.array_equal(saved['observed'], observed):
            raise ValueError('First native32k tensor save/load failed')
    visited = np.zeros(len(wave), bool)
    for row in mappings:
        lo, hi, frame = row['frame_first'], row['frame_stop'], row['frame']
        positions = np.arange(row['grid_first'], row['grid_first']+hi-lo)
        fresh = ~visited[positions]
        if not np.array_equal(wave[positions[fresh]], values[offsets[frame]+lo:offsets[frame]+hi][fresh]):
            raise ValueError('Independent native-sample mapping replay failed')
        visited[positions[fresh]] = True
    if not np.array_equal(visited, observed):
        raise ValueError('Missing audio mask differs from mapped actual samples')
    with np.load(checked(item['input_ref']), allow_pickle=False) as saved:
        old_high = high_band(saved['wave'])
    result = dict(item, input_ref=reference(target), samples=len(wave), observed_fraction=float(observed.mean()),
        original_audio_rate=receipt['original_audio_rate'], source_frames_ref=source_ref,
        old16k_upsampled_ref=item['input_ref'], high_band_fraction=high_band(wave),
        old16k_upsampled_high_band_fraction=old_high)
    write(ROOT/'inputs'/(item['uid']+'.mapping.json'), dict(source_frames=source_ref, mappings=mappings,
        original_clock=item['clock_ref'], old_receipt=item['old_receipt_ref']))
    return result


def main():
    original = read(ROOT.parent/'input_acceptance.json')['rows']
    folder = ROOT/'inputs';folder.mkdir()
    mapping_function, mapping_ref = clipper()
    rows = []
    for sid in dict.fromkeys(x['sid'] for x in original):
        items = [x for x in original if x['sid'] == sid]
        receipt = read(checked(items[0]['old_receipt_ref']))
        media = checked(receipt['media_ref']);clock = read(checked(items[0]['clock_ref']))
        if clock['source_sha256'] != receipt['media_ref']['sha256']:
            raise ValueError('Original media and native clock differ')
        values, offsets, starts, rate = decoder(media, F(clock['original_exact_pts'][0]), receipt['actual_stream_index'])
        source = folder/(sid+'_first32k_source_frames.npz')
        np.savez_compressed(source, values=values, offsets=offsets, starts_exact=np.asarray(list(map(str, starts))))
        receipt['original_audio_rate'] = rate
        for item in items:
            rows.append(save_clip(item, receipt, values, offsets, starts, reference(source), mapping_function))
        print('NATIVE_AUDIO_ACCEPTED', sid, rate, flush=True)
    write(ROOT/'input_acceptance.json', dict(status='PASS_FIRST8_NATIVE_BANDWIDTH32K_AUDIO_INPUTS',
        rows=rows, excerpts=8, sources=4, new_audio_decode_sources=4,
        not_recreating_old16k_or_video_inputs=True, original_label_and_video_clocks_unchanged=True,
        exact_mapping_helper_adopted=mapping_ref))


if __name__ == '__main__':
    main()
