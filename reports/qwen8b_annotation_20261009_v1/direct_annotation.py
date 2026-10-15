"""Source-bound montage and persistence helpers for direct Codex visual annotation.
No semantic detector or default crop: every choice is supplied by the annotating model.
"""
from pathlib import Path
from fractions import Fraction
from PIL import Image,ImageDraw
from spatial_prepare import ROOT,load,save,sha,validate
def sizes(W,H,r):
    w=int(min(Fraction(W),Fraction(H*r[0],r[1]))//r[0])*r[0]
    return w,w*r[1]//r[0]
def prepare(sid):
    m=load(ROOT/'input'/sid/'manifest.json');W=m['frames'][0]['width'];H=m['frames'][0]['height']
    tw=W+38;th=H+28;canvas=Image.new('RGB',(tw*3,th*4),'#202020');d=ImageDraw.Draw(canvas);bindings=[]
    for f in m['frames']:
        path=ROOT/'input'/sid/f['file'];assert sha(path)==f['png_sha256'];im=Image.open(path).convert('RGB');assert im.size==(W,H)
        i=f['sample_index'];x=(i%3)*tw+38;y=(i//3)*th+28;canvas.paste(im,(x,y))
        d.text((x,y-22),f'{i:02d} {sid} native={f["frame_index"]} pts={f["pts_seconds"]:.3f}',fill='white')
        for px in range(0,W,80):d.text((x+px,y-10),str(px),fill='yellow')
        for py in range(0,H,80):d.text((x-30,y+py),str(py),fill='yellow')
        bindings.append(dict(sample_index=i,source_file=str(path),png_sha256=sha(path),paste_xy=[x,y],source_width=W,source_height=H))
    out=ROOT/'direct_view'/sid;out.mkdir(parents=True,exist_ok=True);dest=out/'originals.png'
    if not dest.exists():canvas.save(dest)
    save(out/'originals_manifest.json',dict(source_id=sid,view_file=str(dest),view_sha256=sha(dest),
        transformation='Each original RGB frame pasted at native resolution with coordinate numbers OUTSIDE pixels; no resize or source pixel edit',frames=bindings))
    print(dict(source_id=sid,split=m['split'],size=[W,H],horizontal_max=sizes(W,H,(16,9)),vertical_max=sizes(W,H,(9,16)),view=str(dest)))
def label(sid,choices,version='01'):
    # rows: [visible caption, horizontal x/y or UNKNOWN, vertical x/y or UNKNOWN, vertical reason]; optional horizontal reason.
    assert len(choices)==12
    m=load(ROOT/'input'/sid/'manifest.json');raw=ROOT/'raw/codex_crop'/sid/f'draft_{version}.json';assert not raw.exists()
    vm=load(ROOT/'direct_view'/sid/'originals_manifest.json');assert sha(Path(vm['view_file']))==vm['view_sha256']
    rows=[]
    for f,c in zip(m['frames'],choices):
        i=f['sample_index'];caption,hxy,vxy,vr=c[:4];hr=c[4] if len(c)>4 else '保留主要可见内容；完整原图或最大合法横框。'
        crops=[]
        for r,xy,reason in [([16,9],hxy,hr),([9,16],vxy,vr)]:
            w,h=sizes(f['width'],f['height'],r)
            box=None if xy is None else [xy[0],xy[1],w,h]
            crops.append(dict(targetRatioWH=r,state='UNKNOWN' if box is None else 'CROP',box_xyw=box,reason=reason))
        rows.append(dict(sample_index=i,frame_index=f['frame_index'],pts_seconds=f['pts_seconds'],observed_file=f['file'],visible_content=caption,focus_bounds_xyxy=None,crops=crops))
    save(raw,dict(source_id=sid,annotator_ui='Codex direct native-pixel montage annotation',frames=rows,observed_files=[f['file'] for f in m['frames']],
        source_montage_manifest_sha256=sha(ROOT/'direct_view'/sid/'originals_manifest.json'),
        observation_method='All 12 original frames seen in source-bound native-resolution lossless montage via view_image original detail',
        coordinates_selected_by_current_model=True,quality_reference='MODEL_ANNOTATION_NOT_HUMAN_GOLD'))
    validate(sid,raw);render_checks(sid,version);print(str(raw))
def render_checks(sid,version='01'):
    raw=ROOT/'raw/codex_crop'/sid/f'draft_{version}.json';m,d,rows=validate(sid,raw)
    out=ROOT/'direct_review'/sid/f'draft_{version}';out.mkdir(parents=True,exist_ok=True);images=[]
    for r in rows:
        if r['state']=='UNKNOWN':continue
        f=m['frames'][r['sample_index']];im=Image.open(ROOT/'input'/sid/f['file']).convert('RGB');x,y,w,h=r['box_xywh'];crop=im.crop((x,y,x+w,y+h));tag=f'{r["ratio"][0]}x{r["ratio"][1]}'
        p=out/f'f{r["sample_index"]:02d}_{tag}_actual.png'
        if not p.exists():crop.save(p)
        images.append(dict(sample_index=r['sample_index'],targetRatioWH=r['ratio'],box_xywh=r['box_xywh'],file=str(p),sha256=sha(p),source_png_sha256=f['png_sha256'],source_is_full_image=(x,y,w,h)==(0,0,f['width'],f['height'])))
    views={}
    for r in ([16,9],[9,16]):
        w,h=sizes(m['frames'][0]['width'],m['frames'][0]['height'],r);tw=w+8;th=h+24;canvas=Image.new('RGB',(tw*3,th*4),'#202020');draw=ImageDraw.Draw(canvas)
        for i in range(12):
            x=(i%3)*tw;y=(i//3)*th;draw.text((x+4,y+4),f'{i:02d} {r[0]}:{r[1]}',fill='white')
            item=next((a for a in images if a['sample_index']==i and a['targetRatioWH']==r),None)
            if item:canvas.paste(Image.open(item['file']),(x,y+24))
            else:draw.text((x+4,y+50),'UNKNOWN',fill='orange')
        p=out/f'{r[0]}x{r[1]}_actuals.png'
        if not p.exists():canvas.save(p)
        views[f'{r[0]}x{r[1]}']=dict(file=str(p),sha256=sha(p))
    save(out/'render_manifest.json',dict(source_id=sid,draft_path=str(raw),draft_sha256=sha(raw),images=images,views=views))
def review(sid,rejected=None,version='01',notes=None):
    rejected=rejected or {};notes=notes or {};raw=ROOT/'raw/codex_crop'/sid/f'draft_{version}.json';m,d,rows=validate(sid,raw)
    render=load(ROOT/'direct_review'/sid/f'draft_{version}/render_manifest.json');assert render['draft_sha256']==sha(raw)
    checks=[]
    for r in rows:
        i=r['sample_index'];ratio=r['ratio'];key=(i,tuple(ratio));actual=next((a for a in render['images'] if a['sample_index']==i and a['targetRatioWH']==ratio),None)
        state='UNKNOWN' if r['state']=='UNKNOWN' else ('REJECT' if key in rejected else 'PASS')
        checks.append(dict(sample_index=i,sample_id=r['sample_id'],targetRatioWH=ratio,verdict=state,actual_crop=actual,
            visible_evidence=rejected.get(key,notes.get(key,r['reason'] if state=='UNKNOWN' else '已查看实际裁图，主要所选区域保留；不宣称人类质量金标。')),
            review_method='Codex viewed actual crop montage at native pixel resolution; full-source crops reuse source observation with exact identity'))
    p=raw.with_name(f'codex_visual_review_{version}.json');assert not p.exists();save(p,dict(source_id=sid,draft_sha256=sha(raw),checks=checks,quality_reference='MODEL_VISUAL_REVIEW_NOT_HUMAN_GOLD',actual_crop_render_manifest_sha256=sha(ROOT/'direct_review'/sid/f'draft_{version}/render_manifest.json')))
    print(dict(source_id=sid,counts={s:sum(c['verdict']==s for c in checks) for s in ['PASS','REJECT','UNKNOWN']}))
def wide_source(sid,captions,vertical,unknown_horizontal=()):
    """Explicit model decision to retain each viewed native 640x360 source horizontally.
    Vertical dictionary supplies individual model-selected coordinates and rationale;
    absent entries deliberately remain UNKNOWN, never a centered fallback.
    """
    m=load(ROOT/'input'/sid/'manifest.json')
    assert len(captions)==12 and all((f['width'],f['height'])==(640,360) for f in m['frames'])
    choices=[]
    for i,caption in enumerate(captions):
        v=vertical.get(i)
        choices.append([caption,None if i in unknown_horizontal else [0,0],None if v is None else [v[0],v[1]],
                       '无法可靠在窄竖框保留该帧的主要内容与关键动作。' if v is None else v[2],
                       '原生横图已逐帧查看，保留全部原图像素。' if i not in unknown_horizontal else '无法确认可见内容，保留未知。'])
    label(sid,choices)
if __name__=='__main__':
    import sys
    for sid in sys.argv[1:]:prepare(sid)
