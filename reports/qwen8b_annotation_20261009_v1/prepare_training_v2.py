"""Prepare exact native-ordinal TVSum supervision, not Gemini event pseudo truth."""
import collections
import datetime
import hashlib
import io
import json
import shutil
import zipfile
from fractions import Fraction
from pathlib import Path

import av
import h5py
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'training_v2'
OFFICIAL = ROOT.parent / 'gemini_distillation_data_20261009/data/tvsum/ydata-tvsum50-v1_1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), str(path)
    with path.open('x', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')


def load_humans():
    with zipfile.ZipFile(OFFICIAL / 'ydata-tvsum50-data.zip') as z:
        raw_tsv = z.read('data/ydata-tvsum50-anno.tsv')
    by_id = collections.defaultdict(list)
    for line in raw_tsv.decode('utf-8-sig').splitlines():
        sid, category, scores = line.split('\t')
        by_id[sid].append(np.asarray([int(x) for x in scores.split(',')], dtype=np.uint8))
    with zipfile.ZipFile(OFFICIAL / 'ydata-tvsum50-matlab.zip') as z:
        raw_mat = z.read('matlab/ydata-tvsum50.mat')
    result = {}
    with h5py.File(io.BytesIO(raw_mat), 'r') as f:
        g = f['tvsum50']
        for i in range(len(g['video'])):
            sid = ''.join(chr(int(x)) for x in f[g['video'][i, 0]][()].flatten())
            u = f[g['user_anno'][i, 0]][()]
            gt = f[g['gt_score'][i, 0]][()].reshape(-1)
            n = int(f[g['nframes'][i, 0]][()].item())
            assert u.shape == (20, n) and gt.shape == (n,)
            assert np.isfinite(u).all() and np.isin(u, [1, 2, 3, 4, 5]).all()
            assert np.array_equal(u.mean(axis=0), gt)
            assert len(by_id[sid]) == 20
            # Order of the twenty workers does not affect the average; preserve multiplicities.
            assert collections.Counter(r.tobytes() for r in u.astype(np.uint8)) == collections.Counter(r.tobytes() for r in by_id[sid])
            result[sid] = u.astype(np.uint8)
    assert len(result) == 50
    return result, {'tsv_member_sha256': hashlib.sha256(raw_tsv).hexdigest(),
                    'mat_member_sha256': hashlib.sha256(raw_mat).hexdigest(),
                    'tsv_annotations': 1000, 'workers_per_source': 20,
                    'tsv_mat_worker_vectors_exact': True, 'mat_mean_recomputed_exact': True}


def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'data_preparation.json').exists(), 'Do not repeat completed preparation.'
    humans, evidence = load_humans()
    corpus = json.loads((ROOT / 'corpus.json').read_text(encoding='utf-8'))['sources']
    candidates = [json.loads(s) for s in (ROOT / 'exports/temporal_event_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    # Capacity based on actual sources and maximum retained sample-image pixels.
    projected = sum((u.shape[1] // 24 + 1) * 640 * 480 * 3 for u in humans.values())
    assert shutil.disk_usage(OUT).free > projected
    temporal = {'train': [], 'validation': []}
    all_blocks, excluded, event_checks, source_reports = [], [], [], []
    for index, m in enumerate(corpus):
        sid = m['source_id']
        save(OUT / 'progress.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stage': 'BUILDING_NATIVE_HUMAN_TARGETS',
                                  'done_sources': index, 'expected_sources': 50, 'active_source': sid})
        media = ROOT / 'input' / sid / m['media_file']
        assert sha(media) == m['media_sha256']
        pts_file = ROOT / 'input' / sid / 'native_pts.npz'
        assert sha(pts_file) == m['native_pts_sha256']
        pts = np.load(pts_file)['pts'].astype(np.int64)
        assert len(pts) == m['native_frames'] and np.all(np.diff(pts) > 0)
        tb = Fraction(*m['native_time_base'])
        times = [Fraction(int(p) - int(pts[0])) * tb for p in pts]
        duration = Fraction(str(m['source_duration_seconds']))
        u = humans[sid]
        admissible = u.shape[1] == len(pts)
        if not admissible:
            excluded.append({'source_id': sid, 'split': m['split'], 'native_frames': len(pts), 'human_frames': u.shape[1],
                             'reason': 'NATIVE_HUMAN_FRAME_COUNT_MISMATCH_NO_SHIFT_PADDING_OR_INTERPOLATION'})
        # Every original candidate receives a disposition. Semantic/event-boundary truth is not asserted.
        for event in [e for e in candidates if e['source_id'] == sid]:
            e = event['event']; a = Fraction(str(e['start_seconds'])); b = Fraction(str(e['end_seconds_exclusive']))
            ids = [i for i, t in enumerate(times) if a <= t < b]
            valid = 0 <= a < b <= duration and bool(ids)
            check = {'source_id': sid, 'event_index': event['event_index'], 'original_state': e['state'],
                     'start_seconds': float(a), 'end_seconds_exclusive': float(b),
                     'first_native_ordinal': ids[0] if ids else None, 'end_native_ordinal_exclusive': ids[-1] + 1 if ids else None,
                     'native_domain_valid': valid, 'raw_sha256': event['raw_sha256'],
                     'disposition': 'EXCLUDE_GEMINI_EVENT_BOUNDARIES_FROM_TRAINING',
                     'semantic_event_boundary_verified': False,
                     'reason': 'Native time mapping alone does not prove event boundaries; use source-provided human frame scores instead.'}
            if admissible and valid:
                votes = u[:, ids]
                check['independent_human_importance_mean'] = float(votes.mean())
            event_checks.append(check)
        if not admissible:
            print(json.dumps({'source_id': sid, 'status': 'EXCLUDED_FRAME_COUNT_MISMATCH'}), flush=True)
            continue
        # Preserve the original expanded worker vectors: no synthetic 2-second resampling.
        starts = np.r_[0, np.flatnonzero(np.any(np.diff(u.astype(np.int16), axis=1) != 0, axis=0)) + 1]
        ends = np.r_[starts[1:], len(pts)]
        src_blocks = []
        for k, (a, b) in enumerate(zip(starts, ends)):
            a, b = int(a), int(b)
            assert np.all(u[:, a:b] == u[:, a:a+1])
            ordinal = (a + b - 1) // 2
            votes = u[:, ordinal].astype(int).tolist()
            vote_sum = sum(votes)
            # Frozen aggregation: average of twenty scores, nearest integer, exact half-up.
            score = (vote_sum + 10) // 20
            row = {'source_id': sid, 'source_group': m['source_group'], 'split': m['split'], 'block_index': k,
                   'first_native_ordinal': a, 'end_native_ordinal_exclusive': b,
                   'start_relative_pts': int(pts[a]) - int(pts[0]),
                   'end_relative_pts_exclusive': int(pts[b]) - int(pts[0]) if b < len(pts) else None,
                   'start_seconds': float(times[a]), 'end_seconds_exclusive': float(times[b] if b < len(pts) else duration),
                   'time_base': list(m['native_time_base']), 'sample_native_ordinal': ordinal,
                   'sample_relative_pts': int(pts[ordinal]) - int(pts[0]), 'sample_seconds': float(times[ordinal]),
                   'worker_scores': votes, 'worker_score_sum': vote_sum, 'human_mean': vote_sum / 20,
                   'target_score': score, 'target_scale': 'TVSum importance integer 1..5, exact half-up mean',
                   'media_sha256': m['media_sha256'], 'native_pts_sha256': m['native_pts_sha256'],
                   'label_source': 'ORIGINAL_TVSUM_20_HUMAN_WORKERS',
                   'semantic_event_boundary_claim': False}
            src_blocks.append(row)
        assert src_blocks[0]['first_native_ordinal'] == 0 and src_blocks[-1]['end_native_ordinal_exclusive'] == len(pts)
        assert all(a['end_native_ordinal_exclusive'] == b['first_native_ordinal'] for a, b in zip(src_blocks, src_blocks[1:]))
        dest = OUT / 'temporal_frames' / sid
        dest.mkdir(parents=True, exist_ok=True)
        by_ordinal = {b['sample_native_ordinal']: b for b in src_blocks}
        with av.open(str(media)) as c:
            stream = c.streams.video[0]
            actual_count = 0
            for ordinal, frame in enumerate(c.decode(stream)):
                assert ordinal < len(pts) and frame.pts == int(pts[ordinal])
                actual_count += 1
                if ordinal in by_ordinal:
                    block = by_ordinal[ordinal]
                    image = dest / f'n{ordinal:07d}.png'
                    if image.exists():
                        # Interrupted preparation reuse only if decoded pixels are identical.
                        from PIL import Image
                        with Image.open(image) as old:
                            assert np.array_equal(np.asarray(old.convert('RGB')), frame.to_ndarray(format='rgb24'))
                    else:
                        frame.to_image().save(image)
                    block['image'] = image.relative_to(ROOT).as_posix()
                    block['image_sha256'] = sha(image)
                    block['image_dimensions'] = [frame.width, frame.height]
            assert actual_count == len(pts)
        for w in range(0, len(src_blocks), 16):
            block_rows = src_blocks[w:w+16]
            descriptors = '\n'.join(f'Frame {i}: native ordinal {b["sample_native_ordinal"]}, time {b["sample_seconds"]:.6f} s, size {b["image_dimensions"][0]}x{b["image_dimensions"][1]}.' for i, b in enumerate(block_rows))
            prompt = ('Rate the visual importance of each shown frame within this ordered video sequence. '
                      'Use the TVSum importance scale: 1 low, 2, 3 medium, 4, 5 high. '
                      'Return ONLY JSON {"scores":[...]} with exactly one integer 1..5 per shown frame, in the same order. '
                      'This is frame importance, not precise semantic event start/end detection.\n' + descriptors)
            row = {'id': f'{sid}:human_window:{w//16:04d}', 'source_id': sid, 'source_group': m['source_group'],
                   'images': [b['image'] for b in block_rows],
                   'messages': [{'role': 'user', 'content': '<image>\n' * len(block_rows) + prompt},
                                {'role': 'assistant', 'content': json.dumps({'scores': [b['target_score'] for b in block_rows]}, separators=(',', ':'))}],
                   'task': 'temporal_tvsum_frame_importance', 'split': m['split'], 'label_source': 'ORIGINAL_TVSUM_20_HUMAN_WORKERS',
                   'media_sha256': m['media_sha256'], 'native_pts_sha256': m['native_pts_sha256'],
                   'block_indices': [b['block_index'] for b in block_rows], 'native_ordinals': [b['sample_native_ordinal'] for b in block_rows]}
            temporal[m['split']].append(row)
        all_blocks.extend(src_blocks)
        source_reports.append({'source_id': sid, 'split': m['split'], 'native_frames': len(pts), 'human_blocks': len(src_blocks),
                               'native_pts_all_frames_redecoded_exact': True, 'coverage': 'ALL_NATIVE_ORDINALS_HAVE_ORIGINAL_HUMAN_LABELS'})
        print(json.dumps({'source_id': sid, 'status': 'PASS_NATIVE_HUMAN_LABELS', 'blocks': len(src_blocks)}), flush=True)
    for split, rows in temporal.items():
        jsonl(OUT / 'data' / f'temporal_{split}.jsonl', rows)
        for name, suffix in [('crop', '_nonidentity'), ('crop_full', '')]:
            originals = [json.loads(s) for s in (ROOT / f'exports/codex_crop_v1/crop_sft_{split}{suffix}.jsonl').read_text(encoding='utf-8').splitlines()]
            portable = []
            for row in originals:
                portable.append({'id': row['id'], 'source_id': row['source_id'], 'source_group': row['source_group'],
                                 'images': [Path(p).relative_to(ROOT).as_posix() for p in row['images']],
                                 'messages': row['messages'], 'task': 'spatial_pixel_crop', 'split': split,
                                 'annotation_quality': row['annotation_quality'],
                                 'source_media_sha256': row['label_record']['source_media_sha256'],
                                 'image_sha256': row['label_record']['png_sha256']})
            jsonl(OUT / 'data' / f'{name}_{split}.jsonl', portable)
    jsonl(OUT / 'human_native_blocks.jsonl', all_blocks)
    jsonl(OUT / 'gemini_boundary_dispositions.jsonl', event_checks)
    assert len(event_checks) == 600
    assert not ({r['source_group'] for r in temporal['train']} & {r['source_group'] for r in temporal['validation']})
    files = list((OUT / 'data').glob('*.jsonl')) + [OUT / 'human_native_blocks.jsonl', OUT / 'gemini_boundary_dispositions.jsonl']
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_NATIVE_HUMAN_IMPORTANCE_DATA_PREPARATION', 'human_evidence': evidence,
              'accepted_sources': len(source_reports), 'excluded_sources': excluded,
              'native_human_blocks': len(all_blocks), 'temporal_windows': {s: len(rs) for s, rs in temporal.items()},
              'temporal_source_groups': {s: len({r['source_group'] for r in rs}) for s, rs in temporal.items()},
              'target_histogram': dict(sorted(collections.Counter(b['target_score'] for b in all_blocks).items())),
              'gemini_candidates_disposed': len(event_checks), 'gemini_event_boundaries_used_as_targets': 0,
              'all_native_human_domains_contiguous': True, 'semantic_event_boundaries_verified': False,
              'source_reports': source_reports, 'artifacts': {p.relative_to(OUT).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files},
              'student_training_started': False, 'gpu_started': False,
              'limitation': 'TVSum importance ratings are human supervision, not AIC event-boundary gold or official competition scores.'}
    save(OUT / 'data_preparation.json', report)
    save(OUT / 'progress.json', {'utc': report['utc'], 'stage': 'COMPLETE_DATA_PREPARATION', 'accepted_sources': len(source_reports), 'excluded_sources': excluded})
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_reports', 'artifacts')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
