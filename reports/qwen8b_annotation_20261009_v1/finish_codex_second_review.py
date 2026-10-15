from spatial_prepare import ROOT,load,save,sha,validate
sid='JgHubY5Vw3Y';base=ROOT/'raw/codex_crop'/sid;old=base/'draft_01.json';d=load(old)
render=load(ROOT/'review/codex_crop'/sid/'attempt_01/draft_01/render_manifest.json')
checks=[]
for frame in d['frames']:
    i=frame['sample_index']
    for c in frame['crops']:
        ratio=c['targetRatioWH'];bad=i==4 and ratio==[9,16]
        verdict='UNKNOWN' if c['state']=='UNKNOWN' else ('REJECT' if bad else 'PASS')
        actual=None if c['state']=='UNKNOWN' else next(c for r in render['images'] if r['sample_index']==i for c in r['actual_crops'] if c['targetRatioWH']==ratio)
        checks.append(dict(sample_index=i,targetRatioWH=ratio,verdict=verdict,actual_crop=actual,
            visible_evidence='操作手左边缘贴框并疑似新增截断，保留初稿隔离并另存修订。' if bad else (c['reason'] if verdict=='UNKNOWN' else '已查看实际竖裁图，或横屏为完整原图且不新增截断。')))
review=base/'codex_visual_review_01.json';assert not review.exists();save(review,dict(source_id=sid,draft_sha256=sha(old),checks=checks,quality_reference='MODEL_VISUAL_REVIEW_NOT_HUMAN_GOLD'))
# New semantic position chosen by Codex from original and actual crop, not validator clamping.
frame=next(r for r in d['frames'] if r['sample_index']==4);c=next(c for c in frame['crops'] if c['targetRatioWH']==[9,16]);c['box_xyw']=[198,4,198,352];c['reason']='根据实际裁图左移16像素，保留操作手与快拆杆核心，舍弃外侧轮圈。'
d['revision_parent_sha256']=sha(old);d['revision_reason']='Direct Codex visual correction of sample4 after actual raster crop was viewed'
new=base/'draft_02.json';assert not new.exists();save(new,d);validate(sid,new);print(str(new))
