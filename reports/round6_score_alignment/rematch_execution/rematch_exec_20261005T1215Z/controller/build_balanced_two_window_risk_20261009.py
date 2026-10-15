"""Create an independent user-authorized risk experiment; never edit old routes."""
from pathlib import Path
import ast

RUN=Path(__file__).resolve().parent.parent
OLD=RUN/'native_round_alignment_v1'
NEW=RUN/'balanced_two_window_risk_v1'
NEW.mkdir(exist_ok=False)

def put(name,text):
    ast.parse(text,filename=name) if name.endswith('.py') else None
    (NEW/name).write_text(text,encoding='utf-8',newline='\n')

common=(OLD/'nr_common.py').read_text()
common=common.replace('nr_common','bw_common').replace('nr_','bw_').replace('native-nearest','balanced-two-window')
common=common.replace("arm=='Q'","arm=='BW'").replace("arm='Q'","arm='BW'").replace("'Q/done.json'","'BW/done.json'").replace("/'Q/done.json'","/'BW/done.json'")
common=common.replace("value['arm']=='Q'","value['arm']=='BW'")
common=common.replace("sampling_recipe='NATIVE_NEAREST64_SAME_COUNT_ENDPOINTS'","sampling_recipe='EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64'")
common=common.replace("spatial_resolution_tradeoff='SAME_FRAME_COUNT_PIXEL_GRID_AND_B0_PROMPT'","spatial_resolution_tradeoff='ORIGINAL_TOTAL_PIXEL_BUDGET_ACTUAL_GRID_RECORDED'")
# The exact unchanged V14 projection remains the original, already admitted
# consumer. CPU admission below adds an explicit plan/old-window identity check.
common += '''
def is_changed(part):return part['window']!=part['base_window']

def jobs_for(scope):
    plan=read(HERE/'input_01'/(scope+'_plan.json'))
    return plan,plan['developer_jobs'] if scope=='developer' else plan['jobs']

def proof_aliases(jobs,ex,student):
    source,stage,oldrows=v14_authority(student,read(HERE/'input_01/resume_manifest.json')['model_identity'])
    aliases=[]
    for job in jobs:
        require(len(oldrows[job['video_id']]['windows'])==len(job['windows']),'old V14 window denominator')
        for ix,part in enumerate(job['windows']):
            if is_changed(part):continue
            original=oldrows[job['video_id']]['windows'][ix];w=part['window']
            require(original['start_sec']==part['start_sec'] and original['end_sec']==part['end_sec'] and
                original['video_identity']['source_frame_ids']==w['planned_source_frame_ordinals'] and
                original['video_identity']['actual_pts_sec']==w['planned_actual_pts_sec'] and
                original['video_identity']['native_processor_identity']['window_start']==w['window_pts_start_sec'] and
                original['video_identity']['registered_prompt_sha256']==ex.cc.digest(ex.base_texts(None)['B0']),
                'unchanged exact V14 request/source/PTS/prompt differs')
            path=done_path('rematch',job,ix,'BW',ex.cc)
            save(path,dict(status='PASS_EXACT_V14_UNCHANGED_REQUEST_AUTHORITY_HANDOFF',source=str(source),source_sha256=sha(source),
                video_id=job['video_id'],index=ix,window=w,original_window_digest=ex.cc.digest(original),
                actual_processor_identity=original['video_identity'],new_model_calls=0,new_optimizer_updates=0,
                original_cost_preserved=True,not_new_raw_or_generation=True))
            checked_v14_alias(path,job,ix,ex);aliases.append(dict(path=str(path),sha256=sha(path)))
    save(HERE/'rematch_01/alias_handoff.json',dict(status='PASS_EXACT_UNCHANGED_V14_REQUESTS',aliases=aliases,
        old_validator_and_processor_receipts_referenced=True,new_decoder_calls=0,new_model_calls=0,
        original_temporal_sha256=sha(source),original_costs_preserved=True))
'''
put('bw_common.py',common)
put('bw_video.py',(OLD/'nr_video.py').read_text())

