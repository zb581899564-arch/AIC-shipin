import json, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image

ROOT=Path('G:/ai/AIC视频/reports/annotation_iteration_20261010')
OUT=ROOT/'complete_reference_supplement_v1/student_reviews'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seal(job_index, payload):
    jobs=json.loads((ROOT/'slot6_silver24_v1/observations/jobs.json').read_text('utf-8-sig'))['jobs']
    job=Path(jobs[job_index]); mp=job/'manifest.json'; rp=job/'student_views/receipt.json'
    m=json.loads(mp.read_text('utf-8-sig')); r=json.loads(rp.read_text('utf-8-sig'))
    assert r['window_id']==m['window_id'] and sha(mp)==r['manifest_sha256']
    assert len(r['frames'])==64 and len(payload['frame_notes'])==64
    inventory=[]
    for i,(f,n) in enumerate(zip(r['frames'],payload['frame_notes'])):
        assert f['frame_id']==f'F{i:02d}'
        p=Path(f['path']); png=sha(p)
        with Image.open(p) as im:
            rgb=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest(); size=list(im.size)
        assert png==f['png_sha256'] and rgb==f['rgb_pixel_sha256']
        assert f['source_ordinal']==m['frames'][i]['source_ordinal']
        assert f['global_seconds_exact']==m['frames'][i]['global_seconds_exact']
        inventory.append(dict(f,actual_png_sha256=png,actual_rgb_pixel_sha256=rgb,size=size,visible_static_fact=n))
    document={
      'schema':'independent_student64_visibility_review_v1',
      'review_utc':datetime.now(timezone.utc).isoformat(), 'fixed_job_index':job_index,
      'window_id':m['window_id'], 'domain_global_seconds_exact':m['domain_global_seconds_exact'],
      'teacher_content_received':False,'scores_received':False,'candidate_predictions_received':False,
      'human_gold':False,'training_admitted':False,'full_native_frames_observed':False,
      'actual_viewing':{'effective_input_pngs_visually_inspected':64,'frame_ids':[f'F{i:02d}' for i in range(64)],'method':'tools.view_image originals emitted in ordered groups of four; each slot visually inspected; no contact sheet/no decoding','tool_success_is_not_semantic_attention_evidence':True},
      'machine_binding':{'manifest_path':str(mp),'manifest_sha256':sha(mp),'student_receipt_path':str(rp),'student_receipt_sha256':sha(rp),'receipt_status':r['status'],'normalized_tensor_sha256':r['normalized_tensor_sha256'],'processor_binding_sha256':r['processor_binding_sha256'],'frame_count':64,'all_png_sha256_match_receipt':True,'all_rgb_pixel_sha256_match_receipt':True,'all_source_ordinals_and_exact_PTS_match_manifest':True},
      'student_view_inventory':inventory,
      'independent_initial_judgment':payload['judgment'],
      'visible_sequences':payload.get('sequences',[]),
      'scene_changes':payload.get('scene_changes',[]),
      'limits':payload.get('limits',[])+['Only 64 sampled effective student inputs inspected; intervening native frames and audio unknown.','Short highlight editor initial judgment, not human gold or teacher comparison.']}
    p=OUT/(job.name+'.independent_student64_review_v1.json')
    assert not p.exists(), 'Refusing to overwrite sealed review'
    p.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n','utf-8')
    sp=p.with_suffix('.seal.json')
    sp.write_text(json.dumps({'status':'SEALED_INDEPENDENT_STUDENT64_REVIEW','review_path':str(p),'review_sha256':sha(p),'teacher_content_received':False,'fixed_job_index':job_index,'window_id':m['window_id'],'actual_viewed_effective_pngs':64},ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'review':str(p),'sha256':sha(p),'seal':str(sp),'decision':payload['judgment']['decision']},ensure_ascii=False))
if __name__=='__main__':
    seal(int(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text('utf-8-sig')))
