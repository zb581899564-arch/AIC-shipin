"""Representative accepted samples at native pixels, with no edits to source RGB."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports/codex_crop_v1'
rows=[json.loads(t) for t in (OUT/'labels.jsonl').read_text(encoding='utf-8').splitlines()]
chosen=[('JgHubY5Vw3Y',4),('GsAD1KT1xo8',7),('xxdtq8mxegs',2),('WG0MBPpPC6I',8)]
tile_w=870;tile_h=405;canvas=Image.new('RGB',(tile_w*2,tile_h*2),'#202020');d=ImageDraw.Draw(canvas);bindings=[]
for n,(sid,i) in enumerate(chosen):
    r=next(r for r in rows if r['source_id']==sid and r['sample_index']==i and r['ratio']==[9,16]);assert r['visual_check']['verdict']=='PASS'
    original=Image.open(r['image_path']).convert('RGB');actual=r['visual_check']['actual_crop'];crop=Image.open(actual['file']).convert('RGB')
    ox=n%2*tile_w;oy=n//2*tile_h
    d.text((ox+8,oy+5),f'{sid} native frame {r["frame_index"]} / sample {i}   MODEL WEAK LABEL',fill='white')
    canvas.paste(original,(ox+8,oy+25));canvas.paste(crop,(ox+660,oy+25))
    d.text((ox+8,oy+387),'SOURCE ORIGINAL PIXELS',fill='white');d.text((ox+570,oy+387),f'9:16 {r["box_xywh"]}',fill='#fff0a0')
    bindings.append(dict(source_id=sid,sample_index=i,frame_index=r['frame_index'],pts=r['pts'],time_base=r['time_base'],source_png_sha256=r['png_sha256'],actual_crop_sha256=actual['sha256'],box_xywh=r['box_xywh'],source_paste_xy=[ox+8,oy+25],crop_paste_xy=[ox+660,oy+25],pixels_not_resized=True))
dest=OUT/'representative_native_crops.png';assert not dest.exists();canvas.save(dest)
(OUT/'representative_native_crops_manifest.json').write_text(json.dumps(dict(purpose='Four representative accepted weak labels; not overall dataset quality proof',sources=bindings,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(dest)
