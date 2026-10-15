"""Record Codex visual review performed on actual rendered crops in this turn."""
from spatial_prepare import ROOT,load,save,sha,validate
sid='PJrm840pAUI'
def review(provider,attempt,rejected,unknown):
    raw=ROOT/'raw'/provider/sid/attempt/'draft_01.json' if provider=='gemini_crop' else ROOT/'raw'/provider/sid/'draft_01.json'
    manifest,doc,rows=validate(sid,raw)
    render=load(ROOT/'review'/provider/sid/attempt/'draft_01/render_manifest.json')
    assert render['draft_sha256']==sha(raw)
    checks=[]
    for r in rows:
        i=r['sample_index'];ratio=r['ratio'];bad=ratio==[9,16] and i in rejected
        if r['state']=='UNKNOWN':verdict='UNKNOWN';reason=unknown.get(i,r['reason']);actual=None
        else:
            verdict='REJECT' if bad else 'PASS'
            actual=next(c for p in render['images'] if p['sample_index']==i for c in p['actual_crops'] if c['targetRatioWH']==ratio)
            reason=rejected[i] if bad else ('全图16:9像素不新增裁断。' if ratio==[16,9] else '实际竖裁图保留所选主要可见区域；本判断为模型复核、不是人类金标。')
        checks.append(dict(sample_index=i,sample_id=r['sample_id'],targetRatioWH=ratio,verdict=verdict,visible_evidence=reason,actual_crop=actual,
            review_method='Codex viewed original PNGs and rendered actual crop PNGs; full-size 16:9 preserves original source pixels'))
    out=raw.with_name('codex_visual_review_01.json')
    assert not out.exists()
    save(out,dict(source_id=sid,teacher_provider=provider,teacher_attempt=attempt,draft_sha256=sha(raw),checks=checks,
        counts={s:sum(c['verdict']==s for c in checks) for s in ['PASS','REJECT','UNKNOWN']},
        quality_reference='MODEL_VISUAL_REVIEW_NOT_HUMAN_GOLD',unseen_frames_labeled=False))
    print(str(out))
review('gemini_crop','attempt_01',{
1:'实际竖裁图左边界截断所选紫衣人物的侧脸前缘，包含鼻口的部分落在框外；描述与保留效果不符。',
3:'实际竖裁图保留右侧旁人和建筑，前景蓝衣主角的头脸与大部分持机手均在框外，主体定位错误。'},
{8:'关键支撑动作横向过宽，不用硬裁的坐标充当正例。',10:'头部与手持相机核心横向过宽，不用硬裁的坐标充当正例。'})
review('codex_crop','attempt_01',{},
{1:'遮挡与运动模糊使关键动作无法可靠判断。',8:'双腿与支点无法同时保留。',10:'完整头部与手持相机无法同时保留。',11:'群像无唯一主角，整体保留要求与竖屏不相容。'})
