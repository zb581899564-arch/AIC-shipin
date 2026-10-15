"""Root verifies the immutable successful first-scope supply, not the active parent."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent; C=R/'teacher_expansion/capacity_v4_tool_batches/call04'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def norm(p):return str(Path(p).resolve()).casefold()
a=read(C/'w10_completed_scope_audit.json')
assert a['status']=='PASS_ACTUAL_COMPLETED_SCOPE_TOOL_STRUCTURE_PENDING_ROOT_REVIEW' and not a['issues'] and not a['error_message_steps']
for name in ('proposal','program_bound_facts','stream_prefix','freeze','index','request'):
 assert sha(a[name]['path'])==a[name]['sha256']
for p,h in read(a['freeze']['path'])['inputs'].items():assert sha(p)==h
w=read(a['index']['path'])['windows'][0];assert w['job_index']==10
steps={}
for line in Path(a['stream_prefix']['path']).read_text(encoding='utf-8-sig').splitlines():
 d=json.loads(line)
 if d.get('event')=='step_update':steps[d['step_update']['step_index']]=d['step_update']
tools=[]
for ix,s in sorted(steps.items()):
 if s['step_type']!='tool':continue
 assert s['state']=='DONE' and s['tool_name'] in ('view_file','write_to_file')
 p=s['tool_info']['parameters'];tools.append((s['tool_name'],norm(p.get('AbsolutePath') or p.get('TargetFile'))))
expected=[('view_file',norm(C/'index.json'))]
for g in w['groups']:
 for f in g['frames']:
  assert sha(f['path'])==f['png_sha256']
  with Image.open(f['path']) as im:assert list(im.size)==f['geometry']
  expected.append(('view_file',norm(f['path'])))
 expected.append(('write_to_file',norm(g['output_path'])))
expected.append(('view_file',norm(w['clip_path'])))
for f in w['student_previews']:
 assert sha(f['path'])==f['png_sha256']
 with Image.open(f['path']) as im:assert list(im.size)==f['geometry']
 expected.append(('view_file',norm(f['path'])))
expected.append(('write_to_file',norm(w['proposal_path'])))
assert tools==expected and len(tools)==91
rows=read(a['program_bound_facts']['path'])['rows'];assert len(rows)==64
for row in rows:
 g=w['groups'][row['group']];f=g['frames'][row['slot']]
 assert row['source_ordinal']==f['source_ordinal'] and row['png_sha256']==f['png_sha256']
 assert row['identity_generated_by_program'] is True and row['raw_output_sha256']==sha(g['output_path'])
 assert row['facts']==read(g['output_path'])['items'][row['slot']]
receipt=dict(status='PASS_ROOT_INDEPENDENT_COMPLETED_FIRST_SCOPE_MEDIA_PENDING_SEMANTIC_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),
 window_id=w['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,
 tool_issues=[],proposal_geometry_identity_issues=[],ordered_tool_count=91,prefix_audit=bind(C/'w10_completed_scope_audit.json'),
 stream_prefix=a['stream_prefix'],proposal=a['proposal'],program_bound_facts=a['program_bound_facts'],
 parent_terminal_at_original_scope_audit=a['parent_CLI_terminal_present'],whole_CLI_status_not_inferred=True,
 whole_job_cost='PENDING_ACTUAL_TERMINAL_AT_SCOPE_COMPLETION',cash_cost='UNKNOWN_NOT_ZERO',
 teacher64_static_facts_root_read=True,teacher_claim_of_audio_absence_not_used_as_evidence=True,
 student_bounded_reinspection_pending=True,semantic_admission_pending=True,training_admitted=False,new_optimizer_updates=0)
with (R/'10_byx_w02_lawful_observation_completion.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=receipt['status'],window_id=w['window_id'],training_admitted=False)))
