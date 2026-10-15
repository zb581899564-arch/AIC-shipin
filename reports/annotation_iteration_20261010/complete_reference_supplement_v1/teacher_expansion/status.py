from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def snapshot():
    plan=read(ROOT/'plan.json');windows=[];calls=[]
    for call in plan['calls']:
        a=Path(call['path']);idx=read(a/'index.json');audit=read(a/'audit.json') if (a/'audit.json').exists() else None
        terminal=read(a/'terminal.json') if (a/'terminal.json').exists() else None
        calls.append(dict(call=call['call'],registered=(a/'request.json').exists(),terminal=terminal,audit_sha256=sha(a/'audit.json') if audit else None))
        for w in idx['windows']:
            out=next((v for v in audit['windows'] if v['job_index']==w['job_index']),None) if audit else None
            windows.append(out or dict(job_index=w['job_index'],window_id=w['window_id'],status='RUNNING' if (a/'request.json').exists() and not terminal else 'PENDING',bound_rows=None,training_admitted=False))
    globalcount=23+sum(c['registered'] for c in calls)
    result=dict(utc=datetime.now(timezone.utc).isoformat(),fixed_denominator=21,windows=windows,calls=calls,global_CLI_calls=globalcount,global_cap=36,
      pass_structure_count=sum(w['status']=='PASS_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' for w in windows),failed_or_incomplete_count=sum(w['status']=='REJECTED_OR_INCOMPLETE_KEEP_RAW' for w in windows),
      semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW',training_admitted=False,new_training=0,new_426=0,cash_cost='UNKNOWN_NOT_ZERO')
    dst=ROOT/f'status_CLI{globalcount:02d}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}.json'
    with dst.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(dst),global_CLI_calls=globalcount,pass_structure_count=result['pass_structure_count'],failed_or_incomplete_count=result['failed_or_incomplete_count']),ensure_ascii=False),flush=True)
if __name__=='__main__':snapshot()
