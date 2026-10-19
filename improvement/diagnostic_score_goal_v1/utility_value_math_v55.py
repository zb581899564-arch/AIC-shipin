"""Pure contracts for one fresh continuous-IoU-gradient experiment.

No artifact, processor, decoder or model IO. The2000 original micro draws are
reweighted so their *aggregate empirical objective* is the mean over1204
unordered pairs from602 sources; individual Adam updates are not equal-weight
closed-form fitting. Targets remain original IoU(B)-IoU(A).
"""
from collections import Counter
import hashlib
import json
import math
from numbers import Integral, Real

import numpy as np

RECIPE = dict(updates=500, grad_accum=4, rank=8, alpha=16, dropout=0., lora_lr=5e-5,
    head_lr=.001, geometry_lr=.001, weight_decay=0., grad_clip=1., seed=20261018,
    head_init_std=.001, head_bias=False, geometry_init=0.,
    loss='DRAW_WEIGHT_TIMES_TARGET_RMS_NORMALIZED_SQUARED_GAIN_ERROR', final_only=True)


def require(value, reason):
    if not value:
        raise ValueError(reason)


def number(value):
    require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_)) and math.isfinite(value),
            'Explicit finite numeric value required')
    return float(value)


def index(value):
    require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)) and value >= 0,
            'Explicit nonnegative integer required')
    return int(value)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_schedule(prepared):
    require(prepared['schema'] == 'UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55', 'New utility55 train-only compiler required')
    rows = prepared['train_schedule']; rms = number(prepared['train_target_RMS'])
    require(rms > 0 and isinstance(rows, list) and len(rows) == 2000
            and len({r['id'] for r in rows}) == 2000, 'Nonzero frozen RMS and exact2000 micro IDs required')
    classes = prepared['class_token_ids']
    require(isinstance(classes, list) and len(classes) == len(set(classes)) == 3
            and all(type(c) is int and c >= 0 for c in classes), 'Actual three distinct class IDs required')
    counts = Counter(); sources = {}; unique = {}; scheduled_sources = Counter()
    for row in rows:
        sid, sha = row['source_id'], row['source_sha256']; a, b = index(row['a']), index(row['b'])
        require(isinstance(sid, str) and sid and isinstance(sha, str) and len(sha) == 64
                and all(c in '0123456789abcdef' for c in sha) and a != b, 'Explicit source identity and distinct ordered crops')
        require(sources.get(sid, sha) == sha, 'One source has conflicting SHA')
        sources[sid] = sha; scheduled_sources[sid] += 1
        pair = sorted((a, b)); require(row['unordered_pair'] == pair, 'Canonical unordered pair owner differs')
        key = sid, *pair; counts[key] += 1
        y = number(row['target']); require(-1 <= y <= 1, 'Original signed IoU target outside[-1,1]')
        g = np.asarray(row['geometry_delta11'])
        require(g.shape == (11,) and g.dtype.kind in 'fiu' and bool(np.isfinite(g).all()), 'Finite GT-free11 geometry differences')
        canonical = dict(target=y if a < b else -y,
                         geometry=(g if a < b else -g).astype(np.float64).tolist())
        require(unique.get(key, canonical) == canonical, 'Repeated/swap target or geometry changed')
        unique[key] = canonical
        for name in ('forward', 'reverse'):
            entry = row[name]
            require(entry['source_id'] == sid and entry['source_sha256'] == sha
                    and isinstance(entry['id'], str) and entry['id'] and set(entry['input']) == {'path', 'sha256'},
                    'Both input refs need exact same source owner')
            require(row[name+'_id'] == entry['id'], 'Scheduled real forward/reverse ID differs')
        require(row['forward']['id'] != row['reverse']['id'] and row['forward']['input'] != row['reverse']['input'],
                'Distinct actual AB/BA inputs required')
    require(len(sources) == len(set(sources.values())) == 602 and len(unique) == 1204
            and all(v == 2 for v in Counter(k[0] for k in unique).values()), 'Exact602 distinct sources/two unordered pairs')
    expected_rms = math.sqrt(math.fsum(v['target']**2 for v in unique.values())/1204)
    require(math.isclose(rms, expected_rms, rel_tol=1e-12, abs_tol=1e-15), 'Frozen train RMS differs from unique1204 source-equal targets')
    for row in rows:
        expected = 2000/(1204*counts[(row['source_id'], *row['unordered_pair'])])
        require(number(row['draw_weight']) == expected, 'Fixed inverse unordered-pair draw weight differs')
    require(math.isclose(math.fsum(number(r['draw_weight']) for r in rows), 2000., rel_tol=1e-14), 'Aggregate empirical objective normalization')
    return rows, digest(rows), dict(sources=602, unordered_pairs=1204, micro=2000,
        source_draws=dict(scheduled_sources), unordered_pair_draw_histogram=dict(Counter(counts.values())),
        train_target_RMS=rms, source_pair_equal_empirical_objective=True,
        individual_Adam_steps_are_not_equal_weight_solves=True)


def prediction(head, hidden_forward, hidden_reverse, beta, geometry_delta):
    """Differentiable float32 gain, preserving both hidden autograd graphs."""
    import torch
    require(head.bias is None and tuple(head.weight.shape) == (1, 4096)
            and tuple(hidden_forward.shape) == tuple(hidden_reverse.shape) == (4096,)
            and tuple(beta.shape) == tuple(geometry_delta.shape) == (11,), 'Exact bias-free4096/11 value contract')
    f = head(hidden_forward.float()).reshape(())
    r = head(hidden_reverse.float()).reshape(())
    return .5*(f-r)+torch.dot(beta, geometry_delta.float())


def loss(predicted_gain, target, draw_weight, target_RMS):
    y, weight, rms = number(target), number(draw_weight), number(target_RMS)
    require(-1 <= y <= 1 and weight > 0 and rms > 0, 'Fixed original target/positive weight/RMS required')
    return weight*((predicted_gain-y)/rms).square()


def phase_steps(phase):
    require(phase in ('pilot4', 'remaining496'), 'Only original4 or explicit remaining496')
    return range(1, 5) if phase == 'pilot4' else range(5, 501)
