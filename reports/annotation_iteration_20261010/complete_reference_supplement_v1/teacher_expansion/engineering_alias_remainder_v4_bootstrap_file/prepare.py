"""Preparation only; preserve v3 bytes and project only index/output call paths."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,subprocess,uuid
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'engineering_alias_remainder_v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def put(p,b):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('xb') as f:f.write(b)
def source(name,text):put(ROOT/name,text.encode('utf-8'))
def main():
 assert not(ROOT/'plan.json').exists() and not(ROOT/'root_start_admission.json').exists()
 assert sha(OLD/'prespawn_failure_evidence/actual_prespawn_failure.json')=='9a3b342035d88c708857910ab35e16931b4476953982adc6631e92adebfffad9'
 assert not(OLD/'call34/process.json').exists() and not(OLD/'call34/terminal.json').exists()
 assert (OLD/'call34/stream.jsonl').stat().st_size==(OLD/'call34/stderr.txt').stat().st_size==0
 ledger=BASE/'global_CLI_ledger.jsonl';rows=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()]
 assert rows[-1]['global_count']==34 and rows[-1]['event']=='REGISTERED' and rows[-1]['task']=='engineering_alias_remainder_v3/call34'
 put(ROOT/'global_registered34_ledger_prefix.jsonl',ledger.read_bytes())
 # Only copy runtime source into this new version. All v3 freezes remain immutable.
 common=(OLD/'common.py').read_text(encoding='utf-8').replace("out=[('view_file',key(index['index_path']))]","out=[('view_file',key(index['bootstrap_instruction_path'])),('write_to_file',key(index['bootstrap_ack_path'])),('view_file',key(index['index_path']))]")
 source('common.py',common)
 audit=(OLD/'audit.py').read_text(encoding='utf-8')
 audit=audit.replace('import json,sys','import json,sys,re')
 audit=audit.replace('expected_full=[expected[0]]','expected_full=expected[:3]').replace("windows=[w]))[1:]","windows=[w]))[3:]")
 audit=audit.replace('reports=[];offset=1','reports=[];offset=3').replace("windows=[w])))-1","windows=[w])))-3").replace('core[:1]==expected[:1]','core[:3]==expected[:3]')
 audit=audit.replace("dict(index_path=index['index_path'],windows=[w])","dict(index_path=index['index_path'],bootstrap_instruction_path=index['bootstrap_instruction_path'],bootstrap_ack_path=index['bootstrap_ack_path'],windows=[w])")
 anchor=' reports=[];offset=3'
 extra=''' bootstrap=[t for t in latest.values() if info(t)==('view_file',key(index['bootstrap_instruction_path']))]
 bootstrap_ok=False
 if len(bootstrap)==1:
  bt=bootstrap[0];params=bt.get('tool_info',{}).get('parameters',{});output=str(bt.get('tool_info',{}).get('output',''))
  byte_report=re.search(r'(\\d+) bytes',output);line_report=re.search(r'(\\d+) lines',output)
  bootstrap_file=Path(index['bootstrap_instruction_path']);line_count=len(bootstrap_file.read_bytes().splitlines())
  bootstrap_ok=bt.get('state')=='DONE' and set(params)=={'AbsolutePath'} and byte_report is not None and int(byte_report.group(1))==bootstrap_file.stat().st_size and line_report is not None and int(line_report.group(1))==line_count and not any(x in output.lower() for x in ('truncat','not found','cannot read','failed','error')) and bool(done) and done[0]['step_index']==bt['step_index']
 if not bootstrap_ok:issues.append(dict(reason='BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE',job_index=None))
 ack_steps=[t for t in latest.values() if info(t)==('write_to_file',key(index['bootstrap_ack_path']))]
 ack_ok=False
 try:
  expected_ack=read(index['bootstrap_ack_expected_path']);actual_ack=read(index['bootstrap_ack_path'])
  ack_ok=actual_ack==expected_ack and len(ack_steps)==1 and ack_steps[0].get('state')=='DONE' and core[:3]==expected[:3] and len(done)>=2 and done[1]['step_index']==ack_steps[0]['step_index'] and bootstrap_ok
 except Exception:pass
 if not ack_ok:issues.append(dict(reason='BOOTSTRAP_ACK_MISSING_WRONG_OR_ORDER',job_index=None))
'''
 assert anchor in audit;audit=audit.replace(anchor,extra+anchor)
 audit=audit.replace("actual_supply=supply,expected_core_tool_calls=", "actual_supply=supply,bootstrap_successful_complete=bootstrap_ok,bootstrap_ack_complete=ack_ok,bootstrap_attempts=bootstrap,bootstrap_ack_steps=ack_steps,bootstrap_required_bytes=Path(index['bootstrap_instruction_path']).stat().st_size,bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().splitlines()),bootstrap_ack_sha256=sha(index['bootstrap_ack_path']) if Path(index['bootstrap_ack_path']).exists() else None,bootstrap_provenance_limit='Full file metadata and unique tail ACK verify limited instruction supply/routes, not text attention or semantics',expected_core_tool_calls=")
 audit=audit.replace('F35_prior_DONE_without_fact_reprovided=bool(prior_docs)',"F35_reprovide_planned_exception=bool(prior_docs),F35_actual_new_DONE_steps=steps('view_file',next((f['path'] for g in w['groups'] for f in g['frames'] if f['frame_id']=='F35'),'')) if prior_docs else []")
 source('audit.py',audit)
 controller=(OLD/'controller.py').read_text(encoding='utf-8').replace('ROOT_APPROVED_START_ALIAS_V3_FIXED_CLI34_36','ROOT_APPROVED_START_BOOTSTRAP_V4_FIXED_CLI34_36')
 controller=controller.replace("==33\n for n", "==34\n assert (BASE/'global_CLI_ledger.jsonl').read_bytes()==(ROOT/'global_registered34_ledger_prefix.jsonl').read_bytes()\n from launch import no_old_owned_processes\n no_old_owned_processes()\n for n")
 source('controller.py',controller)
 source('observer.py',(OLD/'observer.py').read_text(encoding='utf-8').replace("same_index_read_count=audit['same_index_read_count'],", "bootstrap_successful_complete=audit['bootstrap_successful_complete'],bootstrap_ack_complete=audit['bootstrap_ack_complete'],bootstrap_attempts=audit['bootstrap_attempts'],same_index_read_count=audit['same_index_read_count'],"))
 source('run_call.py',"from common import ROOT\nfrom launch import launch\nimport sys\nif __name__=='__main__':\n n=int(sys.argv[1]);launch(n,(ROOT/f'call{n}/short_prompt.txt').read_text(encoding='utf-8'))\n")
 put(ROOT/'inherited_v3_prompt_source.py',(OLD/'prompt.py').read_bytes())
 source('PROTOCOL.md','''# Bootstrap file engineering v4 (preparation; ROOT gate required)
Fixed 24 references / 21 supplement denominator, source1458, original floor64/source/clock/target/scientific schema and quality gates stay unchanged. Only text transport changes; no stdin protocol assumption, no extra model probe.
CLI34 = 17 remaining groups8..15 plus complete18; CLI35=19+20; CLI36=21+22+23. Model gemini-3.8-flash-high,7200s each,globalcap36,no37,no automatic retry. Old33 actual32facts/oldF35 DONE193 without facts and old errors/costs unchanged. v3 REGISTERED34 WinError206 had no created AGY child/model/tool; preserve original request/raw/stderr/registered/failure and ledger. v4 uses explicit RECOVERY_REGISTERED count34,prior_actual_spawned_CLI33; no ledger rollback/no model retry.
Each call requires one exact AbsolutePath-only view_file of bootstrap_instruction.txt FIRST, DONE exactly once and reported full bytes/lines equal frozen payload, no truncation/failure marker. Then exactly one write_to_file bootstrap_ack.json BEFORE index. ACK strict6fields must match independent bootstrap_ack_expected.json (program-only frozen input, NOT teacher-readable whitelist). Unique tail marker and complete route summary appear only at instruction end, never short-p. Missing/ERROR/partial bootstrap or wrong/missing/order ACK is STOP. Full metadata and tail ACK prove limited text supply/routes, not complete attention/semantic correctness. Same exact frozen index necessary readonly selfchecks allowed, counted; successful own fact/proposal output selfread once after write; ACK cannot be selfread. No other new teacher-readable file.
Bootstrap text reflows every scientific instruction and literal tool parameter from original frozen prompt into <=450 lines, each<=1000 chars. Remove only redundant expanded read/write lists; complete index/freeze/audit whitelists still enforce paths. Exact old call-directory projection only affects this version index/output paths; aliases remain v3 paths. Original full prompt separately preserved byte exact, NOT teacher-readable. All479 alias paths/payloads remain original v3 exactbytes, prior17 package/proof unchanged. No new image/frame/crop/clock/decode. Negative prep tests are synthetic memory only, not actual observations.
Native four slot reads same response sequential tools, all4DONE then immediate four-fact write, no failed media hidden. All64 actual facts (17 prior32+new32) before clip once, effective8 in two groups4, full-domain proposal; no quota, no static action/motive inference, no old labels/scores/reviews. All new facts/proposals x-write new v4 paths. ExplicitF35 planned exception never substitutes actual new DONE evidence.
Dynamic original core141/181/271 plus bootstrap view1 and ACK write1 =143/183/273; CLI34 prior-context one extra actual read separate. Prefix is bootstrap view -> ACK write -> index view -> priorcontext17 -> groups. Each completed scope has independent immutable prefix including CLI36 middle22. Root semantic review separate; audit supply never labels gold/train. Actual media ERROR/auth/reported failure/non-success/early success stops; bare nonmedia no-body metadata UNKNOWN recorded independently.
Before launch bind code/science/all original inputs/old failure/ledger prefix, require ROOT_APPROVED_START_BOOTSTRAP_V4_FIXED_CLI34_36 and readonly no owned v3 process. Actual subprocess.list2cmdline Windows UTF16 code units INCLUDING NUL must dynamically be <32767; short request expected<1024. Do not alter frozen text to fit. Launch exceptions get independent actual engineering terminal with child_created=false, not an AGY result; cash UNKNOWN, preserve every registration/terminal and original costs.
''')
 # launch.py and verify.py are prewritten independent v4 sources; frozen along with generated copies.
 assert (ROOT/'launch.py').exists() and(ROOT/'verify.py').exists()
 prior=[OLD/n for n in ('registered.json','root_start_admission.json','execution_code_binding.json','alias_original_payload_binding.json','independent_preparation_acceptance.json','prespawn_failure_evidence/actual_prespawn_failure.json','prespawn_failure_evidence/ledger_after_registered34.jsonl')]+[OLD/'call34'/n for n in ('request.json','prompt.txt','stream.jsonl','stderr.txt','freeze.json')]+[ROOT/'global_registered34_ledger_prefix.jsonl']
 execution=ROOT/'execution_code_binding.json';sources={str(p):sha(p) for p in ROOT.glob('*.py')};sources[str(ROOT/'PROTOCOL.md')]=sha(ROOT/'PROTOCOL.md')
 save(execution,dict(sources=sources,prior_failure_and_transfer_inputs={str(p):sha(p) for p in prior},requires_root_start_admission=True,old_registration_not_rewound=True,new_model_calls=0))
 calls=[]
 for n in (34,35,36):
  a=ROOT/f'call{n}';a.mkdir();old=OLD/f'call{n}';oldfr=read(old/'freeze.json');idx=copy.deepcopy(read(old/'index.json'))
  oldpath=str(old);newpath=str(a)
  project=lambda p:p.replace(oldpath,newpath)
  idx['index_path']=str(a/'index.json');idx['bootstrap_instruction_path']=str(a/'bootstrap_instruction.txt');idx['bootstrap_ack_path']=str(a/'bootstrap_ack.json');idx['bootstrap_ack_expected_path']=str(a/'bootstrap_ack_expected.json')
  for w in idx['windows']:
   for g in w['groups']:g['output_path']=project(g['output_path'])
   w['proposal_path']=project(w['proposal_path'])
  save(a/'index.json',idx);put(a/'original_v3_frozen_prompt.txt',(old/'frozen_prompt.txt').read_bytes())
  lit=copy.deepcopy(read(old/'literal_execution_parameters.json'))
  for w in lit:
   for g in w['native_groups']:g['write_to_file']['TargetFile']=project(g['write_to_file']['TargetFile'])
   w['proposal_write_to_file']['TargetFile']=project(w['proposal_write_to_file']['TargetFile'])
  save(a/'literal_execution_parameters.json',lit)
  ack=dict(marker='BOOTSTRAP_END_'+uuid.uuid4().hex,fixed_job_indices=oldfr['fixed_job_indices'],native_required_counts={str(w['job_index']):sum(len(g['frames']) for g in w['groups']) for w in idx['windows']},native_alias_bounds_per_window={str(w['job_index']):dict(first=w['groups'][0]['frames'][0]['path'],last=w['groups'][-1]['frames'][-1]['path']) for w in idx['windows']},actual_student64_per_window={str(w['job_index']):64 for w in idx['windows']},effective_preview8_per_window={str(w['job_index']):8 for w in idx['windows']})
  save(a/'bootstrap_ack_expected.json',ack)
  from bootstrap import build
  body=build((old/'frozen_prompt.txt').read_text(encoding='utf-8').replace(oldpath,newpath),idx,lit,ack)
  put(a/'bootstrap_instruction.txt',body.encode('utf-8'))
  assert len(body.splitlines())<=450 and max(map(len,body.splitlines()))<=1000
  short=f"First view_file the ENTIRE file at AbsolutePath {idx['bootstrap_instruction_path']}, exactly once, no line range. Follow its full instructions: write tail ACK before index, then fixed media and proposals. Any ERROR/truncation/missing ACK: STOP, no retry. Only view_file/write_to_file."
  put(a/'short_prompt.txt',short.encode('utf-8'))
  inputs=dict(oldfr['inputs']);inputs.update(sources);inputs[str(execution)]=sha(execution);inputs.update({str(p):sha(p) for p in prior})
  for p in a.iterdir():inputs[str(p)]=sha(p)
  fr=copy.deepcopy(oldfr);fr.update(inputs=inputs,read_whitelist=[idx['bootstrap_instruction_path']]+[project(p) for p in oldfr['read_whitelist']],self_read_whitelist=[project(p) for p in oldfr['self_read_whitelist']],write_whitelist=[idx['bootstrap_ack_path']]+[project(p) for p in oldfr['write_whitelist']],protocol_sha256=sha(ROOT/'PROTOCOL.md'),execution_binding_sha256=sha(execution),expected_core_tool_calls=oldfr['expected_core_tool_calls']+2,original_media_core_tool_calls=oldfr['expected_core_tool_calls'],bootstrap_instruction_path=idx['bootstrap_instruction_path'],bootstrap_ack_path=idx['bootstrap_ack_path'],bootstrap_ack_expected_path=idx['bootstrap_ack_expected_path'],bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),short_prompt_sha256=sha(a/'short_prompt.txt'),original_v3_frozen_prompt_sha256=sha(a/'original_v3_frozen_prompt.txt'),prior_actual_spawned_CLI=33,prespawn_failure_sha256=sha(prior[5]),CLI_before=34 if n==34 else n-1,recovery_registered=n==34,ledger_prefix_sha256=sha(ROOT/'global_registered34_ledger_prefix.jsonl'))
  save(a/'freeze.json',fr)
  from launch import command
  cmd=command(n,short);length=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1;assert length<32767 and length<1024
  calls.append(dict(CLI=n,jobs=fr['fixed_job_indices'],original_media_core=fr['original_media_core_tool_calls'],core_with_bootstrap_ack=fr['expected_core_tool_calls'],context_steps=fr['context_read_count'],argv_utf16_units_including_NUL=length,input_count=len(inputs),freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),bootstrap_lines=len(body.splitlines()),max_line_chars=max(map(len,body.splitlines())),short_prompt_sha256=sha(a/'short_prompt.txt'),original_prompt_byte_exact=True,only_authorized_reflow_and_whitelist_dedup=True))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p)))
 save(ROOT/'plan.json',dict(status='PREPARED_BOOTSTRAP_V4_PENDING_ROOT_REVIEW',routing={'34':[17,18],'35':[19,20],'36':[21,22,23]},calls=calls,global_registered=34,prior_actual_spawned_CLI=33,global_cap=36,root_gate_status_required='ROOT_APPROVED_START_BOOTSTRAP_V4_FIXED_CLI34_36',new_model_calls=0))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_AST_PROJECTED_BYTES_SHORT_ARGV_FROZEN_NO_MODEL_PENDING_ROOT',AST=AST,calls=calls,execution_binding_sha256=sha(execution),alias_binding_sha256=sha(OLD/'alias_original_payload_binding.json'),prespawn_failure_sha256=sha(prior[5]),fixed_denominator=24,teacher_expansion_denominator=21,no_model_started=True,new_model_calls=0,new_video_decode=0,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(root=str(ROOT),execution_binding_sha256=sha(execution),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),calls=calls),ensure_ascii=False))
if __name__=='__main__':main()
