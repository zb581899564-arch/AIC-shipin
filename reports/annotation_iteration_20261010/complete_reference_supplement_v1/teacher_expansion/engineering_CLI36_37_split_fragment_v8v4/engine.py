"""Explicit actual text proofs + actual media order; no semantic/training inference."""
from common import ROOT,read,sha,key,expected_core,scientific_core,fact_items,proposal_schema,metadata_errors,bootstrap_metadata
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib

def response_before(rows,pos):
 if pos<0:return -1
 return max((i for i,r in enumerate(rows[:pos]) if r.get('step_update',{}).get('step_type')=='agent_response' and r['step_update'].get('state')=='DONE'),default=-1)

def image_batch(rows,view_steps):
 active={};done={};responses={}
 for t in view_steps:
  step=t['step_index'];active[step]=next((i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='ACTIVE'),-1)
  done[step]=next((i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='DONE'),-1)
  responses[step]=response_before(rows,active[step])
 identities={}
 for k in active:
  identities[k]=active[k]>=0 and done[k]>=0 and rows[active[k]]['step_update'].get('tool_name')==rows[done[k]]['step_update'].get('tool_name') and rows[active[k]]['step_update'].get('tool_info',{}).get('parameters')==rows[done[k]]['step_update'].get('tool_info',{}).get('parameters')
 forward=len(view_steps)==4 and all(0<=responses[k]<active[k]<done[k] and identities[k] for k in active)
 same=forward and len(set(responses.values()))==1
 return dict(ACTIVE_raw_positions=active,DONE_raw_positions=done,planning_response_DONE_raw_positions=responses,ACTIVE_DONE_literal_identity_equal=identities,all_ACTIVE_exist_and_forward=forward,all_four_in_same_response=same)

def four_image_barrier(rows,view_steps,write_step):
 batch=image_batch(rows,view_steps)
 write_active=next((i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==write_step['step_index'] and r['step_update'].get('state')=='ACTIVE'),-1)
 writer_response_pos=response_before(rows,write_active)
 good=batch['all_four_in_same_response'] and all(0<=p<writer_response_pos<write_active for p in batch['DONE_raw_positions'].values())
 return dict(native_ACTIVE_raw_positions=batch['ACTIVE_raw_positions'],native_planning_response_DONE_raw_positions=list(batch['planning_response_DONE_raw_positions'].values()),all_ACTIVE_exist_and_forward=batch['all_ACTIVE_exist_and_forward'],all_four_in_same_response=batch['all_four_in_same_response'],native_DONE_raw_positions=batch['DONE_raw_positions'],fact_write_ACTIVE_raw_position=write_active,fact_planning_response_DONE_raw_position=writer_response_pos,all_four_DONE_before_fact_planning_response=good)

def effective_barrier(rows,view_steps,proposal_step):
 batches=[image_batch(rows,view_steps[s:s+4]) for s in (0,4)]
 proposal_active=next((i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==proposal_step['step_index'] and r['step_update'].get('state')=='ACTIVE'),-1)
 proposal_response=response_before(rows,proposal_active)
 full=len(view_steps)==8 and all(b['all_four_in_same_response'] for b in batches)
 if full:
  r0=next(iter(batches[0]['planning_response_DONE_raw_positions'].values()));r1=next(iter(batches[1]['planning_response_DONE_raw_positions'].values()))
  full=r0<max(batches[0]['DONE_raw_positions'].values())<r1<min(batches[1]['ACTIVE_raw_positions'].values()) and max(batches[1]['DONE_raw_positions'].values())<proposal_response<proposal_active
 return dict(batches=batches,proposal_ACTIVE_raw_position=proposal_active,proposal_planning_response_DONE_raw_position=proposal_response,two_distinct_forward_four_image_batches_then_proposal=full)

