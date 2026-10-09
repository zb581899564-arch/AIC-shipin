"""All original assets and fixed domains before any new answer is generated."""
import copy
from fractions import Fraction as F
import bw_common as c
from bw_native import convert_job

def add_exact_domain(job,points):
    from bisect import bisect_left
    for part in job['windows']:
        if not c.is_changed(part):continue
        w=part['window'];first=bisect_left(points,F(w['exact_raw_start']));stop=bisect_left(points,F(w['exact_raw_end']))
        w['eligible_exact_pts']=[str(x) for x in points[first:stop]]
    return job

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    rt,ex,cc,student,old,frames,production=c.helpers();authority=[];model=None;counts={}
    for scope in ('nontest','developer'):
        plan=c.read(c.CAD/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        sources=ex.source_tables(plan)
        for job in jobs:
            points=[F(p) for p in sources[job['source_key']]['pts_rational']]
            origin=F(0) if scope=='developer' else F(sources[job['source_key']]['pts_rational'][0])
            convert_job(job,points,origin);add_exact_domain(job,points)
            for ix,part in enumerate(job['windows']):
                v=c.checked_base(scope,job,ix)
                if model is None:model=v['model_identity']
                c.require(v['model_identity']==model,'baseline model identity differs')
                p=c.base_path(scope,job,ix,cc);authority.append(dict(path=str(p),sha256=c.sha(p),bound_files=v['bound_files']))
        counts[scope]=dict(records=len(jobs),windows=sum(len(j['windows']) for j in jobs),
            changed=sum(c.is_changed(p) for j in jobs for p in j['windows']))
        c.save(c.HERE/'input_01'/(scope+'_plan.json'),plan)
    c.require(counts['nontest']==dict(records=8,windows=8,changed=0) and counts['developer']==dict(records=104,windows=112,changed=16),'fixed non-test inventory differs')
    c.save(c.HERE/'input_01/resume_manifest.json',dict(rows=authority,model_identity=model,counts=counts,
        new_optimizer_updates=0,user_accepted_risk=True,weak_reference_not_admission_gate=True))
    source,stage,oldrows=c.v14_authority(student,model)
    ref,manifest,clocks=old.inputs('rematch');jobs=[]
    for item in manifest['records']:
        clock=clocks[item['video_id']];a=clock['arrays'];tick=F(a['raw_time_base']);points=[x*tick for x in a['native_pts_ticks']]
        origin=a['raw_first_pts_ticks']*tick;parts=[]
        for ix,(start,end) in enumerate(frames.window_schedule(item,manifest['kind'],clock)):
            raw_start,raw_end=production.raw_window_bounds(a,start,end)
            w=student.window_from_pts(item['source_path'],item['source_sha256'],[float(p) for p in points],raw_start,raw_end,item['video_id']+':T:'+str(ix))
            w['window_duration_sec']=end-start
            original=oldrows[item['video_id']]['windows'][ix]
            c.require(w['planned_source_frame_ordinals']==original['video_identity']['source_frame_ids'] and
                w['planned_actual_pts_sec']==original['video_identity']['actual_pts_sec'],'V14 source ordinal/PTS authority differs')
            parts.append(dict(start_sec=start,end_sec=end,window=w,clock_record_sha256=clock['clock_record_sha256'],
                clock_branch=clock['branch'],raw_source_pts_origin_sec=float(origin)))
        job=dict(video_id=item['video_id'],source_key=item['source_sha256'],source_group=item['source_sha256'],metadata=item,windows=parts)
        convert_job(job,points,origin);add_exact_domain(job,points);jobs.append(job)
    c.require(len(jobs)==426 and sum(len(j['windows']) for j in jobs)==521,'426/521 complete plan')
    counts['rematch']=dict(records=426,windows=521,changed=sum(c.is_changed(p) for j in jobs for p in j['windows']))
    c.save(c.HERE/'input_01/rematch_plan.json',dict(scope='rematch',jobs=jobs,input_ref=ref,records=426,windows=521))
    c.proof_aliases(jobs,ex,student)
    c.save(c.HERE/'prepared.json',dict(status='PASS_EXACT_USER_AUTHORIZED_BALANCED_WINDOW_PLAN',utc=c.utc(),counts=counts,
        old_V14_temporal_sha256=c.sha(source),old_V14_time_calls_preserved=521,new_model_calls=0,new_optimizer_updates=0))
    print(c.read(c.HERE/'prepared.json'),flush=True)

if __name__=='__main__':main()
