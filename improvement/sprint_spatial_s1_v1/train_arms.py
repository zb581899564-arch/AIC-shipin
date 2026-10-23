"""Three fresh same-seed50-step LoRAs, unchanged base/vision and fixed final only."""
import json
import random
import time
import numpy as np
import torch
from common import ROOT, RUN, ARMS, read, ref, write, append, runtime_paths, digest
from model_io import values, generate


def order(rows, arm, count, seed):
    if arm != 'W01':
        chosen = []
        epoch = 0
        while len(chosen) < count:
            batch = list(range(len(rows)))
            random.Random(seed + epoch).shuffle(batch)
            chosen.extend(batch)
            epoch += 1
        return chosen[:count]
    groups = [[i for i, row in enumerate(rows) if row['human_bin'] == k] for k in range(3)]
    position = [0, 0, 0]
    cycle = [0, 0, 0]
    plans = [[], [], []]
    chosen = []
    for index in range(count):
        group = index % 3
        if position[group] == len(plans[group]):
            plans[group] = groups[group].copy()
            random.Random(seed + group * 10000 + cycle[group]).shuffle(plans[group])
            cycle[group] += 1
            position[group] = 0
        chosen.append(plans[group][position[group]])
        position[group] += 1
    return chosen


def train_one(base, processor, train, evaluation, arm, recipe, targets):
    from peft import LoraConfig, PeftModel, get_peft_model
    from sft_contract import validate_trainable_names
    from train_sft import fingerprint_base, gradient_evidence, unique_parameters
    seed = recipe['seed']
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=.05, bias='none',
        target_modules=targets, task_type='CAUSAL_LM', modules_to_save=None))
    trainable = [(n, p) for n, p in unique_parameters(model) if p.requires_grad]
    validate_trainable_names([n for n, _ in trainable])
    lora_count = sum(p.numel() for _, p in trainable)
    total = 8782557449 + lora_count
    if total > 9000000000:
        raise ValueError('Actual base/TIME/semantic-head/new-spatial-adapter exceeds9B')
    folder = ROOT / 'arms' / arm
    folder.mkdir(parents=True)
    before = fingerprint_base(model, torch)
    initial = {n: p.detach().cpu().clone() for n, p in trainable}
    init_hash = __import__('hashlib').sha256(b''.join(p.contiguous().view(torch.uint8).numpy().tobytes() for p in initial.values())).hexdigest()
    write(folder / 'initialization.json', dict(seed=seed, adapter_initial_sha256=init_hash, adapter_parameters=lora_count,
                                            combined_pipeline_parameters=total))
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.train()
    for name, layer in model.named_modules():
        if name.endswith('.visual'):
            layer.eval()
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=recipe['lr'], weight_decay=0.0)
    optimizer.zero_grad(set_to_none=True)
    indices = order(train, arm, recipe['updates'] * recipe['grad_accum'], seed)
    write(folder / 'draw_plan.json', dict(indices=indices, bins=[sum(train[i]['human_bin'] == k for i in indices) for k in range(3)]))
    start = time.monotonic()
    losses = []
    for micro, index in enumerate(indices):
        data, keep = values(train[index], arm)
        output = model(**{k: v.cuda() for k, v in data.items()}, logits_to_keep=keep)
        loss = output.loss
        if loss is None or not torch.isfinite(loss):
            raise ValueError('Nonfinite or missing real assistant loss')
        (loss / recipe['grad_accum']).backward()
        losses.append(float(loss.detach()))
        if (micro + 1) % recipe['grad_accum'] == 0:
            step = (micro + 1) // recipe['grad_accum']
            evidence = gradient_evidence(trainable, torch, step)
            norm = torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1.0)
            if not torch.isfinite(norm) or float(norm) <= 0:
                raise ValueError('Nonzero finite gradients required')
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            append(folder / 'updates.jsonl', dict(step=step, microbatches=micro + 1,
                loss_mean=float(np.mean(losses[-recipe['grad_accum']:])), norm=float(norm), gradient=evidence))
            if step % 10 == 0:
                print('ARM', arm, 'UPDATE', step, 'LOSS', float(np.mean(losses[-recipe['grad_accum']:])), flush=True)
    model.eval()
    after = fingerprint_base(model, torch)
    if before != after:
        raise ValueError('Original base/vision fingerprint changed')
    saved = {n: p.detach().cpu().clone() for n, p in unique_parameters(model) if 'lora_' in n}
    if not any(not torch.equal(initial[n], p) for n, p in saved.items()):
        raise ValueError('No real adapter update')
    path = folder / 'adapter'
    model.save_pretrained(str(path), safe_serialization=True)
    base = model.unload()
    model = PeftModel.from_pretrained(base, str(path), is_trainable=False)
    reloaded = {n: p.detach().cpu() for n, p in unique_parameters(model) if 'lora_' in n}
    if set(saved) != set(reloaded) or any(not torch.equal(p, reloaded[n]) for n, p in saved.items()):
        raise ValueError('Saved final adapter reload changed')
    model.gradient_checkpointing_disable()
    model.config.use_cache = True
    model.eval()
    for item in evaluation:
        if item['role'] == 'dev':
            generate(model, processor, item, arm, 'dev')
    result = dict(status='PASS50_REAL_UPDATES_FINAL_RELOAD_AND80_DEV_GENERATIONS', arm=arm,
        updates=recipe['updates'], microbatches=len(indices), actual_loss_forwards=len(indices),
        actual_backwards=len(indices), final_only=True, loss_first=losses[0], loss_last=losses[-1],
        base_fingerprint_unchanged=True, adapter=ref(path / 'adapter_model.safetensors'),
        parameters=lora_count, combined_pipeline_parameters=total, initialization_sha=init_hash,
        wall_seconds=time.monotonic() - start, dev_generations=80)
    write(folder / 'completion.json', result)
    del optimizer, output, loss, saved, reloaded, initial
    base = model.unload()
    del model
    torch.cuda.empty_cache()
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    return base, result


def main():
    runtime_paths()
    from spatial_baseline import Qwen3VL
    from sft_contract import language_target_names, verify_live_gpu_reservation
    verify_live_gpu_reservation()
    acceptance = read(ROOT / 'conditioned_input_acceptance.json')
    if acceptance['status'] != 'PASS_ALL762_CONDITIONED_TOKENS_PIXELS_AND602_TARGETS':
        raise ValueError('All real CPU inputs required before3armtraining')
    recipe = read(ROOT / 'training_recipe.json')
    train, evaluation = read(ROOT / 'conditioned_train.json'), read(ROOT / 'conditioned_eval.json')
    cfg = read(RUN / 'b_score_aligned_package_v4/config.json')
    wrapper = Qwen3VL(cfg['model_dir'], max_pixels=131072, device_map={'': 'cuda:0'}, attn_implementation='sdpa')
    base, processor = wrapper.model, wrapper.processor
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    targets = language_target_names([n for n, layer in base.named_modules() if isinstance(layer, torch.nn.Linear)],
                                   base.config.text_config.num_hidden_layers)
    results = []
    for arm in ARMS:
        base, result = train_one(base, processor, train, evaluation, arm, recipe, targets)
        results.append(result)
    if len({r['initialization_sha'] for r in results}) != 1:
        raise ValueError('Three initial adapter tensor sets were not identical')
    write(ROOT / 'training_completion.json', dict(status='ALL3_ARMS_REAL_TRAINING_AND_DEV_OUTPUTS_COMPLETE',
        arms=results, actual_optimizer_updates=sum(r['updates'] for r in results), actual_dev_generations=240,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(), no_confirm_metrics_read=True))


if __name__ == '__main__':
    main()
