from common import ROOT,V5,BASE,read,sha,key,save
from datetime import datetime,timezone
import ast,json
def main():
 assert not(V5/'root_start_admission.json').exists() and not(V5/'registered.json').exists()
 binding=read(V5/'execution_code_binding.json')
 for p,s in {**binding['sources'],**binding['frozen_prior_inputs']}.items():assert sha(p)==s
 original=(ROOT/'audit.py').read_text(encoding='utf-8').split('\ndef completed_scope(')[0]+'\n'
 assert (V5/'original_engine.py').read_text(encoding='utf-8')==original
 fixed=original.replace('line_count=len(bootstrap_file.read_bytes().splitlines())','line_count=len(bootstrap_file.read_bytes().split(bytes([10])))').replace("bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().splitlines())","bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().split(bytes([10])))")
 assert (V5/'engine.py').read_text(encoding='utf-8')==fixed
 import engine,original_engine
 from pathlib import Path
 a=ROOT/'call35';idx=read(a/'index.json');p=Path(idx['bootstrap_instruction_path']);b=p.read_bytes();lines=len(b.split(bytes([10])));size=len(b)
 assert p.read_bytes().endswith(bytes([10])) and bytes([13]) not in b
 def tool(step,name,path,state='DONE',output='',extra=None):return dict(event='step_update',step_update=dict(step_index=step,state=state,step_type='tool',tool_name=name,tool_info=dict(parameters=({'AbsolutePath':path} if name=='view_file' else {'TargetFile':path})|(extra or {}),output=output)))
 def data(ls):return b'\n'.join(json.dumps(r).encode('utf-8') for r in ls)
 def check(meta,ackdoc=None,order='right',state='DONE',extra=None,mediaerror=False):
  origread=engine.read
  def virtual(path):return (ackdoc if ackdoc is not None else read(idx['bootstrap_ack_expected_path'])) if key(path)==key(idx['bootstrap_ack_path']) else origread(path)
  engine.read=virtual
  ts=[tool(1,'view_file',str(p),state,meta,extra),tool(2,'write_to_file',idx['bootstrap_ack_path']),tool(3,'view_file',idx['index_path'])]
  if order=='wrong':ts=[ts[0],ts[2],ts[1]]
  if mediaerror:ts.append(tool(4,'view_file',idx['windows'][0]['groups'][0]['frames'][0]['path'],'ERROR'))
  result=engine.inspect(a,data(ts));engine.read=origread;return result
 exact=check(f'{lines} lines, {size} bytes');assert exact['bootstrap_successful_complete'] and exact['bootstrap_ack_complete'] and not exact['teacher_task_completed']
 cases=[('minus1',check(f'{lines-1} lines, {size} bytes')),('plus1',check(f'{lines+1} lines, {size} bytes')),('wrongbytes',check(f'{lines} lines, {size-1} bytes')),('toolERROR',check(f'{lines} lines, {size} bytes',state='ERROR')),('range',check(f'{lines} lines, {size} bytes',extra={'StartLine':1})),('wrongACK',check(f'{lines} lines, {size} bytes',ackdoc={'marker':'WRONG'})),('wrongorder',check(f'{lines} lines, {size} bytes',order='wrong')),('mediaERROR',check(f'{lines} lines, {size} bytes',mediaerror=True))]
 for name,d in cases:
  assert not d['teacher_task_completed'],name
  if name not in ('wrongACK','wrongorder','mediaERROR'):assert not d['bootstrap_successful_complete'],name
  if name in ('wrongACK','wrongorder'):assert not d['bootstrap_ack_complete'],name
  if name=='mediaERROR':assert d['errored_tool_attempts'],name
 for n in (35,36):assert not(ROOT/f'call{n}/request.json').exists()
 AST=[]
 for p in V5.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p)))
 assert len(AST)==10
 assert max(json.loads(s)['global_count'] for s in(BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines())==34
 save(V5/'independent_preparation_acceptance.json',dict(status='PASS_INDEPENDENT_EXACT_LF_CPU_PREPARATION_NO_AGY',utc=datetime.now(timezone.utc).isoformat(),AST=AST,execution_binding_sha256=sha(V5/'execution_code_binding.json'),dry_run_sha256=sha(V5/'dry_run_acceptance.json'),all_prior_frozen_input_count=len(binding['frozen_prior_inputs']),exact_two_representation_source_substitutions_verified=True,in_memory_negative_cases=[n for n,_ in cases],no_plus_minus1_tolerance=True,synthetic_cases_not_actual_observation_evidence=True,original_actual34_terminal_not_yet_admitted=True,root_gate_absent=True,no35_36_started=True,no37=True,new_AGY_or_model_calls=0,new_video_decode=0,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(receipt_sha256=sha(V5/'independent_preparation_acceptance.json'),AST_count=len(AST),new_AGY_or_model_calls=0),ensure_ascii=False))
if __name__=='__main__':main()
