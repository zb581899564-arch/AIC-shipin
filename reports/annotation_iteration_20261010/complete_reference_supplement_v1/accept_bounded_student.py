"""Verify only the actually reinspected fixed slots, never all64 captions."""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--review',required=True);ap.add_argument('--output',required=True)
 ap.add_argument('--root-read-selected-facts',action='store_true',required=True);a=ap.parse_args()
 p=Path(a.review).resolve(strict=True);out=Path(a.output).resolve();assert p.parent==R/'student_reviews' and out.parent==R and not out.exists()
 s=read(p);seal=read(p.with_name(p.stem+'.seal.json'));assert sha(p)==seal['review_sha256']
 assert s['not_new_blind_initial'] and not s['material_scene_subject_object_action_error_found']
 assert not any(s[k] for k in ('teacher_content_received','scores_received','candidate_predictions_received','root_final_content_read'))
 assert sha(s['original_review_path'])==s['original_review_sha256']
 fixed_path=Path(s['frozen_plan_path']);assert sha(fixed_path)==s['frozen_plan_sha256']
 fixed=next(x for x in read(fixed_path)['windows'] if x['job_index']==s['fixed_job_index'])
 assert fixed['review_sha256']==s['original_review_sha256']
 receipt_path=Path(s['machine_binding']['student_receipt_path']);receipt=read(receipt_path)
 assert sha(receipt_path)==s['machine_binding']['student_receipt_sha256'] and receipt['patch_inverse_exact'] and len(receipt['frames'])==64
 assert [v['frame_id'] for v in s['selected_slot_inventory']]==[f'F{i:02d}' for i in fixed['slots']]
 for row,frozen in zip(s['selected_slot_inventory'],fixed['input_binding']):
  frame=receipt['frames'][int(row['frame_id'][1:])]
  for k in ('frame_id','path','png_sha256','rgb_pixel_sha256'):assert row[k]==frozen[k]==frame[k]
  for k in ('source_ordinal','global_seconds_exact','local_seconds_exact'):assert row[k]==frame[k]
  assert row['tool_supply']['status']=='SUCCESS_IMAGE_RETURNED_AND_EMITTED' and row['tool_supply']['path']==row['path']
  assert sha(row['path'])==row['png_sha256']==row['actual_png_sha256']
  with Image.open(row['path']) as im:assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==row['rgb_pixel_sha256']==row['actual_rgb_pixel_sha256']
  assert row['fresh_visible_static_fact'] and row['original_sealed_fact']
 value=dict(status='PASS_ROOT_READ_SELECTED_FACTS_AND_RECHECK_CURRENT_BOUNDINGS_NOT_ALL64_CAPTION_CERTIFICATION',
  utc=datetime.now(timezone.utc).isoformat(),window_id=s['window_id'],original_blind_review=bind(s['original_review_path']),
  bounded_reinspection=bind(p),original_review_preserved=True,root_read_all_selected_fresh_facts=True,
  actual_selected_png_rgb_pts_bindings_rechecked=len(fixed['slots']),selected_slots=fixed['slots'],
  detail_qualifications=s['detail_qualifications'],new_blind_initial=False,teacher_exposure=False,
  root_direct_new_images=0,new_model_calls=0,new_optimizer_updates=0)
 encoded=json.dumps(value,ensure_ascii=False,indent=2)
 with out.open('x',encoding='utf-8') as f:f.write(encoded)
 print(json.dumps(dict(window_id=s['window_id'],selected_slots=len(fixed['slots']),output=bind(out))))
if __name__=='__main__':main()
