"""PLAN62: one fixed vision-attention adaptation, no language/head training.

prepare adopts exact100 cached inputs on CPU; train updates only54 visual
attention low-rank branches; review first reads held-out targets on CPU.
There is no decoder, processor, search, automatic retry or production entry.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import re
import shutil
import time
import traceback

PROTOCOL63 = dict(schema='VISION_ATTENTION63_FIXED_SINGLE_PASS_V1', seed=20261021,
    rank=4, alpha=8, dropout=0.0, visual_blocks=27, visual_modules=54,
    adapter_matrices=108, adapter_parameters=746496, feature_dimension=4096,
    training_sources=18, training_pairs=36, source_pair_count=2, optimizer_steps=18,
    lr=1e-5, weight_decay=0.0, gradient_clip=1.0, threads=4, interop_threads=1,
    maximum_visual_forwards=173, maximum_backwards=36, maximum_GPU_seconds=900,
    planned_output_bytes=4 * 1024**3, minimum_check_accuracy=.75,
    minimum_improved_sources=2, pool_LN_eps=1e-5,
    source_order_salt='VISION_ATTENTION63_SOURCE:', pair_order_salt='VISION_ATTENTION63_PAIR:')
BASE_PARAMETERS = 8767123696
PROTECTED_PIPELINE_PARAMETERS = 8782557449
FULL_PIPELINE_WITH_HEAD = PROTECTED_PIPELINE_PARAMETERS + 746496 + 4096
INPUT_KEYS = {'pixel_values_videos', 'video_grid_thw', 'input_ids', 'attention_mask'}
TARGET = re.compile(r'^model\.visual\.blocks\.(\d+)\.attn\.(qkv|proj)$')
_VISUAL_CLASS = None


def _torch():
    """Keep protocol/module inspection independent of Torch availability."""
    global torch, nn, F
    if 'torch' not in globals():
        import torch as torch_module
        from torch import nn as nn_module
        from torch.nn import functional as functional_module
        torch, nn, F = torch_module, nn_module, functional_module
    return torch


def configure_threads():
    _torch()
    torch.set_num_threads(PROTOCOL63['threads'])
    if torch.get_num_interop_threads() != PROTOCOL63['interop_threads']:
        torch.set_num_interop_threads(PROTOCOL63['interop_threads'])


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def reference(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=h.hexdigest())


def checked(ref, workspace):
    path = Path(ref['path']).resolve(strict=True)
    require(path.is_relative_to(workspace) and path.is_file(), 'Bound path escaped workspace')
    actual = reference(path)
    require(all(actual[k] == ref[k] for k in actual), 'Bound bytes changed: ' + str(path))
    return path


def readref(ref, workspace):
    return json.loads(checked(ref, workspace).read_text(encoding='utf-8'))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tensor_signature(values):
    _torch()
    return {k: dict(dtype=str(v.dtype), shape=list(v.shape), sha256=hashlib.sha256(
        v.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
        for k, v in sorted(values.items())}


def cpu_tree(value):
    _torch()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().contiguous().clone()
    if isinstance(value, dict):
        return {k: cpu_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [cpu_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(cpu_tree(v) for v in value)
    return value


class Budget:
    def __init__(self, root, *, started=None):
        self.root, self.started = Path(root), started

    def check(self):
        if self.started is not None:
            require(time.monotonic() - self.started < PROTOCOL63['maximum_GPU_seconds'], 'Fixed900second GPU phase limit')

    def total(self):
        return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())

    def write(self, path, blob):
        self.check()
        path = Path(path)
        require(path.parent.resolve().is_relative_to(self.root) and not path.exists(), 'New63 files only; no overwrite/retry')
        needed = len(blob) + (1 << 20)
        require(self.total() + needed <= PROTOCOL63['planned_output_bytes'], 'Actual63 persistent4GiB budget exceeded')
        require(shutil.disk_usage(self.root).free >= needed, 'Actual next serialized buffer plus failure receipt cannot fit')
        with path.open('xb') as stream:
            stream.write(blob); stream.flush(); os.fsync(stream.fileno())
        return reference(path)

    def save(self, path, value):
        return self.write(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode())

    def tensor(self, path, value):
        _torch()
        buffer = io.BytesIO()
        torch.save(value, buffer)
        with buffer.getbuffer() as blob:
            return self.write(path, blob)


def _visual_class():
    global _VISUAL_CLASS
    _torch()
    if _VISUAL_CLASS is None:
        class Layer(nn.Module):
            def __init__(self, base_layer, rank=4, alpha=8):
                super().__init__()
                require(isinstance(base_layer, nn.Linear) and rank == 4 and alpha == 8, 'Fixed rank4/alpha8 Linear adaptation only')
                self.base_layer = base_layer
                self.rank, self.alpha, self.scaling = rank, alpha, alpha / rank
                for value in self.base_layer.parameters():
                    value.requires_grad_(False)
                self.lora_A = nn.Parameter(torch.empty(rank, base_layer.in_features, device=base_layer.weight.device, dtype=torch.float32))
                self.lora_B = nn.Parameter(torch.zeros(base_layer.out_features, rank, device=base_layer.weight.device, dtype=torch.float32))
                nn.init.kaiming_uniform_(self.lora_A, a=5**.5)

            def forward(self, x):
                original = self.base_layer(x)
                delta = F.linear(F.linear(x.float(), self.lora_A), self.lora_B) * self.scaling
                return original + delta.to(original.dtype)
        _VISUAL_CLASS = Layer
    return _VISUAL_CLASS


def VisualLoRALinear(base_layer, rank=4, alpha=8):
    """Lazy Module factory: immutable base Linear plus FP32 attention delta."""
    return _visual_class()(base_layer, rank, alpha)


def attach_visual_lora(model):
    """Attach to the unwrapped Qwen conditional model; return exact54 paths."""
    _torch()
    names = [name for name, module in model.named_modules() if TARGET.fullmatch(name) and isinstance(module, nn.Linear)]
    expected = {f'model.visual.blocks.{i}.attn.{kind}' for i in range(27) for kind in ['qkv', 'proj']}
    require(set(names) == expected and len(names) == 54, 'Exact27block54 original visual qkv/proj modules required')
    for name in names:
        layer = model.get_submodule(name)
        kind = TARGET.fullmatch(name)[2]
        require(tuple(layer.weight.shape) == ((3456, 1152) if kind == 'qkv' else (1152, 1152)), 'Actual visual attention header differs')
        parent, leaf = name.rsplit('.', 1)
        setattr(model.get_submodule(parent), leaf, VisualLoRALinear(layer))
    return sorted(names)


def lora_parameters(model):
    layer_class = _visual_class()
    result = {}
    for name, module in model.named_modules():
        if isinstance(module, layer_class):
            result[name + '.lora_A'] = module.lora_A
            result[name + '.lora_B'] = module.lora_B
    return result


def lora_state(model):
    return {name: value.detach().cpu().contiguous().clone() for name, value in lora_parameters(model).items()}


def load_lora_state(model, state):
    _torch()
    params = lora_parameters(model)
    require(set(params) == set(state), 'Complete actual adapter key set required')
    with torch.no_grad():
        for name, value in state.items():
            require(isinstance(value, torch.Tensor) and value.dtype == torch.float32 and value.shape == params[name].shape
                    and bool(torch.isfinite(value).all()), 'Exact finite FP32 adapter shape/dtype required')
            params[name].copy_(value.to(device=params[name].device))
    actual = lora_state(model)
    require(all(torch.equal(actual[k].view(torch.uint8), state[k].cpu().contiguous().view(torch.uint8)) for k in state),
            'Actual installed FP32 adapter reload differs')


def inventory(model, training):
    _torch()
    params = lora_parameters(model)
    expected = {f'model.visual.blocks.{i}.attn.{kind}.lora_{side}'
                for i in range(27) for kind in ['qkv', 'proj'] for side in ['A', 'B']}
    require(set(params) == expected and len(params) == 108 and sum(p.numel() for p in params.values()) == 746496,
            'Only exact108 visual adapter matrices/746496parameters are permitted')
    ids = {id(v) for v in params.values()}
    for name, value in model.named_parameters():
        if id(value) in ids:
            require(value.dtype == torch.float32 and value.requires_grad is training, 'Actual visual adapter precision/trainability differs')
        else:
            require(not value.requires_grad and value.grad is None and 'lora_' not in name,
                    'Unexpected trainable BASE/merger/language/TIME/adapter: ' + name)
    return params


def pool_feature(embeddings, grid, plan):
    _torch()
    require(isinstance(embeddings, (tuple, list)) and len(embeddings) == 2 and tuple(grid.shape) == (2, 3),
            'Actual two-video split required; deepstack is a separate unused return value')
    counts = [int(t * h * w // 4) for t, h, w in grid.tolist()]
    require(len(plan['videos']) == 2 and [x['role'] for x in plan['videos']] == ['Overview', 'Excerpt'], 'Original view roles/order required')
    for row, view, values, count in zip(grid.tolist(), plan['videos'], embeddings, counts):
        t, h, w = row
        require(t == view['groups'] > 0 and h > 0 and w > 0 and h % 2 == w % 2 == 0
                and len(view['native_ordinals']) == 2 * t and view['padding'] == 0
                and tuple(values.shape) == (count, 4096), 'Original native group/grid ownership differs')
    excerpt = embeddings[1].float()
    feature = F.layer_norm(excerpt.mean(0), (4096,), eps=1e-5)
    groups, height, width = grid[1].tolist()
    # Independent means are audit data; the differentiable feature stays on GPU.
    audit_means = excerpt.detach().cpu().double().reshape(groups, height * width // 4, 4096).mean(1).float()
    return feature, audit_means


def fixed_margin(left, right, head):
    _torch()
    require(left.dtype == right.dtype == torch.float32 and tuple(left.shape) == tuple(right.shape) == (4096,), 'Original FP32 pooled features required')
    require(head.dtype == torch.float64 and tuple(head.shape) == (4096,) and not head.requires_grad,
            'Original frozen FP64 head53 vector required')
    return ((left.double() - right.double()) / 64) @ head


def soft_pair_loss(left, right, head, target):
    _torch()
    require(type(target) in (float, int) and 0 <= target <= 1, 'Original finite all-rater soft preference required')
    margin = fixed_margin(left, right, head)
    y = torch.as_tensor(target, device=margin.device, dtype=torch.float64)
    return F.binary_cross_entropy_with_logits(margin, y), margin


def validate_training_pairs(rows, cases, train_uids):
    require(len(rows) == 36 and len(train_uids) == 72 and set(train_uids) <= set(cases), 'Only original36pairs72trainingcases required')
    sources, pair_ids, used = {}, set(), []
    for row in rows:
        sid = row['source_id']
        require(row['pair_id'] not in pair_ids and row['source_pair_count'] == 2
                and row['left'] in train_uids and row['right'] in train_uids and row['left'] != row['right']
                and cases[row['left']]['sid'] == cases[row['right']]['sid'] == sid
                and type(row['preference_left']) in (int, float) and 0 <= row['preference_left'] <= 1,
                'No held-out target/case, foreign source, duplicate pair or altered soft target is permitted')
        pair_ids.add(row['pair_id']); sources.setdefault(sid, []).append(row); used.extend([row['left'], row['right']])
    require(len(sources) == 18 and all(len(v) == 2 for v in sources.values()) and set(used) == set(train_uids),
            'Exactly18sources/two original pairs/source and all72cases required')
    return sources


def context(root):
    root = Path(root).resolve(strict=True); r = root.parent; w = r.parent
    reg = json.loads((root / 'registration63.json').read_text(encoding='utf-8'))
    require(checked(reg['code_ref'], w) == Path(__file__).resolve(), 'Exact new63 implementation required')
    protocol = readref(reg['protocol_ref'], w)
    require(all(protocol.get(k) == v for k, v in PROTOCOL63.items()), 'Single fixed PLAN62 protocol differs')
    n53 = Path(reg['old53_root']).resolve(strict=True)
    require(n53.parent == r and n53 != root, 'Explicit separate original53 root required')
    old_path = checked(reg['old53_code_ref'], w)
    require(old_path == n53 / 'vision_readout53.py', 'Exact original53 helper required')
    old = load_module(old_path, 'bound_original_vision53_for63')
    _, _, _, api, common, manifest, store, canonical, a06, a11, _ = old.context(n53)
    require(reg['model_spec'] == manifest['model_spec'], 'Original BASE model specification differs')
    require(readref(reg['old_input06_ref'], w) == a06 and readref(reg['old_input11_ref'], w) == a11,
            'Original06/11 acceptance references differ')
    for key in ['old_head_ref', 'old_review53_ref', 'old_control12_ref']:
        checked(reg[key], w)
    return root, r, w, reg, protocol, n53, old, api, common, manifest, store, canonical, a06, a11


def prepare(root):
    configure_threads()
    n, r, w, reg, p, n53, old, api, common, manifest, store, _, a06, a11 = context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'prepare63 must run in a dedicated CPU child')
    require(not any((n / x).exists() for x in ['prepare_started63.json', 'runtime_inputs63.pt', 'input_acceptance63.json', 'failure_prepare63.json']),
            'New63 CPU prepare is single-use; no automatic retry or overwrite')
    started = time.monotonic(); budget = Budget(n)
    budget.save(n / 'prepare_started63.json', dict(status='FIRST_CPU_ADOPTION63_STARTED', code_ref=reg['code_ref'], automatic_GPU=False))
    values, cases = old.adopted_values(n, r, w, api, common, manifest, store, a06, a11, torch)
    adoption = json.loads((n / 'input_adoption53.json').read_text())
    case_refs = adoption['case_refs']; train_uids = sorted(a11['case_refs'])
    require(len(values) == len(cases) == len(case_refs) == 100, 'Original100 adopted input denominator required')
    rows = readref(a11['training_target_ref'], w)
    groups = validate_training_pairs(rows, cases, set(train_uids))
    train_sha = {cases[u]['source_sha256'] for u in train_uids}
    check_sha = {cases[u]['source_sha256'] for u in cases if u not in set(train_uids)}
    require(len(train_sha) == 18 and len(check_sha) == 8 and not train_sha & check_sha, 'Actual physical train/check SHA isolation required')
    for uid, v in values.items():
        require(set(v) == INPUT_KEYS and common.signature(v) == cases[uid]['input_signature'], 'Exact four CPU input tensors must adopt accepted signatures')
    head = torch.load(checked(reg['old_head_ref'], w), map_location='cpu', weights_only=True)['weight']
    require(head.dtype == torch.float64 and tuple(head.shape) == (4096,) and not head.requires_grad
            and bool(torch.isfinite(head).all()) and bool(head.abs().max() > 0), 'Exact nonzero original FP64 head53 required')
    input_ref = budget.tensor(n / 'runtime_inputs63.pt', values)
    reloaded = torch.load(checked(input_ref, w), map_location='cpu', weights_only=True)
    require(set(reloaded) == set(values) and all(common.signature(reloaded[u]) == cases[u]['input_signature'] for u in cases),
            'First durable runtime100 input serialization lost original bits')
    cases_ref = budget.save(n / 'cases63.json', cases)
    target_ref = budget.save(n / 'train_targets63.json', rows)
    completion53_ref = reference(n53 / 'gpu_completion53.json')
    complete = readref(completion53_ref, w)
    zero_uid = train_uids[0]
    found = [rr for rr in complete['feature_refs'] if readref(rr, w)['uid'] == zero_uid]
    require(len(found) == 1, 'One original53 feature for the fixed zeroB identity case required')
    zero_row = readref(found[0], w)
    require(zero_row['original_case_signature'] == cases[zero_uid]['input_signature'], 'ZeroB cached original53 input identity differs')
    checked(zero_row['feature_ref'], w)
    result = dict(status='PASS_CPU_INPUT_ADOPTION63_NO_MODEL_OR_GPU_ADMISSION', input_values_ref=input_ref,
        cases_ref=cases_ref, case_refs=case_refs, train_target_ref=target_ref, train_uids=train_uids,
        source_ids=sorted(groups), source_count=18, training_pairs=36, cases=100,
        old_QA_adoption_ref=reference(n / 'input_adoption53.json'), old_successful_pixel_text_QA_adopted=True,
        first_runtime100_save_reload_bit_signatures=True, new_decode=0, new_processor=0, new_model_calls=0,
        check_targets_read=False, model_spec=manifest['model_spec'], old_head_ref=reg['old_head_ref'],
        head_signature=tensor_signature({'weight': head}), zero_uid=zero_uid,
        zero_old53_output_ref=found[0], zero_old53_payload_ref=zero_row['feature_ref'],
        old53_completion_ref=completion53_ref, registration_ref=reference(n / 'registration63.json'),
        protocol_ref=reg['protocol_ref'], code_ref=reg['code_ref'], seconds=time.monotonic() - started,
        automatic_GPU=False, planned_output_bytes=p['planned_output_bytes'])
    budget.save(n / 'input_acceptance63.json', result)
    return result


def train(root):
    configure_threads()
    started = time.monotonic()
    n, r, w, reg, p, _, old, api, common, manifest, _, canonical, _, _ = context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in (None, '', '-1'), 'Existing unique GPU wrapper must expose CUDA')
    admission = json.loads((n / 'GPUadmission63.json').read_text())
    require(admission['approved'] is True and admission['code_ref'] == reg['code_ref']
            and admission['protocol_ref'] == reg['protocol_ref'] and admission['max_gpu_seconds'] == 900
            and admission['planned_output_bytes'] == 4 * 1024**3, 'Exact separate bounded GPU admission required')
    accepted_path = checked(admission['input_acceptance_ref'], w)
    require(accepted_path == n / 'input_acceptance63.json', 'Only this new63 accepted runtime cache may train')
    accepted = readref(admission['input_acceptance_ref'], w)
    require(accepted['status'] == 'PASS_CPU_INPUT_ADOPTION63_NO_MODEL_OR_GPU_ADMISSION'
            and accepted['registration_ref'] == reference(n / 'registration63.json')
            and accepted['code_ref'] == reg['code_ref'] and accepted['check_targets_read'] is False,
            'Natural CPU input acceptance identity differs')
    lock = readref(admission['source_lock_ref'], w)
    required_lock = dict(code_ref=reg['code_ref'], protocol_ref=reg['protocol_ref'],
        registration_ref=reference(n / 'registration63.json'), input_acceptance_ref=admission['input_acceptance_ref'])
    require(all(lock.get(k) == value for k, value in required_lock.items()), 'New63 source lock does not bind exact accepted code/protocol/input')
    require(admission['gpu_wrapper_ref'] == manifest['gpu_wrapper_ref'], 'Original unique shared wrapper identity differs')
    checked(admission['gpu_wrapper_ref'], w)
    require(not any((n / name).exists() for name in ['train_started63.json', 'gpu_completion63.json', 'failure_train63.json', 'train63']),
            'One new63 GPU attempt only; no automatic retry/resume')
    budget = Budget(n, started=started)
    budget.save(n / 'train_started63.json', dict(status='FIRST_GPU_ATTENTION63_STARTED', admission_ref=reference(n / 'GPUadmission63.json')))
    random.seed(p['seed']); torch.manual_seed(p['seed']); torch.cuda.manual_seed_all(p['seed'])
    import sys
    sys.path.insert(0, str(w / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    require(torch.cuda.is_available(), 'Actual reserved CUDA is required')
    from transformers import Qwen3VLForConditionalGeneration
    values = torch.load(checked(accepted['input_values_ref'], w), map_location='cpu', weights_only=True)
    cases = readref(accepted['cases_ref'], w)
    require(len(values) == len(cases) == 100 and set(values) == set(cases), 'Exact100 durable runtime cases required')
    for uid, v in values.items():
        require(set(v) == INPUT_KEYS and common.signature(v) == cases[uid]['input_signature'], 'Durable runtime63 input changed')
    targets = readref(accepted['train_target_ref'], w)  # No held-out preferences are read in train.
    sources = validate_training_pairs(targets, cases, set(accepted['train_uids']))
    head_cpu = torch.load(checked(reg['old_head_ref'], w), map_location='cpu', weights_only=True)['weight']
    require(tensor_signature({'weight': head_cpu}) == accepted['head_signature'], 'Original immutable head53 bytes changed')
    require(head_cpu.dtype == torch.float64 and tuple(head_cpu.shape) == (4096,) and not head_cpu.requires_grad,
            'Exact frozen FP64 head53 only')
    head = head_cpu.to('cuda:0'); head.requires_grad_(False)
    protected = [manifest['protected_baseline_ref'], manifest['model_spec']['adapter_weights']]
    for rr in protected:
        checked(rr, w)
    spec = manifest['model_spec']
    model = Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'], revision=spec['revision'],
        local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
    model.requires_grad_(False); model.eval()
    before = canonical(model, torch)
    require(before['parameters'] == BASE_PARAMETERS and before['sha256'] == spec['base_sha256'], 'Actual original BASE identity differs')
    modules = attach_visual_lora(model)
    model.eval()
    params = lora_parameters(model)
    for value in params.values():
        value.requires_grad_(False)
    inventory(model, False)
    require(all(module.base_layer.weight.dtype == torch.bfloat16 for module in model.modules() if isinstance(module, _visual_class())),
            'Original attention BASE tensors must remain BF16')
    initial = lora_state(model)
    require(all(not bool(v.count_nonzero()) for k, v in initial.items() if k.endswith('.lora_B')), 'All54 initial LoRA_B must be exactly zero')
    out, feature_dir = n / 'train63', n / 'features63'
    out.mkdir(); feature_dir.mkdir()
    initial_ref = budget.tensor(out / 'initial_adapter63.pt', initial)
    definition = dict(schema='CUSTOM_VISUAL_ATTENTION_LORA63_V1', target_modules=modules, rank=4, alpha=8,
        scaling=2., dropout=0., matrices=108, adapter_parameters=746496, feature_dimension=4096,
        initial_adapter_ref=initial_ref, head_ref=reg['old_head_ref'], head_signature=accepted['head_signature'],
        head_compute='FP64(LEFT_FP32_FEATURE)-FP64(RIGHT_FP32_FEATURE), /64, dot original FP64 head',
        pool='FINAL_MERGED_EXCERPT_SPATIOTEMPORAL_MEAN_FP32_FIXED_LN_EPS1e-5',
        base_before=before, base_parameters=BASE_PARAMETERS,
        actual_resident_parameters=BASE_PARAMETERS + 746496 + 4096,
        conservative_full_pipeline_parameters=FULL_PIPELINE_WITH_HEAD,
        language_and_TIME_updates=0, main_and_deepstack_merger_updates=0,
        protocol_ref=reg['protocol_ref'], implementation_ref=reg['code_ref'])
    require(FULL_PIPELINE_WITH_HEAD <= 9_000_000_000, 'Whole protected pipeline plus adapter/head exceeds9B')
    definition_ref = budget.save(n / 'definition63.json', definition)
    counts = dict(vision_forwards=0, language_forwards=0, backwards=0, updates=0)
    mode = ['zero']; current_state = [initial_ref]
    def event(kind, **fields):
        budget.check()
        row = dict(event=kind, elapsed=time.monotonic()-started, counts=dict(counts), **fields)
        with (n / 'events63.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush(); os.fsync(stream.fileno())
    def vision_guard(_module, _args):
        budget.check(); inventory(model, mode[0] == 'train')
        require(counts['vision_forwards'] < 173 and head.requires_grad is False, 'Finite vision-only calls and frozen head required')
        counts['vision_forwards'] += 1
    def forbid_language(_module, _args):
        counts['language_forwards'] += 1
        raise RuntimeError('PLAN62 phase63 admits zero language forwards')
    hv = model.model.visual.register_forward_pre_hook(vision_guard)
    hl = model.model.language_model.register_forward_pre_hook(forbid_language)
    def feature(uid, tag, gradient):
        budget.check(); v = values[uid]
        event('BEGIN_FIRST_VISION_RESULT', uid=uid, tag=tag, parameter_state_ref=current_state[0])
        manager = torch.enable_grad() if gradient else torch.inference_mode()
        with manager:
            embeddings, deepstack = model.get_video_features(v['pixel_values_videos'].to('cuda:0'), v['video_grid_thw'].to('cuda:0'))
            f, group_means = pool_feature(embeddings, v['video_grid_thw'], cases[uid]['plan'])
            del embeddings, deepstack
        # Every returned first result is durable before finite/independent QA.
        payload = dict(uid=uid, feature=f.detach().cpu().clone(), independent_group_means=group_means,
            source_sha256=cases[uid]['source_sha256'], input_signature=cases[uid]['input_signature'],
            video_grid_thw=v['video_grid_thw'].clone(), parameter_state_ref=current_state[0], tag=tag)
        raw_ref = budget.tensor(feature_dir / (tag + '.pt'), payload)
        row = dict(uid=uid, source_sha256=cases[uid]['source_sha256'], input_signature=cases[uid]['input_signature'],
            feature_ref=raw_ref, case_ref=accepted['case_refs'][uid], actual_visual_call=counts['vision_forwards'],
            durable_before_first_independent_QA=True, tag=tag)
        row_ref = budget.save(feature_dir / (tag + '.json'), row)
        require(tuple(f.shape) == (4096,) and bool(torch.isfinite(f).all()) and bool(f.abs().max() > 0), 'Finite nonconstant actual feature required')
        require(f.requires_grad is gradient, 'Actual visual LoRA feature gradient connection differs')
        event('FIRST_VISION_RAW_DURABLE', uid=uid, tag=tag, output_ref=row_ref)
        return f, row_ref, payload
    # Exactly one new zeroB identity call; original100 BASE outputs stay adopted.
    zero_uid = accepted['zero_uid']
    zero_f, zero_ref, _ = feature(zero_uid, 'zero_' + zero_uid, False)
    prior = torch.load(checked(accepted['zero_old53_payload_ref'], w), map_location='cpu', weights_only=True)
    require(prior['uid'] == zero_uid and prior['input_signature'] == cases[zero_uid]['input_signature']
            and torch.equal(zero_f.detach().cpu().view(torch.uint8), prior['feature'].view(torch.uint8)),
            'One first active-zeroB visual feature must exactly reproduce its original53 cached output')
    budget.save(n / 'zero_identity63.json', dict(status='PASS_ONE_FIRST_ACTIVE_ZERO_B_CACHE_IDENTITY',
        actual_output_ref=zero_ref, adopted_old53_ref=accepted['zero_old53_payload_ref'], old_BASE_calls_repeated=0,
        new_active_zeroB_identity_calls=1, all_other_BASE_outputs_adopted=True))
    del zero_f, prior
    for value in params.values():
        value.requires_grad_(True)
    model.train(); mode[0] = 'train'
    require(all(not isinstance(module, nn.Dropout) or module.p == 0
                for module in model.model.visual.modules()), 'Visual dropout must remain exactly zero')
    # Non-reentrant checkpointing supports frozen patch inputs and trainable adapters.
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    inventory(model, True)
    optimizer = torch.optim.AdamW(list(params.values()), lr=1e-5, weight_decay=0.)
    optimizer.zero_grad(set_to_none=True)
    source_order = sorted(sources, key=lambda sid: hashlib.sha256((p['source_order_salt'] + sid).encode()).hexdigest())
    order = [row for sid in source_order for row in sorted(sources[sid], key=lambda q: hashlib.sha256((p['pair_order_salt'] + q['pair_id']).encode()).hexdigest())]
    order_ref = budget.save(out / 'frozen_order63.json', dict(source_order=source_order, pair_order=[q['pair_id'] for q in order],
        source_weighting='Each source two original pair BCE losses averaged, exactly one AdamW update/source'))
    training_rows = []
    for index, row in enumerate(order):
        budget.check(); require(counts['backwards'] == index, 'No successful training pair may repeat or be skipped')
        fa, left_ref, _ = feature(row['left'], f'train_{index:02d}_left', True)
        fb, right_ref, _ = feature(row['right'], f'train_{index:02d}_right', True)
        loss, margin = soft_pair_loss(fa, fb, head, row['preference_left'])
        raw = dict(pair_id=row['pair_id'], source_id=row['source_id'], cursor=index+1,
            soft_target=row['preference_left'], margin=float(margin.detach()), BCE=float(loss.detach()),
            gradient_weight=.5, left_ref=left_ref, right_ref=right_ref, parameter_state_ref=current_state[0])
        raw_ref = budget.save(out / f'train_pair_{index:02d}.json', raw)
        require(bool(torch.isfinite(loss)) and loss.requires_grad, 'Finite connected fixed-head soft preference loss required')
        (loss / 2).backward(); counts['backwards'] += 1
        gradients = {k: v.grad for k, v in params.items()}
        require(all(g is not None and g.dtype == torch.float32 and bool(torch.isfinite(g).all()) for g in gradients.values()),
                'Every admitted visual matrix must receive a finite actual FP32 gradient')
        bnorm2 = sum(float(g.detach().double().square().sum()) for k, g in gradients.items() if k.endswith('.lora_B'))
        anorm2 = sum(float(g.detach().double().square().sum()) for k, g in gradients.items() if k.endswith('.lora_A'))
        require(bnorm2 > 0, 'Actual nonzero visual LoRA_B signal is required')
        if (index + 1) % 2 == 0:
            require(order[index-1]['source_id'] == row['source_id'], 'Only same-source two-pair accumulation permitted')
            norm = torch.nn.utils.clip_grad_norm_(list(params.values()), 1.)
            require(bool(torch.isfinite(norm)) and float(norm) > 0, 'Finite positive global visual gradient norm required')
            optimizer.step(); counts['updates'] += 1; optimizer.zero_grad(set_to_none=True)
            event('ACTUAL_VISUAL_ATTENTION_UPDATE', update=counts['updates'], source_id=row['source_id'],
                  gradient_norm=float(norm), A_gradient_norm=anorm2**.5, B_gradient_norm=bnorm2**.5)
        progress = dict(cursor=index+1, counts=dict(counts), adapter_state_dict=lora_state(model),
            optimizer=cpu_tree(optimizer.state_dict()), gradients={k: None if v.grad is None else cpu_tree(v.grad) for k, v in params.items()},
            torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state(), order_ref=order_ref,
            raw_pair_ref=raw_ref, automatic_resume=False)
        current_state[0] = budget.tensor(out / f'progress_pair_{index:02d}.pt', progress)
        event('TRAINING_PAIR_DURABLE', pair_id=row['pair_id'], cursor=index+1, progress_ref=current_state[0])
        training_rows.append(raw_ref)
        del fa, fb, loss, margin, progress
    require(counts['backwards'] == 36 and counts['updates'] == 18 and counts['vision_forwards'] == 73, 'Exact single36pair/18update/72derivativeforward training required')
    model.eval(); model.gradient_checkpointing_disable(); mode[0] = 'final'
    for value in params.values():
        value.requires_grad_(False); value.grad = None
    inventory(model, False)
    final_state = lora_state(model)
    changed = [k for k in initial if not torch.equal(initial[k].view(torch.uint8), final_state[k].view(torch.uint8))]
    require(any(k.endswith('.lora_A') for k in changed) and any(k.endswith('.lora_B') for k in changed), 'Actual A and B visual attention changes required')
    final_ref = budget.tensor(n / 'final_vision_adapter63.pt', dict(adapter_state_dict=final_state,
        definition=definition, definition_ref=definition_ref, protocol_ref=reg['protocol_ref'],
        counts=dict(counts), head_ref=reg['old_head_ref'], base_before=before))
    saved = torch.load(checked(final_ref, w), map_location='cpu', weights_only=True)
    load_lora_state(model, initial)
    require(tensor_signature(lora_state(model)) == tensor_signature(initial), 'Actual RAM initial reset must precede final reload')
    load_lora_state(model, saved['adapter_state_dict'])
    reload_signature = tensor_signature(lora_state(model))
    require(reload_signature == tensor_signature(final_state), 'Every final FP32 visual matrix must reload exactly after actual reset')
    current_state[0] = final_ref
    reload_ref = budget.save(n / 'adapter_reload63.json', dict(status='PASS_ALL108_FP32_RESET_INITIAL_THEN_RELOAD_FINAL_BIT_EXACT',
        initial_ref=initial_ref, final_adapter_ref=final_ref, signature=reload_signature, changed_matrices=changed,
        module_assignment_events_for_replay=2, additional_optimizer_steps=0,
        fixed_head_signature=tensor_signature({'weight': head.detach().cpu()})))
    del optimizer, saved
    final_outputs = []
    for uid in sorted(cases):
        _, rr, _ = feature(uid, 'final_' + uid, False)
        final_outputs.append(rr)
    hv.remove(); hl.remove()
    require(counts == dict(vision_forwards=173, language_forwards=0, backwards=36, updates=18), 'Exact total173/zero-language/36backward/18update limits required')
    require(tensor_signature({'weight': head.detach().cpu()}) == accepted['head_signature'], 'Original FP64 measuring head changed')
    after = canonical(model, torch)
    require(after == before and before['sha256'] == spec['base_sha256'], 'Original BASE including main/deepstack merger/language bytes changed')
    require(tensor_signature(lora_state(model)) == reload_signature, 'Final inference changed reloaded visual adapter')
    inventory(model, False)
    for rr in protected:
        checked(rr, w)
    result = dict(status='ENGINEERING_COMPLETE_VISUAL_ATTENTION63_NOT_QUALITY_OR_TIME43_ADMISSION',
        **counts, final_adapter_ref=final_ref, definition_ref=definition_ref, initial_adapter_ref=initial_ref,
        adapter_reload_ref=reload_ref, reload_signature=reload_signature, feature_refs=final_outputs,
        training_raw_refs=training_rows, input_acceptance_ref=admission['input_acceptance_ref'],
        source_lock_ref=admission['source_lock_ref'], protocol_ref=reg['protocol_ref'], code_ref=reg['code_ref'],
        base_before=before, base_after=after, head_ref=reg['old_head_ref'], head_signature=accepted['head_signature'],
        head_updates=0, merger_updates=0, language_updates=0, TIME_updates=0,
        changed_adapter_matrices=changed, independent_first_output_QA='PENDING_CPU_REVIEW',
        checkpoint_block_recomputation='NON_REENTRANT_INTERNAL_BACKWARD_WORK_NOT_EXTRA_TOP_LEVEL_VISION_CALLS',
        seconds=time.monotonic()-started, protected40_47_unchanged=True, automatic_TIME43=False,
        automatic_production=False, new_ZIP=0, official_submissions=0)
    budget.save(n / 'gpu_completion63.json', result)
    return result


def review(root):
    configure_threads()
    n, _, w, reg, p, _, old, _, _, _, _, _, a06, _ = context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'First63 review is CPU only')
    decision = json.loads((n / 'review_admission63.json').read_text())
    require(decision['approved'] is True and decision['natural_wrapper_exit_code'] == 0
            and decision['unique_ledger'] == 'PASS'
            and checked(decision['gpu_completion_ref'], w) == n / 'gpu_completion63.json', 'Natural unique wrapper completion required before first held-out evaluation')
    checked(decision['resource_ref'], w)
    done = readref(decision['gpu_completion_ref'], w)
    accepted = readref(done['input_acceptance_ref'], w)
    require(done['status'] == 'ENGINEERING_COMPLETE_VISUAL_ATTENTION63_NOT_QUALITY_OR_TIME43_ADMISSION'
            and done['code_ref'] == reg['code_ref'] and done['protocol_ref'] == reg['protocol_ref']
            and accepted['code_ref'] == reg['code_ref'] and accepted['protocol_ref'] == reg['protocol_ref']
            and accepted['registration_ref'] == reference(n / 'registration63.json')
            and done['base_before'] == done['base_after']
            and done['base_before']['sha256'] == reg['model_spec']['base_sha256']
            and done['head_ref'] == reg['old_head_ref']
            and (done['vision_forwards'], done['backwards'], done['updates'], done['language_forwards']) == (173, 36, 18, 0),
            'Actual frozen-backbone training identity/counters differ')
    budget = Budget(n)
    require(not (n / 'review63.json').exists(), 'First review only; no automatic repeat')
    cases = readref(accepted['cases_ref'], w)
    final = torch.load(checked(done['final_adapter_ref'], w), map_location='cpu', weights_only=True)
    initial = torch.load(checked(done['initial_adapter_ref'], w), map_location='cpu', weights_only=True)
    state = final['adapter_state_dict']; signature = tensor_signature(state)
    require(final['definition_ref'] == done['definition_ref'] and final['head_ref'] == reg['old_head_ref']
            and final['protocol_ref'] == reg['protocol_ref']
            and final['counts'] == dict(vision_forwards=73, language_forwards=0, backwards=36, updates=18),
            'Saved final adapter must be the exact final18update state before first100 outputs')
    require(len(state) == 108 and sum(t.numel() for t in state.values()) == 746496
            and all(t.dtype == torch.float32 and bool(torch.isfinite(t).all()) for t in state.values())
            and signature == done['reload_signature'], 'Independent saved full108 FP32 adapter signature differs')
    reload_receipt = readref(done['adapter_reload_ref'], w)
    require(reload_receipt['signature'] == signature and reload_receipt['final_adapter_ref'] == done['final_adapter_ref']
            and reload_receipt['status'] == 'PASS_ALL108_FP32_RESET_INITIAL_THEN_RELOAD_FINAL_BIT_EXACT', 'Actual module reset/reload receipt differs')
    changed = [k for k in state if not torch.equal(state[k].view(torch.uint8), initial[k].view(torch.uint8))]
    require(set(changed) == set(done['changed_adapter_matrices']) and any(k.endswith('.lora_A') for k in changed)
            and any(k.endswith('.lora_B') for k in changed), 'Actual saved A/B updates must be independently visible')
    head = torch.load(checked(reg['old_head_ref'], w), map_location='cpu', weights_only=True)['weight']
    require(tensor_signature({'weight': head}) == accepted['head_signature'] == done['head_signature'], 'Original head53 changed')
    features = {}
    for rr in done['feature_refs']:
        row = readref(rr, w); uid = row['uid']; case = cases[uid]
        require(uid not in features and row['tag'] == 'final_' + uid and row['case_ref'] == accepted['case_refs'][uid]
                and row['source_sha256'] == case['source_sha256'] and row['input_signature'] == case['input_signature'], 'First final feature source/accepted input association differs')
        payload = torch.load(checked(row['feature_ref'], w), map_location='cpu', weights_only=True)
        require(payload['uid'] == uid and payload['source_sha256'] == case['source_sha256']
                and payload['input_signature'] == case['input_signature'] and payload['parameter_state_ref'] == done['final_adapter_ref'],
                'Durable final primary ownership or weight state differs')
        _, groups, _ = old.excerpt_shape(payload['video_grid_thw'], case['plan'])
        f, means = payload['feature'], payload['independent_group_means']
        require(f.dtype == means.dtype == torch.float32 and tuple(f.shape) == (4096,)
                and tuple(means.shape) == (groups, 4096) and bool(torch.isfinite(f).all()) and bool(torch.isfinite(means).all()),
                'Independent final feature/group/dtype geometry differs')
        torch.testing.assert_close(f, old.independent_pool(torch, means), atol=2e-5, rtol=1e-4)
        features[uid] = f.numpy().astype(float)
    require(len(features) == len(cases) == 100 and set(features) == set(cases), 'All100 first final outputs must pass independent CPU QA')
    import numpy as np
    training = readref(accepted['train_target_ref'], w)
    check = readref(a06['check_target_ref'], w)  # First held-out target read is here, after natural GPU completion.
    check = sorted(check, key=lambda q: hashlib.sha256(q['pair_id'].encode()).hexdigest())
    require(len(check) == 14 and len({q['source_id'] for q in check}) == 8
            and all(q['left'] not in accepted['train_uids'] and q['right'] not in accepted['train_uids'] for q in check),
            'Original14pairs8heldout sources required')
    xtrain = np.vstack([(features[q['left']] - features[q['right']]) / 64 for q in training])
    xcheck = np.vstack([(features[q['left']] - features[q['right']]) / 64 for q in check])
    weight = head.numpy()
    measured = dict(train=old.metric(np, training, xtrain, weight), check=old.metric(np, check, xcheck, weight),
                    permuted_content=old.metric(np, check, np.roll(xcheck, 1, axis=0), weight))
    original = readref(reg['old_review53_ref'], w)
    prior_LM = readref(reg['old_control12_ref'], w)['metrics']['SumMe']['check']
    require(prior_LM == original['prior_best_prefill_control'] and prior_LM['source_macro_accuracy'] == .625
            and abs(prior_LM['source_macro_brier'] - .110376784) < 5e-10, 'Exact original53/12 held-out control identity differs')
    real, perm = measured['check'], measured['permuted_content']; reasons = []
    if real['source_macro_accuracy'] < .75: reasons.append('REAL_ACCURACY_BELOW_POINT75')
    if real['source_macro_accuracy'] <= prior_LM['source_macro_accuracy']: reasons.append('NOT_BETTER_THAN_PRIOR_LM_CONTROL')
    if real['source_macro_brier'] >= prior_LM['source_macro_brier']: reasons.append('BRIER_NOT_BETTER_THAN_PRIOR_LM_CONTROL')
    if real['source_macro_accuracy'] <= perm['source_macro_accuracy'] or real['source_macro_brier'] >= perm['source_macro_brier']:
        reasons.append('CONTENT_PERMUTATION_CONTROL_NOT_SURPASSED')
    improved = [sid for sid in sorted({q['source_id'] for q in check})
        if np.mean([q['correct'] for q in real['rows'] if q['source_id'] == sid]) >
           np.mean([q['correct'] for q in prior_LM['rows'] if q['source_id'] == sid])]
    if len(improved) < 2: reasons.append('FEWER_THAN_TWO_SOURCES_IMPROVED')
    result = dict(status='STOP' if reasons else 'ELIGIBLE_FOR_TIME43', stop_reasons=reasons, metrics=measured,
        prior_fixed_vision53=original['metrics'], prior_best_prefill_control=prior_LM, improved_sources=improved,
        first_independent_output_QA='ALL100_NATIVE_GROUP_SOURCE_FP64_POOL_AND_SAVED_ADAPTER_PASS',
        actual_new_head_fits=0, fixed_head_ref=reg['old_head_ref'], final_adapter_ref=done['final_adapter_ref'],
        gpu_completion_ref=decision['gpu_completion_ref'], natural_resource_ref=decision['resource_ref'], unique_ledger='PASS',
        definition_ref=done['definition_ref'], original53_outputs_adopted=True, actual_visual_updates=18,
        language_updates=0, TIME_updates=0, merger_updates=0, historical_exposed=True,
        not_official_joint_truth=True, automatic_TIME43=False, production_admitted=False, new_ZIP=0, official_submissions=0)
    budget.save(n / 'review63.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', required=True)
    parser.add_argument('--phase', choices=['prepare', 'train', 'review'], required=True)
    args = parser.parse_args()
    if args.phase != 'train':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    try:
        print(json.dumps(globals()[args.phase](args.run_root), allow_nan=False))
    except BaseException:
        path = Path(args.run_root) / ('failure_' + args.phase + '63.json')
        if not path.exists():
            with path.open('x', encoding='utf-8') as stream:
                json.dump(dict(status='ACTUAL_FAILURE_PRESERVE_ALL_NO_AUTOMATIC_RETRY', phase=args.phase,
                    traceback=traceback.format_exc(), automatic_resume=False), stream, indent=2)
                stream.flush(); os.fsync(stream.fileno())
        raise

