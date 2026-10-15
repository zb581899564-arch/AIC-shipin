from common import ROOT,BASE,read,sha,save
from datetime import datetime,timezone
from pathlib import Path
import os,subprocess,time,json
OLD=BASE/'engineering_alias_remainder_v3'
def command(number,prompt):
 a=ROOT/f'call{number}'
 return ['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(a/'agy.log'),'-p',prompt]
def no_old_owned_processes():
 # Read only exact old-version Python/AGY command identities; no credentials.
 path=OLD.name.replace("'","''")
 query=f"$p = @(Get-CimInstance Win32_Process | Where-Object {{ $_.Name -match '^(python|pythonw|agy)\\.exe$' -and $_.CommandLine -like '*{path}*' }} | Select-Object ProcessId,ParentProcessId,Name,CommandLine); ConvertTo-Json -InputObject $p -Compress"
 r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,text=True,encoding='utf-8',check=True)
 rows=json.loads(r.stdout.strip() or '[]');assert not rows,('OLD_V3_OWNED_PROCESS_ACTIVE',rows)
 return dict(utc=datetime.now(timezone.utc).isoformat(),readonly_old_v3_owned_processes=rows,query_source=query,no_service_or_account_change=True)
def launch(number,prompt):
 assert number in (34,35,36)
 gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_BOOTSTRAP_V4_FIXED_CLI34_36'
 assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
 a=ROOT/f'call{number}';fr=read(a/'freeze.json');ledger=BASE/'global_CLI_ledger.jsonl'
 rows=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
 assert max(r['global_count'] for r in rows)==fr['CLI_before'] and fr['CLI_after']==number<=36
 if number==34:
  assert ledger.read_bytes()==(ROOT/'global_registered34_ledger_prefix.jsonl').read_bytes()
  assert sha(OLD/'prespawn_failure_evidence/actual_prespawn_failure.json')==fr['prespawn_failure_sha256']
  assert not(OLD/'call34/process.json').exists() and not(OLD/'call34/terminal.json').exists()
  assert (OLD/'call34/stream.jsonl').stat().st_size==(OLD/'call34/stderr.txt').stat().st_size==0
 process_check=no_old_owned_processes()
 assert fr['timeout_seconds']==7200 and not(a/'request.json').exists()
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 assert sha(ROOT/'PROTOCOL.md')==fr['protocol_sha256'] and sha(BASE/'PROTOCOL.md')==fr['parent_protocol_sha256']
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 assert prompt==(a/'short_prompt.txt').read_text(encoding='utf-8') and sha(a/'short_prompt.txt')==fr['short_prompt_sha256']
 cmd=command(number,prompt);units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1
 assert units<32767,('WINDOWS_COMMAND_LINE_LIMIT',units)
 save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),short_prompt_sha256=sha(a/'short_prompt.txt'),bootstrap_instruction_path=str(a/'bootstrap_instruction.txt'),bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),conversation_id=None,CLI_before=fr['CLI_before'],CLI_after=number,prior_actual_spawned_CLI=33,recovery_registered=number==34,prespawn_failure_sha256=fr['prespawn_failure_sha256'],argv_utf16_units_including_NUL=units,readonly_old_v3_process_check=process_check,timeout_seconds=7200,automatic_retry=False))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='RECOVERY_REGISTERED' if number==34 else 'REGISTERED',task='engineering_alias_remainder_v4_bootstrap_file/'+a.name,global_count=number,prior_actual_spawned_CLI=33,prior_prespawn_failure_sha256=fr['prespawn_failure_sha256'],request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0');start=time.monotonic();created=False;failure=None
 with(a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
  try:
   proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err);created=True
   save(a/'process.json',dict(pid=proc.pid,command=cmd,owned_only=True,argv_utf16_units_including_NUL=units))
   try:code=proc.wait(timeout=7200);stop=None
   except subprocess.TimeoutExpired:
    proc.terminate()
    try:code=proc.wait(timeout=30)
    except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
    stop='OWNED_TIMEOUT'
  except OSError as e:code=None;stop='PRESPAWN_ENGINEERING_FAILURE_NO_RETRY';failure=repr(e)
 save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,launch_exception=failure,child_process_created=created,AGY_terminal_exists=created,wall_seconds=time.monotonic()-start,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),CLI_after=number,cash_cost='UNKNOWN_NOT_ZERO',outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
 with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL' if created else 'ENGINEERING_PRESPAWN_TERMINAL',task='engineering_alias_remainder_v4_bootstrap_file/'+a.name,global_count=number,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,child_process_created=created,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
 print(json.dumps(dict(event='ACTUAL_LAUNCH_TERMINAL',CLI_after=number,exit_code=code,child_process_created=created,raw_sha256=sha(a/'stream.jsonl'))),flush=True)
