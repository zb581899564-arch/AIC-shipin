"""ROOT exposed adjudication of the unchanged two preregistered finite display targets."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
pp=R/'23_yi4_w06_main_preteacher_review_v2.json'
tp=R/'23_yi4_w06_lawful_observation_completion_CLI40_literal_separator_recovery_v3.json'
cp=R/'teacher_semantic_crosschecks_v1/23_Yi4Ij2NM7U4_W06.exposed_semantic_crosscheck_CLI40_recovery_v3.json'
rp=R/'CLI40_effective_literal_separator_recovery_receipt_v1.json'
pre,teacher,cross,recovery=map(read,[pp,tp,cp,rp])
assert pre['window_id']==teacher['window_id']==cross['window_id']==recovery['window_id']
assert not pre['teacher_content_read'] and not cross['candidatePredictionExposure']
assert bind(cp)['sha256']=='e5d3816214e64f7679a997cf5a144373e08c0d0714b73c28c8e98237ccb4924d'
assert cross['preregistered_finite_two_events_preserved']==pre['events']
assert bind(tp)['sha256']=='9b96f227bc251c61bde001a773a0a505de69f053bbd1c4b6137b428d990907ca'
assert bind(rp)['sha256']=='3104c645566707afa89405d8d1d3126df91447da24002b6e9c6553b093ab8d43'
assert teacher['global_CLI']==40 and teacher['ordered_actual_core_count']==128 and not teacher['tool_issues'] and not teacher['proposal_geometry_identity_issues']
assert recovery['old_REJECTED_preserved'] and teacher['original_REJECTED_not_changed']
obs=R.parent/'slot6_silver24_v1/observations/23_Yi4Ij2NM7U4_W06/frames'
vp=R/'23_yi4_root_actual_postteacher_pixels_CLI40_v3.json'
pixels=dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_REVIEW_NOT_NEW_BLIND_INITIAL',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],actual_images=[dict(sample_index=i,image=bind(obs/f'F{i:02d}_O{o:06d}.png'),visible_static_fact=fact) for i,o,fact in [(8,4411,'Earlier near-lens transparent package with red-brown long food items is visible; no opening, tasting or cooking result is shown.'),(42,4799,'Earlier clear white-cap red bottle held in one hand with the other hand pointing toward it; food identity, spoken claims, cap opening and pouring are not established.')]],root_direct64_image_review=False,root_video_view=False,candidate_prediction_exposure=False,training_admitted=False)
save(vp,pixels)
d=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,selected_preteacher_event_indices=[0,1],unknown_local_exact=[],consequential_unknowns=[],
 historical_NO_reason_corrections=[dict(first=18,last=49,original_reason=next(x['reason'] for x in pre['complete_domain_editorial_decision_by_samples'] if x['first']==18 and x['last']==49),corrected_reason='同一包装摇动及普通表情手势、转身出框和白盖红瓶出现后的重复持瓶展示；不确认拿取来源或接触结果，保留原NO范围。')],
 evidence=dict(preteacher_main_review=bind(pp),teacher_observation_audit=bind(tp),original_teacher_proposal=teacher['proposal'],original_teacher_bound_fact_audit=teacher['prefix_audit'],exposed_independent_semantic_crosscheck=bind(cp),root_actual_precompletion_pixels=bind(R/'23_yi4_root_actual_pixels_schema_recovery_v1.json'),root_actual_postteacher_pixels=bind(vp),actual_scope_engineering_recovery=bind(rp)),
 differences_adjudicated=pre['explicit_disagreements']+[
 'All64 actual teacher static facts and the complete original proposal were read. Package and bottle holding/pointing are visible. Tomato-sauce identity, vacuum sealing, spoken explanation, food taste, efficacy and intent are not established by the finite supplied images and are excluded from the reference.',
 'The earlier near-lens package F07..08 and earlier bottle pointing F42/F44 are actual visible displays, not absent evidence. They remain repeated NO under the representative-image target fixed before teacher outputs and model predictions. The later frozen short targets F15..17 and F50..52 remain selected; no target was selected from candidate metrics.',
 'Teacher 3.2..9.5 and17.2..27.6 KEEP spans and .8/1/1.3/1.2-second boundary ranges are preserved in the original proposal, but are not copied. The same short representative two-image relationship targets and exact preregistered boundary intervals remain, with midpoint editing choices rather than measured physical cuts.',
 'F00..14 ordinary mouth poses/earlier package repeat, F18..49 repeated package/gestures/turning and repeated bottle holding, F53..63 repeated bottle/ordinary poses keep complete explicit NO coverage. Mouth-open static facts do not establish spoken content or laughter audio. F36 turning toward the counter and F59 bottle moving below the image do not establish grasping/release contact; F63 blurred hand before the face does not establish nose contact. F39 a partly visible white round cap is compatible with the teacher white-object fact but not a fully visible bottle.',
 'Physical opening, pouring, consumption and complete food-use outcomes remain unknown in the sealed initial reviews and outside these two frozen finite display-image targets. They are not relabeled as completed actions; this is finite editorial silver, not human gold.',
 'CLI40 strict original scope/whole REJECT due to eight separator-only literal differences remains bound. Windows actual same-file identity and frozen PNG SHA plus complete128 structure/naturalSUCCESS/actualcost permit only separately signed finite-observation recovery, not old literal compliance or semantic truth.'
 ],actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],additional_precompletion_native_samples=[15,50],additional_postteacher_native_samples=[8,42],read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,root_direct64_image_review=False,root_native_video_view=False,teacher_actual_video_delivery=True,parent_whole_rejected_preserved=True),serializer_source_binding=bind(R/'finalize_eval_window_NO_note_v3.py'),reference_scope_and_reason='Locked-evaluation-only finite visual editorial silver. Two independently preregistered representative package/bottle display images with ordinary/repeated NO. No spoken content, food identity, opening, pouring, consumption or complete cooking claim. Original physical unknowns remain explicit and outside the frozen image targets. Not human gold or training admission.')
out=R/'23_yi4_w06_root_eval_decision_CLI40_v3.json';save(out,d);print(json.dumps(bind(out),ensure_ascii=False))
