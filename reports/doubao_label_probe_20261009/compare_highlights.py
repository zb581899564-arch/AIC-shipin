"""Descriptive interval comparison and one-video TVSum importance diagnostic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile
import av
import numpy as np

root = Path(__file__).resolve().parent
gemini_path = root.parent / 'antigravity_label_probe_20261009/output/native_video_tvsum_v1/highlights.json'
doubao_path = root / 'raw/image_v2/highlights.json'
docs = {'Gemini_native_MP4': json.loads(gemini_path.read_text(encoding='utf-8-sig')),
        'Doubao_1FPS_images': json.loads(doubao_path.read_text(encoding='utf-8-sig'))}
video = root.parent / 'antigravity_label_probe_20261009/input/native_video_tvsum_v1/GsAD1KT1xo8.mp4'
clock = []
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    for frame in container.decode(stream):
        clock.append(float(frame.pts * frame.time_base))
clock = np.asarray(clock)
archive_path = root.parent / 'gemini_distillation_data_20261009/data/tvsum/ydata-tvsum50-v1_1/ydata-tvsum50-data.zip'
with zipfile.ZipFile(archive_path) as z:
    payload = z.read('data/ydata-tvsum50-anno.tsv')
rows = [line.split('\t') for line in payload.decode('utf-8-sig').splitlines() if line.strip()]
chosen = [row for row in rows if row[0]=='GsAD1KT1xo8']
scores = np.asarray([[int(x) for x in row[2].split(',')] for row in chosen],dtype=float)
matched = len(chosen)==20 and scores.ndim==2 and scores.shape[1]==len(clock)
report = {'utc': datetime.now(timezone.utc).isoformat(), 'source_id': 'GsAD1KT1xo8',
    'type': 'SINGLE_VIDEO_DIAGNOSTIC_NOT_AIC_OFFICIAL_SCORE',
    'input_modes_differ': True, 'selected_duration_budget_not_equalized': True,
    'importance_is_not_crop_truth_or_precise_highlight_boundary_truth': True,
    'decoded_native_frames': len(clock), 'human_annotators': len(chosen),
    'human_vector_length': int(scores.shape[1]), 'frame_count_identity': matched,
    'alignment': 'Original decoded ordinal matched to original distributed annotation-vector index; cardinality verified, no label exposure to models',
    'annotation_archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    'models': {}}
masks = {}
for name, doc in docs.items():
    mask = np.zeros(len(clock),dtype=bool)
    for event in doc['events']:
        mask |= (clock >= event['start_seconds']) & (clock < event['end_seconds_exclusive'])
    masks[name] = mask
    value = {'events': len(doc['events']), 'selected_native_frames': int(mask.sum()),
             'selected_frame_fraction': float(mask.mean()),
             'intervals': [[e['start_seconds'],e['end_seconds_exclusive']] for e in doc['events']]}
    if matched:
        mean = scores.mean(axis=0)
        value.update({'human_importance_mean_all': float(mean.mean()),
          'human_importance_mean_selected': float(mean[mask].mean()) if mask.any() else None,
          'human_importance_mean_unselected': float(mean[~mask].mean()) if (~mask).any() else None})
    report['models'][name] = value
a,b = list(masks.values())
report['descriptive_output_overlap'] = {'intersection_native_frames': int((a&b).sum()),
    'union_native_frames': int((a|b).sum()), 'jaccard': float((a&b).sum()/(a|b).sum()) if (a|b).any() else None,
    'is_accuracy': False}
(root / 'highlight_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
