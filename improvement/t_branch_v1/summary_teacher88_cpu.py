"""First full-vocabulary human-target TF check, separate from free-output QA."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path
import sys

import numpy as np
import torch

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_train88'
TEMP = Path('/dev/shm/aic_T_summary_train88')


def main():
    torch.set_num_threads(2)
    path = Path(sys.argv[1]).resolve(strict=True)
    if path != OUT / 'first_TF_raw.json':
        raise ValueError('Only the exact first new88 teacher-forced raw may be checked')
    raw = read(path); activation = check(raw['temporary_full_logits'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('New training activation escaped exact temporary root')
    values = torch.load(activation, map_location='cpu', weights_only=True)['logits'].numpy().astype(np.float64)
    targets = np.asarray(raw['target_ids'], dtype=np.int64)
    if values.ndim != 2 or len(values) != len(targets) or not np.isfinite(values).all():
        raise ValueError('First actual full target-logit inventory invalid')
    maximum = values.max(axis=1)
    norm = maximum + np.log(np.exp(values - maximum[:, None]).sum(axis=1))
    selected = values[np.arange(len(targets)), targets]; logp = selected - norm
    if (not np.allclose(logp, raw['selected_logp'], atol=2e-5, rtol=2e-5)
            or not math.isclose(float(-logp.mean()), raw['unweighted_NLL'], rel_tol=2e-5, abs_tol=2e-5)):
        raise ValueError('First full-vocabulary human-target CPU likelihood differs')
    if raw['causal_signature'] != raw['accepted_target']['actual_causal_signature'] or torch.cuda.is_initialized():
        raise ValueError('First actual teacher-forced input or CPU role differs')
    proof = OUT / 'first_TF_independent_CPU.json'
    save(proof, dict(state='PASS_FIRST_CONTENT_TARGET_FULL_VOCABULARY_TF_CPU',
        raw=identity(path), actual_target_tokens=len(targets), full_vocabulary=values.shape[1],
        mean_NLL_FP64=float(-logp.mean()), teacher_forcing_not_greedy_or_official_quality=True,
        temporary_full_logits=raw['temporary_full_logits'], new_model_calls=0))
    activation.unlink()
    save(OUT / 'first_TF_activation_retirement.json', dict(first_CPU_proof=identity(proof),
        retired_only_registered_current_activation=raw['temporary_full_logits'], permanent_raw=identity(path)))


if __name__ == '__main__':
    main()
