"""Read-only forensic audit of supplied labels; never creates training labels."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_data')
rows = [json.loads(s) for s in (ROOT/'labels/train.jsonl').read_text().splitlines() if s.strip()]
videos = collections.defaultdict(list)
for p in (ROOT/'videos').rglob('*.mp4'):
    videos[p.stem].append(p)
out = {'labels_sha256': hashlib.sha256((ROOT/'labels/train.jsonl').read_bytes()).hexdigest(),
       'rows': len(rows), 'top_level_keys': sorted(set().union(*(r.keys() for r in rows))),
       'provenance_models': dict(collections.Counter(r.get('provenance',{}).get('seed_model') for r in rows)),
       'video_metadata_examples': [], 'matched': 0, 'missing': 0,
       'clip_duration_summary': {}, 'examples': [],
       'limitations': ['Source download log proves a file was queued under the supplied folder, not archive cryptographic identity.',
                       'No recovered transform or verified training labels are produced.',
                       'Teacher text is deliberately excluded from this report.']}
durations=[]
for r in rows:
    c=r.get('clip',{}); stem=c.get('source_vid'); paths=videos.get(stem,[])
    out['matched' if paths else 'missing']+=1
    dur=c.get('end_sec',0)-c.get('start_sec',0); durations.append(dur)
    if len(out['examples'])<5:
        out['examples'].append({'source_vid':stem,'clip':c,
          'video_id':r.get('video_id'), 'video_path':r.get('video_path'),
          'media_metadata':{k:v for k,v in r.items() if k in ('video','metadata','fps','duration','duration_sec','num_frames','width','height')},
          'source_paths':[str(p) for p in paths],
          'roi_frame_range':[min((x[0] for x in r.get('cropRois',[])),default=None),max((x[0] for x in r.get('cropRois',[])),default=None)]})
durations.sort()
out['clip_duration_summary']={'min':min(durations),'median':durations[len(durations)//2],'max':max(durations)}
log=(ROOT/'bddownload.log').read_text(errors='replace')
out['label_download_log_lines']=[s for s in log.splitlines() if 'train.jsonl' in s and len(s)<1500][-15:]
out['missing_source_stems']=[r['clip']['source_vid'] for r in rows if not videos.get(r['clip']['source_vid'])]
print(json.dumps(out,ensure_ascii=False,indent=2))