def inspect(a,raw,stop_job=None,terminal=None):
 index=read(a/'index.json');fr=read(a/'freeze.json');issues=[]
 for p,s in fr['inputs'].items():
  if not Path(p).exists() or sha(p)!=s:issues.append(dict(reason='INPUT_SHA_DRIFT',path=p,job_index=None))
 rows=[]
 for line in raw.splitlines():
  try:rows.append(json.loads(line))
  except (json.JSONDecodeError,UnicodeDecodeError):break
 updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'];latest={t['step_index']:t for t in updates};done=[t for t in latest.values() if t.get('state')=='DONE'];errors=[t for t in updates if t.get('state')=='ERROR'];unfinished=[t for t in latest.values() if t.get('state') not in ('DONE','ERROR')]
 active=[]
 for w in index['windows']:
  active.append(w)
  if w['job_index']==stop_job:break
 activejobs={w['job_index'] for w in active};parts=[p for p in index['text_fragments'] if p['job_index'] is None or p['job_index'] in activejobs]
 part_by_path={key(p['path']):p for p in index['text_fragments']};header_keys={key(p['path']) for p in index['text_fragments'] if p['kind']=='header'}
 def info(t):
  p=t.get('tool_info',{}).get('parameters',{});return t.get('tool_name'),key(p.get('AbsolutePath') or p.get('TargetFile'))
 owners={}
 for w in index['windows']:
  for p in [w['clip_path'],w['proposal_path'],*(g['output_path'] for g in w['groups']),*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])]:owners[key(p)]=w['job_index']
 for p in index['text_fragments']:owners[key(p['path'])]=owners[key(p['ack_path'])]=p['job_index']
 reads={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']};writes={key(p) for p in fr['write_whitelist']}
 histories={};historical_state_issues=[];literal_reads=set(fr['read_whitelist']+fr['self_read_whitelist']);literal_writes=set(fr['write_whitelist'])
 for t in updates:
  name,p=info(t);job=owners.get(p);state=t.get('state');step=t['step_index'];history=histories.setdefault(step,[])
  if state=='ERROR':issues.append(dict(reason='ANY_RAW_TOOL_ERROR',step=step,path=p,job_index=job,actual_update=t))
  output=str(t.get('tool_info',{}).get('output','')).lower()
  if any(x in output for x in ('not found','cannot read','error reading','failed to','content truncated')):issues.append(dict(reason='ANY_RAW_TOOL_FAILURE_OR_TRUNCATION',step=step,path=p,job_index=job,actual_update=t))
  if name and name not in ('view_file','write_to_file'):issues.append(dict(reason='ANY_RAW_ILLEGAL_TOOL',step=step,job_index=job))
  if name=='view_file' and p and p not in reads:issues.append(dict(reason='ANY_RAW_OUTSIDE_READ',step=step,path=p,job_index=job))
  if name=='write_to_file' and p and p not in writes:issues.append(dict(reason='ANY_RAW_OUTSIDE_WRITE',step=step,path=p,job_index=job))
  parameters=t.get('tool_info',{}).get('parameters',{})
  if name=='view_file' and (set(parameters)!={'AbsolutePath'} or parameters.get('AbsolutePath') not in literal_reads):issues.append(dict(reason='ANY_RAW_VIEW_PARAMETERS_NOT_EXACT_LITERAL',step=step,actual_parameters=parameters,job_index=job))
  if name=='write_to_file' and (set(parameters)!={'TargetFile'} or parameters.get('TargetFile') not in literal_writes):issues.append(dict(reason='ANY_RAW_WRITE_PARAMETERS_NOT_EXACT_LITERAL',step=step,actual_parameters=parameters,job_index=job))
  if state not in ('ACTIVE','DONE','ERROR'):historical_state_issues.append(dict(reason='UNKNOWN_RAW_TOOL_STATE',step=step,actual_update=t,job_index=job))
  if history:
   previous=history[-1];prevname,prevpath=info(previous)
   if previous.get('state') in ('DONE','ERROR') and state!=previous.get('state'):historical_state_issues.append(dict(reason='RAW_TOOL_STATE_REGRESSION',step=step,actual_update=t,job_index=job))
   if previous.get('tool_name')!=t.get('tool_name') or previous.get('tool_info',{}).get('parameters')!=t.get('tool_info',{}).get('parameters'):historical_state_issues.append(dict(reason='RAW_TOOL_LITERAL_NAME_FULL_PARAMETERS_CONFLICT',step=step,job_index=job,earlier_tool_name=previous.get('tool_name'),earlier_parameters=previous.get('tool_info',{}).get('parameters'),actual_tool_name=t.get('tool_name'),actual_parameters=t.get('tool_info',{}).get('parameters')))
   if previous.get('state')=='DONE' and state=='DONE' and previous!=t:historical_state_issues.append(dict(reason='RAW_TOOL_CONFLICTING_DONE',step=step,job_index=job))
  history.append(t)
 issues.extend(historical_state_issues)
 for t in latest.values():
  name,p=info(t);job=owners.get(p)
  if name not in ('view_file','write_to_file'):issues.append(dict(reason='ILLEGAL_TOOL',step=t['step_index'],job_index=job))
  if name=='view_file' and p not in reads:issues.append(dict(reason='OUTSIDE_READ_WHITELIST_ATTEMPT',step=t['step_index'],path=p,job_index=job))
  if name=='view_file' and set(t.get('tool_info',{}).get('parameters',{}))!={'AbsolutePath'}:issues.append(dict(reason='VIEW_FILE_PARAMETERS_NOT_LITERAL_FULL_FILE',step=t['step_index'],path=p,job_index=job))
  if name=='write_to_file' and p not in writes:issues.append(dict(reason='OUTSIDE_WRITE_WHITELIST_ATTEMPT',step=t['step_index'],path=p,job_index=job))
  if t.get('state')=='ERROR':issues.append(dict(reason='TOOL_ERROR_TERMINAL',step=t['step_index'],path=p,job_index=job))
  if t.get('state') not in ('DONE','ERROR'):issues.append(dict(reason='TOOL_UNFINISHED',step=t['step_index'],path=p,job_index=job))
 core=[];supply=[];written=set();seen=set();selfcounts={};header_selfchecks=[];self_read_proofs=[]
 for t in done:
  name,p=info(t);supply.append(dict(step=t['step_index'],tool=name,path=p,job_index=owners.get(p)))
  text=str(t.get('tool_info',{}).get('output','')).lower()
  if any(x in text for x in ('not found','cannot read','error reading','failed to','content truncated')):issues.append(dict(reason='TOOL_FAILURE_OR_TRUNCATED_OUTPUT',step=t['step_index'],path=p,job_index=owners.get(p)))
  if name=='view_file' and p in header_keys and p in seen and key(part_by_path[p]['ack_path']) in written:
   header_selfchecks.append(dict(step=t['step_index'],path=p));continue
  if name=='view_file' and p in written:
   selfcounts[p]=selfcounts.get(p,0)+1
   if selfcounts[p]>1:issues.append(dict(reason='SELF_READ_REPEAT',path=p,job_index=owners.get(p)))
   proof=dict(actual_step=t['step_index'],path=p,actual_state=t['state'],actual_parameters=t.get('tool_info',{}).get('parameters'),actual_output=t.get('tool_info',{}).get('output'),complete=False)
   try:
    payload=Path(p).read_bytes();proof.update(current_output_sha256=hashlib.sha256(payload).hexdigest(),required_bytes=len(payload),required_Go_LF_lines=len(payload.split(b'\n')),tailLF=payload.endswith(b'\n'),noCR=b'\r' not in payload)
    proof['complete']=len(payload)<30000 and bootstrap_metadata(payload,str(t.get('tool_info',{}).get('output',''))) and set(t.get('tool_info',{}).get('parameters',{}))=={'AbsolutePath'}
   except Exception as e:proof['read_exception']=repr(e)
   self_read_proofs.append(proof)
   if not proof['complete']:issues.append(dict(reason='SELF_READ_NOT_BOUNDED_FULL_EXACT_TEXT',path=p,step=t['step_index'],job_index=owners.get(p)))
   continue
  core.append((name,p));seen.add(p)
  if name=='write_to_file':
   if p in written:issues.append(dict(reason='OUTPUT_OVERWRITE',path=p,job_index=owners.get(p)))
   written.add(p)
 expected=expected_core(index,stop_job)
 if core!=expected:issues.append(dict(reason='CORE_MEDIA_ORDER_OR_MISSING',expected_count=len(expected),actual_count=len(core),job_index=None))
 text_proofs=[]
 for p in parts:
  views=[t for t in latest.values() if info(t)==('view_file',key(p['path']))];acks=[t for t in latest.values() if info(t)==('write_to_file',key(p['ack_path']))]
  payload=Path(p['path']).read_bytes();exact_views=[dict(actual_step=t['step_index'],actual_state=t['state'],actual_parameters=t.get('tool_info',{}).get('parameters'),actual_output=t.get('tool_info',{}).get('output'),exact_full_metadata=bootstrap_metadata(payload,str(t.get('tool_info',{}).get('output','')))) for t in views]
  view_ok=bool(views) and (p['kind']=='header' or len(views)==1) and len(payload)<30000 and all(t['state']=='DONE' and set(t.get('tool_info',{}).get('parameters',{}))=={'AbsolutePath'} and x['exact_full_metadata'] for t,x in zip(views,exact_views))
  expected_ack=read(p['expected_ACK_path']);ack_doc=None;ack_ok=False
  try:
   ack_doc=read(p['ack_path']);i=next(i for i,t in enumerate(done) if t['step_index']==views[0]['step_index'])
   ack_ok=ack_doc==expected_ack and len(acks)==1 and acks[0]['state']=='DONE' and i+1<len(done) and done[i+1]['step_index']==acks[0]['step_index'] and view_ok
  except Exception:pass
  if not view_ok:issues.append(dict(reason='TEXT_FRAGMENT_NOT_FULL_EXACT_DONE',part_id=p['part_id'],job_index=p['job_index']))
  if not ack_ok:issues.append(dict(reason='TEXT_FRAGMENT_ACK_WRONG_MISSING_OR_ORDER',part_id=p['part_id'],job_index=p['job_index']))
  text_proofs.append(dict(part_id=p['part_id'],kind=p['kind'],job_index=p['job_index'],insertion_point=p['insertion_point'],path=p['path'],input_sha256=sha(p['path']),required_bytes=len(payload),required_Go_LF_lines=len(payload.split(b'\n')),tailLF=payload.endswith(b'\n'),noCR=b'\r' not in payload,actual_view_metadata=exact_views,expected_ACK_path=p['expected_ACK_path'],expected_ACK_sha256=sha(p['expected_ACK_path']),actual_ACK_path=p['ack_path'],actual_ACK_sha256=sha(p['ack_path']) if Path(p['ack_path']).exists() else None,actual_ACK_document=ack_doc,actual_ACK_write_steps=acks,view_successful_complete=view_ok,ACK_complete=ack_ok,complete=view_ok and ack_ok,finite_text_supply_not_attention_or_semantic_PASS=True))
 reports=[];offset=2
 for w in active:
  count=100;local_complete=core[offset:offset+count]==expected[offset:offset+count];local_issues=[i for i in issues if i.get('job_index') in (None,w['job_index']) and i['reason']!='CORE_MEDIA_ORDER_OR_MISSING'];bound=[];schema=[]
  original={int(f['frame_id'][1:]):f for f in w['native_identity_all64']}
  for g in w['groups']:
   view_steps=[t for t in latest.values() if info(t)[0]=='view_file' and info(t)[1] in {key(f['path']) for f in g['frames']}]
   write_steps=[t for t in latest.values() if info(t)==('write_to_file',key(g['output_path']))]
   barrier={}
   if len(view_steps)==4 and len(write_steps)==1:
    barrier=four_image_barrier(rows,view_steps,write_steps[0])
    if not barrier['all_four_DONE_before_fact_planning_response']:local_issues.append(dict(reason='FOUR_IMAGE_DONE_BEFORE_FACT_PLANNING_BARRIER',group=g['group'],job_index=w['job_index'],actual_barrier=barrier))
   try:
    items=fact_items(read(g['output_path']),g['group'])
    for item in items:bound.append(dict(group=g['group'],slot=item['slot'],identity=original[g['group']*4+item['slot']],facts=item,origin='FRESH_SPLIT_ACTUAL_ALIAS_PNG_AND_NEW_FACTS',raw_fact_output=dict(path=g['output_path'],sha256=sha(g['output_path'])),tool_provenance=dict(fact_write_DONE_steps=[s['step'] for s in supply if s['tool']=='write_to_file' and s['path']==key(g['output_path'])],four_image_barrier=barrier),identity_generated_by_program=True))
   except Exception as e:schema.append(dict(reason='FACT_SCHEMA_OR_MISSING',group=g['group'],error=repr(e)))
  effective_steps=[next((t for t in latest.values() if info(t)==('view_file',key(f['path']))),None) for f in w['student_previews']]
  proposal_steps=[t for t in latest.values() if info(t)==('write_to_file',key(w['proposal_path']))]
  effective_proof={}
  if all(t is not None for t in effective_steps) and len(proposal_steps)==1:
   effective_proof=effective_barrier(rows,effective_steps,proposal_steps[0])
   if not effective_proof['two_distinct_forward_four_image_batches_then_proposal']:local_issues.append(dict(reason='EFFECTIVE_TWO_FOUR_IMAGE_BATCHES_AND_FORWARD_PROPOSAL',job_index=w['job_index'],actual_barrier=effective_proof))
  else:local_issues.append(dict(reason='MISSING_EFFECTIVE_OR_PROPOSAL_BARRIER',job_index=w['job_index']))
  proposal_issues=[]
  try:proposal_schema(w['proposal_path'],w)
  except Exception as e:proposal_issues.append(dict(reason='PROPOSAL_SCHEMA_OR_COVERAGE',error=repr(e)))
  good=local_complete and not local_issues and not schema and not proposal_issues and len(bound)==64
  steps=lambda name,p:[s['step'] for s in supply if s['tool']==name and s['path']==key(p)]
  reports.append(dict(job_index=w['job_index'],window_id=w['window_id'],status='PASS_TOOL_TEXT_AND_MEDIA_STRUCTURE_PENDING_ROOT_SEMANTIC' if good else 'REJECTED_OR_INCOMPLETE_KEEP_RAW',required_complete_native_facts=64,prior_native_facts_transferred=0,new_native_frames_planned=64,new_native_read_DONE=[dict(frame_id=f['frame_id'],alias_path=f['path'],original_path=f['original_path'],tool_steps=steps('view_file',f['path'])) for g in w['groups'] for f in g['frames'] if steps('view_file',f['path'])],new_fact_groups_DONE=[g['group'] for g in w['groups'] if steps('write_to_file',g['output_path'])],clip_read_DONE_steps=steps('view_file',w['clip_path']),student_preview_read_DONE=[dict(frame_id=f['frame_id'],alias_path=f['path'],original_path=f['original_path'],tool_steps=steps('view_file',f['path'])) for f in w['student_previews'] if steps('view_file',f['path'])],proposal_write_DONE_steps=steps('write_to_file',w['proposal_path']),effective_preview_batch_barrier=effective_proof,proposal_path=w['proposal_path'],proposal_sha256=sha(w['proposal_path']) if Path(w['proposal_path']).exists() else None,window_core_sequence_complete=local_complete,core_tool_count=count,scientific_media_fact_tool_count=90,bound_rows=len(bound),bound_fact_rows=bound,schema_issues=schema,proposal_issues=proposal_issues,local_tool_issues=local_issues,text_fragment_ids=[p['part_id'] for p in parts if p['job_index'] in (None,w['job_index'])],semantic_correctness='ROOT_INDEPENDENT_PENDING',training_admitted=False));offset+=count
 result=next((r['result'] for r in reversed(rows) if r.get('event')=='result'),{});error_steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message'];bare,reported=metadata_errors(error_steps)
 text_ok=all(p['view_successful_complete'] for p in text_proofs);ack_ok=all(p['ACK_complete'] for p in text_proofs)
 return dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=fr['CLI_after'],scope_stop_job=stop_job,windows=reports,tool_issues=issues,actual_supply=supply,text_fragment_proofs=text_proofs,scientific_core_expected=scientific_core(index,stop_job),bootstrap_successful_complete=text_ok,bootstrap_ack_complete=ack_ok,expected_core_tool_calls=len(expected),actual_core_tool_calls=len(core),expected_supply_with_context=len(expected),actual_supply_with_context=len(core),same_index_read_count=len(header_selfchecks)+len(active),same_index_reads=header_selfchecks,index_hard_count_limit=False,self_reads=selfcounts,actual_self_read_proofs=self_read_proofs,all_raw_tool_state_issues=historical_state_issues,errored_tool_attempts=errors,unfinished_tool_attempts=unfinished,error_message_steps=error_steps,bare_nonmedia_error_metadata=bare,reported_nonmedia_errors=reported,actual_result_status=result.get('status'),actual_result_error=result.get('error'),actual_result_usage=result.get('usage'),actual_stream_SHA=hashlib.sha256(raw).hexdigest(),freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),terminal_sha256=sha(a/'terminal.json') if terminal else None,teacher_task_completed=not issues and all(w['status'].startswith('PASS_') for w in reports),AGY_SUCCESS_does_not_override_media_ERROR=True,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False)
