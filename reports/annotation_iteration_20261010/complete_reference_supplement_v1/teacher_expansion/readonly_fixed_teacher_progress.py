"""Compact actual stream progress; no writes, no model or label access."""
from pathlib import Path
import json,sys
a=Path(sys.argv[1]).resolve()
def key(p):return str(Path(p).resolve()).casefold()
idx=json.loads((a/'index.json').read_text(encoding='utf-8-sig'));rows=[]
for s in (a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines():
 try:rows.append(json.loads(s))
 except json.JSONDecodeError:break
tools={r['step_update']['step_index']:r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'}
def paths(name,state='DONE'):
 out=[]
 for t in tools.values():
  if t.get('tool_name')==name and t.get('state')==state:
   p=t.get('tool_info',{}).get('parameters',{});out.append(key(p.get('AbsolutePath') or p.get('TargetFile')))
 return out
reads=paths('view_file');writes=paths('write_to_file');wins=[]
for w in idx['windows']:
 wins.append(dict(job_index=w['job_index'],native_DONE=sum(key(f['path']) in reads for g in w['groups'] for f in g['frames']),facts_groups_DONE=sum(key(g['output_path']) in writes for g in w['groups']),clip_DONE=key(w['clip_path']) in reads,previews_DONE=sum(key(f['path']) in reads for f in w['student_previews']),proposal_DONE=key(w['proposal_path']) in writes))
print(json.dumps(dict(call=a.name,windows=wins,same_index_DONE_reads=reads.count(key(a/'index.json')),tool_ERROR_count=sum(t['state']=='ERROR' for t in tools.values()),bare_or_reported_error_metadata=sum(r.get('step_update',{}).get('step_type')=='error_message' for r in rows),last_step=next((r.get('step_update',{}).get('step_index') for r in reversed(rows) if 'step_update' in r),None),terminal_present=(a/'terminal.json').exists()),ensure_ascii=False))
