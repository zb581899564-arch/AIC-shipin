"""First read-only final500 training-source readouts for new utility target.

The former CE decision rule remains STOP. No optimizer or target labels are
loaded; these are the first train-source forwards at the final500 weights.
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


def run(root, phase):
    require(phase in ('pilot128', 'remaining2280') and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
            'Explicit readonly phase and actual GPU assignment required')
    original_path = root/'crop_gain_GPU_registration_46.json'
    original = read(original_path)
    regpath = original_path if phase == 'pilot128' else root/'crop_gain_remaining_admission_46.json'
    reg = read(regpath)
    require(original['schema'] == 'FINAL500_GAIN_TRAIN_READOUT_PILOT128_V46'
            and bound(original['GPU_code']) == Path(__file__).resolve(), 'Exact new readout purpose/entry')
    if phase == 'remaining2280':
        require(reg['original_GPU_registration'] == ref(original_path)
                and reg['GPU_code'] == original['GPU_code']
                and reg['input_acceptance'] == original['input_acceptance'], 'Explicit remaining-only admission')
        prior = read(bound(reg['pilot_output_acceptance']))
        require(prior['status'] == 'PASS_GAIN_PILOT128_FIRST_RAW_QA'
                and prior['GPU_registration'] == ref(original_path), 'Adopt completed first pilot QA')
    stop = read(bound(original['original_CE_STOP']))
    require(stop['status'] == 'STOP_NATIVE_CROP_SCREEN' and stop['production_prepare_approved'] is False
            and stop['reports']['TRAINED']['summary']['changed'] == 0
            and stop['adapter_weights'] == original['adapter_weights'],
            'Original CE failure must remain explicit; this is not its quality approval')
    completed = read(bound(original['fixed_training_completion']))
    require(completed['completed_updates'] == 500 and completed['successful_micro'] == 2000
            and completed['adapter_reload_all288_exact'] is True
            and original['adapter_weights'] == completed['adapter_weights'], 'Exact immutable final500 weights')
    old = read(bound(original['original_GPU32']))
    require(original['model_config'] == old['model_config'] and original['GPU_helper'] == old['GPU_code'],
            'Exact original physical model and frozen first-raw implementation')
    gate = read(bound(original['input_acceptance']))
    require(gate['status'] == 'PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA'
            and gate['new_image_processor_calls'] == 0 and gate['new_original_decodes'] == 0,
            'Adopted plus first remaining-combination input gate required')
    paths()
    import numpy as np
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import Qwen3VLForConditionalGeneration
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'], 'Wrong live GPU reservation')
    frozen = module(original['GPU_helper'], '_frozen_crop_gpu32_gain46')
    frozen._deadline(reg)
    component = module(original['input_reader_code'], '_frozen_gain_inputs44')
    image = module(original['image_code'], '_frozen_crop_image31_gain46')
    prepared = read(bound(gate['prepared']))
    inputs = component.GainInputs(prepared, gate=gate, prepared_ref=gate['prepared'],
        registration_ref=original['CPU_registration'], load_json=lambda v: read(bound(v)),
        load_tensor=lambda v: torch.load(bound(v), map_location='cpu', weights_only=True), image=image)
    entries = prepared['pilot_inputs' if phase == 'pilot128' else 'remaining_inputs']
    require(len(entries) == (128 if phase == 'pilot128' else 2280)
            and len({e['source_id'] for e in entries}) == (32 if phase == 'pilot128' else 570),
            'Exact SHA-fixed remaining source partition, no repeat pilot')
    out = root/'crop_gain_model_46'
    if phase == 'pilot128':
        out.mkdir(exist_ok=False)
    else:
        require(out.is_dir(), 'Adopt original pilot namespace')
    namespace = out/phase
    namespace.mkdir(exist_ok=False)
    (namespace/'crop_model_31').mkdir()
    save(namespace/'claim.json', dict(utc=utc(), GPU_registration=ref(regpath), phase=phase,
        fixed_adapter=original['adapter_weights'], optimizer_updates=0, labels_read=False,
        purpose='FIRST_FINAL500_READONLY_TRAIN_SOURCE_OUTPUTS_FOR_SEPARATE_UTILITY_SUPERVISION'))
    raw_success = []
    try:
        cfg = read(bound(original['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        base.eval()
        base.config.use_cache = False
        for p in base.parameters():
            p.requires_grad_(False)
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == 8767123696 and before['sha256'] == cfg['expected_base_sha256'], 'Original BASE differs')
        weights = bound(original['adapter_weights'])
        require(str(weights.parent) == completed['adapter_directory'], 'Only original final500 artifact directory')
        bound(original['adapter_config'])
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name='crop', is_trainable=False).eval()
        for p in model.parameters():
            p.requires_grad_(False)
        _, inventory = frozen._inventory(model, False, torch)
        state = load_file(str(weights), device='cpu')
        require(frozen._same_state(frozen._adapter_state(model, torch), state, torch), 'Actual final500 adapter reload differs')
        role = 'GAIN_'+phase
        output = frozen._prediction_stage(namespace, model, inputs, entries, role, reg, torch, np, raw_success)
        require(frozen._same_state(frozen._adapter_state(model, torch), state, torch)
                and canonical_frozen_hash(model, torch) == before, 'Readout changed BASE/CROP')
        save(out/(phase+'_completion.json'), dict(status='COMPLETE_FIRST_FINAL500_GAIN_TRAIN_RAW_NOT_QUALITY',
            phase=phase, completion=output, GPU_registration=ref(regpath), original_GPU_registration=ref(original_path),
            input_acceptance=original['input_acceptance'], adapter_weights=original['adapter_weights'],
            inventory=inventory, base_fingerprint=before, new_optimizer_updates=0,
            original_TIME_loaded=False, old_PAIR_loaded=False, training_targets_read=False,
            automatic_fit=False, automatic_confirm=False, automatic_production=False))
    except BaseException as error:
        save(namespace/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            successful_raw=raw_success, preserve_all_success=True, automatic_retry=False,
            failure_is_not_empty=True, labels_read=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--phase', choices=['pilot128', 'remaining2280'], required=True)
    a = p.parse_args()
    run(a.root, a.phase)
