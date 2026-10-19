"""Fresh utility-r8 continuous IoU gradients; no actions occur on import.

CLI --root ROOT --phase pilot4|remaining496. GPU55 registration binds this
entry/math, CPU55 prepared/gate, adopted44 train reader and31 screen reader,
original32/18 runtime/config and protected TIME/PAIR/CROP refs. Extra CPU-only
comparison/target refs are deliberately never opened here. Pilot has no dev
forward; remaining explicitly resumes immutable complete step4 through500.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature, paths, append_event
import utility_value_math_v55 as utility

ADAPTER = 'utility'
BASE = 8767123696
LORA = 7667712
PIPELINE = 8790229268
TARGET = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$')
TRAINABLE = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.utility\.weight$')
GPU_REFS = ('GPU_code', 'math_code', 'CPU_registration', 'prepared', 'input_acceptance',
    'gain_CPU_registration', 'gain_prepared', 'gain_input_acceptance', 'gain_reader_code', 'image_code',
    'screen_preparation_code', 'screen_prepared', 'screen_input_acceptance', 'original_GPU32',
    'original_GPU18', 'model_config', 'old_TIME', 'old_PAIR', 'old_CROP', 'protocol')


def module(reference, name):
    path = bound(reference); require(name not in sys.modules, 'Bound helper already imported under another identity')
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _registration(root, phase):
    path = root/'utility_value_GPU_registration_55.json'; reg = read(path)
    require(reg['schema'] == 'UTILITY_CONTINUOUS_IOU_GRADIENT_V55'
            and reg['recipe'] == utility.RECIPE, 'Exact fresh utility objective/recipe required')
    for key in GPU_REFS:
        bound(reg[key])  # Explicit GPU whitelist; never open CPU-only evaluation refs.
    require(bound(reg['GPU_code']) == Path(__file__).resolve()
            and bound(reg['math_code']) == Path(utility.__file__).resolve(), 'Exact utility55 source bytes')
    require(bound(reg['CPU_registration']) == (root/'utility_value_CPU_registration_55.json').resolve()
            and bound(reg['prepared']) == (root/'utility_value_inputs_55/prepared.json').resolve()
            and bound(reg['input_acceptance']) == (root/'utility_value_inputs_55/input_acceptance.json').resolve(),
            'New55 target compiler and adopted-input acceptance required')
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU'
            and gate['prepared'] == reg['prepared'] and gate['registration'] == reg['CPU_registration']
            and gate['adopted_gain_input_acceptance'] == reg['gain_input_acceptance']
            and gate['adopted_screen_input_acceptance'] == reg['screen_input_acceptance'],
            'Actual utility55 CPU gate must bind its own registration/prepared')
    old32 = read(bound(reg['original_GPU32'])); old18 = read(bound(reg['original_GPU18']))
    require(reg['model_config'] == old32['model_config'] and reg['old_TIME'] == old32['old_TIME']
            and reg['old_PAIR'] == old32['old_PAIR'] and old32['original_GPU18'] == reg['original_GPU18'],
            'Frozen physical BASE/TIME/runtime identities differ')
    for reference in old18['runtime_dependencies']:
        bound(reference)
    old17 = read(bound(old18['pair_registration']))
    for name, digest in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen17 runtime changed: '+name)
    frozen = module(old32['GPU_code'], '_utility55_frozen_gpu32')
    frozen._deadline(reg)
    admission, admission_ref = reg, ref(path)
    if phase == 'remaining496':
        p = root/'utility_value_remaining_admission_55.json'; admission = read(p); admission_ref = ref(p)
        require(admission['schema'] == 'UTILITY_CONTINUOUS_REMAINING496_V55'
                and admission['original_GPU_registration'] == ref(path)
                and all(admission[k] == reg[k] for k in ('GPU_code', 'math_code', 'prepared', 'input_acceptance'))
                and admission['expected_remaining_updates'] == 496, 'Explicit same-objective remaining496 admission')
        frozen._deadline(admission)
    return reg, admission, admission_ref, frozen


def _adapter_state(model, torch, frozen):
    from peft import get_peft_model_state_dict
    state = frozen._cpu_tree(get_peft_model_state_dict(model, adapter_name=ADAPTER), torch)
    require(len(state) == 288 and all('lora_' in n for n in state), 'Exact utility288 saved adapter matrices')
    return state


def _inventory(model, head, beta, training, torch):
    parameters = []; base_count = lora_count = 0
    for name, p in model.named_parameters():
        if 'lora_' in name:
            match = TRAINABLE.search(name)
            require(match is not None and p.ndim == 2
                    and (p.shape[0] if match[3] == 'A' else p.shape[1]) == 8
                    and p.requires_grad == training, 'Unexpected utility adapter/trainability: '+name)
            parameters.append((name, p)); lora_count += p.numel()
        else:
            require(not p.requires_grad, 'Frozen BASE/vision/embedding/LMhead became trainable')
            base_count += p.numel()
    layers = [m for m in model.modules() if hasattr(m, 'lora_A')]
    require(len(layers) == 144 and all(set(m.lora_A) == {ADAPTER} and not m.disable_adapters
            and list(m.active_adapters) == [ADAPTER] for m in layers)
            and model.active_adapter == ADAPTER and len(parameters) == 288
            and base_count == BASE and lora_count == LORA, 'One active fresh utility-only language adapter')
    require(head.bias is None and tuple(head.weight.shape) == (1, 4096) and head.weight.dtype == torch.float32
            and head.weight.requires_grad == training and tuple(beta.shape) == (11,)
            and beta.dtype == torch.float32 and beta.requires_grad == training, 'Exact float32 value/geometry trainability')
    return parameters, dict(base=BASE, utility_lora=LORA, value_head=4096, geometry_beta=11,
        trainable=LORA+4107, resident=BASE+LORA+4107, pipeline=PIPELINE,
        actual_lora_matrices=288, actual_language_targets=144, adapter=ADAPTER,
        original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False,
        original_TIME_counted=15335424, semantic_counted=98329)


def _names(parameters):
    return [[n.replace('.utility.', '.') for n, _ in parameters], ['head.weight'], ['geometry_beta']]


def _tree_equal(a, b, torch):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(
            a.cpu().contiguous().reshape(-1).view(torch.uint8), b.cpu().contiguous().reshape(-1).view(torch.uint8))
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(_tree_equal(a[k], b[k], torch) for k in a)
    if isinstance(a, (list, tuple)):
        return type(a) is type(b) and len(a) == len(b) and all(_tree_equal(x, y, torch) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def _trainables(model, head, beta, torch, frozen):
    return dict(adapter_state_dict=_adapter_state(model, torch, frozen),
        head_state_dict=frozen._cpu_tree(head.state_dict(), torch), geometry_beta=beta.detach().cpu().clone())


def _progress(model, head, beta, optimizer, torch, np, frozen, step, schedule_sha, prepared_ref, rms, names):
    state = {}  # The old CROP-specific adapter extractor is never called.
    numpy_state = np.random.get_state()
    state.update(_trainables(model, head, beta, torch, frozen))
    state.update(schema='UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55',
        optimizer_state_dict=frozen._cpu_tree(optimizer.state_dict(), torch),
        optimizer_parameter_names_by_group=names, optimizer_parameter_names_sha256=utility.digest(names),
        torch_rng_state=torch.get_rng_state(), torch_cuda_rng_state_all=[v.cpu() for v in torch.cuda.get_rng_state_all()],
        numpy_rng_state=dict(name=numpy_state[0], keys=torch.tensor(numpy_state[1].astype(np.int64)),
            position=int(numpy_state[2]), has_gauss=int(numpy_state[3]), cached_gaussian=float(numpy_state[4])),
        python_rng_state=random.getstate(), step=step, micro=step*4, logical_training_forwards=step*8,
        schedule_sha256=schedule_sha, train_schedule_reference=prepared_ref, recipe=utility.RECIPE,
        train_target_RMS=rms, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False,
        no_base_tensors_saved=True)
    return state


def _grad_groups(parameters, head, beta, torch):
    groups = dict(LoRA_A=[p for n, p in parameters if '.lora_A.' in n],
                  LoRA_B=[p for n, p in parameters if '.lora_B.' in n],
                  VALUE_HEAD=[head.weight], GEOMETRY_BETA=[beta])
    reports = {}
    for name, params in groups.items():
        gradients = [p.grad for p in params]
        require(bool(params) and all(g is not None for g in gradients), 'Missing actual utility gradient: '+name)
        finite = bool(torch.stack([torch.isfinite(g).all() for g in gradients]).all().item())
        nonzero = int(torch.stack([torch.count_nonzero(g) > 0 for g in gradients]).sum().item())
        norm = float(torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g.float()) for g in gradients])).item())
        reports[name] = dict(tensors=len(params), nonzero_tensors=nonzero, finite=finite, preclip_norm=norm)
        require(finite and np_isfinite(norm), 'Nonfinite actual utility gradient: '+name)
    return reports


def np_isfinite(value):
    import math
    return math.isfinite(value)


def _hidden(model, values, torch, training):
    core = model.get_base_model().model
    result = core(**values, use_cache=False, return_dict=True)
    hidden = result.last_hidden_state[0, -1, :]
    require(tuple(hidden.shape) == (4096,) and bool(torch.isfinite(hidden).all()), 'Actual last normalized4096 hidden')
    if training:
        require(torch.is_grad_enabled() and hidden.requires_grad and hidden.grad_fn is not None,
                'Utility hidden must retain real language-LoRA gradient path')
    return hidden


def _readers(root, reg, prepared, torch):
    component = module(reg['gain_reader_code'], '_utility55_gain_reader44')
    image = module(reg['image_code'], '_utility55_image31')
    old_prepared = read(bound(reg['gain_prepared'])); gate = read(bound(reg['gain_input_acceptance']))
    train = component.GainInputs(old_prepared, gate=gate, prepared_ref=reg['gain_prepared'],
        registration_ref=reg['gain_CPU_registration'], load_json=lambda r: read(bound(r)),
        load_tensor=lambda r: torch.load(bound(r), map_location='cpu', weights_only=True), image=image)
    screen_module = module(reg['screen_preparation_code'], '_utility55_screen_reader31')
    screen_gate = read(bound(reg['screen_input_acceptance']))
    require(screen_gate['status'] == 'PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA'
            and screen_gate['prepared'] == reg['screen_prepared'], 'Adopt exact old31 screen input QA')
    screen = screen_module.CropInputs(root)
    require(screen.prepared == read(bound(reg['screen_prepared']))
            and screen.prepared['screen_inputs'] == prepared['screen_inputs']
            and screen.prepared['class_token_ids'] == prepared['class_token_ids']
            and train.prepared['class_token_ids'] == prepared['class_token_ids'], 'Same old31/44 input identities/classes')
    return train, screen


def _ordered_screen(root, model, head, beta, inputs, entries, admission, original_reg, weights, value_weights,
                    frozen, torch, successful):
    stage = root/'utility_value_model_55/TRAINED_screen'; stage.mkdir(exist_ok=False)
    journal = stage/'attempts.jsonl'; journal.touch(exist_ok=False)
    require(len(entries) == len({e['id'] for e in entries}) == 240, 'Exact old240 ordered screen inputs')
    model.eval(); head.eval()
    require(not any(p.requires_grad for p in model.parameters()) and not head.weight.requires_grad and not beta.requires_grad,
            'Wholly frozen final utility inference')
    aliases, completed = {}, []
    for i, entry in enumerate(entries):
        frozen._deadline(admission); values, request = frozen._input(inputs, entry, torch, training=False)
        key = utility.digest(dict(source_id=request['source_id'], source_sha256=request['source_sha256'],
            class_token_ids=request['class_token_ids'], input_signature=request['input_signature']))
        prior = aliases.get(key); started = time.monotonic()
        if prior is None:
            gpu = {k:v.to('cuda:0') for k, v in values.items()}
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role='UTILITY_TRAINED_screen')
            frozen._deadline(admission)
            with torch.inference_mode():
                hidden = _hidden(model, gpu, torch, False)
                value = float(head(hidden.float()).reshape(()).cpu())
                raw = hidden.float().cpu().contiguous()
            raw_path = stage/('%04d.hidden.pt'%i); frozen._tensor_file(raw_path, raw, torch)
            raw_reference = ref(raw_path)
            successful.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'], raw_hidden=raw_reference))
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_hidden=raw_reference, model_role='UTILITY_TRAINED_screen')
            torch.cuda.synchronize(); del gpu, hidden
        else:
            raw_reference, value = prior['raw_hidden'], prior['head_value']
            raw = torch.load(bound(raw_reference), map_location='cpu', weights_only=True)
        require(raw.dtype == torch.float32 and raw.device.type == 'cpu' and tuple(raw.shape) == (4096,)
                and bool(torch.isfinite(raw).all()) and np_isfinite(value), 'Persisted finite hidden4096/GPU value')
        receipt_path = stage/('%04d.receipt.json'%i)
        save(receipt_path, dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=entry['input'], model_role='UTILITY_TRAINED_screen', raw_hidden=raw_reference,
            head_value=value, raw_dtype='torch.float32', dimension=4096, adapter_weights=weights, value_weights=value_weights,
            input_signature=request['input_signature'], image_grid_thw=request['image_grid_thw'],
            class_token_ids=request['class_token_ids'], actual_new_forward=prior is None,
            alias_of=prior['receipt'] if prior else None, elapsed_seconds=time.monotonic()-started,
            screen_reference_read=False, no_full_vocabulary_logits=True, original_TIME_loaded=False,
            old_PAIR_loaded=False, old_CROP_loaded=False))
        receipt_reference = ref(receipt_path)
        if prior is None:
            aliases[key] = dict(raw_hidden=raw_reference, head_value=value, receipt=receipt_reference)
        completed.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
                              input=entry['input'], receipt=receipt_reference))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_reference,
                     alias=prior is not None, model_role='UTILITY_TRAINED_screen')
        del raw, values
    frozen._deadline(admission)
    save(stage/'completion.json', dict(status='COMPLETE_UTILITY_ORDERED_HIDDEN_VALUES_NOT_QUALITY',
        model_role='UTILITY_TRAINED_screen', entries=completed, actual_forward_calls=len(aliases),
        aliases=len(entries)-len(aliases), expected_inputs=len(entries), attempts=ref(journal),
        GPU_registration=original_reg, adapter_weights=weights, value_weights=value_weights,
        screen_reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False))
    return ref(stage/'completion.json')


def run(root, phase):
    root = Path(root).resolve()
    require(root.is_relative_to(WORK) and phase in ('pilot4', 'remaining496') and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
            'Authorized Linux root, phase and physical GPU assignment required')
    reg, admission, admission_ref, frozen = _registration(root, phase); paths()
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model, PeftModel, set_peft_model_state_dict
    from safetensors.torch import load_file
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Frozen actual utility runtime')
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == admission['GPU_job'], 'Different actual shared GPU job')
    torch.set_num_threads(2)
    prepared = read(bound(reg['prepared'])); rows, schedule_sha, schedule_report = utility.validate_schedule(prepared)
    require(prepared['schedule_sha256'] == schedule_sha and prepared['screen_prepared'] == reg['screen_prepared']
            and prepared['screen_input_acceptance'] == reg['screen_input_acceptance'], 'Exact compiler schedule and adopted screen refs')
    rms = prepared['train_target_RMS']; names = None
    catalog = read(bound(prepared['source_catalog']))['sources']
    require(len(catalog) == len({s['source_id'] for s in catalog}) == 602
            and {s['source_id']:s['source_sha256'] for s in catalog} == {r['source_id']:r['source_sha256'] for r in rows}
            and all(s['role'] == 'train' for s in catalog), 'Exact602 train-only no-human source catalog')
    inputs, screen = _readers(root, reg, prepared, torch)
    require(not {r['source_id'] for r in rows} & {e['source_id'] for e in prepared['screen_inputs']}, 'No screen source in gradient table')
    out = root/'utility_value_model_55'
    if phase == 'pilot4':
        out.mkdir(exist_ok=False); (out/'train').mkdir()
    else:
        require(out.is_dir(), 'Remaining adopts original pilot namespace')
    save(out/(phase+'_claim.json'), dict(utc=utc(), pid=os.getpid(), phase=phase, GPU_admission=admission_ref,
        GPU_registration=ref(root/'utility_value_GPU_registration_55.json'), CPU_prepared=reg['prepared'],
        original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, screen_targets_read=False))
    progress_path = out/'train/progress.pt'; successful = []; completed_step = successful_micro = logical_forwards = 0
    started = time.monotonic(); torch.cuda.reset_peak_memory_stats()
    try:
        pilot = resumed = None
        if phase == 'remaining496':
            pilot = read(bound(admission['pilot_completion']))
            require(pilot['status'] == 'COMPLETE_FIXED4_UTILITY_ENGINEERING_NO_DEV_MODEL'
                    and pilot['completed_updates'] == 4 and pilot['successful_micro'] == 16 and pilot['actual_training_forwards'] == 32
                    and pilot['GPU_registration'] == ref(root/'utility_value_GPU_registration_55.json')
                    and pilot['progress'] == admission['immutable_pilot_progress']
                    and bound(pilot['progress']) == (out/'train/pilot_progress.pt').resolve()
                    and sha(progress_path) == pilot['progress']['sha256'], 'Only exact immutable complete step4 resumes')
            resumed = torch.load(bound(pilot['progress']), map_location='cpu', weights_only=True)
        random.seed(utility.RECIPE['seed']); np.random.seed(utility.RECIPE['seed'])
        torch.manual_seed(utility.RECIPE['seed']); torch.cuda.manual_seed_all(utility.RECIPE['seed'])
        cfg = read(bound(reg['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'':'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'Fresh BASE must not load old adapters')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == BASE and before['sha256'] == cfg['expected_base_sha256'], 'Original physical BASE bytes')
        targets = [n for n, m in base.named_modules() if isinstance(m, torch.nn.Linear) and TARGET.search(n)]
        require(len(targets) == 144, 'Exact144 language q/k/v/o targets')
        random.seed(utility.RECIPE['seed']); np.random.seed(utility.RECIPE['seed'])
        torch.manual_seed(utility.RECIPE['seed']); torch.cuda.manual_seed_all(utility.RECIPE['seed'])
        model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0., bias='none',
            target_modules=targets, task_type='CAUSAL_LM', modules_to_save=None), adapter_name=ADAPTER)
        for name, p in model.named_parameters(): p.requires_grad_(TRAINABLE.search(name) is not None)
        head = torch.nn.Linear(4096, 1, bias=False, device='cuda:0', dtype=torch.float32)
        generator = torch.Generator(device='cuda:0').manual_seed(utility.RECIPE['seed'])
        with torch.no_grad(): head.weight.normal_(0., .001, generator=generator)
        beta = torch.nn.Parameter(torch.zeros(11, device='cuda:0', dtype=torch.float32))
        parameters, inventory = _inventory(model, head, beta, True, torch); names = _names(parameters)
        require(set(names[0]) == set(_adapter_state(model, torch, frozen)), 'Adam LoRA names must match standard PEFT state keys')
        optimizer = torch.optim.AdamW([dict(params=[p for _, p in parameters], lr=5e-5),
            dict(params=[head.weight], lr=.001), dict(params=[beta], lr=.001)], weight_decay=0.)
        if resumed is None:
            initial = _trainables(model, head, beta, torch, frozen)
            frozen._tensor_file(out/'train/initial_trainables.pt', initial, torch)
            initial_ref = ref(out/'train/initial_trainables.pt')
        else:
            require(resumed['schema'] == 'UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55'
                    and resumed['step'] == 4 and resumed['micro'] == 16 and resumed['logical_training_forwards'] == 32
                    and resumed['recipe'] == utility.RECIPE and resumed['schedule_sha256'] == schedule_sha
                    and resumed['train_schedule_reference'] == reg['prepared'] and resumed['train_target_RMS'] == rms
                    and resumed['optimizer_parameter_names_by_group'] == names
                    and resumed['optimizer_parameter_names_sha256'] == utility.digest(names), 'Exact step4 full optimizer/target contract')
            set_peft_model_state_dict(model, resumed['adapter_state_dict'], adapter_name=ADAPTER)
            head.load_state_dict(resumed['head_state_dict'])
            with torch.no_grad(): beta.copy_(resumed['geometry_beta'].to(beta.device))
            require(_tree_equal(_trainables(model, head, beta, torch, frozen),
                {k:resumed[k] for k in ('adapter_state_dict', 'head_state_dict', 'geometry_beta')}, torch), 'All step4 trainables exact restore')
            optimizer.load_state_dict(resumed['optimizer_state_dict'])
            require(_tree_equal(frozen._cpu_tree(optimizer.state_dict(), torch), resumed['optimizer_state_dict'], torch), 'All3 Adam groups exact restore')
            initial_ref = pilot['initial_trainables']; initial = torch.load(bound(initial_ref), map_location='cpu', weights_only=True)
            frozen._restore_rng(resumed, torch, np)
            completed_step, successful_micro, logical_forwards = 4, 16, 32
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False}); model.train()
        for name, m in model.named_modules():
            if name.endswith('.visual'): m.eval()
        _inventory(model, head, beta, True, torch)
        micro_journal = out/'train'/(phase+'_micro_loss.jsonl'); micro_journal.touch(exist_ok=False)
        update_journal = out/'train'/(phase+'_updates.jsonl'); update_journal.touch(exist_ok=False)
        for step in utility.phase_steps(phase):
            optimizer.zero_grad(set_to_none=True); losses = []
            for micro in range((step-1)*4, step*4):
                frozen._deadline(admission); row = rows[micro]
                forward, fr = frozen._input(inputs, row['forward'], torch, training=False)
                reverse, rr = frozen._input(inputs, row['reverse'], torch, training=False)
                require(fr['candidate_indices'] == [row['a'], row['b']] and rr['candidate_indices'] == [row['b'], row['a']]
                        and fr['source_sha256'] == rr['source_sha256'] == row['source_sha256'], 'Compiled target order matches actual AB/BA')
                append_event(micro_journal, event='BEGIN_TRAIN_MICRO', step=step, micro=micro, id=row['id'],
                    forward_id=fr['id'], reverse_id=rr['id'], source_id=row['source_id'],
                    forward_input=row['forward']['input'], reverse_input=row['reverse']['input'])
                gpu_f = {k:v.to('cuda:0') for k, v in forward.items()}; gpu_r = {k:v.to('cuda:0') for k, v in reverse.items()}
                frozen._deadline(admission); hf = _hidden(model, gpu_f, torch, True); logical_forwards += 1
                frozen._deadline(admission); hr = _hidden(model, gpu_r, torch, True); logical_forwards += 1
                geometry = torch.tensor(row['geometry_delta11'], dtype=torch.float32, device='cuda:0')
                prediction = utility.prediction(head, hf, hr, beta, geometry)
                loss = utility.loss(prediction, row['target'], row['draw_weight'], rms)
                value, predicted = float(loss.detach().cpu()), float(prediction.detach().cpu())
                append_event(micro_journal, event='TRAIN_RAW_LOSS', step=step, micro=micro, id=row['id'],
                    forward_id=fr['id'], reverse_id=rr['id'], source_id=row['source_id'], target=row['target'],
                    draw_weight=row['draw_weight'], target_RMS=rms, prediction=predicted if np_isfinite(predicted) else None,
                    loss=value if np_isfinite(value) else None, loss_repr=repr(value), hidden_retained_real_gradient=True)
                require(np_isfinite(value) and np_isfinite(predicted), 'Finite actual normalized utility gain loss')
                (loss/4).backward(); successful_micro = micro+1; losses.append(value)
                append_event(micro_journal, event='TRAIN_BACKWARD_COMPLETE', step=step, micro=micro, id=row['id'])
                del forward, reverse, gpu_f, gpu_r, hf, hr, geometry, prediction, loss
            groups = _grad_groups(parameters, head, beta, torch)
            if 2 <= step <= 4:
                require(all(r['nonzero_tensors'] > 0 and r['preclip_norm'] > 0 for r in groups.values()), 'Pilot2..4 requires each gradient group active')
            norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in parameters]+[head.weight, beta], 1.).detach().cpu())
            require(np_isfinite(norm) and norm > 0, 'Finite nonzero combined utility gradient')
            frozen._deadline(admission)
            optimizer.step(); completed_step = step
            checkpoint = _progress(model, head, beta, optimizer, torch, np, frozen, step, schedule_sha, reg['prepared'], rms, names)
            require(all(bool(torch.isfinite(v).all()) for v in checkpoint['adapter_state_dict'].values())
                    and bool(torch.isfinite(checkpoint['head_state_dict']['weight']).all())
                    and bool(torch.isfinite(checkpoint['geometry_beta']).all()), 'Finite persisted complete utility update')
            frozen._atomic_progress(progress_path, checkpoint, torch)
            append_event(update_journal, event='SUCCESSFUL_UPDATE_PERSISTED', step=step, micro=step*4,
                mean_micro_loss=float(np.mean(losses)), grad_groups=groups,
                combined_preclip_gradient_norm=norm, progress=ref(progress_path))
            _inventory(model, head, beta, True, torch)
        optimizer.zero_grad(set_to_none=True); model.eval(); model.gradient_checkpointing_disable()
        for p in model.parameters(): p.requires_grad_(False)
        head.requires_grad_(False); beta.requires_grad_(False)
        _inventory(model, head, beta, False, torch)
        final = _trainables(model, head, beta, torch, frozen)
        changed_a = sum(not torch.equal(v, initial['adapter_state_dict'][k]) for k, v in final['adapter_state_dict'].items() if '.lora_A.' in k)
        changed_b = sum(not torch.equal(v, initial['adapter_state_dict'][k]) for k, v in final['adapter_state_dict'].items() if '.lora_B.' in k)
        head_changed = not _tree_equal(final['head_state_dict'], initial['head_state_dict'], torch)
        beta_changed = not _tree_equal(final['geometry_beta'], initial['geometry_beta'], torch)
        require(changed_a > 0 and changed_b > 0 and head_changed and beta_changed, 'All new utility parameter groups must actually update')
        after = canonical_frozen_hash(model, torch)
        require(after == before, 'Frozen BASE/vision bytes changed')
        for key in ('old_TIME', 'old_PAIR', 'old_CROP'): bound(reg[key])
        frozen._deadline(admission)
        common = dict(GPU_registration=ref(root/'utility_value_GPU_registration_55.json'),
            remaining_admission=admission_ref if phase == 'remaining496' else None,
            pilot_completion=admission['pilot_completion'] if phase == 'remaining496' else None,
            completed_updates=completed_step, successful_micro=successful_micro, actual_training_forwards=logical_forwards,
            actual_training_forwards_this_phase=32 if phase == 'pilot4' else 3968,
            initial_trainables=initial_ref, update_journal=ref(update_journal), gradient_journal=ref(update_journal),
            micro_journal=ref(micro_journal), inventory=inventory, base_fingerprint=after,
            recipe=utility.RECIPE, train_target_RMS=rms, schedule_sha256=schedule_sha,
            train_schedule_reference=reg['prepared'], schedule_report=schedule_report,
            optimizer_parameter_names_by_group=names, optimizer_parameter_names_sha256=utility.digest(names),
            actual_lora_A_changed=changed_a > 0, actual_lora_B_changed=changed_b > 0,
            changed_lora_A_tensors=changed_a, changed_lora_B_tensors=changed_b,
            head_changed=head_changed, beta_changed=beta_changed, original_TIME_loaded=False,
            old_PAIR_loaded=False, old_CROP_loaded=False, screen_reference_read=False,
            automatic_confirm=False, automatic_production=False)
        if phase == 'pilot4':
            immutable = out/'train/pilot_progress.pt'; frozen._copy_exclusive(progress_path, immutable)
            save(out/'pilot_completion.json', dict(status='COMPLETE_FIXED4_UTILITY_ENGINEERING_NO_DEV_MODEL',
                progress=ref(immutable), seconds=time.monotonic()-started,
                peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
                peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20, dev_model_forwards=0, **common))
            return
        adapter = out/'train/adapter'; adapter.mkdir(exist_ok=False)
        model.save_pretrained(adapter, safe_serialization=True, selected_adapters=[ADAPTER], save_embedding_layers=False)
        weight_paths = list(adapter.rglob('adapter_model.safetensors'))
        require(len(weight_paths) == 1 and weight_paths[0].parent == adapter/'utility', 'Only final utility adapter saved')
        for file in adapter.rglob('*'):
            if file.is_file():
                with file.open('rb') as stream: os.fsync(stream.fileno())
        frozen._sync_directory(adapter/'utility'); frozen._sync_directory(adapter)
        weight_path = weight_paths[0]; saved = load_file(str(weight_path), device='cpu')
        require(frozen._same_state(saved, final['adapter_state_dict'], torch), 'Final utility adapter save exact')
        value_path = out/'train/value_head.pt'
        frozen._tensor_file(value_path, dict(weight=final['head_state_dict']['weight'], geometry_beta=final['geometry_beta']), torch)
        value_saved = torch.load(value_path, map_location='cpu', weights_only=True)
        base = model.unload()
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'Unloaded BASE retained old utility matrices')
        for p in base.parameters(): p.requires_grad_(False)
        model = PeftModel.from_pretrained(base, str(weight_path.parent), adapter_name=ADAPTER, is_trainable=False).eval()
        for p in model.parameters(): p.requires_grad_(False)
        head.load_state_dict(dict(weight=value_saved['weight']))
        with torch.no_grad(): beta.copy_(value_saved['geometry_beta'].to(beta.device))
        require(_tree_equal(_trainables(model, head, beta, torch, frozen), final, torch), 'Complete final utility model save/reload exact')
        _inventory(model, head, beta, False, torch)
        weights, value_weights = ref(weight_path), ref(value_path)
        trained = _ordered_screen(root, model, head, beta, screen, prepared['screen_inputs'], admission,
            ref(root/'utility_value_GPU_registration_55.json'), weights, value_weights, frozen, torch, successful)
        require(_tree_equal(_trainables(model, head, beta, torch, frozen), final, torch)
                and canonical_frozen_hash(model, torch) == before, 'Readonly final screen changed physical model')
        for key in ('old_TIME', 'old_PAIR', 'old_CROP'): bound(reg[key])
        frozen._deadline(admission)
        save(out/'completion.json', dict(status='COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY',
            adapter_weights=weights, value_weights=value_weights, adapter_directory=str(weight_path.parent),
            adapter_reload_all288_exact=True, head_reload_exact=True, beta_reload_exact=True,
            TRAINED_completion=trained, progress=ref(progress_path), seconds=time.monotonic()-started,
            peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20, **common))
    except BaseException as error:
        save(out/(phase+'_failure.json'), dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            completed_updates=completed_step, successful_micro=successful_micro, actual_training_forwards=logical_forwards,
            successful_raw=successful, last_progress=ref(progress_path) if progress_path.is_file() else None,
            preserve_all_success=True, automatic_retry=False, failure_is_not_empty=True,
            automatic_confirm=False, automatic_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=['pilot4', 'remaining496'], required=True)
    args = parser.parse_args(); run(args.root, args.phase)
