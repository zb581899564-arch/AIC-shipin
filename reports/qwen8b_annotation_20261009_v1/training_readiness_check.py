"""Read-only training-data checks; no model loading or training."""
import collections
import datetime
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def check():
    completion = json.loads((ROOT / 'preparation_completion.json').read_text(encoding='utf-8'))
    for name, artifact in completion['artifacts'].items():
        raw = Path(artifact['path']).read_bytes()
        assert len(raw) == artifact['bytes'], name
        assert hashlib.sha256(raw).hexdigest() == artifact['sha256'], name
    images = {}
    profiles = {}
    rows_by_name = {}
    for split in ('train', 'validation'):
        for suffix in ('', '_nonidentity'):
            name = f'crop_sft_{split}{suffix}'
            path = ROOT / 'exports' / 'codex_crop_v1' / (name + '.jsonl')
            rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
            rows_by_name[name] = rows
            assert len({row['id'] for row in rows}) == len(rows), name
            ratios = collections.Counter()
            boxes = collections.Counter()
            identity = 0
            for row in rows:
                record = row['label_record']
                assert record['split'] == split
                assert record['visual_check']['verdict'] == 'PASS'
                assert row['images'] == [record['image_path']]
                path = Path(row['images'][0])
                if str(path) not in images:
                    raw = path.read_bytes()
                    assert hashlib.sha256(raw).hexdigest() == record['png_sha256']
                    with Image.open(path) as im:
                        rgb = im.convert('RGB')
                        rgb.load()
                        images[str(path)] = (rgb.size, hashlib.sha256(rgb.tobytes()).hexdigest())
                (iw, ih), pixel_hash = images[str(path)]
                x, y, w, h = record['box_xywh']
                assert all(type(v) is int for v in (x, y, w, h))
                assert min(x, y) >= 0 and min(w, h) > 0
                assert x + w <= iw and y + h <= ih
                rw, rh = record['ratio']
                assert w * rh == h * rw
                assert [m['role'] for m in row['messages']] == ['user', 'assistant']
                prompt = row['messages'][0]['content']
                assert prompt.count('<image>') == 1
                assert f'{rw}:{rh}' in prompt and f'{iw}x{ih}' in prompt
                assert json.loads(row['messages'][1]['content']) == {'box_xyw': [x, y, w]}
                assert row['source_id'] == record['source_id']
                assert row['source_group'] == record['source_group']
                ratios[f'{rw}:{rh}'] += 1
                boxes[(rw, rh, x, y, w, h)] += 1
                identity += int((x, y, w, h) == (0, 0, iw, ih))
            profiles[name] = {
                'rows': len(rows), 'source_groups': len({r['source_group'] for r in rows}),
                'ratio_counts': dict(ratios), 'identity_rows': identity,
                'distinct_boxes': len(boxes),
                'most_frequent_box': [{'ratio': list(k[:2]), 'box_xywh': list(k[2:]), 'count': v}
                                      for k, v in boxes.most_common(3)],
            }
            if suffix:
                assert identity == 0
                full = {r['id']: r for r in rows_by_name[f'crop_sft_{split}']}
                assert all(full[r['id']] == r for r in rows)
    train = rows_by_name['crop_sft_train']
    val = rows_by_name['crop_sft_validation']
    assert not ({r['source_group'] for r in train} & {r['source_group'] for r in val})
    train_hashes = {images[r['images'][0]][1] for r in train}
    val_hashes = {images[r['images'][0]][1] for r in val}
    cross_pixel_duplicates = train_hashes & val_hashes
    temporal = json.loads((ROOT / 'exports' / 'temporal_independent_audit.json').read_text(encoding='utf-8'))
    return {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_DATA_AND_IMAGE_CONTRACT_ONLY',
        'final_artifacts_hash_verified': len(completion['artifacts']),
        'unique_sft_image_paths_opened': len(images),
        'same_source_train_validation_overlap': 0,
        'exact_rgb_train_validation_overlap': len(cross_pixel_duplicates),
        'profiles': profiles,
        'temporal_sources': temporal['completed_sources'],
        'temporal_event_states': temporal['event_states'],
        'temporal_sft_rows': temporal['complete_temporal_sft_rows'],
        'temporal_quarantined_sources': temporal['known_temporal_alignment_failures'],
        'assessment': {
            'crop_pilot_data_ready': not cross_pixel_duplicates,
            'production_quality_proven': False,
            'processor_collator_training_dry_run_performed': False,
            'spatial_output_contract': 'integer pixel box_xyw, derived aspect-ratio height',
            'temporal_training_ready': False,
            'limitations': ['Model annotation and self-review, no independent human gold',
                            'Only 50 videos and 12 sampled frames per video',
                            '460 of 679 accepted crops retain the entire source image',
                            'No supervised empty/abstain targets',
                            'Current training-loader compatibility not established; image placeholder must resolve to actual vision input',
                            'No tokenization, assistant-only masking, loss or optimizer smoke run',
                            'No near-duplicate or reencoded-content leakage proof'],
        },
        'model_loaded': False, 'training_started': False,
    }


if __name__ == '__main__':
    result = check()
    out = ROOT / 'training_readiness_audit.json'
    assert not out.exists(), 'Preserve prior readiness audit; use a new version.'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
