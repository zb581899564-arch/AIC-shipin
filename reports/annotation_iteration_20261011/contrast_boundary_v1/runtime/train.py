"""Small fixed two-epoch native64 SFT. No old scores_x20 or nested cost runner."""
import argparse
import math
from pathlib import Path
import random
import sys
import traceback
from common import admit, bound, helpers, read, require, save, sha, verify_lock
from native_runtime import encode, validate_plan
from model_binding import load_model, tensor_hash, inventory


def validate_preflight(contract,path,expected_sha):
    require(sha(path)==expected_sha,'actual CPU preflight receipt SHA differs')
    p=Path(path).resolve(strict=True)
    require(p.parent.parent==Path(contract['config']['train_output_dir']).parent.resolve(),'foreign preflight experiment')
    r=read(p)
    require(r['status']=='PASS_ACTUAL_CPU_NATIVE_PROCESSOR_AND_ASSISTANT_TARGET_PARITY_NOT_TRAINING' and
            r['lock_sha256']==contract['lock_sha'] and r['config_sha256']==contract['config_sha'] and
            r['model_loaded'] is False and r['new_model_calls']==r['new_optimizer_updates']==0 and r['cuda_initialized'] is False,
            'actual CPU preflight acceptance absent')
    training=set(contract['schedule']['window_ids']);expected=training|set(contract['config']['final_only_evaluation_window_ids'])
    require(len(r['rows'])==len(expected) and {v['window_id'] for v in r['rows']}==expected,'CPU preflight denominator differs')
    for row in r['rows']:
        detail=read(bound(row['input_receipt']))
        require(detail['window_id']==row['window_id'] and detail['actual_native_and_reviewed_processor_equal'] is True and
                detail['training_target_present']==(row['window_id'] in training) and
                detail['evidence']['normalized_tensor_sha256']==row['normalized_tensor_sha256'],'actual per-window preflight differs')
    contract['native_cpu_preflight_accepted']=True
    contract['native_cpu_preflight_receipt']=dict(path=str(p),sha256=expected_sha)


