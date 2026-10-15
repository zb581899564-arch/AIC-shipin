"""Pure automatic production requests; no pixels, GT, processor or models."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json

SCHEMA='TEMPORAL_PRODUCTION_INPUTS_V1'


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(value):
    require(not isinstance(value,bool),'Explicit seconds required')
    return F(str(value))


def old_clock(arrays,record):
    """A planning witness, never a newly measured native terminal duration."""
    tick=F(arrays['raw_time_base']);raw=[F(x)*tick for x in arrays['native_pts_ticks']]
    origin=F(arrays['raw_first_pts_ticks'])*tick
    require(raw and raw[0]==origin and all(a<b for a,b in zip(raw,raw[1:])),'Old full native PTS/origin invalid')
    endticks=arrays['native_frame_end_pts_ticks']
    require(isinstance(endticks,list) and len(endticks)==len(raw),'Old explicit end-tick array required; no guessed N/fps fallback')
    end=F(endticks[-1])*tick-origin
    points=[p-origin for p in raw]
    require(end>points[-1] and len(raw)==arrays['n_frames']==record['n_frames'],'Old clock denominator/planned domain invalid')
    return dict(original_exact_pts=list(map(str,raw)),normalized_exact_pts=list(map(str,points)),
        first_original_pts_exact=str(origin),planned_physical_end_exact=str(end),n_frames=len(raw),
        old_terminal_evidence=record['terminal_evidence'],native_terminal_reverified=False,
        old_CFR_end_is_measured_duration=False)


def floor64(points,lo,hi):
    first,stop=bisect_left(points,lo),bisect_left(points,hi)
    if stop-first<64:return None
    indices=[first+i*(stop-first-1)//63 for i in range(64)]
    require(len(set(indices))==64,'floor64 repeated a source frame')
    return indices


def request_skeletons(sources):
    """Freeze all IDs/ordinals/leases before results; no adaptive requests."""
    requests,leases={},{}
    for source in sources:
        sid=source['source_id'];clock=source['old_clock'];pts=list(map(F,clock['normalized_exact_pts']))
        end=F(clock['planned_physical_end_exact'])
        for window in source['windows']:
            lo,hi=map(F,window['original_window_exact'])
            ordinals=window['original_frame_ordinals']
            require(len(ordinals)==len(set(ordinals))==64 and all(type(i)is int and 0<=i<len(pts) for i in ordinals) and
                all(a<b for a,b in zip(ordinals,ordinals[1:])) and all(lo<=pts[i]<hi for i in ordinals),
                'Original coarse visual64 identity is invalid; no replacement sampling')
            for event in window['events']:
                first,last=map(F,event['original_interval_exact'])
                require(0<=lo<=first<last<=hi and hi-lo<=30,'Original candidate/full coarse window outside fixed scope')
                for side,pivot in (('start',first),('end',last)):
                    rid=event['event_id']+'.'+side;left,right=max(F(0),pivot-3),min(end,pivot+3)
                    selected=floor64(pts,left,right)
                    row=dict(event,request_id=rid,source_id=sid,kind='ENDPOINT',side=side,
                        window_start=str(left),window_end=str(right),original_endpoint_exact=str(pivot),
                        execution='MODEL' if selected is not None else 'STRUCTURAL_UNKNOWN_NO64',
                        source_frame_ordinals=selected,sample_exact_pts=[str(pts[i]) for i in selected] if selected else None)
                    if selected is None:
                        row['structural_endpoint_result']=dict(request_id=rid,event_id=event['event_id'],side=side,
                            raw_decision={'decision':'UNKNOWN'},applied_decision='UNKNOWN_INSUFFICIENT_DISTINCT_NATIVE_FRAMES',
                            original_endpoint_exact=str(pivot),endpoint_exact=str(pivot),displacement_exact='0',changed=False,
                            actual_model_call=False,declared_before_model=True)
                    requests[rid]=row
                rid=event['event_id']+'.verify'
                requests[rid]=dict(event,request_id=rid,source_id=sid,kind='VERIFY',execution='MODEL',
                    window_start=str(lo),window_end=str(hi),source_frame_ordinals=ordinals,
                    sample_exact_pts=[str(pts[i]) for i in ordinals],original_frame_pixel_sha256=window['original_frame_pixel_sha256'])
    for rid,row in requests.items():
        if row['execution']!='MODEL':continue
        key=digest(dict(source_id=row['source_id'],ordinals=row['source_frame_ordinals'],pts=row['sample_exact_pts']))
        lease_id='RGB_'+key[:40];row['lease_id']=lease_id
        lease=leases.setdefault(lease_id,dict(rgb_relative='staging/rgb/'+lease_id+'.npz',consumers=[],
            source_id=row['source_id'],source_frame_ordinals=row['source_frame_ordinals'],sample_exact_pts=row['sample_exact_pts']))
        lease['consumers'].append(rid)
    require(len(requests)==sum(len(w['events'])*3 for s in sources for w in s['windows']), 'Duplicate frozen request identity')
    return dict(schema=SCHEMA,requests=list(requests.values()),RGB_groups=leases,
        consumers=[rid for rid,row in requests.items() if row['execution']=='MODEL'],
        structural_unknown_requests=[rid for rid,row in requests.items() if row['execution']!='MODEL'],
        request_membership_can_change_with_results=False,batch_size_may_change_for_capacity_only=True,
        new_model_calls=0,new_media_decodes=0,new_processor_encodes=0)


def measured_clock(source,raw,durations,geometry,stream):
    """Keep real measurement, then strict old PTS/origin/end identity gates."""
    require(raw and durations[-1] is not None and durations[-1]>0,'New measured positive last duration unavailable')
    origin=raw[0];points=[p-origin for p in raw];end=points[-1]+durations[-1]
    clock=dict(source_id=source['source_id'],source_sha256=source['source_sha256'],source_path=source['source_path'],
        original_exact_pts=list(map(str,raw)),normalized_exact_pts=list(map(str,points)),first_original_pts_exact=str(origin),
        n_frames=len(raw),physical_end_exact=str(end),last_frame_duration_exact=str(durations[-1]),
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
            last_normalized_pts_exact=str(points[-1]),last_frame_duration_exact=str(durations[-1])),
        native_duration_by_ordinal={str(i):str(value) if value is not None else None for i,value in enumerate(durations)},
        measured_geometry=list(geometry),video_stream_index=stream['index'],stream_time_base_exact=stream['time_base'],
        measured_average_rate_exact=stream['average_rate'],new_native_RGB_materialization_decodes=1,
        old_clock_not_overwritten=True,nominal_fps_or_container_duration_used_for_end=False,audio_observed=False)
    return clock


def compare_clock(source,clock):
    old=source['old_clock']
    require(clock['original_exact_pts']==old['original_exact_pts'] and
        clock['normalized_exact_pts']==old['normalized_exact_pts'] and
        clock['first_original_pts_exact']==old['first_original_pts_exact'] and
        clock['physical_end_exact']==old['planned_physical_end_exact'] and
        clock['n_frames']==old['n_frames'] and clock['measured_geometry']==[source['width'],source['height']],
        'New native PTS/origin/positive-last-duration/end differs; STOP without rewriting old clock or labels')


def materialized_request(source,skeleton,clock,boundary,continuity,verify,durations):
    base=dict(skeleton,source_name=source['source_id'],source_group='Production:'+source['source_id'],
        source_path=source['source_path'],source_sha256=source['source_sha256'],source_bytes=source['source_bytes'],
        width=source['width'],height=source['height'],fps_num=source['fps_num'],fps_den=source['fps_den'],
        source_total_frames=clock['n_frames'],all_source_exact_pts=clock['normalized_exact_pts'],
        original_clock_origin_exact=clock['first_original_pts_exact'],audio_observed=False,reference_available_to_inference=False)
    if skeleton['kind']=='ENDPOINT':
        planned=boundary.plan_endpoint(base,skeleton['side'],clock)
        require(planned['source_frame_ordinals']==skeleton['source_frame_ordinals'] and
                planned['window_start']==skeleton['window_start'] and planned['window_end']==skeleton['window_end'],
                'Measured endpoint request differs from full pre-model frozen algorithm')
        base.update(planned)
        base['continuity_by_sample'],base['original_endpoint_continuity_verified']=continuity(base,clock,durations)
        base['prompt']=boundary.prompt(base)
        base['finite_response_strings']=list(boundary.response_strings(base))
    else:
        req=verify.request(base,dict(base,case_id=base['original_case_id']))
        base.update(req)
        base['request_id']=skeleton['request_id']
        base['prompt']=verify.prompt(req)
        base['finite_response_strings']=list(verify.responses(req))
    return base
