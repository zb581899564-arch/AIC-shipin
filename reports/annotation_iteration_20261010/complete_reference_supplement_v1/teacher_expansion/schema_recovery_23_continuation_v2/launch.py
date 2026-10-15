"""Fresh CLI40/job23 with typed ROOT recovery of old39; preserve wholeREJECT/no41."""
from common import ROOT,BASE,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
import os,subprocess,time,json

def command(number,prompt):
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','60m','--output-format','stream-json','--log-file',str(ROOT/f'call{number}/agy.log'),'-p',prompt]

W20_STATUS='PASS_ROOT20_INDEPENDENT_FINITE_REFERENCE_WITH_UNKNOWN_PRESERVED_NOT_TRAINING'
W20_WINDOW='cjibtmSLxQ4:SLOT6:13'
W20_REFERENCE_KIND='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD'

def verify_w20_recovery(gate):
 # Exact typed ROOT receipt plus actual reference/source-window bytes;
 # no startswith(PASS), STATIC/media-only substitute, or boolean-only gate.
 assert gate['ROOT_w20_complete_independent_semantic_recovery_PASS'] is True
 recovery=gate['w20_semantic_recovery_receipt'];assert recovery['status']==W20_STATUS and sha(recovery['path'])==recovery['sha256']
 recovered=read(recovery['path']);assert recovered['status']==W20_STATUS and recovered['window_id']==W20_WINDOW
 assert recovered['original_silver_contract_actual_verified'] is True and recovered['training_admitted'] is False and recovered['consequential15_18UNKNOWN_preserved'] is True
 bound=recovered['reference_binding'];assert bound==gate['w20_reference_binding']
 assert bound['window_id']==W20_WINDOW and bound['reference_kind']==W20_REFERENCE_KIND and bound['training_admitted'] is False
 assert sha(bound['path'])==bound['sha256'];reference=read(bound['path'])
 assert reference['window_id']==W20_WINDOW and reference['reference_kind']==W20_REFERENCE_KIND and reference['training_admitted'] is False and reference['source_sha256']==bound['source_sha256']
 assert reference['unknown_global_exact'] and any(type(x.get('first')) is int and type(x.get('last')) is int and x['first']==15 and x['last']==18 for x in reference['consequential_unknowns'])
 source_window=bound['source_window'];assert sha(source_window['path'])==source_window['sha256'];source_plan=read(source_window['path'])
 source_jobs=[j for j in source_plan['jobs'] if j['window']['window_id']==W20_WINDOW];assert len(source_jobs)==1
 source=source_jobs[0];assert source['role']=='locked_evaluation' and source['training_admitted'] is False and source['window']['source_sha256']==reference['source_sha256']
 return recovered

USER_STATUS='USER_AUTHORIZED_SCHEMA_REPAIR_TWO_SINGLE_WINDOWS_CLI39_40_NO41'
USER_QUOTE='那你把格式问题修好，继续补完剩下两个窗口，验收通过后就开始微调，一直做到能打包为止。'

RECOVERY39_STATUS='ROOT_CONFIRMED_CLI39_NATURAL_SUCCESS_VALID_JOB22_SCOPE_ONLY_FINAL_PROPOSAL_SELFREAD_WHOLE_REJECT_PRESERVED'
PREVIOUS=BASE/'schema_recovery_22_23_v1'/'call39'

