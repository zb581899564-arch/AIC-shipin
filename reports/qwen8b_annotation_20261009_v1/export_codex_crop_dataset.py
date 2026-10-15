"""Export the directly annotated, actually crop-reviewed source versions without duplicates."""
from pathlib import Path
import json
from spatial_prepare import ROOT,load,save,validate,sha
base=ROOT/'raw/codex_crop/JgHubY5Vw3Y';draft=base/'draft_02.json';old=load(base/'codex_visual_review_01.json');render=load(ROOT/'review/codex_crop/JgHubY5Vw3Y/attempt_01/draft_02/render_manifest.json')
review=base/'codex_visual_review_02.json'
if not review.exists():
    checks=[]
    for c in old['checks']:
        r=dict(c)
        if c['actual_crop'] is not None:
            actual=next(a for f in render['images'] if f['sample_index']==c['sample_index'] for a in f['actual_crops'] if a['targetRatioWH']==c['targetRatioWH'])
            if c['sample_index']==4 and c['targetRatioWH']==[9,16]:
                r['verdict']='PASS';r['visible_evidence']='已实际查看新竖裁图：操作手前缘不再被左框新增截断，车轴快拆杆接触区域保留；原图运动模糊仍然存在。'
            else:assert actual['sha256']==c['actual_crop']['sha256'],'Unchanged crop must retain exact bytes'
            r['actual_crop']=actual
        checks.append(r)
    save(review,dict(source_id='JgHubY5Vw3Y',draft_sha256=sha(draft),checks=checks,quality_reference='MODEL_VISUAL_REVIEW_NOT_HUMAN_GOLD',
        prior_review_sha256=sha(base/'codex_visual_review_01.json'),unchanged_actual_crops_reused_by_exact_png_sha=True))
out=ROOT/'exports/codex_crop_v1';out.mkdir(parents=True,exist_ok=True)
labels=[];sft={'train':[],'validation':[]};source_counts=[]
for directory in sorted((ROOT/'raw/codex_crop').iterdir()):
    if not directory.is_dir():continue
    sid=directory.name;version='02' if (directory/'codex_visual_review_02.json').exists() else '01'
    draft=directory/f'draft_{version}.json';review=directory/f'codex_visual_review_{version}.json'
    if not review.exists():continue
    m,doc,rows=validate(sid,draft);rr=load(review);assert sha(draft)==rr['draft_sha256'];eligible=0
    for row in rows:
        i=row['sample_index'];f=m['frames'][i];ratio=row['ratio'];c=next(c for c in rr['checks'] if c['sample_index']==i and c['targetRatioWH']==ratio)
        if c['actual_crop'] is not None:assert sha(Path(c['actual_crop']['file']))==c['actual_crop']['sha256']
        record=dict(row,source_id=sid,source_group=m['source_group'],split=m['split'],frame_index=f['frame_index'],pts=f['pts'],time_base=f['time_base'],
            image_path=str(ROOT/'input'/sid/f['file']),png_sha256=f['png_sha256'],source_media_sha256=m['media_sha256'],
            draft_path=str(draft),draft_sha256=sha(draft),review_path=str(review),review_sha256=sha(review),visual_check=c,
            quality_reference='CODEX_DIRECT_MODEL_ANNOTATION_AND_SELF_REVIEW_NOT_HUMAN_GOLD')
        labels.append(record)
        if c['verdict']!='PASS':continue
        assert row['state']=='CROP';x,y,w,h=row['box_xywh'];eligible+=1
        prompt=f'Reframe this video frame to {ratio[0]}:{ratio[1]}. Preserve the chosen main visible subject and essential action or object. Source image is {f["width"]}x{f["height"]} pixels. Return ONLY JSON {{"box_xyw":[x,y,width]}} in original integer pixels. Height is width*{ratio[1]}/{ratio[0]}; keep the rectangle inside the source image.'
        sft[m['split']].append(dict(id=f'{f["sample_id"]}:{ratio[0]}x{ratio[1]}',source_id=sid,source_group=m['source_group'],images=[record['image_path']],
            messages=[dict(role='user',content='<image>\n'+prompt),dict(role='assistant',content=json.dumps({'box_xyw':[x,y,w]},separators=(',',':')))],
            annotation_quality='MODEL_ANNOTATED_WEAK_LABEL',label_record=record))
    source_counts.append(dict(source_id=sid,split=m['split'],frames=12,ratio_targets=24,eligible_targets=eligible,selected_version=version))
for name,arr in [('labels',labels),('crop_sft_train',sft['train']),('crop_sft_validation',sft['validation'])]:
    (out/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in arr),encoding='utf-8')
ids=[r['id'] for split in sft.values() for r in split];assert len(ids)==len(set(ids))
status=dict(status='PASS_CURRENT_DIRECT_ANNOTATION_BATCH_IDENTITY_GEOMETRY_ACTUAL_CROP_REVIEW_AND_EXPORT',sources=source_counts,
    expected_corpus_sources=50,annotated_sources=len(source_counts),annotated_frames=len(source_counts)*12,ratio_records=len(labels),
    weak_sft_rows={k:len(v) for k,v in sft.items()},unknown_or_rejected_targets=sum(r['visual_check']['verdict']!='PASS' for r in labels),
    vertical_eligible=sum(r['id'].endswith('9x16') for arr in sft.values() for r in arr),
    raw_provider_variants_not_concatenated=True,actual_student_training_started=False,
    target_contract='New explicit original-pixel box task; existing production center-only decoder remains unchanged.',
    corpus_complete=len(source_counts)==50,
    limitations=[f'Coverage is {len(source_counts)}/50 sources and {len(source_counts)*12}/600 fixed sampled frames; this is not annotation of every native video frame.','Labels are direct model annotation and self-review, not human gold.','Full-image 16:9 labels are simple; vertical eligible count reported separately.'])
save(out/'acceptance.json',status);print(json.dumps(status,ensure_ascii=False,indent=2))
