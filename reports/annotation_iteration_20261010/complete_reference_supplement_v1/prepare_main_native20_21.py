"""Root finite preteacher evidence, with explicit unresolved low-quality targets."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for n,stem,samples in [(20,'20_cjibt_w13',[10,14,15,17,19,27,28,29,31,34]),(21,'21_cjibt_w16',[8,30,52,57,60,62])]:
 np=next((R/'native_reviews').glob(f'{n:02d}*.native_review.json'));d=read(np);m=read(Path(d['job'])/'manifest.json')
 def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 events=[]
 if n==20:
  specs=[(10,14,'bar_pull_and_lower','伸臂抓门框横杆、屈肘上拉，再回伸臂低位，有限一轮变化',(9,10),(14,15)),
   (19,28,'tall_object_tilts_down','身体后倾贴长树干状物，长物从直立斜向下，随后原处灰尘与低位残形可见；不判真实性或因果',(18,19),(28,29)),
   (29,34,'visible_climb_to_window_ledge','墙旁上跃/攀向高窗，身体到窗台、上身伸入窗框；不声称整个人进屋完成',(28,29),(34,35))]
  unknown=[dict(first=15,last=18,reason='低对比小人形与粗长物，手撑和倒置姿态可见但完整准备/变化/结果及实际输入辨识不足；保留UNKNOWN')]
  no=[dict(first=0,last=2,reason='沙地普通起身/步行'),dict(first=3,last=9,reason='低亮度脸近景及抬头普通变化'),
   dict(first=35,last=42,reason='室内遮挡/脸近景'),dict(first=43,last=58,reason='普通住宅步行'),dict(first=59,last=63,reason='门口普通交流/手势')]
  dif=['Native U1 low-contrast forest action remains UNKNOWN. Root saw F15 crouched/support posture and F17 inverted small person but does not promote a full handstand action target from two isolated unclear images.',
   'Window arrival and upper-body-through-frame are visible; complete inside entry is not. Keep only the finite salient visible climb, preserving the physical complete-entry limitation explicitly.',
   'Object tilt and dust are visible; force, destruction, authenticity and who caused it are not asserted.']
  requested=[]
 else:
  specs=[(8,13,'horizontal_high_pose_photo','固定放大照片中，树旁高处人形横向伸身的短代表画面；静态照片不是新运动',(7,8),(13,14)),
   (30,33,'luminous_device_typical_image','暗背景清楚发亮圆口设备近景与蓝光晕短代表画面，不猜设备操作效果',(29,30),(33,34)),
   (52,60,'visible_projected_high_body_descent','杆架上方人形从高伸到团身及下降的有限突出画面，最终接地未清楚显示',(51,52),(60,61))]
  unknown=[dict(first=61,last=62,reason='运动主体下降至下方暗边/遮挡，未清楚重现落地或结束；相关物理结果保持UNKNOWN')]
  no=[dict(first=0,last=7,reason='普通持照片/模糊取景，清楚代表照片在后段'),dict(first=14,last=29,reason='室内重复交流、手势与设备旁站立'),
   dict(first=34,last=42,reason='投影小人形普通远景、动作细节不清无可判显著事件'),dict(first=43,last=51,reason='室内普通脸近景'),dict(first=63,last=63,reason='回室内普通脸近景')]
  dif=['The static high-horizontal-pose photograph is a finite typical image only; no live movement or result is invented.',
   'Projected high-body rotation/descent is actually visible, but F61..62 hides the subject at the lower dark border. Keep the visible part and explicitly mark its consequential result range UNKNOWN; do not claim a complete landing.',
   'The illuminated device is a short clear distinct representative shot, not proof of a projected operation or a claimed effect.']
  requested=[dict(left=7,right=8),dict(left=51,right=52),dict(left=62,right=63)]
 for a,b,typ,desc,start,end in specs:events.append(dict(first=a,last=b,type=typ,description=desc,editing_start_range_local_exact=gap(*start),editing_end_range_local_exact=gap(*end)))
 parts=sorted([dict(**x,decision='NO') for x in no]+[dict(**x,decision='UNKNOWN') for x in unknown]+[dict(first=e['first'],last=e['last'],decision='KEEP',event_index=i) for i,e in enumerate(events)],key=lambda x:x['first'])
 assert parts[0]['first']==0 and parts[-1]['last']==63 and all(a['last']+1==b['first'] for a,b in zip(parts,parts[1:]))
 out=dict(status='MAIN_NATIVE_ONLY_PRETEACHER_REVIEW_PENDING_STUDENT_AND_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),
  window_id=m['window_id'],teacher_content_read=False,student_content_read=False,root_candidate_prediction_exposure=False,
  root_read_all64_native_static_facts=True,root_direct64_image_review=False,root_actually_viewed_native_samples=samples,
  independent_native64=bind(np),provisional_events=events,complete_domain_editorial_decision_by_samples=parts,explicit_disagreements=dif,
  consequential_unknown_sample_ranges=unknown,boundary_tasks_requested=requested,all_no_reasons_reviewed=True,
  training_admitted=False,evaluation_reference_only=True,all_target_boundaries_adjudicated=False,new_model_calls=0,new_optimizer_updates=0,
  interpretation_limit='Finite sampled visual editing advice; original physical completeness limits preserved, never filled to meet locked coverage quotas.')
 op=R/(stem+'_main_native_preteacher_review.json')
 with op.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
 print(json.dumps(bind(op),ensure_ascii=False))
