"""Root actual teacher16 review; do not merge the whole stunt scene as KEEP."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def bind(p):
    return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())


pp = R/'16_eyq_w03_main_preteacher_review_v2.json'
tp = R/'16_eyq_w03_lawful_observation_completion.json'
pre = read(pp); teacher = read(tp)
assert pre['window_id'] == teacher['window_id'] and not pre['teacher_content_read']
value = dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE', utc=datetime.now(timezone.utc).isoformat(),
    window_id=pre['window_id'], candidate_prediction_exposure=False,
    root_read_all64_teacher_facts=True, root_read_all64_native_and_student_facts=True, all_NO_ranges_reviewed=True,
    selected_preteacher_event_indices=[0, 1, 2, 3, 4], unknown_local_exact=[], consequential_unknowns=[],
    evidence=dict(preteacher_main_review=bind(pp), teacher_observation_audit=bind(tp),
        original_teacher_proposal=teacher['proposal'], original_teacher_program_bound_facts=teacher['program_bound_facts'],
        boundary_observations=pre['boundary_observations'], student_arithmetic_erratum=pre['student_arithmetic_erratum']),
    differences_adjudicated=pre['explicit_disagreements']+[
        'Gemini retains the entire performance scene as one continuous high-difficulty completed stunt. The preteacher five finite local highlights remain distinct; ordinary slow positioning F29..34 and F40..44 stays NO. No scene-wide forced event merge is used.',
        'Actual original nativeF21 shows a high rear wheel and low front wheel. Actual native/effectiveF26 shows the black rider rear-wheel-high/front-wheel-low relation; two-wheel airborne jump, exact contact and bounce are not target facts. The raw teacher claims remain unchanged.',
        'Actual original nativeF37 shows the two riders during turning, while effectiveF35/F38 supplies preparation/low-wheel return. Teacher difficulty, excellent balance and whole action completion are not inferred from the still images.',
        'The full64 student review, limited direct original checks and frozen editorial boundary probes establish the finite representative target; teacher eight previews alone cannot certify every selected interval. Physical initial lift/final tyre contact/cut-before-lowering UNKNOWN remains in original independent reviews outside the explicitly declared finite typical-image targets.',
        'All ordinary interview NO spans and intermediate ordinary riding NO spans were reviewed. Teacher decimal scene cuts and claimed audio absence are not used as exact native boundaries or audio evidence.'],
    actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],
        student_sample_indices=pre['root_actually_viewed_student_samples'], additional_postteacher_native_samples=[21, 26, 37],
        additional_postteacher_student_samples=[26, 35, 38], read_native_static_facts=64,
        read_student_static_facts=64, read_teacher_static_facts=64, root_direct64_image_review=False,
        root_native_video_view=False, teacher_actual_video_delivery=True, original_parent_terminal_not_inferred=True),
    reference_scope_and_reason='Locked-evaluation-only finite visual editorial silver. Clear local wheel-high/turn/paired representative images are independently adjudicated, ordinary riding is NO. Not a complete stunt-action annotation, human gold or official score; original unseen physical completeness limits and original teacher raw stay preserved.')
op = R/'16_eyq_w03_root_eval_decision.json'
with op.open('x', encoding='utf-8') as f:
    json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
print(json.dumps(bind(op), ensure_ascii=False))
