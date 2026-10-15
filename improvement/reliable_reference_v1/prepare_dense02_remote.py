"""New native-frame evidence around prediction-blind review anchors only."""
import hashlib
import json
import os
from bisect import bisect_left, bisect_right
from fractions import Fraction as F
from pathlib import Path
import av
from PIL import Image, ImageDraw

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
OUT=ROOT/'reliable_reference_20261012_v1/dense_02'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(8<<20),b''):h.update(x)
    return h.hexdigest()

def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2,allow_nan=False)

def main(anchors):
    os.environ['CUDA_VISIBLE_DEVICES']=''
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json',dict(pid=os.getpid(),purpose='NEW_DENSE_EXTERNAL_REFERENCE_EVIDENCE',model_calls=0))
    save(OUT/'anchor_registration.json',anchors)
    records=[]
    for row in anchors['rows']:
        case=row['case_id'];key=row['source_key']
        cp=ROOT/'context_advisory_v1/input_01'/(key+'.clock.json')
        assert sha(cp)==row['clock_sha256']
        clock=json.loads(cp.read_text());path=Path(clock['source_path']);assert sha(path)==key
        points=[F(str(x)) for x in (clock['exact_pts'] if 'exact_pts' in clock else clock['pts_rational'])]
        ranges=[]
        for lo,hi in sorted((F(a),F(b)) for a,b in row['ranges_exact']):
            lo=max(points[0],lo);hi=min(F(str(clock['physical_endpoint_rational'])),hi)
            if lo>=hi:continue
            if ranges and lo<=ranges[-1][1]:ranges[-1]=(ranges[-1][0],max(hi,ranges[-1][1]))
            else:ranges.append((lo,hi))
        assert ranges
        desired=sorted({i for lo,hi in ranges for i in range(bisect_left(points,lo),bisect_left(points,hi))})
        wanted={points[i]:i for i in desired};images={}
        with av.open(str(path)) as c:
            st=c.streams.video[0]
            for lo,hi in ranges:
                c.seek(max(0,int((lo-F(2))/F(st.time_base))),stream=st,backward=True,any_frame=False)
                for frame in c.decode(st):
                    if frame.pts is None:raise ValueError('Missing source PTS')
                    p=F(frame.pts)*F(frame.time_base)
                    if p>=hi:break
                    if p in wanted and wanted[p] not in images:
                        rgb=frame.reformat(format='rgb24')
                        im=Image.frombytes('RGB',(rgb.width,rgb.height),bytes(rgb.planes[0]),'raw','RGB',rgb.planes[0].line_size,1)
                        im.thumbnail((238,134),Image.Resampling.LANCZOS);images[wanted[p]]=im
        assert set(images)==set(desired),(case,len(images),len(desired))
        folder=OUT/case;folder.mkdir();sheets=[]
        for page in range((len(desired)+47)//48):
            sheet=Image.new('RGB',(240*8,160*6),'#101010');draw=ImageDraw.Draw(sheet)
            for j,n in enumerate(desired[page*48:(page+1)*48]):
                x,y=(j%8)*240,(j//8)*160;im=images[n]
                sheet.paste(im,(x+(240-im.width)//2,y+23+(134-im.height)//2))
                draw.text((x+3,y+3),f'{case} D{page*48+j:04d} {float(points[n]):.3f}',fill='white')
            p=folder/f'page_{page+1:03d}.jpg';sheet.save(p,quality=80)
            sheets.append(dict(path=str(p.relative_to(OUT)),bytes=p.stat().st_size,sha256=sha(p)))
        meta=dict(case_id=case,source_group=row['source_group'],source_sha256=key,
                  original_window=[row['clip_start'],row['clip_end']],ranges_exact=[[str(a),str(b)] for a,b in ranges],
                  observation_kind='EVERY_NATIVE_FRAME_IN_REGISTERED_RANGES_NO_AUDIO',
                  observations=[dict(id=i,ordinal=n,exact_pts=str(points[n])) for i,n in enumerate(desired)],sheets=sheets)
        save(folder/'observations.json',meta);records.append(meta)
        print(json.dumps(dict(case=case,frames=len(desired),pages=len(sheets))),flush=True)
    result=dict(status='PASS_DENSE_NATIVE_PREPARATION_NOT_REFERENCE_QUALITY',records=records,new_model_calls=0,optimizer_updates=0,CUDA_initialized=False)
    save(OUT/'preparation_receipt.json',result)
    import zipfile
    p=OUT/'dense_review_material.zip'
    with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.glob('R*/*')):z.write(f,f.relative_to(OUT))
        z.write(OUT/'preparation_receipt.json','preparation_receipt.json')
    save(OUT/'transfer_receipt.json',dict(bytes=p.stat().st_size,sha256=sha(p)))
    print('COMPLETE',p.stat().st_size,sha(p),flush=True)
