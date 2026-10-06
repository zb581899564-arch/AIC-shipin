#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
python3 - <<'PY'
import json
p='/home/inspur/aic_video_work/orarl_round1/src/OraRL/data/eval/datasets.jsonl'
want={'tracking','temporal_grounding','spatial_grounding'}
for line in open(p,encoding='utf-8'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d['benchmark'] in want and 'test_a' not in d['annotation_path'] and 'test_b' not in d['annotation_path']:
        print('=====', d['benchmark'], d['annotation_path'])
        print('evaluation:', json.dumps(d['evaluation'], ensure_ascii=False))
        print('preprocessing:', json.dumps(d.get('preprocessing'), ensure_ascii=False))
        print('legacy_environment:', json.dumps(d.get('legacy_environment'), indent=1, ensure_ascii=False, sort_keys=True))
        print()
PY
echo '=== DOWNLOAD STATUS ==='
du -sh "$R/model/Video-ORA-4B" 2>&1
ls -la "$R/model/Video-ORA-4B" 2>&1
echo
tail -c 800 "$R/logs/download_model.log" 2>&1
