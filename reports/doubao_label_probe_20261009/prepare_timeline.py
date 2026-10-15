"""Native first frame at/after every integer second, shown as timed contact sheets."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import av
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
source_dir = root.parent / 'antigravity_label_probe_20261009/input/native_video_tvsum_v1'
meta = json.loads((source_dir / 'manifest.json').read_text(encoding='utf-8'))
video = source_dir / meta['file']
assert hashlib.sha256(video.read_bytes()).hexdigest() == meta['media_sha256']
dest = root / 'input/timeline_v1'
dest.mkdir(parents=True, exist_ok=False)
records = []
target = 0
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    for ordinal, frame in enumerate(container.decode(stream)):
        stamp = Fraction(frame.pts) * frame.time_base
        if stamp >= target:
            rgb = frame.to_ndarray(format='rgb24')
            name = f's{target:03d}.png'
            Image.fromarray(rgb).save(dest / name)
            records.append({'requested_seconds': target, 'pts_seconds': float(stamp),
                'pts': frame.pts, 'time_base': [frame.time_base.numerator, frame.time_base.denominator],
                'frame_index': ordinal, 'file': name,
                'rgb24_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                'png_sha256': hashlib.sha256((dest / name).read_bytes()).hexdigest()})
            target += 1
assert len(records) == 146, len(records)
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
sheets = []
for index, begin in enumerate(range(0, len(records), 12)):
    selected = records[begin:begin+12]
    sheet = Image.new('RGB', (990, 816), '#f7f8fa')
    draw = ImageDraw.Draw(sheet)
    for local, record in enumerate(selected):
        x, y = (local % 3) * 330, (local // 3) * 204
        draw.text((x+5, y+3), f"t={record['pts_seconds']:.3f}s / source frame {record['frame_index']}", fill='#111827', font=font)
        im = Image.open(dest / record['file']).convert('RGB')
        sheet.paste(im.resize((320,180), Image.Resampling.LANCZOS), (x+5, y+24))
    name = f'timeline_{index:02d}.png'
    sheet.save(dest / name)
    sheets.append({'file': name, 'samples': len(selected),
        'first_seconds': selected[0]['pts_seconds'], 'last_seconds': selected[-1]['pts_seconds'],
        'sha256': hashlib.sha256((dest / name).read_bytes()).hexdigest()})
manifest = {'source_id': meta['source_id'], 'media_sha256': meta['media_sha256'],
    'duration_seconds': meta['duration_seconds_metadata'],
    'input_mode': 'Native PTS frames, sampled at one second intervals, contact sheets resized for viewing',
    'selection_policy': 'First decoded native frame with PTS >= each integer second 0..145',
    'full_source_frame_observation': False, 'frames': records, 'sheets': sheets}
(dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'native_samples': len(records), 'sheets': len(sheets)}, ensure_ascii=False))
