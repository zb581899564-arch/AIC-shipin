"""Prepare new four-window observation pilot, without scores or model calls."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
import json,hashlib,av
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'reports/qwen8b_annotation_20261009_v1'
HERE=Path(__file__).resolve().parent/'native_event_pilot_v1'
RUN=ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
rows=[json.loads(p.read_text()) for p in (OLD/'input').glob('*/manifest.json')]
excluded={'Se3oxnaPsz0','WG0MBPpPC6I','37rzWOQsNIw','0tmA_C6XwfM','91IHQYk1IQM'}
eligible=sorted([r for r in rows if r['split']=='train' and r['source_id'] not in excluded and r['source_duration_seconds']>=90],
    key=lambda r:hashlib.sha256(('EMPTY407-PILOT-20261010|'+r['source_group']).encode()).hexdigest())
special=json.loads((RUN/'teacher_student_autopilot_v14/config.json').read_text())['source_color_repair']['sources']
HERE.mkdir(exist_ok=False)
save(HERE/'preparation_contract.json',dict(status='OBSERVATION_PREPARATION_ONLY_NOT_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
    source_rule='train-only eligible, exclude two human-count issues and three old native pilot sources; hash EMPTY407-PILOT-20261010|source_group ascending; first two',
    windows=[[0,30],[60,90]],sampling='first+(N-1)*i//63 for i=0..63',
    closed_model_calls=0,new_optimizer_updates=0,pro_decision_pending=True,
    no_human_scores_no_teacher_labels_no_predictions=True))
jobs=[]
for m in eligible[:2]:
    sid=m['source_id'];src=OLD/'input'/sid/m['media_file'];assert sha(src)==m['media_sha256']
    assert m['media_sha256'] not in special,'special color requires bound production decoder'
    for ix,(start,end) in enumerate(((0,30),(60,90))):
        folder=HERE/f'{sid}_{ix:02d}';folder.mkdir();(folder/'frames').mkdir()
        allframes=[];points=[]
        with av.open(str(src)) as inp:
            stream=inp.streams.video[0];rate=stream.average_rate
            for ordinal,frame in enumerate(inp.decode(stream)):
                assert frame.pts is not None and frame.time_base is not None
                point=Fraction(frame.pts)*frame.time_base
                if point<start:continue
                if point>=end:break
                rgb=frame.to_ndarray(format='rgb24')
                allframes.append((ordinal,frame.pts,frame.time_base,point,Image.fromarray(rgb),hashlib.sha256(rgb.tobytes()).hexdigest()))
                points.append(point)
        assert len(allframes)>=64
        selected=[(len(allframes)-1)*i//63 for i in range(64)]
        assert len(set(selected))==64
        frames=[]
        for i,j in enumerate(selected):
            ordinal,pts,tb,point,im,pixsha=allframes[j];p=folder/'frames'/f'F{i:02d}_O{ordinal:06d}.png';im.save(p)
            frames.append(dict(frame_id=f'F{i:02d}',source_ordinal=ordinal,source_pts=pts,time_base=str(tb),
                global_seconds_exact=str(point),local_seconds_exact=str(point-start),path=str(p),png_sha256=sha(p),rgb_pixel_sha256=pixsha))
        sheets=[]
        for batch in range(8):
            canvas=Image.new('RGB',(1280,800),'white');draw=ImageDraw.Draw(canvas)
            for k,r in enumerate(frames[batch*8:batch*8+8]):
                x=(k%4)*320;y=(k//4)*400
                im=Image.open(r['path']).convert('RGB');im.thumbnail((320,360));canvas.paste(im,(x,y+32))
                draw.text((x+3,y+3),f"{r['frame_id']} O{r['source_ordinal']} t={float(Fraction(r['local_seconds_exact'])):.3f}s",fill='black')
            p=folder/f'overview_{batch:02d}.png';canvas.save(p)
            sheets.append(dict(path=str(p),sha256=sha(p),frame_ids=[r['frame_id'] for r in frames[batch*8:batch*8+8]],
                use='navigation and blind review only; scaled, not student tensor'))
        dest=folder/'clip.mp4';offset=allframes[0][1]
        with av.open(str(dest),'w') as out:
            s=out.add_stream('libx264',rate=rate);s.width=allframes[0][4].width;s.height=allframes[0][4].height
            s.pix_fmt='yuv420p';s.options={'crf':'18','preset':'fast'};s.time_base=allframes[0][2];s.codec_context.time_base=s.time_base
            for ordinal,pts,tb,point,im,pixsha in allframes:
                f=av.VideoFrame.from_image(im);f.pts=pts-offset;f.time_base=tb
                for pkt in s.encode(f):out.mux(pkt)
            for pkt in s.encode():out.mux(pkt)
        with av.open(str(dest)) as check:
            clippts=[Fraction(f.pts)*f.time_base for f in check.decode(video=0)]
        assert clippts==[r[3]-allframes[0][3] for r in allframes]
        manifest=dict(window_id=f'{sid}:{start}:{end}',source_id=sid,source_group=m['source_group'],prior_split='train',
            prior_exposure='IMAGE_LABELS_AND_MODEL_DEVELOPMENT; NOT_BLIND',source_path=str(src),source_sha256=m['media_sha256'],
            source_total_frames=m['native_frames'],width=allframes[0][4].width,height=allframes[0][4].height,
            domain_global_seconds_exact=[str(Fraction(start)),str(Fraction(end))],
            sampling='INTEGER_FLOOR_ENDPOINTS_64',eligible_source_frames=len(allframes),
            frames=frames,overviews=sheets,clip_path=str(dest),clip_sha256=sha(dest),clip_pts_offset_exact=str(allframes[0][3]-start),
            clip_encoding='all native frames; unchanged geometry; exact native PTS deltas; libx264 crf18 yuv420p lossy pixels; no audio',
            full_native_frames_observed=False,student_processor_visibility_verified=False,training_admitted=False,
            source_clock=[dict(source_ordinal=r[0],global_seconds_exact=str(r[3]),local_seconds_exact=str(r[3]-start)) for r in allframes])
        save(folder/'manifest.json',manifest);jobs.append(str(folder))
save(HERE/'jobs.json',dict(jobs=jobs,expected=4,closed_model_calls=0,new_optimizer_updates=0))
print(json.dumps(dict(status='FOUR_NEW_NATIVE_OBSERVATION_WINDOWS_PREPARED',jobs=jobs,student_frame_pngs=256,closed_model_calls=0,training_admitted=False),ensure_ascii=False))
