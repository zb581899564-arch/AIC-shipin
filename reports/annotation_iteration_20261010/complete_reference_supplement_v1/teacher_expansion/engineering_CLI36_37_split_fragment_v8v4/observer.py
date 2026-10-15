"""One background observer seals every completed scope, including middle job22."""
from common import ROOT,read,sha,save
from audit import ensure_scopes
from datetime import datetime,timezone
import os,time

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRAGMENTED_SPLIT36_37_FIXED19_23'
 save(ROOT/'observer_registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json')))
 while True:
  for n in (36,37):
   if (ROOT/f'call{n}/stream.jsonl').exists() and not(ROOT/f'call{n}/observer_scope_exception.json').exists():
    try:ensure_scopes(n)
    except Exception as e:
     p=ROOT/f'call{n}/observer_scope_exception.json'
     if not p.exists():save(p,dict(error=repr(e),actual_prefix_files_preserved=True,no_model_retry=True))
     # Current child reaches its natural terminal; controller seals cost/STOP.
  if (ROOT/'stopped.json').exists() or (ROOT/'completion.json').exists():return
  time.sleep(10)
if __name__=='__main__':main()
