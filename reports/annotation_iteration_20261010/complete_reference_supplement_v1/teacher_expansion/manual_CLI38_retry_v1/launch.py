"""One user-authorized manual38 retry of actual zero-tool location37; no39."""
from common import ROOT,BASE,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
import os,subprocess,time,json

def command(number,prompt):
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(ROOT/f'call{number}/agy.log'),'-p',prompt]

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

PRIOR37=BASE/'prospective_CLI37_schema_local_v2/call37'
LOCATION_ERROR='FAILED_PRECONDITION (code 400): User location is not supported for the API use.'
MANUAL_STATUS='USER_EXPLICIT_ONE_MANUAL_CLI38_RETRY_NO39_FIXED21_23'
MANUAL_QUOTE='现在再去试一下，应该IP问题解决了'

def verify_prior37_failure():
 raw=(PRIOR37/'stream.jsonl').read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
 results=[r['result'] for r in rows if r.get('event')=='result'];assert len(results)==1;result=results[0]
 assert result['status']=='ERROR' and result['error']==LOCATION_ERROR
 assert result['usage']['input_tokens']==0 and result['usage']['output_tokens']==0 and all(v==0 for v in result['usage'].values())
 assert not any(r.get('step_update',{}).get('step_type')=='tool' for r in rows)
 terminal=read(PRIOR37/'terminal.json');assert terminal['child_process_created'] is True and terminal['exit_code']==3 and terminal['stop_reason'] is None and terminal['launch_exception'] is None and terminal['CLI_after']==37
 assert sha(PRIOR37/'stream.jsonl')==terminal['stream_sha256'] and sha(PRIOR37/'stderr.txt')==terminal['stderr_sha256'] and terminal['outputs']==[]
 oldfreeze=read(PRIOR37/'freeze.json');assert not any(Path(p).exists() for p in oldfreeze['write_whitelist'])
 audit=read(PRIOR37/'audit.json');assert audit['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and audit['actual_core_tool_calls']==0
 ledger=[json.loads(line) for line in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines()]
 assert max(r['global_count'] for r in ledger)==37
 registered=[r for r in ledger if r['global_count']==37 and r['event']=='REGISTERED'];terminals=[r for r in ledger if r['global_count']==37 and r['event']=='TERMINAL'];assert len(registered)==len(terminals)==1
 assert registered[0]['request_sha256']==sha(PRIOR37/'request.json') and terminals[0]['terminal_sha256']==sha(PRIOR37/'terminal.json') and terminals[0]['raw_sha256']==sha(PRIOR37/'stream.jsonl') and terminals[0]['exit_code']==3 and terminals[0]['child_process_created'] is True
 return dict(error=result['error'],core_tool_count=0,input_tokens=0,output_tokens=0,raw_sha256=sha(PRIOR37/'stream.jsonl'),terminal_sha256=sha(PRIOR37/'terminal.json'))

def verify_manual38_admission(gate):
 binding=gate['manual_user_authorization'];assert binding['path']==str(BASE.parent/'manual_CLI38_user_retry_authorization_v1.json') and sha(binding['path'])==binding['sha256']
 auth=read(binding['path']);assert auth['status']==MANUAL_STATUS and auth['user_quote_exact']==MANUAL_QUOTE
 assert auth['CLI']==38 and auth['prior_actual_CLI']==37 and auth['global_cap']==38 and auth['no39'] is True and auth['automatic_retry'] is False and auth['fixed_job_indices']==[21,22,23] and auth['timeout_seconds']==7200
 assert auth['IP_recovery_verified'] is False and auth['cash_cost']=='UNKNOWN_NOT_ZERO'
 assert gate['CLI']==38 and gate['global_cap']==38 and gate['no39'] is True and gate['automatic_retry'] is False and gate['fixed_job_indices']==[21,22,23] and gate['timeout_seconds']==7200
 for p,h in auth['prior37_actual_bindings'].items():assert sha(p)==h
 assert verify_prior37_failure()==auth['prior37_exact_failure']
 return auth

def launch(number):
 assert number==38
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_MANUAL_CLI38_ONCE_FIXED21_23_AFTER_ZERO_TOOL_LOCATION37'
 assert gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json') and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(ROOT/'independent_CPU_negative_acceptance.json')
 a=ROOT/f'call{number}';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 verify_manual38_admission(gate)
 assert fr['global_cap']==38 and fr['fixed_job_indices']==[21,22,23]
 verify_w20_recovery(gate)
 assert ledger.read_bytes()==(ROOT/'actual_global37_ledger_prefix.jsonl').read_bytes()
 # Oldwhole36 rejection is preserved; new independent ROOT gate, never reuse old continuation.
 old=BASE/'engineering_CLI36_37_split_fragment_v8v5/call36'
 assert read(old/'audit.json')['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST'
 assert sha(old/'stream.jsonl')==read(old/'terminal.json')['stream_sha256']
 assert not any(BASE.rglob(f'call{number}/request.json')) and fr['CLI_before']==number-1 and fr['CLI_after']==number and fr['timeout_seconds']==7200
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 prompt=(a/'short_prompt.txt').read_text(encoding='utf-8');cmd=command(number,prompt);units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),main_instruction_path=fr['main_instruction_path'],main_instruction_sha256=sha(fr['main_instruction_path']),short_prompt_sha256=sha(a/'short_prompt.txt'),fixed_job_indices=fr['fixed_job_indices'],CLI_before=number-1,CLI_after=number,timeout_seconds=7200,argv_utf16_units_including_NUL=units,manual_user_retry=True,manual_user_authorization_sha256=sha(BASE.parent/'manual_CLI38_user_retry_authorization_v1.json'),prior37_zero_tool_location_error=True,zero_previous_completed_media=True,no39=True,automatic_retry=False,conversation_id=None))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task=ROOT.name+f'/call{number}',global_count=number,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic();created=False;exception=None
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  try:
   proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);created=True
   save(a/'process.json',dict(pid=proc.pid,command=cmd,owned_only=True,proxy='http://127.0.0.1:7892',GODEBUG='http2client=0',argv_utf16_units_including_NUL=units))
   deadline=start+7200;stop=None
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
