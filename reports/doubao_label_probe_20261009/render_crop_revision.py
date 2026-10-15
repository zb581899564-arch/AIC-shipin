"""Show unchanged first-pass and self-reviewed teacher crops side by side."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

root=Path(__file__).resolve().parent
meta=json.loads((root/'input/keyframes_v1/manifest.json').read_text(encoding='utf-8'))
versions=[json.loads((root/f'raw/{v}/crop_keyframes.json').read_text(encoding='utf-8')) for v in ['image_v2','image_v3']]
rows=[{f['probe_index']:f for f in doc['frames']} for doc in versions]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
preview=Image.new('RGB',(680,1760),'#f5f7f9')
draw=ImageDraw.Draw(preview)
for index,item in enumerate(meta['frames']):
    original=Image.open(root/'input/keyframes_v1'/item['file']).convert('RGB')
    marked=original.copy()
    top=index*220
    draw.text((8,top+3),f"{item['file']} / 源帧{item['frame_index']} / {item['pts_seconds']:.3f}s",font=font,fill='#16202c')
    for data,label,color,left in zip(rows,['豆包初稿','豆包复核'],['#e95096','#00b7c5'],[414,548]):
        crop=next(c for c in data[index]['crops'] if c['targetRatioWH']==[9,16])
        draw.text((left,top+3),label,font=font,fill=color)
        if crop['state']=='UNKNOWN':
            draw.text((left,top+105),'UNKNOWN',font=font,fill='#16202c')
            continue
        x,y,w=crop['box_xyw']
        h=w*16/9
        ImageDraw.Draw(marked).rectangle((x,y,x+w-1,y+h-1),outline=color,width=3)
        preview.paste(original.transform((101,180),Image.Transform.EXTENT,(x,y,x+w,y+h),Image.Resampling.BICUBIC),(left,top+27))
    preview.paste(marked.resize((320,180),Image.Resampling.LANCZOS),(8,top+27))
preview.save(root/'crop_revision_comparison.png')
preview.crop((0,1100,680,1760)).save(root/'action_crop_revision.png')
print(root/'action_crop_revision.png')
