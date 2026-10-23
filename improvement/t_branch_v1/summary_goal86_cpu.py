"""First two BASE content-goal output checks; not a temporal quality evaluation."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import json
import sys

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from summary_score86 import full_greedy
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_baseline86'
TEMP = Path('/dev/shm/aic_T_summary_goal86')


def main():
    torch.set_num_threads(2)
    path = Path(sys.argv[1]).resolve(strict=True)
    if path.parent != (OUT / 'raw').resolve(strict=True) or path.is_symlink():
        raise ValueError('Only the first new86 BASE goal may be checked')
    raw = torch.load(path, map_location='cpu', weights_only=True)
    cpu = read(check(raw['input_proof']))
    if (raw['model_role'] != 'original_BASE_TIME_disabled' or raw['actual_disabled_adapter_modules'] != 144
            or cpu['source'] != raw['source'] or cpu['actual_signature'] != raw['actual_input_signature']
            or cpu['maximum_new_tokens'] != raw['maximum_new_tokens']):
        raise ValueError('First actual goal/input/BASE role differs')
    activation = check(raw['temporary_scores'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('New86 activation escaped exact registered root')
    ids, reduced = full_greedy(raw, raw['maximum_new_tokens'])
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    text = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    if text != raw['text'] or torch.cuda.is_initialized():
        raise ValueError('First exact goal token/text or CPU execution check differs')
    diagnostic = dict(format='free_text', successful_empty_goal=not bool(text.strip()))
    try:
        value = json.loads(text)
        if isinstance(value, dict) and set(value) == {'summary'} and isinstance(value['summary'], list):
            diagnostic = dict(format='summary_JSON', successful_empty_goal=not value['summary'])
    except (ValueError, TypeError):
        pass
    proof = path.with_suffix('.CPU.json')
    save(proof, dict(state='PASS_FIRST_BASE_CONTENT_GOAL_TOKEN_AND_VOCABULARY_CPU',
        raw=identity(path), actual_input=raw['input_proof'], tokens=len(ids), **reduced,
        goal_representation=diagnostic, generated_goal_is_unverified_not_annotation=True,
        successful_empty_not_execution_failure_or_ordinary=True, no_temporal_quality_or_candidate_claim=True))
    activation.unlink()
    save(path.with_suffix('.retirement.json'), dict(first_CPU_proof=identity(proof),
        retired_only_registered_current_activation=raw['temporary_scores'], permanent_raw=identity(path)))


if __name__ == '__main__':
    main()
