"""Registered BASE-only + independent PAIR-r8 pilot/remaining experiment.

No old TIME adapter is loaded. Only train_targets contains supervision here;
dev inputs are read without reference labels. No implicit retry or resume.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
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
from pair_common import (WORK, RUN, read, save, sha, ref, bound, require, utc,
                         signature, registration, PairInputs, paths, append_event)


ADAPTER = 'pair'
BASE_PARAMETERS = 8767123696
PAIR_PARAMETERS = 7667712
OLD_TIME_PARAMETERS = 15335424
SEMANTIC_PARAMETERS = 98329
RECIPE = dict(updates=200, grad_accum=4, rank=8, alpha=16, dropout=0,
              lr=5e-5, weight_decay=0, grad_clip=1, seed=20261018)
TARGET = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$')
TRAINABLE = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.pair\.weight$')


def _sync_directory(path):
    descriptor = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _tensor_file(path, value, torch):
    """Persist a first raw result before any post-forward acceptance checks."""
    with Path(path).open('xb') as stream:
        torch.save(value, stream); stream.flush(); os.fsync(stream.fileno())
    _sync_directory(Path(path).parent)


def _atomic_progress(path, value, torch):
    temporary = path.with_name(path.name+'.pending')
    _tensor_file(temporary, value, torch)
    os.replace(temporary, path)
    _sync_directory(path.parent)


def _copy_exclusive(source, destination):
    with source.open('rb') as src, destination.open('xb') as dst:
        for block in iter(lambda: src.read(8 << 20), b''):
            dst.write(block)
        dst.flush(); os.fsync(dst.fileno())
    _sync_directory(destination.parent)


def _cpu_tree(value, torch):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().contiguous().clone()
    if isinstance(value, dict):
        return {k: _cpu_tree(v, torch) for k, v in value.items()}
    if isinstance(value, list):
        return [_cpu_tree(v, torch) for v in value]
    if isinstance(value, tuple):
        return tuple(_cpu_tree(v, torch) for v in value)
    return value


def _adapter_state(model, torch):
    from peft import get_peft_model_state_dict
    state = _cpu_tree(get_peft_model_state_dict(model, adapter_name=ADAPTER), torch)
    require(len(state) == 288 and all('lora_' in k for k in state), 'Only288 new PAIR matrices may be saved')
    return state


def _inventory(model, training, torch):
    trainable = []
    base_count = pair_count = 0
    for name, parameter in model.named_parameters():
        if 'lora_' in name:
            match = TRAINABLE.search(name)
            require(match is not None, 'Unexpected adapter tensor: '+name)
            require(parameter.ndim == 2 and (parameter.shape[0] if match[3] == 'A' else parameter.shape[1]) == 8,
                    'Actual PAIR rank differs')
            require(parameter.requires_grad == training, 'Actual PAIR trainability differs')
            pair_count += parameter.numel(); trainable.append((name, parameter))
        else:
            require(not parameter.requires_grad, 'BASE/vision/embedding/head became trainable')
            base_count += parameter.numel()
    layers = [(n, m) for n, m in model.named_modules() if hasattr(m, 'lora_A')]
    require(len(layers) == 144 and all(set(m.lora_A) == {ADAPTER} and not bool(m.disable_adapters)
              and list(m.active_adapters) == [ADAPTER] for _, m in layers), 'Exact144 active PAIR-only layers required')
    require(model.active_adapter == ADAPTER and len(trainable) == 288
            and base_count == BASE_PARAMETERS and pair_count == PAIR_PARAMETERS,
            'Actual BASE plus independent PAIR parameter inventory differs')
    conservative = base_count+pair_count+OLD_TIME_PARAMETERS+SEMANTIC_PARAMETERS
    require(conservative <= 9000000000, 'Conservative whole-pipeline parameter budget exceeded')
    return trainable, dict(base=base_count, pair=pair_count, resident=base_count+pair_count,
             conservative_pipeline=conservative, original_TIME_loaded=False,
             original_TIME_counted=OLD_TIME_PARAMETERS, semantic_counted=SEMANTIC_PARAMETERS,
             adapter=ADAPTER, actual_lora_matrices=288, actual_language_targets=144)


def _softmax3(logits, np):
    values = np.asarray(logits, dtype=np.float64)
    exponential = np.exp(values-values.max())
    return (exponential/exponential.sum()).tolist()


def _deadline(reg):
    if 'deadline_utc' in reg:
        import datetime as dt
        require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')),
                'No new model call after registered goal deadline')


def _prediction_stage(root, model, inputs, entries, role, torch, np, successful_raw):
    stage = root/'pair_model_17'/role; stage.mkdir(exist_ok=False)
    journal = stage/'attempts.jsonl'; journal.touch(exist_ok=False)
    require(len({e['id'] for e in entries}) == len(entries), 'Each dev request ID must occur once per model role')
    model.eval()
    require(not any(p.requires_grad for p in model.parameters()), 'Prediction role must be entirely frozen')
    aliases, completed = {}, []
    for index, entry in enumerate(entries):
        _deadline(inputs.reg)
        values, request = inputs.get(entry['input'])
        require(request['id'] == entry['id'] and request['source_id'] == entry['source_id'], 'Actual dev input identity differs')
        classes = request['class_token_ids']
        key = json.dumps(request['input_signature'], sort_keys=True, separators=(',', ':'))
        previous = aliases.get(key)
        raw_path = stage/('%04d.lastlogits.pt'%index)
        started = time.monotonic()
        if previous is None:
            gpu = {k: v.to('cuda') for k, v in values.items()}
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role=role)
            with torch.inference_mode():
                result = model(**gpu, use_cache=False, return_dict=True, logits_to_keep=1)
                raw = result.logits[0, -1].float().detach().cpu().contiguous()
            torch.cuda.synchronize()
            _tensor_file(raw_path, raw, torch)
            raw_reference = ref(raw_path)
            successful_raw.append(dict(id=entry['id'], model_role=role, raw_logits=raw_reference))
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_logits=raw_reference, model_role=role)
            del gpu, result
        else:
            require(classes == previous['classes'], 'An input alias has different classification token IDs')
            raw_reference = previous['raw_logits']
            raw = torch.load(bound(raw_reference), map_location='cpu', weights_only=True)
        # These checks deliberately follow first-raw persistence.
        require(raw.ndim == 1 and raw.dtype == torch.float32 and torch.isfinite(raw).all(), 'Finite full-vocabulary raw last logits required')
        require(len(classes) == len(set(classes)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in classes),
                'Actual3 distinct class IDs outside full raw vocabulary')
        three = raw[classes].numpy().astype(np.float64)
        probabilities = _softmax3(three, np)
        receipt_path = stage/('%04d.receipt.json'%index)
        receipt = dict(id=entry['id'], source_id=entry['source_id'], input=entry['input'], role=entry['role'],
             model_role=role, raw_logits=raw_reference, class_token_ids=classes, class_logits=three.tolist(),
             probabilities=probabilities, predicted_index=int(np.argmax(three)), full_vocabulary_size=len(raw),
             raw_dtype='torch.float32', input_signature=request['input_signature'],
             softmax_scope='Three class logits ONLY; not full-vocabulary probability or calibrated confidence',
             actual_new_forward=previous is None, alias_of=previous['receipt'] if previous else None,
             elapsed_seconds=time.monotonic()-started, dev_reference_read=False, original_TIME_loaded=False)
        save(receipt_path, receipt); receipt_reference = ref(receipt_path)
        if previous is None:
            aliases[key] = dict(classes=classes, raw_logits=raw_reference, receipt=receipt_reference)
        completed.append(dict(id=entry['id'], input=entry['input'], receipt=receipt_reference))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_reference,
                     alias=previous is not None, model_role=role)
        del values, raw
    completion = dict(status='COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY', model_role=role,
             entries=completed, actual_forward_calls=len(aliases), aliases=len(entries)-len(aliases),
             expected_inputs=len(entries), dev_reference_read=False, original_TIME_loaded=False)
    save(stage/'completion.json', completion)
    return ref(stage/'completion.json')


def _schedule(inputs):
    import numpy as np
    reference = inputs.prepared['train_targets']
    rows = read(bound(reference))
    ids = inputs.prepared['train_source_ids']
    require(len(ids) == len(set(ids)) == 20 and ids == sorted(ids), 'Fixed20 sorted train source IDs required')
    dev_ids = inputs.prepared['dev_source_ids']
    require(len(dev_ids) == len(set(dev_ids)) == 5 and not set(ids) & set(dev_ids), 'Exact disjoint20/5 source IDs required')
    require({r['source_id'] for r in inputs.prepared['dev_inputs']} == set(dev_ids),
            'Inference-only dev input identities differ from the registered five sources')
    require(len({r['id'] for r in rows}) == len(rows), 'Unique ordered train examples required')
    by_source = {sid: [] for sid in ids}
    for row in rows:
        require(row['source_id'] in by_source, 'Nontrain source appeared in supervised target file')
        p = np.asarray(row['target'], dtype=np.float64)
        require(p.shape == (3,) and np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
                and abs(float(p.sum())-1.) < 1e-12, 'Original all-rater3class soft target required')
        bound(row['input']); by_source[row['source_id']].append(row)
    for sid in ids:
        by_source[sid].sort(key=lambda r: r['id'])
        require(by_source[sid], 'Every registered train source needs actual ordered pairs')
    schedule = [by_source[ids[m % 20]][(m//20) % len(by_source[ids[m % 20]])] for m in range(800)]
    require(Counter(r['source_id'] for r in schedule) == {sid: 40 for sid in ids}, 'Exact40 draws per training source required')
    digest = hashlib.sha256(json.dumps([(r['source_id'], r['id'], r['input']['sha256']) for r in schedule],
                                    separators=(',', ':')).encode()).hexdigest()
    return schedule, digest, reference


def _progress(model, optimizer, torch, np, step, schedule_sha, targets_ref, recipe):
    numpy_state = np.random.get_state()
    return dict(schema='PAIR_R8_COMPLETE_UPDATE_PROGRESS_V1', adapter_state_dict=_adapter_state(model, torch),
         optimizer_state_dict=_cpu_tree(optimizer.state_dict(), torch), torch_rng_state=torch.get_rng_state(),
         torch_cuda_rng_state_all=[v.cpu() for v in torch.cuda.get_rng_state_all()],
         numpy_rng_state=dict(name=numpy_state[0], keys=torch.tensor(numpy_state[1].astype(np.int64)),
              position=int(numpy_state[2]), has_gauss=int(numpy_state[3]), cached_gaussian=float(numpy_state[4])),
         python_rng_state=random.getstate(), step=step, micro=step*4,
         schedule_sha256=schedule_sha, train_targets=targets_ref, recipe=recipe,
         original_TIME_loaded=False, no_base_tensors_saved=True)


def _restore_rng(state, torch, np):
    torch.set_rng_state(state['torch_rng_state'])
    torch.cuda.set_rng_state_all(state['torch_cuda_rng_state_all'])
    n = state['numpy_rng_state']
    np.random.set_state((n['name'], n['keys'].numpy().astype(np.uint32), n['position'], n['has_gauss'], n['cached_gaussian']))
    random.setstate(state['python_rng_state'])


def run(root, phase):
    require(phase in ('pilot', 'remaining') and bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Explicit actual GPU phase required')
    reg = registration(root); paths()
    gpu_registration = read(root/'pair_GPU_registration_18.json')
    require(bound(gpu_registration['GPU_code']) == Path(__file__).resolve(), 'Admitted GPU code is not the actual entry file')
    require(bound(gpu_registration['input_acceptance']) == (root/'pair_inputs_17/input_acceptance.json').resolve()
            and bound(gpu_registration['pair_registration']) == (root/'pair_registration_17.json').resolve(),
            'GPU admission must bind this exact original input QA and fixed pair registration')
    require(all(reg['train_recipe'].get(k) == v for k, v in RECIPE.items()), 'Fixed single PAIR training recipe changed')
    from sft_contract import verify_live_gpu_reservation, REVISION
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model, PeftModel, set_peft_model_state_dict
    from safetensors.torch import load_file
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Exact registered model runtime required')
    torch.set_num_threads(2)
    random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed']); torch.manual_seed(RECIPE['seed']); torch.cuda.manual_seed_all(RECIPE['seed'])
    inputs = PairInputs(root)
    cfg = read(bound(reg['model_config'])); old_time = bound(reg['old_TIME_weights'])
    require(sha(old_time) == cfg['b_adapter_sha256'] and cfg['base_parameters'] == BASE_PARAMETERS, 'Original BASE/TIME file binding differs')
    out = root/'pair_model_17'
    if phase == 'pilot':
        out.mkdir(exist_ok=False)
    else:
        require(out.is_dir(), 'A remaining stage needs the original pilot directory')
    save(out/(phase+'_claim.json'), dict(utc=utc(), pid=os.getpid(), phase=phase,
         registration=ref(root/'pair_registration_17.json'), input_acceptance=ref(root/'pair_inputs_17/input_acceptance.json'),
         GPU_registration=ref(root/'pair_GPU_registration_18.json'),
         model_role='BASE_ONLY_THEN_NEW_PAIR_R8; OLD_TIME_NOT_LOADED'))
    successful_raw = []; completed_step = 0; successful_micro = 0; progress_path = out/'train/progress.pt'
    try:
        pilot = None; resumed = None
        if phase == 'remaining':
            admission_path = root/'pair_remaining_admission_19.json'
            admission = read(admission_path); pilot = read(out/'pilot_completion.json')
            require(pilot['completed_updates'] == 4 and pilot['successful_micro'] == 16
                    and admission['progress'] == pilot['progress'], 'Only exact registered step4 progress may be adopted')
            checkpoint = bound(admission['progress'])
            require(sha(progress_path) == sha(checkpoint), 'Mutable progress advanced outside this explicit remaining stage')
            resumed = torch.load(checkpoint, map_location='cpu', weights_only=True)
            bound(pilot['BASE_completion'])
        schedule, schedule_sha, targets_ref = _schedule(inputs)
        _deadline(reg)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
             local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
             low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'BASE stage accidentally loaded an adapter')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == BASE_PARAMETERS and before['sha256'] == cfg['expected_base_sha256'], 'Actual original BASE fingerprint differs')
        save(out/(phase+'_base_identity.json'), dict(base=before, original_TIME_weights=reg['old_TIME_weights'],
             original_TIME_loaded=False, original_TIME_enabled=False))
        if phase == 'pilot':
            base_completion = _prediction_stage(root, base, inputs, inputs.prepared['dev_inputs'], 'BASE', torch, np, successful_raw)
            inputs.cache.clear()
        else:
            base_completion = pilot['BASE_completion']
        targets = [n for n, m in base.named_modules() if isinstance(m, torch.nn.Linear) and TARGET.search(n)]
        require(len(targets) == 144, 'Exactly144 language q/k/v/o targets required')
        # BASE inference never determines the new adapter's initialization RNG.
        random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed'])
        torch.manual_seed(RECIPE['seed']); torch.cuda.manual_seed_all(RECIPE['seed'])
        model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0., bias='none',
             target_modules=targets, task_type='CAUSAL_LM', modules_to_save=None), adapter_name=ADAPTER)
        for name, p in model.named_parameters(): p.requires_grad_(TRAINABLE.search(name) is not None)
        parameters, inventory = _inventory(model, True, torch)
        optimizer = torch.optim.AdamW([p for _, p in parameters], lr=5e-5, weight_decay=0.)
        start_step = 0
        if resumed is not None:
            require(resumed['step'] == 4 and resumed['micro'] == 16 and resumed['recipe'] == RECIPE
                    and resumed['schedule_sha256'] == schedule_sha and resumed['train_targets'] == targets_ref,
                    'Frozen source schedule/targets/recipe differ from original step4')
            set_peft_model_state_dict(model, resumed['adapter_state_dict'], adapter_name=ADAPTER)
            actual = _adapter_state(model, torch)
            require(set(actual) == set(resumed['adapter_state_dict']) and all(torch.equal(actual[k], v) for k, v in resumed['adapter_state_dict'].items()),
                    'Actual adopted step4 PAIR tensors differ')
            optimizer.load_state_dict(resumed['optimizer_state_dict'])
            _restore_rng(resumed, torch, np); start_step = 4
            completed_step, successful_micro = 4, 16
        train = out/'train'; train.mkdir(exist_ok=phase == 'remaining')
        initial = _adapter_state(model, torch)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.train()
        for name, module in model.named_modules():
            if name.endswith('.visual'): module.eval()
        _inventory(model, True, torch)
        micro_journal = train/(phase+'_micro_loss.jsonl'); micro_journal.touch(exist_ok=False)
        update_journal = train/(phase+'_updates.jsonl'); update_journal.touch(exist_ok=False)
        stop_step = 4 if phase == 'pilot' else 200
        for step in range(start_step+1, stop_step+1):
            optimizer.zero_grad(set_to_none=True); losses = []
            for micro in range((step-1)*4, step*4):
                _deadline(reg)
                row = schedule[micro]; values, request = inputs.get(row['input'])
                require(request['id'] == row['id'] and request['source_id'] == row['source_id'], 'Supervised input identity differs')
                gpu = {k: v.to('cuda') for k, v in values.items()}
                append_event(micro_journal, event='BEGIN_TRAIN_MICRO', step=step, micro=micro,
                             id=row['id'], source_id=row['source_id'], input=row['input'])
                result = model(**gpu, use_cache=False, return_dict=True, logits_to_keep=1)
                classes = request['class_token_ids']
                require(len(classes) == len(set(classes)) == 3 and all(type(k) is int and 0 <= k < result.logits.shape[-1] for k in classes),
                        'Actual training class IDs differ')
                logits = result.logits[0, -1, classes].float()
                target = torch.tensor(row['target'], dtype=torch.float32, device=logits.device)
                loss = -(target*torch.nn.functional.log_softmax(logits, dim=-1)).sum()
                value = float(loss.detach().cpu())
                append_event(micro_journal, event='TRAIN_RAW_LOSS', step=step, micro=micro, id=row['id'],
                             source_id=row['source_id'], loss=value if np.isfinite(value) else None, loss_repr=repr(value),
                             class_token_ids=classes, softmax_scope='THREE_CLASSES_ONLY')
                require(np.isfinite(value), 'Nonfinite real training loss')
                (loss/4).backward(); successful_micro = micro+1; losses.append(value)
                append_event(micro_journal, event='TRAIN_BACKWARD_COMPLETE', step=step, micro=micro, id=row['id'])
                del gpu, values, result, logits, target, loss
            gradients = [p.grad for _, p in parameters]
            require(all(g is not None and torch.isfinite(g).all() for g in gradients), 'Missing/nonfinite PAIR gradients')
            nonzero = sum(bool(torch.count_nonzero(g)) for g in gradients)
            gradient_norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in parameters], 1.).detach().cpu())
            require(np.isfinite(gradient_norm), 'Nonfinite real gradient norm')
            optimizer.step(); completed_step = step
            checkpoint = _progress(model, optimizer, torch, np, step, schedule_sha, targets_ref, RECIPE)
            _atomic_progress(progress_path, checkpoint, torch)
            append_event(update_journal, event='SUCCESSFUL_UPDATE_PERSISTED', step=step, micro=step*4,
                 mean_micro_loss=float(np.mean(losses)), preclip_gradient_norm=gradient_norm,
                 finite_gradient_matrices=len(gradients), nonzero_gradient_matrices=nonzero,
                 progress_sha256=sha(progress_path))
            _inventory(model, True, torch)
            require(all(torch.isfinite(v).all() for v in checkpoint['adapter_state_dict'].values()), 'PAIR weights became nonfinite after saved update')
        optimizer.zero_grad(set_to_none=True)
        model.eval(); model.gradient_checkpointing_disable()
        for p in model.parameters(): p.requires_grad_(False)
        _inventory(model, False, torch)
        final_state = _adapter_state(model, torch)
        require(any(not torch.equal(initial[k], final_state[k]) for k in initial), 'No actual PAIR update occurred')
        if phase == 'pilot':
            immutable = train/'pilot_progress.pt'; _copy_exclusive(progress_path, immutable)
            after = canonical_frozen_hash(model, torch)
            require(after == before and sha(old_time) == reg['old_TIME_weights']['sha256'], 'Frozen BASE/original TIME changed during pilot')
            save(out/'pilot_completion.json', dict(status='COMPLETE_FIXED4_ENGINEERING_UPDATES_NO_TRAINED_DEV',
                 completed_updates=4, successful_micro=16, progress=ref(immutable), BASE_completion=base_completion,
                 update_journal=ref(update_journal), micro_journal=ref(micro_journal), inventory=inventory,
                 base_fingerprint=after, schedule_sha256=schedule_sha, train_targets=targets_ref,
                 original_TIME_loaded=False, dev_reference_read=False, final_quality_checkpoint_selected=False))
            return
        adapter = train/'adapter'; adapter.mkdir(exist_ok=False)
        model.save_pretrained(adapter, safe_serialization=True, selected_adapters=[ADAPTER], save_embedding_layers=False)
        weights = list(adapter.rglob('adapter_model.safetensors'))
        require(len(weights) == 1, 'Exactly one final PAIR-only adapter artifact required')
        for file in adapter.rglob('*'):
            if file.is_file():
                with file.open('rb') as stream: os.fsync(stream.fileno())
        _sync_directory(adapter)
        weights = weights[0]; saved = load_file(str(weights), device='cpu')
        require(set(saved) == set(final_state) and all(torch.equal(saved[k], final_state[k]) for k in saved), 'Saved final200 PAIR differs from actual tensors')
        base = model.unload()
        for p in base.parameters(): p.requires_grad_(False)
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'Unloading PAIR left adapter tensors behind')
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name=ADAPTER, is_trainable=False).eval()
        for p in model.parameters(): p.requires_grad_(False)
        actual = _adapter_state(model, torch)
        require(set(actual) == set(final_state) and all(torch.equal(actual[k], final_state[k]) for k in actual), 'Readonly final200 PAIR reload differs')
        _inventory(model, False, torch); inputs.cache.clear()
        trained_completion = _prediction_stage(root, model, inputs, inputs.prepared['dev_inputs'], 'TRAINED', torch, np, successful_raw)
        after = canonical_frozen_hash(model, torch)
        require(after == before and sha(old_time) == reg['old_TIME_weights']['sha256'], 'Frozen BASE/original TIME changed during training/readout')
        save(out/'completion.json', dict(status='COMPLETE_FIXED_FINAL200_PAIR_COMPARISON_NOT_QUALITY',
             BASE_completion=base_completion, TRAINED_completion=trained_completion, pilot_completion=ref(out/'pilot_completion.json'),
             remaining_admission=ref(root/'pair_remaining_admission_19.json'), completed_updates=200, successful_micro=800,
             pilot_updates=4, remaining_updates=196, update_journal=ref(update_journal), micro_journal=ref(micro_journal),
             progress=ref(progress_path), adapter_weights=ref(weights), adapter_directory=str(weights.parent),
             adapter_reload_all288_exact=True, inventory=inventory, base_fingerprint=after,
             schedule_sha256=schedule_sha, train_targets=targets_ref, train_source_draws={s: 40 for s in inputs.prepared['train_source_ids']},
             actual_training_forwards=800, actual_training_forwards_this_phase=784,
             training_forwards_are_unique_inputs=False, unique_ordered_train_inputs=len({r['id'] for r in schedule}),
             original_TIME_loaded=False, original_TIME_unchanged=True, dev_reference_read=False,
             actual_quality_established=False, automatic_426=False, automatic_package=False))
    except BaseException as error:
        save(out/(phase+'_failure.json'), dict(error=repr(error), traceback=traceback.format_exc(),
             completed_updates=completed_step, successful_micro=successful_micro, successful_raw=successful_raw,
             last_progress=ref(progress_path) if progress_path.is_file() else None,
             preserve_all_success=True, do_not_repeat_success=True, automatic_resume=False,
             failure_is_not_empty=True, dev_reference_read=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=['pilot', 'remaining'], required=True)
    args = parser.parse_args()
    run(args.root, args.phase)
