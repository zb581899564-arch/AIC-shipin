"""Read-only progress fields; never expose source content or model text."""
import json,os
from pathlib import Path
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL=RUN/'controller';OUT=RUN/'baseline_a_pts_v1/rematch_e2e_recovery_01'
result={}
for name in ('format_pipeline_latest.json','format_pipeline_completion.json'):
    p=CTRL/name
    if p.exists():
        row=json.loads(p.read_text())
        result[name]={k:v for k,v in row.items() if k in ('stage','checked_utc','pid','actual_scheduling','failure_type','failure','candidate_sha256','candidate_bytes','videos','selected_frames')}
        if 'pid' in row:result[name]['process_exists']=Path('/proc/'+str(row['pid'])).exists()
total=valid=invalid=incomplete=0
file=OUT/'anchor_output.jsonl'
if file.exists():
    with file.open() as stream:
        for line in stream:
            if not line.strip():continue
            try:row=json.loads(line)
            except json.JSONDecodeError:
                incomplete+=1;continue
            total+=1
            valid+=int(row.get('output_valid') is True)
            invalid+=int(row.get('output_valid') is False)
result['partial_anchor_file_progress']=dict(rows=total,valid=valid,invalid=invalid,incomplete_stream_lines=incomplete,
    file_bytes=file.stat().st_size if file.exists() else 0,final_acceptance=False)
active=Path('/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json')
if active.exists():
    row=json.loads(active.read_text());result['active_job']={k:row.get(k) for k in ('name','elapsed_seconds','runner_pid','child_pid','sampled_peak_memory_mib','last_checked_utc')}
    result['active_job']['child_process_exists']=Path('/proc/'+str(row['child_pid'])).exists()
print(json.dumps(result))
