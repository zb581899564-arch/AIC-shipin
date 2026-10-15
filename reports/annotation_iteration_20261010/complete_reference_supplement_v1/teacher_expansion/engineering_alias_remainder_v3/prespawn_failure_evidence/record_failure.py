from pathlib import Path
import hashlib,json,subprocess
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
BASE=ROOT.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)

a=ROOT/'call34'
prompt=(a/'prompt.txt').read_text(encoding='utf-8')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','120m','--output-format','stream-json','--log-file',str(a/'agy.log'),'-p',prompt]
commandline=subprocess.list2cmdline(cmd)
fr=read(a/'freeze.json')
drift=[p for p,s in fr['inputs'].items() if sha(p)!=s]
assert not drift
assert sha(ROOT/'root_start_admission.json')=='9a7b99b1ec87ebe31e1fdef1eb3ca088849ee527310dca88af15d65804b392c2'
assert (a/'stream.jsonl').stat().st_size==0 and (a/'stderr.txt').stat().st_size==0
absent=['process.json','terminal.json','agy.log']
assert all(not(a/n).exists() for n in absent)
ledger=BASE/'global_CLI_ledger.jsonl'
payload=ledger.read_bytes()
with (HERE/'ledger_after_registered34.jsonl').open('xb') as f:f.write(payload)
rows=[json.loads(s) for s in payload.decode('utf-8').splitlines() if s.strip()]
assert max(r['global_count'] for r in rows)==34
assert rows[-1]['event']=='REGISTERED' and rows[-1]['task']=='engineering_alias_remainder_v3/call34'
assert not any(Path(p).exists() for p in fr['write_whitelist'])
bindings={str(p):sha(p) for p in [ROOT/'registered.json',ROOT/'root_start_admission.json',ROOT/'controller.py',ROOT/'launch.py',ROOT/'run_call.py',ROOT/'observer.py',ROOT/'execution_code_binding.json',a/'request.json',a/'prompt.txt',a/'freeze.json',a/'stream.jsonl',a/'stderr.txt',HERE/'ledger_after_registered34.jsonl',Path(__file__)]}
save(HERE/'actual_prespawn_failure.json',dict(
    status='ACTUAL_WINDOWS_CREATEPROCESS_FAILURE_BEFORE_AGY_CHILD_NO_RETRY',utc=datetime.now(timezone.utc).isoformat(),
    actual_exec_tool_result=dict(chunk_id='ae4856',exit_code=1,wall_time_seconds=1.2319542,exception='FileNotFoundError: [WinError 206] 文件名或扩展名太长。',location='launch.py subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err)',controller_error='subprocess.CalledProcessError: run_call.py 34 returned non-zero exit status 1'),
    command_reconstruction_method='subprocess.list2cmdline of frozen launch command and exact saved prompt; reconstruction only, no process/model probe',
    commandline_utf16_code_units_including_NUL=len(commandline.encode('utf-16-le'))//2+1,prompt_characters=len(prompt),prompt_bytes=(a/'prompt.txt').stat().st_size,
    registered_runner=read(ROOT/'registered.json'),request=read(a/'request.json'),
    child_process_created=False,actual_model_calls=0,actual_tools=0,stream_bytes=0,stderr_bytes=0,
    absent_child_artifacts=absent,all_frozen_input_sha_verified=True,checked_input_count=len(fr['inputs']),successful_teacher_outputs=0,
    global_ledger_registered_count=34,global_cap=36,automatic_retry=False,further_calls_launched=False,
    ledger_not_rewound=True,global_registration_reconciliation='ROOT_DECISION_REQUIRED_NO_SELF_REUSE',cash_cost='UNKNOWN_NOT_ZERO',
    agy_natural_terminal='NOT_CREATED_PROCESS_NEVER_STARTED',engineering_parent_terminal='ACTUAL_EXEC_EXIT1',
    observer=dict(session_id=68472,started_once=True,stopped_by_owned_session_CTRL_C=True,stop_tool_chunk='0c0ac6',exit_code=1,stop_wall_seconds=0.015393,last_actual_progress='CLI34 DONE_tools0',reason='No child could produce terminal; stopped owned read-only observer after prespawn failure'),
    old_frozen_sources_and_receipts_unchanged=True,bindings=bindings,
    raw_stdout_copy='No AGY stdout exists; zero-byte stream preserved. Exception text and timing above copied from actual exec result metadata, not represented as an original shell log.',
    next_action='STOP; do not rerun original controller or consume next planned scope without explicit ROOT engineering admission'))
print(json.dumps(dict(status='RECORDED_ACTUAL_PRESPAWN_FAILURE',receipt_path=str(HERE/'actual_prespawn_failure.json'),receipt_sha256=sha(HERE/'actual_prespawn_failure.json'),registered_sha256=sha(ROOT/'registered.json'),request_sha256=sha(a/'request.json'),commandline_utf16_code_units_including_NUL=len(commandline.encode('utf-16-le'))//2+1,global_count=34,model_calls=0,tools=0),ensure_ascii=False))
