"""Explicit three-condition selector roots and adoption-only input loading."""
import numpy as np
import torch

from coarse_call25 import load_case
from event_table71 import ARMS
from t_io import ROOT, check, read

CPU = ROOT / 'event_inputs71'
OUT = ROOT / 'event_selection72'


def values(case, task, rt, tokenizer):
    actual = load_case(case.CPU, rt, tokenizer)[2]
    if 'original_CPU_adopted' in task:
        if task != dict(original_CPU_adopted=case.CPU):
            raise ValueError('Actual no-memory control is not the accepted original input')
    else:
        proof = read(check(task['first_event_text_CPU']))
        if proof['original_CPU'] != case.CPU or proof['case'] != case.name:
            raise ValueError('Event context was assigned to a different original case')
        with np.load(check(proof['text']), allow_pickle=False) as data:
            actual.update({k: torch.from_numpy(data[k].copy()) for k in data.files})
        if rt.tensor_signature(actual) != proof['actual_signature']:
            raise ValueError('Actual source event prefix differs from first accepted CPU')
    return actual


def prefix_ids(case, task):
    proof = read(check(case.CPU)) if 'original_CPU_adopted' in task else read(check(task['first_event_text_CPU']))
    encoded = proof['encoded'] if 'original_CPU_adopted' in task else proof['text']
    with np.load(check(encoded), allow_pickle=False) as data:
        return torch.from_numpy(data['input_ids'].copy())
