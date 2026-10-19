"""Independent CPU first QA and fixed utility screen20 comparison.

CLI --root ROOT --stage pilot|final. Adopts successful31/44 input QA; never
loads pixels, runs a processor/model, repeats old raw QA, or fits a control.
Only final reads the explicitly CPU-only screen reference artifact. Pilot is
engineering-only. Successful output directories/acceptances are exclusive.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from numbers import Real
import os
from pathlib import Path
import random
import re
import sys
import traceback

import numpy as np

BASE = 8767123696
LORA_COUNT = 7667712
VALUE_COUNT = 4107
RESIDENT = 8774795515
PIPELINE = 8790229268
ROLE = 'UTILITY_TRAINED_screen'
LORA = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.weight$')
INPUT_KEYS = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
GRAD_GROUPS = {'LoRA_A', 'LoRA_B', 'VALUE_HEAD', 'GEOMETRY_BETA'}
RAW_ATOL = RAW_RTOL = 1e-5
PILOT_GATE = 'PASS_UTILITY_PILOT4_FIRST_ENGINEERING_QA'
FINAL_GATE = 'PASS_UTILITY_FINAL500_SCREEN_FIRST_RAW_QA'
QUALITY_PASS = 'PASS_UTILITY_SCREEN20_ONLY'
QUALITY_STOP = 'STOP_UTILITY_SCREEN20_REJECTED'
RECIPE = dict(updates=500, grad_accum=4, rank=8, alpha=16, dropout=0., lora_lr=5e-5,
    head_lr=.001, geometry_lr=.001, weight_decay=0., grad_clip=1., seed=20261018,
    head_init_std=.001, head_bias=False, geometry_init=0.,
    loss='DRAW_WEIGHT_TIMES_TARGET_RMS_NORMALIZED_SQUARED_GAIN_ERROR', final_only=True)


def require(value, message):
    if not value:
        raise ValueError(message)


def finite(value):
    require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_)) and math.isfinite(value),
            'Explicit finite numeric evidence required')
    return float(value)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def bound(reference):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
        and isinstance(reference['path'], str) and Path(reference['path']).is_absolute()
        and isinstance(reference['sha256'], str) and len(reference['sha256']) == 64,
        'Explicit absolute bound artifact reference required')
    path = Path(reference['path'])
    require(path.is_file() and sha(path) == reference['sha256'], 'Missing/changed bound artifact: '+str(path))
    return path


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha(path))


def read(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream)


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def module(reference, name):
    spec = importlib.util.spec_from_file_location(name, bound(reference))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def lines(reference):
    return [json.loads(line) for line in bound(reference).read_text(encoding='utf-8').splitlines() if line]


def same_state(actual, expected):
    import torch
    return set(actual) == set(expected) and all(isinstance(actual[k], torch.Tensor)
        and actual[k].dtype == v.dtype and actual[k].shape == v.shape
        and torch.equal(actual[k].contiguous().view(torch.uint8), v.contiguous().view(torch.uint8))
        for k, v in expected.items())


def validate_adapter(state):
    import torch
    require(isinstance(state, dict) and len(state) == 288, 'Exactly288 utility LoRA matrices required')
    owners, count = set(), 0
    for key, value in state.items():
        match = LORA.search(key)
        require(match is not None and int(match[1]) in range(36) and isinstance(value, torch.Tensor)
            and value.device.type == 'cpu' and value.ndim == 2 and value.is_floating_point()
            and bool(torch.isfinite(value).all()), 'Finite language-only CPU utility matrix required')
        layer, projection, kind = int(match[1]), match[2], match[3]
        output = 4096 if projection in ('q_proj', 'o_proj') else 1024
        require(tuple(value.shape) == ((8, 4096) if kind == 'A' else (output, 8)), 'Exact q/k/v/o rank8 dimensions required')
        owners.add((layer, projection, kind)); count += value.numel()
    require(len(owners) == 288 and count == LORA_COUNT, 'Actual utility language matrix/count differs')
    return dict(matrices=288, parameters=count)


def validate_value(state):
    import torch
    require(isinstance(state, dict) and set(state) == {'weight', 'geometry_beta'}, 'Complete bias-free value and geometry state required')
    for key, shape in (('weight', (1, 4096)), ('geometry_beta', (11,))):
        value = state[key]
        require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.dtype == torch.float32
            and tuple(value.shape) == shape and bool(torch.isfinite(value).all()), 'Finite actual CPU F32 '+key+' required')
    return state['weight'][0].double().numpy(), state['geometry_beta'].double().numpy()


def validate_rng(state):
    import torch
    rng = state['torch_rng_state']
    require(isinstance(rng, torch.Tensor) and rng.device.type == 'cpu' and rng.dtype == torch.uint8 and rng.ndim == 1,
            'Actual saved CPU torch RNG required')
    torch.Generator(device='cpu').set_state(rng)
    cuda = state['torch_cuda_rng_state_all']
    require(isinstance(cuda, list) and bool(cuda) and all(isinstance(v, torch.Tensor) and v.device.type == 'cpu'
        and v.dtype == torch.uint8 and v.ndim == 1 and v.numel() for v in cuda), 'Saved physical CUDA RNG states required')
    n = state['numpy_rng_state']; keys = n['keys']
    require(isinstance(keys, torch.Tensor) and keys.device.type == 'cpu' and keys.dtype == torch.int64
        and tuple(keys.shape) == (624,) and bool(((keys >= 0) & (keys <= 2**32-1)).all()), 'Actual saved numpy RNG keys required')
    np.random.RandomState().set_state((n['name'], keys.numpy().astype(np.uint32), n['position'], n['has_gauss'], n['cached_gaussian']))
    random.Random().setstate(state['python_rng_state'])
    return len(cuda)


def validate_progress(state, step, schedule_sha, prepared_ref, recipe, target_rms):
    """CPU-loadable complete state, including4107 non-PEFT parameters/Adam."""
    import torch
    require(state['schema'] == 'UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55' and state['step'] == step
        and state['micro'] == step*4 and state['logical_training_forwards'] == step*8
        and state['schedule_sha256'] == schedule_sha and state['train_schedule_reference'] == prepared_ref
        and state['recipe'] == recipe and finite(state['train_target_RMS']) == finite(target_rms) > 0
        and state['original_TIME_loaded'] is False and state['old_PAIR_loaded'] is False
        and state['old_CROP_loaded'] is False and state['no_base_tensors_saved'] is True,
        'Complete exact update/recipe/schedule/RMS progress required')
    inventory = validate_adapter(state['adapter_state_dict'])
    head = state['head_state_dict']
    require(set(head) == {'weight'}, 'Value head has no bias or unregistered parameter')
    validate_value(dict(weight=head['weight'], geometry_beta=state['geometry_beta']))
    groups = state['optimizer_state_dict']['param_groups']; moments = state['optimizer_state_dict']['state']
    require(len(groups) == 3 and groups[0]['lr'] == 5e-5 and len(groups[0]['params']) == 288
        and all(g['lr'] == 1e-3 and len(g['params']) == 1 for g in groups[1:])
        and all(g['weight_decay'] == 0 for g in groups), 'Fixed separate LoRA/value AdamW learning rates required')
    names = state['optimizer_parameter_names_by_group']
    require(isinstance(names, list) and len(names) == 3 and len(names[0]) == 288
        and len(set(names[0])) == 288 and set(names[0]) == set(state['adapter_state_dict'])
        and names[1:] == [['head.weight'], ['geometry_beta']]
        and hashlib.sha256(json.dumps(names, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            == state['optimizer_parameter_names_sha256'], 'Actual exact Adam parameter order/name binding differs')
    ids = [pid for group in groups for pid in group['params']]
    weights = [state['adapter_state_dict'][name] for name in names[0]]+[head['weight'], state['geometry_beta']]
    require(len(ids) == len(set(ids)) == 290 and set(ids) == set(moments), 'Exactly288+2 complete Adam states required')
    for pid, weight in zip(ids, weights):
        moment = moments[pid]
        require(set(moment) == {'step', 'exp_avg', 'exp_avg_sq'} and isinstance(moment['step'], torch.Tensor)
            and moment['step'].numel() == 1 and float(moment['step']) == step, 'Each Adam state must match completed update')
        for key in ('exp_avg', 'exp_avg_sq'):
            value = moment[key]
            require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.shape == weight.shape
                and value.dtype == weight.dtype and bool(torch.isfinite(value).all()), 'Actual finite Adam moments/parameter shape differ')
        require(bool((moment['exp_avg_sq'] >= 0).all()), 'Invalid negative Adam second moments')
    return dict(**inventory, value_parameters=VALUE_COUNT, adam_states=290, step=step, micro=step*4,
        logical_training_forwards=step*8, optimizer_parameter_names_sha256=state['optimizer_parameter_names_sha256'],
        CUDA_RNG_states=validate_rng(state), CPU_rng_valid=True,
        numpy_rng_valid=True, python_rng_valid=True)


def validate_gradient_updates(updates, first, last, final_progress_ref):
    require(len(updates) == last-first+1 and [r['step'] for r in updates] == list(range(first, last+1)),
            'Exactly contiguous persisted utility updates required')
    expected_tensors = dict(LoRA_A=144, LoRA_B=144, VALUE_HEAD=1, GEOMETRY_BETA=1)
    for row in updates:
        require(row['micro'] == 4*row['step'] and set(row['grad_groups']) == GRAD_GROUPS
            and finite(row['combined_preclip_gradient_norm']) > 0, 'Complete grouped utility gradients required')
        for name, group in row['grad_groups'].items():
            require(group['tensors'] == expected_tensors[name] and group['finite'] is True
                and type(group['nonzero_tensors']) is int and 0 <= group['nonzero_tensors'] <= group['tensors']
                and finite(group['preclip_norm']) >= 0, 'Missing/nonfinite utility gradient group')
            if 2 <= row['step'] <= 4 or (row['step'] == 1 and name != 'LoRA_A'):
                require(group['nonzero_tensors'] > 0 and group['preclip_norm'] > 0,
                        'Actual LoRA/value/geometry gradient signal required after allowed initial zero-A')
        require(isinstance(row['progress'], dict), 'Every successful update must bind persisted complete state')
    # Pilot copies complete step4 bytes from mutable progress.pt to immutable
    # pilot_progress.pt. Their SHA must match; their paths intentionally differ.
    require(updates[-1]['progress']['sha256'] == final_progress_ref['sha256'],
            'Last journal must bind actual accepted complete progress bytes')
    return dict(successful_updates=len(updates), first_step=first, last_step=last,
                grouped_gradients_verified=True, initial_zero_LoRA_A_allowed=True)


def validate_inventory(done, cfg):
    inv = done['inventory']; base = done['base_fingerprint']
    expected = dict(base=BASE, utility_lora=LORA_COUNT, value_head=4096, geometry_beta=11,
        trainable=LORA_COUNT+VALUE_COUNT, resident=RESIDENT, pipeline=PIPELINE,
        actual_lora_matrices=288, actual_language_targets=144, adapter='utility',
        original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False,
        original_TIME_counted=15335424, semantic_counted=98329)
    require(all(inv[k] == v for k, v in expected.items()) and base['parameters'] == BASE
        and base['sha256'] == cfg['expected_base_sha256'], 'Actual frozen BASE+UTILITY+value inventory differs')
    return dict(base_fingerprint=base, inventory=inv)


def validate_micro_logs(events, schedule, first, last, target_rms):
    expected = list(range((first-1)*4, last*4))
    require(len(events) == 3*len(expected), 'Exactly begin/loss/backward per dual-order micro required')
    for offset, micro in enumerate(expected):
        begin, loss, backward = events[3*offset:3*offset+3]; row = schedule[micro]
        require([v['event'] for v in (begin, loss, backward)] == ['BEGIN_TRAIN_MICRO', 'TRAIN_RAW_LOSS', 'TRAIN_BACKWARD_COMPLETE']
            and all(v['step'] == micro//4+1 and v['micro'] == micro and v['id'] == row['id'] for v in (begin, loss, backward)),
            'Actual contiguous utility micro journal differs')
        require(loss['source_id'] == begin['source_id'] == row['source_id']
            and loss['forward_id'] == begin['forward_id'] == row['forward']['id']
            and loss['reverse_id'] == begin['reverse_id'] == row['reverse']['id']
            and finite(loss['target']) == finite(row['target'])
            and finite(loss['draw_weight']) == finite(row['draw_weight']) > 0
            and finite(loss['target_RMS']) == finite(target_rms) > 0,
            'Actual signed target/draw/RMS/ordered pair binding differs')
        expected_loss = finite(row['draw_weight'])*((finite(loss['prediction'])-finite(row['target']))/target_rms)**2
        require(math.isclose(finite(loss['loss']), expected_loss, rel_tol=2e-5, abs_tol=2e-6),
                'Saved loss differs from actual weighted target-RMS MSE')
    return dict(successful_micro=len(expected), actual_dual_training_forwards=2*len(expected),
                normalized_weighted_MSE_replayed=True)


def validate_raw(raw, receipt, value_state):
    """Independent CPU64 dot; GPU/CPU reductions use declared1e-5 tolerance."""
    import torch
    require(isinstance(raw, torch.Tensor) and raw.device.type == 'cpu' and raw.dtype == torch.float32
        and tuple(raw.shape) == (4096,) and bool(torch.isfinite(raw).all()), 'Actual finite normalized-last-hidden F32[4096] required')
    weight, _ = validate_value(value_state)
    value = float(np.dot(raw.double().numpy(), weight))
    require(math.isclose(finite(receipt['head_value']), value, abs_tol=RAW_ATOL, rel_tol=RAW_RTOL),
            'Independent CPU dot differs from saved GPU value')
    return dict(hidden4096=raw.double().numpy(), CPU_value=value,
                GPU_value=finite(receipt['head_value']), absolute_error=abs(value-receipt['head_value']))


def alias_key(receipt):
    return json.dumps({k:receipt[k] for k in ('model_role', 'source_id', 'source_sha256', 'class_token_ids', 'input_signature',
        'adapter_weights', 'value_weights')}, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_alias(receipt, reference, previous, seen):
    key = alias_key(receipt)
    require(type(receipt['actual_new_forward']) is bool, 'Explicit actual forward/alias flag required')
    if receipt['actual_new_forward']:
        require(receipt['alias_of'] is None and key not in seen, 'Repeated successful exact utility input is forbidden')
    else:
        first = previous.get(receipt['alias_of']['path'])
        require(first is not None and first['reference'] == receipt['alias_of'] and reference != receipt['alias_of']
            and first['receipt']['actual_new_forward'] is True and alias_key(first['receipt']) == key
            and first['receipt']['raw_hidden'] == receipt['raw_hidden'] and key in seen,
            'Only an earlier exact same-role/source/input/weights raw may be aliased')
    return key


def validate_raw_journal(events, receipts, entries):
    """Verify each actual raw was persisted before its corresponding ACCEPT."""
    offset = 0
    require(len(receipts) == len(entries), 'Complete receipt journal scope required')
    for receipt, entry in zip(receipts, entries):
        count = 3 if receipt['actual_new_forward'] else 1
        block = events[offset:offset+count]; offset += count
        names = ['BEGIN_NEW_ROLE_FORWARD', 'FIRST_RAW_PERSISTED', 'ACCEPTED_NEW_ROLE_RESULT'] if count == 3 else ['ACCEPTED_NEW_ROLE_RESULT']
        require(len(block) == count and [e['event'] for e in block] == names
            and all(e['id'] == receipt['id'] == entry['id'] and e['model_role'] == ROLE for e in block),
            'Exact ordered BEGIN/PERSIST/ACCEPT sequence required')
        if count == 3:
            require(block[0]['input'] == entry['input'] and block[1]['raw_hidden'] == receipt['raw_hidden'],
                    'Actual first raw persistence/input binding differs')
        require(block[-1]['receipt'] == entry['receipt'] and block[-1]['alias'] is (not receipt['actual_new_forward']),
                'Actual ordered receipt acceptance/alias binding differs')
    require(offset == len(events), 'Unexpected extra raw events')


def choose(gains):
    gains = np.asarray(gains, dtype=np.float64)
    require(gains.ndim == 1 and len(gains) > 0 and bool(np.isfinite(gains).all()) and gains[0] == 0.,
            'Complete finite pool gains with exact baseline zero required')
    return max(range(len(gains)), key=lambda i:(float(gains[i]), i == 0, -i))


def evaluate_scope(sources, pair_index, hidden_lookup, target_ious, value_state, old_gain_state, old_geometry_beta, policy):
    """Fixed20 source pool comparison; no fit, softmax, threshold or reranking scan."""
    weight, beta = validate_value(value_state)
    require(len(sources) == len({s['source_id'] for s in sources}) == 20
        and all(s['role'] == 'screen' for s in sources), 'Exact historical screen20 required')
    rms = np.asarray(old_gain_state['RMS'], dtype=np.float64)
    old_beta = np.asarray(old_gain_state['GEOM11_beta'], dtype=np.float64)
    require(rms.shape == (14,) and bool((rms > 0).all()) and bool(np.isfinite(rms).all())
        and old_beta.shape == (11,) and bool(np.isfinite(old_beta).all()), 'Frozen47 geometry state required')
    old_geometry_beta = np.asarray(old_geometry_beta, dtype=np.float64)
    require(old_geometry_beta.shape == (13,) and bool(np.isfinite(old_geometry_beta).all()), 'Frozen33 geometry13 required')
    arms = ('UTILITY', 'UTILITY_BETA_GEOMETRY', 'OLD47_GEOM11', 'OLD33_GEOM13')
    rows = {a:[] for a in arms}; predictions = []; self_zero = 0; used = set()
    for source in sources:
        sid = source['source_id']; pool = source['pool']; vectors = {}; values = {}
        geometry = np.stack([policy.geometry_features(box, source['width'], source['height']) for box in pool])
        delta = (geometry-geometry[0])[:, 1:12]
        for pair in pair_index:
            if pair['source_id'] != sid:
                continue
            index = pair['candidate_index']; f, r = hidden_lookup[pair['first_id']], hidden_lookup[pair['reverse_id']]
            require(type(index) is int and index not in vectors and 0 <= index < len(pool)
                and all(v['source_id'] == sid and v['source_sha256'] == source['source_sha256'] for v in (f, r)),
                'Actual complete ordered utility source/pool binding differs')
            require((index == 0 and pair['same_crop'] is True and pair['first_id'] == pair['reverse_id'])
                or (index > 0 and pair['same_crop'] is False and pair['first_id'] != pair['reverse_id']), 'Exact self/two-order pair required')
            difference = np.asarray(f['hidden4096'], np.float64)-np.asarray(r['hidden4096'], np.float64)
            require(difference.shape == (4096,) and bool(np.isfinite(difference).all()), 'Complete actual last-hidden pair required')
            vectors[index] = difference
            values[index] = .5*(float(np.dot(np.asarray(f['hidden4096'], np.float64), weight))
                                  -float(np.dot(np.asarray(r['hidden4096'], np.float64), weight)))
            used.update((pair['first_id'], pair['reverse_id']))
        require(set(vectors) == set(range(len(pool))), 'Missing pool pair cannot silently abstain')
        hidden_delta = np.stack([vectors[i] for i in range(len(pool))])
        visual = np.array([values[i] for i in range(len(pool))]); geometric = delta@beta
        gains = dict(UTILITY=visual+geometric, UTILITY_BETA_GEOMETRY=geometric,
            OLD47_GEOM11=(delta/rms[3:])@old_beta, OLD33_GEOM13=geometry@old_geometry_beta)
        gains['OLD33_GEOM13'] -= gains['OLD33_GEOM13'][0]
        negative = -visual+(-delta)@beta
        require(np.array_equal(negative, -gains['UTILITY']) and all(v[0] == 0. for v in gains.values()),
                'Actual utility swap must negate and samecrop must be exactly zero')
        self_zero += 1
        choices = {a:choose(gains[a]) for a in arms}
        truth = np.asarray(target_ious[sid], np.float64)
        require(truth.shape == (len(pool),) and bool(np.isfinite(truth).all()) and bool(((truth >= 0) & (truth <= 1)).all()),
                'Complete unchanged original IoUs required')
        for arm in arms:
            index = choices[arm]; gi = choices['OLD33_GEOM13']
            rows[arm].append(dict(source_id=sid, baseline_iou=float(truth[0]), selected_iou=float(truth[index]),
                geometry_iou=float(truth[gi]), oracle_iou=float(truth.max()), baseline_index=0, selected_index=index))
        predictions.append(dict(source_id=sid, source_sha256=source['source_sha256'], choices=choices,
            predicted_gains={a:v.tolist() for a, v in gains.items()}))
    require(used == set(hidden_lookup), 'All exact240 screen ordered hiddens must be consumed')
    summaries = {a:policy.summarize(rows[a]) for a in arms}
    primary = summaries['UTILITY']
    checks = dict(sources=primary['sources'] == 20, minimum_gain=primary['mean_gain'] >= .01,
        improved_sources=primary['improved'] >= 5, worst_loss=primary['worst_loss'] <= .10,
        actual_changed=primary['changed'] > 0, invalid_zero=True, all_self_exact_zero=self_zero == 20)
    for arm in arms[1:]:
        checks['beats_'+arm] = primary['mean_selected_iou'] > summaries[arm]['mean_selected_iou']
    return dict(primary='UTILITY', summaries=summaries, selected=rows, predictions=predictions,
        self_gain_exact_zero=self_zero, invalid_count=0, quality=dict(admitted=all(checks.values()), checks=checks,
            scope='HISTORICAL_STATIC_SCREEN20_NOT_BLIND_OR_OFFICIAL_QUALITY'))


def review_screen(completion_ref, expected, classes, adapter_ref, value_ref, value_state, *, registration_ref):
    """First output QA only; no input tensor/processor or old output QA replay."""
    import torch
    completion_path = bound(completion_ref); completed = read(completion_path)
    by_id = {v['id']:v for v in expected}
    require(len(by_id) == len(expected) == 240
        and completed['status'] == 'COMPLETE_UTILITY_ORDERED_HIDDEN_VALUES_NOT_QUALITY'
        and completed['model_role'] == ROLE and completed['expected_inputs'] == 240
        and completed['adapter_weights'] == adapter_ref and completed['value_weights'] == value_ref
        and completed['GPU_registration'] == registration_ref and completed['screen_reference_read'] is False
        and all(completed[k] is False for k in ('original_TIME_loaded', 'old_PAIR_loaded', 'old_CROP_loaded'))
        and len(completed['entries']) == 240 and {v['id'] for v in completed['entries']} == set(by_id),
        'Complete final240 actual ordered hidden/value inventory required')
    lookup, previous, seen, raw_paths, raw_cache = {}, {}, set(), set(), {}
    predictions, receipts = [], []
    calls = aliases = 0
    maximum_dot_error = 0.
    for item in completed['entries']:
        entry = by_id[item['id']]; request = read(bound(item['input'])); receipt = read(bound(item['receipt']))
        require(item['input'] == entry['input'] == receipt['input'] and request['id'] == item['id'] == receipt['id']
            and item['source_id'] == entry['source_id'] == request['source_id'] == receipt['source_id']
            and item['source_sha256'] == request['source_sha256'] == receipt['source_sha256']
            and receipt['model_role'] == ROLE and receipt['adapter_weights'] == adapter_ref
            and receipt['value_weights'] == value_ref and receipt['screen_reference_read'] is False
            and receipt['raw_dtype'] == 'torch.float32' and receipt['dimension'] == 4096
            and receipt['no_full_vocabulary_logits'] is True
            and all(receipt[k] is False for k in ('original_TIME_loaded', 'old_PAIR_loaded', 'old_CROP_loaded'))
            and request['reference_or_target_in_prompt'] is False,
            'Actual final output request/source/role/weights binding differs')
        require(request['class_token_ids'] == receipt['class_token_ids'] == classes
            and receipt['input_signature'] == request['input_signature'] and set(request['input_signature']) == INPUT_KEYS,
            'Exact adopted actual token/class/four-tensor signature required')
        grid = np.asarray(request['image_grid_thw'])
        require(grid.shape == (3, 3) and grid.dtype.kind in 'iu' and bool((grid > 0).all())
            and bool((grid[:, 0] == 1).all()) and bool((grid[:, 1:] % 2 == 0).all())
            and receipt['image_grid_thw'] == request['image_grid_thw'], 'Actual accepted three-image grid differs')
        expected_grid_sha = hashlib.sha256(grid.astype(np.int64).tobytes(order='C')).hexdigest()
        require(request['input_signature']['image_grid_thw']['sha256'] == expected_grid_sha,
                'New output grid binding does not match adopted actual grid signature')
        key = validate_alias(receipt, item['receipt'], previous, seen)
        raw_ref = receipt['raw_hidden']; raw_key = json.dumps(raw_ref, sort_keys=True)
        if receipt['actual_new_forward']:
            require(raw_ref['path'] not in raw_paths, 'Distinct first raw hidden file per real forward required')
            raw_paths.add(raw_ref['path']); calls += 1
        else:
            aliases += 1
        if raw_key not in raw_cache:
            raw = torch.load(bound(raw_ref), map_location='cpu', weights_only=True)
            raw_cache[raw_key] = validate_raw(raw, receipt, value_state)
        replay = raw_cache[raw_key]
        require(math.isclose(replay['CPU_value'], finite(receipt['head_value']), abs_tol=RAW_ATOL, rel_tol=RAW_RTOL),
                'Alias GPU value differs from independently replayed raw')
        maximum_dot_error = max(maximum_dot_error, abs(replay['CPU_value']-receipt['head_value']))
        lookup[item['id']] = dict(source_id=request['source_id'], source_sha256=request['source_sha256'],
            hidden4096=replay['hidden4096'], CPU_value=replay['CPU_value'])
        predictions.append(dict(id=item['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=item['input'], receipt=item['receipt'], raw_hidden=raw_ref, CPU_value=replay['CPU_value'],
            GPU_value=receipt['head_value'], adapter_weights=adapter_ref, value_weights=value_ref))
        seen.add(key); previous[item['receipt']['path']] = dict(reference=item['receipt'], receipt=receipt)
        receipts.append(receipt)
    require(calls == completed['actual_forward_calls'] and aliases == completed['aliases'] and calls+aliases == 240,
            'Actual utility first forward/alias counts differ')
    require(completed['attempts'] == ref(completion_path.parent/'attempts.jsonl'), 'Exact new screen journal binding required')
    events = lines(completed['attempts'])
    validate_raw_journal(events, receipts, completed['entries'])
    begins = [e for e in events if e['event'] == 'BEGIN_NEW_ROLE_FORWARD']
    persisted = [e for e in events if e['event'] == 'FIRST_RAW_PERSISTED']
    accepted = [e for e in events if e['event'] == 'ACCEPTED_NEW_ROLE_RESULT']
    first = {r['id']:r for r in receipts if r['actual_new_forward']}
    require(len(events) == 2*calls+240 and all(e['model_role'] == ROLE for e in events)
        and len(begins) == len(persisted) == calls and {e['id'] for e in begins} == {e['id'] for e in persisted} == set(first)
        and all(e['raw_hidden'] == first[e['id']]['raw_hidden'] for e in persisted)
        and [e['id'] for e in accepted] == [e['id'] for e in completed['entries']]
        and all(e['receipt'] == row['receipt'] for e, row in zip(accepted, completed['entries'])),
        'Actual BEGIN/PERSIST/ACCEPT raw-first journal differs')
    return lookup, predictions, dict(actual_new_forwards=calls, aliases=aliases, raw_hidden_files=len(raw_cache),
        raw_hidden_dtype='torch.float32', dimension=4096, independent_CPU_dot_dtype='float64',
        GPU_CPU_dot_atol=RAW_ATOL, GPU_CPU_dot_rtol=RAW_RTOL, maximum_absolute_dot_error=maximum_dot_error,
        attempts=ref(completion_path.parent/'attempts.jsonl'), old_input_QA_repeated=False, old_raw_QA_repeated=False)


def run(root, stage):
    import torch
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and stage in ('pilot', 'final'), 'Explicit independent CPU-only review stage required')
    torch.set_num_threads(2)
    root = Path(root).resolve(); regpath = root/'utility_value_GPU_registration_55.json'; reg = read(regpath)
    require(bound(reg['review_code']) == Path(__file__).resolve() and reg['recipe'] == RECIPE,
            'Exact registered utility56 reviewer/fixed recipe required')
    bound(reg['GPU_code']); bound(reg['CPU_registration'])
    gate = read(bound(reg['input_acceptance'])); prepared_ref = gate['prepared']; prepared = read(bound(prepared_ref))
    require(gate['status'] == 'PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU'
        and gate['registration'] == reg['CPU_registration'] and prepared_ref == reg['prepared']
        and prepared['schema'] == 'UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55', 'Adopt complete successful utility input/target compiler')
    math55 = module(reg['math_code'], '_frozen_utility_math55_review56')
    schedule, schedule_sha, schedule_report = math55.validate_schedule(prepared)
    require(math55.RECIPE == RECIPE, 'GPU/compiler/reviewer recipe differs')
    rms = finite(prepared['train_target_RMS']); cfg = read(bound(reg['model_config']))
    modeldir = root/'utility_value_model_55'
    completion_path = modeldir/('pilot_completion.json' if stage == 'pilot' else 'completion.json')
    completion_ref = ref(completion_path); done = read(completion_path)
    out = root/('utility_value_pilot_QA_56' if stage == 'pilot' else 'utility_value_final_QA_56')
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(stage=stage, registration=ref(regpath), new_model_calls=0,
        old_input_QA_repeated=False, old_raw_QA_repeated=False, no_screen_reference_read=stage == 'pilot'))
    try:
        require(done['GPU_registration'] == ref(regpath) and done['recipe'] == RECIPE
            and finite(done['train_target_RMS']) == rms and done['schedule_sha256'] == schedule_sha
            and done['train_schedule_reference'] == prepared_ref, 'Actual complete utility phase/code/schedule/RMS identity differs')
        validate_inventory(done, cfg)
        first, last = (1, 4) if stage == 'pilot' else (5, 500)
        require(done['completed_updates'] == last and done['successful_micro'] == last*4
            and done['actual_training_forwards'] == last*8, 'Actual500/2000/4000 or4/16/32 counts differ')
        prior = admission = None
        if stage == 'pilot':
            require(done['status'] == 'COMPLETE_FIXED4_UTILITY_ENGINEERING_NO_DEV_MODEL'
                and done['remaining_admission'] is None and done['pilot_completion'] is None,
                'Only first4 engineering pilot, with no dev model or quality selection')
            require(bound(done['progress']) == (modeldir/'train/pilot_progress.pt').resolve(), 'Exact immutable original step4 progress required')
            require(all(done[k] is True for k in ('actual_lora_A_changed', 'actual_lora_B_changed', 'head_changed', 'beta_changed')),
                    'Pilot must prove actual LoRA A/B and head/geometry byte updates')
            require(not (modeldir/'TRAINED_screen').exists(), 'Pilot cannot have performed dev model calls')
            require(done['dev_model_forwards'] == 0, 'Explicit zero pilot dev model calls required')
        else:
            admission_path = root/'utility_value_remaining_admission_55.json'; admission = read(admission_path)
            prior = read(bound(admission['pilot_output_acceptance']))
            require(prior['status'] == PILOT_GATE and prior['registration'] == ref(regpath)
                and admission['schema'] == 'UTILITY_CONTINUOUS_REMAINING496_V55'
                and admission['original_GPU_registration'] == ref(regpath)
                and all(admission[k] == reg[k] for k in ('GPU_code', 'math_code', 'prepared', 'input_acceptance'))
                and admission['expected_remaining_updates'] == 496
                and done['remaining_admission'] == ref(admission_path)
                and done['pilot_completion'] == prior['pilot_completion'] == admission['pilot_completion']
                and admission['immutable_pilot_progress'] == prior['engineering']['progress'],
                'Adopt successful first pilot QA and exact immutable step4; never repeat it')
            require(done['status'] == 'COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY'
                and all(done[k] is True for k in ('adapter_reload_all288_exact', 'head_reload_exact', 'beta_reload_exact'))
                and done['base_fingerprint'] == prior['engineering']['base_fingerprint'],
                'Complete fixed-final500 with exact separate adapter/value reload required')
            require(bound(done['progress']) == (modeldir/'train/progress.pt').resolve(), 'Exact final complete update progress required')
        resource_ref = ref(root/('utility_pilot_resource_receipt_56.json' if stage == 'pilot' else 'utility_remaining_resource_receipt_56.json'))
        resource = read(bound(resource_ref))
        require(resource['unique_ledger_entries'] == 1 and resource['record']['status'] == 'completed'
            and resource['record']['exit_code'] == 0, 'Unique naturally completed shared GPU job required')
        state = torch.load(bound(done['progress']), map_location='cpu', weights_only=True)
        engineering = validate_progress(state, last, schedule_sha, prepared_ref, RECIPE, rms)
        if stage == 'pilot':
            initial = torch.load(bound(done['initial_trainables']), map_location='cpu', weights_only=True)
            validate_adapter(initial['adapter_state_dict'])
            validate_value(dict(weight=initial['head_state_dict']['weight'], geometry_beta=initial['geometry_beta']))
            changed = {kind:sum(not same_state({key:value}, {key:initial['adapter_state_dict'][key]})
                for key, value in state['adapter_state_dict'].items() if '.lora_'+kind+'.' in key) for kind in ('A', 'B')}
            require(changed['A'] == done['changed_lora_A_tensors'] > 0
                and changed['B'] == done['changed_lora_B_tensors'] > 0
                and not same_state(state['head_state_dict'], initial['head_state_dict'])
                and not same_state({'beta':state['geometry_beta']}, {'beta':initial['geometry_beta']}),
                'Actual initial-to-step4 LoRA/value/geometry bytes did not update as declared')
            engineering.update(initial_trainables=done['initial_trainables'], changed_lora_tensors=changed)
        else:
            require(done['initial_trainables'] == prior['engineering']['initial_trainables'], 'Original successful pilot initial identity required')
        require(done['optimizer_parameter_names_by_group'] == state['optimizer_parameter_names_by_group']
            and done['optimizer_parameter_names_sha256'] == state['optimizer_parameter_names_sha256'],
            'Completion must bind actual optimizer parameter order')
        updates = lines(done['update_journal'])
        require(Path(updates[-1]['progress']['path']).resolve() == (modeldir/'train/progress.pt').resolve(),
                'Actual update journal must reference its owned mutable progress file')
        engineering['phase_updates'] = validate_gradient_updates(updates, first, last, done['progress'])
        engineering['phase_micros'] = validate_micro_logs(lines(done['micro_journal']), schedule, first, last, rms)
        # The raw graph-gradient journal is retained and bound separately; the
        # persisted update rows above contain the actual group evidence.
        bound(done['gradient_journal'])
        engineering.update(progress=done['progress'], base_fingerprint=done['base_fingerprint'], inventory=done['inventory'],
            prepared=prepared_ref, schedule_sha256=schedule_sha, schedule_report=schedule_report,
            train_target_RMS=rms, resource=resource_ref, gradient_journal=done['gradient_journal'],
            new_model_calls=0, old_input_QA_repeated=False, old_raw_QA_repeated=False)
        require(not torch.cuda.is_initialized(), 'CPU reviewer cannot initialize CUDA')
        if stage == 'pilot':
            save(root/'utility_pilot_output_acceptance_56.json', dict(status=PILOT_GATE, pilot_completion=completion_ref,
                registration=ref(regpath), engineering=engineering, no_eval_reference_read=True, quality_established=False,
                production_admitted=False, automatic_remaining=False, new_model_calls=0))
            return
        from safetensors.torch import load_file
        adapter_path = bound(done['adapter_weights']); value_path = bound(done['value_weights'])
        require(adapter_path == (modeldir/'train/adapter/utility/adapter_model.safetensors').resolve()
            and value_path == (modeldir/'train/value_head.pt').resolve()
            and Path(done['adapter_directory']).resolve() == adapter_path.parent, 'Exact final utility adapter and value artifacts required')
        require(same_state(load_file(str(adapter_path), device='cpu'), state['adapter_state_dict']),
                'Final saved utility adapter differs from complete500 progress')
        value_state = torch.load(value_path, map_location='cpu', weights_only=True)
        validate_value(value_state)
        require(same_state(value_state, dict(weight=state['head_state_dict']['weight'], geometry_beta=state['geometry_beta'])),
                'Final saved value/beta differ from complete500 progress')
        lookup, predictions, raw_engineering = review_screen(done['TRAINED_completion'], prepared['screen_inputs'],
            prepared['class_token_ids'], done['adapter_weights'], done['value_weights'], value_state, registration_ref=ref(regpath))
        engineering.update(raw_engineering, adopted_pilot_acceptance=admission['pilot_output_acceptance'])
        acceptance_path = root/'utility_final_output_acceptance_56.json'
        save(acceptance_path, dict(status=FINAL_GATE, completion=done['TRAINED_completion'], training_completion=completion_ref,
            registration=ref(regpath), remaining_admission=done['remaining_admission'], predictions=predictions,
            engineering=engineering, adapter_weights=done['adapter_weights'], value_weights=done['value_weights'],
            quality_established=False, new_model_calls=0, production_admitted=False))
        # GT first enters this final CPU-only comparison, after first raw QA.
        screen_ref = reg['screen_sources_and_CPU_targets']; screen = read(bound(screen_ref))
        require(screen['status'] == 'ORIGINAL_SCREEN20_CPU_REFERENCE_ONLY_V55' and screen['historical_not_blind'] is True,
                'Explicit historical CPU-only original screen reference artifact required')
        sources = screen['sources']; targets = {}
        for source in sources:
            require(source['baseline_index'] == 0 and source['reference_modified'] is False
                and source['original_BASE_observed'] is True and source['baseline_box'] == source['pool'][0],
                'Actual unchanged native BASE/pool/reference binding required')
            require(source['source_id'] not in targets, 'Duplicate screen reference source')
            targets[source['source_id']] = source['candidate_ious']
        policy = module(reg['policy_code'], '_frozen_policy33_utility56')
        bound(reg['old_gain_math_code'])
        with np.load(bound(reg['old_gain_state']), allow_pickle=False) as loaded:
            old_gain = {k:loaded[k].copy() for k in loaded.files}
        old_geometry = read(bound(reg['old_geometry_control']))
        with np.load(bound(old_geometry['coefficients']), allow_pickle=False) as loaded:
            old_beta = loaded['beta'].copy()
        old_comparison = read(bound(reg['old_crop_comparison']))
        old_acceptance = read(bound(reg['original_screen_output_acceptance']))
        require(old_comparison['geometry_control'] == reg['old_geometry_control']
            and old_comparison['TRAINED_acceptance'] == reg['original_screen_output_acceptance']
            and old_acceptance['status'] == 'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA'
            and {p['id'] for p in old_acceptance['predictions']} == set(lookup),
            'Adopt exact same-scope old33 QA/control; no old raw QA repetition')
        plan = read(bound(reg['case_plan']))
        require(plan['GT_used_for_input_or_pair_choice'] is False, 'Original GT-free case plan required')
        evaluation = evaluate_scope(sources, plan['pair_index'], lookup, targets, value_state, old_gain, old_beta, policy)
        require(math.isclose(evaluation['summaries']['OLD33_GEOM13']['mean_selected_iou'],
            old_comparison['reports']['TRAINED']['summary']['mean_geometry_iou'], rel_tol=0., abs_tol=1e-14),
            'Replayed same20 frozen33 geometry control differs')
        resultdir = root/'utility_value_comparison_56'; resultdir.mkdir(exist_ok=False)
        admitted = evaluation['quality']['admitted']
        save(resultdir/'result.json', dict(status=QUALITY_PASS if admitted else QUALITY_STOP, primary='UTILITY',
            evaluation=evaluation, confirm_admitted=admitted, production_admitted=False, fixed_final_checkpoint=True,
            registration=ref(regpath), remaining_admission=done['remaining_admission'], training_completion=completion_ref,
            screen_output_acceptance=ref(acceptance_path), adapter_weights=done['adapter_weights'], value_weights=done['value_weights'],
            original_geometry_control=reg['old_geometry_control'], old_gain_state=reg['old_gain_state'],
            source_catalog=screen['source_catalog'], CPU_targets=screen_ref, case_plan=reg['case_plan'],
            historical_sources_not_blind=True, original_CROP_CE_and_old47_52_remain_STOP=True,
            official_joint_quality=False, new_model_calls=0, automatic_confirm=False, automatic_production=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True,
            automatic_retry=False, new_model_calls=0, no_failure_to_empty=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--stage', choices=('pilot', 'final'), required=True)
    args = parser.parse_args()
    run(args.root, args.stage)
