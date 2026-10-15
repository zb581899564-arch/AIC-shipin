"""One new CPU-only thumbnail observation per selected external source."""
import hashlib
import json
import os
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
import av
from PIL import Image, ImageDraw

ROOT = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
OUT = ROOT / 'reliable_reference_20261012_v1/catalog_01'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2,allow_nan=False)

def main(selection):
    os.environ['CUDA_VISIBLE_DEVICES']=''
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json',dict(pid=os.getpid(),task='NEW_EXTERNAL_THUMBNAIL_OBSERVATION_ONLY'))
    plan=json.loads((ROOT/'balanced_two_window_risk_v3/input_01/developer_plan.json').read_text())
    jobs={r['video_id']:r for r in plan['developer_jobs']}
    records=[]
    for row in selection['rows']:
        case=row['case_id'];job=jobs[row['video_id']]
        assert job['source_key']==row['source_key'] and job['source_group']==row['source_group']
        cp=ROOT/'context_advisory_v1/input_01'/(row['source_key']+'.clock.json')
        assert sha(cp)==row['clock_sha256']
        c=json.loads(cp.read_text());path=Path(c['source_path'])
        assert sha(path)==row['source_key']
        points=[F(str(x)) for x in c['exact_pts']] if 'exact_pts' in c else [F(str(x)) for x in c['pts_rational']]
        lo,hi=F(row['clip_start']),F(row['clip_end'])
        desired=[];t=lo
        while t<hi:
            ordinal=bisect_left(points,t)
            if ordinal<len(points) and points[ordinal]<hi and ordinal not in desired:desired.append(ordinal)
            t+=F(1)
        assert desired and len(desired)<=40
        wanted={points[n]:n for n in desired};images={}
        with av.open(str(path)) as container:
            st=container.streams.video[0]
            container.seek(max(0,int((lo-F(2))/F(st.time_base))),stream=st,backward=True,any_frame=False)
            for frame in container.decode(st):
                if frame.pts is None:raise ValueError('Missing native timestamp')
                p=F(frame.pts)*F(frame.time_base)
                if p>=hi:break
                if p in wanted:
                    rgb=frame.reformat(format='rgb24')
                    im=Image.frombytes('RGB',(rgb.width,rgb.height),bytes(rgb.planes[0]),'raw','RGB',rgb.planes[0].line_size,1)
                    im.thumbnail((318,180),Image.Resampling.LANCZOS)
                    images[wanted[p]]=im
        assert set(images)==set(desired),(case,len(images),len(desired))
        folder=OUT/case;folder.mkdir();sheets=[]
        for page in range((len(desired)+23)//24):
            sheet=Image.new('RGB',(320*6,212*4),'#101010');draw=ImageDraw.Draw(sheet)
            for j,n in enumerate(desired[page*24:(page+1)*24]):
                x,y=(j%6)*320,(j//6)*212;im=images[n]
                sheet.paste(im,(x+(320-im.width)//2,y+28+(180-im.height)//2))
                draw.text((x+4,y+3),f'{case} ID {page*24+j:03d} PTS {float(points[n]):.3f}',fill='white')
            p=folder/f'page_{page+1:02d}.jpg';sheet.save(p,quality=85);sheets.append(dict(path=str(p.relative_to(OUT)),bytes=p.stat().st_size,sha256=sha(p)))
        meta=dict(case_id=case,source_sha256=row['source_key'],source_group=row['source_group'],
                  window_start=str(lo),window_end=str(hi),width=c['width'],height=c['height'],
                  observation_kind='NATIVE_FULL_FRAME_1HZ_CATALOG_NOT_REFERENCE_LABELS',
                  observations=[dict(id=i,ordinal=n,exact_pts=str(points[n])) for i,n in enumerate(desired)],sheets=sheets)
        save(folder/'observations.json',meta);records.append(meta)
        print(json.dumps(dict(case=case,frames=len(desired),pages=len(sheets))),flush=True)
    result=dict(status='PASS_45_SOURCE_CATALOG_NOT_REFERENCE_QUALITY',sources=45,records=records,
                new_model_calls=0,optimizer_updates=0,CUDA_initialized=False,
                historical_quality_failed_preserved=True)
    save(OUT/'preparation_receipt.json',result)
    import zipfile
    zp=OUT/'catalog_material.zip'
    with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.glob('S*/*')):z.write(p,p.relative_to(OUT))
        z.write(OUT/'preparation_receipt.json','preparation_receipt.json')
    save(OUT/'transfer_receipt.json',dict(bytes=zp.stat().st_size,sha256=sha(zp),members=len(zipfile.ZipFile(zp).namelist())))
    print('COMPLETE',zp.stat().st_size,sha(zp),flush=True)
