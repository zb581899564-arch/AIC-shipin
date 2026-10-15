"""Automatic accepted B0 metadata projection; never opens video/GT/pixels."""
import argparse
from pathlib import Path

import tp_io as io
from tp_contract import SCHEMA,digest,exact,old_clock,request_skeletons,require


def project(reg):
    plan=io.read(io.bound(reg['original_plan_ref'],(io.RUN,)))
    temporal_path=io.bound(reg['accepted_coarse_temporal_ref'],(io.RUN,))
    import json
    accepted={row['video_id']:row for row in [json.loads(line) for line in temporal_path.read_text().splitlines() if line.strip()]}
    registry=io.read(io.bound(reg['original_clock_registry_ref'],(io.RUN,)))
    records={row['video_id']:row for row in registry['records']}
    require(plan['input_ref']['registry_sha256']==reg['original_clock_registry_ref']['sha256'],'Original plan/clock registry binding changed')
    require(len(plan['jobs'])==len(accepted)==len(records)==426,'Complete fixed 426 source denominator')
    sources=[];window_count=event_count=0
    for job in plan['jobs']:
        vid=job['video_id'];meta=job['metadata'];record=records[vid];answer=accepted[vid]
        sid='P_'+digest(vid)[:32]
        path=Path(meta['source_path']).resolve()
        require(path.is_relative_to(io.MEDIA_ROOT) and path.is_file(),'Only immutable formal source media path metadata admitted')
        clock_ref=record['clock_arrays'];clockpath=io.bound(clock_ref,(io.RUN,))
        arrays=io.read(clockpath);arrays=arrays.get('arrays',arrays)
        require(meta['source_sha256']==record['source_sha256']==arrays['source_sha256'],'Source/old clock byte identity changed')
        clock=old_clock(arrays,record)
        source=dict(source_id=sid,video_id=vid,source_path=str(path),source_sha256=meta['source_sha256'],
            source_bytes=path.stat().st_size,width=meta['width'],height=meta['height'],fps_num=meta['fps_num'],fps_den=meta['fps_den'],
            original_clock_ref=clock_ref,original_record_sha256=digest(record),old_clock=clock,windows=[])
        require(len(job['windows'])==len(answer['windows']),'Original accepted window denominator')
        for ix,(part,done) in enumerate(zip(job['windows'],answer['windows'])):
            require(done['output_valid'] is True and not done['parse_errors'] and done['status'] in ('MODEL_OK','LEGAL_EMPTY'),
                    'Only accepted original B0 outcomes, including legal-empty coverage')
            lo,hi=exact(part['start_sec']),exact(part['end_sec']);visual=done['video_identity']
            require(visual['source_sha256']==source['source_sha256'] and visual['sampled_frames']==64 and
                visual['source_frame_ids']==part['window']['planned_source_frame_ordinals'],
                'Original coarse visual/frame plan identity changed')
            case=sid+'_W'+str(ix).zfill(3)
            window=dict(original_case_id=case,original_legacy_window_id=part['window']['window_id'],
                original_window_exact=[str(lo),str(hi)],original_frame_ordinals=visual['source_frame_ids'],
                original_frame_pixel_sha256=visual['frame_pixel_sha256'],accepted_window_sha256=digest(done),
                original_window_plan_sha256=digest(part),status=done['status'],events=[])
            for seg,(a,b) in enumerate(done['parsed_segments']):
                interval=[str(lo+exact(a)),str(lo+exact(b))]
                window['events'].append(dict(event_id=case+'_E'+str(seg).zfill(2),original_case_id=case,
                    original_legacy_window_id=window['original_legacy_window_id'],original_segment_index=seg,
                    original_interval_exact=interval,original_window_exact=window['original_window_exact'],
                    original_window_start_exact=str(lo),original_window_end_exact=str(hi),
                    accepted_window_sha256=window['accepted_window_sha256']))
                event_count+=1
            source['windows'].append(window);window_count+=1
        sources.append(source)
    require(window_count==521 and event_count==665 and len({s['source_id'] for s in sources})==426,'Fixed 426/521/665 identity denominator')
    frozen=request_skeletons(sources)
    frozen.update(sources=sources,original_plan_ref=reg['original_plan_ref'],accepted_coarse_temporal_ref=reg['accepted_coarse_temporal_ref'],
        original_clock_registry_ref=reg['original_clock_registry_ref'],old_spatial_field_refs=reg['old_spatial_field_refs'],
        source_count=426,window_count=521,event_count=665,original_coarse_answers_rerun=False)
    return frozen


def main(path):
    io.host();reg=io.registration(path)
    frozen=project(reg)
    out=io.BASE/'plan_01';out.mkdir(exist_ok=False)
    io.save(out/'full_plan.json',frozen)
    io.save(out/'completion.json',dict(status='FROZEN_ALL_PRODUCTION_REQUESTS_CONSUMERS_NOT_DECODE_ADMISSION',
        schema=SCHEMA,registration_path=str(path),registration_sha256=io.sha(path),full_plan_sha256=io.sha(out/'full_plan.json'),
        actual_consumers=len(frozen['consumers']),structural_unknown_requests=frozen['structural_unknown_requests'],
        model_calls=0,processor_calls=0,media_decodes=0))


if __name__=='__main__':
    import os
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';main(args.registration)
