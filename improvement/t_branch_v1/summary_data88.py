"""The exact86 causal targets and publisher-balanced two-epoch schedule."""
from fractions import Fraction
import hashlib

import numpy as np
import torch

from causal_policy32 import causal_suffix
from t_io import ROOT, check, read


def load_inputs(rt):
    data = read(ROOT / 'summary_text_inputs87/completion.json')
    if data['state'] != 'PASS_FIRST_ALL86_SOURCE_CONTENT_CAUSAL_INPUTS':
        raise ValueError('Actual complete86 human-content input gate absent')
    publishers = {}; prefixes = {}
    for sid, source in data['original_sources'].items():
        if source['role'] != 'fit':
            raise ValueError('Non-fit source entered actual summary training')
        publishers.setdefault(source['publisher'], []).append(sid)
        row = data['source_prefixes'][sid]
        with np.load(check(row['prefix']), allow_pickle=False) as archive:
            values = {k: torch.from_numpy(archive[k].copy()) for k in archive.files}
        if rt.tensor_signature(values) != row['actual_signature']:
            raise ValueError('Actual pure-text inference prefix differs from first acceptance')
        prefixes[sid] = values['input_ids']
    if len(publishers) != 5 or sum(map(len, data['source_targets'].values())) != 86:
        raise ValueError('Actual publisher/source/reviewer denominator differs')
    for publisher, sids in publishers.items():
        sids.sort()
        for sid in sids:
            rows = data['source_targets'][sid]
            expected = Fraction(1, len(publishers) * len(sids) * len(rows))
            if any(Fraction(r['global_publisher_source_reviewer_weight']) != expected for r in rows):
                raise ValueError('Actual all-reviewer/publisher weighting differs from fixed protocol')
    order = sorted(publishers, key=lambda text: hashlib.sha256(text.encode()).hexdigest())
    return data, publishers, prefixes, order + list(reversed(order))


def actual_suffix(prefix, row, rt):
    suffix = causal_suffix(prefix, row['target_ids'])
    signature = rt.tensor_signature({k: suffix[k] for k in ['input_ids', 'attention_mask', 'targets']})
    if (signature != row['actual_causal_signature'] or suffix['logits_to_keep'] != row['logits_to_keep']
            or suffix['causal_positions'] != row['causal_positions']):
        raise ValueError('Actual new teacher-forced tokens/mask do not equal accepted complete target')
    return suffix, signature
