#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
FD=/home/inspur/aic_video_work/improvement_round1/frozen_data
mkdir -p "$R/clips" "$R/frames" "$R/evidence"

echo '=== candidate dev rows (first 6) ==='
python3 - <<'PY'
import json
FD='/home/inspur/aic_video_work/improvement_round1/frozen_data/dev.jsonl'
rows=[json.loads(l) for l in open(FD) if l.strip()]
for i,r in enumerate(rows[:6]):
    print(i, r['video_id'], '|', r['video_path'])
    print('   query:', r['query'])
    print('   win  :', r['relevant_windows'], 'dur', r['duration_sec'], 'fps', r['fps'])
PY

echo
echo '=== pick 4 distinct sources, extract probe frames at 0s and 20s ==='
python3 - <<'PY'
import json, subprocess, os
FD='/home/inspur/aic_video_work/improvement_round1/frozen_data/dev.jsonl'
rows=[json.loads(l) for l in open(FD) if l.strip()]
seen=set(); picks=[]
for r in rows:
    if r['source_group'] in seen: continue
    seen.add(r['source_group']); picks.append(r)
    if len(picks)==4: break
R='/home/inspur/aic_video_work/orarl_round1'
for i,r in enumerate(picks):
    vp=r['video_path']
    print(i, r['video_id'], vp, '|', r['query'][:70])
    for t in (0, 20):
        out=f'{R}/frames/probe{i}_t{t}.jpg'
        cmd=['ffmpeg','-y','-v','error','-ss',str(t),'-i',vp,'-frames:v','1','-q:v','3',out]
        subprocess.run(cmd, check=False)
        print('   ->', out, os.path.exists(out))
PY

echo
echo '=== models config: processor_config / index present yet? ==='
ls -la "$R/model/Video-ORA-4B" 2>&1
