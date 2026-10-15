"""Synthetic contracts/CPU-storage checks only; no production IO or processor."""
from fractions import Fraction as F
import copy

from tp_contract import compare_clock,floor64,measured_clock,old_clock,request_skeletons,require
from tp_device import signature_any_device,transfer_exact


def run(boundary,verify,continuity,cache_signature,validate_RGB_plan):
    from tp_contract import materialized_request
    checked=[]
    def expect_failure(call,label):
        try:call()
        except (ValueError,KeyError):checked.append(label);return
        raise AssertionError('Expected rejection: '+label)
    def source(sid,fps,n,interval):
        pts=[F(i,fps) for i in range(n)];origin=F(17,3);end=F(n,fps)
        clock=dict(original_exact_pts=[str(p+origin) for p in pts],normalized_exact_pts=list(map(str,pts)),
            first_original_pts_exact=str(origin),planned_physical_end_exact=str(end),n_frames=n,
            old_terminal_evidence={'kind':'LEGACY_CFR_N_DIV_FPS'},native_terminal_reverified=False,
            old_CFR_end_is_measured_duration=False)
        window=dict(original_case_id=sid+'_W000',original_window_exact=['0',str(end)],
            original_frame_ordinals=floor64(pts,F(0),end),original_frame_pixel_sha256=['a'*64]*64,
            events=[dict(event_id=sid+'_W000_E00',original_case_id=sid+'_W000',original_segment_index=0,
                original_interval_exact=list(map(str,interval)),accepted_window_sha256='b'*64)])
        return dict(source_id=sid,source_sha256='c'*64,source_path='/synthetic/not-opened.mp4',width=8,height=8,
            source_bytes=1,fps_num=fps,fps_den=1,old_clock=clock,windows=[window])
    a=source('SYN_A',25,250,[F(0),F(4)]);b=source('SYN_B',10,80,[F(0),F(4)])
    arrays=dict(raw_time_base='1/75',raw_first_pts_ticks=425,n_frames=250,
        native_pts_ticks=[425+3*i for i in range(250)],native_frame_end_pts_ticks=[428+3*i for i in range(250)])
    legacy=old_clock(arrays,dict(n_frames=250,terminal_evidence={'kind':'LEGACY_CFR_N_DIV_FPS'}))
    require(legacy['planned_physical_end_exact']=='10' and legacy['native_terminal_reverified'] is False and
            legacy['old_CFR_end_is_measured_duration'] is False,'Old CFR terminal falsely certified as native duration')
    checked.append('legacy_CFR_end_remains_only_planning_witness')
    frozen=request_skeletons([a,b])
    require(len(frozen['requests'])==6 and len(frozen['consumers'])==4 and len(frozen['structural_unknown_requests'])==2,
            'Logical requests and structural no64 denominator changed')
    require(all(row['source_frame_ordinals'] is None and row['structural_endpoint_result']['endpoint_exact']==row['original_endpoint_exact']
        for row in frozen['requests'] if row['execution']!='MODEL'),'No64 silently expanded or called a model')
    checked.append('structural_no64_preserves_endpoint_without_expand_or_call')
    policy=dict(mode='PRODUCTION',frozen_RGB_leases={key:dict(rgb_relative=row['rgb_relative'],consumers=row['consumers'])
        for key,row in frozen['RGB_groups'].items()})
    validate_RGB_plan(frozen['consumers'],policy);checked.append('complete_exact_one_RGB_lease_per_consumer')
    duplicate=copy.deepcopy(policy);next(iter(duplicate['frozen_RGB_leases'].values()))['consumers'].append(frozen['consumers'][0])
    expect_failure(lambda:validate_RGB_plan(frozen['consumers'],duplicate),'duplicate_consumer_lease_rejected')
    raw=list(map(F,a['old_clock']['original_exact_pts']));dur=[F(1,25)]*len(raw)
    clock=measured_clock(a,raw,dur,[8,8],dict(index=0,time_base='1/25',average_rate='25'))
    compare_clock(a,clock);boundary.normalized_clock(clock);checked.append('nonzero_raw_origin_and_native_positive_terminal_bind')
    bad=copy.deepcopy(clock);bad['original_exact_pts'][10]=str(F(bad['original_exact_pts'][10])+F(1,1000))
    expect_failure(lambda:compare_clock(a,bad),'changed_original_PTS_rejected')
    bad=copy.deepcopy(clock);bad['first_original_pts_exact']='0'
    expect_failure(lambda:compare_clock(a,bad),'changed_raw_origin_rejected')
    bad=copy.deepcopy(clock);bad['physical_end_exact']='10001/1000'
    expect_failure(lambda:compare_clock(a,bad),'changed_measured_terminal_rejected_no_epsilon')
    expect_failure(lambda:measured_clock(a,raw,dur[:-1]+[None],[8,8],dict(index=0,time_base='1/25',average_rate='25')),
        'missing_last_duration_rejected_without_CFR_substitution')
    for row in frozen['requests']:
        if row['source_id']!='SYN_A':continue
        req=materialized_request(a,row,clock,boundary,continuity,verify,clock['native_duration_by_ordinal'])
        require(req['source_frame_ordinals']==row['source_frame_ordinals'] and req['request_id']==row['request_id'] and
                req['reference_available_to_inference'] is False,'Native/prompt event identity changed')
        if row['kind']=='VERIFY':
            require(req['source_frame_ordinals']==a['windows'][0]['original_frame_ordinals'] and
                    req['window_start']=='0' and req['window_end']=='10','VERIFY lost original full-window visuals')
        else:
            result=boundary.resolve_endpoint({'decision':'UNKNOWN'},req)
            require(result['endpoint_exact']==row['original_endpoint_exact'] and not result['changed'],'UNKNOWN moved endpoint')
    checked.append('frozen_v3_math_prompt_and_VERIFY_full_original_window_compatible')
    import torch
    torch.set_num_threads(1)
    buffer=torch.arange(60,dtype=torch.float32)
    nanbits=torch.tensor([0x7fc00001,0x80000000,0],dtype=torch.int64).to(torch.int32).view(torch.float32)
    encoded=dict(input_ids=torch.arange(12,dtype=torch.int64).reshape(1,12),attention_mask=torch.ones(1,12,dtype=torch.int64),
        pixel_values_videos=buffer[7:31].reshape(4,6).t(),aliased_visual=buffer[9:21:2],
        video_grid_thw=torch.tensor([[2,4,6]],dtype=torch.int64),nan_and_signedzero=nanbits,
        bf16_original=torch.tensor([1,2],dtype=torch.bfloat16))
    expected=cache_signature(encoded)
    require(signature_any_device(encoded)==expected,'CPU/any-device signature ABI differs')
    copied,proof=transfer_exact(encoded,'cpu',expected)
    require(cache_signature(copied)==expected and not proof['actual_GPU_transfer'] and
        copied['pixel_values_videos'].untyped_storage().data_ptr()!=encoded['pixel_values_videos'].untyped_storage().data_ptr(),
        'Independent fullstorage copy failed')
    expect_failure(lambda:transfer_exact(encoded,'cpu',{}),'fake_signature_rejected_before_transfer')
    require(not torch.cuda.is_initialized(),'Pure CPU test initialized CUDA')
    checked.append('synthetic_full_storage_dtype_stride_offset_alias_nan_bits_equal')
    return dict(status='PASS_PURE_CONTRACT_AND_SYNTHETIC_CPU_TRANSFER_NOT_PRODUCTION_ADMISSION',checks=checked,
        actual_production_source_reads=0,actual_source_decodes=0,actual_processor_encodes=0,new_model_calls=0,
        actual_GPU_transfers=0,cache_IO=0,old_successful_operations_repeated=0)
