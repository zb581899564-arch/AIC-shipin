import copy,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
np=R/'23_yi4_w06_main_native_preteacher_review.json'
sp=R/'student_reviews/23_Yi4Ij2NM7U4_W06.independent_student64_review_v1.json'
out=copy.deepcopy(read(np));student=read(sp);receipt=read(student['machine_binding']['student_receipt_path'])
assert not student['teacher_content_received'] and not student['candidate_predictions_received']
assert len(student['student_view_inventory'])==len(receipt['frames'])==64 and receipt['patch_inverse_exact']
for a,b in zip(student['student_view_inventory'],receipt['frames']):
 assert a['frame_id']==b['frame_id'] and a['png_sha256']==b['png_sha256']==bind(a['path'])['sha256']
out.update(status='MAIN_PRETEACHER_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),previous_native_only_review=bind(np),independent_student64=bind(sp),student_content_read=True,root_read_all64_native_static_facts_and_all64_student_static_facts=True,root_actually_viewed_student_samples=[15,17,50,52])
out['events'][0].update(necessary_preparation='F15透明包装的四条红褐长圆物及指向手清楚',visible_result='F17透明包装举在脸旁仍可辨；包装开闭过程不在目标内')
out['events'][1].update(necessary_preparation='F50白色盖仍在红瓶颈上、另一手指向瓶身',visible_result='F52白盖、红瓶及指向手关系清楚；无开盖或倒出')
out['explicit_disagreements'] += [
 'Actual effectiveF15/F17 supports the previously frozen short representative packaged-food image, and effectiveF50/F52 supports the white-cap red-bottle pointing relationship. No brand, product efficacy, opening, taste or unseen cooking is inferred.',
 'Student also identifies an earlier near-lens packaging display and longer repeated bottle-holding ranges. Root retains the two distinct short representative images already defined before teacher outputs, rather than every repeat; the full ordinary talking and gesture NO reasons remain explicit.',
 'Student initial target UNKNOWN for complete physical operations remains sealed and outside the finite product-image targets; no complete opening, pouring or eating result is substituted. This remains silver editorial reference only, pending actual teacher comparison.']
out['interpretation_limit']='All64 supplied native/student static facts were read; four listed original effective images were directly inspected. Short visible display images only, no physical opening, pouring or food-use result. Actual teacher and final reference pending.'
op=R/'23_yi4_w06_main_preteacher_review_v2.json'
with op.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
oldp=R/'17_eyq_w04_main_preteacher_review_v2.json';ep=R/'student_reviews/17_EYqVtI9YWJA_W04.F57_actual_pixel_errata_v1.json';err=read(ep)
assert bind(ep)['sha256']=='79062de03f06fe6073bcec5ca1590ac18f6f4c7ce27eb9c2144af2777f87e5d1'
assert err['root_pixel_correction_received'] and not err['new_blind_initial']
out17=copy.deepcopy(read(oldp));out17.update(utc=datetime.now(timezone.utc).isoformat(),previous_main_review=bind(oldp),independent_student_actual_F57_erratum=bind(ep),root_read_actual_F57_erratum=True)
out17['explicit_disagreements'].append('Independent student subsequently inspected the original effectiveF57 once and preserved a separate root-exposed pixel erratum: rear wheel fully visible high at upper right, only upper rider cropped. Original blind KEEP/target UNKNOWN and final rear-wheel landing UNKNOWN remain unchanged; no re-reading neighboring frames or filling their gaps is implied.')
op17=R/'17_eyq_w04_main_preteacher_review_v3.json'
with op17.open('x',encoding='utf-8') as f:json.dump(out17,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps([bind(op),bind(op17)],ensure_ascii=False))

