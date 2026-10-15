"""Bind actual Gemini native/video and separately observed root effective images.
The original Gemini eight ERROR attempts and absent proposal stay rejected.
This is a new, explicitly composed evaluation observation, not repaired CLI success.
"""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent; C=R/'teacher_expansion/capacity_v4_tool_batches/call05'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def norm(p):return str(Path(p).resolve()).casefold()
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
idx=read(C/'index.json');w=idx['windows'][1];assert w['job_index']==13
for p,h in read(C/'freeze.json')['inputs'].items():assert sha(p)==h
steps={}
for line in (C/'stream.jsonl').read_text(encoding='utf-8').splitlines():
 d=json.loads(line)
 if d.get('event')=='step_update':steps[d['step_update']['step_index']]=d['step_update']
tools=[s for _,s in sorted(steps.items()) if s['step_type']=='tool']
done=[];errors=[]
for s in tools:
 p=s['tool_info']['parameters'];item=(s['tool_name'],norm(p.get('AbsolutePath') or p.get('TargetFile')))
 if s['state']=='DONE':done.append(item)
 elif s['state']=='ERROR':errors.append(dict(step=s['step_index'],tool=s['tool_name'],path=item[1],state='ERROR'))
 else:raise AssertionError('Nonterminal tool remains')
expected=[('view_file',norm(C/'index.json'))]
for window in idx['windows']:
 for g in window['groups']:
  for f in g['frames']:expected.append(('view_file',norm(f['path'])))
  expected.append(('write_to_file',norm(g['output_path'])))
 expected.append(('view_file',norm(window['clip_path'])))
 if window['job_index']==12:
  expected.extend(('view_file',norm(f['path'])) for f in window['student_previews'])
  expected.append(('write_to_file',norm(window['proposal_path'])))
assert done==expected and len(done)==172 and len(errors)==8
assert not Path(w['proposal_path']).exists()
for error,f in zip(errors,w['student_previews']):
 assert error['path']==norm(Path(f['path']).parent.parent/'student_previews'/Path(f['path']).name)
rows=read(C/'w13_program_bound_facts.json')['rows'];assert len(rows)==64
for row in rows:
 g=w['groups'][row['group']];f=g['frames'][row['slot']]
 assert row['source_ordinal']==f['source_ordinal'] and row['png_sha256']==sha(f['path'])==f['png_sha256']
 assert row['identity_generated_by_program'] and row['raw_output_sha256']==sha(g['output_path'])
 assert row['facts']==read(g['output_path'])['items'][row['slot']]
 with Image.open(f['path']) as im:assert list(im.size)==f['geometry']
pre=read(R/'13_esjr_w06_main_preteacher_review.json')
student_receipt=Path(read(pre['independent_native64']['path'])['job'])/'student_views/receipt.json'
sr=read(student_receipt);assert len(sr['frames'])==64 and sr['patch_inverse_exact']
facts=[
 '橘条纹猫侧卧棕椅，四肢叠放向左，头朝镜头，右浅色椅背、左后木地板线缆；没有手。',
 '同一橘猫侧躺椅，头朝镜头、眼半开，爪叠放左侧；左下尾端露出，没有手。',
 '橘猫同侧躺椅，脸朝镜头、眼半开，左侧爪叠放，没有手。',
 '更近的侧卧猫头、侧腹和左爪，右浅色椅背，未见手。',
 '人手四指贴在侧卧猫的侧胸腹毛上，猫头朝左、眼较闭，左侧爪叠放；单图不证明抚摸方向或情绪。',
 '木地板上左白盆、蓝桶白座和颗粒粮槽，右下花纹圆盘内褐色残块，右柜角；无猫手。',
 '花纹盘仍在画面下方、部分出边，褐色残块可见，白粮槽与蓝桶在左上；未见端起或撤走的证据。',
 '花纹盘、褐色残块与白粮槽近景，左上蓝桶局部，木地板和柜角，无手猫。']
bound=[]
for f,fact in zip(w['student_previews'],facts):
 frame=next(x for x in sr['frames'] if x['frame_id']==f['frame_id'])
 assert sha(f['path'])==f['png_sha256']==frame['png_sha256']
 with Image.open(f['path']) as im:
  assert list(im.size)==f['geometry'];pixel=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
 assert pixel==frame['rgb_pixel_sha256']
 bound.append({**f,'fresh_root_static_fact':fact,'rgb_pixel_sha256':pixel,'observer':'ROOT_GPT','actual_view_image_detail':'original','actual_image_returned_and_semantically_read':True})
protocol=R/'13_esjr_w06_composed_observation_protocol_v1.json'
save(protocol,dict(status='ROOT_EXPLICIT_SEPARATELY_OBSERVED_MEDIA_COMPOSITION_NOT_ORIGINAL_TEACHER_SUCCESS',utc=datetime.now(timezone.utc).isoformat(),
 window_id=w['window_id'],authority=bind(R/'teacher_expansion/readonly_protocol_composed_media_inquiry_CLI31.json'),
 original_failed_attempt=bind(C/'engineering_wrong_preview_paths_CLI31.json'),
 original_terminal=bind(C/'terminal.json'),original_raw=bind(C/'stream.jsonl'),
 same_native64_and_video_original_Gemini_DONE=True,root_effective8_observer_distinct=True,
 original_Gemini_preview8_ERROR_retained=True,original_Gemini_proposal_absent=True,
 no_original_failure_reclassified=True,no_AGY_retry=True,no_new_decoder=True,
 evaluation_only=True,training_admitted=False,candidate_prediction_exposure=False,
 rationale='Original project protocol permits reuse of actual observations and separately adjudicated complete lists. Original teacher v4 same-instance pipeline failed. This new evaluation observation combines only its real native64/video DONE supply with root actual original effective8 images. Identity/geometry are verified independently; teacher semantics are never automatic targets.'))
preview=R/'13_esjr_w06_root_effective8_actual_observation.json'
save(preview,dict(status='ACTUAL_ROOT_ORIGINAL_EFFECTIVE8_OBSERVED_NOT_GEMINI',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],
 protocol=bind(protocol),student_processor=bind(student_receipt),rows=bound,
 first_attempt_four_image_output_truncated_not_counted=True,successful_reviews_resupplied_in_batches_at_most_two=True,
 root_not_blind=True,root_did_not_watch_native_clip=True,root_read_teacher_static_facts=64,
 additional_native_disagreement_views=[53,54,55],training_admitted=False))
completion=R/'13_esjr_w06_composed_observation_completion.json'
save(completion,dict(status='PASS_NEW_COMPOSED_ACTUAL_MEDIA_PENDING_SEMANTIC_EVALUATION_REFERENCE',utc=datetime.now(timezone.utc).isoformat(),window_id=w['window_id'],
 original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,
 media_observers=dict(native64='GEMINI_REAL_CLI31_DONE',native_video='GEMINI_REAL_CLI31_DONE',effective8='ROOT_ACTUAL_ORIGINAL_PNG_REVIEW'),
 tool_issues=[],proposal_geometry_identity_issues=[],original_Gemini_errors_preserved=errors,
 original_Gemini_task_completed=False,original_Gemini_proposal_absent=True,
 protocol=bind(protocol),root_effective8=bind(preview),original_raw=bind(C/'stream.jsonl'),
 program_bound_facts=bind(C/'w13_program_bound_facts.json'),index=bind(C/'index.json'),freeze=bind(C/'freeze.json'),
 no_failed_tools_counted_as_media=True,new_optimizer_updates=0,new_model_calls=0,training_admitted=False))
print(json.dumps(bind(completion),ensure_ascii=False))