native=(OLD/'nr_native.py').read_text()
native=native[native.index('def decode_round_window'):]
native=native.replace('decode_round_window','decode_balanced_window')
native=native.replace('round_indices(floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]))','floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"])')
native=native.replace('NATIVE_NEAREST64_SAME_COUNT_ENDPOINTS','EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64')
native=native.replace('len(w["baseline_floor64_ordinals"])==len(ids)','len(w["planned_exact_pts"])==len(ids)')
native=native.replace('require(abs(point - pts[len(frames)]) <= 1e-6, "actual decoded ordinal PTS differs from teacher observation")',
'''require(Fraction(frame.pts)*frame.time_base == Fraction(w['planned_exact_pts'][len(frames)]) and
                    point == pts[len(frames)], "actual decoded ordinal exact PTS differs")''')
put('bw_native.py','''"""Exact midpoint domains and original integer-floor64 physical sampling."""
import copy,hashlib,math,sys
from pathlib import Path
from fractions import Fraction
from bisect import bisect_left
import bw_common as c
require,sha,load=c.require,c.sha,c.load
HERE=c.RUN/'teacher_student_autopilot_v14'
_VERIFIED_SOURCE_STATS={}

def floor_indices(first,stop):
    require(type(first) is int and type(stop) is int and 0<=first<stop,'empty/invalid native domain')
    n=stop-first
    return list(range(first,stop)) if n<=64 else [first+i*(n-1)//63 for i in range(64)]

def balanced_schedule(original):
    pairs=[(Fraction(str(a)),Fraction(str(b))) for a,b in original]
    require(pairs and all(a<b and b-a<=30 for a,b in pairs),'original domains')
    if len(pairs)==2 and 30<pairs[-1][1]-pairs[0][0]<60:
        a,b=pairs[0][0],pairs[-1][1];m=(a+b)/2
        require(pairs[0][1]==pairs[1][0],'old two windows not contiguous')
        return [(a,m),(m,b)]
    return pairs

def convert_job(job,points,origin=Fraction(0)):
    original=[(p['start_sec'],p['end_sec']) for p in job['windows']]
    schedule=balanced_schedule(original)
    for ix,(part,(a,b)) in enumerate(zip(job['windows'],schedule)):
        part['base_window']=copy.deepcopy(part['window'])
        part['base_start_sec'],part['base_end_sec']=part['start_sec'],part['end_sec']
        if (a,b)==tuple(map(lambda x:Fraction(str(x)),original[ix])):continue
        raw_a,raw_b=origin+a,origin+b
        first,stop=bisect_left(points,raw_a),bisect_left(points,raw_b)
        ids=floor_indices(first,stop);w=copy.deepcopy(part['window'])
        require([i for i,t in enumerate(points) if float(raw_a)<=float(t)<float(raw_b)]==list(range(first,stop)),
            'float processor boundary membership differs from exact rational domain')
        require(Fraction(str(float(a)))==a and Fraction(str(float(b)))==b and
            Fraction(str(float(b-a)))==b-a,'normalized boundary not exact in decimal consumer')
        w.update(window_id=w['window_id']+':BW',window_pts_start_sec=float(raw_a),window_pts_end_exclusive_sec=float(raw_b),
            window_duration_sec=float(b-a),planned_source_frame_ordinals=ids,planned_actual_pts_sec=[float(points[i]) for i in ids],
            planned_exact_pts=[str(points[i]) for i in ids],eligible_source_frame_count=stop-first,
            exact_raw_start=str(raw_a),exact_raw_end=str(raw_b),exact_normalized_start=str(a),exact_normalized_end=str(b),
            sampling_recipe='EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64')
        part.update(start_sec=float(a),end_sec=float(b),window=w)
    return job

def exact_ranges(segments,window):
    # Exact source clock independently checks the original parser's result.
    from contracts import validate_segments
    validate_segments(segments,window['window_duration_sec'])
    pts=[Fraction(x) for x in window['eligible_exact_pts']]
    start=Fraction(window['exact_raw_start']);result=[]
    for a,b in segments:
        first,stop=bisect_left(pts,start+Fraction(str(a))),bisect_left(pts,start+Fraction(str(b)))
        require(0<=first<stop<=len(pts),'segment has no exact native source frame')
        result.append([first,stop])
    return result

'''+native)

