"""Record four original images actually viewed by ROOT after teacher receipt."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
idx=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5/call36/index.json'
w=read(idx)['windows'][0]
assert w['job_index']==19
notes={'F04':'手指接近胎面浅色纵向线和槽纹的特写，不作磨损或可用性诊断。','F07':'手指指向同一横置胎面纵向纹路，另一人手扶轮胎。有限典型画面，不是完整检查结果。','F14':'白衣人物低头俯身于后轮，手持黄黑色物体靠近轮心；具体接触和机械功能被头手遮挡。','F18':'轮胎向轮拱外倾，黑色轮圈与轮拱内黑色区域可见；不证明装轮、拆轮方向或维修完成。'}
frames=[]
for f in w['native_identity_all64']:
 if f['frame_id'] in notes:
  assert sha(f['original_path'])==f['png_sha256']
  frames.append({'frame_id':f['frame_id'],'path':f['original_path'],'sha256':f['png_sha256'],'root_actual_visible_fact':notes[f['frame_id']]})
out=R/'19_j0n_w11_root_actual_postteacher_pixels_v1.json'
doc={'status':'ROOT_ACTUAL_FOUR_POSTTEACHER_ORIGINAL_PNG_REVIEW','utc':datetime.now(timezone.utc).isoformat(),'window_id':w['window_id'],'frames':frames,'actual_images_viewed':4,'root_direct64_image_review':False,'root_native_video_view':False,'root_read_all64_teacher_static_facts':True,'old_native_student_blind_and_unknown_records_unchanged':True,'candidate_prediction_exposure':False,'new_model_calls':0,'new_video_decode':0}
with out.open('x',encoding='utf-8') as f:json.dump(doc,f,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(out),'sha256':sha(out)},ensure_ascii=False))
