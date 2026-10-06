"""Audit and reload the existing five-update adapter; no additional updates."""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ORIGINAL = HERE/'smoke_01'
OUT = HERE/'saved_adapter_check_01'
from sft_contract import (BASE_PARAMS, LORA_PARAMS, TOTAL_PARAMS, REVISION,
    require, sha256, verify_live_gpu_reservation, verify_model_receipt)

def canonical_frozen_hash(model, torch):
    parameters = {}
    seen = set()
    for name, parameter in model.named_parameters(remove_duplicate=False):
        if id(parameter) in seen or 'lora_' in name:
            continue
        seen.add(id(parameter))
        require(not parameter.requires_grad, 'base/vision became trainable during reload')
        name = name.removeprefix('base_model.model.').replace('.base_layer.', '.')
        require(name not in parameters, 'ambiguous canonical frozen parameter')
        parameters[name] = parameter
    digest = hashlib.sha256()
    count = 0
    for name, parameter in sorted(parameters.items()):
        digest.update(name.encode())
        digest.update(str(tuple(parameter.shape)).encode())
        digest.update(str(parameter.dtype).encode())
        flat = parameter.detach().reshape(-1)
        for offset in range(0, flat.numel(), 1 << 22):
            digest.update(flat[offset:offset+(1 << 22)].contiguous().view(torch.uint8).cpu().numpy().tobytes())
        count += parameter.numel()
    return {'sha256': digest.hexdigest(), 'parameters': count,
            'method': 'sorted canonical names and all unique frozen parameter bytes'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-helper-sha256', required=True)
    args = parser.parse_args()
    require(sha256(__file__) == args.expected_helper_sha256, 'verification source changed')
    lock_path = HERE/'smoke_source_lock.json'
    require(sha256(lock_path) == '806deb54de18835ee6841a1a921f015cd0d8b82ad65268e016af3144cb19ff93', 'original recipe changed')
    lock = json.loads(lock_path.read_text())
    for name, digest in lock['files'].items():
        require(sha256(HERE/name) == digest, 'original source/input changed: '+name)
    report_path = ORIGINAL/'train_report.json'
    original_sha = sha256(report_path)
    original = json.loads(report_path.read_text())
    require(original['status'] == 'STOP_INTERVAL_SFT_SMOKE' and original['optimizer_steps'] == 5 and
            original['effective_batches'] == 80 and original['failure']['message'] == 'saved adapter recipe changed',
            'not the five completed updates with only the registered recipe-check failure')
    require(len(original['losses']) == 80 and all(math.isfinite(v) for v in original['losses']), 'original loss evidence incomplete')
    require(len(original['updates']) == 5 and all(u['changed_lora_tensors'] > 0 and
            math.isfinite(u['gradient_norm']) and u['gradient_norm'] > 0 for u in original['updates']), 'original update/gradient evidence incomplete')
    expected = set(original['exact_language_targets'])
    require(len(expected) == 144 and all(name.startswith('model.language_model.layers.') and
            name.rsplit('.', 1)[-1] in {'q_proj', 'k_proj', 'v_proj', 'o_proj'} for name in expected), 'original language target inventory changed')
    adapter = ORIGINAL/'adapter'
    config_path = adapter/'adapter_config.json'
    saved_config_sha = sha256(config_path)
    weights_path = adapter/'adapter_model.safetensors'
    saved_weights_sha = sha256(weights_path)
    saved = json.loads(config_path.read_text())
    require(saved['r'] == 16 and saved['lora_alpha'] == 32 and saved['lora_dropout'] == .05 and
            saved['bias'] == 'none' and saved['modules_to_save'] is None and
            set(saved['target_modules']) == {'q_proj', 'k_proj', 'v_proj', 'o_proj'}, 'unregistered scalar/target recipe change')
    config = json.loads((HERE/'smoke_config_PREPARED_NOT_ADMITTED.json').read_text())
    verify_model_receipt(Path(config['model_dir']), json.loads(Path(config['model_receipt']['path']).read_text()))
    verify_live_gpu_reservation()
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    result = dict(status='RUNNING_SAVED_ADAPTER_RELOAD_ADDENDUM', original_report_sha256=original_sha,
        original_failed_report_preserved=True, optimizer_steps=5, effective_batches=80,
        additional_optimizer_updates=0, original_freeze_hash_values_were_not_persisted=True,
        original_freeze_comparison_guard_passed_before_recipe_failure=True, uploaded=False)
    try:
        import torch
        from safetensors.torch import load_file
        from peft import PeftModel
        from transformers import Qwen3VLForConditionalGeneration
        require(torch.cuda.is_available(), 'registered CUDA verification required')
        torch.cuda.set_device(0)
        base = Qwen3VLForConditionalGeneration.from_pretrained(config['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        frozen_before = canonical_frozen_hash(base, torch)
        model = PeftModel.from_pretrained(base, str(adapter), is_trainable=False)
        targets = {name.removeprefix('base_model.model.') for name, module in model.named_modules()
                   if hasattr(module, 'lora_A') and 'default' in module.lora_A}
        require(targets == expected, 'compressed target suffixes reloaded different modules/vision/head')
        payload = load_file(str(weights_path), device='cpu')
        actual = {name.replace('.default.', '.'): parameter.detach().cpu()
                  for name, parameter in model.named_parameters() if 'lora_' in name}
        require(set(payload) == set(actual) and len(payload) == 288, 'saved/reloaded tensor identity differs')
        require(all(payload[name].dtype == actual[name].dtype and torch.equal(payload[name], actual[name]) and
                    bool(torch.isfinite(actual[name]).all()) for name in payload), 'saved/reloaded LoRA bytes differ/nonfinite')
        inventory = dict(base=sum(p.numel() for name, p in model.named_parameters() if 'lora_' not in name),
                         lora=sum(p.numel() for name, p in model.named_parameters() if 'lora_' in name))
        require(inventory == {'base': BASE_PARAMS, 'lora': LORA_PARAMS}, 'reload parameter accounting differs')
        require(not any('modules_to_save' in name or p.requires_grad for name, p in model.named_parameters()),
                'inference reload has copied/trainable extra modules')
        frozen_after = canonical_frozen_hash(model, torch)
        with model.disable_adapter():
            frozen_adapter_off = canonical_frozen_hash(model, torch)
        require(frozen_before == frozen_after == frozen_adapter_off and frozen_before['parameters'] == BASE_PARAMS,
                'pinned base/vision bytes changed after adapter reload/off')
        require(sha256(report_path) == original_sha and sha256(config_path) == saved_config_sha and
                sha256(weights_path) == saved_weights_sha, 'original training evidence/adapter modified')
        for name, digest in lock['files'].items():
            require(sha256(HERE/name) == digest, 'original input/code modified during reload')
        result.update(status='PASS_SAVED_ADAPTER_SEMANTIC_RELOAD_ADDENDUM',
            target_serialization='PEFT_MINIMAL_SUFFIX_COMPRESSION_144_QUALIFIED_TO_4_SUFFIXES',
            exact_reloaded_language_modules=144, reloaded_lora_tensors=288,
            all_saved_and_reloaded_lora_tensors_equal=True, adapter_model_sha256=saved_weights_sha,
            base_frozen_on_reload=True, vision_frozen_on_reload=True,
            adapter_reload_succeeded=True, adapter_off_base_bytes_unchanged=True,
            freeze_evidence=dict(pinned_base=frozen_before, adapter_loaded=frozen_after, adapter_off=frozen_adapter_off),
            parameter_inventory={**inventory, 'total': TOTAL_PARAMS},
            original_training_freeze_evidence_kind='audited reached/passed guard in pinned source; original values not persisted',
            full_training_completed=False, quality_claim=False)
    except Exception as exc:
        result.update(status='STOP_SAVED_ADAPTER_RELOAD_ADDENDUM', failure_type=type(exc).__name__,
                      failure=str(exc), traceback=traceback.format_exc())
    result['wall_seconds'] = time.monotonic()-started
    result['checked_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    with (OUT/'verification_report.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['traceback', 'freeze_evidence']}), flush=True)
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)
