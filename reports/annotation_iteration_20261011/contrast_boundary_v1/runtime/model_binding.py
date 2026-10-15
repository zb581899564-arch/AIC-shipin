"""Deferred model imports and actual B/base/language-only LoRA identity."""
from pathlib import Path
from common import require, read, sha, INITIAL_SHA, BASE_SHA


def inventory(model, torch, sft):
    seen = set(); trainable = []; base = lora = 0
    for name, p in model.named_parameters():
        if id(p) in seen:
            continue
        seen.add(id(p))
        if 'lora_' in name:
            lora += p.numel(); trainable.append((name, p))
        else:
            base += p.numel(); require(not p.requires_grad, 'base/vision not frozen')
    sft.validate_trainable_names([name for name, _ in trainable])
    require(len(trainable) == 288 and base == sft.BASE_PARAMS and lora == sft.LORA_PARAMS and
            base+lora == 8782459120, 'actual parameter inventory differs')
    targets = {name for name, module in model.named_modules() if hasattr(module, 'lora_A') and 'default' in module.lora_A}
    require(len(targets) == 144 and all('language_model.layers.' in name and '.self_attn.' in name for name in targets),
            'language-only actual targets differ')
    return trainable


def load_model(contract, sft, smoke, adapter_dir, training):
    import torch
    import transformers
    import peft
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    c = contract['config']
    if training:
        require(Path(adapter_dir).resolve()==Path(c['initial_adapter_dir']).resolve() and
                sha(Path(adapter_dir)/'adapter_model.safetensors')==INITIAL_SHA,
                'training must initialize exact original B, never a prior failed/final adapter')
    require(torch.cuda.is_available() and transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1',
            'registered CUDA/runtime versions required')
    a = read(Path(adapter_dir)/'adapter_config.json')
    require(a['r'] == 16 and a['lora_alpha'] == 32 and a['lora_dropout'] == .05 and
            a['bias'] == 'none' and a.get('modules_to_save') is None, 'adapter scalar recipe differs')
    base = Qwen3VLForConditionalGeneration.from_pretrained(c['model_dir'], revision=sft.REVISION,
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
        low_cpu_mem_usage=True, attn_implementation='sdpa')
    for p in base.parameters():
        p.requires_grad_(False)
    base.config.use_cache = False
    model = PeftModel.from_pretrained(base, str(adapter_dir), is_trainable=training)
    trainable = inventory(model, torch, sft)
    payload=load_file(str(Path(adapter_dir)/'adapter_model.safetensors'),device='cpu')
    actual={name.replace('.default.','.'):p.detach().cpu() for name,p in trainable}
    require(set(payload)==set(actual) and len(actual)==288 and
            all(payload[n].dtype==actual[n].dtype and torch.equal(payload[n],actual[n]) for n in actual),
            'actual loaded288 adapter tensors differ from saved admitted bytes')
    contract['loaded_adapter_tensor_identity_count']=288
    require(all(p.requires_grad == training for _, p in trainable), 'actual adapter training flags differ')
    frozen = smoke.canonical_frozen_hash(model, torch)
    require(frozen['sha256'] == BASE_SHA and frozen['parameters'] == sft.BASE_PARAMS, 'actual frozen base bytes differ')
    processor = AutoProcessor.from_pretrained(c['processor_dir'], local_files_only=True)
    processor.video_processor.do_sample_frames=False
    if training:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.train()
        # Only original language LoRA has dropout; frozen vision remains deterministic.
        for name, module in model.named_modules():
            if name.endswith('.visual'):
                module.eval()
    else:
        model.eval()
    return model, processor, trainable, frozen


def tensor_hash(named, torch):
    import hashlib
    h = hashlib.sha256()
    for name, p in sorted(named):
        h.update(name.encode()); h.update(str(p.dtype).encode()); h.update(str(list(p.shape)).encode())
        h.update(p.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return h.hexdigest()
