"""Validate immutable teacher drafts and render actual pixel crops for review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def validate(sid,path):
    m=load(ROOT/'input'/sid/'manifest.json');d=load(path)
    assert d['source_id']==sid and len(d['frames'])==12
    issues=[];rows=[];seen=set()
    for r in d['frames']:
        i=r['sample_index'];assert type(i)==int and 0<=i<12 and i not in seen;seen.add(i)
        f=m['frames'][i];src=ROOT/'input'/sid/f['file']
        assert r['frame_index']==f['frame_index'] and abs(r['pts_seconds']-f['pts_seconds'])<1e-8
        assert r['observed_file']==f['file'] and sha(src)==f['png_sha256']
        assert len(r['crops'])==2
        ratios=set()
        for c in r['crops']:
            ratio=tuple(c['targetRatioWH']);assert ratio in ((16,9),(9,16)) and ratio not in ratios;ratios.add(ratio)
            assert c['state'] in ('CROP','UNKNOWN') and isinstance(c['reason'],str) and c['reason']
            label=dict(sample_id=f['sample_id'],sample_index=i,ratio=list(ratio),state=c['state'],reason=c['reason'])
            if c['state']=='UNKNOWN':
                assert c.get('box_xyw') is None;rows.append(label);continue
            box=c['box_xyw'];assert len(box) in (3,4) and all(type(v)==int for v in box)
            x,y,w=box[:3];h=w*ratio[1]/ratio[0]
            assert h.is_integer();h=int(h)
            if len(box)==4:assert box[3]==h
            assert x>=0 and y>=0 and w>0 and h>0 and x+w<=f['width'] and y+h<=f['height']
            label['box_xywh']=[x,y,w,h];rows.append(label)
    assert seen==set(range(12))
    return m,d,rows
def render(sid,version='draft_01'):
    draft=ROOT/'raw/doubao'/sid/(version+'.json');m,d,rows=validate(sid,draft)
    out=ROOT/('review/doubao' if version=='draft_01' else 'review_final/doubao')/sid;out.mkdir(parents=True,exist_ok=True)
    images=[]
    for f in m['frames']:
        i=f['sample_index'];src=ROOT/'input'/sid/f['file'];im=Image.open(src).convert('RGB')
        width=im.width;parts=[('SOURCE',im)];files=[]
        for r in [r for r in rows if r['sample_index']==i]:
            ratio=r['ratio'];tag=f'{ratio[0]}x{ratio[1]}'
            if r['state']=='UNKNOWN':continue
            x,y,w,h=r['box_xywh'];crop=im.crop((x,y,x+w,y+h));cp=out/f'f{i:02d}_{tag}_actual.png'
            if not cp.exists():crop.save(cp)
            files.append(dict(ratio=ratio,box_xywh=r['box_xywh'],file=cp.name,sha256=sha(cp)))
            annotated=im.copy();ImageDraw.Draw(annotated).rectangle((x,y,x+w-1,y+h-1),outline=(255,30,30),width=3)
            parts.append((tag+' BOX',annotated));parts.append((tag+' ACTUAL',crop))
        panels=[]
        for title,p in parts:
            scale=min(360/p.height,640/p.width)
            p=p.resize((round(p.width*scale),round(p.height*scale)))
            panel=Image.new('RGB',(p.width,390),'#202020');panel.paste(p,(0,30));ImageDraw.Draw(panel).text((8,8),title,fill='white');panels.append(panel)
        sheet=Image.new('RGB',(sum(p.width for p in panels),420),'#202020');x=0
        ImageDraw.Draw(sheet).text((8,399),f'{sid} sample {i} native {f["frame_index"]} pts {f["pts_seconds"]:.6f}s',fill='white')
        for p in panels:sheet.paste(p,(x,0));x+=p.width
        cp=out/f'f{i:02d}_review.png'
        if not cp.exists():sheet.save(cp)
        images.append(dict(sample_index=i,review_image=str(cp),review_image_sha256=sha(cp),actual_crops=files))
    receipt=dict(status='PASS_IDENTITY_AND_GEOMETRY_ONLY',source_id=sid,draft_path=str(draft),draft_sha256=sha(draft),
        frames=12,ratio_targets=len(rows),crop_count=sum(r['state']=='CROP' for r in rows),unknown_count=sum(r['state']=='UNKNOWN' for r in rows),
        source_media_sha256=m['media_sha256'],visual_quality_independently_validated=False,images=images,
        utc=datetime.now(timezone.utc).isoformat())
    save(out/'render_manifest.json',receipt)
    print(json.dumps({'source_id':sid,'frames':12,'targets':len(rows),'render_manifest':str(out/'render_manifest.json')}),flush=True)
if __name__=='__main__':
    version='review_01' if '--review' in sys.argv else 'draft_01'
    ids=[a for a in sys.argv[1:] if a!='--review'] or [p.parent.name for p in (ROOT/'raw/doubao').glob('*/'+version+'.json')]
    for sid in ids:render(sid,version)
