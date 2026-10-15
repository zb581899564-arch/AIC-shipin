"""Read actual stream progress only; never infer semantic or training success."""
from pathlib import Path
import json
from functools import lru_cache
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
@lru_cache(None)
def key(p):return str(Path(p).resolve()).casefold() if p else ''
out={'version':V.name,'calls':[],'read_only':True}
for n in (36,37):
 a=V/f'call{n}'
 if not (a/'index.json').exists():continue
 idx=read(a/'index.json');rows=[]
 if (a/'stream.jsonl').exists():
  for line in (a/'stream.jsonl').read_bytes().splitlines():
   try:rows.append(json.loads(line))
   except (json.JSONDecodeError,UnicodeDecodeError):break
 tools=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool']
 latest={t['step_index']:t for t in tools}
 done=[t for t in latest.values() if t.get('state')=='DONE']
 def done_path(name,path):
  return any(t.get('tool_name')==name and key(t.get('tool_info',{}).get('parameters',{}).get('AbsolutePath' if name=='view_file' else 'TargetFile'))==key(path) for t in done)
 record={'CLI':n,'request':(a/'request.json').exists(),'stream_bytes':(a/'stream.jsonl').stat().st_size if (a/'stream.jsonl').exists() else 0,'unique_DONE_tools':len(done),'actual_raw_ERROR_updates':len([t for t in tools if t.get('state')=='ERROR']),'terminal':read(a/'terminal.json') if (a/'terminal.json').exists() else None,'result':next((r['result'] for r in reversed(rows) if r.get('event')=='result'),None),'jobs':[]}
 for w in idx['windows']:
  scope=a/f"w{w['job_index']:02d}_completed_scope_audit.json"
  record['jobs'].append({'job':w['job_index'],'native_DONE':sum(done_path('view_file',f['path']) for g in w['groups'] for f in g['frames']),'fact_writes_DONE':sum(done_path('write_to_file',g['output_path']) for g in w['groups']),'clip_DONE':done_path('view_file',w['clip_path']),'effective_DONE':sum(done_path('view_file',f['path']) for f in w['student_previews']),'proposal_DONE':done_path('write_to_file',w['proposal_path']),'immutable_scope_status':read(scope)['status'] if scope.exists() else None})
 out['calls'].append(record)
for name in ('completion.json','stopped.json'):
 if (V/name).exists():out[name]=read(V/name)
print(json.dumps(out,ensure_ascii=False))
