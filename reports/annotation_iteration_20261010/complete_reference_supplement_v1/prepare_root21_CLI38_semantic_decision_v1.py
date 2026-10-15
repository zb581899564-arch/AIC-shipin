"""Serialize ROOT's actual exposed review; preserve the frozen finite targets."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import json, hashlib
R = Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p): return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p, x):
    with p.open('x', encoding='utf-8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False)
pp=R/'21_cjibt_w16_main_preteacher_review_v2.json'
tp=R/'21_cjibt_w16_lawful_observation_completion_CLI38_v1.json'
cp=R/'teacher_semantic_crosschecks_v1/21_cjibtmSLxQ4_W16.exposed_semantic_crosscheck_CLI38_v1.json'
pre,teacher,cross=read(pp),read(tp),read(cp)
assert pre['window_id']==teacher['window_id']==cross['window_id']
assert not pre['teacher_content_read'] and not cross['candidatePredictionExposure']
assert teacher['global_CLI']==38 and not teacher['tool_issues'] and not teacher['proposal_geometry_identity_issues']
obs=R.parent/'slot6_silver24_v1/observations/21_cjibtmSLxQ4_W16/frames'
actual=[
 (8,14500,'Enlarged still photograph: high curled red/blue body beside a tree, not a newly observed live descent.'),
 (30,14813,'Distinct luminous circular opening in a box with blue halo; no operational effect or specific device identity asserted.'),
 (52,15127,'Projected scene with a prominent elevated/leaning body and smaller people below; complete physical onset not shown.'),
 (60,15241,'Prominent compact body lower at the right of the pole frame; exact contact not resolved.'),
 (62,15269,'Prior subject low/obscured at the blue foreground; final landing/outcome cannot be established.')]
vp=R/'21_cjibt_w16_root_actual_postteacher_pixels_CLI38_v1.json'
save(vp,dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_REVIEW_NOT_NEW_BLIND_INITIAL',utc=datetime.now(timezone.utc).isoformat(),
 window_id=pre['window_id'],actual_images=[dict(sample_index=i,image=bind(obs/f'F{i:02d}_O{o:06d}.png'),visible_static_fact=fact) for i,o,fact in actual],
 root_direct64_image_review=False,root_video_view=False,candidate_prediction_exposure=False,
 original_native_and_teacher_claims_preserved=True,training_admitted=False))
last=pre['events'][2]['editing_end_range_local_exact']
end=pre['unknown_end_editing_range_local_exact']
unknown=[[str(sum(map(F,last),F(0))/2),str(sum(map(F,end),F(0))/2)]]
value=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),
 window_id=pre['window_id'],candidate_prediction_exposure=False,
 root_read_all64_teacher_facts=True,root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,
 selected_preteacher_event_indices=[0,1,2],unknown_local_exact=unknown,
 consequential_unknowns=pre['consequential_unknown_sample_ranges'],
 evidence=dict(preteacher_main_review=bind(pp),teacher_observation_audit=bind(tp),
 original_teacher_proposal=teacher['proposal'],original_teacher_bound_fact_audit=teacher['prefix_audit'],
 boundary_observations=pre['boundary_observations'],exposed_independent_semantic_crosscheck=bind(cp),root_actual_postteacher_pixels=bind(vp)),
 differences_adjudicated=pre['explicit_disagreements']+[
 'Teacher all-NO proposal is rejected for the frozen finite-image targets. F08..13 is a still photograph, not a newly observed live descent; a full physical event is not the target of this short representative photo.',
 'F30..33 distinct luminous-device representative image is retained without naming a camera, operation or causal effect. F52..60 visible high-body/posture/descent sequence is retained without claiming a complete release, flip, touchdown or final outcome.',
 'F61..62 consequential result UNKNOWN remains explicit. Teacher ordinary-crowd wording and all-NO do not supply the missing obscured contact. UNKNOWN ends at the separately preregistered scene-return editing midpoint, not an invented landing.',
 'Teacher broad 0.6/0.7-second uncertainty ranges and some support PTS outside its proposed segments are preserved as original discrepancies, not silently narrowed. Final boundaries use the earlier independently reviewed exact ranges only.',
 'All64 teacher/native/student static facts and ordinary NO spans were read. ROOT directly rechecked only five listed originals after the teacher disagreement, not all64 images or video; independent original blind observations remain separate.',
 'Speech, intent, mental state, specific sport, historical attribution and audio absence are not established by these static observations and are excluded from the finite reference.'
 ],
 actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],
 additional_postteacher_native_samples=[i for i,_,_ in actual],read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,
 root_direct64_image_review=False,root_native_video_view=False,teacher_actual_video_delivery=True,original_parent_terminal_not_inferred=True),
 reference_scope_and_reason='Locked-evaluation-only finite visual editorial silver. Three preteacher representative image/visible-body events retained with ordinary NO and explicit consequential UNKNOWN for the obscured result. Not human gold, not a complete physical performance, and not training admission.')
op=R/'21_cjibt_w16_root_eval_decision_CLI38_v1.json'
save(op,value)
print(json.dumps(bind(op),ensure_ascii=False))
