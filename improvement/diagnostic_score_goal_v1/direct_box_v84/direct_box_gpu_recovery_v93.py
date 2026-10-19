"""Independent L2-hidden numerical recovery; no actions on import.

CLI --root ROOT --phase pilot4|remaining794. Only training targets are opened.
Exactly adopt failed84's successful step1 trainables/RNG, reset Adam, skip all
eight already executed inputs, and use head(F32 hidden / its L2 norm).
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback

_here = Path(__file__).resolve()
for _support in (_here.parents[1]/'pair_code_17', _here.parents[1], _here.parents[2]/'pair_code_17'):
    if (_support/'pair_common.py').is_file():
        sys.path.insert(0, str(_support)); break
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature, paths, append_event

BASE = 8767123696
LORA = 7667712
HEAD = 12291
PHYSICAL = 8774803699
PIPELINE = 8790237452
ADAPTER = 'direct_box'
ROLE = 'DIRECT_BOX93_TRAINED_screen'
SCHEMA = 'FROZEN_SOURCE_ONLY_DIRECT_BOX_L2_RECOVERY_GPU_V93'
REMAINING_SCHEMA = 'DIRECT_BOX_REMAINING794_V93'
PROGRESS_SCHEMA = 'DIRECT_BOX_L2_RECOVERY_COMPLETE_UPDATE_PROGRESS_V93'
PILOT_STATUS = 'COMPLETE_DIRECT_BOX93_NEW4_ENGINEERING_NO_DEV_MODEL'
FINAL_STATUS = 'COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY'
SCREEN_STATUS = 'COMPLETE_DIRECT_BOX93_NATIVE20_RAW_NOT_QUALITY'
INPUT_GATE = 'PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA'
TARGET = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$')
TRAINABLE = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.direct_box\.weight$')
GPU_REFS = ('GPU_code', 'math_code', 'preparation_code', 'CPU_registration', 'prepared', 'input_acceptance', 'train_targets',
    'original_GPU32', 'original_GPU18', 'model_config', 'old_TIME', 'old_PAIR', 'old_CROP', 'protocol', 'frozen_GPU84_code', 'frozen_GPU84_registration', 'frozen_math84_code', 'original84_progress', 'original84_failure', 'hard_clamp_diagnosis', 'recovery_prepared')
RNG_KEYS = ('torch_rng_state', 'torch_cuda_rng_state_all', 'numpy_rng_state', 'python_rng_state')


def module(reference, name):
    path = bound(reference)
    require(name not in sys.modules, 'One pinned module identity per process')
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def digest(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def phase_steps(phase):
    require(phase in ('pilot4', 'remaining794'), 'Only explicitly registered4 or remaining794')
    return range(1, 5) if phase == 'pilot4' else range(5, 799)


def _registration(root, phase):
    path = root/'direct_box_GPU_registration_93.json'; reg = read(path)
    require(reg['schema'] == SCHEMA, 'Explicit fresh direct-box84 registration')
    for key in GPU_REFS:
        bound(reg[key])  # Whitelist deliberately excludes screen_CPU_targets.
    require(bound(reg['GPU_code']) == Path(__file__).resolve()
        and bound(reg['CPU_registration']).parent == root.resolve()
        and bound(reg['prepared']) == (root/'direct_box_inputs_84/prepared.json').resolve()
        and bound(reg['input_acceptance']) == (root/'direct_box_inputs_84/input_acceptance.json').resolve(), 'Exact84 code/input namespace')
    math84 = module(reg['math_code'], '_direct_box93_math')
    require(reg['recipe'] == math84.RECIPE, 'One fixed L2 numerical recovery recipe')
    original = read(bound(reg['frozen_GPU84_registration']))
    require(original['GPU_code'] == reg['frozen_GPU84_code']
        and original['math_code'] == reg['frozen_math84_code']
        and Path(math84.frozen84.__file__).resolve() == bound(reg['frozen_math84_code'])
        and all(original[k] == reg[k] for k in ('prepared', 'input_acceptance', 'CPU_registration',
            'preparation_code', 'train_targets', 'model_config', 'original_GPU32', 'original_GPU18',
            'old_TIME', 'old_PAIR', 'old_CROP')), 'Exact84 ancestry and unchanged successful622 input cache')
    failure = read(bound(reg['original84_failure']))
    require(failure['completed_updates'] == 1 and failure['successful_micro'] == 8
        and failure['actual_training_forwards'] == 8 and failure['last_progress'] == reg['original84_progress'],
        'Adopt precisely one successful update; all eight original forwards stay consumed')
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == INPUT_GATE and gate['prepared'] == reg['prepared']
        and gate['registration'] == reg['CPU_registration'], 'Actual source-only622 first input QA required')
    old32 = read(bound(reg['original_GPU32'])); old18 = read(bound(reg['original_GPU18']))
    require(reg['model_config'] == old32['model_config'] and reg['old_TIME'] == old32['old_TIME']
        and reg['old_PAIR'] == old32['old_PAIR'] and old32['original_GPU18'] == reg['original_GPU18'], 'Pinned original physical BASE/runtime identity')
    for item in old18['runtime_dependencies']:
        bound(item)
    old17 = read(bound(old18['pair_registration']))
    for name, expected in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == expected, 'Frozen runtime helper changed: '+name)
    frozen = module(old32['GPU_code'], '_direct_box93_frozen_io32')
    admission, admission_ref = reg, ref(path)
    if phase == 'remaining794':
        remaining_path = root/'direct_box_remaining_admission_93.json'; admission = read(remaining_path); admission_ref = ref(remaining_path)
        require(admission['schema'] == REMAINING_SCHEMA and admission['original_GPU_registration'] == ref(path)
            and all(admission[k] == reg[k] for k in ('GPU_code', 'math_code', 'prepared', 'input_acceptance'))
            and admission['expected_remaining_updates'] == 794, 'Explicit unchanged remaining794 admission')
        accepted = read(bound(admission['pilot_output_acceptance']))
        require(accepted['status'] == 'PASS_DIRECT_BOX93_PILOT4_FIRST_ENGINEERING_QA'
            and accepted['registration'] == ref(path) and accepted['pilot_completion'] == admission['pilot_completion']
            and accepted['engineering']['progress'] == admission['immutable_pilot_progress']
            and accepted['engineering']['global_updates'] == 4, 'Independent accepted4-update pilot before any remaining GPU')
    frozen._deadline(admission)
    return reg, admission, admission_ref, math84, frozen


def validate_original_schedule(prepared):
    require(prepared['schema'] == 'DIRECT_BOX_SOURCE_ONLY_INPUTS_V84', 'New source-only84 prepared schema')
    entries = prepared['train_inputs']; screen = prepared['screen_inputs']; rows = prepared['train_schedule']
    require(len(entries) == len({e['id'] for e in entries}) == len({e['source_id'] for e in entries})
        == len({e['source_sha256'] for e in entries}) == 602 and all(e['role'] == 'train' for e in entries), 'Exact602 unique train source inputs')
    byid = {e['id']:e for e in entries}
    require(len(screen) == len({e['id'] for e in screen}) == len({e['source_id'] for e in screen})
        == len({e['source_sha256'] for e in screen}) == 20 and all(e['role'] == 'screen' for e in screen), 'Exact20 unique historical screen inputs')
    require(not {e['source_sha256'] for e in screen}&{e['source_sha256'] for e in entries}, 'No screen image in training')
    require(len(rows) == len({r['id'] for r in rows}) == 3200, 'Fixed3200 schedule IDs')
    counts = Counter(row['source_id'] for row in rows)
    require(set(counts) == {e['source_id'] for e in entries} and Counter(counts.values()) == {5:412, 6:190}, '602 five visits and190 fixed extra visits')
    for row in rows:
        entry = byid[row['input_id']]
        require(row['source_id'] == entry['source_id'] and row['source_sha256'] == entry['source_sha256']
            and row['input'] == entry['input'] and row['draw_weight'] == 3200/(602*counts[row['source_id']]), 'Exact source-equal draw/physical input binding')
    schedule_sha = digest(rows)
    require(prepared['schedule_sha256'] == schedule_sha, 'Frozen source draw order SHA')
    return rows, byid, schedule_sha, dict(sources=602, micro=3200, draws_per_source_histogram=dict(Counter(counts.values())), source_equal_empirical_objective=True)


def validate_schedule(prepared, recovery, original_reference):
    old, byid, original_sha, _ = validate_original_schedule(prepared)
    require(recovery['schema'] == 'DIRECT_BOX_L2_RECOVERY_SCHEDULE_V93'
        and recovery['original_prepared'] == original_reference
        and recovery['original_schedule_sha256'] == original_sha
        and recovery['skipped_original_micro_indices'] == list(range(8)), 'Exact original eight successful inputs excluded')
    rows = recovery['train_schedule']; counts = Counter(r['source_id'] for r in old[8:])
    expected = [dict(row, draw_weight=3192/(602*counts[row['source_id']]), original_micro=i+8)
        for i, row in enumerate(old[8:])]
    require(rows == expected and len(rows) == 3192 and len(counts) == 602,
        'Only unchanged original schedule8..3199, with source-equal remaining draw weights')
    schedule_sha = digest(rows)
    require(recovery['schedule_sha256'] == schedule_sha, 'Frozen independent recovery schedule SHA')
    return rows, byid, schedule_sha, dict(sources=602, micro=3192,
        draws_per_source_histogram=dict(Counter(counts.values())), source_equal_empirical_objective=True,
        original_micro_start=8, original_micro_stop_exclusive=3200, original_successful_forwards_skipped=8)


def _input(reader, entry, torch):
    values, request = reader.get(entry['input'])
    require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
        and request['source_sha256'] == entry['source_sha256'] and request['role'] == entry['role']
        and request['reference_or_target_in_prompt'] is False, 'Actual source-only prefix/owner/role binding')
    require(not any(k in request for k in ('target', 'labels', 'candidate_ious', 'original_reference_xywh', 'reference_xywh')),
        'Human targets cannot be present in model input metadata')
    require(set(values) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
        and signature(values) == request['input_signature'], 'Exact first-QA source-only four tensors')
    ids, mask, pixels, grid = (values[k] for k in ('input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'))
    require(all(v.device.type == 'cpu' and not v.requires_grad for v in values.values())
        and ids.dtype == mask.dtype == torch.int64 and ids.shape == mask.shape and ids.ndim == 2 and ids.shape[0] == 1
        and 0 < ids.shape[1] <= 4096 and bool((mask == 1).all()), 'One complete unpadded CPU source prefix')
    require(grid.dtype == torch.int64 and tuple(grid.shape) == (1, 3) and bool((grid > 0).all())
        and int(grid[0, 0]) == 1 and bool((grid[:, 1:] % 2 == 0).all()) and grid.tolist() == request['image_grid_thw']
        and pixels.dtype == torch.float32 and tuple(pixels.shape) == (int(grid.prod()), 1536)
        and bool(torch.isfinite(pixels).all()), 'Exactly one accepted static source image')
    require(type(request['width']) is int and type(request['height']) is int and min(request['width'], request['height']) > 0, 'Original native dimensions')
    return values, request


def _adapter_state(model, torch, frozen):
    from peft import get_peft_model_state_dict
    state = frozen._cpu_tree(get_peft_model_state_dict(model, adapter_name=ADAPTER), torch)
    require(len(state) == 288 and all('lora_' in name for name in state), 'Only new direct_box288 PEFT matrices')
    return state


def _inventory(model, head, training, torch):
    parameters = []; base_count = lora_count = 0
    for name, value in model.named_parameters():
        if 'lora_' in name:
            match = TRAINABLE.search(name)
            require(match is not None and value.ndim == 2 and (value.shape[0] if match[3] == 'A' else value.shape[1]) == 8
                and value.requires_grad == training, 'Only new direct_box language matrices trainable: '+name)
            parameters.append((name, value)); lora_count += value.numel()
        else:
            require(not value.requires_grad, 'BASE/vision/embed/LM-head must remain frozen')
            base_count += value.numel()
    layers = [m for m in model.modules() if hasattr(m, 'lora_A')]
    require(base_count == BASE and lora_count == LORA and len(parameters) == 288 and len(layers) == 144
        and model.active_adapter == ADAPTER and all(set(m.lora_A) == {ADAPTER} and not m.disable_adapters
            and list(m.active_adapters) == [ADAPTER] for m in layers), 'One active fresh direct_box adapter only')
    require(tuple(head.weight.shape) == (3, 4096) and tuple(head.bias.shape) == (3,)
        and all(p.dtype == torch.float32 and p.requires_grad == training for p in head.parameters()), 'Exact F32 biased3 value head')
    return parameters, dict(base=base_count, direct_box_lora=lora_count, head=HEAD, trainable=LORA+HEAD,
        resident=PHYSICAL, pipeline=PIPELINE, actual_lora_matrices=288, actual_language_targets=144,
        head_tensors=2, adapter=ADAPTER, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False,
        old_UTILITY_loaded=False, original_TIME_counted=15335424, semantic_counted=98329)


def _names(parameters):
    return [[name.replace('.direct_box.', '.') for name, _ in parameters], ['head.weight', 'head.bias']]


def _trainables(model, head, torch, frozen):
    return dict(adapter_state_dict=_adapter_state(model, torch, frozen), head_state_dict=frozen._cpu_tree(head.state_dict(), torch))


def _tree_equal(a, b, torch):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(
            a.cpu().contiguous().reshape(-1).view(torch.uint8), b.cpu().contiguous().reshape(-1).view(torch.uint8))
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(_tree_equal(a[k], b[k], torch) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(_tree_equal(x, y, torch) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def validate_warmstart(warm, original_reg, prepared, names, torch):
    require(warm['schema'] == 'DIRECT_BOX_COMPLETE_UPDATE_PROGRESS_V84'
        and warm['step'] == 1 and warm['micro'] == warm['logical_training_forwards'] == 4
        and warm['schedule_sha256'] == prepared['schedule_sha256']
        and warm['train_schedule_reference'] == original_reg['prepared']
        and warm['train_targets_reference'] == original_reg['train_targets']
        and warm['recipe'] == original_reg['recipe'] and warm['optimizer_parameter_names_by_group'] == names
        and warm['optimizer_parameter_names_sha256'] == digest(names), 'Only original84 committed step1 checkpoint is adoptable')
    state = warm['adapter_state_dict']; head = warm['head_state_dict']
    require(len(state) == 288 and len([k for k in state if '.lora_B.' in k]) == 144
        and all(bool(torch.isfinite(v).all()) for v in state.values())
        and all(not bool(torch.count_nonzero(v)) for k, v in state.items() if '.lora_B.' in k),
        'Original84 successful step1 leaves precisely all144 B matrices zero')
    require(set(head) == {'weight', 'bias'} and tuple(head['weight'].shape) == (3, 4096)
        and tuple(head['bias'].shape) == (3,)
        and all(v.dtype == torch.float32 and bool(torch.isfinite(v).all()) and bool(torch.count_nonzero(v)) for v in head.values()),
        'Original84 finite nonzero F32 head weight and bias adopted exactly')
    require(len(warm['optimizer_state_dict']['state']) == 290
        and [len(g['params']) for g in warm['optimizer_state_dict']['param_groups']] == [288, 2]
        and all(float(v['step']) == 1. for v in warm['optimizer_state_dict']['state'].values()),
        'Original84 successful update has all290 step1 Adam states; they are not reused')
    require(all(key in warm for key in RNG_KEYS), 'All original84 step1 RNG states are required')


def _progress(model, head, optimizer, torch, np, frozen, step, schedule_sha, reg, names):
    state = _trainables(model, head, torch, frozen); n = np.random.get_state()
    state.update(schema=PROGRESS_SCHEMA, optimizer_state_dict=frozen._cpu_tree(optimizer.state_dict(), torch),
        optimizer_parameter_names_by_group=names, optimizer_parameter_names_sha256=digest(names),
        torch_rng_state=torch.get_rng_state(), torch_cuda_rng_state_all=[v.cpu() for v in torch.cuda.get_rng_state_all()],
        numpy_rng_state=dict(name=n[0], keys=torch.tensor(n[1].astype(np.int64)), position=int(n[2]), has_gauss=int(n[3]), cached_gaussian=float(n[4])),
        python_rng_state=random.getstate(), step=step, micro=step*4, logical_training_forwards=step*4,
        schedule_sha256=schedule_sha, train_schedule_reference=reg['recovery_prepared'], train_targets_reference=reg['train_targets'], recipe=reg['recipe'],
        original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, old_UTILITY_loaded=False, no_base_tensors_saved=True,
        original84_progress=reg['original84_progress'], original_successful_updates=1, original_successful_forwards=8,
        optimizer_reset=True, hidden_transform=reg['recipe']['hidden_transform'])
    return state


def _gradient_groups(parameters, head, torch):
    grouped = dict(LoRA_A=[p for name, p in parameters if '.lora_A.' in name], LoRA_B=[p for name, p in parameters if '.lora_B.' in name],
        HEAD_WEIGHT=[head.weight], HEAD_BIAS=[head.bias])
    result = {}
    for name, values in grouped.items():
        gradients = [v.grad for v in values]
        require(gradients and all(g is not None for g in gradients), 'Missing direct-box gradient path: '+name)
        finite = bool(torch.stack([torch.isfinite(g).all() for g in gradients]).all())
        count = int(torch.stack([torch.count_nonzero(g) > 0 for g in gradients]).sum())
        norm = float(torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g.float()) for g in gradients])).item())
        require(finite and np_isfinite(norm), 'Nonfinite direct-box group gradient')
        result[name] = dict(tensors=len(values), nonzero_tensors=count, finite=finite, preclip_norm=norm)
    return result


def np_isfinite(value):
    import math
    return math.isfinite(value)


def validate_pilot_gradients(groups, step):
    require(step in (1, 2, 3, 4), 'Only first4 engineering gradient diagnostics')
    if step == 1:
        for name in ('HEAD_WEIGHT', 'HEAD_BIAS'):
            require(groups[name]['finite'] and groups[name]['nonzero_tensors'] > 0 and groups[name]['preclip_norm'] > 0,
                'Actual zero-head first-update training signal required')
    if step == 1:
        require(groups['LoRA_A']['nonzero_tensors'] == 0 and groups['LoRA_A']['preclip_norm'] == 0.,
            'Adopted84 B matrices remain zero; first recovery A gradient must be zero')
        require(groups['LoRA_B']['nonzero_tensors'] > 0 and groups['LoRA_B']['preclip_norm'] > 0,
            'Adopted nonzero head must give B real gradient at first recovery update')
    if step >= 2:
        require(all(groups[name]['nonzero_tensors'] > 0 and groups[name]['preclip_norm'] > 0 for name in ('LoRA_A', 'LoRA_B')),
            'LoRA A/B must receive real gradients at recovery steps2..4')


def _hidden(model, values, torch, training):
    hidden = model.get_base_model().model(**values, use_cache=False, return_dict=True).last_hidden_state[0, -1, :]
    if training:
        require(tuple(hidden.shape) == (4096,) and bool(torch.isfinite(hidden).all()) and torch.is_grad_enabled()
            and hidden.requires_grad and hidden.grad_fn is not None, 'Actual normalized source hidden must retain language-LoRA gradient')
    return hidden


def _screen(root, model, head, reader, prepared, admission, registration_ref, adapter_ref, head_ref, math84, frozen, torch, successful):
    stage = root/'direct_box_model_93/TRAINED_screen'; stage.mkdir(exist_ok=False)
    journal = stage/'attempts.jsonl'; journal.touch(exist_ok=False)
    entries = prepared['screen_inputs']
    require(len(entries) == len({e['id'] for e in entries}) == len({e['source_id'] for e in entries})
        == len({e['source_sha256'] for e in entries}) == 20, 'Exact native20 unique source-only entries')
    model.eval(); head.eval()
    require(not any(p.requires_grad for p in model.parameters()) and not any(p.requires_grad for p in head.parameters()), 'Readonly final direct-box model')
    previous = {}; completed = []
    for index, entry in enumerate(entries):
        frozen._deadline(admission); values, request = _input(reader, entry, torch)
        key = digest(dict(model_role=ROLE, source_id=request['source_id'], source_sha256=request['source_sha256'],
            width=request['width'], height=request['height'], input_signature=request['input_signature'], adapter_weights=adapter_ref, head_weights=head_ref))
        prior = previous.get(key); started = time.monotonic()
        if prior is None:
            gpu = {k:v.to('cuda:0') for k, v in values.items()}
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role=ROLE)
            frozen._deadline(admission)
            with torch.inference_mode():
                hidden = _hidden(model, gpu, torch, False)
                raw_hidden = hidden.float().cpu().contiguous()
            hidden_path = stage/('%04d.hidden.pt'%index); frozen._tensor_file(hidden_path, raw_hidden, torch)
            item = dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'], raw_hidden=ref(hidden_path), model_forward_returned=True)
            successful.append(item)
            with torch.inference_mode():
                raw_z_gpu = head(math84.normalize_hidden(hidden))
                raw_head = raw_z_gpu.float().cpu().contiguous()
            head_path = stage/('%04d.head.pt'%index); frozen._tensor_file(head_path, raw_head, torch)
            item['raw_head'] = ref(head_path)
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_hidden=item['raw_hidden'], raw_head=item['raw_head'], model_role=ROLE)
            require(raw_hidden.dtype == raw_head.dtype == torch.float32 and tuple(raw_hidden.shape) == (4096,)
                and tuple(raw_head.shape) == (3,) and bool(torch.isfinite(raw_hidden).all()) and bool(torch.isfinite(raw_head).all()), 'Persisted finite source hidden/head raw shapes')
            with torch.inference_mode(): decoded = math84.decode_torch(raw_z_gpu, request['width'], request['height']).float().cpu().tolist()
            torch.cuda.synchronize(); del gpu, hidden, raw_z_gpu, raw_hidden, raw_head
            hidden_reference, head_reference = item['raw_hidden'], item['raw_head']
        else:
            hidden_reference, head_reference, decoded = prior['raw_hidden'], prior['raw_head'], prior['decoded_xyw']
        receipt_path = stage/('%04d.receipt.json'%index)
        save(receipt_path, dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            role='screen', model_role=ROLE, input=entry['input'], width=request['width'], height=request['height'],
            raw_hidden=hidden_reference, raw_head=head_reference, decoded_xyw=decoded,
            raw_dtype='torch.float32', hidden_dimension=4096, head_dimension=3,
            hidden_transform=math84.RECIPE['hidden_transform'],
            adapter_weights=adapter_ref, head_weights=head_ref, input_signature=request['input_signature'], image_grid_thw=request['image_grid_thw'],
            actual_new_forward=prior is None, alias_of=prior['receipt'] if prior else None, elapsed_seconds=time.monotonic()-started,
            screen_reference_read=False, no_LM_generation=True, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, old_UTILITY_loaded=False))
        receipt_ref = ref(receipt_path)
        if prior is None:
            previous[key] = dict(raw_hidden=hidden_reference, raw_head=head_reference, decoded_xyw=decoded, receipt=receipt_ref)
        completed.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'], input=entry['input'], receipt=receipt_ref))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_ref, alias=prior is not None, model_role=ROLE)
        del values
    frozen._deadline(admission)
    save(stage/'completion.json', dict(status=SCREEN_STATUS, model_role=ROLE, expected_inputs=20, sources=20,
        entries=completed, actual_forward_calls=len(previous), aliases=20-len(previous), attempts=ref(journal),
        GPU_registration=registration_ref, input_prepared=ref(root/'direct_box_inputs_84/prepared.json'),
        adapter_weights=adapter_ref, head_weights=head_ref, hidden_transform=math84.RECIPE['hidden_transform'],
        screen_reference_read=False, no_LM_generation=True))
    return ref(stage/'completion.json')


def run(root, phase):
    root = Path(root).resolve()
    require(root.is_relative_to(WORK) and bool(os.environ.get('CUDA_VISIBLE_DEVICES')) and phase in ('pilot4', 'remaining794'), 'Explicit Linux phase/physical GPU')
    reg, admission, admission_ref, math84, frozen = _registration(root, phase); paths()
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model, set_peft_model_state_dict, PeftModel
    from safetensors.torch import load_file
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Pinned direct-box runtime')
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == admission['GPU_job'], 'Exact unique shared GPU reservation')
    torch.set_num_threads(2)
    prepared = read(bound(reg['prepared'])); recovery = read(bound(reg['recovery_prepared']))
    rows, entries, schedule_sha, schedule_report = validate_schedule(prepared, recovery, reg['prepared'])
    require(prepared['train_targets'] == recovery['train_targets'] == reg['train_targets'], 'Only explicitly registered train targets')
    target_document = read(bound(reg['train_targets'])); target_rows = target_document['sources']
    targets = {t['source_id']:t for t in target_rows}
    require(len(targets) == len(target_rows) == 602 and set(targets) == {e['source_id'] for e in entries.values()}, 'Exact602 train target owners')
    for entry in entries.values():
        t = targets[entry['source_id']]
        require(t['role'] == 'train' and t['reference_modified'] is False and t['source_sha256'] == entry['source_sha256'], 'Unmodified original train-only native XYWH')
        math84.target_xywh(t['original_reference_xywh'], t['width'], t['height'])
    component = module(reg['preparation_code'], '_direct_box93_input_reader')
    reader = component.DirectBoxInputs(root); require(reader.prepared == prepared, 'Reader adopts exact84 prepared')
    out = root/'direct_box_model_93'
    if phase == 'pilot4': out.mkdir(exist_ok=False); (out/'train').mkdir()
    else: require(out.is_dir(), 'Remaining adopts successful pilot namespace')
    save(out/(phase+'_claim.json'), dict(utc=utc(), pid=os.getpid(), GPU_registration=ref(root/'direct_box_GPU_registration_93.json'),
        GPU_admission=admission_ref, phase=phase, screen_targets_read=False, old_adapters_loaded=False))
    started = time.monotonic(); torch.cuda.reset_peak_memory_stats(); progress_path = out/'train/progress.pt'
    successful = []; completed_step = successful_micro = training_forwards = 0
    try:
        pilot = resumed = None
        if phase == 'remaining794':
            pilot = read(bound(admission['pilot_completion']))
            require(pilot['status'] == PILOT_STATUS and pilot['completed_updates'] == 4 and pilot['successful_micro'] == 16
                and pilot['actual_training_forwards'] == 16 and pilot['GPU_registration'] == ref(root/'direct_box_GPU_registration_93.json')
                and pilot['progress'] == admission['immutable_pilot_progress']
                and bound(pilot['progress']) == (out/'train/pilot_progress.pt').resolve()
                and sha(progress_path) == pilot['progress']['sha256'], 'Exact immutable complete direct-box step4 only')
            resumed = torch.load(bound(pilot['progress']), map_location='cpu', weights_only=True)
        random.seed(reg['recipe']['seed']); np.random.seed(reg['recipe']['seed']); torch.manual_seed(reg['recipe']['seed']); torch.cuda.manual_seed_all(reg['recipe']['seed'])
        cfg = read(bound(reg['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION, local_files_only=True,
            torch_dtype=torch.bfloat16, device_map={'':'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        require(not any('lora_' in name for name, _ in base.named_parameters()), 'Fresh physical BASE has no failed adapter')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == BASE and before['sha256'] == cfg['expected_base_sha256'], 'Pinned frozen BASE bytes')
        modules = [name for name, m in base.named_modules() if isinstance(m, torch.nn.Linear) and TARGET.search(name)]
        require(len(modules) == 144, 'Exact144 language qkvo targets')
        model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0., bias='none', target_modules=modules,
            task_type='CAUSAL_LM', modules_to_save=None), adapter_name=ADAPTER)
        for name, p in model.named_parameters(): p.requires_grad_(TRAINABLE.search(name) is not None)
        head = torch.nn.Linear(4096, 3, bias=True, device='cuda:0', dtype=torch.float32)
        with torch.no_grad(): head.weight.zero_(); head.bias.zero_()
        parameters, inventory = _inventory(model, head, True, torch); names = _names(parameters)
        require(set(names[0]) == set(_adapter_state(model, torch, frozen)), 'Exact PEFT-standard Adam name mapping')
        optimizer = torch.optim.AdamW([dict(params=[p for _, p in parameters], lr=5e-5), dict(params=list(head.parameters()), lr=.001)],
            betas=(.9, .999), eps=1e-8, weight_decay=0.)
        if resumed is None:
            warm = torch.load(bound(reg['original84_progress']), map_location='cpu', weights_only=True)
            original_reg = read(bound(reg['frozen_GPU84_registration']))
            validate_warmstart(warm, original_reg, prepared, names, torch)
            set_peft_model_state_dict(model, warm['adapter_state_dict'], adapter_name=ADAPTER)
            head.load_state_dict(warm['head_state_dict'])
            require(_tree_equal(_trainables(model, head, torch, frozen),
                {k:warm[k] for k in ('adapter_state_dict', 'head_state_dict')}, torch), 'Warmstart all288+2 tensors byte exact')
            require(not optimizer.state and len(optimizer.param_groups[0]['params']) == 288
                and len(optimizer.param_groups[1]['params']) == 2, 'Both newly initialized Adam groups must be empty')
            frozen._restore_rng(warm, torch, np)
            initial = _progress(model, head, optimizer, torch, np, frozen, 0, schedule_sha, reg, names)
            require(all(_tree_equal(initial[key], warm[key], torch) for key in RNG_KEYS), 'Exact adopted84 step1 four RNG states')
            frozen._tensor_file(out/'train/initial_trainables.pt', initial, torch); initial_ref = ref(out/'train/initial_trainables.pt')
        else:
            require(resumed['schema'] == PROGRESS_SCHEMA and resumed['step'] == 4 and resumed['micro'] == 16
                and resumed['logical_training_forwards'] == 16 and resumed['schedule_sha256'] == schedule_sha
                and resumed['train_schedule_reference'] == reg['recovery_prepared'] and resumed['train_targets_reference'] == reg['train_targets']
                and resumed['recipe'] == reg['recipe'] and resumed['optimizer_parameter_names_by_group'] == names
                and resumed['optimizer_parameter_names_sha256'] == digest(names)
                and resumed['original84_progress'] == reg['original84_progress']
                and resumed['optimizer_reset'] is True and resumed['original_successful_forwards'] == 8,
                'Complete unchanged recovery optimizer/RNG checkpoint')
            set_peft_model_state_dict(model, resumed['adapter_state_dict'], adapter_name=ADAPTER); head.load_state_dict(resumed['head_state_dict'])
            require(_tree_equal(_trainables(model, head, torch, frozen), {k:resumed[k] for k in ('adapter_state_dict', 'head_state_dict')}, torch), 'All288 adapter and2 head tensors restored exactly')
            optimizer.load_state_dict(resumed['optimizer_state_dict'])
            require(_tree_equal(frozen._cpu_tree(optimizer.state_dict(), torch), resumed['optimizer_state_dict'], torch), 'Both Adam groups exact restore')
            initial_ref = pilot['initial_trainables']; initial = torch.load(bound(initial_ref), map_location='cpu', weights_only=True)
            frozen._restore_rng(resumed, torch, np); completed_step, successful_micro, training_forwards = 4, 16, 16
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False}); model.train()
        for name, m in model.named_modules():
            if name.endswith('.visual'): m.eval()
        _inventory(model, head, True, torch)
        micro_journal = out/'train'/(phase+'_micro_loss.jsonl'); micro_journal.touch(exist_ok=False)
        update_journal = out/'train'/(phase+'_updates.jsonl'); update_journal.touch(exist_ok=False)
        for step in phase_steps(phase):
            optimizer.zero_grad(set_to_none=True); losses = []
            for micro in range((step-1)*4, step*4):
                frozen._deadline(admission); row = rows[micro]; entry = entries[row['input_id']]
                values, q = _input(reader, entry, torch); target = targets[row['source_id']]
                require((q['width'], q['height']) == (target['width'], target['height']), 'Original input/target native dimensions differ')
                append_event(micro_journal, event='BEGIN_TRAIN_MICRO', step=step, micro=micro, id=row['id'],
                    input_id=entry['id'], input=entry['input'], source_id=row['source_id'], original_micro=micro+8)
                gpu = {k:v.to('cuda:0') for k, v in values.items()}
                frozen._deadline(admission); hidden = _hidden(model, gpu, torch, True); training_forwards += 1
                normalized = math84.normalize_hidden(hidden)
                raw_z = head(normalized); unweighted, components = math84.loss(raw_z, target['original_reference_xywh'], q['width'], q['height'])
                loss = row['draw_weight']*unweighted; value = float(loss.detach().cpu())
                append_event(micro_journal, event='TRAIN_RAW_LOSS', step=step, micro=micro, id=row['id'], input_id=entry['id'],
                    source_id=row['source_id'], original_micro=micro+8, target_xywh=target['original_reference_xywh'], width=q['width'], height=q['height'],
                    draw_weight=row['draw_weight'], raw_head=raw_z.detach().float().cpu().tolist(),
                    unweighted_loss=float(unweighted.detach().cpu()), loss=value if np_isfinite(value) else None,
                    loss_repr=repr(value), components={k:float(v.detach().cpu()) for k, v in components.items()}, hidden_retained_real_gradient=True,
                    hidden_l2_norm=float(torch.linalg.vector_norm(hidden.detach().float()).cpu()),
                    normalized_hidden_l2=float(torch.linalg.vector_norm(normalized.detach()).cpu()))
                require(np_isfinite(value), 'Finite weighted direct-box loss')
                (loss/4).backward(); successful_micro = micro+1; losses.append(value)
                append_event(micro_journal, event='TRAIN_BACKWARD_COMPLETE', step=step, micro=micro, id=row['id'])
                del values, gpu, hidden, normalized, raw_z, unweighted, components, loss
            groups = _gradient_groups(parameters, head, torch)
            if step <= 4: validate_pilot_gradients(groups, step)
            norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in parameters]+list(head.parameters()), 1.).detach().cpu())
            require(np_isfinite(norm) and norm > 0., 'Finite nonzero combined direct-box gradient')
            frozen._deadline(admission); optimizer.step(); completed_step = step
            checkpoint = _progress(model, head, optimizer, torch, np, frozen, step, schedule_sha, reg, names)
            require(all(bool(torch.isfinite(v).all()) for v in list(checkpoint['adapter_state_dict'].values())+list(checkpoint['head_state_dict'].values())), 'Finite persisted complete direct-box update')
            frozen._atomic_progress(progress_path, checkpoint, torch)
            append_event(update_journal, event='SUCCESSFUL_UPDATE_PERSISTED', step=step, micro=step*4, mean_micro_loss=float(np.mean(losses)),
                grad_groups=groups, combined_preclip_gradient_norm=norm, progress=ref(progress_path))
            _inventory(model, head, True, torch)
        optimizer.zero_grad(set_to_none=True); model.eval(); model.gradient_checkpointing_disable()
        for p in model.parameters(): p.requires_grad_(False)
        head.requires_grad_(False); _inventory(model, head, False, torch)
        final = _trainables(model, head, torch, frozen)
        changed = {kind:sum(not _tree_equal(v, initial['adapter_state_dict'][key], torch) for key, v in final['adapter_state_dict'].items() if '.lora_'+kind+'.' in key) for kind in ('A', 'B')}
        head_changed = {key:not _tree_equal(v, initial['head_state_dict'][key], torch) for key, v in final['head_state_dict'].items()}
        require(changed['A'] > 0 and changed['B'] > 0 and all(head_changed.values()), 'Actual new A/B and head weight/bias bytes must update')
        after = canonical_frozen_hash(model, torch); require(after == before, 'Physical BASE/vision bytes changed')
        for key in ('old_TIME', 'old_PAIR', 'old_CROP'): bound(reg[key])
        frozen._deadline(admission)
        common = dict(GPU_registration=ref(root/'direct_box_GPU_registration_93.json'), remaining_admission=admission_ref if phase == 'remaining794' else None,
            pilot_completion=admission['pilot_completion'] if phase == 'remaining794' else None,
            completed_updates=completed_step, successful_micro=successful_micro, actual_training_forwards=training_forwards,
            actual_training_forwards_this_phase=16 if phase == 'pilot4' else 3176,
            initial_trainables=initial_ref, update_journal=ref(update_journal), gradient_journal=ref(update_journal), micro_journal=ref(micro_journal),
            inventory=inventory, base_fingerprint=after, recipe=reg['recipe'], schedule_sha256=schedule_sha,
            train_schedule_reference=reg['recovery_prepared'], train_targets_reference=reg['train_targets'], schedule_report=schedule_report,
            optimizer_parameter_names_by_group=names, optimizer_parameter_names_sha256=digest(names),
            changed_lora_A_tensors=changed['A'], changed_lora_B_tensors=changed['B'], actual_lora_A_changed=changed['A'] > 0,
            actual_lora_B_changed=changed['B'] > 0, head_weight_changed=head_changed['weight'], head_bias_changed=head_changed['bias'],
            original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, old_UTILITY_loaded=False,
            screen_reference_read=False, automatic_confirm=False, automatic_production=False,
            original84_progress=reg['original84_progress'], original84_failure=reg['original84_failure'],
            original_successful_updates=1, original_successful_forwards=8, optimizer_reset=True,
            hidden_transform=reg['recipe']['hidden_transform'])
        if phase == 'pilot4':
            immutable = out/'train/pilot_progress.pt'; frozen._copy_exclusive(progress_path, immutable)
            save(out/'pilot_completion.json', dict(status=PILOT_STATUS, progress=ref(immutable), seconds=time.monotonic()-started,
                peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20, peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20, dev_model_forwards=0, **common))
            return
        directory = out/'train/adapter'; directory.mkdir(exist_ok=False)
        model.save_pretrained(directory, safe_serialization=True, selected_adapters=[ADAPTER], save_embedding_layers=False)
        weight_paths = list(directory.rglob('adapter_model.safetensors'))
        require(len(weight_paths) == 1 and weight_paths[0].parent == directory/ADAPTER, 'Only new direct_box adapter saved')
        for file in directory.rglob('*'):
            if file.is_file():
                with file.open('rb') as stream: os.fsync(stream.fileno())
        frozen._sync_directory(directory/ADAPTER); frozen._sync_directory(directory)
        weight_path = weight_paths[0]
        require(frozen._same_state(load_file(str(weight_path), device='cpu'), final['adapter_state_dict'], torch), 'Saved direct-box adapter exact')
        head_path = out/'train/head.pt'; frozen._tensor_file(head_path, final['head_state_dict'], torch)
        saved_head = torch.load(head_path, map_location='cpu', weights_only=True)
        base = model.unload()
        require(not any('lora_' in name for name, _ in base.named_parameters()), 'Unloaded BASE retained adapter matrices')
        for p in base.parameters(): p.requires_grad_(False)
        model = PeftModel.from_pretrained(base, str(weight_path.parent), adapter_name=ADAPTER, is_trainable=False).eval()
        for p in model.parameters(): p.requires_grad_(False)
        head.load_state_dict(saved_head); head.requires_grad_(False)
        require(_tree_equal(_trainables(model, head, torch, frozen), final, torch), 'Complete288 plus2 head save/reload exact')
        _inventory(model, head, False, torch)
        adapter_ref, head_ref = ref(weight_path), ref(head_path)
        trained = _screen(root, model, head, reader, prepared, admission, ref(root/'direct_box_GPU_registration_93.json'),
            adapter_ref, head_ref, math84, frozen, torch, successful)
        require(_tree_equal(_trainables(model, head, torch, frozen), final, torch) and canonical_frozen_hash(model, torch) == before, 'Readonly screen changed final physical model')
        for key in ('old_TIME', 'old_PAIR', 'old_CROP'): bound(reg[key])
        frozen._deadline(admission)
        save(out/'completion.json', dict(status=FINAL_STATUS, adapter_weights=adapter_ref, head_weights=head_ref,
            adapter_directory=str(weight_path.parent), adapter_reload_all288_exact=True, head_reload_all2_exact=True,
            TRAINED_completion=trained, progress=ref(progress_path), seconds=time.monotonic()-started,
            peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20, peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20, **common))
    except BaseException as error:
        save(out/(phase+'_failure.json'), dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            completed_updates=completed_step, successful_micro=successful_micro, actual_training_forwards=training_forwards,
            successful_raw=successful, last_progress=ref(progress_path) if progress_path.is_file() else None,
            original84_progress=reg['original84_progress'], original_successful_updates=1,
            original_successful_forwards=8, hidden_transform=reg['recipe']['hidden_transform'],
            preserve_all_success=True, automatic_retry=False, failure_is_not_empty=True, automatic_confirm=False, automatic_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=('pilot4', 'remaining794'), required=True)
    args = parser.parse_args(); run(args.root, args.phase)
