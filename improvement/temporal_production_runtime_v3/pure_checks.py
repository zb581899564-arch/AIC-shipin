"""Seven NEW dual-coordinate/reader/envelope checks only; never old suites."""
import argparse
import copy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

from output_checks import independent_endpoint_export,independent_verify
from pr_contract import require


def rejected(action):
    try:action()
    except (ValueError,KeyError,TypeError):return
    raise AssertionError('Expected strict rejection')


def run(control_code):
    sys.path.insert(0,str(control_code))
    import pc_contract
    from aggregate import exact_clock
    checks=[]
    schema='TEMPORAL_PRODUCTION_INPUTS_V3_DUAL_RECIPE_READER_NATIVE'
    meta=dict(kind='ENDPOINT',request_id='E.start',event_id='E',side='start',
        original_endpoint_exact='49/50',legacy_recipe_original_endpoint_exact='49/50',
        original_native_cut_endpoint_exact='1',refiner_native_cut_endpoint_exact='1',
        original_interval_exact=['49/50','201/100'],original_native_cut_interval_exact=['1','2'],dual_coordinate_schema=schema)
    def native(reason,point,raw=None):
        return dict(request_id='E.start',event_id='E',side='start',raw_decision=raw or {'decision':reason},
            applied_decision=reason,original_endpoint_exact='1',endpoint_exact=point,displacement_exact=str(F(point)-1),changed=F(point)!=1)
    clock=dict(physical_end_exact='3')
    kept=independent_endpoint_export(native('KEEP','1'),meta,clock)
    require(kept['endpoint_exact']=='49/50' and not kept['changed'] and kept['original_recipe_preserved'],'KEEP leaked native pivot')
    checks.append('KEEP_DIFFERENT_NATIVE_PIVOT_EXACT_OLD_RECIPE')
    unknown=independent_endpoint_export(native('UNKNOWN_EDGE_SAMPLE','1',{'decision':'REFINE','sample_index':0}),meta,clock)
    require(unknown['endpoint_exact']=='49/50' and unknown['native_endpoint_exact']=='1' and not unknown['changed'],'UNKNOWN moved recipe')
    checks.append('UNKNOWN_EDGE_NATIVE_RESULT_EXACT_OLD_RECIPE')
    zero=independent_endpoint_export(native('REFINE','1',{'decision':'REFINE','sample_index':12}),meta,clock)
    require(zero['applied_decision']=='REFINE' and not zero['native_cut_actually_moved'] and not zero['changed'] and
        zero['endpoint_exact']=='49/50','Zero native shift became application shift')
    checks.append('REFINE_ZERO_NATIVE_SHIFT_PRESERVES_OLD_RECIPE')
    moved=independent_endpoint_export(native('REFINE','6/5',{'decision':'REFINE','sample_index':14}),meta,clock)
    require(moved['endpoint_exact']=='6/5' and moved['displacement_exact']=='11/50' and moved['native_displacement_exact']=='1/5' and
        moved['native_cut_actually_moved'],'Moved native REFINE mapping differs')
    rejected(lambda:independent_endpoint_export(native('REFINE','4'),meta,clock))
    checks.append('MOVED_REFINE_DUAL_DISPLACEMENTS_AND_ACTUAL_DOMAIN_REJECTION')
    ref={'path':'/synthetic/terminal.json','sha256':'a'*64};regref={'path':'/synthetic/reg.json','sha256':'b'*64}
    oldref={'path':'/synthetic/clock.json','sha256':'c'*64};source=dict(source_id='P_s',video_id=0,source_path='/synthetic/0.mp4',
        source_sha256='d'*64,source_bytes=100,width=8,height=8,fps_num=5,fps_den=1,original_clock_ref=oldref,
        packet_terminal_observation_ref=ref,packet_registration_ref=regref,
        old_clock=dict(n_frames=4,legacy_planned_end_exact='4/5',old_terminal_evidence={'kind':'NATIVE_LAST_FRAME_PACKET_DURATION'}))
    original=dict(raw_time_base='1/15',native_pts_ticks=[5,8,11,14],raw_first_pts_ticks=5,native_frame_end_pts_ticks=[8,11,14,17])
    packet_source=dict(video_id=0,source_sha256='d'*64,source_path=source['source_path'],source_stat={'bytes':100},n_frames=4,
        width=8,height=8,clock_array_ref=oldref,original_raw_first_frame_pts_exact='1/3',
        original_raw_last_frame_pts_exact='14/15',old_explicit_raw_end_exact='17/15')
    packet=dict(pts=14,duration=6,time_base_exact='1/15',size=10,stream_index=0,raw_display_pts_exact='14/15',
        duration_seconds_exact='2/5',compressed_packet_sha256='e'*64)
    terminal=dict(status='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK',
        error='Measured packet end differs from old explicit native end ticks',observations=dict(actual_source_sha256='d'*64,
        source_SHA_read_bytes=100,AV_open_calls=1,demux_calls=1,actual_frame_decode_calls=0,PyAV_version='17.1.0',
        matching_packets=[packet],max_display_packet_pts_exact='14/15',
        video_stream=dict(index=0,type='video',time_base_exact='1/15',codec_name='synthetic',width=8,height=8)))
    full=dict(original_exact_pts=['1/3','8/15','11/15','14/15'],normalized_exact_pts=['0','1/5','2/5','3/5'],
        first_original_pts_exact='1/3',physical_end_exact='1',source_sha256='d'*64,source_path=source['source_path'],n_frames=4,
        measured_geometry=[8,8],reader_version='17.1.0',video_stream_index=0,stream_time_base_exact='1/15',
        last_frame_duration_exact='2/5',native_duration_by_ordinal={'3':'2/5'},packet_terminal_observation_ref=ref,
        packet_registration_ref=regref,physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
        last_normalized_pts_exact='3/5',last_frame_duration_exact='2/5',packet_terminal_observation_ref=ref),
        first_RGB_decoder_terminal_witness=dict(status='PASS_ACTUAL_FULL_PTS_AND_FRAME_DURATION_EXACT_PACKET_EQUALITY',
        reader_version='17.1.0',last_original_pts_exact='14/15',last_normalized_pts_exact='3/5',last_frame_duration_exact='2/5',
        physical_end_exact='1',packet_terminal_observation_ref=ref),
        packet_terminal_evidence=dict(reader_version='17.1.0',last_original_pts_exact='14/15',last_normalized_pts_exact='3/5',
        packet_duration_exact='2/5',physical_end_exact='1',source_sha256='d'*64,exact_old_last_frame_pts_match=True,
        unique_maxdisplay_packet=True,observation_ref=ref,old_validation_status=terminal['status'],
        old_FAIL_promoted_to_PASS=False,new_full_frame_decode_required=True))
    before=json.dumps(terminal,sort_keys=True);audit=exact_clock(source,full,original,packet_source,terminal)
    require(audit['old_validation_status']=='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK' and not audit['old_FAIL_promoted_to_PASS'] and
        not audit['legacy_end_equals_new_native_end'] and json.dumps(terminal,sort_keys=True)==before,'Prior FAIL body/status changed')
    bad=copy.deepcopy(full);bad['packet_terminal_evidence']['old_FAIL_promoted_to_PASS']=True
    rejected(lambda:exact_clock(source,bad,original,packet_source,terminal))
    checks.append('OLD_END_EQUALITY_FAIL_PRESERVED_NEW_READER_DURATION_SCOPE')
    bad=copy.deepcopy(full);bad['first_RGB_decoder_terminal_witness']['last_frame_duration_exact']='1/5'
    rejected(lambda:exact_clock(source,bad,original,packet_source,terminal))
    bad=copy.deepcopy(full);bad['normalized_exact_pts'][1]='1/4';rejected(lambda:exact_clock(source,bad,original,packet_source,terminal))
    verify=dict(kind='VERIFY',event_id='E',request_id='E.verify',original_case_id='W',original_segment_index=0,
        source_sha256='d'*64,original_interval_exact=['49/50','151/50'],original_window_exact=['0','31/10'],
        original_native_cut_interval_exact=['1','3'],new_verify_window_exact=['0','3'],sample_exact_pts=[str(F(i)*3/64) for i in range(64)],
        candidate_visible_sample_count=42,allowed_decisions=['KEEP','UNKNOWN','DROP'],candidate_window_local_exact=['1','3'],
        audio_observed=False,reference_available_to_inference=False,reference_labels_read=False,new_candidate_created=False,
        uncertainty_gate='NONE',verify_view_kind='NEW_VERIFY_TIMING_CONTEXT_ORIGINAL64_PIXELS',dual_coordinate_schema=schema)
    value=independent_verify(verify,'{"decision":"UNKNOWN"}')
    require(value['retained_interval_exact']==['49/50','151/50'],'VERIFY altered old recipe beyond actual end')
    rejected(lambda:independent_verify(verify,'model_failed'))
    checks.append('DECODER_PACKET_AND_FULL_PTS_MISMATCH_BLOCK_VERIFY_LEGACY_WINDOW_KEEP')
    total=8767123696*2+5+3+2+15335424*2*8+6
    envelope=dict(status='OBSERVATION_UNAVAILABLE_WITH_CODE_BOUNDED_ENVELOPE',cold_load_HWM_observed=False,
        observed_BASE_host_peak_rss_bytes=None,observed_peak_proof_ref=None,actual_base_BF16_bytes=8767123696*2,
        maximum_checkpoint_shard_bytes=5,actual_CPU_peak_rss_bytes=3,maximum_prefill_tensor_code_bound_bytes=2,
        explicit_additional_adapter_two_copy_at_8_bytes_per_parameter_margin=15335424*2*8,
        explicit_additional_three_prefill_cache_signature_copy_margin_bytes=6,required_future_same_processor_and_input_token_cap=16384,
        conservative_host_memory_bound_bytes=total)
    require(pc_contract.gpu_host_envelope(envelope,total)==total,'Honest unavailable-HWM code envelope rejected')
    bad=dict(envelope,cold_load_HWM_observed=True);rejected(lambda:pc_contract.gpu_host_envelope(bad,total))
    rejected(lambda:pc_contract.gpu_host_envelope(envelope,total-1));checks.append('TYPED_UNAVAILABLE_COLD_HWM_BYTE_ENVELOPE_REJECTS_FALSE_OBSERVATION')
    require(len(checks)==7,'Only seven new bounded cases allowed')
    return dict(status='PASS_SEVEN_NEW_DUAL_COORDINATE_READER_ENVELOPE_PURE_CASES',checks=checks,synthetic_only=True,
        old_successful_pure_suites_rerun=False,media_decodes=0,processor_encodes=0,model_calls=0,real_production_operations=0,scientific_quality_claim=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--control-code',required=True,type=Path);parser.add_argument('--result',required=True,type=Path)
    args=parser.parse_args();value=run(args.control_code)
    with args.result.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2)
    print(json.dumps(value))
