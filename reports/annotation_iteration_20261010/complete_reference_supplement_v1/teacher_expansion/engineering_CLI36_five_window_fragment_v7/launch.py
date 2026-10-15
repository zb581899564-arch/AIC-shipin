"""Only prospective final36 five zero-completed windows; no other version/retry."""
from common import ROOT,BASE,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
import os,subprocess,time,json

def command(prompt):
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(ROOT/'call36/agy.log'),'-p',prompt]

def launch():
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRAGMENTED_FINAL36_FIXED19_23'
 assert gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json') and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(ROOT/'independent_CPU_negative_acceptance.json')
 a=ROOT/'call36';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 assert ledger.read_bytes()==(ROOT/'actual_global35_ledger_prefix.jsonl').read_bytes()
 assert not any(BASE.glob('*/call36/request.json')) and fr['CLI_before']==35 and fr['CLI_after']==36 and fr['timeout_seconds']==7200
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 prompt=(a/'short_prompt.txt').read_text(encoding='utf-8');cmd=command(prompt);units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),main_instruction_path=fr['main_instruction_path'],main_instruction_sha256=sha(fr['main_instruction_path']),short_prompt_sha256=sha(a/'short_prompt.txt'),fixed_job_indices=[19,20,21,22,23],CLI_before=35,CLI_after=36,timeout_seconds=7200,argv_utf16_units_including_NUL=units,new_prospective_routing=True,zero_previous_completed_media=True,no35_retry=True,automatic_retry=False,conversation_id=None))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task=ROOT.name+'/call36',global_count=36,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
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
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,launch_exception=exception,child_process_created=created,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=36,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL' if created else 'ENGINEERING_PRESPAWN_TERMINAL',task=ROOT.name+'/call36',global_count=36,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,child_process_created=created,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
