"""Only after immutable original34 terminal acceptance, run fresh frozen35/36 once."""
from common import ROOT,V5,BASE,read,sha,save
from datetime import datetime,timezone
from pathlib import Path
import copy,json,os,subprocess,sys
def execute(*args):subprocess.run([sys.executable,'-B',*map(str,args)],cwd=V5,check=True)
def original_audit_once(n):
 a=ROOT/f'call{n}'
 if not(a/'audit.json').exists():execute(ROOT/'audit.py',n)
def proof_once(n):
 target=V5/f'call{n}/line_representation_final.json'
 if not target.exists():execute(V5/'reconstruct.py',n)
 return read(target)
def snapshot(n):
 prior_path=ROOT/'full_denominator24_after_CLI34.json';prior=read(prior_path);records=copy.deepcopy(prior['records'])
 for earlier in (34,35,36):
  p=V5/f'call{earlier}/line_representation_final.json'
  if not p.exists():continue
  proof=read(p)
  for w in proof['representation_audit']['windows']:
   rec=records[w['window_id']];old=rec.get('teacher_observation')
   if old:rec.setdefault('historical_teacher_observations',[]).append(old)
   rec['teacher_observation']=dict(job_index=w['job_index'],status=w['status'] if proof['status'].startswith('ACCEPT_') else 'REJECT_ACTUAL_OTHER_FAILURE_NO_RETRY',bound_rows=w['bound_rows'],original_strict_audit_path=proof['original_audit_path'],original_strict_audit_sha256=proof['original_audit_sha256'],v5_representation_proof_path=str(p),v5_representation_proof_sha256=sha(p),proposal_sha256=w['proposal_sha256'],prior_native_facts_transferred=w['prior_native_facts_transferred'],semantic_correctness='PENDING_ROOT_INDEPENDENT_REVIEW',training_admitted=False)
 assert len(records)==24
 save(V5/f'full_denominator24_after_CLI{n}.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_SUPPLY_REPRESENTATION_SNAPSHOT_NOT_ROOT_SEMANTIC_REGISTRY',fixed_denominator=24,teacher_expansion_denominator=21,prior_original_v4_snapshot=dict(path=str(prior_path),sha256=sha(prior_path)),historical_frozen_root_registry=prior['root_registry'],historical_frozen_root_qualified_count=prior['root_qualified_references_at_frozen_registry'],records=records,global_registered=n,global_cap=36,all_old_failures_and_cost_preserved=True,root_current_semantic_registry_not_modified=True,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False))
def main():
 gate=read(V5/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_LINE_REPRESENTATION_V5_FIXED_CLI35_36'
 assert gate['execution_binding_sha256']==sha(V5/'execution_code_binding.json') and gate['dry_run_sha256']==sha(V5/'dry_run_acceptance.json')
 binding=read(V5/'execution_code_binding.json')
 for p,s in {**binding['sources'],**binding['frozen_prior_inputs']}.items():assert sha(p)==s
 assert (ROOT/'call34/terminal.json').exists() and (ROOT/'stopped.json').exists()
 assert max(json.loads(s)['global_count'] for s in(BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines())==34
 assert not any((ROOT/f'call{n}/request.json').exists() for n in (35,36))
 original_audit_once(34);accepted34=proof_once(34)
 if not accepted34['status'].startswith('ACCEPT_ACTUAL_SUPPLY_'):
  save(V5/'stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_CLI=34,reason='CLI34_NOT_COMPLETE_STRICT_ACTUAL_SUPPLY_NO35_START',pending_CLI=[35,36]));return 2
 save(V5/'registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),runner_pid=os.getpid(),command=sys.orig_argv,source_sha256=sha(__file__),root_gate_sha256=sha(V5/'root_start_admission.json'),prior_complete34_proof_sha256=sha(V5/'call34/line_representation_final.json'),old_v4_STOP_preserved=True,routing={'35':[19,20],'36':[21,22,23]},global_cap=36,automatic_retry=False))
 snapshot(34)
 for n in (35,36):
  assert not(ROOT/f'call{n}/request.json').exists()
  execute(ROOT/'run_call.py',n)
  original_audit_once(n);proof=proof_once(n)
  snapshot(n)
  save(V5/f'status_after_CLI{n}.json',dict(utc=datetime.now(timezone.utc).isoformat(),CLI=n,proof_sha256=sha(V5/f'call{n}/line_representation_final.json'),status=proof['status'],old_v4_original_audit_preserved=True,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False))
  if not proof['status'].startswith('ACCEPT_ACTUAL_SUPPLY_'):
   save(V5/'stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_CLI=n,reason='ACTUAL_MEDIA_AUTH_PATH_SCHEMA_TERMINAL_FAILURE_NO_RETRY',pending_CLI=list(range(n+1,37))));return 2
 save(V5/'completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='FIXED_FRESH35_36_ACTUAL_SUPPLY_COMPLETE_PENDING_ROOT_SEMANTIC',global_registered=36,global_cap=36,no37=True,no_model_retry=True,old33_and_v3_prespawn34_and_v4_strict_rejections_preserved=True,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO'));return 0
if __name__=='__main__':sys.exit(main())