engine=(OLD/'nr_engine.py').read_text()
engine=engine[:engine.index('def plan_rematch():')]
engine=engine.replace('nr_common','bw_common').replace('from nr_native import decode_round_window,round_window','from bw_native import decode_balanced_window,exact_ranges')
engine=engine.replace('encode_round','encode_balanced').replace('decode_round_window','decode_balanced_window').replace('from nr_video','from bw_video')
engine=engine.replace("'Q'","'BW'").replace("arm='BW'","arm='BW'").replace('ROUND_ALIGNMENT','BALANCED_TWO_WINDOW')
start=engine.index("            if scope!='rematch':")
end=engine.index('            value=rt.attempt',start)
engine=engine[:start]+engine[end:]
engine=engine.replace("            value.update(request_sha256", "            c.require(exact_ranges(value['parsed_segments'],w)==value['native_frame_realizability']['ranges'],'exact vs pinned float realizability differs')\n            value.update(request_sha256")
engine=engine.replace("    c.require(ex.video_signature(encoded)","    c.require(exact_ranges(v['parsed_segments'],w)==v['native_frame_realizability']['ranges'],'exact rational replay differs')\n    c.require(ex.video_signature(encoded)")
engine=engine.replace("if scope=='nontest' and fresh==1:","if not (c.HERE/'first_real_acceptance.json').exists():")
engine=engine.replace('PASS_REAL_FIRST_NATIVE_BALANCED_TWO_WINDOW_AND_INDEPENDENT_CPU_REPLAY','PASS_REAL_FIRST_BALANCED_WINDOW_AND_INDEPENDENT_CPU_REPLAY')
engine=engine.replace('PASS_ALL_NATIVE_BALANCED_TWO_WINDOW_ATTEMPTS','PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS')
engine+='''
if __name__=='__main__':
    import sys
    run(sys.argv[1])
'''
put('bw_engine.py',engine)

put('bw_prepare.py','''"""All original assets and fixed domains before any new answer is generated."""
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
''')

put('bw_cpu.py','''"""Actual pinned input consumer admission, no model or optimizer calls."""
from fractions import Fraction as F
from bisect import bisect_left
import bw_common as c
from bw_native import balanced_schedule,floor_indices,exact_ranges
from bw_engine import encode_balanced

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    for duration in [F('30.001'),F('30.3'),F('32.134'),F('59.999'),F(60)]:
        oldplan=[(0,30),(30,float(duration))];new=balanced_schedule(oldplan)
        c.require(new[0][0]==0 and new[-1][1]==duration and new[0][1]==new[1][0],'exact domain coverage')
        c.require(duration==60 or new[0][1]-new[0][0]==new[1][1]-new[1][0],'balanced equal lengths')
    for n in range(1,2001):
        ids=floor_indices(11,11+n);c.require(ids==([11+i for i in range(n)] if n<=64 else [11+(i*(n-1))//63 for i in range(64)]),'original floor64 differs')
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    from engine import prompt_for
    c.require(prompt_for(processor,True)==rt.prompt(processor,ex.base_texts(None)['B0']),'actual old/new full B0 processor prompt differs')
    proofs=[];counts={}
    for scope in ('nontest','developer','rematch'):
        plan,jobs=c.jobs_for(scope);fresh=0
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                if not c.is_changed(part):
                    c.checked(c.done_path(scope,job,ix,'BW',cc),job,ix,'BW',ex);continue
                w=part['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
                points=[F(x) for x in w['eligible_exact_pts']]
                c.require(len(points)==w['eligible_source_frame_count'] and evidence['window_source_pts_sec']==[float(x) for x in points],
                    'decoded full window source clock differs')
                from native_segment_contract import native_segment_ranges
                duration=w['window_duration_sec']
                for segments in ([[0,duration]],[[0,duration/2],[duration/2,duration]],[]):
                    c.require(exact_ranges(segments,w)==[list(x) for x in native_segment_ranges(segments,evidence['window_source_pts_sec'],w['window_pts_start_sec'],duration)],
                        'actual float parser/consumer differs from exact rational half-open interval')
                proofs.append(dict(scope=scope,video_id=job['video_id'],index=ix,window=w,
                    input_tokens=evidence['input_tokens'],video_identity=evidence,vision_signature=ex.video_signature(encoded)))
                fresh+=1;del encoded;c.state('CPU_BALANCED_ACTUAL_INPUTS',scope=scope,checked=fresh,new_model_calls=0)
        counts[scope]=fresh
    c.require(counts['nontest']==0 and counts['developer']==16 and counts['rematch']==c.read(c.HERE/'prepared.json')['counts']['rematch']['changed'],
        'full actual input denominator')
    c.save(c.HERE/'cpu_acceptance.json',dict(status='PASS_ALL_CHANGED_BALANCED_NATIVE_PROCESSOR_AND_EXACT_BOUNDARIES',utc=c.utc(),
        proofs=proofs,counts=counts,max_input_tokens=max(x['input_tokens'] for x in proofs),arithmetic_cases=2005,
        actual_B0_full_processor_prompt_equal=True,new_model_calls=0,new_optimizer_updates=0,new_32B_calls=0,
        quality='UNKNOWN_USER_ACCEPTED_RISK',weak_direction_not_gate=True))
    print('PASS_ALL_CHANGED_BALANCED_NATIVE_PROCESSOR_AND_EXACT_BOUNDARIES',flush=True)

if __name__=='__main__':main()
''')

