from spatial_prepare import ROOT,load,sha,save,validate
sid='PJrm840pAUI';job=ROOT/'raw/gemini_crop'/sid/'attempt_grid_low_01';m,d,rows=validate(sid,job/'draft_01.json')
render=load(ROOT/'review/gemini_crop'/sid/'attempt_grid_low_01/draft_01/render_manifest.json')
bad={2:'实际竖裁图右边界截断鼻子/前侧面部轮廓，所述完整头脸未保留。',4:'实际竖裁图左边界穿过黑衣人物面部，手部和半张脸落在框外。',8:'实际竖裁图截断分开的双腿末端和支点，关键动作不完整。',10:'实际竖裁图左边界截断手持相机大部分，主体操作物体未完整保留。'}
checks=[]
for row in rows:
    i=row['sample_index'];ratio=row['ratio']
    state='UNKNOWN' if row['state']=='UNKNOWN' else ('REJECT' if ratio==[9,16] and i in bad else 'PASS')
    actual=None if row['state']=='UNKNOWN' else next(c for r in render['images'] if r['sample_index']==i for c in r['actual_crops'] if c['targetRatioWH']==ratio)
    checks.append(dict(sample_index=i,sample_id=row['sample_id'],targetRatioWH=ratio,verdict=state,actual_crop=actual,
        visible_evidence=bad[i] if state=='REJECT' else (row['reason'] if state=='UNKNOWN' else '实际图保留选定区域；横屏为预先固定的全图。'),
        review_method='Codex directly viewed actual ungridded crop PNGs in this turn'))
dest=job/'codex_visual_review_01.json';assert not dest.exists()
save(dest,dict(source_id=sid,teacher_provider='gemini_crop',teacher_attempt='attempt_grid_low_01',draft_sha256=sha(job/'draft_01.json'),checks=checks,
    counts={s:sum(c['verdict']==s for c in checks) for s in ['PASS','REJECT','UNKNOWN']},quality_reference='MODEL_VISUAL_REVIEW_NOT_HUMAN_GOLD'))
low=ROOT/'raw/gemini_crop'/sid/'attempt_low_01';raw=load(low/'draft_01.json')
save(low/'rejection.json',dict(status='REJECT_DECLARED_EXACT_ASPECT_RATIO',raw_sha256=sha(low/'draft_01.json'),
    affected_targets=[dict(sample_index=f['sample_index'],targetRatioWH=c['targetRatioWH'],box_xyw=c['box_xyw'],reason='202/360 is not exactly 9/16; raw fourth height differs from width*16/9') for f in raw['frames'] for c in f['crops'] if c['state']=='CROP' and c['targetRatioWH']==[9,16]],raw_preserved=True,coordinates_not_repaired=True))
