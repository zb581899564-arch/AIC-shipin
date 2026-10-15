import json,hashlib
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
OUT=Path("G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/student_reviews")
p=OUT/'16_EYqVtI9YWJA_W03.independent_student64_review_v1.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
o=json.loads(p.read_text('utf-8'));mp=Path(o['machine_binding']['manifest_path']);m=json.loads(mp.read_text('utf-8-sig'))
g=lambda a,b:str(Fraction(m['frames'][b]['global_seconds_exact'])-Fraction(m['frames'][a]['global_seconds_exact']))
assert sha(p)=='0284a35c129723d60d2e1adc8e3eea29ffff00d21a008b5199d948804ac62a37'
assert g(18,19)==g(44,45)=='7007/15000'
d={'schema':'student_boundary_arithmetic_errata_v1','utc':datetime.now(timezone.utc).isoformat(),'fixed_job_index':16,'teacher_content_received':False,'not_new_blind_initial':True,'original_review_path':str(p),'original_review_sha256':sha(p),'original_review_preserved':True,'machine_manifest_sha256':sha(mp),'cause':'Payload assembled before reading just-returned arithmetic verification output; original incorrect numeric assumption preserved. No new image content supplied or inferred.','corrections':[{'event_index':0,'slots':['F18','F19'],'old_offset_gap_seconds_exact':'1001/2000','correct_offset_gap_seconds_exact':g(18,19),'old_offset_status':'UNKNOWN; gap exceeds 0.5','correct_offset_status':'QUALIFIED local front-wheel high-to-near-ground transition interval F18/F19, 7007/15000 seconds <=0.5; exact contact instant unknown. Event onset remains UNKNOWN due F15/F16 cut and F16 already raised.'},{'event_index':3,'slots':['F44','F45'],'actual_onset_gap_seconds_exact':g(44,45),'correct_onset_status':'UNKNOWN because F44 wheel lower portion is outside frame and F45 already raised; actual time gap is <=0.5, not a >0.5 reason.'}],'decision_unchanged':'KEEP','student_target_observable_unchanged':'UNKNOWN','limits':['Only boundary arithmetic/status corrected; not new teacher comparison or gold.','Original visual facts and original seal are unchanged.']}
ep=OUT/'16_EYqVtI9YWJA_W03.student_boundary_arithmetic_errata_v1.json';assert not ep.exists()
ep.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
sp=ep.with_suffix('.seal.json');assert not sp.exists()
sp.write_text(json.dumps({'status':'SEALED_BOUNDARY_ARITHMETIC_ERRATA','review_path':str(ep),'review_sha256':sha(ep),'original_review_sha256':sha(p),'teacher_content_received':False},ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'path':str(ep),'sha256':sha(ep)},ensure_ascii=False))

