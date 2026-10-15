import json,hashlib
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
root=Path(__file__).parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reports=sorted(root.glob('*.native_review.json'))
assert [int(p.name[:2]) for p in reports]==list(range(3,24))
rows=[]
for p in reports:
 r=json.loads(p.read_text(encoding='utf-8'))
 h=sha(p)
 assert (root/(p.name.replace('.json','.sha256'))).read_text().split()[0]==h
 assert len(r['frames'])==64
 assert all(r[k] is False for k in ['teacher_content_received','candidatePredictionExposure','student_content_received','training_admitted'])
 assert r['new_optimizer_updates']==0 and r['full_domain_keep_no_unknown']
 job=Path(r['job'])
 assert sha(job/'manifest.json')==r['manifest_sha256'] and sha(job/'native_clock.json')==r['native_clock_sha256']
 for f in r['frames']:
  assert sha(f['path'])==f['current_png_sha256']==f['png_sha256']
  assert f['static_visual_fact'] and f['native_clock_identity_match'] and f['visually_inspected_original_png']
 s=r['domain_segments']; assert s[0]['first']==0 and s[-1]['last']==63
 assert all(a['last']+1==b['first'] and a['partition_interval_exact'][1]==b['partition_interval_exact'][0] for a,b in zip(s,s[1:]))
 assert s[0]['partition_interval_exact'][0]==r['domain_global_seconds_exact'][0] and s[-1]['partition_interval_exact'][1]==r['domain_global_seconds_exact'][1]
 for b in r['boundaries']:
  assert Fraction(b['width_exact'])==Fraction(b['bracket_global_seconds_exact'][1])-Fraction(b['bracket_global_seconds_exact'][0])
  assert b['needs_supplement_gt_half_second']==(Fraction(b['width_exact'])>Fraction(1,2))
 rows.append({'job_index':int(p.name[:2]),'file':str(p),'sha256':h,'frame_count':64,'segments':[{'verdict':x['verdict'],'first':x['first'],'last':x['last']} for x in s],'boundaries_count':len(r['boundaries']),'boundary_supplement_count':sum(x['needs_supplement_gt_half_second'] for x in r['boundaries']),'completeness_blockers':[{'event_id':e.get('id'),'blocker':e['completeness_blocker']} for e in r['events'] if e.get('completeness_blocker')]})
out={'status':'PASS_FIXED_21_NATIVE64_INITIAL_REVIEW_SEALS_IDENTITY_AND_DOMAIN','utc':datetime.now(timezone.utc).isoformat(),'owned_job_indices':list(range(3,24)),'windows':21,'actually_visually_inspected_original_pngs':1344,'current_png_sha_identity_checks':1344,'teacher_content_received':False,'candidatePredictionExposure':False,'student_content_received':False,'training_admitted':False,'new_optimizer_updates':0,'complete_domain_partitions':21,'boundary_supplement_count':sum(x['boundary_supplement_count'] for x in rows),'unknown_domain_segment_count':sum(s['verdict']=='UNKNOWN' for x in rows for s in x['segments']),'limitation':'Identity and partition validation does not replace visual judgement or resolve sample gaps. Initial seals remain unchanged. Root independently integrates external evidence.','reports':rows}
target=root/'fixed21_native_initial_review_acceptance.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'fixed21_native_initial_review_acceptance.sha256').write_text(sha(target)+'  '+target.name+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='reports'},ensure_ascii=False));print(sha(target))

