"""One user-authorized manual38; actual terminal/scope audit, no automatic39."""
from common import ROOT,read,sha,save
from datetime import datetime,timezone
import os

def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_MANUAL_CLI38_ONCE_FIXED21_23_AFTER_ZERO_TOOL_LOCATION37'
 assert gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json') and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(ROOT/'independent_CPU_negative_acceptance.json')
 save(ROOT/'registered.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),root_gate_sha256=sha(ROOT/'root_start_admission.json'),calls=[38],jobs=[21,22,23],no35_retry=True,no39=True))
 from launch import launch
 from audit import final,parsed
 for number in (38,):
  try:
   launch(number);whole=final(number)
  except Exception as e:
   a=ROOT/f'call{number}';terminal=read(a/'terminal.json') if (a/'terminal.json').exists() else None;rows=parsed((a/'stream.jsonl').read_bytes()) if (a/'stream.jsonl').exists() else [];result=next((r['result'] for r in reversed(rows) if r.get('event')=='result'),{})
   if not(a/'audit.json').exists():save(a/'audit.json',dict(status='REJECTED_WHOLE_ACTUAL_CPU_OR_LAUNCH_EXCEPTION_NO_RETRY',actual_terminal=terminal,actual_result_status=result.get('status'),actual_result_error=result.get('error'),actual_result_usage=result.get('usage'),actual_tool_updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'],exception=repr(e),training_admitted=False))
   if terminal and not(a/'actual_terminal_cost.json').exists():save(a/'actual_terminal_cost.json',dict(terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),wall_seconds=terminal['wall_seconds'],actual_result_status=result.get('status'),actual_usage=result.get('usage'),cash_cost='UNKNOWN_NOT_ZERO',new_fee_ledger_entry=False,exception=repr(e)))
   save(ROOT/'stopped.json',dict(CLI=number,reason='ACTUAL_ENGINEERING_EXCEPTION_NO_RETRY_NO39',exception=repr(e),audit_sha256=sha(a/'audit.json'),terminal_present=terminal is not None));return
  a=ROOT/f'call{number}';terminal=read(a/'terminal.json')
  save(a/'actual_terminal_cost.json',dict(terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),wall_seconds=terminal['wall_seconds'],actual_usage=whole['actual_result_usage'],actual_result_status=whole['actual_result_status'],whole_status=whole['status'],scope_receipts=whole['actual_scope_receipts'],cash_cost='UNKNOWN_NOT_ZERO',new_fee_ledger_entry=False))
  if whole['status']!='PASS_WHOLE_ACTUAL_CLI_PENDING_ROOT_SEMANTIC' or not whole['continuation_decision']['eligible'] or not whole['continuation_decision']['whole_success']:
   save(ROOT/'stopped.json',dict(CLI=number,status=whole['status'],audit_sha256=sha(a/'audit.json'),no39=True,no_retry=True,training_admitted=False));return
 save(ROOT/'completion.json',dict(status='PASS_SINGLE_MANUAL38_PENDING_ROOT_SEMANTIC',calls=[38],fixed_denominator=24,teacher_supplement_denominator=21,global_cap=38,no39=True,no_retry=True,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO'))
if __name__=='__main__':main()
