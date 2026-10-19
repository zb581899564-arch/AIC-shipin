"""Conditional native confirm19, fixed final500 CROP versus original BASE.

Only a separately admitted, complete native-screen result can enter. There is
no training, checkpoint choice, image processor, reference read or production.
The original missing first confirmation source is permanently excluded.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK, read, save, ref, bound, require, utc, paths


def module(reference, name):
    path = bound(reference)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def run(root):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Actual physical GPU assignment required')
    regpath = root/'crop_confirm_GPU_registration_37.json'
    reg = read(regpath)
    require(reg['schema'] == 'NATIVE_CROP_CONFIRM19_FINAL500_V37'
            and bound(reg['GPU_code']) == Path(__file__).resolve(), 'Exact independent confirm GPU registration')
    native = read(bound(reg['native_screen_result']))
    require(native['status'] == 'PASS_NATIVE_CROP_SCREEN_ONLY' and native['confirm_admitted'] is True
            and native['production_prepare_approved'] is False, 'Native screen must actually qualify first')
    training = read(bound(reg['native_training_completion']))
    require(training['status'] == 'COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'
            and training['completed_updates'] == 500 and training['successful_micro'] == 2000
            and training['adapter_reload_all288_exact'] is True
            and reg['adapter_weights'] == training['adapter_weights'] == native['adapter_weights']
            and reg['adapter_directory'] == training['adapter_directory'], 'Only exact fixed-final500 adapter')
    weights = bound(reg['adapter_weights'])
    require(weights.parent == Path(reg['adapter_directory']).resolve(), 'Bound adapter directory differs')
    bound(reg['adapter_config'])
    original = read(bound(reg['original_GPU_registration']))
    require(reg['model_config'] == original['model_config'] and reg['GPU_helper'] == original['GPU_code'],
            'Original BASE and frozen inference implementation required')
    gate = read(bound(reg['input_acceptance']))
    require(gate['GPU_admitted'] is False and gate['sources'] == 19
            and gate['original20_complete'] is False, 'Only first-QAd explicit remaining19 CPU inputs')
    inputs_module = module(reg['input_reader_code'], '_crop_confirm_input36')
    inputs = inputs_module.ConfirmInputs(root)
    entries = inputs.prepared['confirm_inputs']
    require(len(entries) == gate['confirm_inputs'] and len({e['source_id'] for e in entries}) == 19,
            'Complete new native-confirm input inventory')
    gpu = module(reg['GPU_helper'], '_frozen_crop_gpu32_confirm37')
    gpu._deadline(reg)
    paths()
    import numpy as np
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import Qwen3VLForConditionalGeneration
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'],
            'Actual shared GPU reservation belongs to another job')
    cfg = read(bound(reg['model_config']))
    out = root/'crop_confirm_model_37'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), reference_read=False,
        original20_complete=False, missing_first_source_repeated=False, optimizer_updates=0))
    raw_success = []
    try:
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        base.eval()
        base.config.use_cache = False
        for p in base.parameters():
            p.requires_grad_(False)
        before = canonical_frozen_hash(base, torch)
        require(before['sha256'] == cfg['expected_base_sha256']
                and before['parameters'] == 8767123696
                and not any('lora_' in n for n, _ in base.named_parameters()), 'Exact wholly frozen BASE')
        # The frozen helper owns exclusive raw stages under its supplied root.
        # A separate namespace prevents collision with any screen/pilot stage.
        workspace = out/'raw_namespace'
        workspace.mkdir()
        (workspace/'crop_model_31').mkdir()
        base_completion = gpu._prediction_stage(workspace, base, inputs, entries, 'BASE_confirm',
                                                reg, torch, np, raw_success)
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name='crop',
                                          is_trainable=False).eval()
        for p in model.parameters():
            p.requires_grad_(False)
        _, inventory = gpu._inventory(model, False, torch)
        saved = load_file(str(weights), device='cpu')
        require(gpu._same_state(gpu._adapter_state(model, torch), saved, torch), 'Final500 reload exact')
        trained_completion = gpu._prediction_stage(workspace, model, inputs, entries, 'TRAINED_confirm',
                                                   reg, torch, np, raw_success)
        require(gpu._same_state(gpu._adapter_state(model, torch), saved, torch)
                and canonical_frozen_hash(model, torch) == before, 'Read-only confirm changed weights')
        save(out/'completion.json', dict(status='COMPLETE_FIXED_FINAL500_NATIVE_CONFIRM19_RAW_NOT_QUALITY',
            BASE_completion=base_completion, TRAINED_completion=trained_completion, inventory=inventory,
            base_fingerprint=before, adapter_weights=reg['adapter_weights'],
            original_GPU_registration=reg['original_GPU_registration'], registration=ref(regpath),
            input_acceptance=reg['input_acceptance'], original20_complete=False,
            missing_first_source_repeated=False, new_optimizer_updates=0,
            reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False,
            automatic_production=False, automatic_package=False))
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            successful_raw=raw_success, preserve_all_success=True, automatic_retry=False,
            failure_is_not_empty=True, original20_complete=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    run(p.parse_args().root)
