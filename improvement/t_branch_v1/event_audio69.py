"""Exact new window speech; adopt every known identical successful ASR interval."""
from fractions import Fraction
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from description_audio65 import load_tiny
from description_wave65 import existing_sources
from event_memory69_common import INPUT, AVAILABLE, audio_key
from speech_decode58 import digest
from speech_native58 import chunk_mapping
from speech_scope58 import OUT as SPEECH, original_helpers
from t_io import ROOT, check, identity, read, save

CACHE = Path('/dev/shm/aic_T_event_audio69')


def prior_asr():
    refs = list(read(ROOT / 'description_audio65/ASR_completion.json')['outputs'].values())
    refs += read(SPEECH / 'ASR_completion.json')['outputs']
    for row in read(SPEECH / 'adopted_ASR.json').values():
        refs += row['outputs']
    result = {}
    for ref in refs:
        row = read(check(ref))
        if 'interval_exact' in row:
            sid, (start, end) = row['source'], row['interval_exact']
        else:
            sid, start, end = row['sid'], row['start_exact'], row['end_exact']
        key = audio_key(sid, start, end)
        if key not in result:
            result[key] = ref
    return result


def native_tasks(sources):
    prior = prior_asr(); full = existing_sources(); _, helpers, helper_ref = original_helpers()
    adopted, new = {}, {}
    CACHE.mkdir()
    for sid, source in sources.items():
        media, native, native_proof = full[sid]
        if any(case.meta['source_sha256'] != media['sha256'] for case in source.cases):
            raise ValueError('Adopted complete waveform is not this original media')
        todo = [case for case in source.cases if audio_key(sid, case.meta['window_start'], case.meta['window_end']) not in prior]
        if todo:
            with np.load(check(native), allow_pickle=False) as data:
                values, offsets = data['values'].copy(), data['offsets'].copy()
                starts = list(map(Fraction, data['starts_exact'].tolist()))
        for case in source.cases:
            start, end = map(Fraction, [case.meta['window_start'], case.meta['window_end']])
            key = audio_key(sid, start, end)
            if key in prior:
                adopted[case.name] = dict(ASR=prior[key], original_media=media,
                    adopted_native_waveform=native_proof, interval_exact=[str(start), str(end)])
                continue
            if not 0 < end - start <= 30:
                raise ValueError('Whole fixed window exceeds original tiny context; no trimming')
            folder = CACHE / case.name; folder.mkdir()
            chunk = chunk_mapping(helpers, values, offsets, starts, start, end, folder, 0)
            save(folder / 'CPU.json', dict(case=case.name, source=sid, interval_exact=[str(start), str(end)],
                original_CPU=case.CPU, original_media=media, original_complete_waveform=native,
                adopted_native_waveform=native_proof, chunk=chunk, new_audio_or_video_decode=False,
                no_labels_read=True))
            new[case.name] = identity(folder / 'CPU.json')
        if todo:
            del values, offsets, starts
    save(INPUT / 'native_audio_completion.json', dict(state='ALL_FIXED50_NATIVE_AUDIO_BOUND',
        adopted=adopted, first_new_clips=new, original_helpers=helper_ref,
        no_original_media_decode_repeated=True, prior_ASR_successes_not_repeated=True))
    return adopted, new


def transcribe(sources):
    adopted, tasks = native_tasks(sources)
    outputs = {name: row['ASR'] for name, row in adopted.items()}
    if not tasks:
        save(INPUT / 'ASR_completion.json', dict(state='ALL_WINDOW_ASR_COMPLETE', outputs=outputs,
            new_decoder_calls=0, adopted=len(adopted), no_failed_task_to_missing=True))
        return outputs
    model, helpers, functions, vocab, special, languages, proof = load_tiny()
    before = digest(model); folder = INPUT / 'ASR'; folder.mkdir(); started = time.monotonic(); decoder_calls = 0
    for name, ref in tasks.items():
        if time.monotonic() - started > 600:
            raise TimeoutError('New window ASR budget reached; keep successful journal')
        row = read(check(ref)); chunk = row['chunk']
        with np.load(check(chunk['wave']), allow_pickle=False) as data:
            wave = torch.from_numpy(data['wave'].copy())
        if chunk['observed_fraction'] < .95:
            value = dict(status='VALID_ASR_ABSTAIN_INSUFFICIENT_OBSERVED_AUDIO', raw_text='', new_decoder_call=False)
        else:
            mel = functions['log_mel_spectrogram'](functions['pad_or_trim'](wave))
            if list(mel.shape) != [80, 3000] or not torch.isfinite(mel).all():
                raise ValueError('Actual fixed window audio frontend differs')
            value = helpers.transcribe(model, mel, vocab, special, languages)
            value['new_decoder_call'] = True
            decoder_calls += 1
        value.update(input=ref, name=name, source=row['source'], interval_exact=row['interval_exact'],
            no_human_labels_used=True, text_is_unverified_not_word_aligned=True)
        path = folder / (name + '.json'); save(path, value); outputs[name] = identity(path)
        print('EVENT69_FIRST_ASR', name, value['status'], flush=True)
    if digest(model) != before or torch.cuda.is_initialized():
        raise ValueError('Original tiny changed or CPU process initialized CUDA')
    save(INPUT / 'ASR_completion.json', dict(state='ALL_WINDOW_ASR_COMPLETE', outputs=outputs,
        new_decoder_calls=decoder_calls, first_new_clip_tasks=len(tasks), adopted=len(adopted), actual_original_model=proof,
        CPU_seconds=time.monotonic() - started, no_failed_task_to_missing=True))
    return outputs


if __name__ == '__main__':
    try:
        from development_data46 import development_sources
        torch.set_num_threads(2); torch.set_num_interop_threads(1)
        sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                      values=False, labels=False)
        transcribe(sources)
    except Exception:
        save(INPUT / 'audio_failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
