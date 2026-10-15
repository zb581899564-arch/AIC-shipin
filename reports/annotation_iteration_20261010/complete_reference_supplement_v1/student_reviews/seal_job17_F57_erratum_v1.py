import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
root=Path('G:/ai/AIC视频/reports/annotation_iteration_20261010')
out=root/'complete_reference_supplement_v1/student_reviews'
old=out/'17_EYqVtI9YWJA_W04.independent_student64_review_v1.json'
olds=old.with_suffix('.seal.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
o=json.loads(old.read_text('utf-8-sig'));s=json.loads(olds.read_text('utf-8-sig'))
assert sha(old)==s['review_sha256']
job=Path(json.loads((root/'slot6_silver24_v1/observations/jobs.json').read_text('utf-8-sig'))['jobs'][17])
rp=job/'student_views/receipt.json';mp=job/'manifest.json'
r=json.loads(rp.read_text('utf-8-sig'));m=json.loads(mp.read_text('utf-8-sig'))
assert sha(mp)==r['manifest_sha256'] and o['machine_binding']['student_receipt_sha256']==sha(rp)
f=r['frames'][57];impath=Path(f['path'])
assert f['frame_id']=='F57' and f['source_ordinal']==m['frames'][57]['source_ordinal'] and f['global_seconds_exact']==m['frames'][57]['global_seconds_exact']
with Image.open(impath) as im: rgb=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest();size=list(im.size)
assert sha(impath)==f['png_sha256']==o['student_view_inventory'][57]['actual_png_sha256'] and rgb==f['rgb_pixel_sha256']
p=json.loads((out/'job17_F57_erratum_payload_v1.json').read_text('utf-8-sig'))
d=dict(schema='student_local_pixel_fact_errata_v1',review_utc=datetime.now(timezone.utc).isoformat(),fixed_job_index=17,window_id=r['window_id'],teacher_content_received=False,scores_received=False,candidate_predictions_received=False,root_pixel_correction_received=True,new_blind_initial=False,human_gold=False,original_review_path=str(old),original_review_sha256=sha(old),original_review_and_seal_unchanged=True,actual_effective_png_reinspected_count=1,machine_binding=dict(manifest_path=str(mp),manifest_sha256=sha(mp),receipt_path=str(rp),receipt_sha256=sha(rp),frame=dict(f,actual_png_sha256=sha(impath),actual_rgb_pixel_sha256=rgb,size=size)),original_visible_static_fact=o['student_view_inventory'][57]['visible_static_fact'],**{k:v for k,v in p.items() if k not in ['root_pixel_correction_received','new_blind_initial']})
dest=out/'17_EYqVtI9YWJA_W04.F57_actual_pixel_errata_v1.json';assert not dest.exists()
dest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
sealpath=dest.with_suffix('.seal.json');assert not sealpath.exists()
sealpath.write_text(json.dumps(dict(status='SEALED_ROOT_EXPOSED_LOCAL_PIXEL_ERRATUM',review_path=str(dest),review_sha256=sha(dest),original_review_sha256=sha(old),actual_reinspected_effective_pngs=1,teacher_content_received=False,new_blind_initial=False),ensure_ascii=False,indent=2)+'\n','utf-8')
assert sha(old)==s['review_sha256']
print(json.dumps(dict(review=str(dest),sha256=sha(dest),original_sha256=sha(old)),ensure_ascii=False))

