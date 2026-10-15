"""Bind actual immutable manual38 scope for unchanged ROOT finalize; no semantics/decode."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
import argparse,hashlib,json,importlib,sys,re
R=Path(__file__).resolve().parent
V=R/'teacher_expansion/manual_CLI38_retry_v1'
# Actual38 has stopped during22; only sealed lawful21 may be wrapped.
OUTPUTS={21:'21_cjibt_w16_lawful_observation_completion_manual38_v1.json'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold()
def bind(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def parsed(payload):
 rows=[]
 for line in payload.splitlines():
  try:rows.append(json.loads(line))
  except (json.JSONDecodeError,UnicodeDecodeError):break
 return rows

def pathinfo(t):
 p=t.get('tool_info',{}).get('parameters',{})
 return t.get('tool_name'),key(p.get('AbsolutePath') or p.get('TargetFile'))

@contextmanager
def current_engine():
 # Scoped imports ensure ROOT's other helpers cannot accidentally supply a
 # different common/engine module. Only CPU parsers are imported, never launch.
 oldpath=list(sys.path);oldmodules={n:sys.modules.pop(n,None) for n in ('common','engine')}
 try:
  sys.path.insert(0,str(V));common=importlib.import_module('common');engine=importlib.import_module('engine')
  assert Path(common.__file__).resolve()==V/'common.py' and Path(engine.__file__).resolve()==V/'engine.py'
  yield common,engine
 finally:
  for n in ('engine','common'):sys.modules.pop(n,None)
  for n,m in oldmodules.items():
   if m is not None:sys.modules[n]=m
  sys.path[:]=oldpath

def full_text_read(t,path):
 b=Path(path).read_bytes();text=str(t['tool_info'].get('output',''));nb=re.search(r'(\d+) bytes',text);nl=re.search(r'(\d+) lines',text)
 assert len(b)<30000 and b.endswith(b'\n') and b'\r' not in b
 assert nb and int(nb.group(1))==len(b) and nl and int(nl.group(1))==len(b.split(b'\n'))
 assert not any(x in text.lower() for x in ('truncat','not found','cannot read','failed','error'))
 return dict(step=t['step_index'],parameters=t['tool_info']['parameters'],output=t['tool_info'].get('output'),bytes=len(b),Go_LF_lines=len(b.split(b'\n')))

def raw_tools(rows,fr):
 reads={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']};writes={key(p) for p in fr['write_whitelist']};identities={};last={}
 for r in rows:
  assert r.get('event')!='result'
  t=r.get('step_update',{})
  if t.get('step_type')!='tool':continue
  assert t['state']!='ERROR';name=t['tool_name'];p=t.get('tool_info',{}).get('parameters',{})
  assert name in ('view_file','write_to_file')
  if name=='view_file':assert set(p)=={'AbsolutePath'} and key(p['AbsolutePath']) in reads
  else:assert key(p.get('TargetFile')) in writes
  identity=(name,json.dumps(p,ensure_ascii=False,sort_keys=True));step=t['step_index']
  if step in identities:assert identities[step]==identity
  identities[step]=identity;last[step]=t
 assert all(t['state']=='DONE' for t in last.values())
 return [t for _,t in sorted(last.items())]

def required_core(idx,active):
 parts={p['part_id']:p for p in idx['text_fragments']};seq=[];required=[]
 def add(pid):
  p=parts[pid];required.append(p);seq.extend([('view_file',key(p['path'])),('write_to_file',key(p['ack_path']))])
 add(idx['main_fragment_id'])
 for w in active:
  add(w['header_fragment_id'])
  for g in w['groups']:
   if g['group']%4==0:add(w['native_fragment_ids'][g['group']//4])
   seq.extend(('view_file',key(f['path'])) for f in g['frames']);seq.append(('write_to_file',key(g['output_path'])))
  seq.append(('view_file',key(w['clip_path'])));seq.extend(('view_file',key(f['path'])) for f in w['student_previews']);add(w['proposal_fragment_id']);seq.append(('write_to_file',key(w['proposal_path'])))
 return seq,required

def verify_core_and_text(rows,tools,idx,active,common):
 expected,parts=required_core(idx,active);headers={key(p['path']):p for p in idx['text_fragments'] if p['kind']=='header'};core=[];written=set();seen=set();selfcounts={};selfchecks=[]
 for t in tools:
  name,p=pathinfo(t)
  if name=='view_file' and p in headers and p in seen and key(headers[p]['ack_path']) in written:selfchecks.append(full_text_read(t,p));continue
  if name=='view_file' and p in written:
   selfcounts[p]=selfcounts.get(p,0)+1;assert selfcounts[p]==1;full_text_read(t,p);continue
  if name=='write_to_file':assert p not in written;written.add(p)
  core.append((name,p));seen.add(p)
 assert core==expected and len(core)==2+idx['core_per_window']*len(active)
 textproof=[]
 def position(step,state):return next((i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')==state),-1)
 for p in parts:
  views=[t for t in tools if pathinfo(t)==('view_file',key(p['path']))];acks=[t for t in tools if pathinfo(t)==('write_to_file',key(p['ack_path']))]
  assert views and len(acks)==1 and (p['kind']=='header' or len(views)==1)
  metadata=[full_text_read(t,p['path']) for t in views];expected_ACK=read(p['expected_ACK_path']);assert read(p['ack_path'])==expected_ACK
  assert sha(p['path'])==p['input_sha256'] and sha(p['expected_ACK_path'])==p['expected_ACK_sha256'] and Path(p['path']).read_text(encoding='utf-8').rstrip().endswith(expected_ACK['marker'])
  v=views[0];ack=acks[0];va=position(v['step_index'],'ACTIVE');vd=position(v['step_index'],'DONE');aa=position(ack['step_index'],'ACTIVE');ad=position(ack['step_index'],'DONE')
  assert 0<=va<vd<aa<ad
  planning=[i for i,r in enumerate(rows[:aa]) if r.get('step_update',{}).get('step_type')=='agent_response' and r['step_update'].get('state')=='DONE'];assert planning and vd<planning[-1]<aa
  assert common.bootstrap_metadata(Path(p['path']).read_bytes(),str(v['tool_info'].get('output','')))
  textproof.append(dict(part_id=p['part_id'],input=bind(p['path']),ACK=bind(p['ack_path']),actual_read_metadata=metadata,ACK_barrier=dict(read_ACTIVE=va,read_DONE=vd,planning_DONE=planning[-1],write_ACTIVE=aa,write_DONE=ad)))
 return core,textproof,selfchecks

def verify_prior_pixel_clock_binding(c,w,a,fr):
 # SHA continuity of already accepted pixel bytes proves reuse; do not decode RGB
 # again. Both actual scope RGB receipt and earlier CPU receipt are referenced.
 pcpath=c/'prepared_original_pixel_clock_checks.json';pc=read(pcpath);assert sha(pc['original_receipt_path'])==pc['original_receipt_sha256']
 records=next(x['checks'] for x in pc['windows'] if x['job_index']==w['job_index']);assert len(records)==72 and records==a['actual_png_pixel_checks']
 frames=[*(f for g in w['groups'] for f in g['frames']),*w['student_previews']]
 for f,r in zip(frames,records):
  assert f['path']==r['alias_path'] and f['original_path']==r['original_path'] and f['frame_id']==r['frame_id']
  for k in ('png_sha256','rgb_pixel_sha256','geometry'):assert f[k]==r[k]
  assert sha(f['path'])==f['png_sha256']==sha(f['original_path'])
 manifest=read(w['original_source_manifest']['path']);assert sha(w['original_source_manifest']['path'])==w['original_source_manifest']['sha256'] and manifest['window_id']==w['window_id']
 assert sha(w['clip_path'])==manifest['clip_sha256']==sha(w['original_clip_path'])
 clock=w['original_source_manifest']['native_clock'];assert sha(clock['path'])==clock['sha256']
 receipt=read(w['original_student_receipt']['path']);assert sha(w['original_student_receipt']['path'])==w['original_student_receipt']['sha256'] and receipt['patch_inverse_exact'] and len(receipt['frames'])==64
 students={r['frame_id']:r for r in receipt['frames']}
 for f in w['student_previews']:
  for k in ('png_sha256','rgb_pixel_sha256','source_ordinal'):assert f[k]==students[f['frame_id']][k]
 return dict(scope_actual_RGB_checks_referenced=72,prior_CPU_receipt=bind(pcpath),original_successful_CPU_receipt=bind(pc['original_receipt_path']),original_native_clock=bind(clock['path']),source_manifest=bind(w['original_source_manifest']['path']),student_processor_receipt=bind(w['original_student_receipt']['path']),new_RGB_checks=0,new_decoder_calls=0,new_processor_calls=0,current_PNG_SHA_continuity_verified=72)

def accept(job,output=None):
 assert job in OUTPUTS;c=V/'call38';output=Path(output).resolve() if output else R/OUTPUTS[job];assert output.parent==R and not output.exists()
 ap=c/f'w{job:02d}_completed_scope_audit.json';a=read(ap);fr=read(c/'freeze.json');idx=read(c/'index.json');req=read(c/'request.json');gate=read(V/'root_start_admission.json');binding=read(V/'execution_code_binding.json')
 assert a['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
 for k in ('tool_issues','additional_scope_issues','all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'):assert not a[k],k
 assert fr['CLI_after']==req['CLI_after']==38 and fr['CLI_before']==37 and fr['global_cap']==38 and fr['no39'] is True and fr['timeout_seconds']==7200 and fr['automatic_retry'] is False
 assert req['model']=='gemini-3.8-flash-high' and req['freeze_sha256']==sha(c/'freeze.json') and req['root_start_admission_sha256']==sha(V/'root_start_admission.json')
 assert gate['status']=='ROOT_APPROVED_START_MANUAL_CLI38_ONCE_FIXED21_23_AFTER_ZERO_TOOL_LOCATION37' and gate['CLI']==gate['global_cap']==38 and gate['no39'] is True and gate['automatic_retry'] is False and gate['fixed_job_indices']==[21,22,23] and gate['timeout_seconds']==7200
 assert gate['execution_binding_sha256']==fr['source_binding_sha256']==sha(V/'execution_code_binding.json') and gate['dry_run_sha256']==sha(V/'dry_run_acceptance.json') and gate['negative_receipt_sha256']==sha(V/'independent_CPU_negative_acceptance.json')
 auth=gate['manual_user_authorization'];assert sha(auth['path'])==auth['sha256']==req['manual_user_authorization_sha256']==fr['manual_user_authorization_sha256'];assert read(auth['path'])['status']=='USER_EXPLICIT_ONE_MANUAL_CLI38_RETRY_NO39_FIXED21_23'
 recovery=gate['w20_semantic_recovery_receipt'];assert sha(recovery['path'])==recovery['sha256'] and read(recovery['path'])['reference_binding']==gate['w20_reference_binding']
 for p,h in binding['sources'].items():assert sha(p)==h
 for p,h in binding['actual_prior_bindings'].items():assert sha(p)==h
 for p,h in fr['inputs'].items():assert sha(p)==h,p
 assert idx['core_per_window']==fr['core_per_window']==102 and idx['scope_core_counts']==fr['scope_core_counts']==[104,206,308]
 pref=Path(a['immutable_prefix']['path']);prefix=pref.read_bytes();assert len(prefix)==a['immutable_prefix']['bytes'] and sha(pref)==a['immutable_prefix']['sha256']==a['actual_stream_SHA']
 live=(c/'stream.jsonl').read_bytes();assert live.startswith(prefix)
 sealed={key(x['original_path']):x for x in a['immutable_actual_outputs']}
 for x in sealed.values():assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
 active=[]
 for w in idx['windows']:
  active.append(w)
  if w['job_index']==job:break
 assert active[-1]['job_index']==job;w=active[-1];ar=a['windows'][-1]
 assert ar['job_index']==job and ar['window_id']==w['window_id'] and ar['bound_rows']==len(ar['bound_fact_rows'])==64 and ar['status']=='PASS_TOOL_TEXT_AND_MEDIA_STRUCTURE_PENDING_ROOT_SEMANTIC'
 for k in ('schema_issues','proposal_issues','local_tool_issues'):assert not ar[k],k
 rows=list(map(json.loads,prefix.splitlines()));tools=raw_tools(rows,fr)
 with current_engine() as (common,engine):
  actual=engine.inspect(c,prefix,job)
  for k in ('tool_issues','all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'):assert not actual[k],k
  assert actual['bootstrap_successful_complete'] and actual['bootstrap_ack_complete'] and actual['teacher_task_completed']
  for k in ('actual_supply','text_fragment_proofs','scientific_core_expected','windows'):assert actual[k]==a[k],k
  core,textproof,selfchecks=verify_core_and_text(rows,tools,idx,active,common)
  assert len(core)==a['actual_core_tool_calls']==a['expected_core_tool_calls']==fr['scope_core_counts'][[21,22,23].index(job)]
  assert len(ar['new_native_read_DONE'])==64 and len(ar['new_fact_groups_DONE'])==16 and len(ar['clip_read_DONE_steps'])==1 and len(ar['student_preview_read_DONE'])==8 and len(ar['proposal_write_DONE_steps'])==1
  assert len(w['groups'])==16 and len(w['native_identity_all64'])==64 and len(w['student_previews'])==8
  for i,(r,f) in enumerate(zip(ar['bound_fact_rows'],w['native_identity_all64'])):
   g=w['groups'][i//4];alias=g['frames'][i%4];assert r['identity']==f and f['frame_id']==f'F{i:02d}' and r['identity_generated_by_program'] is True
   assert r['group']==i//4 and r['slot']==i%4 and r['facts']==common.fact_items(read(g['output_path']),i//4)[i%4] and sha(r['raw_fact_output']['path'])==r['raw_fact_output']['sha256']
   for k in ('source_ordinal','global_seconds_exact','local_seconds_exact','png_sha256','rgb_pixel_sha256','geometry','original_path'):assert alias[k]==f[k]
   assert r['tool_provenance']['four_image_barrier']['all_four_DONE_before_fact_planning_response'] is True
  common.proposal_schema(w['proposal_path'],w)
  proposal=bind(w['proposal_path']);assert proposal['sha256']==ar['proposal_sha256']
 pixel_binding=verify_prior_pixel_clock_binding(c,w,a,fr)
 required_output_paths=[g['output_path'] for g in w['groups']]+[w['proposal_path']]+[p['ack_path'] for p in idx['text_fragments'] if p['job_index']==job or p['job_index'] is None and job==21]
 assert {key(p) for p in required_output_paths}==set(sealed)
 completed_media_outputs={key(p) for aw in active for p in [*(g['output_path'] for g in aw['groups']),aw['proposal_path']]}
 for r in parsed(live[len(prefix):]):
  t=r.get('step_update',{})
  if t.get('step_type')=='tool' and t.get('tool_name')=='write_to_file':assert pathinfo(t)[1] not in completed_media_outputs,'LATER_WRITE_TO_SEALED_COMPLETED_OUTPUT'
 # Final CPU race check; no prefix/output is overwritten or synthesized.
 assert (c/'stream.jsonl').read_bytes().startswith(prefix)
 for x in sealed.values():assert sha(x['original_path'])==x['sha256'] and sha(x['sealed_copy_path'])==x['sealed_copy_sha256']
 out=dict(status='PASS_ROOT_BOUND_MANUAL38_IMMUTABLE_MEDIA_SCOPE_PENDING_SEMANTIC_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,global_CLI=38,ordered_actual_core_count=len(core),window_core_count=102,scope_core_counts=[104,206,308],actual_supply=a['actual_supply'],bound_fact_rows=ar['bound_fact_rows'],completed_text_fragments=textproof,prefix_audit=bind(ap),stream_prefix=a['immutable_prefix'],immutable_actual_outputs=a['immutable_actual_outputs'],proposal=proposal,freeze=bind(c/'freeze.json'),request=bind(c/'request.json'),admission=bind(V/'root_start_admission.json'),source_binding=bind(V/'execution_code_binding.json'),protocol=bind(V/'PROTOCOL.md'),strict_actual_engine_source=bind(V/'engine.py'),strict_actual_audit_source=bind(V/'audit.py'),existing_pixel_clock_success_binding=pixel_binding,root_verifier_source=bind(__file__),bare_error_metadata=a['bare_nonmedia_error_metadata'],successful_header_selfchecks=selfchecks,root_semantic_facts_read_not_asserted_by_this_helper=True,semantic_admission_pending=True,training_admitted=False,new_optimizer_updates=0,whole_CLI_status_not_inferred=True,parent_whole_status='UNKNOWN_NOT_INFERRED_FROM_SCOPE',parent_actual_terminal_if_present=bind(c/'terminal.json') if (c/'terminal.json').exists() else None,parent_whole_audit_if_present=bind(c/'audit.json') if (c/'audit.json').exists() else None,parent_actual_cost_if_present=bind(c/'actual_terminal_cost.json') if (c/'actual_terminal_cost.json').exists() else None,parent_terminal_at_original_scope_audit=a['parent_terminal_present'],whole_job_cost='ACTUAL_PARENT_COST_PRESERVED_SEPARATE_FROM_SCOPE' if (c/'actual_terminal_cost.json').exists() else 'PENDING_ACTUAL_PARENT_TERMINAL_COST_RECEIPT',cash_cost='UNKNOWN_NOT_ZERO',tool_issues=[],proposal_geometry_identity_issues=[])
 with output.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False)
 print(json.dumps(bind(output),ensure_ascii=False))
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job-index',type=int,choices=sorted(OUTPUTS),required=True);p.add_argument('--output');args=p.parse_args();accept(args.job_index,args.output)
