"""Read execution failure fields only; never display generated text or media."""
import datetime as dt
import json
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
if __name__ == '__main__':
    records, completed = [], 0
    path = RUN/'baseline_a_pts_v1/rematch_e2e_01/temporal.jsonl'
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        completed += 1
        for window in row['windows']:
            if not window['output_valid']:
                records.append(dict(video_id=row['video_id'],window_index=window['index'],
                    status=window['status'],errors=window['parse_errors'],
                    clock_branch=window.get('clock_branch','CFR_LEGACY')))
    result = dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        completed_source_records=completed,failed_windows=len(records),records=records,
        model_text_displayed=False,test_media_displayed=False,quality_rules_changed=False)
    target = RUN/'controller/a_pts_failure_summary_latest.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
