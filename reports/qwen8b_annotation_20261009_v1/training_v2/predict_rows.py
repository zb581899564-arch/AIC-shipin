"""Explicit post-training greedy prediction entry; never includes assistant gold in inputs."""
import argparse
import json
from pathlib import Path

from PIL import Image

from sft_contract import decode_output, load_rows, typed_messages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-root', required=True)
    parser.add_argument('--data', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--adapter', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(args.dataset_root).resolve(strict=True)
    from verify_bundle import verify
    verify(root)
    output = Path(args.output)
    if output.exists():
        raise ValueError('Use a new prediction output; never overwrite')
    rows = load_rows(args.data, root)
    import torch
    from peft import PeftModel
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    if not torch.cuda.is_available():
        raise ValueError('No GPU for explicitly requested inference; no silent fallback')
    processor = AutoProcessor.from_pretrained(args.adapter, local_files_only=True)
    base = Qwen3VLForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
                   torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    model = PeftModel.from_pretrained(base, args.adapter, local_files_only=True).to('cuda').eval()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        for row in rows:
            images = []
            for p in row['images']:
                with Image.open(root / p) as im:
                    images.append(im.convert('RGB'))
            messages = typed_messages(row, images)[:1]  # No gold answer in generation input.
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            batch = processor(text=[text], images=images, return_tensors='pt').to('cuda')
            if batch['input_ids'].shape[1] > 16384:
                raise ValueError('No silent truncation')
            with torch.inference_mode():
                generated = model.generate(**batch, do_sample=False, max_new_tokens=256)
            answer = processor.tokenizer.decode(generated[0, batch['input_ids'].shape[1]:], skip_special_tokens=True).strip()
            record = {'id': row['id'], 'source_group': row['source_group'], 'answer': answer,
                      'gold_assistant_used_in_input': False}
            try:
                if row['task'].endswith('_x20'):
                    parsed = decode_output(answer, row['task'], image_count=len(images))
                    record['importance_mean'] = [v / 20 for v in parsed['scores_x20']]
                else:
                    import re
                    prompt = row['messages'][0]['content']
                    ratio = tuple(map(int, re.search(r'to (\d+):(\d+)', prompt).groups()))
                    record['parsed'] = decode_output(answer, row['task'], source_size=images[0].size, ratio=ratio)
                record['valid'] = True
            except (ValueError, TypeError, KeyError) as exc:
                record['valid'] = False
                record['error'] = str(exc)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            f.flush()


if __name__ == '__main__':
    main()
