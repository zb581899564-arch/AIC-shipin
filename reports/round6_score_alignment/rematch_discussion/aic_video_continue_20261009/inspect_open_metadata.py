"""Only inspect permitted developer metadata through the existing SSH alias."""
import subprocess

REMOTE_CODE = r'''
import json
from pathlib import Path
r = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
d = json.loads((r / 'temporal_sft8b_dev_v1/input_contract.json').read_text())
print(json.dumps({'keys': list(d), 'count': len(d['records']),
    'record_keys': list(d['records'][0]),
    'first_metadata': {k: v for k, v in d['records'][0].items()
        if k not in ('segments_clip_local', 'segments', 'annotations', 'labels')}}, ensure_ascii=False))
n = json.loads((r / 'baseline_pts_v4/nontest_registry_01/clean_manifest_v2.json').read_text())
print(json.dumps({'nontest_keys': list(n), 'record_keys': list(n['records'][0]),
    'records': len(n['records']), 'sources': len({x['source_path'] for x in n['records']})}, ensure_ascii=False))
'''

if __name__ == '__main__':
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        'aic-inspur-home', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
        input=REMOTE_CODE, text=True, encoding='utf-8', capture_output=True, timeout=90)
    print(result.stdout)
    print(result.stderr)
    raise SystemExit(result.returncode)
