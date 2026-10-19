"""Conditional first native19 readout of the immutable gain-critic pipeline.

No CPU preparation, fitting, baseline model calls, or automatic production.
Requires a new49 CPU gate and actual new47 screen qualification; old33 stays STOP.
Registration crop_gain_confirm_GPU_registration_50.json binds GPU_code,
reader_code, GPU_helper, model_config, input_acceptance, CPU_registration,
screen_result, critic_weights, adapter_weights/config, fixed_training_completion,
original_GPU32, deadline_utc and GPU_job. Only --root is accepted.
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


def admission(reg, screen, gate, training, reader_gate):
    require(reg['schema'] == 'GAIN_CRITIC_NATIVE19_READONLY_GPU_V50', 'Explicit new native gain scope')
    require(screen['status'] == 'PASS_GAIN_CRITIC_SCREEN20_ONLY' and screen['confirm_admitted'] is True
            and screen['production_admitted'] is False and screen['primary'] == 'JOINT14'
            and screen['fixed_final_checkpoint'] is True
            and screen['critic_weights'] == reg['critic_weights']
            and screen['adapter_weights'] == reg['adapter_weights'], 'Actual new gain-screen qualification required')
    require(gate['status'] == reader_gate and gate['registration'] == reg['CPU_registration']
            and gate['sources'] == 19 and gate['original20_complete'] is False
            and gate['first_independent_pixels_text_native_QA'] is True
            and gate['adapter_weights'] == reg['adapter_weights'], 'Every first new native19 input must be accepted')
    require(training['completed_updates'] == 500 and training['successful_micro'] == 2000
            and training['adapter_reload_all288_exact'] is True
            and training['adapter_weights'] == reg['adapter_weights'], 'Exact fixed final500 CROP identity required')


def run(root):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'GPU parent keeps its physical assignment')
    regpath = root/'crop_gain_confirm_GPU_registration_50.json'
    reg = read(regpath)
    require(bound(reg['GPU_code']) == Path(__file__).resolve(), 'Exact new confirm GPU entry')
    reader = module(reg['reader_code'], '_gain_native19_reader49')
    screen = read(bound(reg['screen_result']))
    gate = read(bound(reg['input_acceptance']))
    training = read(bound(reg['fixed_training_completion']))
    admission(reg, screen, gate, training, reader.GATE)
    bound(reg['critic_weights'])  # Bind only; CPU critic/targets are not consumed by the 8B forward.
    old32 = read(bound(reg['original_GPU32']))
    require(reg['model_config'] == old32['model_config'] and reg['GPU_helper'] == old32['GPU_code'],
            'Same physical BASE and frozen first-raw helper')
    inputs = reader.NativeGainConfirmInputs(root)
    prepared = read(bound(gate['prepared']))
    require(inputs.prepared == prepared, 'Actual accepted reader identity')
    entries = prepared['confirm_inputs']
    require(len(entries) == gate['inputs'] and 19 <= len(entries) <= 247
            and len({row['source_id'] for row in entries}) == 19
            and all(row['source_id'] != 'gnmc:test:006575.jpeg' for row in entries),
            'Exact native19 scope excludes the unavailable old source')
    paths()
    import numpy as np
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import Qwen3VLForConditionalGeneration
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'], 'Wrong active shared reservation')
    helper = module(reg['GPU_helper'], '_crop_gpu32_gain_native19')
    helper._deadline(reg)
    out = root/'crop_gain_confirm_model_50'
    out.mkdir(exist_ok=False)
    (out/'crop_model_31').mkdir()
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), screen_result=reg['screen_result'],
        critic_weights=reg['critic_weights'], adapter_weights=reg['adapter_weights'],
        no_optimizer=True, labels_read=False, old_CE_quality='STOP', automatic_production=False))
    successful_raw = []
    try:
        cfg = read(bound(reg['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        base.eval()
        base.config.use_cache = False
        for p in base.parameters():
            p.requires_grad_(False)
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == 8767123696 and before['sha256'] == cfg['expected_base_sha256'], 'BASE changed')
        weights = bound(reg['adapter_weights'])
        require(str(weights.parent) == training['adapter_directory']
                and bound(reg['adapter_config']).parent == weights.parent, 'Exact final500 adapter files')
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name='crop', is_trainable=False).eval()
        for p in model.parameters():
            p.requires_grad_(False)
        _, inventory = helper._inventory(model, False, torch)
        actual = load_file(str(weights), device='cpu')
        require(helper._same_state(helper._adapter_state(model, torch), actual, torch), 'CROP reload changed')
        output = helper._prediction_stage(out, model, inputs, entries, 'GAIN_NATIVE19', reg, torch, np, successful_raw)
        require(helper._same_state(helper._adapter_state(model, torch), actual, torch)
                and canonical_frozen_hash(model, torch) == before, 'Read-only native19 changed model bytes')
        save(out/'completion.json', dict(status='COMPLETE_GAIN_NATIVE19_FIRST_RAW_NOT_QUALITY',
            GPU_registration=ref(regpath), input_acceptance=reg['input_acceptance'], completion=output,
            critic_weights=reg['critic_weights'], adapter_weights=reg['adapter_weights'],
            inventory=inventory, base_fingerprint=before, new_optimizer_updates=0,
            training_targets_read=False, screen_qualified=True, automatic_production=False))
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            successful_raw=successful_raw, preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
