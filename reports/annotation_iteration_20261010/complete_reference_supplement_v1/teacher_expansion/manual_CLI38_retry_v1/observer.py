"""One background observer seals every completed scope, including middle job22."""
from common import ROOT,read,sha,save
from audit import seal_scope,parsed,pathinfo
from datetime import datetime,timezone
import os,time

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_MANUAL_CLI38_ONCE_FIXED21_23_AFTER_ZERO_TOOL_LOCATION37'
 save(ROOT/'observer_registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json')))
 while True:
  for n in (38,):
   if (ROOT/f'call{n}/stream.jsonl').exists() and not(ROOT/f'call{n}/observer_scope_exception.json').exists():
    try:
     schema_scan(n)
     if not(ROOT/f'call{n}/owned_stop_request.json').exists():seal_observed_scopes(n)
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

def proposal_path_guard(path,window):
 from common import proposal_schema
 try:proposal_schema(path,window);return dict(accepted=True,reason=None)
 except Exception as e:return dict(accepted=False,reason='ORIGINAL_CLOSED_PROPOSAL_SCHEMA_REJECTED',error=repr(e))

def request_owned_stop(number,failure,raw,position,step=None,payload=None,payload_kind=None):
 a=ROOT/f'call{number}';signal=a/'owned_stop_request.json'
 if signal.exists():return
 prefix=a/'first_schema_or_raw_failure_prefix.jsonl'
 with prefix.open('xb') as f:f.write(raw[:position])
 original_copy=None
 if payload is not None:
  original_copy=a/f'first_failed_{payload_kind}_original_bytes.json'
  with original_copy.open('xb') as f:f.write(payload)
 process=read(a/'process.json')
 save(signal,dict(reason=failure,actual_tool_step=step,owned_AGY_pid=process['pid'],observer_source_sha256=sha(__file__),freeze_sha256=sha(a/'freeze.json'),raw_prefix_path=str(prefix),raw_prefix_sha256=sha(prefix),failed_fact_exact_copy=str(original_copy) if payload_kind=='fact' else None,failed_original_payload_copy=str(original_copy) if original_copy else None,payload_kind=payload_kind,bounded_natural_grace_seconds=20,only_owned_child_may_stop=True,no_retry=True))

def schema_scan(number):
 import json,hashlib
 from pathlib import Path
 from common import key
 a=ROOT/f'call{number}';idx=read(a/'index.json');raw=(a/'stream.jsonl').read_bytes();outputs={key(g['output_path']):(w,g) for w in idx['windows'] for g in w['groups']};proposals={key(w['proposal_path']):w for w in idx['windows']};position=0
 for line in raw.splitlines(keepends=True):
  position+=len(line)
  try:r=json.loads(line)
  except Exception:break
  t=r.get('step_update',{});params=t.get('tool_info',{}).get('parameters',{})
  if t.get('step_type')!='tool':continue
  k=key(params.get('TargetFile'));item=outputs.get(k);window=proposals.get(k);failure=None;payload=None;kind=None
  if t.get('state')=='ERROR':failure=dict(accepted=False,reason='ANY_REAL_RAW_TOOL_ERROR',actual_update=t)
  elif t.get('state')=='DONE' and t.get('tool_name')=='write_to_file' and (item or window):
   if item:
    w,g=item;original=Path(g['output_path']);kind='fact';checked=a/f"w{w['job_index']:02d}_g{g['group']:02d}_immediate_fact_schema.json"
   else:
    w=window;original=Path(w['proposal_path']);kind='proposal';checked=a/f"w{w['job_index']:02d}_immediate_proposal_schema.json"
   payload=original.read_bytes();payload_sha=hashlib.sha256(payload).hexdigest()
   if checked.exists():
    prior=read(checked)
    if prior['actual_write_DONE_step']!=t['step_index'] or prior['original_payload_sha256']!=payload_sha:failure=dict(accepted=False,reason='CHECKED_FACT_OR_PROPOSAL_REWRITE_OR_BYTE_DRIFT')
    else:continue
   else:
    decision=fact_payload_guard(payload,g['group']) if item else proposal_path_guard(original,w)
    if original.read_bytes()!=payload:decision=dict(accepted=False,reason='PAYLOAD_BYTE_DRIFT_DURING_IMMEDIATE_SCHEMA_CHECK')
    save(checked,dict(job_index=w['job_index'],group=g['group'] if item else None,payload_kind=kind,actual_write_DONE_step=t['step_index'],original_path=str(original),original_payload_sha256=payload_sha,raw_prefix_bytes=position,raw_prefix_sha256=hashlib.sha256(raw[:position]).hexdigest(),decision=decision,semantic_correctness='ROOT_PENDING',new_model_calls=0))
    if not decision['accepted']:failure=decision
  if failure:
   request_owned_stop(number,failure,raw,position,t['step_index'],payload,kind);return

def seal_observed_scopes(number):
 from common import key
 from pathlib import Path
 a=ROOT/f'call{number}';idx=read(a/'index.json');raw=(a/'stream.jsonl').read_bytes()
 done=[r['step_update'] for r in parsed(raw) if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
 for w in idx['windows']:
  if any(pathinfo(t)==('write_to_file',key(w['proposal_path'])) for t in done):
   result=seal_scope(number,w['job_index'])
   if result['status']!='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC':
    pref=result.get('immutable_prefix',{});position=pref.get('bytes',len(raw));payload=Path(w['proposal_path']).read_bytes()
    request_owned_stop(number,dict(accepted=False,reason='ACTUAL_SCOPE_REJECT_REQUIRES_OWNED_STOP',job_index=w['job_index'],scope_status=result['status'],scope_audit_path=str(a/f"w{w['job_index']:02d}_completed_scope_audit.json")),raw,position,payload=payload,payload_kind='proposal');return
if __name__=='__main__':main()
