"""Independent check of selected fixed-grid targets against original TSV worker scores."""
import collections
import datetime
import hashlib
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OFFICIAL = ROOT.parent / 'gemini_distillation_data_20261009/data/tvsum/ydata-tvsum50-v1_1'


def main():
    assert not (HERE / 'selected_data_audit.json').exists()
    with zipfile.ZipFile(OFFICIAL / 'ydata-tvsum50-data.zip') as z:
        lines = z.read('data/ydata-tvsum50-anno.tsv').decode('utf-8-sig').splitlines()
    human = collections.defaultdict(list)
    for line in lines:
        sid, category, scores = line.split('\t')
        human[sid].append(np.asarray([int(s) for s in scores.split(',')], dtype=np.int16))
    human = {sid: np.stack(v) for sid, v in human.items()}
    corpus = {r['source_id']: r for r in json.loads((ROOT / 'corpus.json').read_text(encoding='utf-8'))['sources']}
    samples = [json.loads(s) for s in (HERE / 'fixed_grid_samples.jsonl').read_text(encoding='utf-8').splitlines()]
    lookup = {(s['source_id'], s['grid_index']): s for s in samples}
    source_samples = collections.defaultdict(list)
    for sample in samples:
        sid = sample['source_id']; ordinal = sample['sample_native_ordinal']
        source_samples[sid].append(sample)
        assert human[sid].shape[1] == corpus[sid]['native_frames']
        assert int(human[sid][:, ordinal].sum()) == sample['scores_x20'] == sum(sample['worker_scores'])
        assert not sample['sampling_uses_human_scores_or_gemini_events']
        assert sample['first_native_ordinal'] <= ordinal < sample['end_native_ordinal_exclusive']
        assert ordinal == (sample['first_native_ordinal'] + sample['end_native_ordinal_exclusive'] - 1) // 2
        assert sample['grid_start_seconds'] == 2 * sample['grid_index']
        assert 0 < sample['grid_end_seconds_exclusive'] - sample['grid_start_seconds'] <= 2 + 1e-9
        pts = np.load(ROOT / 'input' / sid / 'native_pts.npz')['pts']
        assert int(pts[ordinal]) - int(pts[0]) == sample['sample_relative_pts']
        tb_num, tb_den = sample['time_base']
        assert math.isclose(sample['sample_seconds'], sample['sample_relative_pts'] * tb_num / tb_den, abs_tol=1e-12)
        path = ROOT / sample['image']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sample['image_sha256']
        with Image.open(path) as im:
            im.load()
            assert im.size == (corpus[sid]['stream_metadata']['width'], corpus[sid]['stream_metadata']['height'])
    for sid, ss in source_samples.items():
        assert ss[0]['first_native_ordinal'] == 0 and ss[-1]['end_native_ordinal_exclusive'] == corpus[sid]['native_frames']
        assert all(a['end_native_ordinal_exclusive'] == b['first_native_ordinal'] for a, b in zip(ss, ss[1:]))
    files = ['crop_balanced_train.jsonl', 'crop_full_validation.jsonl', 'temporal_fixed_train.jsonl', 'temporal_fixed_validation.jsonl']
    data = {name: [json.loads(s) for s in (HERE / 'data' / name).read_text(encoding='utf-8').splitlines()] for name in files}
    for name, records in data.items():
        assert len({r['id'] for r in records}) == len(records)
        split = 'train' if 'train' in name else 'validation'
        for r in records:
            assert r['split'] == split == corpus[r['source_id']]['split']
            if r['task'] == 'temporal_tvsum_importance_x20':
                selected = [lookup[r['source_id'], k] for k in r['grid_indices']]
                assert r['images'] == [s['image'] for s in selected]
                assert r['native_ordinals'] == [s['sample_native_ordinal'] for s in selected]
                assert json.loads(r['messages'][1]['content']) == {'scores_x20': [s['scores_x20'] for s in selected]}
                assert 'FIXED_LABEL_INDEPENDENT' in r['input_sampling']
                assert len(r['images']) <= 16
    for prefix in ('crop', 'temporal'):
        train_key = 'crop_balanced_train.jsonl' if prefix == 'crop' else 'temporal_fixed_train.jsonl'
        val_key = 'crop_full_validation.jsonl' if prefix == 'crop' else 'temporal_fixed_validation.jsonl'
        assert not ({r['source_group'] for r in data[train_key]} & {r['source_group'] for r in data[val_key]})
    # A constant predictor, estimated only from training labels, is the minimal regression baseline.
    train_values = np.asarray([v for r in data['temporal_fixed_train.jsonl'] for v in json.loads(r['messages'][1]['content'])['scores_x20']])
    val_values = np.asarray([v for r in data['temporal_fixed_validation.jsonl'] for v in json.loads(r['messages'][1]['content'])['scores_x20']])
    baseline = float(train_values.mean()) / 20
    report = {'status': 'PASS_INDEPENDENT_SELECTED_NATIVE_GRID_AND_ORIGINAL_HUMAN_TARGETS',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'temporal_sources': len(source_samples), 'fixed_grid_frames': len(samples),
              'selected_rows': {k: len(v) for k, v in data.items()},
              'source_split_overlap': 0, 'label_informed_input_sampling': False,
              'all_selected_scores_recomputed_from_original_tsv': True,
              'native_sample_png_hash_and_decode_verified': True,
              'constant_train_mean_baseline': {'mean_importance': baseline,
                   'validation_mae_importance': float(np.abs(val_values / 20 - baseline).mean()),
                   'validation_rmse_importance': float(np.sqrt(np.mean((val_values / 20 - baseline)**2))),
                   'note': 'Diagnostic human-reference baseline; not student performance or competition score.'},
              'gemini_event_boundaries_used': 0,
              'semantic_event_boundaries_proven': False, 'model_weights_loaded': False, 'training_started': False}
    (HERE / 'selected_data_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
