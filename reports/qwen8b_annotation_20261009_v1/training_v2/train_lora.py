"""Explicit preflight/train entry. Default preflight never loads model weights or CUDA."""
import argparse
import hashlib
import json
from pathlib import Path

from sft_contract import ImageSFTCollator, load_rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    p.add_argument('--dataset-root', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--train', action='store_true', help='Explicitly authorize this invocation to load weights and optimize')
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    root = Path(args.dataset_root).resolve(strict=True)
    from verify_bundle import verify
    verify(root)
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory; no overwrite or implicit resume')
    rows = {s: load_rows(root / config[f'{s}_file'], root) for s in ('train', 'validation')}
    if {r['source_group'] for r in rows['train']} & {r['source_group'] for r in rows['validation']}:
        raise ValueError('Train/validation source leakage')
    if any(r['task'] != config['task'] for s in rows.values() for r in s):
        raise ValueError('Do not silently mix tasks')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True,
                                             min_pixels=config['min_pixels'], max_pixels=config['max_pixels'])
    model_config = Path(args.model) / 'config.json'
    expected = config.get('model_config_sha256')
    actual = hashlib.sha256(model_config.read_bytes()).hexdigest()
    if expected is None or actual != expected:
        raise ValueError('Model config identity is missing or changed')
    collator = ImageSFTCollator(processor, root, max_tokens=config['max_input_tokens'])
    # Every real row is processed before any model/optimizer operation. Refuse silent truncation.
    stats = {}
    for split, records in rows.items():
        counts, supervised = [], []
        for row_index, row in enumerate(records):
            encoded = collator.encode(row)
            counts.append(encoded['input_ids'].shape[1])
            supervised.append(int((encoded['labels'] != -100).sum()))
            if row_index % 20 == 0:
                print(json.dumps({'stage': 'PROCESSOR_PREFLIGHT', 'split': split,
                                  'done_rows': row_index + 1, 'expected_rows': len(records)}), flush=True)
        stats[split] = {'rows': len(records), 'max_tokens': max(counts), 'min_assistant_tokens': min(supervised)}
    output.mkdir(parents=True)
    receipt = {'status': 'PASS_ALL_REAL_IMAGE_ROWS_PROCESSOR_AND_MASK_PREFLIGHT', 'stats': stats,
               'model_config_sha256': actual, 'model_weights_loaded': False, 'optimizer_started': False}
    (output / 'preflight.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if not args.train:
        print(json.dumps(receipt))
        return
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen3VLForConditionalGeneration, Trainer, TrainingArguments
    if not torch.cuda.is_available():
        raise ValueError('Requested training has no CUDA device; no silent CPU fallback')
    model = Qwen3VLForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
                torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    targets = [name for name, module in model.named_modules()
               if name.endswith(tuple('.' + n for n in ('q_proj', 'k_proj', 'v_proj', 'o_proj')))
               and 'visual' not in name and 'vision' not in name and 'language_model' in name]
    if not targets:
        raise ValueError('Language-only LoRA targets not found')
    model = get_peft_model(model, LoraConfig(r=config['lora_rank'], lora_alpha=config['lora_alpha'],
                lora_dropout=config['lora_dropout'], target_modules=targets, bias='none', task_type='CAUSAL_LM'))
    model.config.use_cache = False
    training_args = TrainingArguments(output_dir=str(output / 'trainer'),
                per_device_train_batch_size=1, per_device_eval_batch_size=1,
                gradient_accumulation_steps=config['gradient_accumulation_steps'],
                learning_rate=config['learning_rate'], num_train_epochs=config['epochs'],
                warmup_ratio=0.05, weight_decay=0.01, bf16=True, gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant': False},
                remove_unused_columns=False, dataloader_num_workers=0, report_to=[],
                eval_strategy='epoch', save_strategy='epoch', save_total_limit=2,
                logging_steps=1, seed=20261009, data_seed=20261009)
    trainer = Trainer(model=model, args=training_args, train_dataset=rows['train'],
                      eval_dataset=rows['validation'], data_collator=collator)
    result = trainer.train()
    trainer.save_model(str(output / 'adapter'))
    processor.save_pretrained(output / 'adapter')
    trainer.save_state()
    (output / 'train_metrics.json').write_text(json.dumps(result.metrics, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
