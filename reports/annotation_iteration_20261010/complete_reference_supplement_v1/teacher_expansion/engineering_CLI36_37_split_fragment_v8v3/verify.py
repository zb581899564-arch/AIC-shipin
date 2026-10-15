"""Independent CPU fixtures: never write synthetic teacher outputs/raw."""
from common import ROOT,BASE,read,sha,save,key,expected_core,scientific_core,bootstrap_metadata,fact_items,proposal_schema
from pathlib import Path
import ast,copy,json,hashlib,subprocess
from functools import lru_cache
key=lru_cache(None)(key)
from unittest.mock import patch
import engine,audit,common

def negatives():
 results=[];good=[dict(status='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC',job_index=x) for x in (19,20)]
 terminal=dict(child_process_created=True,exit_code=0,stop_reason=None)
 whole=dict(errored_tool_attempts=[],unfinished_tool_attempts=[],tool_issues=[],reported_nonmedia_errors=[],actual_result_status='SUCCESS',actual_result_error=None)
 def case(name,want,**change):
  v=dict(scopes=copy.deepcopy(good),terminal=copy.deepcopy(terminal),whole=copy.deepcopy(whole),post=[],drift=[],media_repeats=[],late_writes=[]);v.update(change);d=audit.continuation_decision(**v)
  assert d['eligible']==want,(name,d);results.append(dict(name=name,eligible=d['eligible'],whole_success=d['whole_success'],issues=d['issues'],synthetic_memory_only=True))
 case('complete_natural_SUCCESS_positive',True)
 for name,change in [('network_after_all',dict(whole=dict(whole,actual_result_status='ERROR',actual_result_error='request failed tcp EOF'),network_error_after_last_proposal=True)),('401_after_all',dict(whole=dict(whole,actual_result_status='ERROR',actual_result_error='401 UNAUTHENTICATED'))),('early_terminal_SUCCESS',dict(pre_completion_error=True)),('media_ERROR',dict(whole=dict(whole,errored_tool_attempts=[{'state':'ERROR'}]))),('outside_before',dict(whole=dict(whole,tool_issues=[{'reason':'OUTSIDE_READ_WHITELIST_ATTEMPT'}]))),('outside_after',dict(post=[{'tool_name':'view_file'}])),('repeat_media',dict(media_repeats=[{}])),('rewrite_samebytes',dict(late_writes=[{}])),('byte_drift',dict(drift=[{}])),('missing_scope',dict(scopes=[good[0],{'status':'MISSING_SCOPE'}])),('zero_scope',dict(scopes=[])),('unfinished_tool',dict(whole=dict(whole,unfinished_tool_attempts=[{}]))),('timeout',dict(terminal=dict(terminal,stop_reason='OWNED_TIMEOUT'))),('prespawn',dict(terminal=dict(terminal,child_process_created=False))),('reported_error',dict(whole=dict(whole,reported_nonmedia_errors=[{}])))]:case(name+'_STOP_before37',False,**change)
 a=ROOT/'call36';idx=read(a/'index.json');fr=read(a/'freeze.json');docs={};nativekeys=set();groupends={}
 for p in idx['text_fragments']:docs[key(p['ack_path'])]=read(p['expected_ACK_path'])
 for w in idx['windows']:
  for g in w['groups']:
   docs[key(g['output_path'])]=dict(group=g['group'],items=[dict(slot=s,subject='memory fixture',composition='memory fixture',subtitle_visible=False,subtitle_text=None,visible_fact='memory fixture') for s in range(4)])
   for f in g['frames']:nativekeys.add(key(f['path']))
   groupends[key(g['frames'][-1]['path'])]=key(g['output_path'])
  docs[key(w['proposal_path'])]=dict(segments=[dict(decision='NO',start_seconds=0,end_seconds=w['domain_local_seconds'][1],reason='synthetic fixture only',fact_support=[],start_uncertainty_range_seconds=[0,0],end_uncertainty_range_seconds=[w['domain_local_seconds'][1]]*2)],events=[],student_visibility={},limitations=[])
 fixture_fr=copy.deepcopy(fr);fixture_fr['inputs']={};oldexists=Path.exists
 def fake_read(p):
  k=key(p)
  if k==key(a/'freeze.json'):return fixture_fr
  if k in docs:return docs[k]
  return read(p)
 def fake_sha(p):return hashlib.sha256(json.dumps(docs[key(p)],sort_keys=True).encode()).hexdigest() if key(p) in docs else sha(p)
 def fake_exists(p):return key(p) in docs or oldexists(p)
 parts={key(p['path']):p for p in idx['text_fragments']};core=expected_core(idx)
 rows=[];step=0;batch=0
 def agent():
  nonlocal step;step+=1;rows.append(dict(step_update=dict(step_index=step,step_type='agent_response',state='DONE')))
 for name,p in core:
  if p in nativekeys:
   if batch==0:agent()
   batch=(batch+1)%4
  else:agent()
  step+=1;parameters={'AbsolutePath' if name=='view_file' else 'TargetFile':p}
  output='read' if name=='view_file' else 'written'
  if p in parts:
   b=Path(parts[p]['path']).read_bytes();output=f'{len(b)} bytes, {len(b.split(bytes([10])))} lines'
  for state in ('ACTIVE','DONE'):rows.append(dict(step_update=dict(step_index=step,step_type='tool',state=state,tool_name=name,tool_info=dict(parameters=parameters,output=output))))
 encode=lambda r:b'\n'.join(json.dumps(x).encode() for x in r)+b'\n'
 with patch.object(engine,'key',key),patch.object(common,'key',key),patch.object(engine,'read',side_effect=fake_read),patch.object(common,'read',side_effect=fake_read),patch.object(engine,'sha',side_effect=fake_sha),patch.object(Path,'exists',fake_exists):
  d=engine.inspect(a,encode(rows));assert not d['tool_issues'] and all(w['status'].startswith('PASS_') for w in d['windows']),d
  results.append(dict(name='full202_tool_memory_fixture_positive',passed=True,synthetic_memory_only=True))
  def rawcase(name,mutate):
   r=copy.deepcopy(rows);mutate(r);v=engine.inspect(a,encode(r));assert v['tool_issues'] or not all(w['status'].startswith('PASS_') for w in v['windows']),name;results.append(dict(name=name,rejected=True,synthetic_memory_only=True))
  def editfirst(r,k,v):r[2]['step_update']['tool_info']['output']=v
  payload=Path(idx['text_fragments'][0]['path']).read_bytes();ln=len(payload.split(b'\n'))
  for label,out in [('LFminus1',f'{len(payload)} bytes, {ln-1} lines'),('LFplus1',f'{len(payload)} bytes, {ln+1} lines'),('wrongbytes',f'{len(payload)-1} bytes, {ln} lines'),('truncated',f'{len(payload)} bytes, {ln} lines Content truncated')]:rawcase(label,lambda r,o=out:editfirst(r,'output',o))
  rawcase('text_tool_ERROR',lambda r:r[2]['step_update'].update(state='ERROR'))
  rawcase('text_unfinished',lambda r:r[2]['step_update'].update(state='ACTIVE'))
  rawcase('outside_program_index',lambda r:r[2]['step_update']['tool_info']['parameters'].update(AbsolutePath=str(a/'index.json')))
  rawcase('wrong_ACK_order',lambda r:r.__setitem__(slice(0,6),r[3:6]+r[0:3]))
  # The fact response is removed after all4DONE: last response predates views.
  firstfact=key(idx['windows'][0]['groups'][0]['output_path']);factactive=next(i for i,r in enumerate(rows) if r.get('step_update',{}).get('state')=='ACTIVE' and key(r['step_update'].get('tool_info',{}).get('parameters',{}).get('TargetFile'))==firstfact)
  rawcase('fact_planned_before_four_DONE',lambda r:r.pop(factactive-1))
  firstviews=[key(f['path']) for f in idx['windows'][0]['groups'][0]['frames']];secondactive=next(i for i,r in enumerate(rows) if r.get('step_update',{}).get('state')=='ACTIVE' and key(r['step_update'].get('tool_info',{}).get('parameters',{}).get('AbsolutePath'))==firstviews[1])
  rawcase('four_images_not_same_response',lambda r:r.insert(secondactive,dict(step_update=dict(step_index=9999,step_type='agent_response',state='DONE'))))
  rawcase('media_ERROR',lambda r:next(x['step_update'] for x in r if x.get('step_update',{}).get('state')=='DONE' and key(x['step_update'].get('tool_info',{}).get('parameters',{}).get('AbsolutePath'))==firstviews[0]).update(state='ERROR'))
  def rewrite(r):
   more=copy.deepcopy(r[factactive-1:factactive+2])
   for x in more:x['step_update']['step_index']+=10000
   r.extend(more)
  rawcase('rewrite_output_new_tool_identity',rewrite)
  ackkey=key(idx['text_fragments'][0]['ack_path']);original=copy.deepcopy(docs[ackkey]);docs[ackkey]['marker']='WRONG';v=engine.inspect(a,encode(rows));assert not v['bootstrap_ack_complete'];docs[ackkey]=original;results.append(dict(name='wrong_tail_ACK_marker',rejected=True,synthetic_memory_only=True))
  original=copy.deepcopy(docs[firstfact]);docs[firstfact]['items'][0]['slot']=False;v=engine.inspect(a,encode(rows));assert v['windows'][0]['schema_issues'];docs[firstfact]=original;results.append(dict(name='bool_slot_schema',rejected=True,synthetic_memory_only=True))
  docs[firstfact]['extra']=1;v=engine.inspect(a,encode(rows));assert v['windows'][0]['schema_issues'];docs[firstfact]=original;results.append(dict(name='open_fact_schema',rejected=True,synthetic_memory_only=True))
 for label,b,out in [('no_tailLF',payload[:-1],f'{len(payload)-1} bytes, {ln-1} lines'),('CR',payload+b'\r',f'{len(payload)+1} bytes, {ln} lines')]:assert not bootstrap_metadata(b,out);results.append(dict(name=label,rejected=True,synthetic_memory_only=True))
 return results

