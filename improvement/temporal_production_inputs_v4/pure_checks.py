"""Only new V4 ordinal timing cases; no V3 20-case or color suite rerun."""
import copy
from fractions import Fraction as F
from tp_contract import (SCHEMA,validate_reader_scope,request_skeletons,materialized_request,
    verify_request,resolve_verify_result,require)


def run(old_v3,verify,scope):
    checks=[]
    def reject(call,name):
        try:call()
        except (ValueError,KeyError):checks.append(name);return
        raise AssertionError('Expected rejection: '+name)
    validate_reader_scope(scope)
    pts=[F(i,2) for i in range(64)];end=F(32);ordinals=list(range(64));pixels=['1'*64]*64
    event=dict(event_id='SYN_SUPPORT_E00',original_case_id='SYN_SUPPORT_W000',original_segment_index=0,
        original_interval_exact=['19/10','249/10'],original_window_exact=['0','30'],
        original_window_start_exact='0',original_window_end_exact='30',
        original_native_cut_interval_exact=['2','25'],original_native_cut_source_ordinals=[4,50],
        accepted_window_sha256='2'*64)
    clock=dict(original_exact_pts=list(map(str,pts)),normalized_exact_pts=list(map(str,pts)),
        first_original_pts_exact='0',n_frames=64,physical_end_exact='32',
        last_frame_duration_exact='1/2',native_duration_by_ordinal={str(i):'1/2' for i in ordinals})
    source=dict(source_id='SYN_SUPPORT',source_sha256='3'*64,source_path='/synthetic/not-opened.mp4',
        source_bytes=1,width=8,height=8,fps_num=32,fps_den=15,physical_plan_clock=clock,
        packet_terminal_observation_ref={'path':'/synthetic/terminal.json','sha256':'4'*64},
        windows=[dict(original_case_id=event['original_case_id'],original_window_exact=['0','30'],
            original_frame_ordinals=ordinals,original_frame_pixel_sha256=pixels,
            eligible_source_ordinal_bounds=[0,64],events=[event])])
    before=copy.deepcopy(source)
    frozen=request_skeletons([source])
    row=next(x for x in frozen['requests'] if x['kind']=='VERIFY')
    require(row['new_verify_window_exact']==['0','32'] and row['source_frame_ordinals']==ordinals and
        row['original_frame_pixel_sha256']==pixels and source==before and
        row['verify_original_frame_ordinals']==ordinals and row['original_coarse_input_reused'] is False,
        'True >30 ordinal context must retain original64/pixel/order and old recipe')
    meta=materialized_request(source,row,clock,None,None,verify,clock['native_duration_by_ordinal'])
    require(meta['new_verify_window_exact']==['0','32'] and meta['window_end']=='32' and
        meta['original_interval_exact']==event['original_interval_exact'] and
        meta['candidate_window_local_exact']==['2','25'] and
        meta['candidate_visible_sample_count']==46 and
        meta['nominal_seconds_gate_used'] is False and meta['old_CV_v2_request_called'] is False and
        'newly registered reader-native window' in meta['prompt'],
        'New request must be honestly validated on full physical support, not fake old cv.request input')
    checks.append('true32s_original_eligible64_support_accepted_same_pixels_ordinals_order')
    native_event=dict(meta,original_interval_exact=meta['original_native_cut_interval_exact'])
    native_meta=dict(meta,case_id=meta['original_case_id'])
    reject(lambda:verify.request(native_event,native_meta),'old_CV_v2_seconds_validator_remains_unchanged_rejects32')
    reject(lambda:old_v3.request_skeletons([source]),'old_input_v3_seconds_validator_remains_unchanged_rejects32')
    for hi,label in (('30','fake_clipped_hi'),('33','fake_expanded_hi')):
        bad=copy.deepcopy(native_meta);bad['window_end']=hi;bad['new_verify_window_exact']=['0',hi]
        reject(lambda b=bad:verify_request(native_event,b),label+'_rejected_against_original_ordinal_support')
    bad=copy.deepcopy(native_meta);bad['sample_exact_pts'][-1]='157/5'
    reject(lambda:verify_request(native_event,bad),'fake_sample_PTS_rejected_same_original64')
    bad=copy.deepcopy(native_meta);bad['source_frame_ordinals']=list(reversed(ordinals))
    reject(lambda:verify_request(native_event,bad),'changed_original64_order_rejected')
    bad=copy.deepcopy(native_meta);bad['physical_end_exact']='31'
    reject(lambda:verify_request(native_event,bad),'non_positive_actual_terminal_rejected_no_fake_hi')
    for body in ('{"decision":"KEEP"}','{"decision":"UNKNOWN"}'):
        result=resolve_verify_result(body,meta,verify,execution_status='MODEL_OK')
        require(result['retained_interval_exact']==event['original_interval_exact'] and
            result['dual_coordinate_schema']==SCHEMA,'Conservative new timing results changed old recipe')
    result=resolve_verify_result('{"decision":"DROP"}',meta,verify,execution_status='MODEL_OK')
    require(result['retained_interval_exact'] is None and result['original_interval_exact']==event['original_interval_exact'],
        'Finite DROP grammar must keep original recipe identity')
    checks.append('new_true_support_finite_KEEP_UNKNOWN_DROP_resolve_preserves_recipe')
    return dict(status='PASS_INCREMENTAL_V4_TRUE_ELIGIBLE_ORDINAL_CONTEXT_ONLY',
        checks=checks,synthetic_context_seconds_exact='32',original_visual_ordinals=64,original_pixel_hashes=64,
        real_sources_read=0,real_source_decodes=0,real_processor_calls=0,real_model_calls=0,
        actual_production_projection_calls=0,old_V3_20_case_suite_repeated=False,old_color5_suite_repeated=False)
