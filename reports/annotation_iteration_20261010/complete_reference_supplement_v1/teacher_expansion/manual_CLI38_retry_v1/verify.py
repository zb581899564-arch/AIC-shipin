"""Necessary manual38 path/auth CPU proof; no prior schema/image reruns."""
from common import ROOT,BASE,read,sha,save,key,expected_core,scientific_core,bootstrap_metadata
from pathlib import Path
import ast,json,copy,hashlib,subprocess
from unittest.mock import patch
import launch
from prepare import project
OLD=BASE/'prospective_CLI37_schema_local_v2'

def new_gate_cases(auth):
 cases=[];gate=dict(CLI=38,global_cap=38,no39=True,automatic_retry=False,fixed_job_indices=[21,22,23],timeout_seconds=7200,manual_user_authorization=dict(path=str(BASE.parent/'manual_CLI38_user_retry_authorization_v1.json'),sha256='MEMORY_AUTH_SHA'))
 def check(name,document,g,want):
  accepted=True
  try:
   with patch.object(launch,'read',return_value=document),patch.object(launch,'sha',return_value='MEMORY_AUTH_SHA'),patch.object(launch,'verify_prior37_failure',return_value=auth['prior37_exact_failure']):launch.verify_manual38_admission(g)
  except (AssertionError,KeyError):accepted=False
  assert accepted==want,(name,accepted);cases.append(dict(name=name,accepted=accepted,memory_only=True,new_model_calls=0))
 # Strip actual hashes only in memory to exercise the typed/manual gate.
 doc=copy.deepcopy(auth);doc['prior37_actual_bindings']={}
 check('one_manual38_typed_authorization_positive',doc,gate,True)
 for name,changes in [('old37_status_not_manual38_STOP',dict(status='ROOT_APPROVED_START_SCHEMA_LOCAL_FRESH37_FIXED21_23_AFTER_ROOT20_RECOVERY')),('missing_exact_human_quote_STOP',dict(user_quote_exact='OTHER')),('automatic_retry_STOP',dict(automatic_retry=True)),('wrong_scope_STOP',dict(fixed_job_indices=[19,20])),('no39_false_STOP',dict(no39=False)),('cap39_STOP',dict(global_cap=39)),('time_expansion_STOP',dict(timeout_seconds=7201)),('claim_IP_verified_STOP',dict(IP_recovery_verified=True)),('cash_zero_STOP',dict(cash_cost=0))]:check(name,dict(doc,**changes),gate,False)
 check('gate_wrong_counter_STOP',doc,dict(gate,CLI=37),False)
 return cases

def prior37_cases():
 prior=launch.PRIOR37;raw=(prior/'stream.jsonl').read_bytes();rows=[json.loads(x) for x in raw.splitlines()];ledger=BASE/'global_CLI_ledger.jsonl';ledgertext=ledger.read_text(encoding='utf-8');cases=[];original_bytes=Path.read_bytes;original_text=Path.read_text;original_read=launch.read;original_sha=launch.sha
 def check(name,changed_rows,terminal_change=None,ledger_override=None,output_exists=False,want=False):
  rr=(b'\n'.join(json.dumps(x,ensure_ascii=False).encode() for x in changed_rows)+b'\n');terminal=read(prior/'terminal.json');terminal.update(terminal_change or {})
  def fake_bytes(p):return rr if p==prior/'stream.jsonl' else original_bytes(p)
  def fake_text(p,*args,**kwargs):return ledger_override if p==ledger and ledger_override is not None else original_text(p,*args,**kwargs)
  def fake_read(p):
   if Path(p)==prior/'terminal.json':return terminal
   if Path(p)==prior/'freeze.json' and output_exists:return dict(write_whitelist=[str(ROOT/'launch.py')])
   return original_read(p)
  accepted=True
  try:
   with patch.object(Path,'read_bytes',fake_bytes),patch.object(Path,'read_text',fake_text),patch.object(launch,'read',side_effect=fake_read),patch.object(launch,'sha',side_effect=lambda p:terminal['stream_sha256'] if Path(p)==prior/'stream.jsonl' else original_sha(p)):launch.verify_prior37_failure()
  except (AssertionError,KeyError):accepted=False
  assert accepted==want,(name,accepted);cases.append(dict(name=name,accepted=accepted,memory_only=True,new_model_calls=0))
 check('actual_location_zero_tool_shape_positive',rows,want=True)
 changed=copy.deepcopy(rows);changed[-1]['result']['error']='OTHER_ERROR';check('different_error_type_STOP',changed)
 changed=copy.deepcopy(rows);changed[-1]['result']['usage']['input_tokens']=1;check('nonzero_tokens_STOP',changed)
 changed=copy.deepcopy(rows);changed.insert(-1,dict(step_update=dict(step_type='tool',state='ACTIVE',tool_name='view_file',step_index=2)));check('any_prior_tool_even_ACTIVE_STOP',changed)
 check('prior_output_exists_STOP',rows,output_exists=True)
 check('prior_terminal_not_created_STOP',rows,terminal_change=dict(child_process_created=False))
 terminalrow=next(x for x in ledgertext.splitlines() if json.loads(x)['global_count']==37 and json.loads(x)['event']=='TERMINAL');check('duplicate_TERMINAL37_STOP',rows,ledger_override=ledgertext+terminalrow+'\n')
 return cases

