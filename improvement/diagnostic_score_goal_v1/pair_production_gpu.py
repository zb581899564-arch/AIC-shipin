"""Conditional one-role production inference; no training or implicit admission.

CPU preparation21 and independent GPU admission22 remain separate immutable
artifacts. This file never calls an old stage or writes pair_model_17.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature, paths, append_event


def _load_module(reference, name):
    file = bound(reference)
    require(name not in sys.modules, 'Production helpers already imported through another path')
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def _registration(root):
    path = root/'pair_production_GPU_admission_22.json'
    reg = read(path)
    require(reg['schema'] == 'EXPLICIT_FROZEN_PAIR_PRODUCTION_GPU_V22'
            and reg['production_admitted'] is True and reg['role'] in ('BASE', 'TRAINED'),
            'This exact production role has not been explicitly admitted')
    require(bound(reg['GPU_code']) == Path(__file__).resolve(), 'Admitted production GPU code is not this entry file')
    production_reg = read(bound(reg['production_registration']))
    require(bound(reg['production_registration']) == (root/'pair_production_registration_21.json').resolve(),
            'GPU22 must bind the actual frozen CPU21 registration')
    quality = read(bound(reg['quality']))
    require(quality['production_prepare_approved'] is True and quality['model_role'] == reg['role'],
            'Quality admission does not support this exact model role')
    bound(reg['baseline_40_47'])
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_ALL426_NEW_TWO_VIDEO_PRODUCTION_INPUTS'
            and gate['sources'] == 426
            and gate['registration'] == reg['production_registration'], 'All426 first production input QA must pass first')
    prepared = read(bound(gate['prepared']))
    require(reg['baseline_40_47'] == production_reg['protected_baseline'] == gate['protected_baseline'] == prepared['protected_baseline']
            and reg['quality'] == production_reg['approved_quality']
            and reg['model_config'] == production_reg['model_config'], 'Production baseline/quality/model refs are not one frozen chain')
    require(gate['inputs'] == len(prepared['dev_inputs']) and prepared['no_train_targets'] is True
            and prepared['reference_labels_read'] is False, 'Exact label-free accepted production input set required')
    old18 = read(bound(reg['frozen_GPU_registration18']))
    for reference in old18['runtime_dependencies']:
        bound(reference)
    old17 = read(bound(old18['pair_registration']))
    require(reg['oldTIME'] == old17['old_TIME_weights'] and reg['model_config'] == old17['model_config'],
            'Production original BASE/TIME bindings differ from the frozen experiment')
    for reference in old17['old_helpers']:
        bound(reference)
    for name, digest in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen17 helper changed: '+name)
    bound(reg['oldTIME']); bound(reg['model_config'])
    trained = read(bound(reg['training_completion']))
    require(trained['status'] == 'COMPLETE_FIXED_FINAL200_PAIR_COMPARISON_NOT_QUALITY'
            and trained['completed_updates'] == 200 and trained['successful_micro'] == 800,
            'Only the completed fixed200 experiment may support production')
    if reg['role'] == 'TRAINED':
        require(trained['adapter_reload_all288_exact'] is True and reg['adapter_weights'] == trained['adapter_weights'],
                'TRAINED must use the exact independently reloaded final200 PAIR artifact')
        weights = bound(reg['adapter_weights']); directory = Path(reg['adapter_directory']).resolve()
        require(directory.is_relative_to(WORK) and directory == weights.parent
                and weights.name == 'adapter_model.safetensors', 'Actual final200 adapter directory/weights differ')
    return reg, production_reg, gate, prepared, old18


def _source_inventory(prepared):
    sources = prepared['sources']; entries = prepared['dev_inputs']
    require(len(sources) == 426 and len({s['id'] for s in sources}) == 426, 'All426 source dispositions must be explicit')
    ids = {s['id'] for s in sources}
    expected = {}
    for source in sources:
        require(bool(source['source_sha256']) and 'status' in source and 'inventory' in source,
                'Every source needs its original identity and legal policy disposition')
        for candidate in source['candidates']:
            for case_id in (candidate['first_id'], candidate['reverse_id']):
                require(case_id not in expected or expected[case_id] == source['id'], 'A production request is assigned to different source identities')
                expected[case_id] = source['id']
    require(len({e['id'] for e in entries}) == len(entries) and {e['id'] for e in entries} == set(expected)
            and all(e['source_id'] in ids and e['source_id'] == expected[e['id']] for e in entries),
            'Production inference inputs do not match all frozen policy pairs and source owners')
    require(entries, 'No eligible production comparisons: all-abstain preparation needs no GPU inference')
    return dict(total_sources=426, inference_inputs=len(entries),
                candidate_pairs=sum(len(s['candidates']) for s in sources),
                sources_with_candidates=sum(bool(s['candidates']) for s in sources),
                source_status_counts={status: sum(s['status'] == status for s in sources)
                                      for status in sorted({s['status'] for s in sources})})


def run(root):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Production child must retain its physical GPU assignment')
    reg, production_reg, gate, prepared, old18 = _registration(root)
    helper = _load_module(old18['GPU_code'], '_frozen_pair_GPU18_production_helpers'); paths()
    helper._deadline(reg)
    from sft_contract import verify_live_gpu_reservation, REVISION
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    active = read(WORK/'improvement_round1/active_gpu_job.json')
    require(active['name'] == reg['GPU_job'], 'Shared wrapper reservation belongs to another job')
    preparation = _load_module(production_reg['code'], '_frozen_pair_production21_inputs')
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Frozen production runtime changed')
    torch.set_num_threads(2)
    inputs = preparation.ProductionInputs(root)
    require(inputs.reg == production_reg and inputs.prepared == prepared,
            'Actual production loader is not using the GPU-admitted CPU21 evidence')
    inventory_sources = _source_inventory(prepared)
    source_hashes = {s['id']: s['source_sha256'] for s in prepared['sources']}
    role = reg['role']; out = root/'pair_production_21'/role; out.mkdir(parents=True, exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), pid=os.getpid(), GPU_admission=ref(root/'pair_production_GPU_admission_22.json'),
         production_registration=reg['production_registration'], input_acceptance=reg['input_acceptance'],
         quality=reg['quality'], baseline_40_47=reg['baseline_40_47'], model_role=role,
         training_completion=reg['training_completion'], original_TIME_loaded=False, sources=inventory_sources))
    successful_raw, completed = [], []
    attempts = out/'attempts.jsonl'; attempts.touch(exist_ok=False)
    started = time.monotonic()
    try:
        cfg = read(bound(reg['model_config'])); old_time = bound(reg['oldTIME'])
        require(sha(old_time) == cfg['b_adapter_sha256'] and cfg['base_parameters'] == helper.BASE_PARAMETERS,
                'Original BASE/TIME byte binding differs')
        helper._deadline(reg)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
             local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
             low_cpu_mem_usage=True, attn_implementation='sdpa')
        for parameter in base.parameters(): parameter.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'Production BASE unexpectedly includes an adapter')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == helper.BASE_PARAMETERS and before['sha256'] == cfg['expected_base_sha256'],
                'Actual original BASE fingerprint differs')
        expected_adapter = None
        if role == 'TRAINED':
            weights = bound(reg['adapter_weights'])
            expected_adapter = load_file(str(weights), device='cpu')
            model = PeftModel.from_pretrained(base, reg['adapter_directory'], adapter_name=helper.ADAPTER,
                                             is_trainable=False).eval()
            for parameter in model.parameters(): parameter.requires_grad_(False)
            _, parameter_inventory = helper._inventory(model, False, torch)
            actual_adapter = helper._adapter_state(model, torch)
            require(set(actual_adapter) == set(expected_adapter) and all(torch.equal(actual_adapter[k], v)
                    for k, v in expected_adapter.items()), 'Actual final200 readonly PAIR differs before production')
        else:
            model = base
            require(sum(p.numel() for p in model.parameters()) == helper.BASE_PARAMETERS, 'Actual BASE-only inventory differs')
            parameter_inventory = dict(base=helper.BASE_PARAMETERS, pair=0, resident=helper.BASE_PARAMETERS,
                 conservative_pipeline=helper.BASE_PARAMETERS+helper.PAIR_PARAMETERS+helper.OLD_TIME_PARAMETERS+helper.SEMANTIC_PARAMETERS,
                 pair_component_counted=helper.PAIR_PARAMETERS, original_TIME_counted=helper.OLD_TIME_PARAMETERS,
                 semantic_counted=helper.SEMANTIC_PARAMETERS, original_TIME_loaded=False, adapter=None)
        require(parameter_inventory['conservative_pipeline'] == 8790225161
                and parameter_inventory['conservative_pipeline'] <= 9000000000
                and not any(p.requires_grad for p in model.parameters()), 'Frozen whole-pipeline inventory differs')
        save(out/'model_identity.json', dict(model_role=role, base=before, inventory=parameter_inventory,
             frozen_GPU18=reg['frozen_GPU_registration18'], original_TIME=reg['oldTIME'],
             adapter_weights=reg['adapter_weights'] if role == 'TRAINED' else None,
             original_TIME_loaded=False, no_training=True))
        aliases = {}
        for index, entry in enumerate(prepared['dev_inputs']):
            helper._deadline(reg)
            values, request = inputs.get(entry['input'])
            require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
                    and request['source_sha256'] == source_hashes[entry['source_id']]
                    and set(values) == {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}
                    and signature(values) == request['input_signature'], 'Actual production request/token/pixel signature differs')
            classes = request['class_token_ids']
            key = json.dumps(request['input_signature'], sort_keys=True, separators=(',', ':'))
            previous = aliases.get(key); one = time.monotonic()
            if previous is None:
                gpu = {k: v.to('cuda') for k, v in values.items()}
                append_event(attempts, event='BEGIN_FIRST_PRODUCTION_FORWARD', id=entry['id'], input=entry['input'], model_role=role)
                with torch.inference_mode():
                    output = model(**gpu, use_cache=False, return_dict=True, logits_to_keep=1)
                    raw = output.logits[0, -1].float().detach().cpu().contiguous()
                torch.cuda.synchronize()
                raw_path = out/('%05d.lastlogits.pt'%index)
                helper._tensor_file(raw_path, raw, torch)
                raw_reference = ref(raw_path)
                successful_raw.append(dict(id=entry['id'], source_id=entry['source_id'],
                                           source_sha256=request['source_sha256'], raw_logits=raw_reference))
                append_event(attempts, event='FIRST_PRODUCTION_RAW_PERSISTED', id=entry['id'], raw_logits=raw_reference, model_role=role)
                del gpu, output
            else:
                require(classes == previous['classes'], 'Exact input alias has different class IDs')
                raw_reference = previous['raw_logits']
                raw = torch.load(bound(raw_reference), map_location='cpu', weights_only=True)
            # Every successful first forward is already durable before these checks.
            require(raw.ndim == 1 and raw.dtype == torch.float32 and torch.isfinite(raw).all(), 'Finite full-vocabulary production logits required')
            require(len(classes) == len(set(classes)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in classes),
                    'Actual production0/1/2 class mapping differs')
            three = raw[classes].numpy().astype(np.float64)
            probabilities = helper._softmax3(three, np)
            receipt_path = out/('%05d.receipt.json'%index)
            save(receipt_path, dict(id=entry['id'], source_id=entry['source_id'], source_sha256=request['source_sha256'],
                 input=entry['input'], role=entry['role'],
                 model_role=role, raw_logits=raw_reference, class_token_ids=classes, class_logits=three.tolist(),
                 probabilities=probabilities, predicted_index=int(np.argmax(three)), full_vocabulary_size=len(raw),
                 raw_dtype='torch.float32', input_signature=request['input_signature'],
                 softmax_scope='Three class logits ONLY; uncalibrated fixed heuristic', actual_new_forward=previous is None,
                 alias_of=previous['receipt'] if previous else None, elapsed_seconds=time.monotonic()-one,
                 labels_read=False, original_TIME_loaded=False, new_optimizer_updates=0))
            receipt_reference = ref(receipt_path)
            if previous is None:
                aliases[key] = dict(classes=classes, raw_logits=raw_reference, receipt=receipt_reference)
            completed.append(dict(id=entry['id'], input=entry['input'], receipt=receipt_reference))
            append_event(attempts, event='ACCEPTED_FIRST_PRODUCTION_RESULT', id=entry['id'], receipt=receipt_reference,
                         model_role=role, alias=previous is not None)
            del values, raw
        if role == 'TRAINED':
            helper._inventory(model, False, torch)
            actual_adapter = helper._adapter_state(model, torch)
            require(all(torch.equal(actual_adapter[k], v) for k, v in expected_adapter.items())
                    and sha(bound(reg['adapter_weights'])) == reg['adapter_weights']['sha256'],
                    'Final200 PAIR bytes changed during production')
        else:
            require(not any('lora_' in n for n, _ in model.named_parameters()), 'BASE-only role changed during production')
        after = canonical_frozen_hash(model, torch)
        require(after == before and sha(old_time) == reg['oldTIME']['sha256']
                and not any(p.requires_grad for p in model.parameters()), 'Frozen BASE/original TIME changed during production')
        save(out/'completion.json', dict(status='COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY', model_role=role,
             entries=completed, actual_forward_calls=len(aliases), aliases=len(completed)-len(aliases),
             expected_inputs=len(prepared['dev_inputs']), total_sources=426, source_inventory=inventory_sources,
             production_registration=reg['production_registration'], GPU_admission=ref(root/'pair_production_GPU_admission_22.json'),
             input_acceptance=reg['input_acceptance'], quality=reg['quality'], baseline_40_47=reg['baseline_40_47'],
             training_completion=reg['training_completion'], model_identity=ref(out/'model_identity.json'),
             base_fingerprint=after, inventory=parameter_inventory, adapter_all288_unchanged=role == 'TRAINED',
             original_TIME_loaded=False, original_TIME_unchanged=True, labels_read=False, new_optimizer_updates=0,
             elapsed_seconds=time.monotonic()-started, automatic_QA_or_package=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), successful_raw=successful_raw,
             completed_receipts=completed, preserve_all_success=True, do_not_repeat_success=True,
             failure_is_not_empty=True, automatic_resume=False, model_role=role, labels_read=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); run(args.root)
