"""Fresh36/37 parameterized routing; actual sidecar/gate/budget enforced."""
from common import ROOT,BASE,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
import os,subprocess,time,json

def command(number,prompt):
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(ROOT/f'call{number}/agy.log'),'-p',prompt]

def launch(number):
 assert number in (36,37)
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRAGMENTED_SPLIT36_37_FIXED19_23'
 assert gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json') and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(ROOT/'independent_CPU_negative_acceptance.json')
 a=ROOT/f'call{number}';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 auth=read(BASE.parent/'teacher_dispatch_capacity_v5_split_recovery_authorization.json');constraints=read(BASE.parent/'teacher_split_v5_continuation_constraints.json')
 assert auth['new_fresh_routes']=={'36':[19,20],'37':[21,22,23]} and auth['new_global_CLI_max']==37 and auth['timeout_seconds_per_call']==7200
 assert constraints['global_cap']==37 and constraints['timeout_seconds_each']==7200 and constraints['any_whole_ERROR_even_postcompletion_STOP_before37'] is True and constraints['no_postcompletion_network_exception'] is True
 assert fr['global_cap']==37 and fr['fixed_job_indices']==auth['new_fresh_routes'][str(number)]
 if number==36:assert ledger.read_bytes()==(ROOT/'actual_global35_ledger_prefix.jsonl').read_bytes()
 else:
  from audit import continuation_decision
  prior=read(ROOT/'call36/audit.json');assert prior['status']=='PASS_WHOLE_ACTUAL_CLI_PENDING_ROOT_SEMANTIC' and prior['continuation_decision']['eligible'] and prior['continuation_decision']['whole_success']
  firstterm=read(ROOT/'call36/terminal.json');assert firstterm['child_process_created'] is True and firstterm['exit_code']==0 and firstterm['stop_reason'] is None
  assert len(prior['actual_scope_receipts'])==2 and [x['job_index'] for x in prior['actual_scope_receipts']]==[19,20] and prior['actual_result_status']=='SUCCESS'
  # Recheck every immutable prefix/output and input immediately before37.
  for scope in prior['actual_scope_receipts']:
   d=read(scope['audit_path']);assert sha(scope['audit_path'])==scope['audit_sha256']
   assert d['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
   b=Path(d['immutable_prefix']['path']).read_bytes();assert sha(d['immutable_prefix']['path'])==d['immutable_prefix']['sha256'] and (ROOT/'call36/stream.jsonl').read_bytes()[:len(b)]==b
   for o in d['immutable_actual_outputs']:assert sha(o['original_path'])==o['sha256'] and sha(o['sealed_copy_path'])==o['sealed_copy_sha256']
  for q,h in read(ROOT/'call36/freeze.json')['inputs'].items():assert sha(q)==h
  assert sha(ROOT/'call36/stream.jsonl')==read(ROOT/'call36/terminal.json')['stream_sha256']
  rows=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()];assert max(x['global_count'] for x in rows)==36 and len([x for x in rows if x['global_count']==36 and x['event']=='TERMINAL'])==1
 assert not any(BASE.glob(f'*/call{number}/request.json')) and fr['CLI_before']==number-1 and fr['CLI_after']==number and fr['timeout_seconds']==7200
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 prompt=(a/'short_prompt.txt').read_text(encoding='utf-8');cmd=command(number,prompt);units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),main_instruction_path=fr['main_instruction_path'],main_instruction_sha256=sha(fr['main_instruction_path']),short_prompt_sha256=sha(a/'short_prompt.txt'),fixed_job_indices=fr['fixed_job_indices'],CLI_before=number-1,CLI_after=number,timeout_seconds=7200,argv_utf16_units_including_NUL=units,new_prospective_routing=True,zero_previous_completed_media=True,no35_retry=True,automatic_retry=False,conversation_id=None))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task=ROOT.name+f'/call{number}',global_count=number,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic();created=False;exception=None
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  try:
   proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);created=True
   save(a/'process.json',dict(pid=proc.pid,command=cmd,owned_only=True,proxy='http://127.0.0.1:7892',GODEBUG='http2client=0',argv_utf16_units_including_NUL=units))
   try:code=proc.wait(timeout=7200);stop=None
   except subprocess.TimeoutExpired:
    proc.terminate()
    try:code=proc.wait(timeout=30)
    except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
    stop='OWNED_TIMEOUT_NO_RETRY'
  except OSError as e:code=None;stop='PRESPAWN_FAILURE_NO_RETRY';exception=repr(e)
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,launch_exception=exception,child_process_created=created,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=number,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL' if created else 'ENGINEERING_PRESPAWN_TERMINAL',task=ROOT.name+f'/call{number}',global_count=number,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,child_process_created=created,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
