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
  launch(n);whole=final(n)
  terminal=read(ROOT/f'call{n}/terminal.json')
  save(ROOT/f'call{n}/actual_terminal_cost.json',dict(terminal_sha256=sha(ROOT/f'call{n}/terminal.json'),raw_sha256=sha(ROOT/f'call{n}/stream.jsonl'),wall_seconds=terminal['wall_seconds'],actual_result_status=whole['actual_result_status'],actual_usage=whole['actual_result_usage'],whole_status=whole['status'],scope_receipts=whole['actual_scope_receipts'],cash_cost='UNKNOWN_NOT_ZERO',new_fee_ledger_entry=False,original_all_fees_preserved=True))
  if not whole['continuation_decision']['eligible']:
   save(ROOT/'stopped.json',dict(CLI=n,reason='REAL_ENGINEERING_OR_TERMINAL_FAILURE_NO_RETRY',audit_sha256=sha(ROOT/f'call{n}/audit.json'),decision=whole['continuation_decision'],fixed_denominator=24,teacher_supplement_denominator=21,cash_cost='UNKNOWN_NOT_ZERO'));return
 save(ROOT/'completion.json',dict(status='FIXED_UNUSED35_36_FINISHED_SCOPE_ENGINEERING_ONLY',fixed_denominator=24,teacher_supplement_denominator=21,actual_global=36,whole_statuses={str(n):read(ROOT/f'call{n}/audit.json')['status'] for n in (35,36)},ROOT_semantic_gate_separate=True,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO'))

if __name__=='__main__':main()
