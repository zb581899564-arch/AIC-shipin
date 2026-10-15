from common import ROOT,BASE,read,sha,save
from datetime import datetime,timezone
from pathlib import Path
import os,subprocess,time,json
def launch(number,prompt):
 assert number in (34,35,36)
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_ALIAS_V3_FIXED_CLI34_36'
 assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
 prior=read(BASE/'remaining_CLI33_36_same_index_selfcheck_v2/call07/terminal.json');assert prior['CLI_after']==33
 a=ROOT/f'call{number}';fr=read(a/'freeze.json')
 assert max(json.loads(s)['global_count'] for s in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip())==fr['CLI_before']
 assert fr['CLI_after']==number<=36 and fr['timeout_seconds']==7200 and not(a/'request.json').exists()
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 assert sha(ROOT/'PROTOCOL.md')==fr['protocol_sha256'] and sha(BASE/'PROTOCOL.md')==fr['parent_protocol_sha256']
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 assert prompt==(a/'frozen_prompt.txt').read_text(encoding='utf-8') and sha(a/'frozen_prompt.txt')==fr['frozen_prompt_sha256']
 with(a/'prompt.txt').open('x',encoding='utf-8',newline='') as f:f.write(prompt)
 cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(a/'agy.log'),'-p',prompt]
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),prompt_sha256=sha(a/'prompt.txt'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),conversation_id=None,CLI_before=number-1,CLI_after=number,timeout_seconds=7200,automatic_retry=False))
 ledger=BASE/'global_CLI_ledger.jsonl'
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task='engineering_alias_remainder_v3/'+a.name,global_count=number,request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic()
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);save(a/'process.json',dict(pid=proc.pid,command=cmd[:cmd.index('-p')],owned_only=True))
  try:code=proc.wait(timeout=7200);stop=None
  except subprocess.TimeoutExpired:
   proc.terminate()
   try:code=proc.wait(timeout=30)
   except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
   stop='OWNED_TIMEOUT'
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=number,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL',task='engineering_alias_remainder_v3/'+a.name,global_count=number,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 print(json.dumps(dict(event='ACTUAL_TERMINAL',CLI_after=number,exit_code=code,raw_sha256=sha(a/'stream.jsonl'))),flush=True)
