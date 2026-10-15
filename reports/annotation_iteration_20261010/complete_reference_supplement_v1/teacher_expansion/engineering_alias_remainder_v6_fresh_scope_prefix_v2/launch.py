"""Only fresh UNUSED35/36, one actual child each, never retry."""
from common import ROOT,BASE,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
import os,subprocess,time,json

def command(number,prompt):
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(ROOT/f'call{number}/agy.log'),'-p',prompt]

def launch(number):
 assert number in (35,36)
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FRESH_SCOPE_V6_FIXED_CLI35_36'
 assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
 a=ROOT/f'call{number}';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 rows=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
 assert max(r['global_count'] for r in rows)==number-1 and fr['CLI_after']==number<=36 and fr['timeout_seconds']==7200
 assert not(a/'request.json').exists() and not any(Path(p).exists() for p in fr['write_whitelist'])
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 if number==35:assert ledger.read_bytes()==(ROOT/'actual_global34_ledger_prefix.jsonl').read_bytes()
 if number==36:
  prior=read(ROOT/'call35/audit.json');assert prior['continuation_decision']['eligible'] and (ROOT/'call35/terminal.json').exists()
 prompt=(a/'short_prompt.txt').read_text(encoding='utf-8');cmd=command(number,prompt)
 units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),bootstrap_instruction_path=fr['bootstrap_instruction_path'],bootstrap_sha256=fr['bootstrap_sha256'],short_prompt_sha256=sha(a/'short_prompt.txt'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),CLI_before=number-1,CLI_after=number,conversation_id=None,fresh_unused_call=True,recovery_registered=False,argv_utf16_units_including_NUL=units,timeout_seconds=7200,automatic_retry=False))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task=ROOT.name+'/'+a.name,global_count=number,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic();created=False;failure=None
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  try:
   proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);created=True
   save(a/'process.json',dict(pid=proc.pid,command=cmd,owned_only=True,argv_utf16_units_including_NUL=units,proxy='http://127.0.0.1:7892',GODEBUG='http2client=0'))
   try:code=proc.wait(timeout=7200);stop=None
   except subprocess.TimeoutExpired:
    proc.terminate()
    try:code=proc.wait(timeout=30)
    except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
    stop='OWNED_TIMEOUT'
  except OSError as e:code=None;stop='PRESPAWN_ENGINEERING_FAILURE_NO_RETRY';failure=repr(e)
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,launch_exception=failure,child_process_created=created,AGY_terminal_exists=created,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=number,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL' if created else 'ENGINEERING_PRESPAWN_TERMINAL',task=ROOT.name+'/'+a.name,global_count=number,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,child_process_created=created,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 print(json.dumps(dict(event='ACTUAL_TERMINAL',CLI=number,exit_code=code,created=created)),flush=True)
