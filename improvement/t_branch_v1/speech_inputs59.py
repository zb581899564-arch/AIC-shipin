"""First CPU prefix binding for aligned/shifted speech, with identical visual input."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
import hashlib
from pathlib import Path
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from development_data46 import development_sources
from prompt_contract13 import prompt_binding
from speech_scope58 import GENERAL, OUT as SPEECH, WORK
from speech_text59 import AVAILABLE, first_new_ASR_token_QA, halfshift, observations, prompt
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'speech_inputs59'


def encode(case, blocks, tokenizer, rt, folder):
    folder.mkdir()
    ids = case.values['input_ids'][0].tolist()
    decoded = tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if tokenizer.encode(decoded, add_special_tokens=False) != ids or decoded.count(rt.EMPTY_PROMPT) != 1:
        raise ValueError('Original prefix cannot support one exact task-text insertion')
    expected = prompt(rt.EMPTY_PROMPT, blocks, (case.meta['window_start'], case.meta['window_end']))
    replaced = tokenizer.encode(decoded.replace(rt.EMPTY_PROMPT, expected), add_special_tokens=False)
    pad = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    visual_end = max(i for i, token in enumerate(ids) if token == pad) + 1
    if replaced[:visual_end] != ids[:visual_end] or len(replaced) + 256 > 16384:
        raise ValueError('New speech changed visual/timestamp tokens or exceeds frozen context; never truncate')
    values = dict(case.values, input_ids=torch.tensor([replaced], dtype=torch.long))
    values['attention_mask'] = torch.ones_like(values['input_ids'])
    binding = prompt_binding(tokenizer, values['input_ids'],
        dict(prompt_sha256=hashlib.sha256(expected.encode()).hexdigest()), expected, 'COARSE_WITH_SPEECH')
    path = folder / 'text.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, input_ids=values['input_ids'].numpy(), attention_mask=values['attention_mask'].numpy())
    with np.load(path, allow_pickle=False) as archive:
        if not all(np.array_equal(archive[key], values[key].numpy()) for key in archive.files):
            raise ValueError('First new speech prefix roundtrip differs')
    save(folder / 'CPU.json', dict(original_CPU=case.CPU, text=identity(path), prompt_binding=binding,
        actual_signature=rt.tensor_signature(values), actual_video_and_native_timestamps_unchanged=True,
        original_text_prefix_tokens=len(ids), speech_prefix_tokens=len(replaced), no_processor_or_decode_repeated=True,
        no_labels_in_input=True, quoted_observations=blocks, source=case.meta['source_name']))
    return identity(folder / 'CPU.json')


def main():
    OUT.mkdir()
    if not (SPEECH / 'completion.json').exists():
        raise ValueError('All new native speech inputs and actual ASR must complete first')
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    blocks = observations(); accepted, information = {}, {}
    token_QA = first_new_ASR_token_QA(WORK / 'bottleneck_24h_20261019_v1/audio_semantic23/author/whisper/assets/multilingual.tiktoken')
    for sid, source in sources.items():
        known = sum((Fraction(row['source_end']) - Fraction(row['source_start']))
            for row in blocks[sid] if row['evidence_status'] == AVAILABLE)
        duration = Fraction(blocks[sid][-1]['source_end'])
        if Fraction(blocks[sid][0]['source_start']) != 0 or duration != source.timeline.end or known / duration < Fraction(1, 2):
            raise ValueError('Fixed development source lacks majority correctly timed ASR evidence')
        information[sid] = dict(blocks=len(blocks[sid]), available_fraction=float(known / duration),
            original_reviewers_read=False, exact_full_source_time_bound=True)
        accepted[sid] = {}
        for arm, content in [('speech_correct', blocks[sid]), ('speech_shift', halfshift(blocks[sid]))]:
            accepted[sid][arm] = {case.name: encode(case, content, tokenizer, rt, OUT / (arm + '_' + case.name))
                                   for case in source.cases}
    if torch.cuda.is_initialized():
        raise ValueError('CPU prefix preparation initialized CUDA')
    lengths = [read(check(ref))['speech_prefix_tokens'] for source in accepted.values() for arm in source.values() for ref in arm.values()]
    save(OUT / 'completion.json', dict(state='FIRST_ALL100_AV_TEXT_PREFIXES_PASS_NO_MODEL_QUALITY',
        accepted=accepted, information=information, new_inputs=len(lengths), min_prefix_tokens=min(lengths),
        max_prefix_tokens=max(lengths), first51_ASR_token_QA=token_QA, original50_coarse_controls_adopted=True,
        no_new_model_or_training_or_confirmation=True, labels_read=False, exact_visual_pixels_and_time_prefix_preserved=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
