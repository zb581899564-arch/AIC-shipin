"""Independent CPU synthetic negatives only; no fake observations or API calls."""
from common import ROOT,BASE,read,sha,save,expected_core,key,bootstrap_metadata
from pathlib import Path
import ast,copy,json,subprocess
from unittest.mock import patch
import engine,audit

def negatives():
 results=[]
 good=[dict(status='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC',job_index=x) for x in (19,20)]
 terminal=dict(child_process_created=True,exit_code=0,stop_reason=None)
 whole=dict(errored_tool_attempts=[],unfinished_tool_attempts=[],tool_issues=[],reported_nonmedia_errors=[],actual_result_status='SUCCESS',actual_result_error=None)
 def case(name,expected,**change):
  v=dict(scopes=copy.deepcopy(good),terminal=copy.deepcopy(terminal),whole=copy.deepcopy(whole),post=[],drift=[],media_repeats=[],late_writes=[]);v.update(change)
  d=audit.continuation_decision(**v);assert d['eligible']==expected,(name,d);results.append(dict(name=name,eligible=d['eligible'],whole_success=d['whole_success'],issues=d['issues'],synthetic_memory_only=True))
 case('all_complete_natural_SUCCESS',True)
 nw=dict(whole,actual_result_status='ERROR',actual_result_error='request failed tcp wsasend connection forcibly closed')
 case('final_network_after_ALL_no_tools_keep_whole_REJECT_allow_fresh36',True,whole=nw,network_error_after_last_proposal=True)
 assert not audit.continuation_decision(good,terminal,nw,[],[],[],[],True)['whole_success']
 case('same_network_BEFORE_completion_STOP',False,whole=nw,network_error_after_last_proposal=True,pre_completion_error=True)
 case('early_SUCCESS_before_final_proposal_STOP',False,pre_completion_error=True)
 case('network_timing_unknown_STOP',False,whole=nw)
 case('401_after_completion_STOP',False,whole=dict(nw,actual_result_error='401 UNAUTHENTICATED'),network_error_after_last_proposal=True)
 case('media_ERROR_before_proposal_STOP',False,whole=dict(whole,errored_tool_attempts=[{'state':'ERROR','tool_name':'view_file'}]))
 case('outside_before_proposal_STOP',False,whole=dict(whole,tool_issues=[{'reason':'OUTSIDE_READ_WHITELIST_ATTEMPT'}]))
 case('outside_after_all_proposals_STOP_scopes_separate',False,whole=dict(nw,tool_issues=[{'reason':'OUTSIDE_READ_WHITELIST_ATTEMPT'}]),post=[{'tool_name':'view_file'}],network_error_after_last_proposal=True)
 case('any_tool_after_finalproposal_STOP',False,post=[{'tool_name':'view_file'}])
 case('repeated_media_STOP',False,media_repeats=[{'path':'synthetic'}])
 case('samebyte_output_rewrite_STOP',False,late_writes=[{'path':'synthetic'}])
 case('output_or_prefix_byte_drift_STOP',False,drift=[{'reason':'BYTE_DRIFT'}])
 case('missing_scope_STOP',False,scopes=[good[0],{'status':'MISSING_SCOPE'}])
 case('zero_scopes_STOP',False,scopes=[])
 case('bootstrap_failure_STOP',False,whole=dict(whole,tool_issues=[{'reason':'BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE'}]))
 case('network_after_incomplete_core_STOP',False,whole=dict(nw,tool_issues=[{'reason':'CORE_MEDIA_ORDER_OR_MISSING'}]),network_error_after_last_proposal=True)
 case('reported_error_message_body_STOP',False,whole=dict(nw,reported_nonmedia_errors=[{'body':'synthetic error'}]),network_error_after_last_proposal=True)
 case('unfinished_tool_STOP',False,whole=dict(whole,unfinished_tool_attempts=[{'state':'ACTIVE'}]))
 case('owned_timeout_STOP',False,terminal=dict(terminal,stop_reason='OWNED_TIMEOUT'),whole=nw,network_error_after_last_proposal=True)
 case('prespawn_failure_STOP',False,terminal=dict(terminal,child_process_created=False))
 # Real frozen text and exact metadata are compared CPU-only. Synthetic tool rows
 # exist only in memory; no stream.jsonl/ACK/facts/proposal is written.
 a=ROOT/'call35';idx=read(a/'index.json');fr=read(a/'freeze.json');payload=Path(idx['bootstrap_instruction_path']).read_bytes();expected=read(idx['bootstrap_ack_expected_path'])
 lines=len(payload.split(b'\n'));output=f'{len(payload)} bytes, {lines} lines';assert bootstrap_metadata(payload,output)
 for name,p,o in [('LF_minus1',payload,f'{len(payload)} bytes, {lines-1} lines'),('LF_plus1',payload,f'{len(payload)} bytes, {lines+1} lines'),('wrongbytes',payload,f'{len(payload)-1} bytes, {lines} lines'),('no_tailLF',payload[:-1],output),('CR_added',payload+b'\r',f'{len(payload)+1} bytes, {lines} lines'),('truncation',payload,output+' truncated')]:
  assert not bootstrap_metadata(p,o),name;results.append(dict(name=name,rejected=True,synthetic_memory_only=True))
 fixture_idx=copy.deepcopy(idx);fixture_idx['windows']=[];fixture_fr=copy.deepcopy(fr);fixture_fr['inputs']={}
 def rows(out=output,reverse=False,outside=False,error=False):
  tools=[('view_file',{'AbsolutePath':idx['bootstrap_instruction_path']},out),('write_to_file',{'TargetFile':idx['bootstrap_ack_path']},'written'),('view_file',{'AbsolutePath':idx['index_path']},'read')]
  if reverse:tools[0],tools[1]=tools[1],tools[0]
  if outside:tools[2]=('view_file',{'AbsolutePath':str(a/'NON_WHITELIST.txt')},'read')
  return b'\n'.join(json.dumps({'step_update':dict(step_index=i+1,step_type='tool',state='ERROR' if error and i==0 else 'DONE',tool_name=name,tool_info=dict(parameters=p,output=o))}).encode() for i,(name,p,o) in enumerate(tools))+b'\n'
 actual_ack=copy.deepcopy(expected)
 def fake_read(p):
  if key(p)==key(a/'index.json'):return fixture_idx
  if key(p)==key(a/'freeze.json'):return fixture_fr
  if key(p)==key(idx['bootstrap_ack_path']):return actual_ack
  return read(p)
 with patch.object(engine,'read',side_effect=fake_read):
  d=engine.inspect(a,rows());assert d['bootstrap_successful_complete'] and d['bootstrap_ack_complete'] and not d['tool_issues']
  for name,raw in [('tool_LF_minus1',rows(f'{len(payload)} bytes, {lines-1} lines')),('tool_wrong_first_second_order',rows(reverse=True)),('tool_outside_before',rows(outside=True)),('bootstrap_toolERROR',rows(error=True))]:
   d=engine.inspect(a,raw);assert d['tool_issues'],name;results.append(dict(name=name,rejected=True,issues=[x['reason'] for x in d['tool_issues']],synthetic_memory_only=True))
  actual_ack=dict(expected,marker='WRONG_TAIL_MARKER');d=engine.inspect(a,rows());assert not d['bootstrap_ack_complete'];results.append(dict(name='wrong_ACK_marker',rejected=True,synthetic_memory_only=True))
 return results

