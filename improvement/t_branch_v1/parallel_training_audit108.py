"""Independent source coverage, loss, accumulated-gradient and Adam-state review."""
from fractions import Fraction
import hashlib
import json
import math

import numpy as np
import torch

from native_training_data99 import coefficients
from summary_train88_cpu import first_AdamW
from t_io import ROOT, check, identity, read


def state_digest(state, base):
    digest = hashlib.sha256(json.dumps(base, sort_keys=True).encode())
    for name, value in sorted(state.items()):
        value = value.detach().contiguous().cpu()
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def gradient(ref, cursor, checkpoint):
    packet = torch.load(check(ref['file']), map_location='cpu', weights_only=True)
    items = packet['gradients']
    if packet['cursor'] != cursor or packet['publisher_checkpoint'] != checkpoint:
        raise ValueError('A saved successful query gradient has a different recovery cursor')
    if len(items) != 288 or sum(v.numel() for v in items.values()) != 15335424 or any(
            ('.lora_A.actor.' not in name and '.lora_B.actor.' not in name)
            or value.dtype != torch.float32 or not torch.isfinite(value).all()
            for name, value in items.items()):
        raise ValueError('Actual query gradient is nonfinite or affects a protected parameter')
    norm = math.sqrt(math.fsum(float(value.double().square().sum()) for value in items.values()))
    if not math.isclose(norm, ref['norm_float64'], abs_tol=1e-7, rel_tol=1e-7):
        raise ValueError('Independent query cumulative gradient norm differs')
    return norm


def teacher(row, task, weight, model_state):
    raw = row['actual_teacher']
    selection = read(check(read(check(row['actual_selection']))['raw']))
    if (raw['target_binding'] != task or raw['publisher_source_weight'] != weight
            or raw['actual_model_state'] != model_state
            or selection['actual_model_state'] != model_state
            or raw['actual_selection'] != row['actual_selection']
            or raw['binary_logits'] != selection['binary_logits']):
        raise ValueError('Actual source-global query loss belongs to a different case/state')
    z = np.asarray(raw['binary_logits'], dtype=np.float64)
    logp = z - z.max(axis=1, keepdims=True)
    logp -= np.log(np.exp(logp).sum(axis=1, keepdims=True))
    a, b, scalar = coefficients(task, weight)
    expected = -float(np.sum(a * logp[:, 0] + b * logp[:, 1])) * scalar
    if (z.shape != (32, 2) or not np.isfinite(z).all()
            or not np.allclose(logp, raw['binary_logp'], atol=2e-5, rtol=2e-5)
            or not math.isclose(expected, raw['weighted_preference_loss'], abs_tol=2e-6, rel_tol=3e-5)):
        raise ValueError('Independent exact-source binary query preference loss differs')
    return expected


def training(result, data):
    first_gpu = identity(ROOT / 'parallel_cost107/GPU_completion.json')
    first_cpu = identity(ROOT / 'parallel_cost107/CPU_completion.json')
    first = read(check(first_gpu))['first_micro']
    base = result['actual_loaded']['base']
    last_state, previous_checkpoint = first['actual_actor_state'], first['initial_actor_optimizer']
    observed, proofs, first_update = [], [], None
    for episode, ref in enumerate(result['training']['publisher_updates'], 1):
        update = read(check(ref))
        publisher = data['schedule'][episode - 1]
        expected = [(sid, case) for sid in data['publishers'][publisher]
                    for case in data['sources'][sid]['cases']]
        if (update['episode'] != episode or update['publisher'] != publisher
                or update['before'] != last_state or update['after'] == last_state
                or update['actual_optimizer_updates'] != 1
                or len(update['all_prescribed_micro']) != len(expected)):
            raise ValueError('Actual fixed publisher update/order or complete window denominator differs')
        mass = 0.
        for ref_micro, (sid, task) in zip(update['all_prescribed_micro'], expected):
            row = read(check(ref_micro))
            cursor = row['cursor']
            observed.append((publisher, sid, task['case']))
            if (cursor != dict(publisher=publisher, source=sid, case=task['case'],
                    completed_micro=len(observed), optimizer_updates=episode - 1)):
                raise ValueError('Actual query training micro sequence is incomplete or reordered')
            weight = data['sources'][sid]['publisher_source_weight']
            mass += (task['positive_mass'] + task['negative_mass']) * float(Fraction(weight))
            if len(observed) == 1:
                if (row['adopted_actual_GPU'] != first_gpu or row['adopted_first_CPU'] != first_cpu
                        or row['target_binding'] != first['target_binding']
                        or row['exact_recovery_gradient'] != first['exact_successful_gradient']):
                    raise ValueError('Claimed first successful query micro was not exactly adopted')
                proofs.append(dict(cursor=cursor, first_CPU_adopted=True))
                continue
            loss = teacher(row, task, weight, update['before'])
            norm = gradient(row['exact_recovery_gradient'], cursor, previous_checkpoint)
            proofs.append(dict(cursor=cursor, actual_teacher_loss_FP64=loss,
                               actual_accumulated_gradient_norm_FP64=norm, micro=ref_micro))
        if not math.isclose(mass, 1., abs_tol=1e-12, rel_tol=0):
            raise ValueError('Actual complete publisher/source loss mass differs')
        checkpoint = torch.load(check(update['checkpoint']), map_location='cpu', weights_only=True)
        if (checkpoint['completed_episode'] != episode
                or state_digest(checkpoint['actor'], base) != update['after']
                or len(checkpoint['optimizer']['state']) != 288
                or any(float(value['step']) != episode for value in checkpoint['optimizer']['state'].values())):
            raise ValueError('Actual publisher actor/Adam state does not prove its update count')
        if episode == 1:
            first_update = first_AdamW(update['first_optimizer_witness'])
        last_state, previous_checkpoint = update['after'], update['checkpoint']
    expected_all = [(publisher, sid, case['case']) for publisher in data['schedule']
                    for sid in data['publishers'][publisher] for case in data['sources'][sid]['cases']]
    if observed != expected_all or len(observed) != 217 or len(proofs) != 217:
        raise ValueError('All217 original windows were not used exactly once')
    return dict(whole_training_windows=217, adopted_first_micro=1, newly_reviewed_micro=216,
        all_original_reviewers=86, actual_optimizer_updates=5, first_AdamW_FP64=first_update,
        micro=proofs, actual_final_actor_state=last_state)
