"""First independent full-vocabulary probability check; retain projected raw scores."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import sys

import numpy as np
import torch

from t_io import ROOT, check, identity, read, save

TEMP = Path('/dev/shm/aic_T_description_score67')


def main():
    torch.set_num_threads(2)
    raw_path = Path(sys.argv[1]).resolve(strict=True)
    if not raw_path.is_relative_to(ROOT / 'description_score67/raw'):
        raise ValueError('Only registered current score task permitted')
    raw = torch.load(raw_path, map_location='cpu', weights_only=True)
    manifest = read(check(raw['CPU_manifest']))
    task = manifest['tasks'][raw['input_key']]
    with np.load(check(task['tokens']), allow_pickle=False) as data:
        if not np.array_equal(data['target_tokens'], raw['targets']):
            raise ValueError('Actual human target differs from frozen CPU input')
    if raw['model_role'] not in ('BASE', 'TIME') or raw['actual_disabled_adapter_modules'] != (144 if raw['model_role'] == 'BASE' else 0):
        raise ValueError('Frozen model-role evidence differs')
    activation = check(raw['temporary_full_logits'])
    if activation.parent != TEMP.resolve(strict=True) or activation.is_symlink():
        raise ValueError('Temporary activation retirement escaped the registered exact root')
    scores = torch.load(activation, map_location='cpu', weights_only=True)
    logits = scores['logits'].float().numpy().astype(np.float64)
    targets = np.asarray(raw['targets'], dtype=np.int64)
    if logits.shape != tuple(raw['shape']) or len(logits) != len(targets) or not np.isfinite(logits).all():
        raise ValueError('Full-vocabulary activation or target shape invalid')
    maximum = logits.max(axis=1)
    normalizer = maximum + np.log(np.exp(logits - maximum[:, None]).sum(axis=1))
    selected = logits[np.arange(len(targets)), targets]
    logp = selected - normalizer
    gpu = np.asarray(raw['target_logp'], dtype=np.float64)
    error = float(np.max(np.abs(logp - gpu)))
    if not np.all(np.abs(logp - gpu) <= 2e-5 * (1 + np.abs(logp))) or torch.cuda.is_initialized():
        raise ValueError('First independent FP64 full-vocabulary probability differs')
    proof = raw_path.with_suffix('.CPU.json')
    save(proof, dict(state='PASS_FIRST_ALL_VOCABULARY_FP64_TARGET_PROBABILITY',
        input_key=raw['input_key'], model_role=raw['model_role'], raw_projection=identity(raw_path),
        full_activation=raw['temporary_full_logits'], actual_shape=list(logits.shape),
        CPU_selected_logits=selected.tolist(), CPU_log_normalizers=normalizer.tolist(),
        CPU_target_logp=logp.tolist(), mean_logp=float(logp.mean()), max_absolute_error=error,
        new_model_calls=0, first_CPU_implementation='NumPy float64 max/exp/sum/log, separate CUDA-masked process'))
    # The task outputs above remain durable. Only evaluator activations created
    # for this first check are retired, as registered before the model task.
    activation.unlink()
    save(raw_path.with_suffix('.retirement.json'), dict(first_CPU_proof=identity(proof),
        retired_temporary_activation=raw['temporary_full_logits'],
        permanent_projected_raw_preserved=identity(raw_path), no_old_or_unrelated_file_removed=True))


if __name__ == '__main__':
    main()
