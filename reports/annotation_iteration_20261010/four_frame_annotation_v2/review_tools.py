"""Local inspection artifacts; no source-image modifications or model calls."""
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'w01_editorial_diagnostic_v1'

def sheets(phase):
    frames=json.loads((OLD/f'{phase}_index.json').read_text(encoding='utf-8-sig'))['frames']
    out=ROOT/'inspection'/phase
    out.mkdir(parents=True,exist_ok=True)
    for start in range(0,64,4):
        target=out/f'{start:02}_{start+3:02}.png'
        if target.exists(): continue
        # Four originals at their full resolution, with external identity labels.
        images=[Image.open(r['path']).convert('RGB') for r in frames[start:start+4]]
        w=max(im.width for im in images);h=max(im.height for im in images)+32
        canvas=Image.new('RGB',(w*2,h*2),'#ffffff');draw=ImageDraw.Draw(canvas)
        for n,(im,ref) in enumerate(zip(images,frames[start:start+4])):
            x=(n%2)*w;y=(n//2)*h
            draw.text((x+8,y+8),f"{phase} {ref['frame_id']} ordinal={ref['source_ordinal']}",fill='black')
            canvas.paste(im,(x,y+32))
        canvas.save(target)
    print(str(out))

if __name__=='__main__': sheets(sys.argv[1])
