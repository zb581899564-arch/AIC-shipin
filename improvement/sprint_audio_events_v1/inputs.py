"""First PANN-specific32k inputs from accepted16k waveforms, without decoding."""
from fractions import Fraction
import json
import math
import av
import numpy as np
import torch
from common import ROOT, OLD, read, write, checked, reference
from model import load, frontend_check


def resample(wave):
    frame = av.AudioFrame.from_ndarray(wave[None].copy(), format='fltp', layout='mono')
    frame.sample_rate = 16000
    frame.pts, frame.time_base = 0, Fraction(1, 16000)
    resampler = av.AudioResampler(format='fltp', layout='mono', rate=32000)
    frames = resampler.resample(frame) + resampler.resample(None)
    values = np.concatenate([value.to_ndarray().reshape(-1) for value in frames])
    cursor = 0
    for value in frames:
        if Fraction(value.pts)*Fraction(value.time_base) != Fraction(cursor, 32000):
            raise ValueError('New resampler timestamps are not contiguous')
        cursor += value.samples
    if len(values) != 2*len(wave) or not np.isfinite(values).all():
        raise ValueError('Resampler changed exact interval/sample count')
    return values.astype(np.float32, copy=False)


def prepare_waveforms(folder):
    rows = []
    for entry in read(OLD/'first_audio_inputs.json')['receipts']:
        receipt = read(checked(entry))
        with np.load(checked(receipt['waveform_ref']), allow_pickle=False) as saved:
            wave, observed = saved['wave'], saved['observed']
        if wave.dtype != np.float32 or observed.dtype != bool or not observed.mean() >= .95:
            raise ValueError('Adopted waveform or missing-modality contract changed')
        if len(wave) != math.ceil((Fraction(receipt['source_end_exact'])-Fraction(receipt['source_start_exact']))*16000):
            raise ValueError('Original exact interval differs from retained waveform')
        data = resample(wave)
        mask = np.repeat(observed, 2)
        target = folder/(receipt['uid']+'.npz')
        np.savez_compressed(target, wave=data, observed=mask)
        with np.load(target, allow_pickle=False) as check:
            if not np.array_equal(data, check['wave']) or not np.array_equal(mask, check['observed']):
                raise ValueError('First32k serialized tensor QA failed')
        rows.append(dict(uid=receipt['uid'], sid=receipt['sid'], input_ref=reference(target),
            old_receipt_ref=entry, old_waveform_ref=receipt['waveform_ref'],
            request_ref=receipt['request_ref'], clock_ref=receipt['original_clock_ref'],
            start_exact=receipt['source_start_exact'], end_exact=receipt['source_end_exact'],
            sample_rate=32000, samples=len(data), observed_fraction=float(mask.mean()),
            retained_grid_ceil_end_excess_seconds_exact=str(Fraction(len(wave),16000)-
                (Fraction(receipt['source_end_exact'])-Fraction(receipt['source_start_exact'])))))
    write(ROOT/'input_acceptance.json', dict(status='PASS_FIRST8_PANN32K_REAL_INPUTS',
        rows=rows, excerpts=len(rows), sources=len({row['sid'] for row in rows}),
        new_audio_or_video_decode=0, old_inputs_adopted=True, new_model_frontend_parity_only=True))
    print('PASS_FIRST8_PANN32K_INPUTS', flush=True)


def main():
    torch.set_num_threads(2)
    model, tensors = load()
    parameters = sum(value.numel() for value in model.parameters())
    total = 8782557449 + parameters
    if total > 9000000000:
        raise ValueError('Actual complete pipeline exceeds9B')
    proof = frontend_check(model)
    write(ROOT/'model_cpu_acceptance.json', dict(status='PASS_STRICT_AUTHOR_PANN_AND_FRONTEND_PARITY',
        actual_parameters=parameters, total_complete_pipeline_parameters=total,
        state_tensors=tensors, checks=proof, augmentation_in_eval_unused=True,
        no_backbone_training=True, weight_ref=read(ROOT/'acquisition05_completion.json')['weight']))
    del model
    folder = ROOT/'inputs';folder.mkdir()
    prepare_waveforms(folder)


if __name__ == '__main__':
    main()
