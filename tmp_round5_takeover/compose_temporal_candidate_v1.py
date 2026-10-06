#!/usr/bin/env python3
"""Compose temporal predictions with the previously validated Qwen spatial boxes.

This deliberately isolates the new temporal component. For a frame absent from
the old spatial prediction, use that video's nearest existing box. An invalid
temporal window falls back to its centered 80% span; this rule is fixed before
test inference and does not use test labels or manual review.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--temporal', required=True)
    p.add_argument('--spatial-base', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--report', required=True)
    p.add_argument('--max-invalid-window-rate', type=float, default=0.05)
    p.add_argument('--calibration-report', default='')
    a = p.parse_args()
    for name in ['out', 'report']:
        path = Path(getattr(a, name))
        if path.exists():
            raise RuntimeError(f'refusing overwrite: {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
    tmp = {str(r['video_id']): r for r in read_jsonl(a.temporal)}
    spatial = {str(r['video_id']): r for r in read_jsonl(a.spatial_base)}
    if len(tmp) != 174 or len(spatial) != 174 or set(tmp) != set(spatial):
        raise RuntimeError('expected 174 unique matching video ids')
    total_windows = sum(len(r['windows']) for r in tmp.values())
    invalid_windows = sum(not w.get('output_valid', False)
                          for r in tmp.values() for w in r['windows'])
    if not total_windows or invalid_windows / total_windows > a.max_invalid_window_rate:
        raise RuntimeError(f'temporal inference health gate: {invalid_windows}/{total_windows} '
                           f'invalid windows exceeds {a.max_invalid_window_rate:.1%}')
    calibration_factor = 1.0
    if a.calibration_report:
        calibration = json.loads(Path(a.calibration_report).read_text())
        calibration_factor = float(calibration['selected_factor'])
        if calibration_factor not in (1.0, 0.9, 0.8, 0.7):
            raise RuntimeError('unregistered calibration factor')
        if {r.get('arm') for r in tmp.values()} != {calibration['arm']}:
            raise RuntimeError('calibration arm does not match temporal inference arm')
    report = {'temporal_path': a.temporal, 'temporal_sha256': sha(a.temporal),
              'spatial_base_path': a.spatial_base,
              'spatial_base_sha256': sha(a.spatial_base),
              'frame_rounding': 'nearest integer; inclusive end',
              'missing_box': 'nearest available old spatial box',
              'invalid_window': 'centered 80% of window', 'videos': []}
    report['temporal_window_count'] = total_windows
    report['temporal_invalid_window_rate'] = invalid_windows / total_windows
    report['calibration_factor'] = calibration_factor
    report['calibration_report_sha256'] = sha(a.calibration_report) if a.calibration_report else None
    n_pred = 0
    with Path(a.out).open('w', encoding='utf-8') as f:
        for vid in sorted(tmp, key=lambda v: int(v) if v.isdigit() else v):
            t, s = tmp[vid], spatial[vid]
            if t['targetRatioWH'] != s['targetRatioWH']:
                raise RuntimeError(f'target ratio mismatch {vid}')
            n_frames, fps = int(t['n_frames']), float(t['fps'])
            assert n_frames > 1 and math.isfinite(fps) and fps > 0
            old_boxes = {}
            for pred in s['predictions']:
                frame = pred['frame']
                box = pred['bboxes']
                if type(frame) is not int or not 0 <= frame < n_frames:
                    raise RuntimeError(f'invalid old spatial frame {vid}: {frame}')
                if not (isinstance(box, list) and len(box) == 3 and
                        all(type(x) is int for x in box)):
                    raise RuntimeError(f'invalid old spatial box {vid}: {box}')
                old_boxes[frame] = box
            if not old_boxes:
                raise RuntimeError(f'no old spatial boxes for video {vid}')
            old_frames = sorted(old_boxes)
            selected = set()
            fallback_windows = 0
            intervals = []
            for w in t['windows']:
                duration = float(w['duration_sec'])
                start = float(w['start_sec'])
                end = float(w['end_sec'])
                if not (0 <= start < end <= t['duration_sec'] + 1e-3):
                    raise RuntimeError(f'invalid window boundary {vid}')
                segs = w.get('parsed_segments') if w.get('output_valid') else None
                if not segs:
                    fallback_windows += 1
                    segs = [[duration * 0.1, duration * 0.9]]
                elif calibration_factor < 1.0:
                    segs = [[(a0+b0)/2 - (b0-a0)*calibration_factor/2,
                             (a0+b0)/2 + (b0-a0)*calibration_factor/2]
                            for a0,b0 in segs]
                for a0, b0 in segs:
                    if not (0 <= a0 < b0 <= duration + 1e-3):
                        raise RuntimeError(f'invalid temporal segment {vid}: {a0},{b0}')
                    fa = max(0, min(n_frames-1, round((start+a0)*fps)))
                    fb = max(0, min(n_frames-1, round((start+b0)*fps)))
                    if fb <= fa:
                        fb = min(n_frames-1, fa+1)
                    intervals.append([fa, fb])
                    selected.update(range(fa, fb+1))
            if not selected:
                raise RuntimeError(f'empty selected video {vid}')
            predictions = []
            nearest_count = 0
            for frame in sorted(selected):
                box = old_boxes.get(frame)
                if box is None:
                    i = bisect.bisect_left(old_frames, frame)
                    options = old_frames[max(0, i-1):min(len(old_frames), i+1)]
                    nearest = min(options, key=lambda x: (abs(x-frame), x))
                    box = old_boxes[nearest]
                    nearest_count += 1
                predictions.append({'frame': frame, 'bboxes': box})
            official = {'video_id': vid, 'targetRatioWH': t['targetRatioWH'],
                        'predictions': predictions}
            f.write(json.dumps(official, ensure_ascii=False,
                               separators=(',', ':')) + '\n')
            n_pred += len(predictions)
            report['videos'].append({'video_id': vid, 'n_frames': n_frames,
                                     'n_predictions': len(predictions),
                                     'n_invalid_windows': fallback_windows,
                                     'n_nearest_old_boxes': nearest_count,
                                     'intervals': intervals})
    report['video_count'] = len(tmp)
    report['prediction_count'] = n_pred
    report['invalid_window_count'] = sum(r['n_invalid_windows'] for r in report['videos'])
    report['nearest_old_box_count'] = sum(r['n_nearest_old_boxes'] for r in report['videos'])
    report['out_sha256'] = sha(a.out)
    Path(a.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['video_count', 'prediction_count',
                                             'invalid_window_count', 'nearest_old_box_count',
                                             'out_sha256']}, indent=2))


if __name__ == '__main__':
    main()
