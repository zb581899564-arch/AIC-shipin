"""Render the teacher's unchanged first-pass crop boxes for feedback."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

root = Path(__file__).resolve().parent
manifest = json.loads((root/'input/keyframes_v1/manifest.json').read_text(encoding='utf-8'))
labels = json.loads((root/'raw/image_v2/crop_keyframes.json').read_text(encoding='utf-8'))
out = root/'input/crop_review_v1'
out.mkdir(exist_ok=False)
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
rows = {r['probe_index']: r for r in labels['frames']}
for item in manifest['frames']:
    row = rows[item['probe_index']]
    crop = next(c for c in row['crops'] if c['targetRatioWH'] == [9,16])
    x,y,w = crop['box_xyw']
    h = w*16/9
    source = Image.open(root/'input/keyframes_v1'/item['file']).convert('RGB')
    panel = Image.new('RGB', (930,410), '#f4f7f9')
    marked = source.copy()
    ImageDraw.Draw(marked).rectangle((x,y,x+w-1,y+h-1), outline='#00b7c5',width=3)
    panel.paste(marked,(8,40))
    panel.paste(source.transform((202,359),Image.Transform.EXTENT,(x,y,x+w,y+h),Image.Resampling.BICUBIC),(694,40))
    draw = ImageDraw.Draw(panel)
    draw.text((8,8),f"k{item['probe_index']:02d} 原图640x360 / 青色=你初稿9:16框 {crop['box_xyw']}",font=font,fill='#16202c')
    draw.text((694,8),'实际裁出画面',font=font,fill='#16202c')
    panel.save(out/f"review_k{item['probe_index']:02d}.png")
print(out)
