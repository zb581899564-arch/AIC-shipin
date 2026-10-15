"""Root finite all-NO adjudication; whole CLI34 failure remains failed."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
pp=R/'18_j0n_w02_main_preteacher_review.json';tp=R/'18_j0n_w02_lawful_observation_completion.json'
cp=R/'teacher_semantic_crosschecks_v1/18_J0nA4VgnoCo_W02.teacher_semantic_crosscheck_v1.json'
pre,teacher,cross=read(pp),read(tp),read(cp)
assert pre['window_id']==teacher['window_id']==cross['window_id'] and not pre['teacher_content_read']
assert not pre['events'] and not cross['candidate_predictions_received']
vp=R/'18_j0n_w02_root_actual_postteacher_pixels_v1.json'
obs=R.parent/'slot6_silver24_v1/observations/18_J0nA4VgnoCo_W02/frames'
save(vp,dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_REVIEW_NOT_NEW_BLIND_INITIAL',utc=datetime.now(timezone.utc).isoformat(),
    window_id=pre['window_id'],actual_images=[dict(sample_index=i,image=bind(obs/f'F{i:02d}_O{o:06d}.png'),visible_static_fact=t) for i,o,t in [
        (16,1621,'Hand holds dark bent rod low beside thigh and car. Open boot behind does not prove extraction from it.'),
        (19,1655,'Standing man holds upright dark rod in tilted frame. Intent, speech and tool use not inferred.'),
        (62,2145,'Standing man extends arm near upper car/window edge; not visible wheel repair or result.')]],
    root_direct64_image_review=False,root_video_view=False,candidate_prediction_exposure=False,training_admitted=False))
value=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),
    window_id=pre['window_id'],candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,
    root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,selected_preteacher_event_indices=[],
    unknown_local_exact=[],consequential_unknowns=[],evidence=dict(preteacher_main_review=bind(pp),teacher_observation_audit=bind(tp),
        original_teacher_proposal=teacher['proposal'],original_teacher_bound_fact_audit=teacher['prefix_audit'],
        exposed_independent_semantic_crosscheck=bind(cp),root_actual_postteacher_pixels=bind(vp)),
    differences_adjudicated=pre['explicit_disagreements']+[
        'Teacher all four contiguous NO subdivisions and zero KEEP events agree the frozen finite sampled visual editorial decision. No approximate internal teacher subdivision becomes a measured physical-action cut.',
        'Actual originalF16 does not show extraction from the boot. Actual F19/F62 are ordinary rod-holding/upper-car reaching images. Independent original native/studentF60 crosscheck excludes a wheel-repair posture. Object origin/material/purpose, impact and repair result are not labelled.',
        'Mouth/hand/body postures are visible; teacher volume, greeting, conversation content, emotion, prop-use and no-audio assertions are not accepted as sensory evidence.',
        'Student original physical target UNKNOWN and between-sample limits remain sealed. No distinct finite visual highlight is selected; all-domain NO is editing advice, not proof that no physical event ever occurred.',
        'Actual immutable completed media prefix precedes the later CLI34 out-of-whitelist transcript reads and API connection error. Whole CLI34 is REJECTED and remains REJECTED; this finite reference uses only separately verified early media/facts plus independent reviews, not its terminal success.'],
    actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],
        student_sample_indices=pre['root_actually_viewed_student_samples'],additional_postteacher_native_samples=[16,19,62],
        read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,
        root_direct64_image_review=False,root_native_video_view=False,teacher_actual_video_delivery=True,
        original_parent_terminal_not_inferred=True,whole_CLI34_status='REJECTED_ACTUAL_POST_SCOPE_OUTSIDE_READ_AND_NETWORK_ERROR'),
    reference_scope_and_reason='Locked-evaluation-only finite sampled visual all-NO silver. Ordinary tilted parking views, holding rod, repeated gestures and reaching show no distinct retained highlight. Physical intent/function/result/between-frame limits remain unknown in the original records. Not human gold, physical no-event proof or official score; failed whole CLI34 stays failed.')
out=R/'18_j0n_w02_root_eval_decision.json';save(out,value);print(json.dumps(bind(out),ensure_ascii=False))
