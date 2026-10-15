"""Record actual root spot inspection plus independently sealed complete reviews."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
for name,stem,ids in [('04_HT5vyqe0Xaw_W02','04_ht5_w02',['F30','F31','F39','F40','F54']),('05_HT5vyqe0Xaw_W10','05_ht5_w10',['F00','F28','F42','F63'])]:
    np=ROOT/'native_reviews'/(name+'.native_review.json');sp=ROOT/'student_reviews'/(name+'.independent_student64_review_v1.json')
    n=read(np);s=read(sp);assert n['frame_count']==64 and len(n['frames'])==64 and len(s['student_view_inventory'])==64
    for f in n['frames']:assert sha(Path(f['path']))==f['png_sha256'] and f['native_clock_identity_match'] and f['visually_inspected_original_png']
    for f in s['student_view_inventory']:assert sha(Path(f['path']))==f['png_sha256']
    images=[dict(frame_id=f['frame_id'],path=f['path'],sha256=f['png_sha256'],view='native') for f in n['frames'] if f['frame_id'] in ids]
    if name.startswith('04'):
        images += [dict(frame_id=f['frame_id'],path=f['path'],sha256=f['png_sha256'],view='effective_student') for f in s['student_view_inventory'] if f['frame_id'] in ['F31','F39']]
        decision=dict(keep_sample_runs=[[31,39]],events=[dict(event_id='M1',visible_fact='蓝白卡车正面、打开的左门和两侧贴近的林木/窄路关系的短代表画面',necessary_preparation='F31从轮胎局部转到整体车头，保留建立整体关系的镜头',visible_result='完整车头与狭窄道路空间关系；不推断受困、脱困、行驶或救援',evidence_frame_ids=['F31','F32','F33','F34','F35','F36','F37','F38','F39'])],
            no_ranges=[dict(samples=[0,30],reason='车尾/绳结/轮胎视角巡览，无绳索操作或清楚行动结果。'),dict(samples=[40,63],reason='同一车头和车厢继续重复展示，随后模糊摇向树林又回车头；整体典型画面已在短片段建立。')],
            student_initial_disagreement='Student initial NO was based on lack of action. Root finite target is explicitly a typical visual image, which the initial student facts and directly seen F31/F39 do show; not a hidden action. Initial UNKNOWN and NO remain unchanged in their sealed files.',
            root_observation='F30低角度轮胎；F31全车正面尚软、F39车头/门/窄路关系较清楚，F40重复同构图、F54同车更近前角。不能把视角变化称车辆运动。',
            consequential_boundary=[dict(left='F39',right='F40',width_exact='1001/2000',requires_actual_interior_observation=True)])
    else:
        decision=dict(keep_sample_runs=[],events=[],explicit_no_highlight=True,no_ranges=[dict(samples=[0,41],reason='远车尾逐渐被遮挡、远处人物细节不清，普通远景离开不足以保留，不能推断脱困完成。'),dict(samples=[42,62],reason='暗林路空景长时间重复，无主要行动或代表主体。'),dict(samples=[63,63],reason='全黑尾帧无视觉事件。')],
            student_initial_disagreement='Both initial editorial reviews select NO. Student initial target observable UNKNOWN is kept; root explicitly adjudicates this finite sampled visual editing target, without claiming absence of unseen physical action or audio importance.',
            root_observation='F00车尾很小、有红灯；F28车尾远、右方小人物但无可辨手势；F42暗空路；F63黑屏。',consequential_boundary=[])
    save(ROOT/(stem+'_main_preteacher_review.json'),dict(status='ROOT_NATIVE_STUDENT_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER_COMPLETION',utc=datetime.now(timezone.utc).isoformat(),window_id=n['window_id'],source_sha256=n['source_sha256'],native_complete_review=bound(np),student_complete_review=bound(sp),root_directly_inspected_images=images,root_inspected_all64_images=False,complete64_image_inspection_performed_by_delegated_reviewers=True,root_read_all64_native_and_student_static_facts=True,decision=decision,teacher_content_received=False,candidatePredictionExposure=False,training_admitted=False,new_model_calls=0,new_optimizer_updates=0))
    print(stem,'root review recorded, not admitted')
