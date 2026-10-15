"""Real-image batching and invalid-output checks. No model weights or optimizer."""
import importlib.metadata
import json
from pathlib import Path

import torch
from transformers import AutoProcessor

from sft_contract import ImageSFTCollator, decode_output, load_rows

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    rows = load_rows(HERE / 'data/temporal_fixed_validation.jsonl', ROOT)
    examples = [max(rows, key=lambda r: len(r['images'])), min(rows, key=lambda r: len(r['images']))]
    processor = AutoProcessor.from_pretrained(HERE / 'processor_snapshot', local_files_only=True, min_pixels=4096, max_pixels=65536)
    collator = ImageSFTCollator(processor, ROOT)
    batch = collator(examples)
    assert batch['image_grid_thw'].shape[0] == sum(len(r['images']) for r in examples)
    assert bool((batch['labels'][batch['attention_mask'] == 0] == -100).all())
    for i, row in enumerate(examples):
        ids = batch['labels'][i][batch['labels'][i] != -100]
        answer = processor.tokenizer.decode(ids, skip_special_tokens=True).strip()
        assert json.loads(answer) == json.loads(row['messages'][1]['content'])
    assert all(t.device.type == 'cpu' for t in batch.values())
    assert not torch.cuda.is_initialized()
    bad_temporal = ['{"scores_x20":[19]}', '{"scores_x20":[101]}', '{"scores_x20":[true]}',
                    '{"scores_x20":[40.5]}', '{"scores_x20":[40,41]}', '{"scores_x20":[40],"other":1}']
    for text in bad_temporal:
        try:
            decode_output(text, 'temporal_tvsum_importance_x20', image_count=1)
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed output was accepted')
    for text in ['{"box_xyw":[630,0,198]}', '{"box_xyw":[0,0,199]}', '{"box_xyw":[0,-1,198]}']:
        try:
            decode_output(text, 'spatial_pixel_crop', source_size=(640,360), ratio=(9,16))
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed crop accepted')
    valid = decode_output('{"box_xyw":[187,4,198]}', 'spatial_pixel_crop', source_size=(640,360), ratio=(9,16))
    assert valid == {'box_xywh': [187,4,198,352]}
    versions = {}
    for package in ['torch','transformers','peft','accelerate','Pillow','scipy']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    report = {'status': 'PASS_REAL_IMAGE_BATCH_PADDING_MASKING_AND_STRICT_OUTPUT_CHECKS',
              'batch_shape': list(batch['input_ids'].shape), 'real_images': sum(len(r['images']) for r in examples),
              'assistant_roundtrip_exact': True, 'all_tensors_CPU': True, 'CUDA_initialized': False,
              'invalid_temporal_cases_rejected': len(bad_temporal), 'invalid_crop_cases_rejected': 3,
              'versions': versions,
              'runtime_scope': 'Windows CPU data preflight; Linux training runtime is checked separately',
              'model_weights_loaded': False, 'optimizer_started': False,
              'echo_evaluation_is_fixture_not_student_performance': True}
    out = HERE / 'runtime_contract_checks.json'
    assert not out.exists()
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
