"""Check raw frame identities/geometry and render unchanged crop coordinates."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import math
import sys
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
raw = root / 'raw' / (sys.argv[1] if len(sys.argv)>1 else 'image_v2')
input_dir = root / 'input/keyframes_v1'
meta = json.loads((input_dir / 'manifest.json').read_text(encoding='utf-8'))
labels = json.loads((raw / 'crop_keyframes.json').read_text(encoding='utf-8-sig'))
highlight_path = raw / 'highlights.json'
if raw.name == 'image_v3':
    # The correction request is spatial only; temporal labels remain the
    # unchanged first-pass output, not a second annotation run.
    highlight_path = root / 'raw/image_v2/highlights.json'
highlights = json.loads(highlight_path.read_text(encoding='utf-8-sig'))
timeline = json.loads((root / 'input/timeline_v1/manifest.json').read_text(encoding='utf-8'))
issues = []
def number(x):
    return not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)
def ratio(crop):
    value = crop.get('targetRatioWH')
    if isinstance(value, str):
        return [int(x) for x in value.split(':')]
    return value
frames = labels.get('frames', [])
if len(frames) != 8:
    issues.append('FRAME_COUNT')
by_index = {f.get('probe_index'): f for f in frames}
if set(by_index) != set(range(8)) or len(by_index) != len(frames):
    issues.append('FRAME_KEY_SET')
for record in meta['frames']:
    index = record['probe_index']
    row = by_index.get(index, {})
    if row.get('frame_index') != record['frame_index']:
        issues.append(f'FRAME_ID_{index}')
    t = row.get('pts_seconds')
    if not number(t) or abs(t - record['pts_seconds']) > 1e-9:
        issues.append(f'PTS_{index}')
    # Both manifest-relative and input-directory-relative references resolve
    # to the same frozen PNG. No other path form is accepted.
    if row.get('observed_file') not in [record['file'], 'keyframes_v1/' + record['file']]:
        issues.append(f'FILE_{index}')
    path = input_dir / record['file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['png_sha256']:
        issues.append(f'INPUT_CHANGED_{index}')
    crops = row.get('crops', [])
    if sorted(ratio(c) for c in crops) != [[9, 16], [16, 9]]:
        issues.append(f'RATIO_SET_{index}')
    for crop in crops:
        if crop.get('state') == 'UNKNOWN':
            continue
        box = crop.get('box_xyw')
        if crop.get('state') != 'CROP' or not isinstance(box, list) or len(box) != 3 or not all(number(v) for v in box):
            issues.append(f'BOX_SCHEMA_{index}')
            continue
        x, y, w = box
        tw, th = ratio(crop)
        h = w * th / tw
        if min(x, y) < 0 or w <= 0 or x+w > 640+1e-9 or y+h > 360+1e-9:
            issues.append(f'BOX_BOUNDS_{index}_{tw}:{th}')
events = highlights.get('events', [])
for index, event in enumerate(events):
    start, end = event.get('start_seconds'), event.get('end_seconds_exclusive')
    if not number(start) or not number(end) or not 0 <= start < end <= meta['source_duration_seconds']:
        issues.append(f'TIME_{index}')
for doc in [labels, highlights]:
    if doc.get('source_id') != meta['source_id']:
        issues.append('SOURCE_ID')
expected_crops = {f'k{i:02d}.png' for i in range(8)}
if raw.name == 'image_v3':
    expected_crops = {f'review_k{i:02d}.png' for i in range(8)}
expected_sheets = {f'timeline_{i:02d}.png' for i in range(13)}
def observed_names(doc):
    return {Path(str(x).replace('\\','/')).name for x in doc.get('observed_files', [])}
reported_reads = {'crop_expected': 8, 'crop_reported': len(observed_names(labels) & expected_crops),
                  'timeline_expected': 13, 'timeline_reported': len(observed_names(highlights) & expected_sheets)}
intervals = sorted((e['start_seconds'], e['end_seconds_exclusive']) for e in events
                   if number(e.get('start_seconds')) and number(e.get('end_seconds_exclusive')))
union = []
for start, end in intervals:
    if union and start <= union[-1][1]:
        union[-1][1] = max(union[-1][1], end)
    else:
        union.append([start,end])
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PASS_RAW_FRAME_IDENTITY_GEOMETRY_AND_TIME_BOUNDS' if not issues else 'LABEL_ISSUES',
    'model_ui': '豆包 2.1 Pro', 'source_id': meta['source_id'], 'frame_count': len(frames),
    'crop_states': dict(Counter(c.get('state') for f in frames for c in f.get('crops',[]))),
    'highlights': len(events), 'union_selected_seconds': sum(e-s for s,e in union),
    'reported_reads': reported_reads, 'image_input_not_native_video': True,
    'spatial_review_panels': raw.name == 'image_v3',
    'temporal_label_file': str(highlight_path),
    'full_source_frame_observation': False, 'human_crop_truth_available': False,
    'issues': issues, 'raw_files': [{'path':str(p), 'bytes':p.stat().st_size,
      'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(raw.glob('*.json'))]}
suffix = '' if raw.name == 'image_v2' else '_' + raw.name
(root / ('image_acceptance' + suffix + '.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
if issues:
    raise SystemExit(1)

gemini_path = root.parent / 'gemini_distillation_data_20261009/annotation_pilot_01/gemini_labels.jsonl'
gemini = {r['local_index']:r for r in (json.loads(line) for line in gemini_path.read_text(encoding='utf-8').splitlines())}
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
preview = Image.new('RGB',(680,8*220),'#f5f7f9')
draw = ImageDraw.Draw(preview)
for index, record in enumerate(meta['frames']):
    row = by_index[index]
    original = Image.open(input_dir / record['file']).convert('RGB')
    marked = original.copy()
    top = index*220
    draw.text((8,top+3),f"{record['file']} / 源帧{record['frame_index']} / {record['pts_seconds']:.3f}s",fill='#16202c',font=font)
    model_rows = [('豆包',row,'#00b7c5',548)]
    if 'gemini_comparison_local_index' in record:
        model_rows.insert(0,('Gemini',gemini[record['gemini_comparison_local_index']],'#e95096',414))
    else:
        draw.text((411,top+105),'Gemini未标',fill='#64748b',font=font)
    for label, model_row, color, left in model_rows:
        crop = next(c for c in model_row['crops'] if ratio(c)==[9,16])
        draw.text((left,top+3),label,fill=color,font=font)
        if crop['state']=='UNKNOWN':
            draw.text((left,top+105),'UNKNOWN',fill='#16202c',font=font)
            continue
        x,y,w = crop['box_xyw']
        h = w*16/9
        ImageDraw.Draw(marked).rectangle((x,y,x+w-1,y+h-1),outline=color,width=3)
        portrait = original.transform((101,180),Image.Transform.EXTENT,(x,y,x+w,y+h),Image.Resampling.BICUBIC)
        preview.paste(portrait,(left,top+27))
    preview.paste(marked.resize((320,180),Image.Resampling.LANCZOS),(8,top+27))
preview.save(root / ('crop_comparison' + suffix + '.png'))
