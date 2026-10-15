"""ROOT actual exposed adjudication of the unchanged four finite preteacher targets."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
pp=R/'22_yi4_w03_main_preteacher_review_v2.json';tp=R/'22_yi4_w03_lawful_observation_completion_CLI39_v1.json'
cp=R/'teacher_semantic_crosschecks_v1/22_Yi4Ij2NM7U4_W03.exposed_semantic_crosscheck_CLI39_v2.json'
rp=R/'schema_recovery_CLI39_final_selfread_root_recovery_v1.json'
pre,teacher,cross,recovery=map(read,[pp,tp,cp,rp])
assert pre['window_id']==teacher['window_id']==cross['window_id']==recovery['window_id']
assert not pre['teacher_content_read'] and not cross['candidatePredictionExposure']
assert teacher['global_CLI']==39 and teacher['ordered_actual_core_count']==128 and not teacher['tool_issues'] and not teacher['proposal_geometry_identity_issues']
assert recovery['old_whole_REJECTED_preserved'] and recovery['ROOT_actual_scope_independently_verified']
assert bind(cp)['sha256']=='49b45c3983763128bf587739268dfbde5ce03d892daf09ddba1d330ab7032422'
obs=R.parent/'slot6_silver24_v1/observations/22_Yi4Ij2NM7U4_W03/frames'
vp=R/'22_yi4_root_actual_postteacher_pixels_CLI39_v1.json'
pixels=dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_REVIEW_NOT_NEW_BLIND_INITIAL',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],
 actual_images=[dict(sample_index=i,image=bind(obs/f'F{i:02d}_O{o:06d}.png'),visible_static_fact=fact) for i,o,fact in
 [(31,2513,'Narrowed/closed eyes, drawn eyebrows, open mouth and a blurred raised hand; no pain, taste, cough or causal state established.'),
  (63,2879,'Two white onion parts on the board with a blurred knife above them; contact, cutting completion and whether parts are newly produced are not established.')]],
 root_direct64_image_review=False,root_video_view=False,candidate_prediction_exposure=False,training_admitted=False)
if vp.exists():
 previous=read(vp)
 assert {k:v for k,v in previous.items() if k!='utc'}=={k:v for k,v in pixels.items() if k!='utc'}
else:save(vp,pixels)
old=next(v for v in pre['complete_domain_editorial_decision_by_samples'] if v['first']==39 and v['last']==61)['reason']
d=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],
 candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,
 selected_preteacher_event_indices=[0,1,2,3],unknown_local_exact=[],consequential_unknowns=[],
 evidence=dict(preteacher_main_review=bind(pp),teacher_observation_audit=bind(tp),original_teacher_proposal=teacher['proposal'],
 original_teacher_bound_fact_audit=teacher['prefix_audit'],
 exposed_independent_semantic_crosscheck=bind(cp),root_actual_precompletion_pixels=bind(R/'22_yi4_root_actual_pixels_schema_recovery_v1.json'),
 root_actual_postteacher_pixels=bind(vp),actual_scope_engineering_recovery=bind(rp)),
 historical_NO_reason_corrections=[dict(first=39,last=61,original_reason=old,
 corrected_reason='F39..60为坐着戴墨镜/耳机、手持手机及普通嘴部或手部姿态；F61切回案板且刀接触被手臂遮挡。保留原NO范围，不声称讲话音频或实际切割。')],
 differences_adjudicated=pre['explicit_disagreements']+[
 'Teacher all64 original facts and proposal are preserved. F13 fully peeled on every side, F24..30 internal chewing/force, F31..37 taste, pain, endurance, coughing/vomiting and intention are not established by these static images and are excluded from the finite reference.',
 'The frozen four targets remain separate: partial skin/white surface display, mouth-contact/away-visible notch, finite face/hand/body postures, and the two already visible white parts beside the knife. They are representative image/editing targets, not a complete challenge, swallowing, recovery, actual cutting or completed cooking.',
 'Teacher 10..18 second challenge merger is rejected. Original broad 1/.6/.8/.7 second uncertainties and F38 support outside its18-second KEEP remain preserved. Final exact boundary ranges and midpoint choices are the preregistered independent ones, with no narrowing or target selection from candidate predictions.',
 'Original preteacher39..61 ordinary-NO reason is corrected from standing/knife wording to the actually observed sunglasses/earphones/phone scene and F61 occlusion. Original reason, range, allfour events and all boundary intervals are preserved.',
 'Full physical ingestion/recovery/knife-contact unknowns remain explicit in sealed initial reviews and final scope explanation. Those outcomes were outside the preteacher finite-image targets; they are not converted into completed physical events or excluded after model metrics.',
 'CLI39 completed128core media scope is accepted separately. Its naturalSUCCESS, single final proposal selfread, wholeREJECT and actual usage/cost remain bound. Scope integrity is not semantic truth or human gold.'
 ],
 actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],
 additional_precompletion_native_samples=[25,61],additional_postteacher_native_samples=[31,63],
 read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,root_direct64_image_review=False,root_native_video_view=False,
 teacher_actual_video_delivery=True,parent_whole_rejected_preserved=True),
 serializer_source_binding=bind(R/'finalize_eval_window_NO_note_v3.py'),
 reference_scope_and_reason='Locked-evaluation-only finite visual editorial silver. Four independently preregistered visible image/relationship targets with ordinary NO; no claims of taste, pain, swallowing, recovery, newly cut parts or full cooking completion. Physical-outcome unknowns stay in the bound original reviews and are outside these frozen image targets. Not human gold or training admission.')
out=R/'22_yi4_w03_root_eval_decision_CLI39_v1.json';save(out,d);print(json.dumps(bind(out),ensure_ascii=False))
