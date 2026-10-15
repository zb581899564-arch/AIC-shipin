"""Root adjudication of actual supplied window17; immutable earlier claims retained."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p): return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)

pp = R/'17_eyq_w04_main_preteacher_review_v3.json'
tp = R/'17_eyq_w04_lawful_observation_completion.json'
cp = R/'teacher_semantic_crosschecks_v1/17_EYqVtI9YWJA_W04.teacher_semantic_crosscheck_v1.json'
pre, teacher, cross = read(pp), read(tp), read(cp)
assert pre['window_id'] == teacher['window_id'] == cross['window_id']
assert not pre['teacher_content_read'] and not cross['candidate_predictions_received']
obs = R.parent/'slot6_silver24_v1/observations/17_EYqVtI9YWJA_W04/frames'
observed = [
    (33, 4067, 'Both wheels are low near the platform top; exact tyre contact is not resolved.'),
    (38, 4138, 'Front wheel low near platform, rear wheel high; not a two-wheel airborne claim.'),
    (45, 4238, 'Front wheel low near platform and rear wheel high; fine contact unresolved.'),
    (46, 4252, 'Both wheels low near platform; no exact touchdown instant.'),
    (54, 4366, 'Front wheel low and rear wheel high above blue structures while descending; not proof of already landing.'),
    (57, 4409, 'Main rear wheel fully visible high at right; front wheel low near the ground.'),
    (58, 4423, 'Both main wheels low near floor. Earlier native rear-high wording is contradicted by the actual original image.'),
    (59, 4437, 'Frontal fork and near front wheel visible; rear contact and complete physical ending unresolved.')]
vp = R/'17_eyq_w04_root_actual_postteacher_pixels_v1.json'
save(vp, dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_REVIEW_NOT_NEW_BLIND_INITIAL',
    utc=datetime.now(timezone.utc).isoformat(), window_id=pre['window_id'],
    actual_images=[dict(sample_index=i, image=bind(obs/f'F{i:02d}_O{o:06d}.png'), visible_static_fact=fact) for i,o,fact in observed],
    root_direct64_image_review=False, root_video_view=False, candidate_prediction_exposure=False,
    original_native_and_teacher_claims_preserved=True, training_admitted=False))
value = dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE', utc=datetime.now(timezone.utc).isoformat(),
    window_id=pre['window_id'], candidate_prediction_exposure=False,
    root_read_all64_teacher_facts=True, root_read_all64_native_and_student_facts=True, all_NO_ranges_reviewed=True,
    selected_preteacher_event_indices=[0,1,2,3,4], unknown_local_exact=[], consequential_unknowns=[],
    evidence=dict(preteacher_main_review=bind(pp), teacher_observation_audit=bind(tp),
        original_teacher_proposal=teacher['proposal'], original_teacher_bound_fact_audit=teacher['prefix_audit'],
        boundary_observations=pre['boundary_observations'], student_actual_F57_erratum=pre['independent_student_actual_F57_erratum'],
        exposed_independent_semantic_crosscheck=bind(cp), root_actual_postteacher_pixels=bind(vp)),
    differences_adjudicated=pre['explicit_disagreements']+[
        'Teacher whole-performance KEEP12..27.5 and alleged interview at F58/F59 are rejected. The five preregistered finite local image events and ordinary interview NO0..25/60..63 remain; F58/F59 still show the bicycle.',
        'Actual F33 is low wheels near platform, F38/F45 front low and rear high, F54 descending above structures. Full hops, exact contact and already completed landing are not supplied facts. Support/ground wording denotes visible wheel relation, not measured contact.',
        'Actual F57 supplies the high main rear wheel. Actual F58 supplies both wheels low near floor; the old native rear-high caption is erroneous and is preserved as history. No neighbouring missing interval or exact final rear contact is invented.',
        'Physical complete-turn ending and fine contact remain UNKNOWN in the original sealed records and independent crosscheck. Those are outside the finite typical-image target defined before teacher/predictions; F56..59 is not relabelled as a complete physical stunt.',
        'Teacher emotion, speed, difficulty, audio and outcome assertions are excluded. All64 actual teacher/static native/student rows and all ordinary NO spans were reviewed; eight actual postteacher original images were inspected. Original parent strict failure remains a strict failure; only the independently proved trailing-LF count representation is corrected.'],
    actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],
        student_sample_indices=pre['root_actually_viewed_student_samples'], additional_postteacher_native_samples=[i for i,_,_ in observed],
        read_native_static_facts=64, read_student_static_facts=64, read_teacher_static_facts=64,
        root_direct64_image_review=False, root_native_video_view=False, teacher_actual_video_delivery=True,
        original_parent_terminal_not_inferred=True, current_teacher_native_images=32, earlier_proven_native_images=32),
    reference_scope_and_reason='Locked-evaluation-only finite visual editorial silver. Five frozen representative wheel/airborne/turn image events retained with ordinary interview NO; complete physical hop, landing and final contact remain unknown outside these limited targets. Not human gold or official quality proof; original contradictory raw claims stay preserved.')
op=R/'17_eyq_w04_root_eval_decision.json'
save(op,value)
print(json.dumps(bind(op),ensure_ascii=False))
