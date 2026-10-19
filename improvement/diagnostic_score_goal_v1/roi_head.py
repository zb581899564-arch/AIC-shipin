"""CPU-only fixed ROI-IoU research head and one-sided source calibration.

No backbone, GPU, media, external reference lookup or production launcher.
Targets are original candidate IoUs, not binary ordinary/highlight labels.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping

import numpy as np
import torch
from torch import nn

from crop_geometry import require
from roi_pool import FEATURE_DIM, VISUAL_DIM

ARMS = ('ROI', 'GEOMETRY_CONTROL')
SEED = 20261018
BATCH_SOURCES = 32
UPDATES = 200
HEAD_PARAMETERS = FEATURE_DIM*32+32+32+1
FIXED_TRAIN_SOURCES = 482
FIXED_DEV_SOURCES = 120
STD_MIN = 1e-4


def _features(value):
    require(isinstance(value, np.ndarray) and value.dtype == np.float32 and value.ndim == 2
            and value.shape[0] > 0 and value.shape[1] == FEATURE_DIM and bool(np.isfinite(value).all()),
            'Finite float32[K,12296] CPU features required')
    return value


def _targets(value, count, dtype=np.float32):
    array = np.asarray(value)
    require(array.ndim == 1 and len(array) == count and np.issubdtype(array.dtype, np.floating)
            and bool(np.isfinite(array).all()) and bool(((array >= 0) & (array <= 1)).all()),
            'Complete finite candidate true-IoU targets in[0,1] required')
    return array.astype(dtype, copy=False)


def _source(sources, sid):
    require(sid in sources and isinstance(sources[sid], Mapping), 'Missing complete source: '+str(sid))
    row = sources[sid]; x = _features(row['features']); y = _targets(row['targets'], len(x))
    return x, y


def fit_normalization(sources, train_ids):
    """Population mean/std over train candidate rows only; stable streaming."""
    ids = list(train_ids)
    require(ids and len(ids) == len(set(ids)), 'Distinct nonempty train source IDs required')
    count = 0; mean = np.zeros(FEATURE_DIM, np.float64); m2 = np.zeros(FEATURE_DIM, np.float64)
    for sid in ids:
        # Do not inspect targets or any source outside the declared train IDs.
        x = _features(sources[sid]['features']).astype(np.float64)
        n = len(x); local_mean = x.mean(axis=0, dtype=np.float64)
        centered = x-local_mean; local_m2 = np.sum(centered*centered, axis=0, dtype=np.float64)
        total = count+n; delta = local_mean-mean
        m2 += local_m2+delta*delta*(count*n/total)
        mean += delta*(n/total); count = total
    std = np.maximum(np.sqrt(np.maximum(m2/count, 0.)), STD_MIN)
    norm = dict(mean=mean.astype(np.float32), std=std.astype(np.float32))
    require(all(value.shape == (FEATURE_DIM,) and value.dtype == np.float32 and bool(np.isfinite(value).all())
                for value in norm.values()), 'Finite train-only normalization required')
    return norm


def normalize_features(features, norm, arm):
    x = _features(features)
    require(arm in ARMS and isinstance(norm, Mapping) and set(norm) == {'mean', 'std'}, 'Declared arm and mean/std normalization required')
    mean, std = norm['mean'], norm['std']
    require(all(isinstance(v, np.ndarray) and v.dtype == np.float32 and v.shape == (FEATURE_DIM,)
                and bool(np.isfinite(v).all()) for v in (mean, std)) and bool((std >= np.float32(STD_MIN)).all()),
            'Saved normalization shape/dtype/std mismatch')
    result = ((x-mean)/std).astype(np.float32, copy=True)
    if arm == 'GEOMETRY_CONTROL':
        result[:, :VISUAL_DIM] = 0.  # AFTER normalization, never before it.
    require(bool(np.isfinite(result).all()), 'Normalized feature overflow; no replacement')
    return result


class CandidateIoUHead(nn.Module):
    def __init__(self, arm='ROI'):
        super().__init__()
        require(arm in ARMS, 'Unregistered head arm')
        self.arm = arm
        self.network = nn.Sequential(nn.Linear(FEATURE_DIM, 32), nn.GELU(), nn.Linear(32, 1), nn.Sigmoid())
        require(self.parameter_count == HEAD_PARAMETERS == 393537, 'Actual all-head parameter count differs')

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, features):
        require(isinstance(features, torch.Tensor) and features.device.type == 'cpu' and features.dtype == torch.float32
                and features.ndim == 2 and features.shape[0] > 0 and features.shape[1] == FEATURE_DIM
                and not features.requires_grad and bool(torch.isfinite(features).all())
                and all(p.device.type == 'cpu' for p in self.parameters()), 'Detached finite CPU float32 candidate features required')
        output = self.network(features).squeeze(-1)
        require(bool(torch.isfinite(output).all()), 'Nonfinite small-head score')
        return output


def source_mean_mse(prediction, targets, source_sizes, source_weights=None):
    """Each source first averages its candidates; then average source draws."""
    require(isinstance(prediction, torch.Tensor) and isinstance(targets, torch.Tensor)
            and prediction.device.type == targets.device.type == 'cpu'
            and prediction.dtype == targets.dtype == torch.float32
            and bool(torch.isfinite(prediction).all()) and bool(torch.isfinite(targets).all())
            and prediction.ndim == targets.ndim == 1 and prediction.shape == targets.shape
            and all(type(n) is int and n > 0 for n in source_sizes) and sum(source_sizes) == len(prediction),
            'Complete candidate/source loss denominator required')
    losses = []; start = 0
    for count in source_sizes:
        losses.append((prediction[start:start+count]-targets[start:start+count]).square().mean())
        start += count
    means = torch.stack(losses)
    if source_weights is None:
        return means.mean()
    require(source_weights.device.type == 'cpu' and source_weights.shape == means.shape
            and bool(torch.isfinite(source_weights).all()) and bool((source_weights >= 0).all())
            and abs(float(source_weights.sum())-1.) < 1e-6, 'Complete normalized source-draw weights required')
    return (means*source_weights).sum()


def batch_sequence(train_ids, updates=UPDATES):
    ids = list(train_ids)
    require(ids and len(ids) == len(set(ids)) and type(updates) is int and updates in (1, UPDATES),
            'Fixed200 updates or explicit one-update synthetic check only')
    matrix = np.random.default_rng(SEED).integers(0, len(ids), size=(updates, BATCH_SOURCES), dtype=np.int64)
    payload = json.dumps(dict(ids=ids, indices=matrix.tolist()), separators=(',', ':'), ensure_ascii=True).encode()
    return matrix, hashlib.sha256(payload).hexdigest()


def fit(sources, train_ids, arm='ROI', updates=UPDATES):
    """Return(model, {'mean','std'}, report), with the single fixed recipe.

    sources[id]={'features':float32[K,12296], 'targets':float[K]}. Candidate0
    must be the original frame's baseline. Only train IDs are read. updates=1
    is solely for a tiny synthetic interface/gradient check, never admission.
    """
    ids = list(train_ids)
    require(arm in ARMS and ids and all(isinstance(sid, str) for sid in ids) and len(set(ids)) == len(ids),
            'Declared arm and complete unique source IDs required')
    require(type(updates) is int and updates in (1, UPDATES), 'No optimizer-budget search allowed')
    require(updates == 1 or len(ids) == FIXED_TRAIN_SOURCES, 'Real fixed recipe requires exactly482 train sources')
    raw = {sid: _source(sources, sid) for sid in ids}
    norm = fit_normalization(sources, ids)
    xs = {sid: torch.from_numpy(normalize_features(raw[sid][0], norm, arm)) for sid in ids}
    ys = {sid: torch.from_numpy(np.array(raw[sid][1], dtype=np.float32, copy=True)) for sid in ids}
    batches, batch_sha = batch_sequence(ids, updates)
    losses, gradients = [], []
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(SEED)
        model = CandidateIoUHead(arm).cpu()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        model.train()
        for batch in batches:
            # Group repeated draws without changing their source-average weight.
            unique, multiplicity = np.unique(batch, return_counts=True)
            selected = [ids[int(i)] for i in unique]
            feature = torch.cat([xs[sid] for sid in selected])
            target = torch.cat([ys[sid] for sid in selected])
            weights = torch.from_numpy((multiplicity/BATCH_SOURCES).astype(np.float32))
            optimizer.zero_grad(set_to_none=True)
            loss = source_mean_mse(model(feature), target, [len(ys[sid]) for sid in selected], weights)
            require(bool(torch.isfinite(loss)), 'Nonfinite source-balanced training loss')
            loss.backward()
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            require(bool(torch.isfinite(grad)), 'Nonfinite head gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(p).all()) for p in model.parameters()), 'Nonfinite final-only head state')
            losses.append(float(loss.detach())); gradients.append(float(grad))
    model.eval()
    norm_sha = hashlib.sha256(norm['mean'].tobytes()+norm['std'].tobytes()).hexdigest()
    report = dict(schema='FIXED_ROI_CANDIDATE_IOU_HEAD_V1', arm=arm, seed=SEED, updates=updates,
        synthetic_interface_check_only=(updates == 1), training_source_ids=ids, training_sources=len(ids),
        normalization='Population candidate-row mean/std over train IDs only; std>=1e-4',
        normalization_sha256=norm_sha, normalization_candidate_rows=sum(len(raw[sid][0]) for sid in ids),
        source_balanced_batch_size=BATCH_SOURCES, sampling='Source draws uniformly with replacement; repeated draws retain multiplicity',
        batch_sequence_sha256=batch_sha, loss='Per-source mean candidate true-IoU MSE, then mean sampled source draws',
        optimizer='AdamW', learning_rate=1e-3, weight_decay=1e-4, gradient_clip=1.,
        checkpoint='final_update_only', loss_history=losses, gradient_norm_history=gradients,
        hidden_dim=32, feature_dimension=FEATURE_DIM, visual_channels=VISUAL_DIM,
        geometry_control_visual_zero_after_normalization=(arm == 'GEOMETRY_CONTROL'),
        head_parameters=model.parameter_count, frozen_backbone_updates=0, new_backbone_calls=0,
        budget_if_original_base_TIME_and_protected_semantic_head_resident=8782459120+98329+model.parameter_count,
        parameter_budget_basis='Arithmetic budget assumption, not a new physical-backbone inventory',
        scope='Historically exposed static16:9 research; source/video exchangeability unproved; no screen20 read',
        training_or_production_admission=False, scientific_or_official_quality_claim=False)
    return model, norm, report


def predict_scores(model, norm, features, arm=None):
    require(isinstance(model, CandidateIoUHead), 'Exact fixed head class required')
    use_arm = model.arm if arm is None else arm
    require(use_arm == model.arm, 'Prediction arm differs from fitted head arm')
    x = torch.from_numpy(normalize_features(features, norm, use_arm))
    model.eval()
    with torch.inference_mode():
        result = model(x).detach().cpu().numpy().astype(np.float32)
    require(result.shape == (len(features),) and bool(np.isfinite(result).all()), 'Complete finite candidate scores required')
    return result


def _scores(value):
    array = np.asarray(value, dtype=np.float64)
    require(array.ndim == 1 and len(array) > 0 and bool(np.isfinite(array).all())
            and bool(((array >= 0) & (array <= 1)).all()), 'Complete finite sigmoid candidate scores in[0,1] required')
    return array


def calibrate_margin(dev_scores, dev_targets):
    """Fixed alpha=.1, one optimism maximum per source, rank109 of120.

    Includes candidate0, so each source error is at least0. This is a static
    research margin rule, NOT a guarantee of exchangeability with videos.
    """
    require(isinstance(dev_scores, Mapping) and isinstance(dev_targets, Mapping)
            and set(dev_scores) == set(dev_targets) and len(dev_scores) == FIXED_DEV_SOURCES,
            'Exactly120 complete source-disjoint dev score/target records required')
    errors = []
    for sid in sorted(dev_scores):
        score = _scores(dev_scores[sid]); true = _targets(dev_targets[sid], len(score), dtype=np.float64)
        optimism = float(np.max((score-score[0])-(true-true[0])))
        require(np.isfinite(optimism) and optimism >= 0., 'Invalid one-sided source optimism')
        errors.append(dict(source_id=sid, optimism_error=optimism, candidates=len(score)))
    count = len(errors); rank = (9*(count+1)+9)//10  # exact ceil((n+1)*.9)
    require(1 <= rank <= count, 'Requested finite-sample order statistic unavailable; no clamping/fallback')
    threshold = max(0., sorted(row['optimism_error'] for row in errors)[rank-1])
    return dict(schema='FIXED_SOURCE_MAX_MARGIN_CALIBRATION_V1', alpha=.1, sources=count,
        order_statistic_rank_one_based=rank, quantile_interpolation='NONE_NEAREST_ORDER', threshold=threshold,
        errors=errors, source_statistic='max_j[(score_j-score0)-(trueIoU_j-trueIoU0)] includingj0',
        action='Change only if best_score-score0 strictly exceeds threshold; equality keepsbaseline',
        scope='Historically exposed static source calibration; video exchangeability and joint quality UNKNOWN',
        train_dev_source_disjointness_must_be_bound_by_caller=True,
        screen20_read=False, alpha_or_threshold_tuning_allowed=False, production_admitted=False)


def select_candidate(scores, threshold):
    score = _scores(scores)
    require(type(threshold) in (int, float) and math.isfinite(threshold) and threshold >= 0,
            'Frozen finite nonnegative calibration threshold required')
    best = int(np.argmax(score))  # first index wins a score tie, baseline is0
    return best if float(score[best]-score[0]) > threshold else 0
