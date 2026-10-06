"""Bounded BF16 LoRA with assistant-only loss and generated epoch validation."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
import time

from training.gate import evaluate_training_gate, write_gate_report
from training.train_lora import TrainingConfig, _attach_lora
from evaluation_v2.temporal import evaluate_rows, intervals, read_jsonl, truth_intervals


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n')
    temp.replace(path)


def validate_rows(rows):
    from inference_v2.temporal import parse_segments_response
    for row in rows:
        if row.get('task_type') != 'query_moment_retrieval' or not row.get('query','').strip():
            raise ValueError('training requires explicit query-conditioned official annotation')
        intervals(truth_intervals(row), float(row['duration_sec']))
        answer_json=json.dumps({'segments':truth_intervals(row)},separators=(',',':'))
        if not parse_segments_response(answer_json,'multi').ok:
            raise ValueError('annotation conflicts with the fixed 0..4 coherent-window training contract')
        if row.get('alignment_verified') is not True or row.get('trusted_identity') is not True:
            raise ValueError('untrusted training sample')


def train(args, decision):
    # The full data/authorization gate runs before any CUDA framework import.
    import torch
    import peft
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from inference_v2.qwen_io import build_temporal_messages, encode_qwen3vl_messages, infer_temporal_policy
    from inference_v2.temporal import build_temporal_prompt, canonicalize_segments

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + args.max_seconds
    random.seed(42)
    torch.manual_seed(42)
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError('BF16 CUDA required')
    rows = {split: read_jsonl(decision.split_audit[split]['path']) for split in ('train','dev')}
    for values in rows.values():
        validate_rows(values)
    if args.smoke:
        rows['train'] = rows['train'][:16]
        rows['dev'] = rows['dev'][:2]
    config = TrainingConfig(model_name_or_path=args.model, output_dir=str(output), max_frames=64,
                            max_pixels_per_frame=131072, max_seq_length=12288)
    write(output/'config.json', dict(**config.as_dict(), smoke=args.smoke,
          smoke_optimizer_steps=args.smoke_steps, dev_policy=args.policy,
          task_type='query_moment_retrieval', official_aic_score=None,
          generated_validation_constrained_json=True,
          selection='generated dev duration-union F1', hard_wall_seconds=args.max_seconds,
          reference_hashes={s:hashlib.sha256(Path(decision.split_audit[s]['path']).read_bytes()).hexdigest()
                            for s in ('train','dev','holdout')}))
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True,
                                              min_pixels=131072, max_pixels=131072, padding_side='right')
    model = Qwen3VLForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
                torch_dtype=torch.bfloat16, attn_implementation='sdpa', low_cpu_mem_usage=True).to('cuda')
    model = _attach_lora(model, config, torch, peft)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    model.enable_input_require_grads()
    trainable = [(n,p) for n,p in model.named_parameters() if p.requires_grad]
    write(output/'trainable_parameters.json', {'names':[n for n,p in trainable],
          'count':sum(p.numel() for n,p in trainable), 'base_frozen':True,'vision_frozen':True})
    optimizer = torch.optim.AdamW([p for n,p in trainable], lr=5e-5, weight_decay=.01)
    steps_per_epoch = math.ceil(len(rows['train'])/16)
    total_steps = args.smoke_steps if args.smoke else 3*steps_per_epoch
    warmup = max(1, round(.05*total_steps))
    def factor(step):
        if step < warmup:
            return (step+1)/warmup
        progress = min(1., (step-warmup)/max(1,total_steps-warmup))
        return .5*(1+math.cos(math.pi*progress))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, factor)
    step = 0
    epoch = 0
    best = None
    history = []
    token_audit = []
    stopped = None
    optimizer.zero_grad(set_to_none=True)

    def batch(row):
        # Training always learns coherent query-relevant windows on the full
        # video. The same multi prompt is shared with the candidate inference.
        prompt = build_temporal_prompt(row['query'], policy='multi',duration_sec=row['duration_sec'])
        messages = build_temporal_messages(row['video_path'], prompt, fps=2., max_frames=64, max_pixels=131072)
        encoded = encode_qwen3vl_messages(processor, messages, device=None)
        inputs = dict(encoded.inputs)
        prefix = inputs['input_ids']
        answer = json.dumps({'segments':truth_intervals(row)}, separators=(',',':'))
        suffix = processor.tokenizer(answer + '<|im_end|>\n', add_special_tokens=False, return_tensors='pt')['input_ids']
        ids = torch.cat((prefix, suffix), dim=1)
        if ids.shape[1] > 12288:
            raise ValueError(f'length {ids.shape[1]} exceeds 12288; refusing truncation')
        labels = ids.clone()
        labels[:,:prefix.shape[1]] = -100
        if not (labels != -100).any():
            raise ValueError('empty assistant supervision')
        inputs.update(input_ids=ids, labels=labels, attention_mask=torch.ones_like(ids))
        inputs = {k:v.to('cuda') if hasattr(v,'to') else v for k,v in inputs.items()}
        if len(token_audit) < 16:
            token_audit.append(dict(video_id=row['video_id'], prefix_tokens=prefix.shape[1],
                                   answer_tokens=suffix.shape[1], sampling=encoded.sampling))
        return inputs

    def generated_eval():
        model.eval()
        model.config.use_cache = True
        predictions = []
        try:
            for row in rows['dev']:
                if time.monotonic() > deadline:
                    raise TimeoutError('training wall limit during generated validation')
                with torch.inference_mode():
                    result = infer_temporal_policy(model, processor, row['video_path'], policy=args.policy,
                              query=row['query'], duration_sec=row['duration_sec'], max_frames=64, max_pixels=131072,
                              constrained_json=True)
                result_dict = asdict(result) if hasattr(result,'__dataclass_fields__') else dict(result)
                status = result_dict['status']
                seconds,_ = canonicalize_segments(result_dict['segments_sec'],row['fps'],row['n_frames'],row['duration_sec'])
                predictions.append(dict(video_id=row['video_id'], source_group=row['source_group'],
                    status='ok' if status=='valid' else status,
                    segments_sec=seconds,
                    inference_detail=result_dict))
            path = output/f'epoch_{epoch}_dev_predictions.jsonl'
            path.write_text(''.join(json.dumps(row)+'\n' for row in predictions))
            report = evaluate_rows(predictions, rows['dev'])
            write(output/f'epoch_{epoch}_dev_report.json', report)
            return report['metrics']['f1']
        finally:
            model.config.use_cache = False
            model.train()

    while step < total_steps and (args.smoke or epoch < 3):
        epoch += 1
        order = list(range(len(rows['train'])))
        random.Random(42+epoch).shuffle(order)
        model.train()
        epoch_complete = True
        for offset in range(0,len(order),16):
            group = order[offset:offset+16]
            losses = []
            for idx in group:
                if time.monotonic() > deadline:
                    stopped = 'time_limit'
                    epoch_complete = False
                    break
                inputs = batch(rows['train'][idx])
                with torch.autocast('cuda',dtype=torch.bfloat16):
                    loss = model(**inputs).loss
                if not torch.isfinite(loss):
                    raise RuntimeError('nonfinite training loss')
                losses.append(float(loss.detach()))
                (loss/len(group)).backward()
                del inputs,loss
            if not epoch_complete:
                optimizer.zero_grad(set_to_none=True)
                break
            grad = torch.nn.utils.clip_grad_norm_([p for n,p in trainable],1.0,error_if_nonfinite=True)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            record = dict(epoch=epoch,step=step,loss=sum(losses)/len(losses),grad_norm=float(grad),
                          learning_rate=scheduler.get_last_lr()[0], elapsed_seconds=time.monotonic()-started)
            with (output/'loss.jsonl').open('a') as log:
                log.write(json.dumps(record)+'\n')
            print(json.dumps(record),flush=True)
            write(output/'progress.json',record)
            if step >= total_steps:
                break
        model.save_pretrained(output/'last')
        write(output/'token_audit.json', token_audit)
        if not epoch_complete:
            break
        try:
            score = generated_eval()
            history.append(dict(epoch=epoch,step=step,dev_f1=score))
            if best is None or score > best['dev_f1']:
                best = history[-1]
                model.save_pretrained(output/'best')
                processor.save_pretrained(output/'best')
        except TimeoutError:
            stopped = 'time_limit_during_validation'
            break
        write(output/'selection.json',dict(best=best,history=history,smoke=args.smoke))
    report = dict(status='completed' if stopped is None else 'time_limited', optimizer_steps=step,
                  best=best,history=history,smoke=args.smoke,stop_reason=stopped,
                  elapsed_seconds=time.monotonic()-started,
                  max_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
                  adapter_offline_reload_verified=False)
    write(output/'training_report.json',report)
    print(json.dumps(report),flush=True)
    if best is None:
        raise RuntimeError('no generated dev validation completed; adapter is not a candidate')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--coordination',required=True)
    ap.add_argument('--data-gate',required=True)
    ap.add_argument('--model',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--policy',choices=['single','multi','windowed'],default='multi')
    ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--smoke-steps',type=int,default=2)
    ap.add_argument('--max-seconds',type=int,default=27000)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    if not 1 <= args.smoke_steps <= 20 or not 1 <= args.max_seconds <= 28800:
        raise ValueError('training resource settings exceed authorization')
    decision=evaluate_training_gate(args.coordination,args.data_gate)
    write_gate_report(Path(args.output).parent/(Path(args.output).name+'_gate.json'),decision)
    if not decision.ok:
        raise RuntimeError('training gate rejected: '+','.join(decision.reasons))
    if args.dry_run:
        for split in ('train','dev','holdout'):
            validate_rows(read_jsonl(decision.split_audit[split]['path']))
        print('DATA_GATE_ACCEPTED_NO_GPU')
        return
    train(args,decision)


if __name__=='__main__':
    main()
