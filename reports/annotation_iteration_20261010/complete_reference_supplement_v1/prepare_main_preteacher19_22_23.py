"""Root actual preteacher judgments, finite visible targets without unseen outcomes."""
import json,hashlib,copy
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
for n,tag,observed in [(19,'19_j0n_w11',[4,7,14,16,18,51,52,54,58]),(22,'22_yi4_w03',[6,13,23,25,31,38,61,63]),(23,'23_yi4_w06',[15,17,50,52])]:
 np=next((R/'native_reviews').glob(f'{n:02d}*.native_review.json'));native=read(np);m=read(Path(native['job'])/'manifest.json')
 def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 def event(a,b,kind,description,prep,result):
  return dict(first=a,last=b,type=kind,description=description,necessary_preparation=prep,visible_result=result,
   editing_start_range_local_exact=gap(a-1,a),editing_end_range_local_exact=gap(b,b+1) if b<63 else ['30','30'])
 out=dict(status='MAIN_NATIVE_ONLY_PRETEACHER_REVIEW_PENDING_STUDENT_AND_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),
  window_id=m['window_id'],teacher_content_read=False,root_candidate_prediction_exposure=False,independent_native64=bind(np),
  root_read_all64_native_static_facts=True,root_actually_viewed_native_samples=observed,root_direct64_image_review=False,
  student_content_read=False,training_admitted=False,evaluation_reference_only=True,new_model_calls=0,new_optimizer_updates=0,all_no_reasons_reviewed=True)
 if n==19:
  oldp=R/'19_j0n_w11_main_native_preteacher_review.json';old=read(oldp)
  sp=next((R/'student_reviews').glob('19*independent_student64_review_v1.json'));s=read(sp)
  assert len(s['student_view_inventory'])==64 and not s['teacher_content_received'] and not s['candidate_predictions_received']
  rec=read(s['machine_binding']['student_receipt_path']);assert rec['patch_inverse_exact']
  for a,z in zip(s['student_view_inventory'],rec['frames']):
   assert a['source_ordinal']==z['source_ordinal'] and a['png_sha256']==z['png_sha256']==bind(a['path'])['sha256']
  accp=R/'19_j0n_w11_boundary_observations_acceptance.json';acc=read(accp)
  bd=read(acc['observations'][0]['path'])['reviewed_editing_range_local_exact']
  out.update(status='MAIN_PRETEACHER_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',previous_native_only_review=bind(oldp),
   independent_student64=bind(sp),student_content_read=True,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
   root_actually_viewed_student_samples=[4,7,14,18],boundary_observations=bind(accp),events=copy.deepcopy(old['provisional_events']))
  out['events'][0]['editing_end_range_local_exact']=bd
  out['events'][1].update(type='local_wheel_outward_tilt_and_exposed_arch',description='车轮旁俯身握轮后轮胎向轮拱外倾斜，轮拱内圆形黑色区域露出；仅局部可见关系变化，不断言拆卸安装方向或完整维修',
   necessary_preparation='F14..15轮旁手与黄柄工具近轮心，接触被头手遮挡',visible_result='F16..18轮胎位于轮拱外倾斜，后方轮拱内黑色区域可见')
  out['complete_domain_editorial_decision_by_samples']=[dict(first=0,last=3,decision='NO',reason=old['no_sample_ranges'][0]['reason']),
   dict(first=4,last=7,decision='KEEP',event_index=0),dict(first=8,last=13,decision='NO',reason=old['no_sample_ranges'][1]['reason']),
   dict(first=14,last=18,decision='KEEP',event_index=1)]+[dict(first=x['first'],last=x['last'],decision='NO',reason=x['reason']) for x in old['no_sample_ranges'][2:]]
  out['explicit_disagreements']=old['explicit_disagreements']+['Student initial broad operation KEEP/UNKNOWN is unchanged. Root keeps only clear tread detail and short outward tyre relation, excludes prolonged wheel-center obstruction and ordinary stand-up. No repair/security or exact release result is inferred.','Registered interior task12 only narrows a typical tread excerpt, not a physical diagnostic endpoint.']
 elif n==22:
  out['events']=[event(6,15,'visible_peeling_and_white_onion','双手处理半剥洋葱至全白洋葱被举起，保留明确局部准备和可见结果；中间转场未证明每一步连续',
   'F06半剥洋葱与双手，刀已置板上','F13..15白色去皮洋葱清楚'),
   event(18,25,'visible_bite_and_notch_result','举洋葱至嘴边接触，随后洋葱离嘴并有可见缺口；仅可见咬取局部结果，不声称吞咽或后续恢复',
    'F18..21举洋葱、头与洋葱建立关系','F23嘴部接触后F24..25离嘴与缺口可见'),
   event(26,38,'visible_face_and_hand_typical_changes','短暂眼闭、嘴部变化、手近面部及转身俯身的清楚典型图像；不从表情推断味觉、心理、吐出或恢复',
    '咬取后脸部和手位置清楚，不需不可见的心理起点','F31眼闭与面部变化、F38转身俯身手近面部可见；后切场景只界定有限编辑域'),
   event(62,63,'two_onion_parts_typical_result','板上两块白洋葱和上方刀的短结果图像；F61手臂遮挡不据此断言切割瞬间或全烹饪完成',
    'F61大幅手臂遮挡不作为完整物理切割目标','F62..63两块白洋葱可见，域末端30只是观察边界')]
  out['complete_domain_editorial_decision_by_samples']=[dict(first=0,last=5,decision='NO',reason='普通持刀、放置及手势，局部剥皮目标从清楚双手与半剥洋葱开始'),
   dict(first=6,last=15,decision='KEEP',event_index=0),dict(first=16,last=17,decision='NO',reason='普通站立和建立持物姿态'),
   dict(first=18,last=25,decision='KEEP',event_index=1),dict(first=26,last=38,decision='KEEP',event_index=2),
   dict(first=39,last=61,decision='NO',reason='重新站立和普通讲话持刀、置物，末端刀操作被手臂遮挡，不声称实际切割过程'),
   dict(first=62,last=63,decision='KEEP',event_index=3)]
  out['explicit_disagreements']=['Original native E2 physical final mouth/recovery endpoint UNKNOWN after F39 cut stays sealed. Root separates the observable bite/notch result from finite representative face/hand images; neither asserts swallowing, spitting, taste or completed recovery. These target definitions are fixed before teacher/student final or model predictions, not chosen from metric outcomes.',
   'Original native E3 includes occluded F61 knife preparation. Root finite target is the clear two-part result F62..63 only; the actual cutting instant and full cooking completion remain unknown and outside this image target.',
   'No event overlap or semantic merging is introduced even where bite and later image excerpts touch; mandatory student effective-input comparison remains pending.']
  out['physical_unknowns_preserved_outside_finite_targets']=['吞咽/吐出及最终口部恢复状态','遮挡期间具体切刀瞬间','完整烹饪完成']
 else:
  out['events']=[event(15,17,'packaged_sausage_typical_display','完整透明包装与多根红褐长条食物的清楚展示，手指向包装；不推断品牌、味道或烹饪',
    'F15包装完整清楚且手指向它','F17包装脸旁仍清楚可見'),
   event(50,52,'red_bottle_typical_display','白盖红瓶清楚近胸脸旁、手指向瓶身的短典型展示，不推断口述内容或产品功效',
    'F50瓶身白盖清楚且手指向瓶','F52瓶和头肩清楚、展示关系仍在')]
  out['complete_domain_editorial_decision_by_samples']=[dict(first=0,last=14,decision='NO',reason='普通厨房站立讲话式口型、模糊或短暂举包，清楚代表展示单取后续短段'),
   dict(first=15,last=17,decision='KEEP',event_index=0),dict(first=18,last=49,decision='NO',reason='同一包装摇动及普通表情手势、取瓶后重复持瓶展示，避免长重复'),
   dict(first=50,last=52,decision='KEEP',event_index=1),dict(first=53,last=63,decision='NO',reason='重复持瓶及普通讲话式表情手势，没有新的清楚局部结果')]
  out['explicit_disagreements']=['Only two distinct clear product-relationship representative images are kept; ordinary talking and repeated holding have explicit NO reasons. No unseen audio, product efficacy or physical process completion is inferred.']
 for e in out['events']:
  for k in ['editing_start_range_local_exact','editing_end_range_local_exact']:
   a,z=map(F,e[k]);assert 0<=a<=z<=30 and z-a<=F('1/2'),(n,e,k)
 covered=[i for x in out['complete_domain_editorial_decision_by_samples'] for i in range(x['first'],x['last']+1)]
 assert covered==list(range(64))
 out['all_selected_editing_boundary_ranges_at_most_half_second']=True
 out['interpretation_limit']='Finite visible editing judgment; actual teacher and all64 effective student comparison required before final reference, original physical UNKNOWN untouched.'
 op=R/(tag+('_main_preteacher_review_v2.json' if n==19 else '_main_native_preteacher_review.json'));save(op,out);print(json.dumps(bind(op),ensure_ascii=False))