put('bw_report.py','''"""Replay every new answer once; quality measurements are descriptive only."""
import bw_common as c
from bw_engine import replay

def main(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    plan,jobs=c.jobs_for(scope);proofs=[];rows=[]
    first=c.read(c.HERE/'first_real_acceptance.json') if (c.HERE/'first_real_acceptance.json').exists() else None
    for job in jobs:
        ids=set();baseline=set()
        for ix,part in enumerate(job['windows']):
            p=c.done_path(scope,job,ix,'BW',cc);v=c.checked(p,job,ix,'BW',ex)
            if c.is_changed(part):
                if first and str(p)==first['path']:
                    c.require(c.sha(p)==first['done_sha256'],'first accepted answer changed')
                    proofs.append(dict(first,first_proof_referenced=True))
                else:proofs.append(replay(p,job,ix,ex,rt,student,processor))
            for a,b in v['native_frame_realizability']['ranges']:ids.update(range(part['window']['planned_source_frame_ordinals'][0]+a,part['window']['planned_source_frame_ordinals'][0]+b))
            if scope=='developer':
                oldv=c.checked_base(scope,job,ix)
                for a,b in oldv['native_frame_realizability']['ranges']:baseline.update(range(part['base_window']['planned_source_frame_ordinals'][0]+a,part['base_window']['planned_source_frame_ordinals'][0]+b))
        rows.append(dict(video_id=job['video_id'],source_group=job['source_group'],selected_native_ordinals=sorted(ids),
            original_B0_native_ordinals=sorted(baseline) if scope=='developer' else None))
    expected=c.read(c.HERE/'prepared.json')['counts'][scope]['changed']
    c.require(len(proofs)==expected,'each new request must have one independent CPU replay')
    c.save(c.HERE/(scope+'_01/replay_acceptance.json'),dict(status='PASS_ALL_BALANCED_NEW_REQUESTS_CPU_REPLAY',utc=c.utc(),proofs=proofs,
        new_calls=expected,original_successes_referenced=sum(len(j['windows']) for j in jobs)-expected,new_model_calls=0,new_optimizer_updates=0))
    if scope=='developer':
        c.save(c.HERE/'developer_01/matched_rows.json',rows)
        c.save(c.HERE/'developer_01/report.json',dict(status='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426',utc=c.utc(),records=104,groups=96,
            windows=112,fresh_calls=expected,changed_native_sets=sum(r['selected_native_ordinals']!=r['original_B0_native_ordinals'] for r in rows),
            independent_quality_reference='UNKNOWN',official_score=None,new_training=False,quality_go_claim=False,
            user_override='2026-10-09 proceed with the discussed experiment and ZIP; we are experimenting',
            weak_reference_not_used_to_select_or_retune_recipe=True))

if __name__=='__main__':
    import sys;main(sys.argv[1])
''')