def execute(contract):
    require(contract.get('native_cpu_preflight_accepted') is True,'actual CPU input parity must precede model loading')
    c = contract['config']; out = Path(c['train_output_dir']); out.mkdir(parents=True, exist_ok=False)
    report = dict(reference_kind='CONTRAST_BOUNDARY_NATIVE_SILVER_V1',status='RUNNING_FIXED_NATIVE64_SILVER_SFT', optimizer_steps=0, examples_backward=0,
        updates=[], losses=[], new_optimizer_updates=0, quality_evaluation_pending=True,
        lock_sha256=contract['lock_sha'], config_sha256=contract['config_sha'],
        source_order=contract['schedule']['window_ids'], schedule=contract['schedule'],
        final_checkpoint_only=True, original_B_preserved=True,
        native_cpu_preflight_receipt=contract['native_cpu_preflight_receipt'])
    try:
        import numpy as np
        import torch
        random.seed(c['seed']); np.random.seed(c['seed']); torch.manual_seed(c['seed']); torch.cuda.manual_seed_all(c['seed'])
        student, video, sft, smoke = helpers(c)
        model, processor, params, frozen_before = load_model(contract, sft, smoke, c['initial_adapter_dir'], True)
        report['initial_loaded_tensor_equality_count']=contract['loaded_adapter_tensor_identity_count']
        original = {name: p.detach().cpu().clone() for name, p in params}
        report['initial_lora_tensor_sha256'] = tensor_hash(params, torch)
        optimizer = torch.optim.AdamW([p for _, p in params], lr=1e-5, betas=(.9, .999), eps=1e-8, weight_decay=0)
        require(not optimizer.state, 'optimizer must be fresh')
        schedule = contract['schedule']; keys = schedule['window_ids']
        for key in keys:
            validate_plan(contract['jobs'][key]['window'])
        with (out/'examples.jsonl').open('x', encoding='utf-8') as evidence_stream:
            for step, batch in enumerate(schedule['batches'], 1):
                optimizer.zero_grad(set_to_none=True)
                evidence_rows = []
                for index in batch['indices']:
                    key = keys[index]
                    encoded, evidence = encode(contract, key, processor, video, training=True)
                    result = model(**{k: v.to('cuda:0') if hasattr(v, 'to') else v for k, v in encoded.items()})
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), 'missing/nonfinite assistant CE')
                    # Original registered source objective: NO extra division by batch size.
                    coefficient = schedule['window_ce_coefficient']*schedule['source_weights'][index]
                    (result.loss*float(coefficient)).backward()
                    loss = float(result.loss.detach().cpu())
                    report['losses'].append(loss); report['examples_backward'] += 1
                    evidence.update(window_id=key, source_group=contract['jobs'][key]['source_group'],
                        optimizer_step=step, epoch=batch['epoch'], window_loss=loss,
                        exact_gradient_coefficient=str(coefficient), second_accumulation_division=False,
                        reference_sha256=contract['reference_sha'][key],
                        target_sidecar_sha256=c.get('target_sidecars', {}).get(key, {}).get('sha256'))
                    import json
                    evidence_stream.write(json.dumps(evidence, ensure_ascii=False, default=str, allow_nan=False)+'\n')
                    evidence_stream.flush(); evidence_rows.append(key)
                    del encoded, result
                nonzero = 0; squared = 0.0
                for name, p in params:
                    require(p.grad is not None and bool(torch.isfinite(p.grad).all()), 'missing/nonfinite LoRA gradient: '+name)
                    norm = float(p.grad.float().norm()); nonzero += norm > 0; squared += norm*norm
                require(nonzero > 0 and squared > 0 and math.isfinite(squared), 'zero/nonfinite connected gradient')
                clipped_norm = torch.nn.utils.clip_grad_norm_([p for _, p in params], 1.0)
                require(bool(torch.isfinite(clipped_norm)) and float(clipped_norm) > 0, 'gradient clip failure')
                previous = tensor_hash(params, torch)
                optimizer.step(); report['optimizer_steps'] = step; report['new_optimizer_updates'] = step
                current = tensor_hash(params, torch)
                require(previous != current, 'actual optimizer update changed no weights')
                item = dict(step=step, epoch=batch['epoch'], window_ids=evidence_rows, nonzero_gradient_tensors=nonzero,
                    gradient_norm=math.sqrt(squared), clip_input_norm=float(clipped_norm), actual_weights_changed=True,
                    previous_lora_sha256=previous, lora_sha256=current)
                report['updates'].append(item); save(out/('step_%02d.json'%step), item)
                print(__import__('json').dumps(item), flush=True)
        require(report['optimizer_steps'] == schedule['updates'] == c['epochs']*((len(keys)+c['gradient_accumulation']-1)//c['gradient_accumulation']) and
                report['examples_backward'] == contract['protocol']['counts']['examples_backward'] == c['epochs']*len(keys), 'fixed training denominator incomplete')
        frozen_after = smoke.canonical_frozen_hash(model, torch)
        require(frozen_after == frozen_before, 'frozen base/vision bytes changed')
        changed = sum(not torch.equal(p.detach().cpu(), original[name]) for name, p in params)
        require(changed > 0, 'final weights equal original B')
        trained = {name: p.detach().cpu().clone() for name, p in params}
        final = out/'final_adapter'; model.save_pretrained(str(final), safe_serialization=True)
        require(list(out.glob('*adapter')) == [final], 'unique final checkpoint required')
        from peft import PeftModel
        reloaded = PeftModel.from_pretrained(model.unload(), str(final), is_trainable=False)
        actual = dict(inventory(reloaded, torch, sft))
        require(set(actual) == set(trained) and len(actual) == 288 and
                all(actual[name].dtype == trained[name].dtype and torch.equal(actual[name].detach().cpu(), trained[name]) for name in actual),
                'saved/reloaded 288 tensor identity differs')
        frozen_reload = smoke.canonical_frozen_hash(reloaded, torch)
        require(frozen_reload == frozen_before, 'saved final changed frozen base/vision')
        verify_lock(contract['lock_path'], contract['lock_sha'])
        report.update(status='PASS_FIXED_NATIVE64_SILVER_SFT_ENGINEERING_ONLY',
            final_adapter_dir=str(final), final_adapter_sha256=sha(final/'adapter_model.safetensors'),
            final_adapter_config_sha256=sha(final/'adapter_config.json'), saved_tensor_identity_count=288,
            changed_final_lora_tensors=changed, finite_losses=all(map(math.isfinite, report['losses'])),
            frozen_before=frozen_before, frozen_after=frozen_after, frozen_reload=frozen_reload,
            first_step_nonzero_gradients=report['updates'][0]['nonzero_gradient_tensors'] > 0,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(), training_complete=True)
    except BaseException as exc:
        report.update(status='STOP_NATIVE64_SILVER_SFT', failure_type=type(exc).__name__, failure=str(exc),
            traceback=traceback.format_exc(), failure_converted_to_empty=False, training_complete=False)
        save(out/'training_receipt.json', report)
        raise
    save(out/'training_receipt.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True); p.add_argument('--lock', required=True)
    p.add_argument('--expected-lock', required=True); p.add_argument('--check-only', action='store_true')
    p.add_argument('--preflight-receipt');p.add_argument('--expected-preflight-receipt')
    args = p.parse_args()
    contract = admit(args.config, args.lock, args.expected_lock, 'train')
    if args.check_only:
        print(__import__('json').dumps(dict(status='PASS_STATIC_ADMISSION_ONLY', windows=len(contract['schedule']['window_ids']),
            updates=contract['schedule']['updates'], decoder_started=False, processor_started=False, model_started=False)))
        return 0
    require(args.preflight_receipt and args.expected_preflight_receipt,'actual preflight receipt arguments required')
    validate_preflight(contract,args.preflight_receipt,args.expected_preflight_receipt)
    execute(contract)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
