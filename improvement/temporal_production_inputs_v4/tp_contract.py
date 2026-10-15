"""Pure V4 dual coordinates and exact original-ordinal VERIFY support."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import re

SCHEMA='TEMPORAL_PRODUCTION_INPUTS_V4_DUAL_RECIPE_READER_NATIVE_VERIFY_ORDINAL_CONTEXT'
READER_SCOPE='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT'


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(value):
    require(not isinstance(value,bool),'Explicit finite exact seconds required')
    return value if isinstance(value,F) else F(str(value))


def same_ref(first,second):
    return first['path']==second['path'] and first['sha256']==second['sha256']


def validate_reader_scope(scope):
    gates=['source_bytes_and_SHA_exact_original','complete_all_original_frame_PTS_exactly_equal_old',
        'frame_count_and_origin_exactly_equal_old','frame_geometry_exactly_equal_old',
        'actual_last_Frame_duration_positive_in_actual_frame_time_base',
        'last_Frame_duration_exactly_equals_first_packet_observation_duration']
    require(scope['schema']=='MAIN_READER_NATIVE_TERMINAL_SCOPE_V4' and
        scope['status']=='FROZEN_NEW_READER_SCOPE_NOT_ACTUAL_DECODE_GPU_ADMISSION' and
        scope['scope']==READER_SCOPE and scope['source_denominator']==426 and scope['reader_version']=='17.1.0' and
        scope['source_identity_subset_exception'] is False and scope['old_equality_failure_count']==5 and
        scope['old_D8_recipe_and_clock_refs_unchanged'] is True and scope['first_new_RGB_decode_gate']==gates and
        scope['new_terminal_equals_old_Nfps_required'] is False and
        scope['new_terminal_equals_old_native_endticks_required'] is False and
        scope['KEEP_UNKNOWN_recipe_not_changed'] is True and scope['native_cut_pivot_not_applied_for_KEEP_UNKNOWN'] is True and
        scope['padding_or_resampling_old_visual64_allowed'] is False and scope['failure_as_UNKNOWN_allowed'] is False and
        scope['old_success_work_modified'] is False and scope['test_GT_or_annotation_used'] is False and
        scope['new_VERIFY_timing_support_bound']=='EXACT_ORIGINAL_ELIGIBLE_ORDINAL_DOMAIN_NOT_NOMINAL_SECONDS_30' and
        scope['nominal_B0_window_seconds_limit_is_not_new_VERIFY_timing_gate'] is True and
        scope['original_CV_v2_or_input_v3_seconds_gate_modified'] is False and
        scope['new_VERIFY_visual_frames_changed'] is False and scope['new_VERIFY_actual_hi_not_clipped_or_fabricated'] is True and
        scope['new_VERIFY_still_requires']==['SAME_ORIGINAL64_ORDINAL_ORDER_AND_PIXEL_HASH',
            'ALL_ORIGINAL_SOURCE_PTS_AND_IDENTITY','ACTUAL_POSITIVE_NATIVE_TERMINAL',
            'ALL_SAMPLES_AND_NATIVE_CANDIDATE_CUTS_IN_ACTUAL_ORDINAL_SUPPORT','MAX_INPUT_TOKENS_16384',
            'FINITE_CONSERVATIVE_KEEP_UNKNOWN_DROP_GRAMMAR','ENGINEERING_FAILURE_BLOCKS_NO_UNKNOWN_FALLBACK'],
        'Frozen root scope/full first-decode gates required; no old-failure fallback or subset exception')


def old_clock(arrays,record):
    """Old PTS and terminal claims are immutable recipe evidence, not new end."""
    tick=F(arrays['raw_time_base'])
    require(tick>0 and all(type(x)is int for x in arrays['native_pts_ticks']),'Old exact integer PTS required')
    raw=[F(x)*tick for x in arrays['native_pts_ticks']]
    origin=F(arrays['raw_first_pts_ticks'])*tick
    require(raw and raw[0]==origin and all(a<b for a,b in zip(raw,raw[1:])) and
        len(raw)==arrays['n_frames']==record['n_frames'],'Old full native PTS/count/origin invalid')
    ends=arrays['native_frame_end_pts_ticks']
    if ends is None:
        terminal=record['terminal_evidence']
        require(record['clock_branch']=='CFR_LEGACY' and record.get('cfr_eligible') is True and
            terminal['kind']=='LEGACY_CFR_N_DIV_FPS' and terminal['native_packet_endpoint_proven'] is False,
            'Unknown null old terminal claim cannot be invented')
        require(type(record['fps_num'])is int and type(record['fps_den'])is int and
            record['fps_num']>0 and record['fps_den']>0,'Original positive CFR nominal rate required')
        legacy_end=F(record['n_frames']*record['fps_den'],record['fps_num'])
        provenance='OLD_CFR_N_DIV_FPS_RECIPE_REFERENCE_NOT_PHYSICAL'
    else:
        require(isinstance(ends,list) and len(ends)==len(raw) and type(ends[-1])is int,
                'Old explicit end-tick array identity required')
        legacy_end=F(ends[-1])*tick-origin
        provenance='OLD_EXPLICIT_END_TICKS_RECIPE_REFERENCE'
    points=[p-origin for p in raw]
    return dict(original_exact_pts=list(map(str,raw)),normalized_exact_pts=list(map(str,points)),
        first_original_pts_exact=str(origin),n_frames=len(raw),legacy_planned_end_exact=str(legacy_end),
        legacy_terminal_above_last_pts=legacy_end>points[-1],old_terminal_evidence=record['terminal_evidence'],
        legacy_terminal_provenance=provenance,old_clock_overwritten=False,
        legacy_end_used_for_new_sampling=False,old_terminal_reclassified=False)


def physical_plan_clock(source,packet_source,terminal,scope):
    """Revalidate existing observations; never promote an old failed gate."""
    validate_reader_scope(scope)
    old=source['old_clock'];obs=terminal['observations']
    require(packet_source['source_sha256']==source['source_sha256']==obs['actual_source_sha256'] and
        packet_source['source_stat']['bytes']==source['source_bytes']==obs['source_SHA_read_bytes'] and
        packet_source['n_frames']==old['n_frames'] and packet_source['source_path']==source['source_path'],
        'Existing source hash/bytes/path/frame-count identity changed')
    require(same_ref(packet_source['clock_array_ref'],source['original_clock_ref']),'Original clock reference changed')
    require(obs['AV_open_calls']==1 and obs['demux_calls']==1 and obs['actual_frame_decode_calls']==0 and
        obs['PyAV_version']=='17.1.0','Existing one-pass PyAV17.1.0 packet-only observations required')
    video=obs['video_stream']
    require([video['width'],video['height']]==[source['width'],source['height']],'Packet stream geometry changed')
    matches=obs['matching_packets']
    require(len(matches)==1,'Unique matching max-display packet required')
    row=matches[0];origin=F(old['first_original_pts_exact']);last=F(old['original_exact_pts'][-1])
    require(F(packet_source['original_raw_first_frame_pts_exact'])==origin and
        F(packet_source['original_raw_last_frame_pts_exact'])==last and
        F(row['raw_display_pts_exact'])==last==F(obs['max_display_packet_pts_exact']) and
        F(row['pts'])*F(row['time_base_exact'])==last,'Packet/old full-clock origin and last/max PTS differ')
    duration=F(row['duration_seconds_exact'])
    require(type(row['duration'])is int and row['duration']>0 and duration>0 and
        F(row['duration'])*F(row['time_base_exact'])==duration and type(row['size'])is int and row['size']>0 and
        isinstance(row['compressed_packet_sha256'],str) and len(row['compressed_packet_sha256'])==64 and
        row['stream_index']==video['index'],'Actual positive packet duration/payload/stream binding required')
    status=terminal['status']
    if status=='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK':
        require(terminal.get('error')=='Measured packet end differs from old explicit native end ticks' and
            packet_source['old_explicit_raw_end_exact'] is not None and
            last+duration!=F(packet_source['old_explicit_raw_end_exact']),
            'Only explicitly authorized old terminal-equality mismatch can use independent new scope')
    else:
        require(status=='PASS_MATCHING_MAX_DISPLAY_PACKET_POSITIVE_DURATION_NOT_FRAME_DECODE',
                'Identity/demux/other failed witness is never a physical fallback')
        require(F(terminal['physical_end_exact'])==last-origin+duration,'Successful old packet observation changed')
    end=last-origin+duration
    require(end>F(old['normalized_exact_pts'][-1]),'Positive packet ending required')
    return dict(original_exact_pts=old['original_exact_pts'],normalized_exact_pts=old['normalized_exact_pts'],
        first_original_pts_exact=old['first_original_pts_exact'],n_frames=old['n_frames'],
        physical_end_exact=str(end),last_packet_duration_exact=str(duration),
        packet_original_validation_status=status,old_packet_status_preserved=True,old_FAIL_promoted_to_PASS=False,
        packet_terminal_observation_ref=source['packet_terminal_observation_ref'],
        packet_registration_ref=source['packet_registration_ref'],packet_registration_source_sha256=digest(packet_source),
        reader_version=obs['PyAV_version'],video_stream_index=video['index'],stream_time_base_exact=video['time_base_exact'],
        planning_scope=READER_SCOPE,packet_only_planning=True,new_full_frame_PTS_measured=False,
        last_frame_duration_measured=False,actual_future_full_frame_decode_required=True,
        physical_endpoint_observation_kind='COMPRESSED_PACKET_AT_ORIGINAL_LAST_FRAME_PTS_PLUS_POSITIVE_DURATION',
        old_CFR_N_div_FPS_used_for_physical_end=False,old_explicit_end_required_equal=False,old_terminal_not_modified=True,
        packet_terminal_evidence=dict(reader_version=obs['PyAV_version'],last_original_pts_exact=str(last),
            last_normalized_pts_exact=str(last-origin),packet_duration_exact=str(duration),physical_end_exact=str(end),
            source_sha256=source['source_sha256'],exact_old_last_frame_pts_match=True,unique_maxdisplay_packet=True,
            observation_ref=source['packet_terminal_observation_ref'],old_validation_status=status,
            old_FAIL_promoted_to_PASS=False,new_full_frame_decode_required=True))


def ordinal_cut(points,ordinal,end):
    require(type(ordinal)is int and 0<=ordinal<=len(points),'Exact source ordinal cut required')
    return points[ordinal] if ordinal<len(points) else end


def floor64(points,lo,hi):
    first,stop=bisect_left(points,lo),bisect_left(points,hi)
    if stop-first<64:return None
    values=[first+i*(stop-first-1)//63 for i in range(64)]
    require(len(set(values))==64,'floor64 repeated a source frame')
    return values


def request_skeletons(sources):
    """Global pre-result membership: fixed original IDs, ordinals and view rule."""
    requests,leases={},{}
    for source in sources:
        sid=source['source_id'];clock=source['physical_plan_clock']
        pts=list(map(F,clock['normalized_exact_pts']));end=F(clock['physical_end_exact'])
        require(pts and pts[0]==0 and end>pts[-1] and all(a<b for a,b in zip(pts,pts[1:])),'Physical planning clock invalid')
        for window in source['windows']:
            first,stop=window['eligible_source_ordinal_bounds'];ordinals=window['original_frame_ordinals']
            require(type(first)is int and type(stop)is int and 0<=first<stop<=len(pts) and
                len(ordinals)==len(set(ordinals))==64 and all(type(i)is int and first<=i<stop for i in ordinals) and
                all(a<b for a,b in zip(ordinals,ordinals[1:])),
                'Original sample64/full eligible ordinals invalid; no replacement samples')
            lo,hi=ordinal_cut(pts,first,end),ordinal_cut(pts,stop,end)
            require(0<=lo<hi<=end and all(lo<=pts[i]<hi for i in ordinals),
                'New VERIFY exact original-ordinal domain must contain fixed original64; no invented seconds cap')
            recipe_lo,recipe_hi=map(F,window['original_window_exact'])
            for event in window['events']:
                legacy_first,legacy_last=map(F,event['original_interval_exact'])
                cuts=event['original_native_cut_source_ordinals']
                native_first,native_last=map(F,event['original_native_cut_interval_exact'])
                require(recipe_lo<=legacy_first<legacy_last<=recipe_hi and
                    first<=cuts[0]<cuts[1]<=stop and
                    native_first==ordinal_cut(pts,cuts[0],end) and native_last==ordinal_cut(pts,cuts[1],end) and
                    lo<=native_first<native_last<=hi,'Original recipe/native core identity differs')
                for side,pivot,legacy in (('start',native_first,legacy_first),('end',native_last,legacy_last)):
                    rid=event['event_id']+'.'+side;left,right=max(F(0),pivot-3),min(end,pivot+3)
                    selected=floor64(pts,left,right)
                    row=dict(event,request_id=rid,source_id=sid,kind='ENDPOINT',side=side,
                        dual_coordinate_schema=SCHEMA,
                        window_start=str(left),window_end=str(right),original_endpoint_exact=str(legacy),
                        legacy_recipe_original_endpoint_exact=str(legacy),
                        original_native_cut_endpoint_exact=str(pivot),refiner_native_cut_endpoint_exact=str(pivot),
                        original_native_cut_endpoint_ordinal=cuts[0] if side=='start' else cuts[1],
                        execution='MODEL' if selected is not None else 'STRUCTURAL_UNKNOWN_NO64',
                        source_frame_ordinals=selected,sample_exact_pts=[str(pts[i]) for i in selected] if selected else None,
                        endpoint_coordinates='LEGACY_RECIPE_AND_NEW_READER_NATIVE_CUT',
                        consumer_resolution_adapter='tp_contract.resolve_endpoint_result')
                    if selected is None:
                        row['structural_endpoint_result']=dict(request_id=rid,event_id=event['event_id'],side=side,
                            raw_decision={'decision':'UNKNOWN'},applied_decision='UNKNOWN_INSUFFICIENT_DISTINCT_NATIVE_FRAMES',
                            original_endpoint_exact=str(legacy),endpoint_exact=str(legacy),
                            legacy_recipe_original_endpoint_exact=str(legacy),
                            original_native_cut_endpoint_exact=str(pivot),refiner_native_cut_endpoint_exact=str(pivot),
                            native_endpoint_exact=str(pivot),displacement_exact='0',changed=False,
                            actual_model_call=False,declared_before_model=True)
                    require(rid not in requests,'Duplicate fixed event request')
                    requests[rid]=row
                rid=event['event_id']+'.verify'
                require(rid not in requests,'Duplicate fixed verification request')
                requests[rid]=dict(event,request_id=rid,source_id=sid,kind='VERIFY',execution='MODEL',
                    dual_coordinate_schema=SCHEMA,
                    window_start=str(lo),window_end=str(hi),new_verify_window_exact=[str(lo),str(hi)],
                    source_frame_ordinals=ordinals,sample_exact_pts=[str(pts[i]) for i in ordinals],
                    verify_original_frame_ordinals=ordinals,verify_eligible_source_ordinal_bounds=[first,stop],
                    original_frame_pixel_sha256=window['original_frame_pixel_sha256'],
                    verify_view_kind='NEW_VERIFY_TIMING_CONTEXT_ORIGINAL64_PIXELS',
                    original_coarse_input_reused=False,original_coarse_pixels_ordinals_preserved=True,
                    new_processor_and_input_proof_required=True,consumer_resolution_adapter='tp_contract.resolve_verify_result')
    for rid,row in requests.items():
        if row['execution']!='MODEL':continue
        key=digest(dict(source_id=row['source_id'],ordinals=row['source_frame_ordinals'],pts=row['sample_exact_pts']))
        lease_id='RGB_'+key[:40];row['lease_id']=lease_id
        lease=leases.setdefault(lease_id,dict(rgb_relative='staging/rgb/'+lease_id+'.npz',consumers=[],
            source_id=row['source_id'],source_frame_ordinals=row['source_frame_ordinals'],sample_exact_pts=row['sample_exact_pts']))
        lease['consumers'].append(rid)
    nominal=sum(len(w['events'])*3 for s in sources for w in s['windows'])
    require(len(requests)==nominal,'Complete fixed request denominator changed')
    return dict(schema=SCHEMA,requests=list(requests.values()),RGB_groups=leases,
        consumers=[rid for rid,row in requests.items() if row['execution']=='MODEL'],
        structural_unknown_requests=[rid for rid,row in requests.items() if row['execution']!='MODEL'],
        nominal_requests=nominal,request_membership_can_change_with_results=False,
        batch_size_may_change_for_capacity_only=True,physical_plan_requires_first_new_frame_decode_gate=True,
        new_model_calls=0,new_media_decodes=0,new_processor_encodes=0)


def measured_clock(source,raw,durations,geometry,stream):
    require(raw and len(durations)==len(raw) and durations[-1] is not None and durations[-1]>0,
        'New positive last Frame.duration unavailable; no packet/nominal substitution')
    origin=raw[0];points=[p-origin for p in raw];end=points[-1]+durations[-1]
    clock=dict(source_id=source['source_id'],source_sha256=source['source_sha256'],source_path=source['source_path'],
        original_exact_pts=list(map(str,raw)),normalized_exact_pts=list(map(str,points)),first_original_pts_exact=str(origin),
        n_frames=len(raw),physical_end_exact=str(end),last_frame_duration_exact=str(durations[-1]),
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
            last_normalized_pts_exact=str(points[-1]),last_frame_duration_exact=str(durations[-1]),
            exactly_matches_packet_duration=True,packet_terminal_observation_ref=source['packet_terminal_observation_ref']),
        native_duration_by_ordinal={str(i):str(v) if v is not None else None for i,v in enumerate(durations)},
        measured_geometry=list(geometry),video_stream_index=stream['index'],stream_time_base_exact=stream['time_base'],
        measured_average_rate_exact=stream['average_rate'],reader_version=stream['reader_version'],
        packet_terminal_observation_ref=source['packet_terminal_observation_ref'],
        packet_registration_ref=source['packet_registration_ref'],
        packet_terminal_evidence=source['physical_plan_clock']['packet_terminal_evidence'],
        first_RGB_decoder_terminal_witness=dict(status='ACTUAL_FRAME_DURATION_REQUIRES_EXACT_PACKET_COMPARISON',
            reader_version=stream['reader_version'],last_original_pts_exact=str(raw[-1]),
            last_normalized_pts_exact=str(points[-1]),last_frame_duration_exact=str(durations[-1]),
            physical_end_exact=str(end),packet_terminal_observation_ref=source['packet_terminal_observation_ref']),
        new_native_RGB_materialization_decodes=1,
        old_clock_not_overwritten=True,nominal_fps_or_container_duration_used_for_end=False,audio_observed=False)
    compare_clock(source,clock)
    clock['first_RGB_decoder_terminal_witness']['status']='PASS_ACTUAL_FULL_PTS_AND_FRAME_DURATION_EXACT_PACKET_EQUALITY'
    return clock


def compare_clock(source,clock):
    old=source['old_clock'];physical=source['physical_plan_clock']
    require(clock['original_exact_pts']==old['original_exact_pts'] and
        clock['normalized_exact_pts']==old['normalized_exact_pts'] and
        clock['first_original_pts_exact']==old['first_original_pts_exact'] and clock['n_frames']==old['n_frames'] and
        clock['measured_geometry']==[source['width'],source['height']],'New full frame PTS/count/origin/geometry differs; STOP')
    require(clock['reader_version']==physical['reader_version'] and
        clock['video_stream_index']==physical['video_stream_index'] and
        F(clock['stream_time_base_exact'])==F(physical['stream_time_base_exact']) and
        F(clock['last_frame_duration_exact'])>0 and
        F(clock['last_frame_duration_exact'])==F(physical['last_packet_duration_exact']) and
        F(clock['physical_end_exact'])==F(physical['physical_end_exact']),
        'New positive Frame.duration/reader/stream/end differs from packet witness; STOP without epsilon')


def native_boundary_request(request):
    require(request['kind']=='ENDPOINT','Endpoint dual adapter only')
    require(request['original_endpoint_exact']==request['legacy_recipe_original_endpoint_exact'] and
        request['original_native_cut_endpoint_exact']==request['refiner_native_cut_endpoint_exact'],
        'Dual endpoint coordinate aliases changed')
    return dict(request,original_interval_exact=request['original_native_cut_interval_exact'],
        original_endpoint_exact=request['original_native_cut_endpoint_exact'])


def resolve_endpoint_result(decision,request,boundary):
    """Only a genuinely moved REFINE cut replaces legacy recipe seconds."""
    native=boundary.resolve_endpoint(decision,native_boundary_request(request))
    legacy=F(request['original_endpoint_exact']);old_native=F(request['original_native_cut_endpoint_exact'])
    new_native=F(native['endpoint_exact'])
    moved=native['applied_decision']=='REFINE' and new_native!=old_native
    applied=new_native if moved else legacy
    return dict(native,original_endpoint_exact=str(legacy),endpoint_exact=str(applied),
        legacy_recipe_original_endpoint_exact=str(legacy),displacement_exact=str(applied-legacy),changed=applied!=legacy,
        original_native_cut_endpoint_exact=str(old_native),refiner_native_cut_endpoint_exact=str(old_native),
        native_endpoint_exact=str(new_native),native_displacement_exact=str(new_native-old_native),
        native_cut_actually_moved=moved,original_recipe_preserved=not moved,dual_coordinate_schema=SCHEMA)


def resolve_verify_result(text,request,verify,*,execution_status):
    value=verify.resolve(text,dict(request,original_interval_exact=request['original_native_cut_interval_exact']),
        execution_status=execution_status)
    legacy=request['original_interval_exact']
    value.update(original_interval_exact=legacy,retained_interval_exact=legacy if value['decision']!='DROP' else None,
        original_native_cut_interval_exact=request['original_native_cut_interval_exact'],
        verify_view_kind=request['verify_view_kind'],dual_coordinate_schema=SCHEMA)
    return value


def verify_prompt(request,verify):
    original='The complete original silent video window is shown with its original sampled frames. '
    prompt=verify.prompt(request)
    require(original in prompt,'Frozen VERIFY wording changed; explicit new-view prompt adapter required')
    return prompt.replace(original,'The original 64 silent visual frames are shown without replacing any sampled frame. '
        'Time labels use the newly registered reader-native window over the original eligible ordinal range. ',1)


def verify_request(event,meta):
    """Independent registered ordinal-support validator; never fake old cv.request hi."""
    for value in (event['event_id'],meta['case_id']):
        require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',value),
            'Stable safe original candidate/case identity required')
    points=list(map(exact,meta['all_source_exact_pts']));end=exact(meta['physical_end_exact'])
    require(points and points[0]==0 and all(a<b for a,b in zip(points,points[1:])) and
        type(meta['source_total_frames'])is int and meta['source_total_frames']==len(points) and end>points[-1],
        'Complete real native source PTS/count/positive terminal required')
    first_ordinal,stop_ordinal=meta['verify_eligible_source_ordinal_bounds']
    require(type(first_ordinal)is int and type(stop_ordinal)is int and
        0<=first_ordinal<stop_ordinal<=len(points),'Frozen original full eligible ordinal support required')
    lo=ordinal_cut(points,first_ordinal,end);hi=ordinal_cut(points,stop_ordinal,end)
    require(exact(meta['window_start'])==lo and exact(meta['window_end'])==hi and
        list(map(exact,meta['new_verify_window_exact']))==[lo,hi],
        'VERIFY context must equal the true original eligible support; no fake hi, clip or expansion')
    ordinals=meta['source_frame_ordinals'];samples=list(map(exact,meta['sample_exact_pts']))
    require(ordinals==meta['verify_original_frame_ordinals'] and len(ordinals)==len(set(ordinals))==64 and
        all(type(i)is int and first_ordinal<=i<stop_ordinal for i in ordinals) and
        all(a<b for a,b in zip(ordinals,ordinals[1:])) and len(samples)==64 and
        samples==[points[i] for i in ordinals] and all(lo<=p<hi for p in samples) and
        meta['audio_observed'] is False and meta['reference_available_to_inference'] is False,
        'Exact unchanged original64 order/PTS and silent reference-free evidence required')
    cuts=event['original_native_cut_source_ordinals'];a,b=map(exact,event['original_interval_exact'])
    require(len(cuts)==2 and all(type(i)is int for i in cuts) and
        first_ordinal<=cuts[0]<cuts[1]<=stop_ordinal and
        [a,b]==[ordinal_cut(points,cuts[0],end),ordinal_cut(points,cuts[1],end)] and
        [a,b]==list(map(exact,event['original_native_cut_interval_exact'])) and lo<=a<b<=hi,
        'Existing native candidate cuts must bind their original accepted core ordinals inside actual support')
    observed=sum(a<=point<b for point in samples)
    return dict(schema='CANDIDATE_VERIFY_V4_ORIGINAL_ORDINAL_CONTEXT',request_id=event['event_id']+'.verify',
        event_id=event['event_id'],original_case_id=meta['case_id'],original_segment_index=event['original_segment_index'],
        source_name=meta['source_name'],source_sha256=meta['source_sha256'],original_interval_exact=[str(a),str(b)],
        original_window_start_exact=str(lo),original_window_end_exact=str(hi),new_verify_window_exact=[str(lo),str(hi)],
        verify_eligible_source_ordinal_bounds=[first_ordinal,stop_ordinal],verify_original_frame_ordinals=ordinals,
        candidate_window_local_exact=[str(a-lo),str(b-lo)],candidate_visible_sample_count=observed,
        allowed_decisions=['KEEP','UNKNOWN','DROP'] if observed else ['UNKNOWN'],
        uncertainty_gate='NONE' if observed else 'NO_SHOWN_SAMPLE_IN_CANDIDATE',
        source_frame_ordinals=ordinals,sample_exact_pts=list(map(str,samples)),reference_labels_read=False,audio_observed=False,
        action_completion_required=False,silent_lecture_or_static_landscape_is_ordinary=False,new_candidate_created=False,
        timing_scope='EXACT_ORIGINAL_ELIGIBLE_ORDINAL_DOMAIN_NOT_NOMINAL_SECONDS_30',
        nominal_seconds_gate_used=False,old_CV_v2_request_called=False)


def materialized_request(source,skeleton,clock,boundary,continuity,verify,durations):
    base=dict(skeleton,source_name=source['source_id'],source_group='Production:'+source['source_id'],
        source_path=source['source_path'],source_sha256=source['source_sha256'],source_bytes=source['source_bytes'],
        width=source['width'],height=source['height'],fps_num=source['fps_num'],fps_den=source['fps_den'],
        source_total_frames=clock['n_frames'],all_source_exact_pts=clock['normalized_exact_pts'],
        original_clock_origin_exact=clock['first_original_pts_exact'],audio_observed=False,
        reference_available_to_inference=False,legacy_end_used_for_input_timing=False,
        physical_end_exact=clock['physical_end_exact'],
        new_reader_native_terminal_scope=READER_SCOPE,packet_terminal_observation_ref=source['packet_terminal_observation_ref'])
    if skeleton['kind']=='ENDPOINT':
        planned=boundary.plan_endpoint(native_boundary_request(base),skeleton['side'],clock)
        require(planned['actionable'] is True and planned['source_frame_ordinals']==skeleton['source_frame_ordinals'] and
            planned['window_start']==skeleton['window_start'] and planned['window_end']==skeleton['window_end'] and
            F(planned['original_endpoint_exact'])==F(skeleton['original_native_cut_endpoint_exact']),
            'Measured endpoint differs from globally frozen native-cut plan')
        base.update(planned)
        base['original_interval_exact']=skeleton['original_interval_exact']
        base['original_endpoint_exact']=skeleton['original_endpoint_exact']
        native=native_boundary_request(base)
        base['continuity_by_sample'],base['original_endpoint_continuity_verified']=continuity(native,clock,durations)
        base['prompt']=boundary.prompt(native)
        base['finite_response_strings']=list(boundary.response_strings(native))
    else:
        req=verify_request(dict(base,original_interval_exact=base['original_native_cut_interval_exact']),
            dict(base,case_id=base['original_case_id']))
        base.update(req)
        base['original_interval_exact']=skeleton['original_interval_exact']
        base['original_window_start_exact']=skeleton['original_window_exact'][0]
        base['original_window_end_exact']=skeleton['original_window_exact'][1]
        base['request_id']=skeleton['request_id']
        base['prompt']=verify_prompt(base,verify)
        base['finite_response_strings']=list(verify.responses(base))
    return base
