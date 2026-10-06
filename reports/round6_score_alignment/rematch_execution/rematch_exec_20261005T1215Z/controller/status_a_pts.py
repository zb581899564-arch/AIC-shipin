"""Compact status without displaying test media, model text or label content."""
import datetime as dt
import json
from pathlib import Path
import re

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL, OUTPUT = RUN/'controller', RUN/'baseline_a_pts_v1/rematch_e2e_01'

def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):
        return None

if __name__ == '__main__':
    result = dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        expected_sources=426, competition_upload_authorized=False, stages={})
    for name in ('preflight','temporal','select','shots','anchors','spatial','compose','package'):
        stage = read(OUTPUT/(name+'.stage.json'))
        if stage:
            result['stages'][name] = {k:stage[k] for k in ('status','videos','video_records','windows',
                'invalid_windows','selected_frames','frames','anchor_calls','rows','invalid',
                'prediction_frames','issues','wall_seconds','zip_sha256','source_lock_sha256') if k in stage}
    active = read(ROOT/'improvement_round1/active_gpu_job.json')
    result['active'] = {k:active.get(k) for k in ('name','child_pid','elapsed_seconds','sampled_peak_memory_mib')} if active else None
    for name in ('temporal','space'):
        log = CTRL/('rematch_a_pts_'+name+'_01.log')
        if log.exists():
            content = log.read_text(errors='replace')
            matches = re.findall(r'\[(\d+)/426\] windows=(\d+) failures=(\d+)',content)
            if matches:
                done,windows,failures = map(int,matches[-1])
                result['temporal_progress'] = dict(sources_completed=done,last_source_windows=windows,cumulative_failed_windows=failures)
            result[name+'_traceback_in_log'] = 'Traceback (most recent call last)' in content
        receipt = read(CTRL/('rematch_a_pts_'+name+'_01.resource.json'))
        if receipt:
            result[name+'_resource'] = {k:receipt.get(k) for k in ('status','exit_code','stop_reason','charged_seconds')}
    print(json.dumps(result),flush=True)
