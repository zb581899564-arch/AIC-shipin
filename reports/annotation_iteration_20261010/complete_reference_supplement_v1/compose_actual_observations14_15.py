"""ROOT separate media composition; original CLI32 strict rejection is immutable."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent;C=R/'teacher_expansion/remaining_CLI32_36_literal_paths_v1/call06'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def norm(p):return str(Path(p).resolve()).casefold()
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
invp=C/'actual_media_completion_evidence_original_strict_failed.json';inv=read(invp);term=read(C/'terminal.json');audit=read(C/'audit.json');idx=read(C/'index.json')
assert inv['original_strict_failure_preserved'] and term['exit_code']==0 and audit['actual_result_status']=='SUCCESS'
assert all(w['status']=='REJECTED_OR_INCOMPLETE_KEEP_RAW' for w in audit['windows'])
assert sha(C/'stream.jsonl')==term['stream_sha256']
for p,h in read(C/'freeze.json')['inputs'].items():assert sha(p)==h
steps={}
for line in (C/'stream.jsonl').read_text(encoding='utf-8').splitlines():
 d=json.loads(line)
 if d.get('event')=='step_update':steps[d['step_update']['step_index']]=d['step_update']
tools=[s for _,s in sorted(steps.items()) if s['step_type']=='tool'];assert all(s['state']=='DONE' for s in tools)
actual=[];indexreads=[]
for s in tools:
 p=s['tool_info']['parameters'];item=(s['tool_name'],norm(p.get('AbsolutePath') or p.get('TargetFile')))
 if item==('view_file',norm(C/'index.json')):
  indexreads.append(s['step_index'])
  if len(indexreads)>1:continue
 actual.append(item)
expected=[('view_file',norm(C/'index.json'))]
for w in idx['windows']:
 for g in w['groups']:
  expected.extend(('view_file',norm(f['path'])) for f in g['frames']);expected.append(('write_to_file',norm(g['output_path'])))
 expected.append(('view_file',norm(w['clip_path'])))
 expected.extend(('view_file',norm(f['path'])) for f in w['student_previews'])
 expected.append(('write_to_file',norm(w['proposal_path'])))
assert actual==expected and len(expected)==181 and len(tools)==191 and len(indexreads)==11
metadata={'conversation_id','step_index','state','step_type','duration_seconds'}
bare=[s for s in steps.values() if s['step_type']=='error_message']
assert len(bare)==3
for s in bare:assert not any(k not in metadata and v not in (None,'',{},[]) for k,v in s.items())
protocol=R/'14_15_root_actual_media_composition_protocol_v1.json'
save(protocol,dict(status='ROOT_EXPLICIT_SEPARATE_MEDIA_COMPOSITION_ORIGINAL_CLI32_STRICT_FAILED_UNCHANGED',utc=datetime.now(timezone.utc).isoformat(),
 original_protocol_authority=bind(R/'teacher_expansion/readonly_protocol_composed_media_inquiry_CLI31.json'),original_strict_audit=bind(C/'audit.json'),
 actual_media_inventory=bind(invp),original_terminal=bind(C/'terminal.json'),original_raw=bind(C/'stream.jsonl'),
 rationale='Original project protocol allows actual observations reused with separately adjudicated complete references. This separate composition accepts only the actually delivered native64/video/effective8 and real fact/proposal files; harmless same frozen index rereads are individually recorded as metadata, not media. Original exact181/191 strict failure, bare metadata and costs are immutable and never reclassified.',
 original_failed_tasks=[14,15],actual_index_read_steps=indexreads,actual_bare_nonmedia_metadata=bare,
 no_original_failure_reclassified=True,no_AGY_retry=True,no_new_media=True,no_decoder=True,no_model=True,
 candidate_prediction_exposure=False,training_admitted=False,evaluation_only=True))
for w,tag in zip(idx['windows'],['14_i3w_w02','15_i3w_w03']):
 n=w['job_index'];bp=C/f'w{n:02d}_program_bound_facts.json';rows=read(bp)['rows'];assert len(rows)==64
 for row in rows:
  g=w['groups'][row['group']];f=g['frames'][row['slot']]
  assert row['source_ordinal']==f['source_ordinal'] and row['png_sha256']==sha(f['path'])==f['png_sha256']
  assert row['facts']==read(g['output_path'])['items'][row['slot']] and row['raw_output_sha256']==sha(g['output_path'])
  assert row['identity_generated_by_program']
  with Image.open(f['path']) as im:assert list(im.size)==f['geometry']
 pre=read(R/(tag+'_main_preteacher_review.json'));receipt=Path(read(pre['independent_native64']['path'])['job'])/'student_views/receipt.json';sr=read(receipt)
 assert sr['patch_inverse_exact'] and len(sr['frames'])==64
 for f in w['student_previews']:
  row=next(v for v in sr['frames'] if v['frame_id']==f['frame_id'])
  assert sha(f['path'])==f['png_sha256']==row['png_sha256']
  with Image.open(f['path']) as im:
   assert list(im.size)==f['geometry'];assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==row['rgb_pixel_sha256']
 original=next(v for v in audit['windows'] if v['job_index']==n);assert not original['schema_issues'] and not original['proposal_issues']
 op=R/(tag+'_composed_observation_completion.json')
 save(op,dict(status='PASS_NEW_ROOT_COMPOSED_ACTUAL_MEDIA_PENDING_SEMANTIC_EVALUATION_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],
  original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,tool_issues=[],proposal_geometry_identity_issues=[],
  media_observers=dict(native64='GEMINI_REAL_CLI32_DONE',native_video='GEMINI_REAL_CLI32_DONE',effective8='GEMINI_REAL_CLI32_DONE'),
  original_Gemini_strict_task_completed=False,original_strict_failure_preserved=True,original_strict_audit=bind(C/'audit.json'),
  actual_media_inventory=bind(invp),protocol=bind(protocol),original_raw=bind(C/'stream.jsonl'),original_terminal=bind(C/'terminal.json'),
  program_bound_facts=bind(bp),proposal=bind(w['proposal_path']),index=bind(C/'index.json'),freeze=bind(C/'freeze.json'),student_processor=bind(receipt),
  actual_same_index_reads_not_media=indexreads,actual_bare_nonmedia_metadata=bare,root_new_images=0,new_model_calls=0,new_optimizer_updates=0,training_admitted=False))
 print(json.dumps(bind(op),ensure_ascii=False))

