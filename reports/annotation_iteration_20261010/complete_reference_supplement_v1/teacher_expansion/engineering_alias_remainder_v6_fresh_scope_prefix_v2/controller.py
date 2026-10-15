"""Whole failed stays failed; only unused fresh routes and explicit conservative gate."""
from common import ROOT,BASE,read,sha,save
from datetime import datetime,timezone
import os,subprocess,sys,json

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRESH_SCOPE_V6_FIXED_CLI35_36'
 assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
 ready=read(ROOT/'readiness_actual34.json')
 for p,s in ready['actual_bindings'].items():assert sha(p)==s,(p,'PRIOR_ACTUAL_BYTE_DRIFT')
 assert (BASE/'global_CLI_ledger.jsonl').read_bytes()==(ROOT/'actual_global34_ledger_prefix.jsonl').read_bytes()
 for n in (35,36):assert not(ROOT/f'call{n}/request.json').exists()
 save(ROOT/'registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json'),fixed_calls=[35,36],no34_repeat=True,no37=True))
 from launch import launch
 from audit import final
 for n in (35,36):
  try:
   launch(n);whole=final(n)
  except Exception as e:
   # Real terminal fees remain auditable even if CPU inspection itself fails.
   from audit import parsed
   terminal_path=ROOT/f'call{n}/terminal.json';raw_path=ROOT/f'call{n}/stream.jsonl'
   terminal=read(terminal_path) if terminal_path.exists() else None
   rows=parsed(raw_path.read_bytes()) if raw_path.exists() else []
   result=next((r['result'] for r in reversed(rows) if r.get('event')=='result'),{})
   audit_path=ROOT/f'call{n}/audit.json'
   if not audit_path.exists():save(audit_path,dict(status='REJECTED_WHOLE_CLI_CPU_INSPECTION_EXCEPTION_NO_RETRY',inspection_exception=repr(e),actual_terminal=terminal,actual_result_status=result.get('status'),actual_result_error=result.get('error'),actual_result_usage=result.get('usage'),actual_raw_sha256=sha(raw_path) if raw_path.exists() else None,actual_tool_updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'],continuation_decision={'eligible':False,'issues':['ACTUAL_INSPECTION_EXCEPTION_STOP']},training_admitted=False))
   if terminal and not(ROOT/f'call{n}/actual_terminal_cost.json').exists():save(ROOT/f'call{n}/actual_terminal_cost.json',dict(terminal_sha256=sha(terminal_path),raw_sha256=sha(raw_path),wall_seconds=terminal['wall_seconds'],actual_result_status=result.get('status'),actual_usage=result.get('usage'),inspection_exception=repr(e),cash_cost='UNKNOWN_NOT_ZERO',new_fee_ledger_entry=False,original_all_fees_preserved=True))
   save(ROOT/'stopped.json',dict(CLI=n,reason='ACTUAL_LAUNCH_OR_CPU_INSPECTION_EXCEPTION_NO_RETRY',audit_sha256=sha(audit_path),actual_terminal_present=terminal is not None,fixed_denominator=24,teacher_supplement_denominator=21,exception=repr(e),cash_cost='UNKNOWN_NOT_ZERO'));return
  terminal=read(ROOT/f'call{n}/terminal.json')
  save(ROOT/f'call{n}/actual_terminal_cost.json',dict(terminal_sha256=sha(ROOT/f'call{n}/terminal.json'),raw_sha256=sha(ROOT/f'call{n}/stream.jsonl'),wall_seconds=terminal['wall_seconds'],actual_result_status=whole['actual_result_status'],actual_usage=whole['actual_result_usage'],whole_status=whole['status'],scope_receipts=whole['actual_scope_receipts'],cash_cost='UNKNOWN_NOT_ZERO',new_fee_ledger_entry=False,original_all_fees_preserved=True))
  if not whole['continuation_decision']['eligible']:
   save(ROOT/'stopped.json',dict(CLI=n,reason='REAL_ENGINEERING_OR_TERMINAL_FAILURE_NO_RETRY',audit_sha256=sha(ROOT/f'call{n}/audit.json'),decision=whole['continuation_decision'],fixed_denominator=24,teacher_supplement_denominator=21,cash_cost='UNKNOWN_NOT_ZERO'));return
 save(ROOT/'completion.json',dict(status='FIXED_UNUSED35_36_FINISHED_SCOPE_ENGINEERING_ONLY',fixed_denominator=24,teacher_supplement_denominator=21,actual_global=36,whole_statuses={str(n):read(ROOT/f'call{n}/audit.json')['status'] for n in (35,36)},ROOT_semantic_gate_separate=True,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO'))

if __name__=='__main__':main()
