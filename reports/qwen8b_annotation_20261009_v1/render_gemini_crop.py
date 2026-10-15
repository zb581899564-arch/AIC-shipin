"""Render a Gemini crop draft without altering its coordinates or prior labels."""
import sys
from PIL import Image,ImageDraw
from spatial_prepare import ROOT,validate,save,sha
def render(sid,version='draft_01',attempt='attempt_01',provider='gemini_crop'):
    draft=ROOT/'raw'/provider/sid/attempt/(version+'.json') if provider=='gemini_crop' else ROOT/'raw'/provider/sid/(version+'.json')
    m,d,rows=validate(sid,draft);out=ROOT/'review'/provider/sid/attempt/version;out.mkdir(parents=True,exist_ok=True)
    receipt=dict(source_id=sid,draft_path=str(draft),draft_sha256=sha(draft),images=[])
    for f in m['frames']:
        i=f['sample_index'];im=Image.open(ROOT/'input'/sid/f['file']).convert('RGB');display=[];records=[]
        a=im.copy();draw=ImageDraw.Draw(a)
        for r in [x for x in rows if x['sample_index']==i]:
            if r['state']!='CROP':continue
            x,y,w,h=r['box_xywh'];ratio=r['ratio'];tag=f'{ratio[0]}x{ratio[1]}'
            color='red' if ratio==[9,16] else 'cyan';draw.rectangle((x,y,x+w-1,y+h-1),outline=color,width=3)
            cp=out/f'f{i:02d}_{tag}_actual.png';crop=im.crop((x,y,x+w,y+h));crop.save(cp)
            records.append(dict(targetRatioWH=ratio,box_xywh=r['box_xywh'],file=str(cp),sha256=sha(cp)))
            display.append((tag+' ACTUAL',crop))
        panels=[]
        for title,p in [('SOURCE BOXES (cyan=16:9 red=9:16)',a)]+display:
            scale=min(360/p.height,640/p.width);p=p.resize((round(p.width*scale),round(p.height*scale)))
            panel=Image.new('RGB',(p.width,410),'#202020');panel.paste(p,(0,30));ImageDraw.Draw(panel).text((6,8),title,fill='white');panels.append(panel)
        sheet=Image.new('RGB',(sum(p.width for p in panels),410),'#202020');left=0
        for p in panels:sheet.paste(p,(left,0));left+=p.width
        ImageDraw.Draw(sheet).text((6,389),f'{sid} frame {f["frame_index"]} sample {i} pts {f["pts_seconds"]:.6f}',fill='white')
        cp=out/f'f{i:02d}_review.png';sheet.save(cp)
        receipt['images'].append(dict(sample_index=i,review_image=str(cp),review_sha256=sha(cp),actual_crops=records))
    save(out/'render_manifest.json',receipt);print(str(out/'render_manifest.json'))
if __name__=='__main__':render(*sys.argv[1:])
