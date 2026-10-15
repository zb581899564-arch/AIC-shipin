"""Label-independent two-second native sampling with exact original human frame targets."""
import collections
import json
import sys
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from prepare_training_v2 import load_humans, save, sha, jsonl


def main():
    assert not (HERE / 'fixed_grid_preparation.json').exists()
    humans, evidence = load_humans()
    corpus = json.loads((ROOT / 'corpus.json').read_text(encoding='utf-8'))['sources']
    rows = {'train': [], 'validation': []}
    samples, exclusions, source_reports = [], [], []
    for m in corpus:
        sid = m['source_id']; u = humans[sid]
        pts = np.load(ROOT / 'input' / sid / 'native_pts.npz')['pts'].astype(np.int64)
        if u.shape[1] != len(pts):
            exclusions.append(sid)
            continue
        tb = Fraction(*m['native_time_base'])
        rel = [Fraction(int(p) - int(pts[0])) * tb for p in pts]
        duration = Fraction(str(m['source_duration_seconds']))
        grid, start, cursor = [], Fraction(0), 0
        while cursor < len(pts):
            end = min(start + 2, duration)
            first = cursor
            while cursor < len(pts) and rel[cursor] < end:
                cursor += 1
            if cursor == first:
                raise ValueError('Empty or out-of-domain fixed interval')
            ordinal = (first + cursor - 1) // 2
            image = HERE / 'temporal_frames' / sid / f'n{ordinal:07d}.png'
            sample = {'source_id': sid, 'source_group': m['source_group'], 'split': m['split'],
                      'grid_index': len(grid), 'first_native_ordinal': first, 'end_native_ordinal_exclusive': cursor,
                      'grid_start_seconds': float(start), 'grid_end_seconds_exclusive': float(end),
                      'sample_native_ordinal': ordinal, 'sample_relative_pts': int(pts[ordinal]) - int(pts[0]),
                      'time_base': m['native_time_base'], 'sample_seconds': float(rel[ordinal]),
                      'image': image.relative_to(ROOT).as_posix(), 'worker_scores': u[:, ordinal].astype(int).tolist(),
                      'scores_x20': int(u[:, ordinal].sum()), 'media_sha256': m['media_sha256'],
                      'sampling_uses_human_scores_or_gemini_events': False,
                      'target_applies_to_sampled_frame_only': True,
                      'grid_edges_are_sampling_domains_not_semantic_event_boundaries': True}
            grid.append(sample)
            start += 2
        assert grid[0]['first_native_ordinal'] == 0 and grid[-1]['end_native_ordinal_exclusive'] == len(pts)
        needed = {s['sample_native_ordinal']: s for s in grid if not (ROOT / s['image']).exists()}
        reused = len(grid) - len(needed)
        if needed:
            with av.open(str(ROOT / 'input' / sid / m['media_file'])) as c:
                actual_count = 0
                for ordinal, frame in enumerate(c.decode(c.streams.video[0])):
                    assert ordinal < len(pts) and frame.pts == int(pts[ordinal])
                    actual_count += 1
                    if ordinal in needed:
                        frame.to_image().save(ROOT / needed[ordinal]['image'])
                assert actual_count == len(pts)
        for sample in grid:
            sample['image_sha256'] = sha(ROOT / sample['image'])
        for first in range(0, len(grid), 16):
            sequence = grid[first:first+16]
            descriptors = '\n'.join(f'Frame {i}: native ordinal {s["sample_native_ordinal"]}, time {s["sample_seconds"]:.6f} s.' for i, s in enumerate(sequence))
            prompt = ('Rate the visual importance of each shown frame within this ordered video sequence. '
                      'Use TVSum average importance: 1 low, 3 medium, 5 high. '
                      'Encode the average multiplied by 20 as an integer 20..100, preserving 0.05-point precision. '
                      'Return ONLY JSON {"scores_x20":[...]} with exactly one integer per shown frame in the same order. '
                      'Divide each output by 20 to recover average importance. '
                      'This is sampled-frame importance, not semantic event start/end detection.\n' + descriptors)
            rows[m['split']].append({'id': f'{sid}:fixedgrid:{first//16:04d}', 'source_id': sid, 'source_group': m['source_group'],
                'split': m['split'], 'task': 'temporal_tvsum_importance_x20',
                'images': [s['image'] for s in sequence],
                'messages': [{'role': 'user', 'content': '<image>\n'*len(sequence)+prompt},
                             {'role': 'assistant', 'content': json.dumps({'scores_x20': [s['scores_x20'] for s in sequence]}, separators=(',', ':'))}],
                'grid_indices': [s['grid_index'] for s in sequence], 'native_ordinals': [s['sample_native_ordinal'] for s in sequence],
                'media_sha256': m['media_sha256'], 'label_source': 'ORIGINAL_TVSUM_20_HUMAN_WORKERS',
                'input_sampling': 'FIXED_LABEL_INDEPENDENT_TWO_SECOND_NATIVE_ORDINAL_MIDPOINTS'})
        samples.extend(grid)
        source_reports.append({'source_id': sid, 'samples': len(grid), 'reused_native_pngs': reused, 'new_native_pngs': len(needed)})
        print(json.dumps(source_reports[-1]), flush=True)
    for split, data in rows.items():
        jsonl(HERE / 'data' / f'temporal_fixed_{split}.jsonl', data)
    jsonl(HERE / 'fixed_grid_samples.jsonl', samples)
    histogram = collections.Counter(s['scores_x20'] for s in samples)
    report = {'status': 'SELECTED_LABEL_INDEPENDENT_FIXED_GRID_HUMAN_TARGETS',
              'human_evidence': evidence, 'accepted_sources': len(source_reports), 'excluded_sources': exclusions,
              'source_groups': {s: len({r['source_group'] for r in data}) for s, data in rows.items()},
              'windows': {s: len(data) for s, data in rows.items()}, 'native_sampled_frames': len(samples),
              'distinct_targets': len(histogram), 'target_histogram': dict(sorted(histogram.items())),
              'sampling_uses_label_changes': False, 'sampling_uses_gemini_events': False,
              'selected_targets': 'Exact sum of twenty worker ratings at each sampled native frame',
              'previous_label_change_sampled_variants_selected': False,
              'all_original_candidates_preserved': True, 'source_reports': source_reports,
              'artifacts': {p.name: sha(p) for p in list((HERE / 'data').glob('temporal_fixed_*.jsonl'))+[HERE / 'fixed_grid_samples.jsonl']}}
    save(HERE / 'fixed_grid_preparation.json', report)
    # This is a new unexecuted recipe version; earlier data and CPU receipts are preserved.
    config = json.loads((HERE / 'configs/temporal.json').read_text(encoding='utf-8'))
    config['train_file'] = 'training_v2/data/temporal_fixed_train.jsonl'
    config['validation_file'] = 'training_v2/data/temporal_fixed_validation.jsonl'
    save(HERE / 'configs/temporal_fixed.json', config)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_reports','artifacts','target_histogram','human_evidence')}), flush=True)


if __name__ == '__main__':
    main()
