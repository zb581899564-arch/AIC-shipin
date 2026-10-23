"""Unique CPU continuation: remaining AV inputs, never automatically train."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import base64
from fractions import Fraction
from pathlib import Path
import shutil
import time
import traceback
from types import SimpleNamespace

import torch
from transformers import AutoTokenizer

from event_memory69_common import save_prefix
from frozen_branch46 import RUN
from summary_audio83 import prepare_clips, transcribe
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_av83'


def wait_for_first_inputs():
    launch = read(ROOT / 'summary_inputs84_launch.json')
    until = time.monotonic() + 2400
    while True:
        done, failed = ROOT / 'summary_inputs84/completion.json', ROOT / 'summary_inputs84/failure.json'
        if failed.exists():
            raise RuntimeError('Upstream first input stage failed; never re-launch it here')
        if done.exists():
            value = read(done)
            if value['state'] != 'FIRST_ALL217_FIT_NATIVE64_INPUTS_AND_QA_PASS':
                raise ValueError('Upstream input terminal is not the accepted scope')
            return value
        proc = Path('/proc') / str(launch['pid'])
        if not proc.exists():
            raise RuntimeError('Upstream parent exited without authoritative terminal; inspect, do not repeat')
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != launch['start_ticks'] or stat[0] == 'Z' or time.monotonic() > until:
            raise RuntimeError('Upstream handle identity/wait bound differs; no auto-recovery')
        time.sleep(3)


def first_ASR_token_QA(outputs, adopted):
    asset = WORK / 'bottleneck_24h_20261019_v1/audio_semantic23/author/whisper/assets/multilingual.tiktoken'
    ranks = {}
    for line in asset.read_bytes().splitlines():
        text, index = line.split(); ranks[int(index)] = base64.b64decode(text)
    count = 0
    for name, ref in outputs.items():
        if name in adopted:
            continue
        row = read(check(ref))
        if row['new_decoder_call']:
            text = b''.join(ranks[t] for t in row['generated_ids'] if t in ranks).decode('utf-8', errors='replace')
            if text != row['raw_text']:
                raise ValueError('First actual ASR text/token replay differs')
        count += 1
    return dict(first_ASR_token_checks=count, adopted_token_QA_not_repeated=True)


def main():
    terminal = wait_for_first_inputs(); OUT.mkdir(); started = time.monotonic()
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    inventory = read(ROOT / 'summary_content81/completion.json')
    sources = {row['source']['sid']: row['source'] for row in inventory['planned']}
    cases = {}
    for sid, refs in terminal['accepted'].items():
        if sid not in sources or sources[sid]['role'] != 'fit':
            raise ValueError('Unexpected development/confirmation source in fit preparation')
        cases[sid] = []
        for ref in refs:
            meta = read(check(read(check(ref))['input']))
            cases[sid].append(SimpleNamespace(name=meta['case_id'], meta=meta, CPU=ref))
    seconds = sum(float(Fraction(row['windows'][-1]['end_exact'])) for row in inventory['planned'])
    proposed = int(seconds * 16000 * 10 + 3000000 * 217)
    if proposed > shutil.disk_usage('/dev/shm').free:
        raise RuntimeError('Specific remaining audio/prefix estimate exceeds live tmpfs capacity')
    save(OUT / 'registration.json', dict(first217_visual_inputs=identity(ROOT / 'summary_inputs84/completion.json'),
        whole_fit_sources=9, fixed_original_native_windows=217, CPU_budget_seconds=1500,
        estimated_new_audio_prefix_bytes=proposed, no_labels_or_confirmation_in_input=True,
        same_original_tiny_local_ASR=True, no_author_Gemini_transcript=True,
        no_old_waveform_or_successful_interval_ASR_repeated=True,
        new_Qwen_calls=0, training_or_production_admitted=False))
    tasks, adopted = prepare_clips(sources, cases, started + 1500)
    outputs, usage = transcribe(tasks, adopted, started + 1500)
    save(OUT / 'ASR_completion.json', dict(outputs=outputs, **usage,
        first_token_QA=first_ASR_token_QA(outputs, adopted)))
    rt = runtime(); config = read(RUN / 'b_score_aligned_package_v4/config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    folder = OUT / 'prefixes'; folder.mkdir(); accepted = {}
    for sid, rows in cases.items():
        accepted[sid] = {}
        for case in rows:
            if time.monotonic() > started + 1500:
                raise TimeoutError('First AV prefix budget expired; preserve all successful artifacts')
            accepted[sid][case.name] = save_prefix(case, outputs[case.name], tokenizer, rt, folder / case.name)
            print('SUMMARY83_FIRST_AV_PREFIX', case.name, flush=True)
    if sum(map(len, accepted.values())) != 217 or torch.cuda.is_initialized():
        raise ValueError('Actual complete217 input/CPU execution denominator differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL217_FIT_AV_INPUTS_PASS_NOT_TRAINING_ADMISSION',
        accepted=accepted, original_visual=identity(ROOT / 'summary_inputs84/completion.json'),
        ASR=identity(OUT / 'ASR_completion.json'), CPU_seconds=time.monotonic() - started,
        all_human_target_descriptions_excluded_from_inference=True,
        fresh_confirmation_read=False, new_Qwen_calls=0, new_training=0,
        remaining='Freeze one whole-source content-supervision protocol and actual parameter/context/cost budget.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        else:
            save(ROOT / 'summary_av83_dependency_failure.json', dict(traceback=traceback.format_exc(),
                no_original_input_restart=True, new_ASR_or_Qwen_calls=0))
        raise
