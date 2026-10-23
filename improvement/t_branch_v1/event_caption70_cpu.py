"""First independent CPU replay of every free event token and greedy score."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import sys

import numpy as np
import torch
from transformers import AutoTokenizer

from event_memory69_common import CAPTION
from frozen_branch46 import RUN
from t_io import check, identity, read, save

TEMP = Path('/dev/shm/aic_T_event_caption70')


def main():
    torch.set_num_threads(2)
    path = Path(sys.argv[1]).resolve(strict=True)
    if not path.is_relative_to(CAPTION / 'raw'):
        raise ValueError('Only registered current raw event may be checked')
    raw = torch.load(path, map_location='cpu', weights_only=True)
    if raw['model_role'] != 'original_BASE_TIME_disabled' or raw['actual_disabled_adapter_modules'] != 144:
        raise ValueError('Actual shared BASE perception/TIME separation differs')
    cpu = read(check(raw['input_proof']))
    if cpu['case'] != raw['case'] or cpu['actual_signature'] != raw['actual_input_signature']:
        raise ValueError('Actual greedy event came from a different first CPU input')
    activation = check(raw['temporary_scores'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('Temporary activation escaped its exact registered root')
    scores = torch.load(activation, map_location='cpu', weights_only=True)['scores'].numpy().astype(np.float64)
    ids = np.asarray(raw['tokens'], dtype=np.int64)
    if (scores.ndim != 2 or len(scores) != len(ids) or not 0 < len(ids) <= 128
            or np.isnan(scores).any() or np.isposinf(scores).any()):
        raise ValueError('Actual full-vocabulary generation scores are invalid')
    if not np.array_equal(scores.argmax(axis=1), ids) or ids[-1] not in raw['eos'] or any(t in raw['eos'] for t in ids[:-1]):
        raise ValueError('Actual complete event is not first greedy EOS-terminated output')
    maximum = scores.max(axis=1)
    norm = maximum + np.log(np.exp(scores - maximum[:, None]).sum(axis=1))
    selected = scores[np.arange(len(ids)), ids]
    logp = selected - norm
    if not np.allclose(logp, raw['selected_logp'], atol=2e-5, rtol=2e-5):
        raise ValueError('Independent first full-vocabulary token probabilities differ')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    text = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    if text != raw['text'] or not text.strip() or torch.cuda.is_initialized():
        raise ValueError('First exact token/text replay failed; not an empty observation')
    proof = path.with_suffix('.CPU.json')
    save(proof, dict(state='PASS_FIRST_FULL_EVENT_GREEDY_TOKEN_AND_VOCABULARY_CPU',
        raw=identity(path), actual_input=raw['input_proof'], tokens=len(ids), full_vocabulary=scores.shape[1],
        CPU_mean_logp=float(logp.mean()), all_greedy_argmax=True, EOT_observed=True,
        factual_accuracy_or_highlight_quality_claim=False, temporary_scores=raw['temporary_scores'],
        separate_CUDA_masked_NumPy_FP64=True, new_model_calls=0))
    activation.unlink()
    save(path.with_suffix('.retirement.json'), dict(first_CPU_proof=identity(proof),
        retired_only_registered_current_activation=raw['temporary_scores'], permanent_raw=identity(path)))


if __name__ == '__main__':
    main()