def previous39_documents_guard(terminal,whole,scope,confirmation,window,proposal):
 assert terminal['child_process_created'] is True and terminal['exit_code']==0 and terminal['stop_reason'] is None and terminal['launch_exception'] is None and terminal['CLI_after']==39
 assert whole['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and whole['actual_result_status']=='SUCCESS' and whole['actual_result_error'] is None
 decision=whole['continuation_decision'];assert decision['issues']==['TOOL_AFTER_FINAL_PROPOSAL_TERMINAL_INSTRUCTION'] and decision['eligible'] is False and decision['whole_success'] is True and decision['further_CLI_allowed'] is False
 for k in ('tool_issues','all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','error_message_steps','reported_nonmedia_errors','actual_pre_completion_result_ERRORS','actual_post_completion_result_ERRORS','immutable_drift','repeated_media_attempts','rewritten_output_attempts'):assert not whole[k]
 assert whole['actual_core_tool_calls']==whole['expected_core_tool_calls']==128
 assert whole['self_reads']=={str(Path(proposal).resolve()).casefold():1}
 after=whole['actual_post_last_proposal_tool_updates'];assert len(after)==2 and [x['state'] for x in after]==['ACTIVE','DONE']
 for x in after:assert x['step_index']==204 and x['step_type']=='tool' and x['tool_name']=='view_file' and x['tool_info']['name']=='view_file' and x['tool_info']['parameters']=={'AbsolutePath':proposal}
 proofs=whole['actual_self_read_proofs'];assert len(proofs)==1 and proofs[0]['actual_step']==204 and proofs[0]['actual_state']=='DONE' and proofs[0]['complete'] is True and proofs[0]['actual_parameters']=={'AbsolutePath':proposal}
 assert scope['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC' and len(scope['windows'])==1
 w=scope['windows'][0];assert w['window_id']==window and w['job_index']==22 and w['bound_rows']==64 and w['core_tool_count']==126 and w['scientific_media_fact_tool_count']==90
 assert scope['actual_core_tool_calls']==scope['expected_core_tool_calls']==128 and len(scope['text_fragment_proofs'])==19 and all(p['complete'] is True for p in scope['text_fragment_proofs'])
 for k in ('tool_issues','additional_scope_issues','all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'):assert not scope[k]
 assert confirmation['status']==RECOVERY39_STATUS and confirmation['CLI']==39 and confirmation['window_id']==window and confirmation['ROOT_actual_scope_independently_verified'] is True
 assert confirmation['old_whole_REJECTED_preserved'] is True and confirmation['allowed_whole_issue']=='TOOL_AFTER_FINAL_PROPOSAL_TERMINAL_INSTRUCTION' and confirmation['final_proposal_selfread_step']==204

def verify_previous39(gate):
 b=gate['previous39_recovery'];assert b['status']==RECOVERY39_STATUS and sha(b['path'])==b['sha256'];confirmed=read(b['path'])
 a=PREVIOUS;terminal=read(a/'terminal.json');whole=read(a/'audit.json');scope=read(a/'w22_completed_scope_audit.json');w=read(a/'index.json')['windows'][0]
 assert w['window_id']=='Yi4Ij2NM7U4:SLOT6:3';previous39_documents_guard(terminal,whole,scope,confirmed,w['window_id'],w['proposal_path'])
 required={str(a/n):sha(a/n) for n in ('terminal.json','stream.jsonl','audit.json','w22_completed_scope_audit.json','actual_terminal_cost.json')};assert confirmed['bindings']==required
 independent=confirmed['independent_actual_scope_review'];assert sha(independent['path'])==independent['sha256']
 lawful=confirmed['lawful_observation_binding'];assert sha(lawful['path'])==lawful['sha256'];observed=read(lawful['path'])
 assert observed['status']=='PASS_ROOT_BOUND_SCHEMA_RECOVERY_SINGLE_IMMUTABLE_MEDIA_SCOPE_PENDING_SEMANTIC_REFERENCE' and observed['window_id']==w['window_id'] and observed['global_CLI']==39 and observed['ordered_actual_core_count']==128 and observed['training_admitted'] is False and not observed['tool_issues'] and not observed['proposal_geometry_identity_issues']
 assert sha(a/'stream.jsonl')==terminal['stream_sha256'] and read(a/'actual_terminal_cost.json')['terminal_sha256']==sha(a/'terminal.json')
 cost=read(a/'actual_terminal_cost.json');assert cost['raw_sha256']==sha(a/'stream.jsonl') and cost['wall_seconds']==terminal['wall_seconds'] and cost['actual_result_status']=='SUCCESS' and cost['whole_status']==whole['status'] and cost['new_fee_ledger_entry'] is False
 prefix=Path(scope['immutable_prefix']['path']);assert sha(prefix)==scope['immutable_prefix']['sha256'] and (a/'stream.jsonl').read_bytes().startswith(prefix.read_bytes())
 for x in scope['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
 raw=[json.loads(x) for x in (a/'stream.jsonl').read_text(encoding='utf-8').splitlines()];tools=[r['step_update'] for r in raw if r.get('step_update',{}).get('step_type')=='tool'];assert not any(t['state']=='ERROR' for t in tools)
 write=scope['windows'][0]['proposal_write_DONE_steps'];assert len(write)==1;last=write[0]
 actual_after=[t for t in tools if t['step_index']>last];assert actual_after==whole['actual_post_last_proposal_tool_updates']
 ledger=[json.loads(x) for x in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines()];assert max(x['global_count'] for x in ledger)==39
 terms=[x for x in ledger if x['global_count']==39 and x['event']=='TERMINAL'];assert len(terms)==1 and terms[0]['terminal_sha256']==sha(a/'terminal.json') and terms[0]['raw_sha256']==sha(a/'stream.jsonl')
 assert (BASE/'global_CLI_ledger.jsonl').read_bytes()==(ROOT/'actual_global39_ledger_prefix.jsonl').read_bytes()


def launch(number):
 assert number==40
 gatepath=ROOT/f'root_start_admission_CLI{number}.json';gate=read(gatepath);assert gate['status']=='ROOT_APPROVED_START_SCHEMA_RECOVERY_CONTINUATION_SINGLE_CLI40_JOB23'
 assert gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json') and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(ROOT/'independent_CPU_negative_acceptance.json')
 a=ROOT/f'call{number}';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 assert gate['previous39_recovery']==fr['previous39_recovery']
 auth_binding=gate['user_authorization'];assert auth_binding['path']==str(BASE.parent/'schema_recovery_22_23_user_authorization_v1.json') and sha(auth_binding['path'])==auth_binding['sha256']==fr['user_authorization_sha256']
 auth=read(auth_binding['path']);assert auth['status']==USER_STATUS and auth['user_quote_exact']==USER_QUOTE and auth['routes']=={'39':[22],'40':[23]} and auth['global_cap']==40 and auth['no41'] is True and auth['automatic_retry'] is False and auth['timeout_seconds_each']==3600
 assert gate['CLI']==number and gate['global_cap']==40 and gate['no41'] is True and gate['automatic_retry'] is False and gate['fixed_job_indices']==[number-17] and gate['timeout_seconds']==3600
 verify_w20_recovery(gate)
 verify_previous39(gate)
 assert fr['global_cap']==40 and fr['CLI_before']==number-1 and fr['CLI_after']==number and fr['timeout_seconds']==3600 and fr['fixed_job_indices']==[number-17]
 assert not any(BASE.rglob(f'call{number}/request.json'))
 for p,h in fr['inputs'].items():assert sha(p)==h,(p,'INPUT_SHA_DRIFT')
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 prompt=(a/'short_prompt.txt').read_text(encoding='utf-8');cmd=command(number,prompt);units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),root_start_admission_sha256=sha(gatepath),main_instruction_path=fr['main_instruction_path'],main_instruction_sha256=sha(fr['main_instruction_path']),short_prompt_sha256=sha(a/'short_prompt.txt'),fixed_job_indices=fr['fixed_job_indices'],CLI_before=number-1,CLI_after=number,timeout_seconds=3600,argv_utf16_units_including_NUL=units,user_schema_recovery=True,user_authorization_sha256=sha(auth_binding['path']),prior38_partial_failure_preserved=True,no41=True,automatic_retry=False,conversation_id=None))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task=ROOT.name+f'/call{number}',global_count=number,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic();created=False;exception=None
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  try:
   proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);created=True
   save(a/'process.json',dict(pid=proc.pid,command=cmd,owned_only=True,proxy='http://127.0.0.1:7892',GODEBUG='http2client=0',argv_utf16_units_including_NUL=units))
   deadline=start+3600;stop=None
   while proc.poll() is None:
    signal=a/'owned_stop_request.json'
    if signal.exists():
     demand=read(signal);assert demand['owned_AGY_pid']==proc.pid and demand['freeze_sha256']==sha(a/'freeze.json') and demand['observer_source_sha256']==sha(ROOT/'observer.py')
     stop='OWNED_SCHEMA_OR_RAW_STOP_NO_RETRY'
     # Only this owned child gets a bounded chance to finish naturally.
     try:code=proc.wait(timeout=min(20,max(0,deadline-time.monotonic())))
     except subprocess.TimeoutExpired:
      proc.terminate()
      try:code=proc.wait(timeout=10)
      except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
     break
    if time.monotonic()>=deadline:
     stop='OWNED_TIMEOUT_NO_RETRY';proc.terminate()
     try:code=proc.wait(timeout=10)
     except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
     break
    time.sleep(0.5)
   else:code=proc.returncode

  except Exception as e:
   exception=repr(e);stop='OWNED_ENGINEERING_MONITOR_FAILURE_NO_RETRY' if created else 'PRESPAWN_FAILURE_NO_RETRY';code=None
   if created and proc.poll() is None:
    proc.terminate()
    try:code=proc.wait(timeout=10)
    except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,launch_exception=exception,child_process_created=created,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=number,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL' if created else 'ENGINEERING_PRESPAWN_TERMINAL',task=ROOT.name+f'/call{number}',global_count=number,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,child_process_created=created,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
