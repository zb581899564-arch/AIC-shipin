"""Prepare eight fixed native-frame images, without using model annotations."""
from pathlib import Path
import hashlib
import json
import shutil
import av
from PIL import Image

root = Path(__file__).resolve().parent
reports = root.parent
source_dir = reports / 'antigravity_label_probe_20261009/input'
video_dir = source_dir / 'native_video_tvsum_v1'
meta = json.loads((video_dir / 'manifest.json').read_text(encoding='utf-8'))
video = video_dir / meta['file']
assert hashlib.sha256(video.read_bytes()).hexdigest() == meta['media_sha256']
old_dir = source_dir / 'real_tvsum_v1'
old = json.loads((old_dir / 'manifest.json').read_text(encoding='utf-8'))
dest = root / 'input/keyframes_v1'
dest.mkdir(parents=True, exist_ok=False)
records = []
for ordinal, local_index in enumerate([0, 8, 24, 32, 47]):
    item = old['frames'][local_index]
    src = old_dir / item['file']
    assert hashlib.sha256(src.read_bytes()).hexdigest() == item['png_sha256']
    name = f'k{ordinal:02d}.png'
    shutil.copyfile(src, dest / name)
    records.append({**item, 'file': name, 'probe_index': ordinal,
                    'requested_seconds': item['pts_seconds'],
                    'actual_pts_seconds': item['pts_seconds'],
                    'gemini_comparison_local_index': local_index})
targets = iter([50.5, 86.25, 135.0])
target = next(targets, None)
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    for ordinal, frame in enumerate(container.decode(stream)):
        stamp = float(frame.pts * frame.time_base)
        if target is not None and stamp >= target:
            index = len(records)
            name = f'k{index:02d}.png'
            rgb = frame.to_ndarray(format='rgb24')
            Image.fromarray(rgb).save(dest / name)
            records.append({'file': name, 'probe_index': index,
                'frame_index': ordinal, 'requested_seconds': target,
                'pts': frame.pts, 'time_base': [frame.time_base.numerator, frame.time_base.denominator],
                'actual_pts_seconds': stamp, 'pts_seconds': stamp,
                'width': rgb.shape[1], 'height': rgb.shape[0],
                'png_sha256': hashlib.sha256((dest / name).read_bytes()).hexdigest(),
                'rgb24_sha256': hashlib.sha256(rgb.tobytes()).hexdigest()})
            target = next(targets, None)
        if target is None:
            break
assert len(records) == 8
manifest = {'purpose': 'Explicit native-frame fallback diagnostic; not native video input',
    'source_id': meta['source_id'], 'media_sha256': meta['media_sha256'],
    'source_duration_seconds': meta['duration_seconds_metadata'],
    'selection_policy': 'Five fixed previous frame positions and first native PTS at or after 50.5/86.25/135 seconds',
    'target_ratios': [[16, 9], [9, 16]], 'frames': records}
(dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'count': len(records), 'input': str(dest)}, ensure_ascii=False))
