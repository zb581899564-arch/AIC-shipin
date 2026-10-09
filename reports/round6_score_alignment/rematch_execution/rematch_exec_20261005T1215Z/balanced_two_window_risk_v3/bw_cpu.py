"""Actual pinned input consumer admission, no model or optimizer calls."""
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
                for segments in ([[0,1]],[[0,1],[1,2]],[]):
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
