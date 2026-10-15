"""Root actual effective-input20 review; retain unresolved forest motion."""
import json,hashlib,copy
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
p=R/'20_cjibt_w13_main_native_preteacher_review.json';out=copy.deepcopy(read(p))
s=R/'student_reviews/20_cjibtmSLxQ4_W13.independent_student64_review_v1.json';v=read(s);rec=read(v['machine_binding']['student_receipt_path'])
assert not v['teacher_content_received'] and not v['candidate_predictions_received'] and len(v['student_view_inventory'])==64 and rec['patch_inverse_exact']
for a,z in zip(v['student_view_inventory'],rec['frames']):
 assert a['frame_id']==z['frame_id'] and a['png_sha256']==z['png_sha256']==bind(a['path'])['sha256']
out.update(status='MAIN_PRETEACHER_PARTIAL_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),
 previous_native_only_review=bind(p),independent_student64=bind(s),student_content_read=True,
 root_read_all64_native_static_facts_and_all64_student_static_facts=True,root_actually_viewed_student_samples=[12,19,27,28,34])
out['events']=out.pop('provisional_events')
out['events'][1].update(type='visible_treelike_object_upright_to_low_result',description='人物举臂近长柱后，远景粗长树干样物由直立/倾斜至地面低横位的可见局部结果；不推断用力、动作意图、因果或真实性',
 necessary_preparation='F19..23人物双臂高位、手近树干，接触细节不清',visible_result='F27物体明显倾斜、F28地面低横位与圆暗端可见')
out['events'][2].update(type='visible_window_ledge_and_frame_image',description='屋外人物从高位伸手到窗台附近、上身进入窗框后腿仍外侧的清楚局部图像；不声称完整进入室内',
 necessary_preparation='F29屋墙窗旁模糊人物及F30..31高位伸手姿态',visible_result='F33窗台站位及F34上身在窗框后、下肢仍可见')
out['explicit_disagreements']+=['Student full physical握梁/入室起止UNKNOWN remains sealed. The finite local flexion/extension and visible window-frame relation do not assert complete entry or exact initial grasp.',
 'Student factsF24..28 record upright/tilted long pillar and ground-level end. Root original effectiveF19/F27/F28 confirms this visible change; selected finite local result has no force, plot, purpose or causal target.',
 'F15..18 low-contrast forest motion remains UNKNOWN. It is not relabeled to meet a completeness quota.']
out['interpretation_limit']='Actual full64 native/student supplied static facts plus limited root original image checks. No whole-film plot, force, intent, complete entry or unclear forest acrobatics asserted; teacher final still pending.'
q=R/'20_cjibt_w13_main_preteacher_review_v2.json'
with q.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(q),ensure_ascii=False))

