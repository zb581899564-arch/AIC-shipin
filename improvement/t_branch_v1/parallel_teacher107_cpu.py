"""Independent first full-vocabulary query loss/readout check; CPU only."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path

import numpy as np
import torch

from native_training_data99 import coefficients
from parallel_query105 import select
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_cost107'
TEMP = Path('/dev/shm/aic_T_parallel_first107')


def main():
    torch.set_num_threads(2)
    raw = read(OUT / 'first_TF_raw.json')
    input_proof = read(check(raw['actual_input_CPU']))
    output = read(check(read(check(raw['actual_selection']))['raw']))
    path = check(raw['temporary_full_logits'])
    if path.parent != TEMP.resolve(strict=True) or path.is_symlink():
        raise ValueError('First parallel activation escaped its registered exact temporary directory')
    logits = torch.load(path, map_location='cpu', weights_only=True)['logits'].numpy().astype(np.float64)
    code = input_proof['actual_query_code']
    binary = logits[:, [code['Yes'], code['No']]]
    logp = binary - binary.max(axis=1, keepdims=True)
    logp -= np.log(np.exp(logp).sum(axis=1, keepdims=True))
    a, b, weight = coefficients(raw['target_binding'], raw['publisher_source_weight'])
    loss = -float(np.sum(a * logp[:, 0] + b * logp[:, 1])) * weight
    selected = select(binary, code)
    expected_ids = [code['Yes'] if v else code['No'] for v in selected]
    if (logits.shape[0] != 32 or not np.isfinite(logits).all()
            or not np.array_equal(binary, output['binary_logits'])
            or expected_ids != output['selected_token_ids']
            or raw['query_positions'] != input_proof['query_positions']
            or not np.allclose(logp, raw['binary_logp'], atol=2e-5, rtol=2e-5)
            or not math.isclose(loss, raw['weighted_preference_loss'], abs_tol=2e-6, rel_tol=3e-5)
            or torch.cuda.is_initialized()):
        raise ValueError('Independent first parallel full-logit native selection/source loss differs')
    proof = OUT / 'first_TF_CPU.json'
    save(proof, dict(state='FIRST_PARALLEL_FULL_VOCAB_NATIVE_SELECTION_AND_LOSS_CPU_PASS',
        actual_TF=identity(OUT / 'first_TF_raw.json'), actual_query_input=raw['actual_input_CPU'],
        positions=32, vocabulary_columns=logits.shape[1], source_global_preference_loss_FP64=loss,
        no_previous_human_or_generated_choices_in_input=True, summary_no_is_not_generic_NHL=True))
    path.unlink()
    save(OUT / 'first_TF_activation_retirement.json', dict(retired_only_new_activation=raw['temporary_full_logits'],
        prior_independent_CPU=identity(proof), permanent_projected_raw=identity(OUT / 'first_TF_raw.json')))


if __name__ == '__main__':
    main()
