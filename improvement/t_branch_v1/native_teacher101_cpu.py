"""First actual8B native preference teacher: independent full-logit/cause/loss QA."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path
import sys

import numpy as np
import torch

from native_codec98 import causal_history
from native_training_data99 import coefficients
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_first_micro101'
TEMP = Path('/dev/shm/aic_T_native_action100_first')


def main():
    torch.set_num_threads(2); rt = runtime()
    raw = read(OUT / 'first_TF_raw.json'); task = raw['target_binding']
    generated = read(check(read(check(raw['actual_greedy']))['raw']))
    proof = read(check(task['actual_input_CPU']))
    with np.load(check(proof['text']), allow_pickle=False) as data:
        prefix = torch.from_numpy(data['input_ids'].copy())
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    expected = causal_history(prefix, generated['tokens'], code)
    signature = rt.tensor_signature({k: expected[k] for k in ['input_ids', 'attention_mask']})
    if (signature != raw['actual_causal_text_signature'] or expected['logits_to_keep'] != raw['choice_logit_positions']
            or generated['actual_model_state'] != raw['actual_model_state']):
        raise ValueError('First actual teacher uses a different prefix/greedy history/model state')
    activation = check(raw['temporary_full_logits'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('First native teacher activation escaped exact registered temporary root')
    full = torch.load(activation, map_location='cpu', weights_only=True)['logits'].numpy().astype(np.float64)
    if full.shape[0] != 32 or not np.isfinite(full).all():
        raise ValueError('First full vocabulary native teacher activation inventory invalid')
    z = full[:, [code['Yes'], code['No']]]; maximum = z.max(axis=1, keepdims=True)
    logp = z - maximum - np.log(np.exp(z - maximum).sum(axis=1, keepdims=True))
    a, b, weight = coefficients(task, raw['publisher_source_weight'])
    loss = -float(np.sum(a * logp[:, 0] + b * logp[:, 1])) * weight
    if (not np.allclose(logp, raw['binary_logp'], atol=2e-5, rtol=2e-5)
            or not math.isclose(loss, raw['weighted_preference_loss'], abs_tol=2e-6, rel_tol=3e-5)
            or torch.cuda.is_initialized()):
        raise ValueError('Independent native conditional binary/source-global preference loss differs')
    proof_path = OUT / 'first_TF_independent_CPU.json'
    save(proof_path, dict(state='PASS_FIRST_NATIVE_ON_POLICY_HISTORY_AND_FULL_LOGIT_LOSS_CPU',
        raw=identity(OUT / 'first_TF_raw.json'), original_source_reference=task['source_summary_reference'],
        actual_greedy_history_only=True, human_answers_not_in_teacher_input=True,
        choice_positions=32, full_vocabulary=full.shape[1], conditional_action_space=2,
        native_source_global_loss_FP64=loss, unknown_task_cells_zero_weight=True,
        summary_nonselection_not_generic_ordinary=True))
    activation.unlink()
    save(OUT / 'first_TF_activation_retirement.json', dict(first_CPU_proof=identity(proof_path),
        retired_only_registered_current_activation=raw['temporary_full_logits'],
        permanent_projected_raw=identity(OUT / 'first_TF_raw.json')))


if __name__ == '__main__':
    main()
