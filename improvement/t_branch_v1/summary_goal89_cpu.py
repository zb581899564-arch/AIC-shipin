"""First independently checked free goals from the final trained content adapter."""
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

OUT = ROOT / 'summary_goals89'
TEMP = Path('/dev/shm/aic_T_summary_goals89')


def main():
    torch.set_num_threads(2)
    path = Path(sys.argv[1]).resolve(strict=True)
    if path.parent != (OUT / 'raw').resolve(strict=True) or path.is_symlink():
        raise ValueError('Only the exact new89 trained goal may be checked')
    raw = torch.load(path, map_location='cpu', weights_only=True)
    cpu = read(check(raw['input_proof'])); trained = read(ROOT / 'summary_train88/completion.json')
    if (raw['model_role'] != 'final_trained_summary_only' or raw['active_summary_layers'] != 144
            or raw['actual_pipeline_parameters'] != 8869330010
            or raw['trained_adapter'] != trained['final_adapter']
            or cpu['source'] != raw['source'] or cpu['actual_signature'] != raw['actual_GPU_signature']
            or cpu['maximum_new_tokens'] != raw['maximum_new_tokens']):
        raise ValueError('Actual trained content role/input/final weight binding differs')
    activation = check(raw['temporary_scores'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('New89 temporary activation escaped exact registered root')
    ids, reduced = full_greedy(raw, raw['maximum_new_tokens'])
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    text = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    if text != raw['text'] or torch.cuda.is_initialized():
        raise ValueError('Actual trained free goal token/text or CPU role differs')
    representation = dict(format='free_text', successful_empty_goal=not bool(text.strip()))
    try:
        value = json.loads(text)
        if isinstance(value, dict) and set(value) == {'summary'} and isinstance(value['summary'], list):
            representation = dict(format='summary_JSON', successful_empty_goal=not value['summary'])
    except (ValueError, TypeError):
        pass
    proof = path.with_suffix('.CPU.json')
    save(proof, dict(state='PASS_FIRST_FINAL_TRAINED_GOAL_FULL_VOCABULARY_CPU',
        raw=identity(path), actual_input=raw['input_proof'], final_adapter=raw['trained_adapter'],
        actual_pipeline_parameters=8869330010, tokens=len(ids), **reduced,
        goal_representation=representation, no_temporal_quality_or_new_training_claim=True,
        unverified_machine_content_not_human_labels_or_ordinary=True))
    activation.unlink()
    save(path.with_suffix('.retirement.json'), dict(first_CPU_proof=identity(proof),
        retired_only_registered_current_activation=raw['temporary_scores'], permanent_raw=identity(path)))


if __name__ == '__main__':
    main()