pack=(OLD/'packager.py').read_text().replace('nr_common','bw_common').replace("'Q'","'BW'")
pack=pack.replace('NATIVE_ROUND_ALIGNMENT','BALANCED_TWO_WINDOW').replace('native-nearest','balanced two-window')
pack=pack.replace("    production.scheduling(scope, out)","    schedule_space(scope,out,manifest,clocks,ref)")
pack+='''
'''
# insert actual independent changed-domain selector before finish definition
insert='''
def select_balanced(manifest,temporal,clocks,plan):
    from fractions import Fraction as F
    from bisect import bisect_left
    from contracts import validate_segments
    meta={r['video_id']:r for r in manifest['records']};by_id={r['video_id']:r for r in temporal};jobs={j['video_id']:j for j in plan['jobs']}
    c.require(len(by_id)==len(temporal)==len(meta) and set(meta)==set(by_id)==set(jobs)==set(clocks),'selector identities')
    selected=[]
    for vid in sorted(meta):
        item=meta[vid];row=by_id[vid];job=jobs[vid];clock=clocks[vid]
        points=[F(x) for x in clock['pts']]
        c.require(row['n_frames']==item['n_frames'] and row['video_path']==item['source_path'] and row['targetRatioWH']==item['targetRatioWH'] and
            row['fps']==item['fps_num']/item['fps_den'] and len(row['windows'])==len(job['windows']),'selector source/window identity')
        chosen=set()
        for ix,(value,part) in enumerate(zip(row['windows'],job['windows'])):
            c.require(value['output_valid'] is True and not value['parse_errors'] and value['start_sec']==part['start_sec'] and
                value['end_sec']==part['end_sec'] and value['clock_record_sha256']==clock['clock_record_sha256'],'failed/wrong-clock window')
            segments=value['parsed_segments'];validate_segments(segments,part['end_sec']-part['start_sec'])
            c.require(value['status']==('MODEL_OK' if segments else 'LEGAL_EMPTY'),'invalid empty/failure status')
            if c.is_changed(part):
                start=F(part['window']['exact_normalized_start'])
                for a,b in segments:
                    first,stop=bisect_left(points,start+F(str(a))),bisect_left(points,start+F(str(b)))
                    c.require(first<stop,'no actual frame in exact new segment');chosen.update(range(first,stop))
            else:
                from native_segment_contract import native_segment_ranges
                for first,stop in native_segment_ranges(segments,[float(x) for x in points],part['start_sec'],part['end_sec']-part['start_sec']):chosen.update(range(first,stop))
        for ordinal in sorted(chosen):
            selected.append(dict(video_id=vid,source_frame=ordinal,source_path=item['source_path'],source_width=item['width'],source_height=item['height'],
                source_n_frames=item['n_frames'],fps=item['fps_num']/item['fps_den'],target_ratio_wh=item['targetRatioWH']))
    return selected

def schedule_space(scope,out,manifest,clocks,ref):
    import shutil
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));selected=select_balanced(manifest,old.rows(out/'temporal.jsonl'),clocks,plan)
    cache=c.RUN/'b_score_aligned_package_v4'/(scope+'_01');frozen=c.RUN/'teacher_student_autopilot_v14/cache_01'/(scope+'.json')
    evidence=production.b2_cache_evidence(scope,ref);c.require({k:v for k,v in c.read(frozen).items() if k!='utc'}==evidence,'complete exact spatial cache authority changed')
    schedule=c.read(cache/'schedule.stage.json');field=old.rows(cache/'field_frames.jsonl')
    c.require(field==production.helpers()[3].field_frames(manifest,clocks),'all source field identity/algorithm differs')
    from field_contract import build_field_requests
    c.require(build_field_requests(field,old.rows(cache/'field_shots.jsonl'),8)==old.rows(cache/'anchor_requests.jsonl'),'space request identity differs')
    old.write_rows(out/'selected.jsonl',selected)
    for name in ('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'):
        shutil.copyfile(cache/name,out/name);c.require(c.sha(out/name)==evidence['files'][name],'copied complete field bytes changed')
    c.save(out/'schedule.stage.json',dict(schedule,selected_frames=len(selected),source_cache=str(cache),reused_time_independent_source_field=True))
    space=c.read(cache/'spatial.stage.json');space.update(reused_cache=True,model_calls_this_candidate=0,source_cache=str(cache),anchor_output_sha256=c.sha(out/'anchor_output.jsonl'))
    c.save(out/'spatial.stage.json',space)
    c.save(out/'cache_reuse_receipt.json',dict(status='PASS_COMPLETE_EXACT_SPATIAL_SOURCE_FIELD_NEW_BALANCED_SELECTION',frozen_cache_receipt_sha256=c.sha(frozen),
        selected_sha256=c.sha(out/'selected.jsonl'),original_space_cost_preserved=True,new_spatial_calls=0,files=evidence['files']))

'''
pack=pack.replace('def finish(scope):',insert+'def finish(scope):')
put('packager.py',pack)

