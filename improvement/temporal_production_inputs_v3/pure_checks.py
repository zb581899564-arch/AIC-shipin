"""Incremental synthetic V3 math gates only; no source/processor/storage calls."""
import copy
from fractions import Fraction as F
from tp_contract import (SCHEMA,READER_SCOPE,compare_clock,digest,floor64,measured_clock,old_clock,
    physical_plan_clock,request_skeletons,materialized_request,resolve_endpoint_result,resolve_verify_result,require)


def run(boundary,verify,continuity,scope):
    checked=[];preserved=0
    def rejects(call,label):
        try:call()
        except (ValueError,KeyError):checked.append(label);return
        raise AssertionError('Expected STOP: '+label)
    def fixture(sid,period,tick,n,old_duration_ticks,new_duration_ticks,failed):
        origin=F(17,3);raw=[origin+i*period for i in range(n)]
        ticks=[int(p/tick) for p in raw]
        require(all(F(x)*tick==p for x,p in zip(ticks,raw)),'Synthetic exact ticks')
        arrays=dict(raw_time_base=str(tick),raw_first_pts_ticks=ticks[0],n_frames=n,native_pts_ticks=ticks,
            native_frame_end_pts_ticks=[x+old_duration_ticks for x in ticks])
        record=dict(n_frames=n,terminal_evidence={'kind':'NATIVE_LAST_FRAME_PACKET_DURATION'},clock_branch='NATIVE_PTS')
        ref=dict(path='/synthetic/clock.json',sha256='a'*64)
        source=dict(source_id=sid,video_id=sid,source_sha256='b'*64,source_path='/synthetic/not-opened.mp4',
            source_bytes=123,width=8,height=8,fps_num=period.denominator,fps_den=period.numerator,
            original_clock_ref=ref,old_clock=old_clock(arrays,record),packet_terminal_observation_ref=dict(
                path='/synthetic/terminal.json',sha256='c'*64),packet_registration_ref=dict(
                path='/synthetic/registration.json',sha256='d'*64))
        ps=dict(source_sha256=source['source_sha256'],source_path=source['source_path'],source_stat={'bytes':123},
            n_frames=n,clock_array_ref=dict(ref,bytes=77),original_raw_first_frame_pts_exact=str(raw[0]),
            original_raw_last_frame_pts_exact=str(raw[-1]),old_explicit_raw_end_exact=str(raw[-1]+old_duration_ticks*tick))
        row=dict(pts=ticks[-1],duration=new_duration_ticks,time_base_exact=str(tick),size=16,stream_index=0,
            raw_display_pts_exact=str(raw[-1]),duration_seconds_exact=str(new_duration_ticks*tick),compressed_packet_sha256='e'*64)
        obs=dict(actual_source_sha256=source['source_sha256'],source_SHA_read_bytes=123,AV_open_calls=1,demux_calls=1,
            actual_frame_decode_calls=0,PyAV_version='17.1.0',video_stream=dict(index=0,time_base_exact=str(tick),width=8,height=8),
            matching_packets=[row],max_display_packet_pts_exact=str(raw[-1]))
        terminal=dict(status='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK' if failed else
            'PASS_MATCHING_MAX_DISPLAY_PACKET_POSITIVE_DURATION_NOT_FRAME_DECODE',observations=obs)
        if failed:terminal['error']='Measured packet end differs from old explicit native end ticks'
        else:terminal['physical_end_exact']=str(raw[-1]-origin+new_duration_ticks*tick)
        source['physical_plan_clock']=physical_plan_clock(source,ps,terminal,scope)
        pts=[p-origin for p in raw];end=F(source['physical_plan_clock']['physical_end_exact'])
        first,stop=(30,270) if n==300 else (20,60)
        epsilon_named_only_for_fixture=F(1,100000)  # synthetic fractional recipe; never tolerance in any gate
        interval=[str(pts[first]-epsilon_named_only_for_fixture),str(pts[stop]-epsilon_named_only_for_fixture)]
        event=dict(event_id=sid+'_E00',original_case_id=sid+'_W000',original_segment_index=0,
            original_interval_exact=interval,original_window_exact=['0',str(end+F(1,10**15))],
            original_window_start_exact='0',original_window_end_exact=str(end+F(1,10**15)),
            original_native_cut_interval_exact=list(map(str,(pts[first],pts[stop]))),
            original_native_cut_source_ordinals=[first,stop],accepted_window_sha256='f'*64)
        source['windows']=[dict(original_case_id=sid+'_W000',original_window_exact=event['original_window_exact'],
            original_frame_ordinals=floor64(pts,F(0),end),eligible_source_ordinal_bounds=[0,n],
            original_frame_pixel_sha256=['1'*64]*64,events=[event])]
        durations=[period]*n;durations[-1]=new_duration_ticks*tick
        stream=dict(index=0,time_base=str(tick),average_rate=str(1/period),reader_version='17.1.0')
        return source,ps,terminal,raw,durations,stream
    fixtures=[]
    for i in range(5):
        period,tick,old,new=(F(1,30),F(1,15360),256,512) if i<3 else (F(100,2997),F(1,11988),200,400)
        values=fixture('SYN_'+str(i),period,tick,300,old,new,True)
        source,ps,terminal,raw,dur,stream=values;before=digest(terminal)
        measured=measured_clock(source,raw,dur,[8,8],stream)
        require(source['physical_plan_clock']['packet_original_validation_status'].startswith('FAIL_') and
            source['physical_plan_clock']['old_FAIL_promoted_to_PASS'] is False and digest(terminal)==before and
            measured['packet_terminal_evidence']['old_validation_status']==terminal['status'],
            'New reader scope changed an original failed terminal gate')
        fixtures.append((values,measured));preserved+=1
    checked.append('five_old_equality_FAILs_preserved_reader_scope_is_separate')
    values,clock=fixtures[0];source,ps,terminal,raw,dur,stream=values
    rejects(lambda:physical_plan_clock(source,ps,dict(terminal,error='Unrelated demux failure'),scope),
        'non_equality_packet_failure_blocks_no_fallback')
    bad=copy.deepcopy(terminal);bad['observations']['matching_packets'].append(bad['observations']['matching_packets'][0])
    rejects(lambda:physical_plan_clock(source,ps,bad,scope),'non_unique_packet_blocks')
    bad=copy.deepcopy(terminal);bad['observations']['max_display_packet_pts_exact']='999'
    rejects(lambda:physical_plan_clock(source,ps,bad,scope),'non_max_last_packet_blocks')
    bad=copy.deepcopy(terminal);bad['observations']['actual_source_sha256']='2'*64
    rejects(lambda:physical_plan_clock(source,ps,bad,scope),'source_SHA_mismatch_blocks')
    rejects(lambda:measured_clock(source,raw,dur[:-1]+[None],[8,8],stream),'missing_Frame_duration_blocks')
    rejects(lambda:measured_clock(source,raw,dur[:-1]+[dur[-1]/2],[8,8],stream),
        'Frame_duration_must_exactly_equal_packet_without_epsilon')
    badraw=list(raw);badraw[10]+=F(1,100000)
    rejects(lambda:measured_clock(source,badraw,dur,[8,8],stream),'full_PTS_mismatch_blocks')
    rejects(lambda:measured_clock(source,raw,dur,[9,8],stream),'geometry_mismatch_blocks')
    rejects(lambda:measured_clock(source,raw[1:],dur[1:],[8,8],stream),'origin_and_count_mismatch_blocks')
    short=fixture('SYN_SHORT',F(1,10),F(1,30),100,3,3,False)[0]
    frozen=request_skeletons([source,short])
    require(frozen['nominal_requests']==6 and len(frozen['consumers'])==4 and len(frozen['structural_unknown_requests'])==2,
        'Nominal/actionable/structural partition differs')
    for row in frozen['requests']:
        if row['execution']!='MODEL':
            result=row['structural_endpoint_result']
            require(result['endpoint_exact']==row['original_endpoint_exact'] and result['actual_model_call'] is False and
                result['native_endpoint_exact']==row['original_native_cut_endpoint_exact'],'Structural skip leaked native cut')
    checked.append('short_context_full_nominal_partition_preserves_recipe_no_fakecall')
    verify_row=next(row for row in frozen['requests'] if row['source_id']==source['source_id'] and row['kind']=='VERIFY')
    require(F(source['windows'][0]['original_window_exact'][1])>F(clock['physical_end_exact']) and
        F(verify_row['window_end'])==F(clock['physical_end_exact']) and
        verify_row['source_frame_ordinals']==source['windows'][0]['original_frame_ordinals'] and
        verify_row['original_coarse_input_reused'] is False,
        'Old float/recipe end must not define physical new VERIFY or silently resample')
    checked.append('old_float_recipe_over_end_kept_new_VERIFY_domain_legal_same_original64')
    bad=copy.deepcopy(source);bad['windows'][0]['original_frame_ordinals'][0]=-1
    rejects(lambda:request_skeletons([bad]),'legacy64_outside_eligible_ordinals_blocks_no_replacement')
    bad=copy.deepcopy(source);bad['physical_plan_clock']['physical_end_exact']='100'
    rejects(lambda:request_skeletons([bad]),'new_VERIFY_over30_blocks_without_clipping')
    arrays=dict(raw_time_base='1/24',raw_first_pts_ticks=0,n_frames=250,
        native_pts_ticks=list(range(250)),native_frame_end_pts_ticks=None)
    cfr=old_clock(arrays,dict(n_frames=250,fps_num=25,fps_den=1,clock_branch='CFR_LEGACY',cfr_eligible=True,
        terminal_evidence={'kind':'LEGACY_CFR_N_DIV_FPS','native_packet_endpoint_proven':False}))
    require(cfr['legacy_terminal_above_last_pts'] is False and cfr['legacy_end_used_for_new_sampling'] is False,
        'Old nominal end not above last PTS must stay a recipe claim, never new physical end')
    checked.append('CFR_nominal_invalid_physical_end_not_used_for_new_views')
    for row in frozen['requests']:
        if row['source_id']!=source['source_id'] or row['execution']!='MODEL':continue
        req=materialized_request(source,row,clock,boundary,continuity,verify,clock['native_duration_by_ordinal'])
        require(req['dual_coordinate_schema']==SCHEMA and req['original_interval_exact']==row['original_interval_exact'],
            'Stored original recipe coordinate overwritten')
        if req['kind']=='VERIFY':
            require('newly registered reader-native window' in req['prompt'] and
                req['source_frame_ordinals']==source['windows'][0]['original_frame_ordinals'],
                'New VERIFY context falsely claimed old-input reuse')
            for text in ('{"decision":"KEEP"}','{"decision":"UNKNOWN"}'):
                result=resolve_verify_result(text,req,verify,execution_status='MODEL_OK')
                require(result['retained_interval_exact']==row['original_interval_exact'],'VERIFY KEEP/UNKNOWN changed recipe')
            rejects(lambda:resolve_verify_result('{"decision":"UNKNOWN"}',req,verify,execution_status='INFERENCE_FAILURE'),
                'VERIFY_bad_model_must_block_not_UNKNOWN')
        else:
            for decision in ({'decision':'KEEP'},{'decision':'UNKNOWN'}):
                result=resolve_endpoint_result(decision,req,boundary)
                require(result['endpoint_exact']==row['original_endpoint_exact'] and result['original_recipe_preserved'] and
                    not result['changed'],'KEEP/UNKNOWN leaked native-cut pivot')
            # Force only pure geometric continuity flags; no semantic success is claimed.
            req['original_endpoint_continuity_verified']=True
            req['continuity_by_sample']={str(i):True for i in req['allowed_sample_indices']}
            chosen=next(i for i in req['allowed_sample_indices'] if i not in (0,63) and
                req['selected_cut_has_two_sided_visible_samples'][str(i)] and
                F(req['sample_boundary_exact'][i])!=F(req['original_native_cut_endpoint_exact']))
            result=resolve_endpoint_result({'decision':'REFINE','sample_index':chosen},req,boundary)
            require(result['native_cut_actually_moved'] and result['endpoint_exact']==req['sample_boundary_exact'][chosen],
                'True REFINE did not apply exact native cut')
            rejects(lambda:resolve_endpoint_result({'decision':'FAKE'},req,boundary),'bad_endpoint_schema_blocks')
    checked.append('native_cut_prompt_KEEP_UNKNOWN_preserve_recipe_REFINE_only_moves_native')
    event=source['windows'][0]['events'][0];pts=list(map(F,clock['normalized_exact_pts']))
    def padded_mask(interval):
        a,b=map(F,interval);lo,hi=map(F,event['original_window_exact'])
        left=max(lo,a-F(3,4));right=min(hi,b+F(1,2)+(F(1,4) if b-a>=8 else 0))
        return {i for i,p in enumerate(pts) if left<=p<right}
    applied=[]
    for side in ('start','end'):
        row=next(r for r in frozen['requests'] if r['source_id']==source['source_id'] and r.get('side')==side)
        req=materialized_request(source,row,clock,boundary,continuity,verify,clock['native_duration_by_ordinal'])
        applied.append(resolve_endpoint_result({'decision':'UNKNOWN'},req,boundary)['endpoint_exact'])
    require(padded_mask(applied)==padded_mask(event['original_interval_exact']),'Native-cut UNKNOWN changed synthetic D8 frames')
    checked.append('synthetic_D8_KEEP_UNKNOWN_frame_mask_exactly_unchanged')
    return dict(status='PASS_INCREMENTAL_V3_DUAL_COORDINATES_SYNTHETIC_ONLY_NOT_PRODUCTION_ADMISSION',
        checks=checked,synthetic_old_failed_terminals_preserved=preserved,
        real_source_or_packet_proofs_read=0,real_source_decodes=0,real_processor_calls=0,real_model_calls=0,
        actual_GPU_calls=0,actual_production_projection_calls=0,old_successful_checks_repeated=0)
