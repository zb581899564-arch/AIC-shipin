"""Root actual effective22 comparison; visible images do not prove ingestion."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def bind(p):
    return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())


np = R/'22_yi4_w03_main_native_preteacher_review.json'
sp = R/'student_reviews/22_Yi4Ij2NM7U4_W03.independent_student64_review_v1.json'
out = copy.deepcopy(read(np)); student = read(sp)
receipt = read(student['machine_binding']['student_receipt_path'])
assert not student['teacher_content_received'] and not student['candidate_predictions_received']
assert len(student['student_view_inventory']) == len(receipt['frames']) == 64 and receipt['patch_inverse_exact']
for a, b in zip(student['student_view_inventory'], receipt['frames']):
    assert a['frame_id'] == b['frame_id'] and a['png_sha256'] == b['png_sha256'] == bind(a['path'])['sha256']
out.update(status='MAIN_PRETEACHER_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',
    utc=datetime.now(timezone.utc).isoformat(), previous_native_only_review=bind(np), independent_student64=bind(sp),
    student_content_read=True, root_read_all64_native_static_facts_and_all64_student_static_facts=True,
    root_actually_viewed_student_samples=[6, 13, 23, 25, 31, 38, 62, 63])
out['events'][2].update(description='嘴部姿态变化后，眼闭/眉部收拢、手近面部、俯身转侧的有限清楚图像；不解释感受、原因或最终恢复',
    necessary_preparation='此前嘴部与洋葱接触、缺口及嘴部姿态可见，只有时间顺序，不声称内部物质转移',
    visible_result='F31眼闭、嘴部与眉部姿态和抬手，F38转侧低头姿态清楚；后续恢复不在该图像目标内')
out['events'][3].update(type='two_visible_onion_parts_typical_image',
    description='板上两个白色洋葱部分与上方刀的短典型图像；不声称它们刚在遮挡中切出或整项烹饪完成',
    necessary_preparation='F61手臂遮挡刀与洋葱接触，不能提供完整切割目标；未补造切刀动作',
    visible_result='F62可见不同白色部分但手臂遮边，F63前方白色圆体和平端另一白色部分清楚；这里只标它们的可见关系')
out['explicit_disagreements'] += [
    'Actual original effectiveF06/F13 shows partial brown skin then a displayed white round surface; not every side being peeled clean. F23 mouth/white object contact and F25 upper notch are visible; swallowing or internal transfer remains unknown.',
    'EffectiveF31/F38 supports only visible face/hand/body postures. Student full recovery endpoint UNKNOWN is not replaced by a complete physical aftermath target; the separately frozen finite typical images have no taste, emotion or causal assertion.',
    'EffectiveF62/F63 supplies the board/object relationship but not the occluded knife contact. Multiple white parts already appear earlier; no newly produced result is inferred. The old native-only result-image wording remains preserved in its original record.',
    'Student initial UNKNOWN for complete physical cutting/ingestion stays sealed. Root finite editorial targets were defined before teacher or candidate outputs, and the actual student originals now support those limited targets. All ordinary phone/ear-handling NO spans are separately reviewed.']
out['interpretation_limit'] = 'Finite sampled visual editorial silver only. All64 native/student supplied static facts were read; only listed effective originals were directly rechecked. Physical swallowing, taste, recovery, knife contact and full cooking completion remain outside the explicitly frozen image targets. Teacher comparison/final reference remains pending.'
op = R/'22_yi4_w03_main_preteacher_review_v2.json'
with op.open('x', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2, allow_nan=False)
print(json.dumps(bind(op), ensure_ascii=False))
