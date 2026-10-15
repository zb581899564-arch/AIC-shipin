"""Read-only actual supply inventory; retains original strict rejection."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
BASE=Path(__file__).resolve().parent
A=BASE/'remaining_CLI32_36_literal_paths_v1/call06'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold()
def ref(p):return dict(path=str(p),sha256=sha(p))
idx=read(A/'index.json');fr=read(A/'freeze.json');audit=read(A/'audit.json');terminal=read(A/'terminal.json')
assert sha(A/'stream.jsonl')==terminal['stream_sha256']
rows=[json.loads(line) for line in (A/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
tools=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool']
last={t['step_index']:t for t in tools}
done=[t for t in last.values() if t['state']=='DONE']
def path(t):
 p=t.get('tool_info',{}).get('parameters',{});return key(p.get('AbsolutePath') or p.get('TargetFile'))
def steps(name,p):return [t['step_index'] for t in done if t.get('tool_name')==name and path(t)==key(p)]
input_drift=[p for p,s in fr['inputs'].items() if sha(p)!=s]
allowed={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']+fr['write_whitelist']}
outside=[t for t in last.values() if path(t) not in allowed or t.get('tool_name') not in ('view_file','write_to_file')]
windows=[]
for w in idx['windows']:
 report=next(r for r in audit['windows'] if r['job_index']==w['job_index'])
 native=[];preview=[];sequence=[]
 for g in w['groups']:
  for f in g['frames']:
   assert sha(f['path'])==f['png_sha256']
   native.append(dict(identity=f,actual_current_png_sha256=sha(f['path']),DONE_tool_steps=steps('view_file',f['path'])))
   sequence.extend(steps('view_file',f['path']))
  sequence.extend(steps('write_to_file',g['output_path']))
 sequence.extend(steps('view_file',w['clip_path']))
 for f in w['student_previews']:
  preview.append(dict(identity=f,actual_current_png_sha256=sha(f['path']),DONE_tool_steps=steps('view_file',f['path'])))
  sequence.extend(steps('view_file',f['path']))
 sequence.extend(steps('write_to_file',w['proposal_path']))
 windows.append(dict(job_index=w['job_index'],window_id=w['window_id'],original_strict_status=report['status'],original_strict_failed=True,
  native=native,clip=dict(path=w['clip_path'],actual_current_sha256=sha(w['clip_path']),DONE_tool_steps=steps('view_file',w['clip_path'])),student_previews=preview,
  fact_outputs=[dict(group=g['group'],path=g['output_path'],sha256=sha(g['output_path']),DONE_tool_steps=steps('write_to_file',g['output_path'])) for g in w['groups']],
  proposal=dict(path=w['proposal_path'],sha256=sha(w['proposal_path']),DONE_tool_steps=steps('write_to_file',w['proposal_path'])),
  original_program_bound_facts=ref(A/f"w{w['job_index']:02d}_program_bound_facts.json"),
  media_and_output_sequence_steps=sequence,media_and_output_sequence_increasing=sequence==sorted(sequence),
  native64_each_exactly_once=all(len(f['DONE_tool_steps'])==1 for f in native),preview8_each_exactly_once=all(len(f['DONE_tool_steps'])==1 for f in preview),
  original_schema_issues=report['schema_issues'],original_proposal_issues=report['proposal_issues'],semantic_correctness='UNVERIFIED_ROOT_DECISION_REQUIRED',training_admitted=False))
error_metadata=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message']
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_MEDIA_INVENTORY_ONLY_ORIGINAL_STRICT_FAILED_NOT_ADMISSION',
 CLI=32,terminal=ref(A/'terminal.json'),raw=ref(A/'stream.jsonl'),freeze=ref(A/'freeze.json'),index=ref(A/'index.json'),original_strict_audit=ref(A/'audit.json'),
 readonly_step1_diagnosis=ref(A/'step1_nonmedia_metadata_readonly_diagnosis.json'),
 original_strict_failure_preserved=True,original_strict_tool_issues=audit['tool_issues'],windows=windows,
 same_index_DONE_steps=steps('view_file',A/'index.json'),actual_tool_ERROR=[t for t in last.values() if t['state']=='ERROR'],
 actual_unfinished_tools=[t for t in last.values() if t['state']=='ACTIVE'],outside_whitelist_or_tool_attempts=outside,input_SHA_drift=input_drift,
 nonmedia_error_message_metadata=error_metadata,nonmedia_metadata_cause='UNKNOWN_NO_BODY_IN_ACTUAL_STREAM',
 no_teacher_rerun=True,no_new_media_observation=True,no_decoder=True,no_semantic_or_combined_reference_created=True,cash_cost='UNKNOWN_NOT_ZERO')
p=A/'actual_media_completion_evidence_original_strict_failed.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(receipt=ref(p),windows=[dict(job_index=w['job_index'],native64_once=w['native64_each_exactly_once'],preview8_once=w['preview8_each_exactly_once'],order=w['media_and_output_sequence_increasing']) for w in windows],index_reads=len(out['same_index_DONE_steps']),input_drift=len(input_drift),outside=len(outside),media_errors=len(out['actual_tool_ERROR'])),ensure_ascii=False))
