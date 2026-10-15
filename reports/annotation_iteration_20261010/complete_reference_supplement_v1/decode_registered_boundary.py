"""One preregistered native interior image for one consequential observed gap."""
import argparse,hashlib,json,sys,time
from datetime import datetime,timezone
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--job',required=True);ap.add_argument('--left',type=int,required=True);ap.add_argument('--right',type=int,required=True)
    ap.add_argument('--main-review',required=True);ap.add_argument('--task-number',type=int,required=True)
    args=ap.parse_args();capacity=ROOT/'boundary_observation_capacity_v2.json';cap=read(capacity)
    assert 1<=args.task_number<=cap['additional_window_tasks_max']
    prior=[p for p in ROOT.glob('boundary_phase_v2_task*/registration.json')]
    assert len(prior)==args.task_number-1, 'Sequential fresh task registration required'
    obs=ROOT.parent/'slot6_silver24_v1/observations'/args.job
    m=read(obs/'manifest.json');clock=read(obs/'native_clock.json')
    job_index=int(args.job.split('_')[0]);assert job_index in cap['allowed_pending_job_indices']
    left,right=m['frames'][args.left],m['frames'][args.right]
    width=F(right['global_seconds_exact'])-F(left['global_seconds_exact'])
    assert args.right==args.left+1 and F('0.5')<width<=F(cap['per_task_source_time_span_max_seconds'])
    ordinal=(left['source_ordinal']+right['source_ordinal'])//2
    assert left['source_ordinal']<ordinal<right['source_ordinal']
    assert right['source_ordinal']-left['source_ordinal']<=cap['per_task_contiguous_source_frames_max']
    point=next(x for x in clock if x['source_ordinal']==ordinal)
    source=Path(m['source_path']);assert sha(source)==m['source_sha256']
    review=Path(args.main_review).resolve(strict=True);assert review.parent==ROOT
    out=ROOT/('boundary_phase_v2_task%02d'%args.task_number);out.mkdir(exist_ok=False)
    save(out/'registration.json',dict(utc=datetime.now(timezone.utc).isoformat(),task_number=args.task_number,
        job_index=job_index,window_id=m.get('window_id'),capacity=dict(path=str(capacity),sha256=sha(capacity)),
        source_sha256=m['source_sha256'],manifest_sha256=sha(obs/'manifest.json'),native_clock_sha256=sha(obs/'native_clock.json'),
        main_review=dict(path=str(review),sha256=sha(review)),endpoints=[left,right],interior_registered=point,
        actual_gap_width_exact=str(width),max_new_images=1,not_automatic_boundary_acceptance=True,new_model_calls=0,new_optimizer_updates=0))
    import av
    from PIL import Image
    run=ROOT.parents[1]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    sys.path.insert(0,str(run/'teacher_student_autopilot_v14'))
    from source_color import convert_frame
    start=time.monotonic();found=False
    with av.open(str(source)) as c:
        assert len(c.streams.video)==1
        for i,frame in enumerate(c.decode(c.streams.video[0])):
            if i!=ordinal:continue
            pts=F(frame.pts)*frame.time_base;assert pts==F(point['global_seconds_exact'])
            rgb=convert_frame(frame,m['source_sha256'],'rgb24');p=out/f'O{i:06d}.png';Image.fromarray(rgb).save(p)
            save(out/'receipt.json',dict(status='PASS_ONE_ACTUAL_REGISTERED_NATIVE_IMAGE_SEMANTIC_REVIEW_PENDING',
                source_ordinal=i,global_seconds_exact=str(pts),local_seconds_exact=point['local_seconds_exact'],path=str(p),
                png_sha256=sha(p),rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),width=rgb.shape[1],height=rgb.shape[0],
                wall_seconds=time.monotonic()-start,actual_new_images=1,new_model_calls=0,new_optimizer_updates=0))
            found=True;break
    assert found
    print(json.dumps(read(out/'receipt.json'),ensure_ascii=False))
if __name__=='__main__':main()