def same_function(oldtext,newtext,name):
 of=next(n for n in ast.parse(oldtext).body if isinstance(n,ast.FunctionDef) and n.name==name);nf=next(n for n in ast.parse(newtext).body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.get_source_segment(oldtext,of)==ast.get_source_segment(newtext,nf),name
 return hashlib.sha256(ast.get_source_segment(newtext,nf).encode()).hexdigest()

def main():
 a=ROOT/'call38';old=OLD/'call37';binding=read(ROOT/'execution_code_binding.json');fr=read(a/'freeze.json');idx=read(a/'index.json');literal=read(a/'literal_execution_parameters.json')
 assert len(list(ROOT.glob('*.py')))==10
 for p,h in binding['sources'].items():assert sha(p)==h;ast.parse(Path(p).read_text(encoding='utf-8')) if p.endswith('.py') else None
 for p,h in binding['actual_prior_bindings'].items():assert sha(p)==h
 for p,h in fr['inputs'].items():assert sha(p)==h
 assert fr['CLI_before']==37 and fr['CLI_after']==fr['global_cap']==38 and fr['fixed_job_indices']==[21,22,23] and fr['automatic_retry'] is False and fr['no39'] is True and fr['timeout_seconds']==7200
 oldidx=read(old/'index.json');assert idx['windows']==project(oldidx['windows'],old,a) and literal==project(read(old/'literal_execution_parameters.json'),old,a)
 science=(a/'science_verbatim_program_only.txt').read_bytes();assert science==(old/'science_verbatim_program_only.txt').read_bytes()
 for name in ('engine.py','common.py'):assert (ROOT/name).read_bytes()==(OLD/name).read_bytes()
 assert (ROOT/'audit.py').read_text(encoding='utf-8')==(OLD/'audit.py').read_text(encoding='utf-8').replace('global_cap=37','global_cap=38').replace('stops before37','stops, no39')
 guardproof={}
 for file,names in [('launch.py',['verify_w20_recovery']),('observer.py',['fact_payload_guard','proposal_path_guard','request_owned_stop','schema_scan','seal_observed_scopes']),('prompt.py',['scientific_text','piece','header_body','native_body','native_schema_notice','proposal_example','proposal_body'])]:
  for name in names:guardproof[file+':'+name]=same_function((OLD/file).read_text(encoding='utf-8'),(ROOT/file).read_text(encoding='utf-8'),name)
 from prompt import piece,main_body,header_body,native_body,proposal_body
 headers=[p for p in idx['text_fragments'] if p['kind']=='header'];short=(a/'short_prompt.txt').read_text(encoding='utf-8');white={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']};parts=[]
 for p in idx['text_fragments']:
  w=next((w for w in idx['windows'] if w['job_index']==p['job_index']),None);l=next((l for l in literal if l['job_index']==p['job_index']),None);ack=read(p['expected_ACK_path'])
  body=main_body(science.decode(),headers,38,[21,22,23]) if w is None else header_body(w,[q for q in idx['text_fragments'] if q['job_index']==w['job_index'] and q['kind']=='native_index'],l) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],l)
  b=Path(p['path']).read_bytes();assert b==piece(body,ack,p['ack_path']).encode() and len(b)<30000 and bootstrap_metadata(b,f"{len(b)} bytes, {len(b.split(bytes([10])))} lines") and len(b.splitlines())<=450 and max(map(len,b.decode().splitlines()))<=1000
  assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8') and key(p['expected_ACK_path']) not in white
  parts.append(dict(part_id=p['part_id'],bytes=len(b),sha256=sha(p['path']),full_text_regenerated_exact=True))
 assert len(parts)==19 and len(expected_core(idx))==308 and len(scientific_core(idx))==270 and [len(expected_core(idx,w['job_index'])) for w in idx['windows']]==[104,206,308]
 assert not any(Path(p).exists() for p in fr['write_whitelist']) and not(a/'request.json').exists() and not(ROOT/'root_start_admission.json').exists()
 units=len(subprocess.list2cmdline(launch.command(38,short)).encode('utf-16-le'))//2+1;assert units<1024
 auth=read(BASE.parent/'manual_CLI38_user_retry_authorization_v1.json');cases=new_gate_cases(auth)+prior37_cases()
 save(ROOT/'independent_CPU_negative_acceptance.json',dict(status='PASS_NECESSARY_MANUAL38_PATH_AUTH_ZERO_TOOL_PRIOR_FAILURE_CPU_NO_MODEL_PENDING_ROOT_GATE',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),new_cases=cases,guard_functions_byte_exact=guardproof,parts=parts,argv_units=units,core=308,scope_cores=[104,206,308],prior24_receipt_sha256=sha(OLD/'independent_CPU_negative_acceptance.json'),prior68_receipt_sha256=sha(BASE/'engineering_CLI36_37_split_fragment_v8v5/independent_CPU_negative_acceptance.json'),prior51_24_68_repeated=False,new_PNG_decode=0,new_processor_calls=0,new_model_calls=0,IP_recovery_verified=False))
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),new_cases=len(cases),max_text_bytes=max(p['bytes'] for p in parts),argv_units=units,gate_present=False,new_model_calls=0)))
if __name__=='__main__':main()
