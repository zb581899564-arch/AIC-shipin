"""Frozen BASE/PAIR200 source-overview pilot only: no training or continuation.

Every newly returned full-vocabulary logit vector is persisted before acceptance
checks. This entry imports only frozen18 utility helpers; it never invokes an old
prediction stage, reads evaluation targets, or writes the old pair_model_17.
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


ROLES = ('BASE_TRUE', 'PAIR_TRUE', 'PAIR_FOREIGN')
COUNTS = {'BASE_TRUE': 45, 'PAIR_TRUE': 45, 'PAIR_FOREIGN': 40}
PIPELINE_PARAMETERS = 8790225161


def _load_module(reference, name):
    file = bound(reference)
    require(name not in sys.modules, 'Frozen context helper name already loaded from another path')
    spec = importlib.util.spec_from_file_location(name, file)
    require(spec is not None and spec.loader is not None, 'Frozen helper cannot be imported')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _registration(root):
    reg = read(root/'context_GPU_registration_29.json')
    require(reg['schema'] == 'FROZEN_PAIR200_SOURCE_OVERVIEW_PILOT_V29'
            and reg['expected_pilot_forwards'] == 130, 'Only this frozen130 context pilot is registered')
    require(bound(reg['GPU_code']) == Path(__file__).resolve(), 'Frozen context GPU code differs from this file')
    preparation_file = bound(reg['preparation_code'])
    require(bound(reg['CPU_registration']) == (root/'context_CPU_registration_28.json').resolve()
            and bound(reg['input_acceptance']) == (root/'context_inputs_28/input_acceptance.json').resolve(),
            'Only the actual frozen28 CPU registration and first input gate may be adopted')
    cpu_registration = read(bound(reg['CPU_registration']))
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_ALL_NEW_SOURCE_OVERVIEW_CONTEXT_INPUTS'
            and gate['registration'] == reg['CPU_registration']
            and gate['TRUE_inputs'] == 295 and gate['FOREIGN_inputs'] == 40 and gate['inputs'] == 335
            and gate['first_independent_pixels_text_native_owner_QA'] is True
            and gate['actual3video_grids'] is True and gate['old_two_video_QA_substituted'] is False,
            'All335 first independent context input QA must precede GPU')
    prepared = read(bound(gate['prepared']))
    old18 = read(bound(reg['original_GPU18']))
    for reference in old18['runtime_dependencies']:
        bound(reference)
    old17 = read(bound(old18['pair_registration']))
    require(reg['model_config'] == old17['model_config']
            and reg['old_TIME'] == old17['old_TIME_weights'], 'Original BASE/TIME artifact binding differs')
    for reference in old17['old_helpers']:
        bound(reference)
    for name, digest in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen17 dependency changed: '+name)
    require(cpu_registration['preparation_code'] == reg['preparation_code']
            and cpu_registration['pair_registration'] == old18['pair_registration']
            and cpu_registration['training_completion'] == reg['training_completion'],
            'CPU/GPU preparation/original experiment/final200 reference differs')
    require(prepared['source_catalog'] == cpu_registration['source_catalog']
            and prepared['remaining_or_production_admitted'] is False
            and prepared['new_real_vision_processor_calls'] == 0 and prepared['original_decode'] == 0,
            'Only accepted original-pixel overview pilot inputs are admitted')
    require(bound(reg['preparation_code']) == preparation_file, 'Preparation bytes changed during registration checks')
    training = read(bound(reg['training_completion']))
    require(training['status'] == 'COMPLETE_FIXED_FINAL200_PAIR_COMPARISON_NOT_QUALITY'
            and training['completed_updates'] == 200 and training['successful_micro'] == 800
            and training['adapter_reload_all288_exact'] is True
            and training['adapter_weights'] == reg['adapter_weights'],
            'Only the exact independently reloaded final200 PAIR adapter is allowed')
    weights = bound(reg['adapter_weights']); directory = Path(reg['adapter_directory']).resolve()
    require(directory.is_relative_to(WORK) and directory == weights.parent
            and weights.name == 'adapter_model.safetensors'
            and directory == Path(training['adapter_directory']).resolve(), 'Final200 adapter directory differs')
    old_gate = read(bound(old18['input_acceptance']))
    old_prepared = read(bound(old_gate['prepared']))
    old_catalog = read(bound(old_prepared['source_catalog']))
    source_hashes = {s['id']: s['source_sha256'] for s in old_catalog['sources']}
    dev_ids = old_prepared['dev_source_ids']; classes = old_prepared['class_token_ids']
    require(len(dev_ids) == len(set(dev_ids)) == 5 and len(classes) == len(set(classes)) == 3,
            'Original accepted five dev sources and digit classes required')
    return reg, cpu_registration, gate, prepared, old18, source_hashes, dev_ids, classes


def _owners(request):
    """Owners are part of alias identity even when all tensor bytes coincide."""
    keys = ('source_id', 'source_sha256', 'overview_source_id', 'overview_source_sha256', 'overview_is_foreign')
    return {key: request[key] for key in keys}


def _pilot_manifest(prepared, source_hashes, dev_ids, classes):
    roles = prepared['pilot_roles']
    require(set(roles) == set(ROLES) and roles['BASE_TRUE'] == roles['PAIR_TRUE'],
            'Frozen BASE and PAIR true-context pilot entries must be identical')
    original_true = {}
    metadata = {}
    for role in ROLES:
        entries = roles[role]
        require(len(entries) == COUNTS[role] and len({e['id'] for e in entries}) == len(entries)
                and {e['source_id'] for e in entries} == set(dev_ids), 'Exact role counts/all five source coverage required')
        role_meta = {}
        for entry in entries:
            request = read(bound(entry['inputref']))
            require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
                    and request['source_sha256'] == source_hashes[entry['source_id']]
                    and request['class_token_ids'] == classes, 'Actual pilot request/source/class identity differs')
            overview_source = request['overview_source_id']
            require(overview_source in source_hashes
                    and request['overview_source_sha256'] == source_hashes[overview_source],
                    'Overview source is not the accepted original external source')
            foreign = role == 'PAIR_FOREIGN'
            require(request['overview_is_foreign'] is foreign, 'True/foreign context role is mislabeled')
            require((overview_source != entry['source_id'] and request['overview_source_sha256'] != request['source_sha256'])
                    if foreign else (overview_source == entry['source_id'] and request['overview_source_sha256'] == request['source_sha256']),
                    'Actual overview ownership does not match the explicit true/foreign treatment')
            original_id = request['original_case_id']
            require(isinstance(original_id, str) and bool(original_id), 'Original successful two-clip case identity required')
            bound(request['tokens'])
            row = dict(original_case_id=original_id, owners=_owners(request), input_signature=request['input_signature'],
                       input=entry['inputref'], class_token_ids=request['class_token_ids'])
            role_meta[entry['id']] = row
            if role == 'BASE_TRUE':
                require(original_id not in original_true, 'Pilot true-context original cases must be unique')
                original_true[original_id] = entry['source_id']
            if foreign:
                require(original_id in original_true and original_true[original_id] == entry['source_id'],
                        'Foreign treatment must refer to the same source/clip cases as the true pilot')
        metadata[role] = role_meta
    return metadata


def _base_inventory(model, helper):
    require(not any('lora_' in name for name, _ in model.named_parameters())
            and sum(p.numel() for p in model.parameters()) == helper.BASE_PARAMETERS
            and not any(p.requires_grad for p in model.parameters()), 'BASE role must be exactly frozen physical BASE')
    return dict(base=helper.BASE_PARAMETERS, pair=0, resident=helper.BASE_PARAMETERS,
        conservative_pipeline=helper.BASE_PARAMETERS+helper.PAIR_PARAMETERS+helper.OLD_TIME_PARAMETERS+helper.SEMANTIC_PARAMETERS,
        pair_component_counted=helper.PAIR_PARAMETERS, original_TIME_counted=helper.OLD_TIME_PARAMETERS,
        semantic_counted=helper.SEMANTIC_PARAMETERS, original_TIME_loaded=False, adapter=None)


def _check_adapter(model, expected, helper, torch):
    _, inventory = helper._inventory(model, False, torch)
    actual = helper._adapter_state(model, torch)
    require(set(actual) == set(expected) and len(actual) == 288
            and all(actual[key].dtype == value.dtype and actual[key].shape == value.shape
                    and torch.equal(actual[key].contiguous().view(torch.uint8), value.contiguous().view(torch.uint8))
                    for key, value in expected.items()),
            'Readonly PAIR must remain byte-exact to all288 final200 tensors')
    return inventory


def _stage(root_out, model, inputs, entries, role, metadata, inventory, vocabulary_size, reg, helper, torch, np,
           successful_raw, completed_receipts):
    out = root_out/role; out.mkdir(exist_ok=False)
    weights_role = 'BASE' if role == 'BASE_TRUE' else 'PAIR200'
    save(out/'claim.json', dict(utc=utc(), role=role, weights_role=weights_role,
         GPU_registration=ref(root_out.parent/'context_GPU_registration_29.json'),
         expected_inputs=len(entries), foreign_context=role == 'PAIR_FOREIGN', labels_read=False))
    aliases, completed = {}, []
    attempts = out/'attempts.jsonl'; attempts.touch(exist_ok=False)
    started = time.monotonic()
    for index, entry in enumerate(entries):
        helper._deadline(reg)
        values, request = inputs.get(entry['inputref'])
        expected = metadata[entry['id']]
        require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
                and request['original_case_id'] == expected['original_case_id']
                and _owners(request) == expected['owners']
                and request['class_token_ids'] == expected['class_token_ids']
                and request['input_signature'] == expected['input_signature'], 'Actual consumed pilot metadata changed')
        require(set(values) == {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}
                and signature(values) == request['input_signature']
                and values['video_grid_thw'].tolist() == request['video_grid_thw'],
                'Actual pilot tokens/pixels/three-video grid differ from first accepted input')
        grid = values['video_grid_thw']
        require(grid.device.type == 'cpu' and grid.dtype == torch.int64 and tuple(grid.shape) == (3, 3)
                and bool((grid > 0).all()) and bool((grid[:, 1:] % 2 == 0).all())
                and 1 <= int(grid[0, 0]) <= 32 and int(grid[1, 0]) == int(grid[2, 0]) == 4,
                'Actual Overview(max64 observations)/A8/B8 grids required')
        require(not any(p.requires_grad for p in model.parameters()), 'Frozen inference parameters became trainable')
        classes = request['class_token_ids']
        key = json.dumps(dict(signature=request['input_signature'], owners=_owners(request), classes=classes),
                         sort_keys=True, separators=(',', ':'))
        previous = aliases.get(key); one = time.monotonic()
        if previous is None:
            gpu = {name: value.to('cuda:0') for name, value in values.items()}
            append_event(attempts, event='BEGIN_FIRST_CONTEXT_FORWARD', id=entry['id'], input=entry['inputref'], model_role=role,
                         original_case_id=request['original_case_id'], **_owners(request))
            helper._deadline(reg)
            with torch.inference_mode():
                output = model(**gpu, use_cache=False, return_dict=True, logits_to_keep=1)
                raw = output.logits[0, -1].float().detach().cpu().contiguous()
            raw_path = out/('%05d.lastlogits.pt' % index)
            helper._tensor_file(raw_path, raw, torch)
            raw_reference = ref(raw_path)
            successful_raw.append(dict(model_role=role, id=entry['id'], original_case_id=request['original_case_id'],
                                       raw_logits=raw_reference, **_owners(request)))
            append_event(attempts, event='FIRST_CONTEXT_RAW_PERSISTED', id=entry['id'], raw_logits=raw_reference, model_role=role)
            torch.cuda.synchronize()
            del gpu, output
        else:
            raw_reference = previous['raw_logits']
            raw = torch.load(bound(raw_reference), map_location='cpu', weights_only=True)
        # No post-forward output/flag/identity validation can precede first raw persistence.
        require(raw.ndim == 1 and raw.dtype == torch.float32 and len(raw) == vocabulary_size and torch.isfinite(raw).all(),
                'Finite raw full-vocabulary float32 last logits required')
        require(len(classes) == len(set(classes)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in classes),
                'Actual three-class digit token IDs outside full vocabulary')
        three = raw[classes].numpy().astype(np.float64)
        probabilities = helper._softmax3(three, np)
        receipt_path = out/('%05d.receipt.json' % index)
        save(receipt_path, dict(id=entry['id'], original_case_id=request['original_case_id'], input=entry['inputref'],
            role='SOURCE_OVERVIEW_PILOT', model_role=role, weights_role=weights_role,
            raw_logits=raw_reference, class_token_ids=classes, class_logits=three.tolist(), probabilities=probabilities,
            predicted_index=int(np.argmax(three)), full_vocabulary_size=len(raw), raw_dtype='torch.float32',
            input_signature=request['input_signature'], softmax_scope='Three class logits ONLY; not calibrated confidence',
            actual_new_forward=previous is None, alias_of=previous['receipt'] if previous else None,
            elapsed_seconds=time.monotonic()-one, labels_read=False, dev_reference_read=False,
            original_TIME_loaded=False, new_optimizer_updates=0, **_owners(request)))
        receipt_reference = ref(receipt_path)
        if previous is None:
            aliases[key] = dict(raw_logits=raw_reference, receipt=receipt_reference)
        row = dict(id=entry['id'], input=entry['inputref'], receipt=receipt_reference)
        completed.append(row); completed_receipts.append(dict(model_role=role, **row))
        append_event(attempts, event='ACCEPTED_FIRST_CONTEXT_RESULT', id=entry['id'], receipt=receipt_reference,
                     model_role=role, alias=previous is not None)
        del values, raw
    completion = out/'completion.json'
    save(completion, dict(status='COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY', model_role=role,
        weights_role=weights_role, entries=completed, actual_forward_calls=len(aliases), aliases=len(completed)-len(aliases),
        expected_inputs=len(entries), inventory=inventory, elapsed_seconds=time.monotonic()-started,
        full_vocabulary_size=vocabulary_size,
        input_acceptance=reg['input_acceptance'], CPU_registration=reg['CPU_registration'],
        GPU_registration=ref(root_out.parent/'context_GPU_registration_29.json'),
        training_completion=reg['training_completion'], labels_read=False, dev_reference_read=False,
        original_TIME_loaded=False, new_optimizer_updates=0, automatic_remaining_or_production=False))
    return ref(completion)


def run(root):
    root = Path(root).resolve()
    require(root.is_relative_to(WORK) and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
            'Context child must retain its registered physical GPU assignment inside the work root')
    reg, cpu_registration, gate, prepared, old18, source_hashes, dev_ids, classes = _registration(root)
    metadata = _pilot_manifest(prepared, source_hashes, dev_ids, classes)
    helper = _load_module(old18['GPU_code'], '_frozen_pair18_context29_utilities')
    helper._deadline(reg); paths()
    from sft_contract import verify_live_gpu_reservation, REVISION
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'],
            'Active shared GPU wrapper belongs to a different job')
    preparation = _load_module(reg['preparation_code'], '_frozen_context28_input_loader')
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Frozen context runtime changed')
    torch.set_num_threads(2)
    inputs = preparation.ContextInputs(root)
    require(inputs.prepared == prepared and inputs.reg == cpu_registration,
            'Actual context loader is not consuming the GPU-admitted CPU registration/prepared inputs')
    out = root/'context_model_29'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), pid=os.getpid(), physical_GPU_assignment=os.environ['CUDA_VISIBLE_DEVICES'],
        GPU_registration=ref(root/'context_GPU_registration_29.json'), CPU_registration=reg['CPU_registration'],
        input_acceptance=reg['input_acceptance'], training_completion=reg['training_completion'],
        expected_roles=list(ROLES), expected_receipts=130, labels_read=False, new_optimizer_updates=0,
        original_TIME_loaded=False, pilot_only=True))
    successful_raw, completed_receipts, stages = [], [], {}
    started = time.monotonic()
    try:
        cfg = read(bound(reg['model_config'])); old_time = bound(reg['old_TIME'])
        require(cfg['base_parameters'] == helper.BASE_PARAMETERS and sha(old_time) == cfg['b_adapter_sha256'],
                'Exact original BASE/TIME byte identity differs')
        helper._deadline(reg)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        for parameter in base.parameters(): parameter.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        vocabulary_size = int(base.config.text_config.vocab_size)
        require(vocabulary_size > max(classes), 'Actual BASE vocabulary cannot contain the accepted digit classes')
        base_inventory = _base_inventory(base, helper)
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == helper.BASE_PARAMETERS and before['sha256'] == cfg['expected_base_sha256']
                and base_inventory['conservative_pipeline'] == PIPELINE_PARAMETERS,
                'Actual frozen BASE or whole-pipeline inventory differs')
        save(out/'BASE_identity.json', dict(base_fingerprint=before, inventory=base_inventory,
            original_TIME=reg['old_TIME'], original_TIME_loaded=False, role='BASE_TRUE', no_training=True))
        stages['BASE_TRUE'] = _stage(out, base, inputs, prepared['pilot_roles']['BASE_TRUE'], 'BASE_TRUE',
            metadata['BASE_TRUE'], base_inventory, vocabulary_size, reg, helper, torch, np, successful_raw, completed_receipts)
        _base_inventory(base, helper)
        require(canonical_frozen_hash(base, torch) == before, 'BASE changed during plain BASE_TRUE treatment')
        helper._deadline(reg)
        expected_adapter = load_file(str(bound(reg['adapter_weights'])), device='cpu')
        require(len(expected_adapter) == 288, 'Exactly288 saved final200 PAIR matrices required')
        model = PeftModel.from_pretrained(base, reg['adapter_directory'], adapter_name=helper.ADAPTER,
                                         is_trainable=False).eval()
        for parameter in model.parameters(): parameter.requires_grad_(False)
        model.config.use_cache = False
        inventory = _check_adapter(model, expected_adapter, helper, torch)
        require(inventory['base'] == 8767123696 and inventory['pair'] == 7667712
                and inventory['resident'] == 8774791408 and inventory['conservative_pipeline'] == PIPELINE_PARAMETERS
                and inventory['conservative_pipeline'] <= 9000000000,
                'Actual BASE+PAIR and conservative pipeline parameter counts differ')
        save(out/'PAIR_identity.json', dict(base_fingerprint=before, inventory=inventory,
            adapter_weights=reg['adapter_weights'], training_completion=reg['training_completion'],
            independent_adapter_reload_all288_exact=True, original_TIME=reg['old_TIME'],
            original_TIME_loaded=False, no_training=True))
        for role in ('PAIR_TRUE', 'PAIR_FOREIGN'):
            stages[role] = _stage(out, model, inputs, prepared['pilot_roles'][role], role,
                metadata[role], inventory, vocabulary_size, reg, helper, torch, np, successful_raw, completed_receipts)
            _check_adapter(model, expected_adapter, helper, torch)
            require(canonical_frozen_hash(model, torch) == before and not any(p.requires_grad for p in model.parameters()),
                    'Frozen BASE/PAIR changed during source-overview treatment')
        require(sha(bound(reg['adapter_weights'])) == reg['adapter_weights']['sha256']
                and sha(old_time) == reg['old_TIME']['sha256'], 'Saved final200 PAIR/original TIME bytes changed')
        summaries = {role: read(bound(reference)) for role, reference in stages.items()}
        actual = sum(row['actual_forward_calls'] for row in summaries.values())
        aliases = sum(row['aliases'] for row in summaries.values())
        require(len(completed_receipts) == 130 and actual+aliases == 130 and len(stages) == 3,
                'All130 frozen pilot receipts and actual-call/alias accounting required')
        save(out/'completion.json', dict(status='COMPLETE_130_SOURCE_OVERVIEW_PILOT_NOT_QUALITY',
            stages=stages, role_order=list(ROLES), expected_pilot_forwards=130, completed_receipts=130,
            actual_forward_calls=actual, aliases=aliases, expected_role_counts=COUNTS,
            GPU_registration=ref(root/'context_GPU_registration_29.json'), CPU_registration=reg['CPU_registration'],
            input_acceptance=reg['input_acceptance'], preparation_code=reg['preparation_code'],
            original_GPU18=reg['original_GPU18'], training_completion=reg['training_completion'],
            model_config=reg['model_config'], old_TIME=reg['old_TIME'], adapter_weights=reg['adapter_weights'],
            BASE_identity=ref(out/'BASE_identity.json'), PAIR_identity=ref(out/'PAIR_identity.json'),
            base_fingerprint=before, inventory=inventory, independent_adapter_reload_all288_exact=True,
            full_vocabulary_size=vocabulary_size,
            adapter_all288_unchanged=True, original_TIME_loaded=False, original_TIME_unchanged=True,
            labels_read=False, dev_reference_read=False, new_optimizer_updates=0,
            elapsed_seconds=time.monotonic()-started, actual_quality_established=False,
            automatic_remaining_or_production=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            stages_completed=stages, successful_raw=successful_raw, completed_receipts=completed_receipts,
            labels_read=False, original_TIME_loaded=False, new_optimizer_updates=0,
            preserve_all_success=True, do_not_repeat_success=True, failure_is_not_empty=True,
            automatic_resume=False, automatic_remaining_or_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    run(args.root)
