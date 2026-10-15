"""Create labeled coordinate aids; bind every derived PNG to its original frame."""
from PIL import Image,ImageDraw,ImageFont
from spatial_prepare import ROOT,load,save,sha
sid='PJrm840pAUI';m=load(ROOT/'input'/sid/'manifest.json');out=ROOT/'input_coordinate_grid'/sid;out.mkdir(parents=True,exist_ok=True)
rows=[]
for f in m['frames']:
    src=ROOT/'input'/sid/f['file'];assert sha(src)==f['png_sha256'];im=Image.open(src).convert('RGB');draw=ImageDraw.Draw(im)
    for x in range(0,im.width,40):
        draw.line((x,0,x,im.height-1),fill=(80,190,80),width=1)
        if x%80==0:draw.rectangle((x+1,2,min(x+32,im.width-1),17),fill='black');draw.text((x+2,3),str(x),fill='yellow')
    for y in range(0,im.height,40):
        draw.line((0,y,im.width-1,y),fill=(80,190,80),width=1)
        draw.rectangle((2,y+1,30,min(y+16,im.height-1)),fill='black');draw.text((3,y+2),str(y),fill='yellow')
    path=out/f['file'];im.save(path)
    rows.append(dict(sample_index=f['sample_index'],frame_index=f['frame_index'],original_file=str(src),original_png_sha256=sha(src),grid_file=str(path),grid_png_sha256=sha(path),width=im.width,height=im.height))
save(out/'manifest.json',dict(source_id=sid,coordinate_system='Original 640x360 pixels, x right and y down. Thin green grid every40 px; numbered x every80, y every40.',grid_images_are_annotation_aids_not_training_images=True,frames=rows))
print(str(out/'manifest.json'))