controller=(OLD/'controller.py').read_text().replace('nr_common','bw_common').replace('nr_engine','bw_engine').replace('nr_report','bw_report')
controller=controller.replace('aic_NRA_v1_','aic_BW_risk_v1_').replace('native nearest ordinal alignment','exact balanced two-window domains')
start=controller.index("        charges['nontest']=gpu")
end=controller.index("        charges['developer']=gpu",start)
controller=controller[:start]+'''        cpu('nontest_alias',[c.HERE/'bw_alias_nontest.py'])
        for step in ('assemble','finish'):cpu('nontest_'+step,[c.HERE/'packager.py',step,'nontest'])
'''+controller[end:]
start=controller.index("        if report['status']")
end=controller.index("        charges['rematch']=gpu",start)
controller=controller[:start]+'''        c.require(report['status']=='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426','developer engineering not accepted')
'''+controller[end:]
controller=controller.replace("        for step in ('assemble','finish'):cpu('rematch_", "        cpu('rematch_replay',[c.HERE/'bw_report.py','rematch'])\n        for step in ('assemble','finish'):cpu('rematch_")
controller=controller.replace('PASS_INDEPENDENT_NATIVE_ROUND_ALIGNMENT_FINAL','PASS_INDEPENDENT_BALANCED_TWO_WINDOW_RISK_FINAL').replace('PASS_COMPLETE_426_NATIVE_ROUND_ALIGNMENT_ZIP_ON_LINUX','PASS_COMPLETE_426_BALANCED_TWO_WINDOW_RISK_ZIP_ON_LINUX')
put('controller.py',controller)

put('bw_alias_nontest.py','''import bw_common as c
def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers();plan,jobs=c.jobs_for('nontest')
    c.require(len(jobs)==8 and all(not c.is_changed(p) for j in jobs for p in j['windows']),'NT8 must remain exact original')
    for job in jobs:
        for ix,part in enumerate(job['windows']):c.checked(c.done_path('nontest',job,ix,'BW',cc),job,ix,'BW',ex)
    c.save(c.HERE/'nontest_01/nontest.completion.json',dict(status='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS',utc=c.utc(),records=8,
        total_windows=8,fresh_model_calls=0,reused_exact_original_calls=8,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))
if __name__=='__main__':main()
''')

put('freeze.py','''import bw_common as c
def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    c.require(c.read(c.HERE/'cpu_acceptance.json')['status']=='PASS_ALL_CHANGED_BALANCED_NATIVE_PROCESSOR_AND_EXACT_BOUNDARIES','CPU admission missing')
    previous=c.RUN/'native_round_alignment_v1/source_lock.json';files=dict(c.read(previous)['files']);files[str(previous)]=c.sha(previous)
    for p in (c.RUN/'native_round_alignment_v1').glob('*.py'):files[str(p)]=c.sha(p)
    resume=c.read(c.HERE/'input_01/resume_manifest.json')
    for row in resume['rows']:files[row['path']]=row['sha256'];files.update(row['bound_files'])
    for p in c.HERE.rglob('*'):
        if p.is_file():files[str(p)]=c.sha(p)
    for p,s in files.items():c.require(c.sha(p)==s,'pre-freeze source changed: '+p)
    c.save(c.HERE/'source_lock.json',dict(schema='AIC_BALANCED_TWO_WINDOW_USER_ACCEPTED_RISK_V1',files=files,utc=c.utc(),
        scientific_recipe='exact two equal windows only when original two-window duration strictly between30and60',new_model_calls_at_freeze=0))
    c.save(c.HERE/'preflight.json',dict(status='PASS_FROZEN_BALANCED_TWO_WINDOW_CPU_BINDING',utc=c.utc(),source_lock_sha256=c.sha(c.HERE/'source_lock.json')))
    print(dict(files=len(files),source_lock_sha256=c.sha(c.HERE/'source_lock.json')),flush=True)
if __name__=='__main__':main()
''')
launch=(OLD/'launch.py').read_text().replace('nr_common','bw_common').replace('PASS_FROZEN_NATIVE_ROUND_ALIGNMENT_CPU_BINDING','PASS_FROZEN_BALANCED_TWO_WINDOW_CPU_BINDING')
put('launch.py',launch)

