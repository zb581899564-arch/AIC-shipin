"""One v5 observer; every scope retains original immutable prefix plus new proof."""
from common import ROOT,V5,read,sha,save,key
from datetime import datetime,timezone
import json,subprocess,sys,time
def execute(*args):subprocess.run([sys.executable,'-B',*map(str,args)],cwd=V5,check=True)
def emit(event,**kw):print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event=event,**kw),ensure_ascii=False),flush=True)
def main():
 last=0
 while True:
  for n in (34,35,36):
   a=ROOT/f'call{n}';d=V5/f'call{n}';d.mkdir(exist_ok=True)
   if not(a/'stream.jsonl').exists():continue
   done=[]
   for line in(a/'stream.jsonl').read_bytes().splitlines():
    try:r=json.loads(line)
    except Exception:break
    t=r.get('step_update',{})
    if t.get('step_type')=='tool' and t.get('state')=='DONE':done.append(t)
   for w in read(a/'index.json')['windows']:
    finished=any(t.get('tool_name')=='write_to_file' and key(t.get('tool_info',{}).get('parameters',{}).get('TargetFile',''))==key(w['proposal_path']) for t in done)
    if not finished:continue
    original=a/f"w{w['job_index']:02d}_completed_scope_audit.json";proof=d/f"w{w['job_index']:02d}_line_representation_scope.json"
    if not original.exists():execute(ROOT/'audit.py','scope',n,w['job_index'])
    if not proof.exists():
     execute(V5/'reconstruct.py','scope',n,w['job_index']);p=read(proof)
     emit('EVERY_SCOPE_ORIGINAL_PREFIX_AND_V5_REPRESENTATION_PROOF',CLI=n,job=w['job_index'],status=p['status'],original_prefix=p['original_immutable_prefix'],proof_path=str(proof),proof_sha256=sha(proof))
   if(a/'audit.json').exists() and(a/'terminal.json').exists() and not(d/'actual_terminal_cost.json').exists():execute(V5/'cost.py',n)
  end=next((V5/p for p in ('stopped.json','completion.json') if(V5/p).exists()),None)
  if end:emit('V5_TERMINAL_OBSERVED',path=str(end),sha256=sha(end));return
  if time.monotonic()-last>=300:execute(V5/'progress.py');last=time.monotonic()
  time.sleep(10)
if __name__=='__main__':main()
