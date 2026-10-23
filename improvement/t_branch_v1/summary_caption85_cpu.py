"""Persistent independent CPU service: first QA of new85 outputs only."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import json
import sys
import traceback

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from summary_score86 import full_greedy
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_caption85'
TEMP = Path('/dev/shm/aic_T_summary_caption85')


def review(path, tokenizer):
    path = Path(path).resolve(strict=True)
    if path.parent != (OUT / 'raw').resolve(strict=True) or path.is_symlink():
        raise ValueError('Only this new85 raw may be checked')
    raw = torch.load(path, map_location='cpu', weights_only=True)
    if raw['model_role'] != 'original_BASE_TIME_disabled' or raw['actual_disabled_adapter_modules'] != 144:
        raise ValueError('Actual caption did not use the frozen BASE perception role')
    cpu = read(check(raw['input_proof']))
    if (cpu['case'] != raw['case'] or cpu['source'] != raw['source']
            or cpu['actual_signature'] != raw['actual_input_signature']
            or cpu['original_native_interval_exact'] != raw['original_interval_exact']):
        raise ValueError('First actual event/input/native interval binding differs')
    activation = check(raw['temporary_scores'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('Temporary full scores escaped exact registered85 root')
    ids, reduced = full_greedy(raw, 128)
    text = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    if text != raw['text'] or not text.strip() or torch.cuda.is_initialized():
        raise ValueError('First token/text or CPU execution check failed')
    proof = path.with_suffix('.CPU.json')
    save(proof, dict(state='PASS_FIRST_FULL_EVENT_GREEDY_TOKEN_AND_VOCABULARY_CPU',
        raw=identity(path), actual_input=raw['input_proof'], tokens=len(ids),
        **reduced, separate_CUDA_masked_NumPy_FP64=True,
        factual_accuracy_or_highlight_quality_claim=False, temporary_scores=raw['temporary_scores'],
        new_model_calls=0, first_fit_source_event=True))
    activation.unlink()
    save(path.with_suffix('.retirement.json'), dict(first_CPU_proof=identity(proof),
        retired_only_registered_current_activation=raw['temporary_scores'], permanent_raw=identity(path)))
    return identity(proof)


def main():
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    print(json.dumps(dict(state='READY_CPU_ONLY_FIRST_NEW85_QA')), flush=True)
    for line in sys.stdin:
        try:
            proof = review(json.loads(line)['raw_path'], tokenizer)
            print(json.dumps(dict(ok=True, proof=proof)), flush=True)
        except Exception:
            print(json.dumps(dict(ok=False, traceback=traceback.format_exc())), flush=True)
            raise


if __name__ == '__main__':
    main()
