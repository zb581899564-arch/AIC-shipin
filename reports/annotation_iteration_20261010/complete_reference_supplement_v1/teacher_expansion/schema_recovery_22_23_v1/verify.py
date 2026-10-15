"""Only new16group route/count and previous39 admission CPU cases; no old suites."""
from common import ROOT,BASE,read,sha,save,expected_core,scientific_core,bootstrap_metadata
from pathlib import Path
import ast,json,copy,hashlib,subprocess
from prepare import project
OLD=BASE/'manual_CLI38_retry_v1'

def previous39_cases():
 from launch import previous39_documents_guard
 t=dict(child_process_created=True,exit_code=0,stop_reason=None,launch_exception=None)
 whole=dict(status='PASS_WHOLE_ACTUAL_CLI_PENDING_ROOT_SEMANTIC',actual_result_status='SUCCESS',continuation_decision=dict(whole_success=True,eligible=True))
 scope=dict(status='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC',windows=[dict(window_id='MEMORY22',bound_rows=64)],tool_issues=[],additional_scope_issues=[],errored_tool_attempts=[],unfinished_tool_attempts=[],reported_nonmedia_errors=[])
 c=dict(status='ROOT_CONFIRMED_CLI39_NATURAL_SUCCESS_AND_IMMUTABLE_SCOPE',CLI=39,window_id='MEMORY22',ROOT_actual_scope_independently_verified=True);cases=[]
 def run(name,tt,ww,ss,cc,want):
  accepted=True
  try:previous39_documents_guard(tt,ww,ss,cc,'MEMORY22')
  except (AssertionError,KeyError):accepted=False
  assert accepted==want;cases.append(dict(name=name,accepted=accepted,memory_only=True))
 run('strict_natural39_scope_confirmation_positive',t,whole,scope,c,True)
 for name,updates in [('timeout39_blocks40',dict(stop_reason='OWNED_TIMEOUT_NO_RETRY')),('exitnonzero_blocks40',dict(exit_code=1)),('notspawned_blocks40',dict(child_process_created=False))]:run(name,dict(t,**updates),whole,scope,c,False)
 run('wholeERROR_blocks40',t,dict(whole,actual_result_status='ERROR'),scope,c,False)
 run('missingROOTactualverification_blocks40',t,whole,scope,dict(c,ROOT_actual_scope_independently_verified=False),False)
 run('scopeREJECT_blocks40',t,whole,dict(scope,status='REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY'),c,False)
 ss=copy.deepcopy(scope);ss['errored_tool_attempts']=[dict(memory=True)];run('mediaERROR_blocks40',t,whole,ss,c,False)
 return cases

