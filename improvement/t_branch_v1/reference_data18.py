"""Canonical input loader for first corrected VERIFY tasks, adopting old video tensors."""
import numpy as np
import torch

from t_io import check, read


def load_input(record):
    with np.load(check(record['adopted_multimodal']), allow_pickle=False) as archive:
        values = {key: torch.from_numpy(archive[key].copy()) for key in archive.files}
    with np.load(check(record['encoded_text']), allow_pickle=False) as archive:
        if set(archive.files) != {'input_ids', 'attention_mask'}:
            raise ValueError('Only explicit text-prefix tensors may replace the adopted input')
        values.update({key: torch.from_numpy(archive[key].copy()) for key in archive.files})
    values.update(record['non_tensor_inputs'])
    return values


def accepted_cases(root):
    terminal = read(root / 'CPU_completion.json')
    if terminal['state'] != 'PASS_FIRST_CORRECT_TASK_PREFIX14' or len(terminal['cases']) != 14:
        raise ValueError('First explicit-prompt input acceptance is incomplete')
    return terminal['cases']
