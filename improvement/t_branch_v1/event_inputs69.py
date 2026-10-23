"""First CPU-only local AV inputs, adopting all original native video caches."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import base64
from pathlib import Path
import shutil
import subprocess
import time
import traceback

import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from event_memory69_common import INPUT, save_prefix
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime


def first_asr_token_QA():
    result = read(INPUT / 'ASR_completion.json')
    adopted = read(INPUT / 'native_audio_completion.json')['adopted']
    asset = WORK / 'bottleneck_24h_20261019_v1/audio_semantic23/author/whisper/assets/multilingual.tiktoken'
    ranks = {}
    for line in asset.read_bytes().splitlines():
        text, index = line.split(); ranks[int(index)] = base64.b64decode(text)
    checked = []
    for name, ref in result['outputs'].items():
        if name in adopted:
            continue
        row = read(check(ref))
        if row['new_decoder_call']:
            text = b''.join(ranks[t] for t in row['generated_ids'] if t in ranks).decode('utf-8', errors='replace')
            if text != row['raw_text']:
                raise ValueError('First new ASR token/text replay differs')
        checked.append(ref)
    save(INPUT / 'first_ASR_token_QA.json', dict(state='PASS_FIRST_REMAINING_WINDOW_ASR_TOKENS',
        first_new=checked, adopted_successful_QA_not_repeated=True, no_model_calls=True))


def main():
    INPUT.mkdir(); torch.set_num_threads(2); torch.set_num_interop_threads(1)
    protocol = read(ROOT / 'code/event_memory_protocol69.json')
    frozen = read(ROOT / 'code/joint_policy_protocol44.json')
    sources = development_sources(None, None, frozen, values=False, labels=False)
    if set(sources) != set(protocol['development_sources']) or sum(len(s.cases) for s in sources.values()) != 50:
        raise ValueError('Exact complete two-source development set changed')
    # All waveforms already exist: only at most50 clipped float32 arrays and
    # small new text prefixes are materialized. No video or processor work.
    estimate = sum(4 * 16000 * float(source.timeline.end) for source in sources.values())
    if shutil.disk_usage('/dev/shm').free < estimate or shutil.disk_usage(ROOT).free < 3000000:
        raise RuntimeError('Actual proposed input/receipt capacity insufficient')
    started = time.monotonic()
    save(INPUT / 'registration.json', dict(protocol=identity(ROOT / 'code/event_memory_protocol69.json'),
        old50_visual_inputs_adopted=True, no_labels_or_confirmation_read=True,
        maximum_new_window_ASR=50, proposed_float32_wave_bytes=estimate,
        CPU_threads_chosen_after_live_resource_inspection=2))
    with (INPUT / 'audio_CPU.log').open('x') as stream:
        status = subprocess.run([str(WORK / 'env/qwen3vl_isolated_20260910/bin/python'), '-B', '-u',
            str(Path(__file__).with_name('event_audio69.py'))], stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')).returncode
    save(INPUT / 'audio_CPU_terminal.json', dict(exit_code=status))
    if status:
        raise RuntimeError('First native audio stage failed; retain all successful intervals')
    speech = read(INPUT / 'ASR_completion.json')['outputs']; first_asr_token_QA()
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    folder = INPUT / 'prefixes'; folder.mkdir(); accepted = {}
    for sid, source in sources.items():
        accepted[sid] = {}
        for case in source.cases:
            accepted[sid][case.name] = save_prefix(case, speech[case.name], tokenizer, rt, folder / case.name)
            print('EVENT69_FIRST_AV_INPUT', case.name, flush=True)
    if torch.cuda.is_initialized() or sum(len(v) for v in accepted.values()) != 50:
        raise ValueError('All fixed50 event inputs must pass without CUDA')
    save(INPUT / 'completion.json', dict(state='FIRST_ALL50_LOCAL_EVENT_AV_INPUTS_PASS',
        accepted=accepted, maximum_first_event_generations=50,
        new_visual_decode_or_processor_calls=0, all_human_labels_excluded=True,
        first_ASR_token_QA=identity(INPUT / 'first_ASR_token_QA.json'),
        ASR=identity(INPUT / 'ASR_completion.json'), fresh_confirmation_read=False,
        CPU_seconds=time.monotonic() - started, no_model_quality_claim=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if INPUT.exists():
            save(INPUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