def main():
 plan=read(ROOT/'plan.json');bindings=read(ROOT/'execution_code_binding.json');assert len(list(ROOT.glob('*.py')))==10
 for p,s in bindings['sources'].items():assert sha(p)==s;ast.parse(Path(p).read_text(encoding='utf-8')) if p.endswith('.py') else None
 for p,s in bindings['actual_prior_bindings'].items():assert sha(p)==s
 from launch import command
 routes=[]
 for n,jobs in ((35,[19,20]),(36,[21,22,23])):
  a=ROOT/f'call{n}';fr=read(a/'freeze.json');idx=read(a/'index.json');literal=read(a/'literal_execution_parameters.json')
  assert fr['fixed_job_indices']==jobs and [w['job_index'] for w in idx['windows']]==jobs
  for p,s in fr['inputs'].items():assert sha(p)==s,(p,'SHA_DRIFT')
  old=read(BASE/f'engineering_alias_remainder_v4_bootstrap_file/call{n}/index.json')
  for ow,w,l in zip(old['windows'],idx['windows'],literal):
   projected=copy.deepcopy(ow)
   for g in projected['groups']:g['output_path']=g['output_path'].replace(str(BASE/f'engineering_alias_remainder_v4_bootstrap_file/call{n}'),str(a))
   projected['proposal_path']=projected['proposal_path'].replace(str(BASE/f'engineering_alias_remainder_v4_bootstrap_file/call{n}'),str(a));assert projected==w
   for g,lg in zip(w['groups'],l['native_groups']):assert lg['view_file']==[dict(AbsolutePath=f['path']) for f in g['frames']] and lg['write_to_file']==dict(TargetFile=g['output_path'])
   assert [p for batch in l['effective_preview_batches'] for p in batch]==[dict(AbsolutePath=f['path']) for f in w['student_previews']]
   assert l['clip_view_file']==dict(AbsolutePath=w['clip_path']) and l['proposal_write_to_file']==dict(TargetFile=w['proposal_path'])
  assert len(expected_core(idx))==(183 if n==35 else 273)
  assert not any(Path(p).exists() for p in fr['write_whitelist']) and not(a/'request.json').exists()
  body=Path(idx['bootstrap_instruction_path']).read_bytes();short=(a/'short_prompt.txt').read_text(encoding='utf-8');ack=read(idx['bootstrap_ack_expected_path'])
  assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8');assert body.decode().count(ack['marker'])==2
  assert key(idx['bootstrap_ack_expected_path']) not in {key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']}
  assert len(subprocess.list2cmdline(command(n,short)).encode('utf-16-le'))//2+1<1024
  routes.append(dict(CLI=n,jobs=jobs,core=len(expected_core(idx)),scope_cores=[len(expected_core(idx,w['job_index'])) for w in idx['windows']]))
 receipt=dict(status='PASS_INDEPENDENT_CPU_NEGATIVES_EXACT_BINDINGS_NO_MODEL_PENDING_ROOT',sources=bindings['sources'],routing=routes,negative_cases=negatives(),scope_helper_paths=[str(ROOT/'audit.py'),str(ROOT/'engine.py'),str(ROOT/'common.py')],actual_models_started=0,actual_requests35_36=0,new_video_decode=0,root_review_required=True,cash_cost='UNKNOWN_NOT_ZERO')
 save(ROOT/'independent_CPU_negative_acceptance.json',receipt)
 print(json.dumps(dict(status=receipt['status'],negative_count=len(receipt['negative_cases']),receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),routes=routes)))
if __name__=='__main__':main()