final=(OLD/'final_acceptance.py').read_text().replace('nr_common','bw_common').replace("'Q'","'BW'").replace('NATIVE_ROUND_ALIGNMENT','BALANCED_TWO_WINDOW_RISK')
start=final.index('    # Independently reconstruct')
end=final.index('    reports={}',start)
final=final[:start]+'''    proofs={}
    for scope in ('developer','rematch'):
        replay=c.read(c.HERE/(scope+'_01/replay_acceptance.json'));plan,jobs=c.jobs_for(scope)
        expected=c.read(c.HERE/'prepared.json')['counts'][scope]['changed']
        c.require(replay['status']=='PASS_ALL_BALANCED_NEW_REQUESTS_CPU_REPLAY' and len(replay['proofs'])==expected,'complete independent replay')
        accepted={p['path']:p for p in replay['proofs']}
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                p=c.done_path(scope,job,ix,'BW',cc);v=c.checked(p,job,ix,'BW',ex)
                if c.is_changed(part):c.require(str(p) in accepted and c.sha(p)==accepted[str(p)]['done_sha256'],'accepted done bytes changed')
        proofs.update(accepted)
    c.require(c.read(c.HERE/'developer_01/report.json')['status']=='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426','user risk recipe engineering not complete')
'''+final[end:]
final=final.replace("'PASS_ALL_NATIVE_BALANCED_TWO_WINDOW_RISK_ATTEMPTS'","'PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS'")
final=final.replace("for name in ('nontest','developer','rematch'):","for name in ('developer','rematch'):")
final=final.replace('aic_NRA_v1_','aic_BW_risk_v1_')
final=final.replace("c.read(c.HERE/'input_01/resume_manifest.json')['resources']","{'spatial_and_V14_original_terminal_costs_preserved':True}")
final=final.replace("'native_nearest64_same_count_grid_endpoints':True,'no_native_PTS_rounding':True,","'balanced_two_windows_exact_midpoint':True,'no_native_PTS_rounding':True,")
final=final.replace("'independent_gate_reconstructed_from_all104_raw':True,","'user_explicitly_accepted_experiment_risk':True,'independent_quality_reference':'UNKNOWN',")
put('final_acceptance.py',final)

put('PROTOCOL.md','''# Balanced two-window user-authorized risk experiment v1

2026-10-09 最新用户明确要求“按照讨论出来的方案去训练打包zip，本来我们就是在试的”。据此独立执行讨论中的双窗均衡候选。保留此前讨论和全部科学STOP，当前用户接受风险的授权取代上一轮主控的G0止步决定。独立质量参考、提分和新官网分均UNKNOWN，不宣称旧科学门通过。

原B8B/288adapter、B0 prompt、0..5原grammar、greedy、原native clock/source97颜色白名单、floor64、input16384/output256、原video像素预算不变。此方案仅改变推理输入分区，新optimizer/32B/overview/空间调用0；原B已经训练过，不增加无依据的权重训练。

仅原来恰好两窗且总域严格30<duration<60秒：改为[a,(a+b)/2)、[(a+b)/2,b)。中点Fraction精确计算，不吸附PTS、不epsilon、不裁端点。其他原窗完全相同、按完整旧身份和SHA引用成功。每个新窗采样精确域内整数floor64，真实decoder/processor/token/prefix/raw/原validator和独立有理数成员核验。失败不转空、不合并模型结果、不强行补证据。

先完整NT8原请求精确引用/空间原完整源场/11strict，再真实非测试104中16个变化窗新生成与独立CPU回放；质量方向仅UNKNOWN，不按弱分改提示/门/样本。工程通过后执行完整426/521的新计划：所有变化请求真实生成、其他V14原成功exact引用。全426先完整原空间源场，再按本候选时间选择；原31295空间锚点/18723.876秒和旧V14全部GPU成本/7200offset保留。新GPU自然终态费用唯一追加。

仅独立final PASS、8/426全部11strict、ZIP实际size/SHA/CRC/唯一predictions.jsonl/426身份/原字节、全部新CPU回放和所有真实GPU账本通过才交付。新包可能低于旧最佳37.63，旧最佳不覆盖。包留Linux，不自动回传/官网提交。源/资产/代码先CPU验收再锁定/单次launcher。新工程错误保留trace/raw，在独立版本修复；不修改冻结代码或重跑成功。
''')
put('CONTINUE.md','''# 唯一新入口：balanced_two_window_risk_v1

最新用户接受风险并要求真实执行讨论的双窗均衡分区与426 ZIP。当前仅独立代码创建，尚未完成CPU或启动。先读PROTOCOL.md，执行bw_prepare.py→bw_cpu.py→freeze.py→单次launch.py。严禁重复launcher/成功生成。当前方案新优化器0，真实推理和包按回执；独立质量参考/官网分UNKNOWN。保留全部历史冻结锁/raw/STOP/UNKNOWN和成本，不复活旧实验。小量项目控制直SSH已授权，新大流量需许可。
''')
print(NEW)
