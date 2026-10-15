"""New two-single-window19-part preparation; original media/science exact reuse."""
from common import ROOT,BASE,read,sha,save,expected_core,scientific_core
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,json,uuid,subprocess
OLD=BASE/'manual_CLI38_retry_v1'
def put(p,b):
 with Path(p).open('xb') as f:f.write(b)
def project(v,old,new):
 if isinstance(v,str):return v.replace(str(old),str(new))
 if isinstance(v,list):return [project(x,old,new) for x in v]
 if isinstance(v,dict):return {k:project(x,old,new) for k,x in v.items()}
 return v

def main():
 assert not(ROOT/'plan.json').exists() and not any(BASE.rglob('call39/request.json')) and not any(BASE.rglob('call40/request.json'))
 old=OLD/'call38';oldfr=read(old/'freeze.json');oldidx=read(old/'index.json');oldliteral=read(old/'literal_execution_parameters.json')
 for p,h in oldfr['inputs'].items():assert sha(p)==h
 assert read(old/'audit.json')['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and read(old/'terminal.json')['stop_reason']=='OWNED_SCHEMA_OR_RAW_STOP_NO_RETRY'
 assert sha(old/'stream.jsonl')==read(old/'terminal.json')['stream_sha256']
 assert read(old/'w21_completed_scope_audit.json')['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
 ledger=BASE/'global_CLI_ledger.jsonl';rows=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()];terms=[x for x in rows if x['global_count']==38 and x['event']=='TERMINAL'];assert max(x['global_count'] for x in rows)==38 and len(terms)==1 and terms[0]['raw_sha256']==sha(old/'stream.jsonl')
 put(ROOT/'actual_global38_ledger_prefix.jsonl',ledger.read_bytes())
 prior=[*(old/n for n in ('index.json','freeze.json','request.json','terminal.json','stream.jsonl','stderr.txt','audit.json','actual_terminal_cost.json','w21_completed_scope_audit.json','owned_stop_request.json','first_schema_or_raw_failure_prefix.jsonl','first_failed_fact_original_bytes.json')),*(OLD/n for n in ('execution_code_binding.json','dry_run_acceptance.json','independent_CPU_negative_acceptance.json','root_start_admission.json','stopped.json')),BASE/'prospective_CLI37_schema_local_v2/independent_CPU_negative_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v5/independent_CPU_negative_acceptance.json',ROOT/'actual_global38_ledger_prefix.jsonl']
 wrapper=BASE.parent/'21_cjibt_w16_lawful_observation_completion_manual38_v1.json'
 if wrapper.exists():prior.append(wrapper)
 bindings={str(p):sha(p) for p in prior}
 from launch import USER_STATUS,USER_QUOTE,command
 auth=BASE.parent/'schema_recovery_22_23_user_authorization_v1.json'
 save(auth,dict(status=USER_STATUS,utc=datetime.now(timezone.utc).isoformat(),user_quote_exact=USER_QUOTE,authorization_source='CURRENT_USER_EXPLICIT_FORMAT_REPAIR_AND_REMAINING_TWO_RELAYED_BY_ROOT',routes={'39':[22],'40':[23]},global_cap=40,no41=True,automatic_retry=False,timeout_seconds_each=3600,ROOT_separate_gate_each_call_required=True,previous39_natural_terminal_and_independent_immutable_scope_required_before40=True,prior38_actual_bindings=bindings,old38_REJECT_STOP_costs_and21_accepted_preserved=True,new_model_calls=0,scope='TEACHER_ENGINEERING_PREPARATION_ONLY_ROOT_OWNS_TRAINING_GATES',cash_cost='UNKNOWN_NOT_ZERO'))
 bindings[str(auth)]=sha(auth)
 sources={str(p):sha(p) for p in list(ROOT.glob('*.py'))+[ROOT/'PROTOCOL.md']};assert len(list(ROOT.glob('*.py')))==10
 save(ROOT/'execution_code_binding.json',dict(sources=sources,actual_prior_bindings=bindings,user_authorization_sha256=sha(auth),old38_failure_preserved=True,existing21_preserved=True,new_model_calls=0))
 from prompt import piece,main_body,header_body,native_body,proposal_body
 science=(old/'science_verbatim_program_only.txt').read_bytes();routes=[];freezes=[]
 for number,job in ((39,22),(40,23)):
  a=ROOT/f'call{number}';a.mkdir();(a/'text').mkdir();w=project(copy.deepcopy(next(w for w in oldidx['windows'] if w['job_index']==job)),old,a);l=project(copy.deepcopy(next(l for l in oldliteral if l['job_index']==job)),old,a)
  parts=[]
  def part(pid,kind,group=None):
   p=dict(part_id=pid,kind=kind,job_index=None if kind=='main' else job,path=str(a/'text'/f'{pid}.txt'),ack_path=str(a/f'{pid}_ACK.json'),expected_ACK_path=str(a/'text'/f'{pid}_expected_ACK.json'),insertion_point='MAIN' if kind=='main' else 'WINDOW_HEADER' if kind=='header' else 'AFTER_EFFECTIVE8_BEFORE_PROPOSAL' if kind=='proposal_schema' else f'GROUP_{group:02d}_BEFORE_NATIVE',before_group=group,before_native_frame_id=f'F{group*4:02d}' if group is not None else None);parts.append(p);return p
  mainp=part('main','main');header=part(f'w{job}_header','header');w['header_fragment_id']=header['part_id'];w['native_fragment_ids']=[part(f'w{job}_group{g:02d}_schema','native_index',g)['part_id'] for g in range(16)];pp=part(f'w{job}_proposal_schema','proposal_schema');w['proposal_fragment_id']=pp['part_id'];w['proposal_template_path']=pp['path']
  idx=dict(index_path=str(a/'index.json'),windows=[w],text_fragments=parts,main_fragment_id='main',bootstrap_instruction_path=mainp['path'],bootstrap_ack_path=mainp['ack_path'],bootstrap_ack_expected_path=mainp['expected_ACK_path'],main_instruction_path=mainp['path'],model_identity_forbidden=True,original_science_unchanged=True,program_only_index_not_teacher_whitelisted=True,core_per_window=126,scope_core_counts=[128],scientific_source_plan_unchanged=True,each_native_group_has_one_schema_fragment=True)
  for p in parts:
   body=main_body(science.decode(),[header],number,[job]) if p['kind']=='main' else header_body(w,[p for p in parts if p['kind']=='native_index'],l) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],l)
   group=p['before_group'];ack=dict(marker=f'SINGLE{number}_'+uuid.uuid4().hex,part_id=p['part_id'],fixed_job_indices=[job],group_indices=[group] if group is not None else list(range(16)) if p['kind']=='header' else [],frame_count=dict(native=4 if group is not None else 64 if p['kind'] in ('main','header') else 0,effective=8 if group is None else 0),route_anchor=dict(first_native=w['groups'][group]['frames'][0]['path'],last_native=w['groups'][group]['frames'][-1]['path'],fact_output=w['groups'][group]['output_path']) if group is not None else dict(proposal=w['proposal_path']))
   b=piece(body,ack,p['ack_path']).encode();assert len(b)<30000 and b.endswith(b'\n') and b'\r' not in b and len(b.splitlines())<=450 and max(map(len,b.decode().splitlines()))<=1000
   save(p['expected_ACK_path'],ack);put(p['path'],b);p.update(input_sha256=sha(p['path']),payload_bytes=len(b),exact_Go_LF_lines=len(b.split(b'\n')),Python_splitlines=len(b.splitlines()),max_line_characters=max(map(len,b.decode().splitlines())),expected_ACK_sha256=sha(p['expected_ACK_path']))
  assert len(parts)==19 and len(expected_core(idx))==128 and len(scientific_core(idx))==90
  save(a/'index.json',idx);save(a/'literal_execution_parameters.json',[l]);put(a/'science_verbatim_program_only.txt',science)
  for n in ('original_v3_prompt35.txt','original_v3_prompt36.txt','prepared_original_pixel_clock_checks.json'):put(a/n,(old/n).read_bytes())
  save(a/'scientific_text_map.json',project(read(old/'scientific_text_map.json'),old,a))
  short=f"First view_file the ENTIRE file at AbsolutePath {mainp['path']} once, no range. Follow its full instructions and single-window group routes. Immediately write each text tail ACK. Any ERROR/missing/invalid schema STOP, no retry. Only view_file/write_to_file."
  put(a/'short_prompt.txt',short.encode());assert all(read(p['expected_ACK_path'])['marker'] not in short and read(p['expected_ACK_path'])['marker'] not in (a/'index.json').read_text(encoding='utf-8') for p in parts)
  reads=[p['path'] for p in parts]+[w['clip_path'],*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])];writes=[p['ack_path'] for p in parts]+[*(g['output_path'] for g in w['groups']),w['proposal_path']];selfreads=[*(g['output_path'] for g in w['groups']),w['proposal_path']]
  inputs=dict(oldfr['inputs']);inputs.update(bindings);inputs.update(sources);inputs[str(ROOT/'execution_code_binding.json')]=sha(ROOT/'execution_code_binding.json')
  for p in a.rglob('*'):
   if p.is_file():inputs[str(p)]=sha(p)
  fr=dict(inputs=inputs,automatic_retry=False,read_whitelist=reads,self_read_whitelist=selfreads,write_whitelist=writes,fixed_job_indices=[job],CLI_before=number-1,CLI_after=number,timeout_seconds=3600,model='gemini-3.8-flash-high',global_cap=40,no41=True,expected_core_tool_calls=128,scientific_media_fact_tool_calls=90,fragment_count=19,core_per_window=126,scope_core_counts=[128],main_instruction_path=mainp['path'],protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),source_binding_sha256=sha(ROOT/'execution_code_binding.json'),user_authorization_sha256=sha(auth),old38_partial_failure_not_observation_transfer=True,new_ROOT_gate_per_call_required=True)
  assert not any(Path(p).exists() for p in writes);save(a/'freeze.json',fr);freezes.append(dict(path=str(a/'freeze.json'),sha256=sha(a/'freeze.json'),inputs=len(inputs)))
  units=len(subprocess.list2cmdline(command(number,short)).encode('utf-16-le'))//2+1;assert units<1024
  routes.append(dict(CLI=number,job=job,scope_core128=len(expected_core(idx)),window_core126=idx['core_per_window'],science90=len(scientific_core(idx)),parts19=len(parts),max_bytes=max(p['payload_bytes'] for p in parts),argv_units=units))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
 save(ROOT/'plan.json',dict(status='PREPARED_TWO_SEPARATELY_ROOT_GATED_SINGLE_WINDOWS_NO_START',routes=routes,global_cap=40,no41=True,automatic_retry=False,timeout_seconds_each=3600,old38_and21_preserved=True,new_model_calls=0,new_PNG_decode=0))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_NEW_SINGLE_GROUP_SCHEMA_TRANSPORT_AST_SHA_NO_MODEL_PENDING_ROOT',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),routes=routes,freezes=freezes,AST=AST,new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,old51_24_68_repeated=False))
 print(json.dumps(dict(binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_sha256=sha(ROOT/'dry_run_acceptance.json'),authorization_sha256=sha(auth),routes=routes)))
if __name__=='__main__':main()
