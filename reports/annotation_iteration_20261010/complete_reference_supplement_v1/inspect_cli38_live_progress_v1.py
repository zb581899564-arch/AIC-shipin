"""Read-only manual retry progress; no incomplete observation acceptance."""
import json
from datetime import datetime, timezone
from pathlib import Path
R=Path(__file__).resolve().parent/'teacher_expansion'/'manual_CLI38_retry_v1'
A=R/'call38'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
raw=(A/'stream.jsonl').read_bytes();rows=[]
for line in raw.splitlines():
    try:rows.append(json.loads(line))
    except (json.JSONDecodeError,UnicodeDecodeError):pass
updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool']
done={t['step_index']:t for t in updates if t.get('state')=='DONE'}
media=[t for t in done.values() if t.get('tool_name')=='view_file' and Path(t.get('tool_info',{}).get('parameters',{}).get('AbsolutePath','')).suffix.lower() in ('.png','.jpg','.mp4')]
result=dict(utc=datetime.now(timezone.utc).isoformat(),CLI=38,raw_bytes=len(raw),unique_tool_DONE=len(done),actual_media_DONE=len(media),actual_tool_ERROR=sum(t.get('state')=='ERROR' for t in updates),new_optimizer_updates=0)
if updates:
    t=updates[-1];p=t.get('tool_info',{}).get('parameters',{})
    result['last_tool']=dict(step=t['step_index'],state=t.get('state'),name=t.get('tool_name'),target_name=Path(p.get('AbsolutePath',p.get('TargetFile',''))).name)
result['windows']=[]
for w in read(A/'index.json')['windows']:
    audit=A/f"w{w['job_index']:02d}_completed_scope_audit.json"
    result['windows'].append(dict(job_index=w['job_index'],fact_groups_written=sum(Path(g['output_path']).is_file() for g in w['groups']),proposal_written=Path(w['proposal_path']).is_file(),scope_status=read(audit)['status'] if audit.is_file() else 'PENDING'))
for name in ('terminal.json','owned_stop_request.json','audit.json'):
    if (A/name).is_file():
        d=read(A/name);result[name]={k:d[k] for k in ('status','exit_code','stop_reason','wall_seconds','reason') if k in d}
for name in ('completion.json','stopped.json'):
    if (R/name).is_file():result[name]=read(R/name)
result['stderr_bytes']={n:(R/n).stat().st_size for n in ('observer.stderr.txt','controller.stderr.txt')}
print(json.dumps(result,ensure_ascii=False))
