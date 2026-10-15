"""Only manual38 path projection from the already reviewed37; no model/decode."""
from common import ROOT,BASE,read,sha,save,expected_core,scientific_core,key
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,json,uuid,subprocess
OLD=BASE/'prospective_CLI37_schema_local_v2'

def put(p,b):
 with Path(p).open('xb') as f:f.write(b)

def project(value,old,new):
 if isinstance(value,str):return value.replace(str(old),str(new))
 if isinstance(value,list):return [project(v,old,new) for v in value]
 if isinstance(value,dict):return {k:project(v,old,new) for k,v in value.items()}
 return value

def main():
 from launch import verify_prior37_failure,MANUAL_STATUS,MANUAL_QUOTE,command
 assert not(ROOT/'plan.json').exists() and not(ROOT/'root_start_admission.json').exists() and not any(BASE.rglob('call38/request.json'))
 failure=verify_prior37_failure();a=ROOT/'call38';old=OLD/'call37'
 oldfr=read(old/'freeze.json')
 for path,h in oldfr['inputs'].items():assert sha(path)==h
 oldbinding=read(OLD/'execution_code_binding.json')
 for path,h in oldbinding['sources'].items():assert sha(path)==h
 prior=[*(old/x for x in ('request.json','process.json','terminal.json','stream.jsonl','stderr.txt','audit.json','actual_terminal_cost.json','freeze.json','index.json','literal_execution_parameters.json')),*(OLD/x for x in ('execution_code_binding.json','dry_run_acceptance.json','independent_CPU_negative_acceptance.json','stopped.json','root_start_admission.json')),BASE.parent/'plan_review/CLI37_schema_local_v2_independent_static_review.json']
 priorbindings={str(q):sha(q) for q in prior}
 auth_path=BASE.parent/'manual_CLI38_user_retry_authorization_v1.json'
 save(auth_path,dict(status=MANUAL_STATUS,utc=datetime.now(timezone.utc).isoformat(),user_quote_exact=MANUAL_QUOTE,authorization_source='CURRENT_HUMAN_EXPLICIT_RETRY_RELAYED_BY_ROOT_TASK_NOT_INFERRED_FROM_OLD_CAP',CLI=38,prior_actual_CLI=37,global_cap=38,fixed_job_indices=[21,22,23],timeout_seconds=7200,no39=True,automatic_retry=False,IP_recovery_verified=False,network_proxy_account_service_changed=False,prior37_actual_bindings=priorbindings,prior37_exact_failure=failure,old_cap37_NO38_STOP_preserved=True,old36_whole_REJECT_preserved=True,new_model_calls_at_preparation=0,cash_cost='UNKNOWN_NOT_ZERO'))
 priorbindings[str(auth_path)]=sha(auth_path)
 ledger=BASE/'global_CLI_ledger.jsonl';put(ROOT/'actual_global37_ledger_prefix.jsonl',ledger.read_bytes());priorbindings[str(ROOT/'actual_global37_ledger_prefix.jsonl')]=sha(ROOT/'actual_global37_ledger_prefix.jsonl')
 save(ROOT/'prior37_zero_tool_location_error.json',dict(status='ACTUAL37_FAILED_PRECONDITION_LOCATION_BEFORE_ANY_TOOL_ZERO_TOKENS_NOT_CASH_ZERO',exact_failure=failure,actual_bindings=priorbindings,new_model_calls=0,successful_media_repeated=0))
 sources={str(q):sha(q) for q in list(ROOT.glob('*.py'))+[ROOT/'PROTOCOL.md']};assert len(list(ROOT.glob('*.py')))==10
 save(ROOT/'execution_code_binding.json',dict(sources=sources,actual_prior_bindings=priorbindings,manual_user_authorization_sha256=sha(auth_path),old37_whole_REJECT_preserved=True,new_root_gate_required=True,new_model_calls=0))
 a.mkdir();(a/'text').mkdir();idx=project(read(old/'index.json'),old,a);literal=project(read(old/'literal_execution_parameters.json'),old,a);parts=idx['text_fragments']
 # New text/output/ACK paths only; scientific media aliases and clocks stay original.
 from prompt import piece,main_body,header_body,native_body,proposal_body
 science=(old/'science_verbatim_program_only.txt').read_bytes();put(a/'science_verbatim_program_only.txt',science)
 headers=[p for p in parts if p['kind']=='header'];partproof=[]
 for part in parts:
  w=next((w for w in idx['windows'] if w['job_index']==part['job_index']),None);l=next((l for l in literal if l['job_index']==part['job_index']),None)
  body=main_body(science.decode(),headers,38,[21,22,23]) if w is None else header_body(w,[p for p in parts if p['job_index']==w['job_index'] and p['kind']=='native_index'],l) if part['kind']=='header' else proposal_body(w) if part['kind']=='proposal_schema' else native_body(w,part['before_group'],l)
  ack=project(read(next(p for p in read(old/'index.json')['text_fragments'] if p['part_id']==part['part_id'])['expected_ACK_path']),old,a);ack['marker']='MANUAL38_'+uuid.uuid4().hex
  payload=piece(body,ack,part['ack_path']).encode();assert len(payload)<30000 and payload.endswith(b'\n') and b'\r' not in payload and len(payload.splitlines())<=450 and max(map(len,payload.decode().splitlines()))<=1000
  save(part['expected_ACK_path'],ack);put(part['path'],payload)
  part.update(input_sha256=sha(part['path']),payload_bytes=len(payload),exact_Go_LF_lines=len(payload.split(b'\n')),Python_splitlines=len(payload.splitlines()),max_line_characters=max(map(len,payload.decode().splitlines())),expected_ACK_sha256=sha(part['expected_ACK_path']))
  partproof.append(dict(part_id=part['part_id'],bytes=len(payload),sha256=sha(part['path'])))
 save(a/'index.json',idx);save(a/'literal_execution_parameters.json',literal)
 for n in ('original_v3_prompt35.txt','original_v3_prompt36.txt','prepared_original_pixel_clock_checks.json'):
  put(a/n,(old/n).read_bytes())
 smap=project(read(old/'scientific_text_map.json'),old,a);save(a/'scientific_text_map.json',smap);save(ROOT/'scientific_text_map.json',smap)
 put(a/'short_prompt.txt',(old/'short_prompt.txt').read_bytes().replace(str(old).encode(),str(a).encode()))
 reads=[p['path'] for p in parts]+[x for w in idx['windows'] for x in [w['clip_path'],*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])]];outputs=[p['ack_path'] for p in parts]+[x for w in idx['windows'] for x in [*(g['output_path'] for g in w['groups']),w['proposal_path']]];selfreads=[x for w in idx['windows'] for x in [*(g['output_path'] for g in w['groups']),w['proposal_path']]]
 assert len(expected_core(idx))==308 and len(scientific_core(idx))==270 and not any(Path(p).exists() for p in outputs)
 inputs=dict(oldfr['inputs']);inputs.update(sources);inputs.update(priorbindings)
 for q in [ROOT/'execution_code_binding.json',ROOT/'prior37_zero_tool_location_error.json',ROOT/'scientific_text_map.json',*(q for q in a.rglob('*') if q.is_file())]:inputs[str(q)]=sha(q)
 fr=dict(inputs=inputs,automatic_retry=False,read_whitelist=reads,self_read_whitelist=selfreads,write_whitelist=outputs,fixed_job_indices=[21,22,23],CLI_before=37,CLI_after=38,timeout_seconds=7200,model='gemini-3.8-flash-high',global_cap=38,no39=True,expected_core_tool_calls=308,scientific_media_fact_tool_calls=270,fragment_count=19,core_per_window=102,scope_core_counts=[104,206,308],main_instruction_path=idx['main_instruction_path'],protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),source_binding_sha256=sha(ROOT/'execution_code_binding.json'),old37_zero_tools_location_FAILURE_preserved=True,prior38_not_started=True,manual_user_authorization_path=str(auth_path),manual_user_authorization_sha256=sha(auth_path),new_manual_retry_root_gate_required=True)
 save(a/'freeze.json',fr)
 AST=[]
 for q in ROOT.glob('*.py'):ast.parse(q.read_text(encoding='utf-8'));AST.append(dict(path=str(q),sha256=sha(q),bytes=q.stat().st_size))
 short=(a/'short_prompt.txt').read_text(encoding='utf-8');units=len(subprocess.list2cmdline(command(38,short)).encode('utf-16-le'))//2+1;assert units<1024
 for p in parts:assert read(p['expected_ACK_path'])['marker'] not in short and read(p['expected_ACK_path'])['marker'] not in (a/'index.json').read_text(encoding='utf-8')
 save(ROOT/'plan.json',dict(status='PREPARED_MANUAL38_PENDING_NEW_ROOT_GATE_NOT_STARTED',CLI=38,fixed_job_indices=[21,22,23],global_cap=38,no39=True,automatic_retry=False,timeout_seconds=7200,core=308,scope_cores=[104,206,308],parts=19,new_model_calls=0,new_PNG_decode=0,new_video_decode=0,IP_recovery_verified=False))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_MANUAL38_AST_TEXT_PATH_PROJECTION_SHA_PREP_ONLY_NO_MODEL',AST=AST,source_binding_sha256=sha(ROOT/'execution_code_binding.json'),freeze_sha256=sha(a/'freeze.json'),input_count=len(inputs),parts=partproof,max_text_bytes=max(p['bytes'] for p in partproof),argv_utf16_units_including_NUL=units,prior37_exact_failure=failure,old24_CPU_receipt_sha256=sha(OLD/'independent_CPU_negative_acceptance.json'),old68_CPU_receipt_sha256=sha(BASE/'engineering_CLI36_37_split_fragment_v8v5/independent_CPU_negative_acceptance.json'),old51_and24_and68_repeated=False,new_PNG_decode=0,new_model_calls=0,new_root_gate_required=True))
 print(json.dumps(dict(source_binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),freeze_sha256=sha(a/'freeze.json'),manual_authorization_sha256=sha(auth_path),max_text_bytes=max(p['bytes'] for p in partproof),argv_units=units,input_count=len(inputs))))
if __name__=='__main__':main()
