"""One background observer seals every completed scope, including middle job22."""
from common import ROOT,read,sha,save
from audit import ensure_scopes
from datetime import datetime,timezone
import os,time

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRESH_SCOPE_V6_FIXED_CLI35_36'
 save(ROOT/'observer_registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json')))
 while True:
  for n in (35,36):
   if (ROOT/f'call{n}/stream.jsonl').exists():ensure_scopes(n)
  if (ROOT/'stopped.json').exists() or (ROOT/'completion.json').exists():return
  time.sleep(10)
if __name__=='__main__':main()
