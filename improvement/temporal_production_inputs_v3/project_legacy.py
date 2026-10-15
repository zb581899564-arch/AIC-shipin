"""Automatic metadata-only V3 projection; no media body, GT or pixel reads."""
import argparse
import json
from fractions import Fraction as F
from pathlib import Path
import tp_io as io
from tp_contract import SCHEMA,READER_SCOPE,digest,exact,old_clock,ordinal_cut,physical_plan_clock,request_skeletons,require,same_ref,validate_reader_scope


def project(reg):
    plan=io.read(io.bound(reg['original_plan_ref'],(io.RUN,)))
    temporal_path=io.bound(reg['accepted_coarse_temporal_ref'],(io.RUN,))
    rows=[json.loads(line) for line in temporal_path.read_text().splitlines() if line.strip()]
    accepted={row['video_id']:row for row in rows}
    registry=io.read(io.bound(reg['original_clock_registry_ref'],(io.RUN,)))
    records={row['video_id']:row for row in registry['records']}
    normalized=io.read(io.bound(reg['D8_normalized_windows_ref'],(io.RUN,)))
    normalized_by_id={row['video_id']:row['windows'] for row in normalized['records']}
    D8_clocks=io.read(io.bound(reg['D8_original_clocks_ref'],(io.RUN,)))
    packet_registration=io.read(io.bound(reg['packet_registration_ref'],(io.CAMPAIGN,)))
    packet_complete=io.read(io.bound(reg['packet_completion_ref'],(io.CAMPAIGN,)))
    packet_sources={row['video_id']:row for row in packet_registration['sources']}
    packet_refs=dict(packet_complete['success_terminal_refs'])
    require(not set(packet_refs)&set(packet_complete['failure_terminal_refs']),'Duplicate original packet terminal identity')
    packet_refs.update(packet_complete['failure_terminal_refs'])
    scope=io.read(io.bound(reg['reader_native_terminal_scope_ref'],(io.BASE,)))
    validate_reader_scope(scope)
    require(plan['input_ref']['registry_sha256']==reg['original_clock_registry_ref']['sha256'] and
        same_ref(packet_registration['original_plan_ref'],reg['original_plan_ref']) and
        same_ref(packet_registration['original_clock_registry_ref'],reg['original_clock_registry_ref']) and
        same_ref(packet_complete['registration_ref'],reg['packet_registration_ref']) and
        same_ref(scope['packet_first_measurement_ref'],reg['packet_completion_ref']),
        'Old recipe/full PTS and packet registration identity changed')
    require(packet_complete['status']=='COMPLETE_FIRST426_PACKET_WITNESS_AGGREGATE_NOT_FULL_FRAME_DECODE' and
        packet_complete['registered_sources']==426 and packet_complete['attempted_source_terminal_count']==426 and
        packet_complete['remaining_unattempted_sources']==0 and packet_complete['fatal'] is None and
        packet_complete['frame_decode_calls']==0,'First original packet measurement must be naturally complete, not frame-decode admission')
    require(len(plan['jobs'])==len(rows)==len(accepted)==len(records)==len(normalized_by_id)==len(D8_clocks)==
        len(packet_sources)==len(packet_refs)==426 and
        set(accepted)==set(records)==set(normalized_by_id)==set(D8_clocks)==set(packet_sources)==set(packet_refs)==
        {str(i) for i in range(426)},'Fixed complete426 identities required')
    sources=[];window_count=event_count=0
    for job in plan['jobs']:
        vid=job['video_id'];meta=job['metadata'];record=records[vid];answer=accepted[vid];ps=packet_sources[vid]
        sid='P_'+digest(vid)[:32]
        path=Path(meta['source_path']).resolve()
        require(path.is_relative_to(io.MEDIA_ROOT) and str(path)==ps['source_path'],
            'Only immutable formal media path metadata admitted')
        clock_ref=record['clock_arrays'];arrays=io.read(io.bound(clock_ref,(io.RUN,)))
        arrays=arrays.get('arrays',arrays)
        require(meta['source_sha256']==record['source_sha256']==arrays['source_sha256']==ps['source_sha256'] and
            arrays['video_id']==vid and arrays['n_frames']==meta['n_frames']==ps['n_frames'],
            'Source/old complete PTS identity changed')
        old=old_clock(arrays,record);d8=D8_clocks[vid]
        require(F(d8['raw_time_base'])==F(arrays['raw_time_base']) and
            d8['raw_first_pts_ticks']==arrays['raw_first_pts_ticks'] and
            d8['native_pts_ticks']==arrays['native_pts_ticks'] and
            d8['clock_record_sha256']==clock_ref['sha256'],'Original D8/full native PTS recipe binding changed')
        terminal=io.read(io.bound(packet_refs[vid],(io.CAMPAIGN,)))
        source=dict(source_id=sid,video_id=vid,source_path=str(path),source_sha256=meta['source_sha256'],
            source_bytes=ps['source_stat']['bytes'],packet_source_stat=ps['source_stat'],
            width=meta['width'],height=meta['height'],fps_num=meta['fps_num'],fps_den=meta['fps_den'],
            original_clock_ref=clock_ref,original_record_sha256=digest(record),old_clock=old,
            packet_terminal_observation_ref=packet_refs[vid],packet_registration_ref=reg['packet_registration_ref'],
            packet_completion_ref=reg['packet_completion_ref'],
            packet_original_validation_status=terminal['status'],old_packet_FAIL_preserved=terminal['status'].startswith('FAIL_'),
            reader_native_terminal_scope_ref=reg['reader_native_terminal_scope_ref'],windows=[])
        source['physical_plan_clock']=physical_plan_clock(source,ps,terminal,scope)
        pts=list(map(F,old['normalized_exact_pts']));physical_end=F(source['physical_plan_clock']['physical_end_exact'])
        require(len(job['windows'])==len(answer['windows'])==len(normalized_by_id[vid]),'Original source/window denominator changed')
        for ix,(part,done,norm) in enumerate(zip(job['windows'],answer['windows'],normalized_by_id[vid])):
            require(done['output_valid'] is True and not done['parse_errors'] and done['status'] in ('MODEL_OK','LEGAL_EMPTY'),
                'Only true accepted B0 outcomes, including legal empty coverage')
            require(norm['segments']==done['parsed_segments'] and norm['original_status']==done['status'] and
                norm['clock_record_sha256']==clock_ref['sha256'],'Old D8 normalized segment/status/clock binding changed')
            lo,hi=F(norm['start_exact']),F(norm['end_exact']);visual=done['video_identity']
            ordinals=part['window']['planned_source_frame_ordinals']
            require(visual['source_sha256']==source['source_sha256'] and visual['sampled_frames']==64 and
                visual['source_frame_ids']==ordinals==done['window']['planned_source_frame_ordinals'] and
                len(visual['frame_pixel_sha256'])==64 and all(isinstance(x,str) and len(x)==64 for x in visual['frame_pixel_sha256']),
                'Original accepted visual64/pixel/source identity changed')
            first=ordinals[0];eligible=part['window']['eligible_source_frame_count']
            require(type(eligible)is int and eligible==done['window']['eligible_source_frame_count'],
                'Complete original eligible ordinal denominator changed')
            stop=first+eligible
            require(0<=first<stop<=len(pts),'Original full eligible source ordinal domain invalid')
            ranges=done['native_frame_realizability']['ranges']
            require(done['native_frame_realizability']['status']=='PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY' and
                len(ranges)==len(done['parsed_segments']),'Original accepted core-range proof required')
            case=sid+'_W'+str(ix).zfill(3)
            window=dict(original_case_id=case,original_legacy_window_id=part['window']['window_id'],
                original_window_exact=[str(lo),str(hi)],original_frame_ordinals=ordinals,
                eligible_source_ordinal_bounds=[first,stop],original_frame_pixel_sha256=visual['frame_pixel_sha256'],
                accepted_window_sha256=digest(done),original_window_plan_sha256=digest(part),
                original_D8_normalized_window_sha256=digest(norm),status=done['status'],
                raw_float_window_is_not_new_view_domain=True,events=[])
            for seg,((a,b),pair) in enumerate(zip(norm['segments'],ranges)):
                require(isinstance(pair,list) and len(pair)==2 and all(type(x)is int for x in pair) and
                    0<=pair[0]<pair[1]<=eligible,'Exact accepted window-local half-open integer core required')
                interval=[str(lo+exact(a)),str(lo+exact(b))]
                core=[first+pair[0],first+pair[1]]
                native=[str(ordinal_cut(pts,x,physical_end)) for x in core]
                require(lo<=F(interval[0])<F(interval[1])<=hi,'Original D8 recipe interval invalid')
                window['events'].append(dict(event_id=case+'_E'+str(seg).zfill(2),original_case_id=case,
                    original_legacy_window_id=window['original_legacy_window_id'],original_segment_index=seg,
                    original_interval_exact=interval,original_window_exact=window['original_window_exact'],
                    original_window_start_exact=str(lo),original_window_end_exact=str(hi),
                    original_native_cut_interval_exact=native,original_native_cut_source_ordinals=core,
                    original_core_window_local_range=pair,legacy_recipe_coordinate_source='FROZEN_D8_NORMALIZED_WINDOWS',
                    native_cut_coordinate_source='FROZEN_ACCEPTED_CORE_SOURCE_ORDINALS_ON_NEW_READER_NATIVE_DOMAIN',
                    accepted_window_sha256=window['accepted_window_sha256'],
                    accepted_native_realizability_sha256=digest(done['native_frame_realizability']),
                    original_D8_normalized_window_sha256=window['original_D8_normalized_window_sha256']))
                event_count+=1
            source['windows'].append(window);window_count+=1
        sources.append(source)
    require(window_count==521 and event_count==665 and len({s['source_id'] for s in sources})==426,
        'Fixed426/521/665 denominator changed')
    frozen=request_skeletons(sources)
    frozen.update(sources=sources,original_plan_ref=reg['original_plan_ref'],
        accepted_coarse_temporal_ref=reg['accepted_coarse_temporal_ref'],original_clock_registry_ref=reg['original_clock_registry_ref'],
        D8_normalized_windows_ref=reg['D8_normalized_windows_ref'],D8_original_clocks_ref=reg['D8_original_clocks_ref'],
        reader_native_terminal_scope_ref=reg['reader_native_terminal_scope_ref'],
        packet_registration_ref=reg['packet_registration_ref'],packet_completion_ref=reg['packet_completion_ref'],
        old_spatial_field_refs=reg['old_spatial_field_refs'],source_count=426,window_count=521,event_count=665,
        source_order='UNCHANGED_ORIGINAL_PLAN_ORDER',original_coarse_answers_rerun=False,
        legacy_recipe_or_old_packet_files_overwritten=False)
    return frozen


def main(path):
    io.host();reg=io.registration(path);frozen=project(reg)
    out=io.BASE/'plan_01';out.mkdir(exist_ok=False)
    io.save(out/'full_plan.json',frozen)
    io.save(out/'completion.json',dict(status='FROZEN_ALL_DUAL_COORDINATE_REQUESTS_NOT_DECODE_ADMISSION',
        schema=SCHEMA,registration_path=str(path),registration_sha256=io.sha(path),
        full_plan_sha256=io.sha(out/'full_plan.json'),actual_consumers=len(frozen['consumers']),
        nominal_requests=frozen['nominal_requests'],structural_unknown_requests=frozen['structural_unknown_requests'],
        model_calls=0,processor_calls=0,media_decodes=0,old_packet_validation_failures_reclassified=False))


if __name__=='__main__':
    import os
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';main(args.registration)
