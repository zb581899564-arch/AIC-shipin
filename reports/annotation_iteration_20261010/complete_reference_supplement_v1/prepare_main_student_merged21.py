"""Actual root effective-input21 checks; do not invent the hidden landing."""
import copy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def bind(p):
    return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())


np = R/'21_cjibt_w16_main_native_preteacher_review.json'
sp = R/'student_reviews/21_cjibtmSLxQ4_W16.independent_student64_review_v1.json'
out = copy.deepcopy(read(np)); student = read(sp)
receipt = read(student['machine_binding']['student_receipt_path'])
assert not student['teacher_content_received'] and not student['candidate_predictions_received']
assert len(student['student_view_inventory']) == len(receipt['frames']) == 64 and receipt['patch_inverse_exact']
for a, b in zip(student['student_view_inventory'], receipt['frames']):
    assert a['frame_id'] == b['frame_id'] and a['png_sha256'] == b['png_sha256'] == bind(a['path'])['sha256']
out.update(status='MAIN_PRETEACHER_PARTIAL_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',
    utc=datetime.now(timezone.utc).isoformat(), previous_native_only_review=bind(np), independent_student64=bind(sp),
    student_content_read=True, root_read_all64_native_static_facts_and_all64_student_static_facts=True,
    root_actually_viewed_student_samples=[8, 30, 57, 60, 62],
    boundary_observations=bind(R/'21_cjibt_w16_boundary_observations_acceptance.json'))
out['events'] = out.pop('provisional_events')
photo = read(R/'boundary_phase_v2_task13/main_observation.json')['reviewed_editing_range_local_exact']
projection = read(R/'boundary_phase_v2_task14/main_observation.json')['reviewed_editing_range_local_exact']
unknown_end = read(R/'boundary_phase_v2_task15/main_observation.json')['reviewed_editing_range_local_exact']
out['events'][0].update(type='high_curled_pose_static_photo',
    description='放大静态照片中，树干旁高处红蓝衣人物屈腿/屈身，手臂近树枝的短代表画面；不是新的实况动作',
    editing_start_range_local_exact=photo)
out['events'][2]['editing_start_range_local_exact'] = projection
assert all(F(b)-F(a) <= F('.5') for e in out['events'] for a, b in
           (e['editing_start_range_local_exact'], e['editing_end_range_local_exact']))
out['unknown_end_editing_range_local_exact'] = unknown_end
out['explicit_disagreements'] += [
    'Actual original effectiveF08 shows a high curled body near the tree, not a fully stretched horizontal body. This separately saved correction preserves the original native-only wording and the old boundary observation wording; it changes no source frame, time or candidate metric.',
    'Student initial does not call a still photo or luminous device a complete live event. Root retains the already frozen finite typical-image targets only; no new movement, projector effect or complete physical operation is asserted.',
    'Original effectiveF57/F60/F62 confirms high body posture then a lower curled body and hidden lower-blue-border result. F61..62 remains consequential UNKNOWN; the interior scene-return image narrows editing uncertainty without showing a landing.',
    'Actual registered task14 is already projection, so the entrance uses F51/interior. Task13 is still a held photo, so the full-frame typical photo entrance uses interior/F08.']
out['all_selected_editing_boundary_ranges_at_most_half_second'] = True
out['interpretation_limit'] = 'Finite sampled visual silver; root read all64 native/student facts and directly checked only listed originals. Static photograph and luminous-device targets are representative images. Projection result remains consequential UNKNOWN. No teacher or candidate result was read for this judgment.'
op = R/'21_cjibt_w16_main_preteacher_review_v2.json'
with op.open('x', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2, allow_nan=False)
print(json.dumps(bind(op), ensure_ascii=False))
