"""ROOT independent exact actual supply reconstruction, never semantic labels."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import argparse,json,hashlib,re
from PIL import Image
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def key(p):return str(Path(p).resolve()).casefold()
def pixels(f):
 assert sha(f['path'])==f['png_sha256']
 with Image.open(f['path']) as im:
  assert list(im.size)==f['geometry']
  assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==f['rgb_pixel_sha256']
def facts(doc,g):
 assert set(doc)=={'group','items'} and doc['group']==g and len(doc['items'])==4
 assert [v['slot'] for v in doc['items']]==list(range(4))
 for item in doc['items']:
  assert set(item)=={'slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'}
  assert all(isinstance(item[k],str) and item[k].strip() for k in ('subject','composition','visible_fact'))
 return doc['items']
def accept(n,job,output):
 c=V/f'call{n}';ap=c/f'w{job:02d}_completed_scope_audit.json';a=read(ap)
 assert a['status']=='ACTUAL_SCOPE_SUPPLY_AUDIT_ONLY_PENDING_ROOT_REVIEW'
 representation_reasons={'BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE','BOOTSTRAP_ACK_MISSING_WRONG_OR_ORDER'}
 assert a['tool_issues'] and {v['reason'] for v in a['tool_issues']}==representation_reasons
 assert all(v.get('job_index') is None for v in a['tool_issues'])
 assert not a['errored_tool_attempts'] and not a['unfinished_tool_attempts']
 assert not a['reported_nonmedia_errors']
 idx=read(c/'index.json');fr=read(c/'freeze.json');req=read(c/'request.json')
 assert req['model']=='gemini-3.8-flash-high' and req['CLI_after']==n and 34<=n<=36
 assert req['freeze_sha256']==sha(c/'freeze.json')
 assert req['root_start_admission_sha256']==sha(V/'root_start_admission.json')
 assert fr['protocol_sha256']==sha(V/'PROTOCOL.md') and fr['global_cap']==36 and fr['timeout_seconds']==7200 and not fr['automatic_retry']
 for p,h in fr['inputs'].items():assert sha(p)==h,p
 prefix=Path(a['immutable_prefix']['path']).read_bytes()
 assert sha(a['immutable_prefix']['path'])==a['immutable_prefix']['sha256'] and len(prefix)==a['immutable_prefix']['bytes']
 assert (c/'stream.jsonl').read_bytes().startswith(prefix)
 states={};bare=[];allowedmeta={'conversation_id','step_index','state','step_type','duration_seconds'}
 for row in map(json.loads,prefix.splitlines()):
  st=row.get('step_update')
  if not st:continue
  if st.get('step_type')=='tool':
   assert st.get('state')!='ERROR'
   states[st['step_index']]=st
  elif st.get('step_type')=='error_message':
   body={k:v for k,v in st.items() if k not in allowedmeta and v not in (None,'',{},[])}
   assert not body,st
   bare.append(st)
 tools=[t for _,t in sorted(states.items())]
 assert tools and all(t['state']=='DONE' for t in tools)
 boot=idx['bootstrap_instruction_path'];ackp=idx['bootstrap_ack_path']
 ackexpected=read(idx['bootstrap_ack_expected_path'])
 assert idx['bootstrap_ack_expected_path'] not in fr['read_whitelist']
 assert ackp not in fr['self_read_whitelist']
 assert read(ackp)==ackexpected
 assert not Path(output).exists() and Path(output).parent==R
 wl=set(map(key,fr['read_whitelist']+fr['self_read_whitelist']));ww=set(map(key,fr['write_whitelist']))
 core=[];indexes=[];selfreads=[];written=set();selfcount={}
 for t in tools:
  name=t['tool_name'];params=t['tool_info']['parameters']
  assert name in ('view_file','write_to_file')
  p=key(params.get('AbsolutePath') or params.get('TargetFile'))
  assert p in (wl if name=='view_file' else ww),(name,p)
  assert not any(x in str(t['tool_info'].get('output','')).lower() for x in ('not found','cannot read','error reading','failed to'))
  if name=='view_file' and p==key(c/'index.json'):
   indexes.append(t['step_index'])
   if len(indexes)>1:continue
  if name=='view_file' and p in written:
   selfcount[p]=selfcount.get(p,0)+1;assert selfcount[p]==1
   selfreads.append(dict(step=t['step_index'],path=p));continue
  if name=='write_to_file':assert p not in written;written.add(p)
  core.append((name,p))
 expected=[('view_file',key(boot)),('write_to_file',key(ackp)),('view_file',key(c/'index.json'))]
 active=[]
 for w in idx['windows']:
  active.append(w)
  if w.get('prior_context_path'):expected.append(('view_file',key(w['prior_context_path'])))
  for g in w['groups']:
   expected += [('view_file',key(f['path'])) for f in g['frames']]
   expected.append(('write_to_file',key(g['output_path'])))
  expected.append(('view_file',key(w['clip_path'])))
  expected += [('view_file',key(f['path'])) for f in w['student_previews']]
  expected.append(('write_to_file',key(w['proposal_path'])))
  if w['job_index']==job:break
 assert active[-1]['job_index']==job and core==expected,(len(core),len(expected))
 bootsteps=[t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters'].get('AbsolutePath',''))==key(boot)]
 assert len(bootsteps)==1 and tools[0]==bootsteps[0] and set(bootsteps[0]['tool_info']['parameters'])=={'AbsolutePath'}
 text=str(bootsteps[0]['tool_info'].get('output',''))
 byte_report=re.search(r'(\d+) bytes',text);line_report=re.search(r'(\d+) lines',text)
 assert byte_report and int(byte_report.group(1))==Path(boot).stat().st_size
 boot_bytes=Path(boot).read_bytes()
 assert boot_bytes.endswith(b'\n') and b'\r' not in boot_bytes
 assert line_report and int(line_report.group(1))==len(boot_bytes.split(b'\n'))
 assert not any(t in text.lower() for t in ('truncat','not found','cannot read','failed','error'))
 assert tools[1]['tool_name']=='write_to_file' and key(tools[1]['tool_info']['parameters']['TargetFile'])==key(ackp)
 w=active[-1];ar=a['windows'][-1]
 assert ar['job_index']==job and ar['status']=='REJECTED_OR_INCOMPLETE_KEEP_RAW' and ar['bound_rows']==64
 assert not ar['schema_issues'] and not ar['proposal_issues']
 assert {v['reason'] for v in ar['local_tool_issues']}==representation_reasons
 prior={}
 if w.get('prior_context_path'):
  pr=read(w['prior_facts_provenance_path']);package=read(w['prior_context_path'])
  prior={g['group']:g for g in package['groups']}
  assert sorted(prior)==list(range(8)) and pr['actual_native32_DONE']==32 and pr['actual_fact_groups8_DONE']==8
  assert pr['original_CLI33_strict_failed_preserved'] and pr['old_group8_not_successful'] and pr['old_F35_actual_DONE_steps']==[193]
  oldprefix=Path(pr['immutable_prior32_prefix']['path']).read_bytes()
  assert sha(pr['immutable_prior32_prefix']['path'])==pr['immutable_prior32_prefix']['sha256']
  assert Path(pr['original_CLI33_raw']['path']).read_bytes().startswith(oldprefix)
  oldstates={}
  for row in map(json.loads,oldprefix.splitlines()):
   t=row.get('step_update',{})
   if t.get('step_type')=='tool':assert t.get('state')!='ERROR';oldstates[t['step_index']]=t
  assert all(t['state']=='DONE' for t in oldstates.values())
  oldwant=[];oldpaths=set()
  for g in pr['groups']:
   assert sha(g['facts']['path'])==g['facts']['sha256']
   assert prior[g['group']]==read(g['facts']['path'])
   for f in g['native_reads']:
    oldwant.append(('view_file',key(f['identity']['path'])));oldpaths.add(key(f['identity']['path']))
   oldwant.append(('write_to_file',key(g['facts']['path'])));oldpaths.add(key(g['facts']['path']))
  actual=[]
  for _,t in sorted(oldstates.items()):
   pp=t['tool_info']['parameters'];p=key(pp.get('AbsolutePath') or pp.get('TargetFile'))
   if p in oldpaths:actual.append((t['tool_name'],p))
  assert actual==oldwant and len(actual)==40
 fresh={g['group']:g for g in w['groups']};boundrows=ar['bound_fact_rows'];frozen=w['native_identity_all64']
 assert len(boundrows)==len(frozen)==64
 for i,(r,f) in enumerate(zip(boundrows,frozen)):
  assert f['frame_id']==f'F{i:02d}' and r['identity']==f and r['identity_generated_by_program']
  original=dict(f,path=f['original_path']);pixels(original)
  doc=prior[i//4] if i//4 in prior else read(fresh[i//4]['output_path'])
  assert r['facts']==facts(doc,i//4)[i%4]
  if i//4 not in prior:
   alias=fresh[i//4]['frames'][i%4];assert Path(alias['path']).read_bytes()==Path(f['original_path']).read_bytes()
   assert len([t for t in core if t==('view_file',key(alias['path']))])==1
  assert sha(r['raw_fact_output']['path'])==r['raw_fact_output']['sha256']
 receipt=read(w['original_student_receipt']['path'])
 assert sha(w['original_student_receipt']['path'])==w['original_student_receipt']['sha256'] and receipt['patch_inverse_exact'] and len(receipt['frames'])==64
 frames={f['frame_id']:f for f in receipt['frames']}
 for f in w['student_previews']:
  pixels(f);assert Path(f['path']).read_bytes()==Path(f['original_path']).read_bytes()
  sf=frames[f['frame_id']]
  for field in ('png_sha256','rgb_pixel_sha256','source_ordinal'):assert sf[field]==f[field]
 manifest=read(w['original_source_manifest']['path'])
 assert sha(w['original_source_manifest']['path'])==w['original_source_manifest']['sha256']
 assert sha(w['clip_path'])==manifest['clip_sha256']==sha(w['original_clip_path'])
 assert sha(w['original_source_manifest']['native_clock']['path'])==w['original_source_manifest']['native_clock']['sha256']
 proposal=read(w['proposal_path']);cursor=F(0)
 assert set(proposal)=={'segments','events','student_visibility','limitations'}
 for seg in proposal['segments']:
  assert seg['decision'] in ('KEEP','NO','UNKNOWN') and F(str(seg['start_seconds']))==cursor
  stop=F(str(seg['end_seconds']));assert cursor<stop<=F(w['domain_local_seconds'][1]);cursor=stop
  for f in seg['fact_support']:assert set(f)=={'group','slot'} and f['group'] in range(16) and f['slot'] in range(4)
 assert cursor==F(w['domain_local_seconds'][1])
 out=dict(status='PASS_ROOT_INDEPENDENT_BOOTSTRAP_FIXED_SCOPE_MEDIA_PENDING_SEMANTIC_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,original_pngs_delivered_in_current_CLI=sum(len(g['frames']) for g in w['groups']),prior_native32_and_raw_facts_transferred=len(prior)*4,prior_CLI33_strict_failure_preserved=bool(prior),old_F35_extra_successful_read_without_group8_fact_preserved=bool(prior),current_F35_read_DONE_verified=bool(prior),tool_issues=[],proposal_geometry_identity_issues=[],prefix_audit=bind(ap),stream_prefix=a['immutable_prefix'],proposal=bind(w['proposal_path']),freeze=bind(c/'freeze.json'),request=bind(c/'request.json'),protocol=bind(V/'PROTOCOL.md'),bootstrap_instruction=bind(boot),bootstrap_ack=bind(ackp),bootstrap_ack_is_finite_text_route_check_not_all_text_attention_proof=True,ordered_actual_core_with_context_count=len(core),same_index_read_steps=indexes,successful_output_self_reads=selfreads,bare_error_metadata=bare,whole_CLI_status_not_inferred=True,parent_terminal_at_original_scope_audit=a['parent_terminal_present'],whole_job_cost='PENDING_ACTUAL_PARENT_TERMINAL',cash_cost='UNKNOWN_NOT_ZERO',global_CLI=n,root_semantic_facts_read_not_asserted_by_this_helper=True,semantic_admission_pending=True,training_admitted=False,new_optimizer_updates=0)
 out.update(original_frozen_scope_audit_status='REJECTED_OR_INCOMPLETE_KEEP_RAW',original_frozen_tool_issues_preserved=a['tool_issues'],root_verifier_source=bind(__file__),representation_correction=dict(kind='EXACT_TRAILING_LF_LINE_REPRESENTATION_ONLY',actual_reported_lines=int(line_report.group(1)),actual_reported_bytes=int(byte_report.group(1)),python_splitlines=len(boot_bytes.splitlines()),exact_LF_split_count=len(boot_bytes.split(b'\n')),ends_with_LF=True,no_tolerance_or_media_requirement_relaxation=True,old_v4_audit_source_and_results_not_modified=True),root_independent_actual_supply_order_pixels_native_fact_bindings_ACK_checked=True)
 with Path(output).open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(bind(output),ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--call',type=int,required=True);p.add_argument('--job-index',type=int,required=True);p.add_argument('--output',required=True);args=p.parse_args()
 accept(args.call,args.job_index,Path(args.output))

