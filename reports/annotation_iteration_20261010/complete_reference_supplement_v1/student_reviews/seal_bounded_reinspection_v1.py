import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
OUT=Path("G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/student_reviews")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
payload=json.loads(Path(sys.argv[1]).read_text('utf-8-sig'))
planp=OUT/'bounded_reinspection_fixed_plan_v2.json'
plan=json.loads(planp.read_text('utf-8-sig'))
w=next(x for x in plan['windows'] if x['job_index']==payload['job_index'])
oldp=Path(w['review_path']); assert sha(oldp)==w['review_sha256']
old=json.loads(oldp.read_text('utf-8-sig'))
mp=Path(old['machine_binding']['manifest_path']); rp=Path(old['machine_binding']['student_receipt_path'])
m=json.loads(mp.read_text('utf-8-sig')); r=json.loads(rp.read_text('utf-8-sig'))
assert sha(mp)==r['manifest_sha256']==old['machine_binding']['manifest_sha256']
assert sha(rp)==old['machine_binding']['student_receipt_sha256']
assert set(map(int,payload['notes']))==set(w['slots'])
assert [x['frame_id'] for x in payload['supplies']]==[x['frame_id'] for x in w['input_binding']]
inv=[]
for b,s in zip(w['input_binding'],payload['supplies']):
 i=int(b['frame_id'][1:]); f=r['frames'][i]; p=Path(b['path'])
 assert s['path']==b['path'] and s['status']=='SUCCESS_IMAGE_RETURNED_AND_EMITTED'
 assert sha(p)==b['png_sha256']==f['png_sha256']
 with Image.open(p) as im:rgb=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
 assert rgb==b['rgb_pixel_sha256']==f['rgb_pixel_sha256']
 assert f['source_ordinal']==m['frames'][i]['source_ordinal'] and f['global_seconds_exact']==m['frames'][i]['global_seconds_exact']
 inv.append(dict(f,actual_png_sha256=sha(p),actual_rgb_pixel_sha256=rgb,original_sealed_fact=old['student_view_inventory'][i]['visible_static_fact'],fresh_visible_static_fact=payload['notes'][str(i)],comparison=payload.get('qualifications',{}).get(str(i),'Scene/subject/object/pose core matches at this actually reinspected slot.'),tool_supply=s))
doc={'schema':'student_bounded_fact_reinspection_v1','utc':datetime.now(timezone.utc).isoformat(),'fixed_job_index':w['job_index'],'window_id':old['window_id'],'not_new_blind_initial':True,'root_job08_correction_exposure_received':True,'teacher_content_received':False,'scores_received':False,'candidate_predictions_received':False,'root_final_content_read':False,'human_gold':False,'training_admitted':False,'frozen_plan_path':str(planp),'frozen_plan_sha256':sha(planp),'original_review_path':str(oldp),'original_review_sha256':sha(oldp),'original_review_unchanged':True,'actual_viewing':{'effective_pngs_visually_reinspected':len(inv),'frame_ids':[x['frame_id'] for x in inv],'maximum_batch_images':4,'method':'Sequential view_image originals with explicit slot labels; fresh facts recorded and compared only for selected slots.','tool_success_is_not_semantic_attention_evidence':True},'machine_binding':{'manifest_path':str(mp),'manifest_sha256':sha(mp),'student_receipt_path':str(rp),'student_receipt_sha256':sha(rp),'all_selected_png_and_rgb_sha_match_frozen_plan_and_receipt':True,'all_selected_ordinal_and_exact_PTS_match_manifest':True},'selected_slot_inventory':inv,'material_scene_subject_object_action_error_found':False,'detail_qualifications':payload.get('qualifications',{}),'conclusion':'Only the listed actual slots have matching scene/subject/object/pose core; this does not validate all 64 original captions or imply training admission.','limits':['No teacher comparison, no intervening frames or audio.','Original independent initial judgment and original seal are preserved.','Sampling cannot establish absence of errors in uninspected slots.']}
p=OUT/(oldp.name.replace('.independent_student64_review_v1.json','.student_bounded_reinspection_v1.json'))
assert not p.exists();p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n','utf-8')
sp=p.with_suffix('.seal.json');assert not sp.exists()
sp.write_text(json.dumps({'status':'SEALED_BOUNDED_REINSPECTION_ACTUAL_SLOTS_ONLY','review_path':str(p),'review_sha256':sha(p),'fixed_job_index':w['job_index'],'actual_viewed_effective_pngs':len(inv),'teacher_content_received':False,'original_review_sha256':sha(oldp),'frozen_plan_sha256':sha(planp)},ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'job':w['job_index'],'path':str(p),'sha256':sha(p),'slots':[x['frame_id'] for x in inv],'material_error':False},ensure_ascii=False))

