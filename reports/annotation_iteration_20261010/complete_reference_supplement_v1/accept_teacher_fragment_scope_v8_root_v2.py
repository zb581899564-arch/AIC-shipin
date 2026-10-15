"""ROOT reconstructs actual fragment/media supply; semantic review is separate."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
from PIL import Image
import json,hashlib,argparse,re
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold()
def bind(p):return dict(path=str(p),sha256=sha(p))
def pixels(f):
 assert sha(f['path'])==f['png_sha256']
 with Image.open(f['path']) as im:
  assert list(im.size)==f['geometry']
  assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==f['rgb_pixel_sha256']

def full_text_read(t,path):
 payload=Path(path).read_bytes();text=str(t['tool_info'].get('output',''))
 n=re.search(r'(\d+) bytes',text);lines=re.search(r'(\d+) lines',text)
 assert len(payload)<30000 and payload.endswith(b'\n') and b'\r' not in payload
 assert n and int(n.group(1))==len(payload) and lines and int(lines.group(1))==len(payload.split(b'\n'))
 assert not any(x in text.lower() for x in ('truncat','not found','cannot read','failed','error'))

def validate_all_updates(rows,fr):
 reads=set(map(key,fr['read_whitelist']+fr['self_read_whitelist']));writes=set(map(key,fr['write_whitelist']))
 identity={}
 for row in rows:
  t=row.get('step_update',{})
  if t.get('step_type')!='tool':continue
  assert t.get('state')!='ERROR'
  name=t.get('tool_name');params=t.get('tool_info',{}).get('parameters',{})
  assert name in ('view_file','write_to_file')
  if name=='view_file':
   assert set(params)=={'AbsolutePath'} and key(params['AbsolutePath']) in reads
  else:assert key(params.get('TargetFile')) in writes
  ident=(name,json.dumps(params,sort_keys=True,ensure_ascii=False))
  step=t['step_index']
  if step in identity:assert identity[step]==ident
  identity[step]=ident

def actual_same_response(rows,batch):
 assert len(batch)==4
 planning=[];done=[]
 for t in batch:
  step=t['step_index']
  active=[i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='ACTIVE']
  completed=[i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='DONE']
  assert active and completed and active[0]>=0 and active[0]<completed[0]
  prior=[i for i,r in enumerate(rows[:active[0]]) if r.get('step_update',{}).get('step_type')=='agent_response' and r['step_update'].get('state')=='DONE']
  assert prior
  planning.append(prior[-1]);done.append(completed[0])
 assert len(set(planning))==1
 return dict(planning_response=planning[0],native_DONE=done)

def accept(job,output):
 assert job in range(19,24)
 number=36 if job<21 else 37
 c=V/f'call{number}';ap=c/f'w{job:02d}_completed_scope_audit.json';a=read(ap)
 assert a['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
 assert not any(a[k] for k in ('tool_issues','additional_scope_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'))
 fr=read(c/'freeze.json');idx=read(c/'index.json');req=read(c/'request.json')
 assert req['CLI_after']==number and req['model']=='gemini-3.8-flash-high'
 assert req['freeze_sha256']==sha(c/'freeze.json') and req['root_start_admission_sha256']==sha(V/'root_start_admission.json')
 assert fr['global_cap']==37 and fr['timeout_seconds']==7200 and not fr['automatic_retry']
 for p,h in fr['inputs'].items():assert sha(p)==h,p
 prefix=Path(a['immutable_prefix']['path']).read_bytes()
 assert len(prefix)==a['immutable_prefix']['bytes'] and sha(a['immutable_prefix']['path'])==a['immutable_prefix']['sha256']
 assert (c/'stream.jsonl').read_bytes().startswith(prefix)
 for x in a['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
 rows=list(map(json.loads,prefix.splitlines()));validate_all_updates(rows,fr);states={};bare=[]
 for row in rows:
  assert row.get('event')!='result'
  t=row.get('step_update',{})
  if t.get('step_type')=='tool':assert t.get('state')!='ERROR';states[t['step_index']]=t
  if t.get('step_type')=='error_message':
   body={k:v for k,v in t.items() if k not in {'conversation_id','step_index','state','step_type','duration_seconds'} and v not in (None,'',{},[]) and not(isinstance(v,str) and not v.strip())}
   assert not body;bare.append(t)
 tools=[t for _,t in sorted(states.items())];assert all(t['state']=='DONE' for t in tools)
 parts={p['part_id']:p for p in idx['text_fragments']};active=[]
 for w in idx['windows']:
  active.append(w)
  if w['job_index']==job:break
 assert active[-1]['job_index']==job
 expected=[];required_parts=[]
 def part(pid):
  p=parts[pid];required_parts.append(p);expected.extend([('view_file',key(p['path'])),('write_to_file',key(p['ack_path']))])
 part(idx['main_fragment_id'])
 for w in active:
  part(w['header_fragment_id'])
  for g in w['groups']:
   if g['group']%4==0:part(w['native_fragment_ids'][g['group']//4])
   expected.extend(('view_file',key(f['path'])) for f in g['frames']);expected.append(('write_to_file',key(g['output_path'])))
  expected.append(('view_file',key(w['clip_path'])))
  expected.extend(('view_file',key(f['path'])) for f in w['student_previews']);expected.append(('write_to_file',key(w['proposal_path'])))
 reads=set(map(key,fr['read_whitelist']+fr['self_read_whitelist']));writes=set(map(key,fr['write_whitelist']))
 headers={key(p['path']):p for p in idx['text_fragments'] if p['kind']=='header'}
 core=[];written=set();seen=set();selfcount={};selfchecks=[]
 for t in tools:
  name=t['tool_name'];params=t['tool_info']['parameters'];p=key(params.get('AbsolutePath') or params.get('TargetFile'))
  assert name in ('view_file','write_to_file') and p in (reads if name=='view_file' else writes)
  if name=='view_file':assert set(params)=={'AbsolutePath'}
  text=str(t['tool_info'].get('output','')).lower()
  assert not any(x in text for x in ('not found','cannot read','error reading','failed to','content truncated'))
  if name=='view_file' and p in headers and p in seen and key(headers[p]['ack_path']) in written:
   full_text_read(t,p);selfchecks.append(dict(step=t['step_index'],path=p));continue
  if name=='view_file' and p in written:
   selfcount[p]=selfcount.get(p,0)+1;assert selfcount[p]==1;full_text_read(t,p);continue
  if name=='write_to_file':assert p not in written;written.add(p)
  core.append((name,p));seen.add(p)
 assert core==expected and len(core)==2+100*len(active)
 textproof=[]
 for p in required_parts:
  payload=Path(p['path']).read_bytes();assert len(payload)<30000 and payload.endswith(b'\n') and b'\r' not in payload
  views=[t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters'].get('AbsolutePath',''))==key(p['path'])]
  assert views and (p['kind']=='header' or len(views)==1)
  for t in views:
   text=str(t['tool_info'].get('output',''));n=re.search(r'(\d+) bytes',text);lines=re.search(r'(\d+) lines',text)
   assert n and int(n.group(1))==len(payload) and lines and int(lines.group(1))==len(payload.split(b'\n'))
   assert not any(x in text.lower() for x in ('truncat','not found','cannot read','failed','error'))
  actual=read(p['ack_path']);expect=read(p['expected_ACK_path'])
  assert actual==expect and key(p['expected_ACK_path']) not in reads and key(p['ack_path']) not in reads
  assert payload.decode('utf-8').rstrip().endswith(expect['marker'])
  i=tools.index(views[0]);assert tools[i+1]['tool_name']=='write_to_file' and key(tools[i+1]['tool_info']['parameters'].get('TargetFile',''))==key(p['ack_path'])
  ack=tools[i+1]
  def position(step,state):
   return next((j for j,row in enumerate(rows) if row.get('step_update',{}).get('step_type')=='tool' and row['step_update'].get('step_index')==step and row['step_update'].get('state')==state),-1)
  va=position(views[0]['step_index'],'ACTIVE');vd=position(views[0]['step_index'],'DONE')
  aa=position(ack['step_index'],'ACTIVE');ad=position(ack['step_index'],'DONE')
  assert 0<=va<vd<aa<ad
  response=[j for j,row in enumerate(rows[:aa]) if row.get('step_update',{}).get('step_type')=='agent_response' and row['step_update'].get('state')=='DONE']
  assert response and vd<response[-1]<aa
  textproof.append(dict(part_id=p['part_id'],input=bind(p['path']),ACK=bind(p['ack_path']),actual_view_steps=[t['step_index'] for t in views],required_bytes=len(payload),required_LF_lines=len(payload.split(b'\n'))))
 w=active[-1];ar=a['windows'][-1]
 assert ar['job_index']==job and ar['bound_rows']==64 and ar['status']=='PASS_TOOL_TEXT_AND_MEDIA_STRUCTURE_PENDING_ROOT_SEMANTIC'
 assert not any(ar[k] for k in ('schema_issues','proposal_issues','local_tool_issues'))
 assert len(w['groups'])==16 and len(w['native_identity_all64'])==64 and len(w['student_previews'])==8
 for i,(r,f) in enumerate(zip(ar['bound_fact_rows'],w['native_identity_all64'])):
  assert r['identity']==f and f['frame_id']==f'F{i:02d}' and r['identity_generated_by_program']
  pixels(dict(f,path=f['original_path']))
  g=w['groups'][i//4];alias=g['frames'][i%4];assert Path(alias['path']).read_bytes()==Path(f['original_path']).read_bytes()
  doc=read(g['output_path']);assert set(doc)=={'group','items'} and doc['group']==i//4 and len(doc['items'])==4
  assert [r['slot'] for r in doc['items']]==[0,1,2,3] and r['facts']==doc['items'][i%4]
  assert sha(r['raw_fact_output']['path'])==r['raw_fact_output']['sha256']
  assert r['tool_provenance']['four_image_barrier']['all_four_DONE_before_fact_planning_response']
  # Independently validate the barrier's raw positions and response ordering.
  b=r['tool_provenance']['four_image_barrier'];wp=b['fact_write_ACTIVE_raw_position'];rp=b['fact_planning_response_DONE_raw_position']
  assert rows[wp]['step_update']['state']=='ACTIVE' and rows[wp]['step_update']['tool_name']=='write_to_file'
  assert key(rows[wp]['step_update']['tool_info']['parameters']['TargetFile'])==key(g['output_path'])
  assert rows[rp]['step_update']['state']=='DONE' and rows[rp]['step_update']['step_type']=='agent_response'
  for step,pos in b['native_DONE_raw_positions'].items():
   assert 0<=pos<rp<wp and rows[pos]['step_update']['state']=='DONE' and rows[pos]['step_update']['step_index']==int(step)
 for group in w['groups']:
  batch=[next(t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters']['AbsolutePath'])==key(f['path'])) for f in group['frames']]
  actual_same_response(rows,batch)
 effective_batches=[]
 for first in (0,4):
  batch=[next(t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters']['AbsolutePath'])==key(f['path'])) for f in w['student_previews'][first:first+4]]
  effective_batches.append(actual_same_response(rows,batch))
 assert max(effective_batches[0]['native_DONE'])<effective_batches[1]['planning_response']
 proposal_step=next(t for t in tools if t['tool_name']=='write_to_file' and key(t['tool_info']['parameters']['TargetFile'])==key(w['proposal_path']))
 proposal_active=next(j for j,row in enumerate(rows) if row.get('step_update',{}).get('step_type')=='tool' and row['step_update'].get('step_index')==proposal_step['step_index'] and row['step_update'].get('state')=='ACTIVE')
 proposal_planning=[j for j,row in enumerate(rows[:proposal_active]) if row.get('step_update',{}).get('step_type')=='agent_response' and row['step_update'].get('state')=='DONE']
 assert proposal_planning and max(effective_batches[1]['native_DONE'])<proposal_planning[-1]<proposal_active
 receipt=read(w['original_student_receipt']['path']);assert sha(w['original_student_receipt']['path'])==w['original_student_receipt']['sha256']
 assert receipt['patch_inverse_exact'] and len(receipt['frames'])==64
 frames={f['frame_id']:f for f in receipt['frames']}
 for f in w['student_previews']:
  pixels(f);assert Path(f['path']).read_bytes()==Path(f['original_path']).read_bytes()
  for k in ('png_sha256','rgb_pixel_sha256','source_ordinal'):assert f[k]==frames[f['frame_id']][k]
 manifest=read(w['original_source_manifest']['path']);assert sha(w['original_source_manifest']['path'])==w['original_source_manifest']['sha256']
 assert sha(w['clip_path'])==manifest['clip_sha256']==sha(w['original_clip_path'])
 assert sha(w['original_source_manifest']['native_clock']['path'])==w['original_source_manifest']['native_clock']['sha256']
 proposal=read(w['proposal_path']);assert set(proposal)=={'segments','events','student_visibility','limitations'}
 cursor=F(0)
 for s in proposal['segments']:
  assert s['decision'] in ('KEEP','NO','UNKNOWN') and F(str(s['start_seconds']))==cursor
  cursor=F(str(s['end_seconds']));assert cursor>F(str(s['start_seconds'])) and cursor<=F(w['domain_local_seconds'][1])
  for f in s['fact_support']:assert set(f)=={'group','slot'} and type(f['group']) is int and f['group'] in range(16) and type(f['slot']) is int and f['slot'] in range(4)
 assert cursor==F(w['domain_local_seconds'][1])
 out=dict(status='PASS_ROOT_INDEPENDENT_FRAGMENT_SCOPE_MEDIA_PENDING_SEMANTIC_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,global_CLI=number,ordered_actual_core_count=len(core),completed_text_fragments=textproof,prefix_audit=bind(ap),stream_prefix=a['immutable_prefix'],proposal=bind(w['proposal_path']),freeze=bind(c/'freeze.json'),request=bind(c/'request.json'),protocol=bind(V/'PROTOCOL.md'),root_verifier_source=bind(__file__),bare_error_metadata=bare,successful_header_selfchecks=selfchecks,root_semantic_facts_read_not_asserted_by_this_helper=True,semantic_admission_pending=True,training_admitted=False,new_optimizer_updates=0,whole_CLI_status_not_inferred=True,parent_terminal_at_original_scope_audit=a['parent_terminal_present'],whole_job_cost='PENDING_ACTUAL_PARENT_TERMINAL',cash_cost='UNKNOWN_NOT_ZERO')
 out.update(tool_issues=[],proposal_geometry_identity_issues=[])
 assert output.parent==R
 serialized=json.dumps(out,ensure_ascii=False,indent=2)
 with output.open('x',encoding='utf-8') as f:f.write(serialized)
 print(json.dumps(bind(output),ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--job-index',required=True,type=int);p.add_argument('--output',required=True);a=p.parse_args();accept(a.job_index,Path(a.output))

