"""Three explicit new crop decisions after re-viewing the original source frames."""
from spatial_prepare import ROOT,load,save,sha,validate
from direct_annotation import render_checks
updates={
'Bhxk-O1Y7Ho':[(1,[9,16],[226,4,198,352],'重新选择面部肖像，左移保留脸颊；外围头发不作所选主体。')],
'LRw_obCPUt0':[(8,[9,16],[291,4,198,352],'右移保留男子完整面部、掌心和右侧指尖。')],
'xxdtq8mxegs':[(0,[16,9],[0,72,480,270],'下移保留完整绿色品牌标识、标语与底部网址。')]
}
for sid,changes in updates.items():
    old=ROOT/'raw/codex_crop'/sid/'draft_01.json';new=old.with_name('draft_02.json');assert not new.exists()
    doc=load(old);doc['prior_draft_sha256']=sha(old);doc['revision_method']='Explicit source-native visual correction, no clamping or inferred automatic shift'
    doc['changed_targets']=[dict(sample_index=i,targetRatioWH=r,new_box_xywh=b) for i,r,b,reason in changes]
    for i,r,b,reason in changes:
        c=next(c for f in doc['frames'] if f['sample_index']==i for c in f['crops'] if c['targetRatioWH']==r)
        c['box_xyw']=b;c['state']='CROP';c['reason']=reason
    save(new,doc);validate(sid,new);render_checks(sid,'02');print(sid)
