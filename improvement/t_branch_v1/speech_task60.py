"""Adopt native visual tensors and load only first accepted speech text prefixes."""
from dataclasses import replace

import numpy as np
import torch

from t_io import ROOT, check, read

OUT = ROOT / 'speech_development60'
ARMS = ('original_correct', 'speech_correct', 'speech_shift')


def values(case, proof, rt):
    row = read(check(proof))
    if row['original_CPU'] != case.CPU:
        raise ValueError('Speech text belongs to a different original native view')
    with np.load(check(row['text']), allow_pickle=False) as archive:
        loaded = dict(case.values, **{name: torch.from_numpy(archive[name].copy()) for name in archive.files})
    if rt.tensor_signature(loaded) != row['actual_signature']:
        raise ValueError('Actual GPU speech/visual inputs differ from accepted CPU binding')
    return replace(case, values=loaded)
