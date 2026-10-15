"""One background observer seals every completed scope, including middle job22."""
from common import ROOT,read,sha,save
from audit import ensure_scopes
from datetime import datetime,timezone
import os,time

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_SCHEMA_LOCAL_FRESH37_FIXED21_23_AFTER_ROOT20_RECOVERY'
 save(ROOT/'observer_registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json')))
 while True:
  for n in (37,):
   if (ROOT/f'call{n}/stream.jsonl').exists() and not(ROOT/f'call{n}/observer_scope_exception.json').exists():
    try:
     schema_scan(n)
     if not(ROOT/f'call{n}/owned_stop_request.json').exists():ensure_scopes(n)
    except Exception as e:
     p=ROOT/f'call{n}/observer_scope_exception.json'
     if not p.exists():save(p,dict(error=repr(e),actual_prefix_files_preserved=True,no_model_retry=True))
     # A CPU observer failure is conservative STOP, not permission to continue media.
     a=ROOT/f'call{n}';signal=a/'owned_stop_request.json'
     if not signal.exists() and (a/'process.json').exists():
      raw=(a/'stream.jsonl').read_bytes();pref=a/'first_observer_exception_prefix.jsonl'
      if not pref.exists():
       with pref.open('xb') as f:f.write(raw)
      process=read(a/'process.json');save(signal,dict(reason={'accepted':False,'reason':'OBSERVER_CPU_EXCEPTION','error':repr(e)},owned_AGY_pid=process['pid'],freeze_sha256=sha(a/'freeze.json'),observer_source_sha256=sha(__file__),raw_prefix_path=str(pref),raw_prefix_sha256=sha(pref),only_owned_child_may_stop=True,no_retry=True))
  if (ROOT/'stopped.json').exists() or (ROOT/'completion.json').exists():return
  time.sleep(10)



def fact_payload_guard(payload,group):
 import json
 from common import fact_items
 try:fact_items(json.loads(payload),group);return dict(accepted=True,reason=None)
 except Exception as e:return dict(accepted=False,reason='ORIGINAL_CLOSED_FACT_SCHEMA_REJECTED',error=repr(e))

def schema_scan(number):
 import json
 from pathlib import Path
 from common import key
 a=ROOT/f'call{number}';idx=read(a/'index.json');raw=(a/'stream.jsonl').read_bytes();outputs={key(g['output_path']):(w,g) for w in idx['windows'] for g in w['groups']};position=0
 for line in raw.splitlines(keepends=True):
  position+=len(line)
  try:r=json.loads(line)
  except Exception:break
  t=r.get('step_update',{});params=t.get('tool_info',{}).get('parameters',{})
  if t.get('step_type')!='tool':continue
  k=key(params.get('TargetFile'));item=outputs.get(k);failure=None;payload=None
  if t.get('state')=='ERROR':failure=dict(accepted=False,reason='ANY_REAL_RAW_TOOL_ERROR',actual_update=t)
  elif t.get('state')=='DONE' and t.get('tool_name')=='write_to_file' and item:
   w,g=item;checked=a/f"w{w['job_index']:02d}_g{g['group']:02d}_immediate_fact_schema.json"
   if checked.exists():continue
   original=Path(g['output_path']);payload=original.read_bytes();decision=fact_payload_guard(payload,g['group'])
   save(checked,dict(job_index=w['job_index'],group=g['group'],actual_write_DONE_step=t['step_index'],original_path=str(original),original_payload_sha256=sha(original),raw_prefix_bytes=position,raw_prefix_sha256=__import__('hashlib').sha256(raw[:position]).hexdigest(),decision=decision,semantic_correctness='ROOT_PENDING',new_model_calls=0))
   if not decision['accepted']:failure=decision
  if failure:
   signal=a/'owned_stop_request.json'
   if signal.exists():return
   prefix=a/'first_schema_or_raw_failure_prefix.jsonl'
   with prefix.open('xb') as f:f.write(raw[:position])
   original_copy=None
   if payload is not None:
    original_copy=a/'first_failed_fact_original_bytes.json'
    with original_copy.open('xb') as f:f.write(payload)
   process=read(a/'process.json')
   save(signal,dict(reason=failure,actual_tool_step=t['step_index'],owned_AGY_pid=process['pid'],observer_source_sha256=sha(__file__),freeze_sha256=sha(a/'freeze.json'),raw_prefix_path=str(prefix),raw_prefix_sha256=sha(prefix),failed_fact_exact_copy=str(original_copy) if original_copy else None,bounded_natural_grace_seconds=20,only_owned_child_may_stop=True,no_retry=True))
   return
if __name__=='__main__':main()
