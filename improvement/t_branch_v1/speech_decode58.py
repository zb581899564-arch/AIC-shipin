"""First remaining CPU tiny transcripts, preserving all abstentions and timing."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from collections import Counter
import hashlib
from fractions import Fraction
import time

import numpy as np
import torch

from speech_scope58 import OUT, check, identity, original_helpers, read, save


def digest(model):
    return {name: hashlib.sha256(value.detach().contiguous().numpy().tobytes()).hexdigest()
            for name, value in model.state_dict().items()}


def decode_source(source, model, functions, helpers, vocab, special, languages, deadline):
    outputs, available, language_counts = [], 0., Counter()
    for chunk in source['chunks']:
        if time.monotonic() >= deadline:
            raise TimeoutError('New CPU information budget elapsed; successful chunks retained')
        with np.load(check(chunk['wave']), allow_pickle=False) as archive:
            wave = torch.from_numpy(archive['wave'].copy())
        if chunk['observed_fraction'] < .95:
            result = dict(status='VALID_ASR_ABSTAIN_INSUFFICIENT_OBSERVED_AUDIO', raw_text='', new_decoder_call=False)
        else:
            mel = functions['log_mel_spectrogram'](functions['pad_or_trim'](wave))
            if list(mel.shape) != [80, 3000] or not torch.isfinite(mel).all():
                raise ValueError('Original CPU ASR mel contract differs')
            result = helpers.transcribe(model, mel, vocab, special, languages)
            result['new_decoder_call'] = True
        result.update(sid=source['sid'], index=chunk['index'], start_exact=chunk['start_exact'],
            end_exact=chunk['end_exact'], waveform_acceptance=chunk, no_human_labels_used=True,
            word_time_precision='NONE; only original30sec chunk intervals, no invented word alignment')
        path = OUT / 'asr' / (source['sid'] + '_%03d.json' % chunk['index'])
        save(path, result); outputs.append(identity(path))
        if result['status'] == 'ASR_TRANSCRIPT_AVAILABLE_UNVERIFIED_TEXT_NOT_GROUND_TRUTH':
            available += float(Fraction(chunk['end_exact']) - Fraction(chunk['start_exact']))
        language_counts[str(result.get('detected_language'))] += 1
        print('SPEECH58_FIRST_ASR', source['sid'], chunk['index'], result['status'], flush=True)
    return outputs, dict(sid=source['sid'], chunks=len(outputs), available_seconds=available,
        duration_seconds=float(Fraction(source['physical_duration_exact'])), languages=dict(language_counts))


def main():
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    module36, helpers, _ = original_helpers()
    weights = read(module36.OLD / 'download_completion.json')['model_ref']
    if weights['sha256'] != '65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9':
        raise ValueError('Original authorized tiny weight identity differs')
    original, functions, proof = helpers.original_modules(module36.OLD / 'author')
    state = torch.load(check(weights), map_location='cpu', weights_only=True)
    model = original.Whisper(original.ModelDimensions(**state['dims']))
    model.load_state_dict(state['model_state_dict'], strict=True)
    model = model.float().eval().requires_grad_(False)
    count = sum(p.numel() for p in model.parameters())
    if count != 37184640 or 8797892873 + count > 9000000000 or torch.cuda.is_initialized():
        raise ValueError('Actual CPU ASR/shared main parameter budget differs')
    vocab, special, languages, _ = helpers.vocabulary(module36.OLD / 'author', model)
    before = digest(model); (OUT / 'asr').mkdir()
    started = time.monotonic()
    deadline = float(os.environ['AIC_SPEECH58_DEADLINE'])
    outputs, summaries = [], []
    for ref in read(OUT / 'native_completion.json')['accepted']:
        new, summary = decode_source(read(check(ref)), model, functions, helpers, vocab, special, languages, deadline)
        outputs.extend(new); summaries.append(summary)
    if digest(model) != before or torch.cuda.is_initialized():
        raise ValueError('Frozen CPU ASR weights changed')
    save(OUT / 'ASR_completion.json', dict(state='TWO_FIRST_FULL_SOURCE_ASR_COMPLETE_NOT_QUALITY',
        outputs=outputs, sources=summaries, weights=weights, original_core=proof,
        actual_ASR_parameters=count, actual_with_original40_47=8782557449 + count,
        actual_with_optional_trained_actor=8797892873 + count,
        CPU_seconds=time.monotonic() - started, new_GPU_calls=0,
        no_new_training_or_confirmation_or_production=True))


if __name__ == '__main__':
    main()
