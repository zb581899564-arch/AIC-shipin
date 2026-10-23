"""Only missing fit audio/ASR, adopting full waveforms and identical intervals."""
from fractions import Fraction
from pathlib import Path
import time

import numpy as np
import torch

from description_audio65 import load_tiny
from description_wave65 import existing_sources
from event_audio69 import prior_asr
from event_memory69_common import audio_key
from speech_decode58 import digest
from speech_native58 import chunk_mapping
from speech_scope58 import original_helpers
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_av83'
CACHE = Path('/dev/shm/aic_T_summary_audio83')


def known_waveforms(sources):
    result = existing_sources()
    for row in read(ROOT / 'description_audio65/native_completion.json')['first_audio_sources']:
        sid = row['sid']
        if sid in sources:
            result[sid] = (sources[sid]['media'], row['full_audio'],
                           identity(ROOT / 'description_audio65/native_completion.json'))
    return result


def prepare_clips(sources, cases, deadline):
    prior = prior_asr(); full = known_waveforms(sources)
    module, helpers, helper_ref = original_helpers()
    CACHE.mkdir(); tasks, adopted, first_waveforms, reused = {}, {}, {}, {}
    for sid, source in sources.items():
        if time.monotonic() > deadline:
            raise TimeoutError('First AV preparation budget expired; preserve completed sources')
        folder = CACHE / sid; folder.mkdir()
        if sid in full:
            media, native, proof = full[sid]
            if media['sha256'] != source['media']['sha256']:
                raise ValueError('Prior complete waveform belongs to a different source')
            with np.load(check(native), allow_pickle=False) as data:
                values, offsets = data['values'].copy(), data['offsets'].copy()
                starts = list(map(Fraction, data['starts_exact'].tolist()))
            reused[sid] = dict(original_native=native, proof=proof)
        else:
            clock = read(check(source['clock'])); check(source['media'])
            values, offsets, starts, native = module.audio_frames(
                source['media'], Fraction(clock['first_PTS_exact']), folder)
            first_waveforms[sid] = dict(source=source, original_audio=native)
            save(OUT / (sid + '_first_full_audio.json'), first_waveforms[sid])
        for case in cases[sid]:
            lo, hi = map(Fraction, [case.meta['window_start'], case.meta['window_end']])
            key = audio_key(sid, lo, hi)
            if key in prior:
                adopted[case.name] = prior[key]; continue
            if not 0 < hi - lo <= 30:
                raise ValueError('Original equal native window exceeds fixed ASR context')
            target = folder / case.name; target.mkdir()
            chunk = chunk_mapping(helpers, values, offsets, starts, lo, hi, target, 0)
            path = target / 'native_CPU.json'
            save(path, dict(source=sid, interval_exact=[str(lo), str(hi)], original_CPU=case.CPU,
                original_media=source['media'], original_clock=source['clock'],
                original_complete_waveform=native, chunk=chunk, human_labels_read=False))
            tasks[case.name] = identity(path)
        del values, offsets, starts
    save(OUT / 'native_audio_completion.json', dict(state='ALL_FIT_EXACT_WINDOW_AUDIO_PASS',
        first_tasks=tasks, adopted_ASR=adopted, first_complete_waveforms=first_waveforms,
        reused_complete_waveforms=reused, original_helper=helper_ref,
        no_successful_prior_audio_decode_or_ASR_repeated=True))
    return tasks, adopted


def transcribe(tasks, adopted, deadline):
    outputs = dict(adopted)
    if not tasks:
        return outputs, dict(first_ASR_calls=0, adopted=len(adopted))
    model, helpers, functions, vocab, special, languages, proof = load_tiny()
    before = digest(model); folder = OUT / 'ASR'; folder.mkdir(); started = time.monotonic()
    for name, ref in tasks.items():
        if time.monotonic() > deadline:
            raise TimeoutError('First fit ASR budget expired; retain successful journal')
        row = read(check(ref)); chunk = row['chunk']
        with np.load(check(chunk['wave']), allow_pickle=False) as data:
            wave = torch.from_numpy(data['wave'].copy())
        if chunk['observed_fraction'] < .95:
            value = dict(status='VALID_ASR_ABSTAIN_INSUFFICIENT_OBSERVED_AUDIO',
                         raw_text='', new_decoder_call=False)
        else:
            mel = functions['log_mel_spectrogram'](functions['pad_or_trim'](wave))
            if list(mel.shape) != [80, 3000] or not torch.isfinite(mel).all():
                raise ValueError('Actual native-window ASR frontend differs')
            value = helpers.transcribe(model, mel, vocab, special, languages)
            value['new_decoder_call'] = True
        value.update(source=row['source'], interval_exact=row['interval_exact'], input=ref,
            no_human_labels_given_to_ASR=True, text_is_unverified_not_word_aligned=True)
        path = folder / (name + '.json'); save(path, value); outputs[name] = identity(path)
        print('SUMMARY83_FIRST_ASR', name, value['status'], flush=True)
    if digest(model) != before or torch.cuda.is_initialized():
        raise ValueError('Original CPU ASR weights or CPU execution role changed')
    return outputs, dict(first_ASR_calls=sum(read(check(r))['new_decoder_call']
                                           for n, r in outputs.items() if n not in adopted),
        adopted=len(adopted), ASR_model=proof, CPU_seconds=time.monotonic() - started)