def main():
 binding=read(ROOT/'execution_code_binding.json');assert len(list(ROOT.glob('*.py')))==10
 for p,s in binding['sources'].items():assert sha(p)==s;ast.parse(Path(p).read_text(encoding='utf-8')) if p.endswith('.py') else None
 for p,s in binding['actual_prior_bindings'].items():assert sha(p)==s
 from prompt import scientific_text,piece,main_body,header_body,native_body
 from launch import command
 science=scientific_text((BASE/'engineering_alias_remainder_v3/call35/frozen_prompt.txt').read_text(encoding='utf-8'));assert science==scientific_text((BASE/'engineering_alias_remainder_v3/call36/frozen_prompt.txt').read_text(encoding='utf-8'))
 routes=[];allparts=[]
 for number,jobs,oldnumber in ((36,[19,20],35),(37,[21,22,23],36)):
  a=ROOT/f'call{number}';idx=read(a/'index.json');fr=read(a/'freeze.json');literal=read(a/'literal_execution_parameters.json');old=read(BASE/f'engineering_alias_remainder_v6_fresh_scope_prefix_v2/call{oldnumber}/index.json')
  for p,s in fr['inputs'].items():assert sha(p)==s,(p,'SHA_DRIFT')
  assert [w['job_index'] for w in idx['windows']]==jobs and fr['automatic_retry'] is False
  rec=read(a/'lossless_index_fragment_reconstruction.json');assert rec['native_frame_records']==64*len(jobs) and rec['native_identity_records']==64*len(jobs) and rec['student_preview_records']==8*len(jobs) and rec['clip_records']==len(jobs) and rec['literal_view_parameters']==73*len(jobs)
  cpu=read(a/'prepared_original_pixel_clock_checks.json');assert cpu['actual_PNG_count']==72*len(jobs) and cpu['clip_count']==len(jobs) and cpu['new_CPU_PNG_decode']==0
  for ow,w,l in zip(old['windows'],idx['windows'],literal):
   proj=copy.deepcopy(ow)
   for g in proj['groups']:g['output_path']=g['output_path'].replace(str(BASE/f'engineering_alias_remainder_v6_fresh_scope_prefix_v2/call{oldnumber}'),str(a))
   proj['proposal_path']=proj['proposal_path'].replace(str(BASE/f'engineering_alias_remainder_v6_fresh_scope_prefix_v2/call{oldnumber}'),str(a))
   assert proj=={k:v for k,v in w.items() if k not in ('header_fragment_id','native_fragment_ids')}
   for g,lg in zip(w['groups'],l['native_groups']):assert lg['view_file']==[dict(AbsolutePath=f['path']) for f in g['frames']] and lg['write_to_file']==dict(TargetFile=g['output_path'])
   assert [p for b in l['effective_preview_batches'] for p in b]==[dict(AbsolutePath=f['path']) for f in w['student_previews']]
   assert l['clip_view_file']==dict(AbsolutePath=w['clip_path']) and l['proposal_write_to_file']==dict(TargetFile=w['proposal_path'])
  parts=idx['text_fragments'];headers=[p for p in parts if p['kind']=='header'];short=(a/'short_prompt.txt').read_text(encoding='utf-8');white={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']}
  for p in parts:
   ack=read(p['expected_ACK_path']);w=next((w for w in idx['windows'] if w['job_index']==p['job_index']),None);l=next((l for l in literal if l['job_index']==p['job_index']),None)
   body=main_body(science,headers,number,jobs) if w is None else header_body(w,[q for q in parts if q['job_index']==w['job_index'] and q['kind']=='native_index'],l) if p['kind']=='header' else native_body(w,p['before_group'],l)
   b=Path(p['path']).read_bytes();assert b==piece(body,ack,p['ack_path']).encode() and len(b)<30000 and len(b.splitlines())<=450 and max(map(len,b.decode().splitlines()))<=1000
   assert bootstrap_metadata(b,f'{len(b)} bytes, {len(b.split(bytes([10])))} lines')
   assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8') and key(p['expected_ACK_path']) not in white
   allparts.append(dict(part_id=p['part_id'],CLI=number,bytes=len(b),sha256=sha(p['path']),full_regenerated_body_byte_exact=True))
  assert len(expected_core(idx))==2+100*len(jobs) and len(scientific_core(idx))==90*len(jobs)
  assert not any(Path(p).exists() for p in fr['write_whitelist']) and not(a/'request.json').exists() and key(a/'index.json') not in white
  assert len(subprocess.list2cmdline(command(number,short)).encode('utf-16-le'))//2+1<1024
  routes.append(dict(CLI=number,jobs=jobs,core=len(expected_core(idx)),scope_cores=[len(expected_core(idx,w['job_index'])) for w in idx['windows']]))
 # Every old line must have a real explicit classification, with exact science selected.
 mapping=read(ROOT/'scientific_text_map.json')
 for source in mapping['sources']:
  lines=Path(source['original_path']).read_text(encoding='utf-8').splitlines();mapped=source['all_original_lines_classified'];assert len(lines)==len(mapped)
  for line,m in zip(lines,mapped):assert hashlib.sha256(line.encode()).hexdigest()==m['original_line_sha256'] and m['category'] in ('OLD_ENGINEERING_INDEX_PREFIX_REPLACED_SCIENTIFIC_TAIL_VERBATIM','GIANT_DUPLICATED_LITERAL_LOSSLESS_IDENTITY_AND_LITERAL_PARTS','OLD_ENGINEERING_17_TRANSFER_CONDITION_NOT_IN_FIXED19_23','GIANT_EXPANDED_DUPLICATE_WHITELIST_REPLACED_FROZEN_PROGRAM_WHITE_AND_LITERAL_PARTS','SCIENTIFIC_PARAGRAPH_VERBATIM')
 save(ROOT/'independent_CPU_negative_acceptance.json',dict(status='PASS_CPU_ONLY_EXACT_BODY_ROUTE_SCHEMA_NEGATIVES_PENDING_ROOT_NO_START',sources=binding['sources'],routing=routes,parts=allparts,negative_cases=negatives(),scope_helper_paths=[str(ROOT/x) for x in ('common.py','engine.py','audit.py')],actual_requests36_37=0,new_models=0,new_video_decode=0,capacity_risk_not_runtime_PASS=True))
 print(json.dumps(dict(negative_count=len(read(ROOT/'independent_CPU_negative_acceptance.json')['negative_cases']),receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),routing=routes)))
if __name__=='__main__':main()
