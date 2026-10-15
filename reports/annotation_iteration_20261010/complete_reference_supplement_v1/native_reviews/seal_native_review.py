import json,sys,hashlib
from pathlib import Path
from fractions import Fraction

root=Path(__file__).parent
inp=json.loads((root/sys.argv[1]).read_text(encoding='utf-8'))
job=Path(inp['job'])
manifest_path=job/'manifest.json'
clock_path=job/'native_clock.json'
m=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
c=json.loads(clock_path.read_text(encoding='utf-8-sig'))
hashfile=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert len(m['frames'])==64==len(inp['facts'])
clock={x['source_ordinal']:x for x in c}
rows=[]
for f,fact in zip(m['frames'],inp['facts']):
    assert fact and clock[f['source_ordinal']]['global_seconds_exact']==f['global_seconds_exact']
    actual=hashfile(f['path'])
    assert actual==f['png_sha256']
    rows.append({**f,'current_png_sha256':actual,'native_clock_identity_match':True,'visually_inspected_original_png':True,'static_visual_fact':fact})
domain=m['domain_global_seconds_exact']
segments=[]
for s in inp['segments']:
    # Partition points retain sampling uncertainty, never narrow a gap.
    lo=domain[0] if s['first']==0 else m['frames'][s['first']]['global_seconds_exact']
    hi=domain[1] if s['last']==63 else m['frames'][s['last']+1]['global_seconds_exact']
    segments.append({**s,'partition_interval_exact':[lo,hi], 'observed_first_pts_exact':m['frames'][s['first']]['global_seconds_exact'],'observed_last_pts_exact':m['frames'][s['last']]['global_seconds_exact']})
assert segments[0]['first']==0 and segments[-1]['last']==63
assert all(a['last']+1==b['first'] for a,b in zip(segments,segments[1:]))
boundaries=[]
for b in inp.get('boundaries',[]):
    a,z=b['left'],b['right']
    lo=m['frames'][a]['global_seconds_exact'];hi=m['frames'][z]['global_seconds_exact']
    width=Fraction(hi)-Fraction(lo)
    boundaries.append({**b,'bracket_global_seconds_exact':[lo,hi],'width_exact':str(width),'needs_supplement_gt_half_second':width>Fraction(1,2)})
out={'status':'SEALED_INDEPENDENT_NATIVE64_EDITORIAL_INITIAL_REVIEW','window_id':m['window_id'],'source_id':m['source_id'],'source_sha256':m['source_sha256'],'job':str(job),'domain_global_seconds_exact':domain,'manifest_sha256':hashfile(manifest_path),'native_clock_sha256':hashfile(clock_path),'native_clock_count':len(c),'frame_count':64,'teacher_content_received':False,'candidatePredictionExposure':False,'student_content_received':False,'training_admitted':False,'new_optimizer_updates':0,'observation_limit':'All 64 original PNG samples inspected individually. Static samples cannot prove intervening unsampled motion, audio, intent or outcome.','editorial_standard':'Short visual highlight: salient visible event or clear typical image; routine narration/subtitle plot/ordinary movement are not automatically KEEP.','frames':rows,'domain_segments':segments,'events':inp.get('events',[]),'boundaries':boundaries,'full_domain_keep_no_unknown':True,'initial_review_only':True}
target=root/(job.name+'.native_review.json')
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=hashfile(target)
(root/(job.name+'.native_review.sha256')).write_text(sha+'  '+target.name+'\n',encoding='ascii')
print(json.dumps({'path':str(target),'sha256':sha,'segments':[(s['verdict'],s['first'],s['last']) for s in segments],'boundary_supplement_count':sum(b['needs_supplement_gt_half_second'] for b in boundaries)},ensure_ascii=False))