def main():
 binding=read(ROOT/'execution_code_binding.json');assert len(list(ROOT.glob('*.py')))==10
 for p,h in binding['sources'].items():assert sha(p)==h;ast.parse(Path(p).read_text(encoding='utf-8')) if p.endswith('.py') else None
 for p,h in binding['actual_prior_bindings'].items():assert sha(p)==h
 assert (ROOT/'engine.py').read_bytes()==(OLD/'engine.py').read_bytes()
 # Exact scientific validators/observer guards retained; only expected engineering
 # sequence changes from4group fragments to one pergroup.
 proof={}
 for file,names in [('common.py',['fact_items','proposal_schema','scientific_core','bootstrap_metadata']),('launch.py',['verify_w20_recovery']),('observer.py',['fact_payload_guard','proposal_path_guard','request_owned_stop','schema_scan','seal_observed_scopes']),('prompt.py',['scientific_text','piece','proposal_example','proposal_body'])]:
  old=(OLD/file).read_text(encoding='utf-8');new=(ROOT/file).read_text(encoding='utf-8')
  for name in names:
   of=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name==name);nf=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name==name);ob=ast.get_source_segment(old,of);nb=ast.get_source_segment(new,nf);assert ob==nb;proof[file+':'+name]=hashlib.sha256(nb.encode()).hexdigest()
 from prompt import piece,main_body,header_body,native_body,proposal_body
 from launch import command
 checks=[];cases=previous39_cases()
 oldidx=read(OLD/'call38/index.json');oldlit=read(OLD/'call38/literal_execution_parameters.json')
 for number,job in ((39,22),(40,23)):
  a=ROOT/f'call{number}';fr=read(a/'freeze.json');idx=read(a/'index.json');w=idx['windows'][0];lit=read(a/'literal_execution_parameters.json');l=lit[0];parts=idx['text_fragments'];headers=[p for p in parts if p['kind']=='header']
  for p,h in fr['inputs'].items():assert sha(p)==h
  oldw=project(next(w for w in oldidx['windows'] if w['job_index']==job),OLD/'call38',a)
  ignored={'header_fragment_id','native_fragment_ids','proposal_fragment_id','proposal_template_path'};assert {k:v for k,v in oldw.items() if k not in ignored}=={k:v for k,v in w.items() if k not in ignored}
  assert lit==[project(next(l for l in oldlit if l['job_index']==job),OLD/'call38',a)]
  science=(a/'science_verbatim_program_only.txt').read_bytes();assert science==(OLD/'call38/science_verbatim_program_only.txt').read_bytes()
  seq=expected_core(idx);assert len(seq)==128 and len(scientific_core(idx))==90 and idx['core_per_window']==126 and len(parts)==19 and len(w['native_fragment_ids'])==16
  for g in w['groups']:
   p=next(p for p in parts if p['part_id']==w['native_fragment_ids'][g['group']]);at=seq.index(('view_file',str(Path(p['path']).resolve()).casefold()));chunk=seq[at:at+7]
   want=[('view_file',str(Path(p['path']).resolve()).casefold()),('write_to_file',str(Path(p['ack_path']).resolve()).casefold()),*[('view_file',str(Path(f['path']).resolve()).casefold()) for f in g['frames']],('write_to_file',str(Path(g['output_path']).resolve()).casefold())];assert chunk==want
   assert chunk[:1]+chunk[2:]!=want;cases.append(dict(name=f'CLI{number}_group{g["group"]:02d}_missing_ACK_rejected',passed=True,memory_only=True))
  short=(a/'short_prompt.txt').read_text(encoding='utf-8');white=set(fr['read_whitelist']+fr['self_read_whitelist'])
  for p in parts:
   body=main_body(science.decode(),headers,number,[job]) if p['kind']=='main' else header_body(w,[q for q in parts if q['kind']=='native_index'],l) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],l)
   ack=read(p['expected_ACK_path']);b=Path(p['path']).read_bytes();assert b==piece(body,ack,p['ack_path']).encode() and len(b)<30000 and bootstrap_metadata(b,f"{len(b)} bytes, {len(b.split(bytes([10])))} lines")
   assert p['expected_ACK_path'] not in white and ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8')
   if p['kind']=='native_index':assert p['before_group'] in range(16) and '禁止裸list' in body and len(ack['group_indices'])==1
  units=len(subprocess.list2cmdline(command(number,short)).encode('utf-16-le'))//2+1;assert units<1024
  assert not any(Path(p).exists() for p in fr['write_whitelist']) and not(a/'request.json').exists() and not(ROOT/f'root_start_admission_CLI{number}.json').exists()
  checks.append(dict(CLI=number,job=job,science=90,engineering=38,window=126,scope=128,parts=19,argv_units=units,freeze_sha256=sha(a/'freeze.json')))
 save(ROOT/'independent_CPU_negative_acceptance.json',dict(status='PASS_NECESSARY_SINGLE_GROUP_ROUTE_COUNT_PREVIOUS39_GUARD_NO_MODEL_PENDING_ROOT_GATES',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),new_cases=cases,routes=checks,byte_exact_scientific_guard_sources=proof,old51_24_68_repeated=False,prior24_sha256=sha(BASE/'prospective_CLI37_schema_local_v2/independent_CPU_negative_acceptance.json'),prior68_sha256=sha(BASE/'engineering_CLI36_37_split_fragment_v8v5/independent_CPU_negative_acceptance.json'),new_model_calls=0,new_RGB_decode=0,new_decoder_calls=0,new_processor_calls=0))
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),new_cases=len(cases),routes=checks)))
if __name__=='__main__':main()
