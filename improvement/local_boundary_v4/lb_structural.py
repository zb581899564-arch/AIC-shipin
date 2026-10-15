"""Independent pure geometry for typed short contexts. No media/model imports."""
from fractions import Fraction as F


def validate_partition(events, actionable, skips):
    expected = {event['event_id']+'.'+side for event in events for side in ('start','end')}
    ids = [x['request_id'] for x in actionable]+[x['request_id'] for x in skips]
    if len(expected) != 2*len(events) or len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError('Nominal endpoints must equal disjoint actionable plus structural skips')
    if any(x.get('actionable') is not True or x.get('structural_skip') is not False for x in actionable):
        raise ValueError('A structural endpoint entered actual request list')
    if any(x.get('actionable') is not False or x.get('structural_skip') is not True or
           x.get('structural_status') != 'SHORT_NATIVE_CONTEXT_UNAVAILABLE' for x in skips):
        raise ValueError('An ordinary request/failure became a structural skip')
    return dict(nominal_endpoints=len(ids),actionable_requests=len(actionable),structural_skips=len(skips))


def independent_skip(skip, clock):
    """Separate list/count implementation; never invokes producer plan_endpoint."""
    if (skip.get('actionable') is not False or skip.get('structural_skip') is not True or
            skip.get('structural_status') != 'SHORT_NATIVE_CONTEXT_UNAVAILABLE' or
            skip.get('half_window_exact') != '3' or skip.get('required_native_frames') != 64 or
            skip.get('model_called') is not False or skip.get('processor_encoded') is not False or
            skip.get('RGB_read') is not False):
        raise ValueError('Only exact typed uncalled native64 structural skips are verifiable')
    original = list(map(F, clock['original_exact_pts']))
    points = list(map(F, clock['normalized_exact_pts']))
    origin = F(clock['first_original_pts_exact'])
    duration, physical = F(clock['last_frame_duration_exact']), F(clock['physical_end_exact'])
    if (not points or len(points) != len(original) or len(points) != clock['n_frames'] or
            original[0] != origin or points[0] != 0 or any(a>=b for a,b in zip(points,points[1:])) or
            any(raw-origin != normalized for raw,normalized in zip(original,points)) or
            duration <= 0 or physical != points[-1]+duration):
        raise ValueError('Structural skip complete native clock identity/domain changed')
    if (clock['source_sha256'] != skip['source_sha256'] or clock['source_id'] != skip['source_id'] or
            clock['source_bytes'] != skip['source_bytes'] or len(points) != skip['source_total_frames'] or
            [str(x) for x in points] != skip['all_source_exact_pts'] or
            str(origin) != skip['original_clock_origin_exact']):
        raise ValueError('Structural skip source/fullclock identity differs')
    start,end = map(F,skip['original_interval_exact'])
    side=skip['side'];pivot=start if side=='start' else end
    if side not in ('start','end') or not 0<=start<end<=physical:
        raise ValueError('Structural skip original event/side interval invalid')
    lo,hi=max(F(0),pivot-F(3)),min(physical,pivot+F(3))
    count=sum(lo<=point<hi for point in points)
    first=sum(point<lo for point in points)
    limit=sum(point<hi for point in points)
    if (count >= 64 or count != limit-first or str(lo) != skip['window_start'] or
            str(hi) != skip['window_end'] or str(pivot) != skip['original_endpoint_exact'] or
            first != skip['eligible_first_ordinal'] or limit != skip['eligible_stop_ordinal'] or
            count != skip['actual_context_native_frames'] or
            skip['original_endpoint_preserved'] is not True or skip['native64_gate_lowered'] is not False or
            skip['padded_frames'] is not False or skip['wider_window'] is not False):
        raise ValueError('Structural skip exact fixed window/native count differs')
    endpoint = dict(request_id=skip['request_id'],event_id=skip['event_id'],side=side,
        raw_decision=None,static_decision={'decision':'UNKNOWN'},
        decision_origin='STRUCTURAL_GEOMETRY_NOT_MODEL',
        applied_decision='UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE',
        original_endpoint_exact=str(pivot),endpoint_exact=str(pivot),displacement_exact='0',changed=False,
        model_called=False,processor_encoded=False,structural_skip=True)
    endpoint.update(actual_model_call=False,predeclared_skip=True)
    return dict(status='PASS_FIRST_INDEPENDENT_STRUCTURAL_GEOMETRY_NO_MEDIA_PROCESSOR_MODEL',
        request_id=skip['request_id'],event_id=skip['event_id'],side=side,
        source_id=skip['source_id'],source_sha256=skip['source_sha256'],
        clock_reference=skip['original_evidence']['clock'],source_total_frames=len(points),
        window_start=str(lo),window_end=str(hi),actual_context_native_frames=count,
        required_native_frames=64,endpoint_result=endpoint,new_media_reads=0,new_processor_encodes=0,
        new_model_calls=0,new_optimizer_updates=0,not_a_failed_model_fallback=True)


def independent_availability(record,clock):
    """All nominal endpoints, independently count the complete clock geometry."""
    points=list(map(F,clock['normalized_exact_pts']))
    original=list(map(F,clock['original_exact_pts']))
    origin=F(clock['first_original_pts_exact']);physical=F(clock['physical_end_exact'])
    if (not points or len(points)!=clock['n_frames'] or len(points)!=len(original) or points[0]!=0 or
            any(a>=b for a,b in zip(points,points[1:])) or
            any(a-origin!=b for a,b in zip(original,points)) or
            physical!=points[-1]+F(clock['last_frame_duration_exact']) or physical<=points[-1] or
            record['source_sha256']!=clock['source_sha256'] or record['source_id']!=clock['source_id'] or
            record['source_total_frames']!=len(points) or record['all_source_exact_pts']!=list(map(str,points))):
        raise ValueError('Independent complete availability source/clock identity failed')
    start,end=map(F,record['original_interval_exact']);side=record['side']
    if side not in ('start','end') or not 0<=start<end<=physical:
        raise ValueError('Independent nominal endpoint interval failed')
    pivot=start if side=='start' else end
    lo,hi=max(F(0),pivot-F(3)),min(physical,pivot+F(3))
    count=sum(lo<=p<hi for p in points)
    available=count>=64
    if (str(lo)!=record['window_start'] or str(hi)!=record['window_end'] or
            count!=record['actual_context_native_frames'] or record['required_native_frames']!=64 or
            record['actionable']!=available or record['structural_skip']==available):
        raise ValueError('Producer availability differs from independent clock-only count')
    return dict(event_id=record['event_id'],side=side,request_id=record['request_id'],
        status='AVAILABLE_NATIVE_CONTEXT' if available else 'SHORT_NATIVE_CONTEXT_UNAVAILABLE',
        native_frame_count=count,required_native_frames=64,source_id=record['source_id'],
        source_sha256=record['source_sha256'],full_clock_reference=record['original_evidence']['clock'],
        window_start=str(lo),window_end=str(hi),new_media_reads=0,new_processor_encodes=0,new_model_calls=0)
