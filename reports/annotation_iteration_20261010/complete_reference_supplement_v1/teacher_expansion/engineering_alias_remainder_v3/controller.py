"""Only approved fixed three calls; fail closed without retry or call37."""
from common import ROOT,BASE,read,sha,save
from datetime import datetime,timezone
import copy,json,os,subprocess,sys
def main():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_ALIAS_V3_FIXED_CLI34_36'
 assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
 assert max(json.loads(s)['global_count'] for s in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip())==33
 for n in (34,35,36):
  a=ROOT/f'call{n}';fr=read(a/'freeze.json');assert not(a/'request.json').exists()
  for p,s in fr['inputs'].items():assert sha(p)==s
 save(ROOT/'registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),runner_pid=os.getpid(),runner_command=sys.orig_argv,runner_source_sha256=sha(__file__),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),fixed_routing={'34':[17,18],'35':[19,20],'36':[21,22,23]},global_cap=36,automatic_retry=False,cash_cost='UNKNOWN_NOT_ZERO'))
 previous=BASE/'remaining_CLI33_36_same_index_selfcheck_v2/full_denominator24_after_CLI33.json';prior=read(previous)
 for n in (34,35,36):
  a=ROOT/f'call{n}';subprocess.run([sys.executable,'-B',str(ROOT/'run_call.py'),str(n)],cwd=ROOT,check=True)
  subprocess.run([sys.executable,'-B',str(ROOT/'audit.py'),str(n)],cwd=ROOT,check=True)
  audit=read(a/'audit.json');terminal=read(a/'terminal.json');records=copy.deepcopy(prior['records'])
  for earlier in (34,35,36):
   aa=ROOT/f'call{earlier}'
   if not(aa/'audit.json').exists():continue
   for w in read(aa/'audit.json')['windows']:
    old=records[w['window_id']].get('teacher_observation')
    if old:records[w['window_id']].setdefault('historical_teacher_observations',[]).append(old)
    records[w['window_id']]['teacher_observation']=dict(job_index=w['job_index'],status=w['status'],bound_rows=w['bound_rows'],audit_path=str(aa/'audit.json'),audit_sha256=sha(aa/'audit.json'),proposal_sha256=w['proposal_sha256'],prior_native_facts_transferred=w['prior_native_facts_transferred'],semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW')
  save(ROOT/f'full_denominator24_after_CLI{n}.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_FIXED24_SNAPSHOT_ALL_OLD_FAILURES_PRESERVED',fixed_denominator=24,teacher_expansion_denominator=21,previous_snapshot=dict(path=str(previous),sha256=sha(previous)),root_registry=prior['root_registry'],root_qualified_references_at_frozen_registry=prior['root_qualified_references_at_frozen_registry'],records=records,global_CLI_calls=n,global_CLI_cap=36,original_CLI33_strict_failure_preserved=True,cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_426=0))
  save(ROOT/f'status_after_CLI{n}.json',dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=n,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),audit_sha256=sha(a/'audit.json'),windows=[dict(job_index=w['job_index'],status=w['status']) for w in audit['windows']],cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False))
  failed=terminal['exit_code']!=0 or audit['tool_issues'] or audit['errored_tool_attempts'] or audit['unfinished_tool_attempts'] or any(not w['status'].startswith('PASS_') for w in audit['windows'])
  if failed:
   save(ROOT/'stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_CLI=n,reason='ACTUAL_MEDIA_PATH_AUTH_OR_ENGINEERING_FAILURE_NO_RETRY_NO_ADVANCE',pending_CLI=list(range(n+1,37))));return 2
  if audit['actual_result_status']!='SUCCESS' or audit['reported_nonmedia_errors']:
   save(ROOT/'awaiting_root.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_CLI=n,reason='ACTUAL_NON_SUCCESS_OR_REPORTED_ERROR_REQUIRES_ROOT',pending_CLI=list(range(n+1,37))));return 3
 save(ROOT/'completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_FIXED_REMAINING_SUPPLY_PENDING_ROOT_SEMANTIC',global_CLI_calls=36,global_cap=36,fixed_windows=[17,18,19,20,21,22,23],old17_native32_facts_exact_transfer=True,original33_failure_preserved=True,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,new_optimizer_updates=0,new_426=0));return 0
if __name__=='__main__':sys.exit(main())
