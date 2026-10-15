from common import ROOT,read
from pathlib import Path
import json
def main():
 reports=[]
 for n in (34,35,36):
  a=ROOT/f'call{n}';latest={}
  if not(a/'stream.jsonl').exists():continue
  for s in(a/'stream.jsonl').read_bytes().splitlines():
   try:r=json.loads(s)
   except Exception:break
   t=r.get('step_update',{})
   if t.get('step_type')=='tool':latest[t['step_index']]=t
  reports.append(dict(CLI=n,DONE_tools=sum(t.get('state')=='DONE' for t in latest.values()),ERROR_tools=sum(t.get('state')=='ERROR' for t in latest.values()),terminal_present=(a/'terminal.json').exists(),windows=[dict(job=w['job_index'],groups_written=[g['group'] for g in w['groups'] if Path(g['output_path']).exists()],proposal_present=Path(w['proposal_path']).exists()) for w in read(a/'index.json')['windows']]))
 print(json.dumps(dict(event='READONLY_ACTUAL_PROGRESS',calls=reports),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
