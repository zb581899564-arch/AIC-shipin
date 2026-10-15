"""New memory-only ACK timing counterexample. No generated teacher files, model, decode or transport."""
from pathlib import Path
import sys,json,copy,hashlib,datetime
from unittest.mock import patch
R=Path(r"G:\ai\AIC视频\reports\annotation_iteration_20261010\complete_reference_supplement_v1\teacher_expansion\engineering_CLI36_37_split_fragment_v8v5")
sys.path.insert(0,str(R))
import engine,common,audit
from functools import lru_cache
common.key=lru_cache(None)(common.key);engine.key=common.key;audit.key=common.key
A=R/'call36';index=common.read(A/'index.json');freeze=common.read(A/'freeze.json')
docs={};native=set();effective=set()
for part in index['text_fragments']:docs[common.key(part['ack_path'])]=common.read(part['expected_ACK_path'])
for w in index['windows']:
 effective.update(common.key(f['path']) for f in w['student_previews'])
 for g in w['groups']:
  native.update(common.key(f['path']) for f in g['frames'])
  docs[common.key(g['output_path'])]={'group':g['group'],'items':[{'slot':s,'subject':'memory fixture','composition':'memory fixture','subtitle_visible':False,'subtitle_text':None,'visible_fact':'memory fixture'} for s in range(4)]}
 docs[common.key(w['proposal_path'])]={'segments':[{'decision':'NO','start_seconds':0,'end_seconds':w['domain_local_seconds'][1],'reason':'memory fixture only','fact_support':[],'start_uncertainty_range_seconds':[0,0],'end_uncertainty_range_seconds':[w['domain_local_seconds'][1]]*2}],'events':[],'student_visibility':{},'limitations':[]}
fakefreeze=copy.deepcopy(freeze);fakefreeze['inputs']={}
original_read=common.read;original_sha=common.sha;original_exists=Path.exists
canonical={common.key(p):p for p in freeze['read_whitelist']+freeze['self_read_whitelist']+freeze['write_whitelist']}
parts={common.key(p['path']):p for p in index['text_fragments']}
def memory_read(p):
 k=common.key(p)
 if k==common.key(A/'freeze.json'):return fakefreeze
 return docs[k] if k in docs else original_read(p)
def memory_sha(p):
 k=common.key(p)
 return hashlib.sha256(json.dumps(docs[k],sort_keys=True).encode()).hexdigest() if k in docs else original_sha(p)
def memory_exists(p):return common.key(p) in docs or original_exists(p)
rows=[];step=0;batch=0
for name,p in common.expected_core(index):
 if p in native or p in effective:
  planning=batch==0;batch=(batch+1)%4
 else:planning=True
 if planning:
  step+=1;rows.append({'step_update':{'step_index':step,'step_type':'agent_response','state':'DONE'}})
 step+=1;parameters={'AbsolutePath' if name=='view_file' else 'TargetFile':canonical[p]}
 output='read' if name=='view_file' else 'written'
 if p in parts:
  payload=Path(parts[p]['path']).read_bytes();output=f'{len(payload)} bytes, {len(payload.split(bytes([10])))} lines'
 for state in ('ACTIVE','DONE'):rows.append({'step_update':{'step_index':step,'step_type':'tool','state':state,'tool_name':name,'tool_info':{'parameters':copy.deepcopy(parameters),'output':output}}})
rows.append({'event':'result','result':{'status':'SUCCESS'}})
def encoded(v):return b'\n'.join(json.dumps(x).encode() for x in v)+b'\n'
with patch.object(engine,'read',side_effect=memory_read),patch.object(common,'read',side_effect=memory_read),patch.object(engine,'sha',side_effect=memory_sha),patch.object(Path,'exists',memory_exists):
 good=engine.inspect(A,encoded(rows))
 changed=copy.deepcopy(rows);changed[:6]=[changed[i] for i in (0,1,3,4,2,5)]
 bad=engine.inspect(A,encoded(changed))
 eligibility=audit.continuation_decision([{'status':'PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC','job_index':x} for x in (19,20)],{'child_process_created':True,'exit_code':0,'stop_reason':None},bad,[],[],[],[])
result={'status':'COUNTEREXAMPLE_ACK_ACTIVE_BEFORE_FRAGMENT_DONE_ACCEPTED' if bad['teacher_task_completed'] else 'ACK_ORDER_COUNTEREXAMPLE_REJECTED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'synthetic_memory_only':True,'actual_teacher_outputs_written':0,'actual_model_calls':0,'existing_CPU_tests_repeated':False,'execution_binding_sha256':original_sha(R/'execution_code_binding.json'),'engine_sha256':original_sha(R/'engine.py'),'valid_control':{'teacher_task_completed':good['teacher_task_completed'],'issues':good['tool_issues']},'counterexample':{'first_raw_updates':changed[:6],'teacher_task_completed':bad['teacher_task_completed'],'bootstrap_complete':bad['bootstrap_successful_complete'],'ACK_complete':bad['bootstrap_ack_complete'],'issues':bad['tool_issues'],'window_statuses':[w['status'] for w in bad['windows']],'hypothetical_whole_eligibility_with_valid_scopes':eligibility},'expected_result':'REJECT: main view DONE must precede main ACK write ACTIVE','actual_ACK_barrier':bad['text_fragment_proofs'][0].get('text_ACK_barrier')}
assert good['teacher_task_completed'] and not bad['teacher_task_completed'] and not eligibility['eligible'],result
O=Path(r'G:\ai\AIC视频\reports\annotation_iteration_20261010\complete_reference_supplement_v1\plan_review\v8v5_ack_order_memory_regression_v1.json')
# This new plan_review result is the only filesystem mutation.
with O.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(O),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'status':result['status'],'counterexample_accepted':bad['teacher_task_completed'],'whole_eligible':eligibility['eligible']},ensure_ascii=False))
