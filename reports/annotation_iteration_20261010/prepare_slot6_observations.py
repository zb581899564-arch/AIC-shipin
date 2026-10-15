"""Native observation evidence for the fixed public-rule plan; no label/model calls."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,shutil,av
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent/'slot6_silver24_v1'
PLAN=json.loads((HERE/'source_window_plan.json').read_text())
RUN=HERE.parents[1]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
OUT=HERE/'observations';OUT.mkdir(exist_ok=False)
special=json.loads((RUN/'teacher_student_autopilot_v14/config.json').read_text())['source_color_repair']['sources']
jobs=[]
for index,job in enumerate(PLAN['jobs']):
    w=job['window'];assert w['source_sha256'] not in special
    folder=OUT/f"{index:02d}_{job['source_id']}_W{w['original_window_index']:02d}";folder.mkdir();(folder/'frames').mkdir()
    src=Path(w['source_path']);ids=w['planned_source_frame_ordinals'];wanted=set(ids)
    a,b=F(w['domain_start_exact']),F(w['domain_end_exact']);selected={};native=[]
    with av.open(str(src)) as inp:
        stream=inp.streams.video[0];rate=stream.average_rate
        for ordinal,frame in enumerate(inp.decode(stream)):
            p=F(frame.pts)*frame.time_base
            if p<a:continue
            if p>=b:break
            rgb=frame.to_ndarray(format='rgb24');im=Image.fromarray(rgb)
            native.append((ordinal,frame.pts,frame.time_base,p,im))
            if ordinal in wanted:selected[ordinal]=(im,hashlib.sha256(rgb.tobytes()).hexdigest(),p)
    assert sorted(selected)==ids
    frames=[]
    for i,ordinal in enumerate(ids):
        im,pixsha,p=selected[ordinal];file=folder/'frames'/f'F{i:02d}_O{ordinal:06d}.png';im.save(file)
        frames.append(dict(frame_id=f'F{i:02d}',source_ordinal=ordinal,path=str(file),global_seconds_exact=str(p),
            local_seconds_exact=str(p-a),png_sha256=sha(file),rgb_pixel_sha256=pixsha))
    dest=folder/'clip.mp4';origin=native[0][3];offset=native[0][1]
    with av.open(str(dest),'w') as out:
        s=out.add_stream('libx264',rate=rate);s.width=w['width'];s.height=w['height'];s.pix_fmt='yuv420p'
        s.options={'crf':'18','preset':'fast'};s.time_base=native[0][2];s.codec_context.time_base=s.time_base
        for ordinal,pts,tb,p,im in native:
            frame=av.VideoFrame.from_image(im);frame.pts=pts-offset;frame.time_base=tb
            for packet in s.encode(frame):out.mux(packet)
        for packet in s.encode():out.mux(packet)
    with av.open(str(dest)) as check:actual=[F(f.pts)*f.time_base for f in check.decode(video=0)]
    assert actual==[x[3]-origin for x in native]
    sheets=[]
    for batch in range((len(frames)+7)//8):
        canvas=Image.new('RGB',(1280,800),'white');draw=ImageDraw.Draw(canvas)
        for k,r in enumerate(frames[batch*8:batch*8+8]):
            x=k%4*320;y=k//4*400;im=Image.open(r['path']);im.thumbnail((320,360));canvas.paste(im,(x,y+32))
            draw.text((x+3,y+3),f"{r['frame_id']} O{r['source_ordinal']} t={float(F(r['local_seconds_exact'])):.3f}",fill='black')
        p=folder/f'overview_{batch:02d}.png';canvas.save(p);sheets.append(dict(path=str(p),sha256=sha(p),frame_ids=[r['frame_id'] for r in frames[batch*8:batch*8+8]]))
    clock=folder/'native_clock.json';save(clock,[dict(source_ordinal=x[0],global_seconds_exact=str(x[3]),local_seconds_exact=str(x[3]-a)) for x in native])
    manifest=dict(window_id=w['window_id'],role=job['role'],source_id=job['source_id'],source_group=job['source_group'],
        source_sha256=w['source_sha256'],source_path=str(src),source_total_frames=w['source_total_frames'],
        domain_global_seconds_exact=[str(a),str(b)],domain_is_registered_B_nominal_plan=True,
        clip_path=str(dest),clip_sha256=sha(dest),clip_pts_offset_exact=str(origin-a),
        clip_encoding='all native frames; exact PTS deltas; unchanged geometry; libx264 crf18 yuv420p lossy pixels; no audio',
        frames=frames,overviews=sheets,native_clock_path=str(clock),native_clock_sha256=sha(clock),
        original_window=w,plan_sha256=sha(HERE/'source_window_plan.json'),
        student_effective_views='PENDING_ACTUAL_PROCESSOR_CPU',student_processor_visibility_verified=False,
        teacher_proposal=None,blind_review=None,training_admitted=False,full_native_frames_observed=False)
    save(folder/'manifest.json',manifest);jobs.append(str(folder))
    print(json.dumps(dict(prepared=index+1,expected=24,window=w['window_id']),ensure_ascii=False),flush=True)
save(OUT/'jobs.json',dict(jobs=jobs,expected=24,first_four=jobs[:4],training_admitted=False,new_optimizer_updates=0))
