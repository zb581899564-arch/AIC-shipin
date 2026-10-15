"""Export visually reviewed probe targets without mixing duplicate teacher versions."""
from spatial_prepare import ROOT,load,validate,sha,save
from pathlib import Path
sid='PJrm840pAUI';out=ROOT/'exports/crop_provider_probe';counts={}
for provider,attempt in [('codex_crop','attempt_01'),('gemini_crop','attempt_01'),('gemini_crop','attempt_grid_low_01')]:
    draft=ROOT/'raw'/provider/sid/attempt/'draft_01.json' if provider=='gemini_crop' else ROOT/'raw'/provider/sid/'draft_01.json'
    review=draft.with_name('codex_visual_review_01.json')
    if not review.exists():continue
    m,doc,rows=validate(sid,draft);r=load(review);assert r['draft_sha256']==sha(draft)
    samples=[];labels=[]
    for row in rows:
        i=row['sample_index'];ratio=row['ratio'];f=m['frames'][i]
        c=next(c for c in r['checks'] if c['sample_index']==i and c['targetRatioWH']==ratio)
        record=dict(row,source_id=sid,source_group=m['source_group'],split=m['split'],provider=provider,attempt=attempt,
            frame_index=f['frame_index'],pts=f['pts'],time_base=f['time_base'],png_sha256=f['png_sha256'],media_sha256=m['media_sha256'],
            raw_sha256=sha(draft),review_sha256=sha(review),review=c,quality_reference='MODEL_REVIEWED_WEAK_LABEL_NOT_HUMAN_GOLD')
        labels.append(record)
        if c['verdict']!='PASS':continue
        assert row['state']=='CROP';x,y,w,h=row['box_xywh']
        prompt=f'Reframe this video frame to {ratio[0]}:{ratio[1]}. Preserve the chosen main subject and essential action or object. Source image is {f["width"]}x{f["height"]} pixels. Return ONLY JSON {{"box_xyw":[x,y,width]}} in original integer pixels. Height is width*{ratio[1]}/{ratio[0]}; keep the rectangle inside the source image.'
        samples.append(dict(id=f'{f["sample_id"]}:{ratio[0]}x{ratio[1]}',source_id=sid,source_group=m['source_group'],split=m['split'],
            images=[str(ROOT/'input'/sid/f['file'])],messages=[dict(role='user',content='<image>\n'+prompt),dict(role='assistant',content=__import__('json').dumps({'box_xyw':[x,y,w]},separators=(',',':')))],
            teacher_provider=provider,teacher_attempt=attempt,annotation_quality='MODEL_REVIEWED_WEAK_LABEL',label_record=record))
    prefix=provider+'_'+attempt;out.mkdir(parents=True,exist_ok=True)
    for name,arr in [('sft_train',samples),('labels',labels)]:
        (out/(prefix+'_'+name+'.jsonl')).write_text(''.join(__import__('json').dumps(v,ensure_ascii=False,separators=(',',':'))+'\n' for v in arr),encoding='utf-8')
    counts[prefix]=dict(reviewed_targets=len(labels),eligible_weak_sft=len(samples),vertical_eligible=sum(s['id'].endswith('9x16') for s in samples),
        horizontal_targets_are_full_source_or_fixed_policy=True)
save(out/'status.json',dict(source_id=sid,counts=counts,variants_are_alternatives_not_concat_training_rows=True,actual_student_training_started=False,
    production_decoder_unchanged=True,target_contract='New explicit original-pixel crop box task; existing center-only decoder is not modified.',all_counts_are_probe_not_corpus_completion=True))
print(counts)
