from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,subprocess,time
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def launch(a,prompt,conversation=None):
    gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_SELF_CHECK_CLI33_36' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
    prior=read(ROOT.parent/'remaining_CLI32_36_literal_paths_v1/call06/terminal.json');assert prior['CLI_after']==32
    counts=[json.loads(s)['global_count'] for s in (ROOT.parent/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    fr=read(a/'freeze.json');assert max(counts)==fr['CLI_before'];assert sha(ROOT/'PROTOCOL.md')==fr['protocol_sha256'] and sha(ROOT.parent/'PROTOCOL.md')==fr['parent_protocol_sha256']
    for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
    assert not (a/'request.json').exists() and not any(Path(p).exists() for p in fr['write_whitelist'])
    assert sha(a/'frozen_prompt.txt')==fr['frozen_prompt_sha256'] and prompt==(a/'frozen_prompt.txt').read_text(encoding='utf-8')
    with (a/'prompt.txt').open('x',encoding='utf-8',newline='') as output:output.write(prompt)
    cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(a/'agy.log')]
    if conversation:cmd+=['--conversation',conversation]
    cmd+=['-p',prompt]
    save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),prompt_sha256=sha(a/'prompt.txt'),
      root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),literal_preview_argument_receipt_sha256=sha(a/'literal_preview_arguments.json'),conversation_id=conversation,CLI_before=fr['CLI_before'],CLI_after=fr['CLI_after'],timeout_seconds=fr['timeout_seconds'],automatic_retry=False))
    ledger=ROOT.parent/'global_CLI_ledger.jsonl'
    with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',task='remaining_CLI33_36_same_index_selfcheck_v2/'+a.name,global_count=fr['CLI_after'],request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
    env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
    started=time.monotonic()
    with (a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
        proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err)
        save(a/'process.json',dict(pid=proc.pid,command=cmd[:cmd.index('-p')],owned_only=True))
        try:code=proc.wait(timeout=fr['timeout_seconds']);stop=None
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:code=proc.wait(timeout=30)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
            stop='OWNED_TIMEOUT'
    save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-started,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),
      cash_cost='UNKNOWN_NOT_ZERO',CLI_after=fr['CLI_after'],outputs=[p for p in fr['write_whitelist'] if Path(p).exists()]))
    with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL',task='remaining_CLI33_36_same_index_selfcheck_v2/'+a.name,global_count=fr['CLI_after'],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
    print(json.dumps(dict(task=a.name,exit_code=code,CLI_after=fr['CLI_after'],raw_sha256=sha(a/'stream.jsonl'))),flush=True)
