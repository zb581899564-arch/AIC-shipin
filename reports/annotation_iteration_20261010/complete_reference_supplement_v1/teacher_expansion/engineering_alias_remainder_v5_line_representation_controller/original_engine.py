"""Actual supply only; preserves old failure and never admits semantic labels."""
from common import ROOT,read,sha,key,save,expected_core,fact_items,proposal_schema,metadata_errors
from pathlib import Path
from datetime import datetime,timezone
import json,sys,re
def inspect(a,raw,stop_job=None,terminal=None):
 index=read(a/'index.json');fr=read(a/'freeze.json');issues=[]
 for p,s in fr['inputs'].items():
  if sha(p)!=s:issues.append(dict(reason='INPUT_SHA_DRIFT',path=p,job_index=None))
 rows=[]
 for line in raw.splitlines():
  try:rows.append(json.loads(line))
  except (json.JSONDecodeError,UnicodeDecodeError):break
 updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'];latest={t['step_index']:t for t in updates}
 done=[t for t in latest.values() if t.get('state')=='DONE'];errors=[t for t in latest.values() if t.get('state')=='ERROR'];unfinished=[t for t in latest.values() if t.get('state')=='ACTIVE']
 active_windows=[]
 for w in index['windows']:
  active_windows.append(w)
  if w['job_index']==stop_job:break
 def owner(p):
  for w in index['windows']:
   if p in {key(x) for x in [w['clip_path'],w['proposal_path'],*([w['prior_context_path']] if w.get('prior_context_path') else []),*(g['output_path'] for g in w['groups']),*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])]}:return w['job_index']
   if p.startswith(key(ROOT/'aliases'/f"w{w['job_index']:02d}")+str(Path('/'))):return w['job_index']
  return None
 def info(t):
  p=t.get('tool_info',{}).get('parameters',{});return t.get('tool_name'),key(p.get('AbsolutePath') or p.get('TargetFile'))
 allowed_reads={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']};allowed_writes={key(p) for p in fr['write_whitelist']}
 for t in latest.values():
  name,p=info(t);job=owner(p)
  if name not in ('view_file','write_to_file'):issues.append(dict(reason='ILLEGAL_TOOL',step=t['step_index'],tool=name,job_index=job))
  if name=='view_file' and p not in allowed_reads:issues.append(dict(reason='OUTSIDE_READ_WHITELIST_ATTEMPT',step=t['step_index'],path=p,job_index=job))
  if name=='write_to_file' and p not in allowed_writes:issues.append(dict(reason='OUTSIDE_WRITE_WHITELIST_ATTEMPT',step=t['step_index'],path=p,job_index=job))
  if t.get('state')=='ERROR':issues.append(dict(reason='TOOL_ERROR_TERMINAL',step=t['step_index'],tool=name,path=p,job_index=job))
  if t.get('state')=='ACTIVE':issues.append(dict(reason='TOOL_UNFINISHED',step=t['step_index'],tool=name,path=p,job_index=job))
 core=[];full=[];supply=[];index_reads=[];context_reads={};written=set();selfcounts={}
 contexts={key(w['prior_context_path']):w['job_index'] for w in index['windows'] if w.get('prior_context_path')}
 for t in done:
  name,p=info(t);step=t['step_index'];supply.append(dict(step=step,tool=name,path=p,job_index=owner(p)))
  text=str(t.get('tool_info',{}).get('output','')).lower()
  if any(x in text for x in ('not found','cannot read','error reading','failed to')):issues.append(dict(reason='TOOL_FAILURE_OUTPUT',step=step,path=p,job_index=owner(p)))
  if name=='view_file' and p==key(a/'index.json'):
   index_reads.append(dict(step=step,core_tools_before=len(core),path=p))
   if len(index_reads)==1:core.append((name,p));full.append((name,p))
  elif name=='view_file' and p in contexts:
   context_reads.setdefault(p,[]).append(step);full.append((name,p))
  elif name=='view_file' and p in written:
   selfcounts[p]=selfcounts.get(p,0)+1
   if selfcounts[p]>1:issues.append(dict(reason='SELF_READ_REPEAT',path=p,job_index=owner(p)))
  else:
   core.append((name,p));full.append((name,p))
   if name=='write_to_file':
    if p in written:issues.append(dict(reason='OUTPUT_OVERWRITE',path=p,job_index=owner(p)))
    written.add(p)
 expected=expected_core(index,stop_job);expected_full=expected[:3]
 for w in active_windows:
  if w.get('prior_context_path'):expected_full.append(('view_file',key(w['prior_context_path'])))
  one=expected_core(dict(index_path=index['index_path'],bootstrap_instruction_path=index['bootstrap_instruction_path'],bootstrap_ack_path=index['bootstrap_ack_path'],windows=[w]))[3:];expected_full.extend(one)
 if core!=expected:issues.append(dict(reason='CORE_MEDIA_ORDER_OR_MISSING',expected_count=len(expected),actual_count=len(core),job_index=None))
 if full!=expected_full:issues.append(dict(reason='CONTEXT_OR_SUPPLY_ORDER_OR_MISSING',expected_count=len(expected_full),actual_count=len(full),job_index=None))
 bootstrap=[t for t in latest.values() if info(t)==('view_file',key(index['bootstrap_instruction_path']))]
 bootstrap_ok=False
 if len(bootstrap)==1:
  bt=bootstrap[0];params=bt.get('tool_info',{}).get('parameters',{});output=str(bt.get('tool_info',{}).get('output',''))
  byte_report=re.search(r'(\d+) bytes',output);line_report=re.search(r'(\d+) lines',output)
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
 reports=[];offset=3
 for w in active_windows:
  count=len(expected_core(dict(index_path=index['index_path'],bootstrap_instruction_path=index['bootstrap_instruction_path'],bootstrap_ack_path=index['bootstrap_ack_path'],windows=[w])))-3
  local_complete=core[offset:offset+count]==expected[offset:offset+count] and core[:3]==expected[:3]
  local_issues=[i for i in issues if i.get('job_index') in (None,w['job_index']) and i['reason'] not in ('CORE_MEDIA_ORDER_OR_MISSING','CONTEXT_OR_SUPPLY_ORDER_OR_MISSING')]
  schema=[];bound=[];prior_docs={}
  if w.get('prior_context_path'):
   package=read(w['prior_context_path']);proof=read(w['prior_facts_provenance_path'])
   assert package['window_id']==w['window_id'] and package['job_index']==w['job_index']
   assert proof['actual_prior_group_sequence_complete'] and proof['original_CLI33_strict_failed_preserved']
   prior_docs={d['group']:d for d in package['groups']}
   if len(context_reads.get(key(w['prior_context_path']),[]))!=1:local_issues.append(dict(reason='PRIOR_CONTEXT_NOT_EXACTLY_ONCE',job_index=w['job_index']))
  fresh={g['group']:g for g in w['groups']};original={int(f['frame_id'][1:]):f for f in w['native_identity_all64']}
  for group in range(16):
   try:
    if group in prior_docs:
     doc=prior_docs[group];origin='CLI33_ACTUAL_NATIVE_AND_FACTS_TRANSFER_NOT_NEW_READ';out_ref=proof['groups'][group]['facts'];tool_provenance=proof['groups'][group]
    else:
     g=fresh[group];doc=read(g['output_path']);origin=f"CLI{fr['CLI_after']}_ALIAS_NATIVE_AND_NEW_FACTS";out_ref=dict(path=g['output_path'],sha256=sha(g['output_path']));tool_provenance=dict(fact_write_DONE_steps=[s['step'] for s in supply if s['tool']=='write_to_file' and s['path']==key(g['output_path'])])
    items=fact_items(doc,group)
    for item in items:
     f=original[group*4+item['slot']]
     bound.append(dict(group=group,slot=item['slot'],identity=f,facts=item,origin=origin,raw_fact_output=out_ref,tool_provenance=tool_provenance,identity_generated_by_program=True))
   except Exception as e:schema.append(dict(reason='FACT_SCHEMA_OR_MISSING',group=group,error=repr(e)))
  proposal_issues=[]
  try:proposal_schema(w['proposal_path'],w)
  except Exception as e:proposal_issues.append(dict(reason='PROPOSAL_SCHEMA_OR_COVERAGE',error=repr(e)))
  complete=local_complete and not local_issues and not schema and not proposal_issues and len(bound)==64
  status=('PASS_COMPOSED_SUPPLY_PENDING_ROOT_SEMANTIC_REVIEW' if w.get('prior_context_path') else 'PASS_TOOL_STRUCTURE_PENDING_ROOT_SEMANTIC_REVIEW') if complete else 'REJECTED_OR_INCOMPLETE_KEEP_RAW'
  def steps(name,p):return [s['step'] for s in supply if s['tool']==name and s['path']==key(p)]
  reports.append(dict(job_index=w['job_index'],window_id=w['window_id'],status=status,required_complete_native_facts=64,prior_native_facts_transferred=32 if prior_docs else 0,new_native_frames_planned=sum(len(g['frames']) for g in w['groups']),new_native_read_DONE=[dict(frame_id=f['frame_id'],alias_path=f['path'],original_path=f['original_path'],tool_steps=steps('view_file',f['path'])) for g in w['groups'] for f in g['frames'] if steps('view_file',f['path'])],new_fact_groups_DONE=[g['group'] for g in w['groups'] if steps('write_to_file',g['output_path'])],clip_read_DONE_steps=steps('view_file',w['clip_path']),student_preview_read_DONE=[dict(frame_id=f['frame_id'],alias_path=f['path'],original_path=f['original_path'],tool_steps=steps('view_file',f['path'])) for f in w['student_previews'] if steps('view_file',f['path'])],proposal_write_DONE_steps=steps('write_to_file',w['proposal_path']),proposal_path=w['proposal_path'],proposal_sha256=sha(w['proposal_path']) if Path(w['proposal_path']).exists() else None,window_core_sequence_complete=local_complete,core_tool_count=count,context_read_DONE_steps=context_reads.get(key(w['prior_context_path']),[]) if w.get('prior_context_path') else [],bound_rows=len(bound),bound_fact_rows=bound,schema_issues=schema,proposal_issues=proposal_issues,local_tool_issues=local_issues,old_CLI33_not_reclassified_as_PASS=bool(prior_docs),F35_reprovide_planned_exception=bool(prior_docs),F35_actual_new_DONE_steps=steps('view_file',next((f['path'] for g in w['groups'] for f in g['frames'] if f['frame_id']=='F35'),'')) if prior_docs else [],semantic_correctness='UNVERIFIED_ROOT_AND_INDEPENDENT_STUDENT_REQUIRED',training_admitted=False))
  offset+=count
 result=next((r['result'] for r in reversed(rows) if r.get('event')=='result'),{})
 error_steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message'];bare,reported=metadata_errors(error_steps)
 return dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=fr['CLI_after'],scope_stop_job=stop_job,windows=reports,tool_issues=issues,actual_supply=supply,bootstrap_successful_complete=bootstrap_ok,bootstrap_ack_complete=ack_ok,bootstrap_attempts=bootstrap,bootstrap_ack_steps=ack_steps,bootstrap_required_bytes=Path(index['bootstrap_instruction_path']).stat().st_size,bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().splitlines()),bootstrap_ack_sha256=sha(index['bootstrap_ack_path']) if Path(index['bootstrap_ack_path']).exists() else None,bootstrap_provenance_limit='Full file metadata and unique tail ACK verify limited instruction supply/routes, not text attention or semantics',expected_core_tool_calls=len(expected),actual_core_tool_calls=len(core),expected_supply_with_context=len(expected_full),actual_supply_with_context=len(full),same_index_read_count=len(index_reads),same_index_reads=index_reads,index_hard_count_limit=False,context_read_steps=context_reads,self_reads=selfcounts,errored_tool_attempts=errors,unfinished_tool_attempts=unfinished,error_message_steps=error_steps,bare_nonmedia_error_metadata=bare,reported_nonmedia_errors=reported,actual_result_status=result.get('status'),actual_result_error=result.get('error'),actual_result_usage=result.get('usage'),actual_stream_SHA=__import__('hashlib').sha256(raw).hexdigest(),freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),terminal_sha256=sha(a/'terminal.json') if terminal else None,actual_terminal_exit_code=terminal.get('exit_code') if terminal else None,teacher_task_completed=not issues and all(w['status'].startswith('PASS_') for w in reports),AGY_SUCCESS_does_not_override_media_ERROR=True,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False)
