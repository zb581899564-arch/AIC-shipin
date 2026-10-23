"""First audio evidence for mixed audiovisual human descriptions, never new labels."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import shutil
import subprocess
import time
import traceback

import numpy as np
import torch

from description_wave65 import prepare
from speech_decode58 import digest
from speech_scope58 import original_helpers
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'description_audio65'
CACHE = Path('/dev/shm/aic_T_human_description_audio65')


def load_tiny():
    original36, helpers, _ = original_helpers()
    weight = read(original36.OLD / 'download_completion.json')['model_ref']
    if weight['sha256'] != '65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9':
        raise ValueError('Original tiny identity differs')
    module, functions, core = helpers.original_modules(original36.OLD / 'author')
    state = torch.load(check(weight), map_location='cpu', weights_only=True)
    model = module.Whisper(module.ModelDimensions(**state['dims']))
    model.load_state_dict(state['model_state_dict'], strict=True)
    model = model.float().eval().requires_grad_(False)
    count = sum(parameter.numel() for parameter in model.parameters())
    if count != 37184640 or torch.cuda.is_initialized():
        raise ValueError('CPU tiny parameter/runtime differs')
    vocab, special, languages, _ = helpers.vocabulary(original36.OLD / 'author', model)
    return model, helpers, functions, vocab, special, languages, dict(weight=weight, core=core, parameters=count)


def transcribe(accepted):
    model, helpers, functions, vocab, special, languages, proof = load_tiny()
    before = digest(model); outputs, available = {}, 0
    folder = OUT / 'asr'; folder.mkdir(); started = time.monotonic()
    for name, ref in accepted.items():
        if time.monotonic() - started >= 600:
            raise TimeoutError('Fixed first clip-ASR budget exhausted; successful tasks retained')
        row = read(check(ref)); chunk = row['chunk']
        with np.load(check(chunk['wave']), allow_pickle=False) as data:
            wave = torch.from_numpy(data['wave'].copy())
        if chunk['observed_fraction'] < .95:
            value = dict(status='VALID_ASR_ABSTAIN_INSUFFICIENT_OBSERVED_AUDIO', raw_text='', new_decoder_call=False)
        else:
            mel = functions['log_mel_spectrogram'](functions['pad_or_trim'](wave))
            if list(mel.shape) != [80, 3000] or not torch.isfinite(mel).all():
                raise ValueError('Original clip ASR frontend differs')
            value = helpers.transcribe(model, mel, vocab, special, languages)
            value['new_decoder_call'] = True
        value.update(input=ref, name=name, source=row['source'], condition=row['condition'],
            interval_exact=row['actual_native_interval_exact'], human_description_used=False,
            text_is_unverified_observation_not_label=True, no_word_time_alignment_claim=True)
        path = folder / (name + '.json'); save(path, value); outputs[name] = identity(path)
        available += int(value['status'] == 'ASR_TRANSCRIPT_AVAILABLE_UNVERIFIED_TEXT_NOT_GROUND_TRUTH')
        print('DESCRIPTION65_FIRST_ASR', name, value['status'], flush=True)
    if digest(model) != before or torch.cuda.is_initialized():
        raise ValueError('Original CPU tiny changed')
    save(OUT / 'ASR_completion.json', dict(state='FIRST48_NEW_CLIP_TRANSCRIPTS_COMPLETE_NOT_QUALITY',
        outputs=outputs, available=available, total=len(outputs), original_model=proof,
        CPU_seconds=time.monotonic() - started, new_GPU_calls=0, no_training=True))


def main():
    OUT.mkdir(); torch.set_num_threads(2); torch.set_num_interop_threads(1)
    inventory = read(ROOT / 'description_inventory63/completion.json')
    examples = read(check(inventory['selected_examples']))
    rows = examples['fit'] + examples['development']
    if len(rows) != 24 or any(row['source']['role'] == 'confirmation' for row in rows):
        raise ValueError('Fixed24 human-description role set differs')
    # Three previously undecoded source waveforms plus48 short clips, separate
    # from64's accepted visual arrays; no fixed free-space admission threshold.
    estimate = sum(int(float(__import__('fractions').Fraction(read(check(row['source']['clock']))['physical_end_exact'])) * 16000 * 9)
        for row in {x['source']['sid']: x for x in rows}.values())
    if shutil.disk_usage('/dev/shm').free < estimate or shutil.disk_usage(ROOT).free < 10000000:
        raise RuntimeError('Actual audio/caption input capacity insufficient')
    save(OUT / 'registration.json', dict(cohort=inventory['selected_examples'], pairs=24, new_clip_ASR_tasks=48,
        rationale='Human descriptions include spoken facts as well as visible events; do not blindly treat them as silent-visual truth',
        new_native_views_or_GPU=0, new_training=0, new_downloads=0,
        all_current_ASR_rules_unchanged=True, no_labels_or_descriptions_given_to_ASR=True,
        CPU_ASR_limit_seconds=600, code={n: identity(Path(__file__).parent / n) for n in
            ['description_wave65.py', 'description_audio65.py', 'speech_native58.py', 'speech_decode58.py']},
        RAM=subprocess.check_output(['free', '-b'], text=True),
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    CACHE.mkdir(); accepted = prepare(rows, CACHE, OUT)
    if len(accepted) != 48:
        raise ValueError('New exact audio-view task set incomplete')
    transcribe(accepted)
    save(OUT / 'completion.json', dict(state='MATCHED_HUMAN_CLIP_AUDIO_EVIDENCE_COMPLETE_NO_TRAINING_ADMISSION',
        native=identity(OUT / 'native_completion.json'), ASR=identity(OUT / 'ASR_completion.json'),
        fresh_confirmation_read=False, new_model_download=0, new_Qwen_or_GPU_calls=0,
        next='Only separately registered BASE/TIME matched/misaligned human-text likelihood diagnosis after64/65 CPU gates; not a candidate score'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
