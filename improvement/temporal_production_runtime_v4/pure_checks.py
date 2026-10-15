"""Only NEW V4 true-context/root/capacity metadata smoke; no previous seven cases."""
import argparse
import copy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

from output_checks import independent_verify
import pr_contract as c


def rejected(action):
    try:action()
    except (ValueError,KeyError,TypeError):return
    raise AssertionError('Expected explicit generation/context rejection')


def run(control_code,bootstrap_code):
    sys.path.insert(0,str(control_code));sys.path.insert(0,str(bootstrap_code))
    import pc_contract,pb_contract,pr_io,pc_io,pb_io
    scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT'
    application='LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE'
    c.input_generation('temporal_production_inputs_v4',scope,application)
    rejected(lambda:c.input_generation('temporal_production_inputs_v3',scope,application))
    rejected(lambda:c.input_generation('temporal_production_inputs_v4','NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE',application))
    c.require(c.SCHEMA=='TEMPORAL_PRODUCTION_RUNTIME_V4' and pc_contract.SCHEMA=='TEMPORAL_PRODUCTION_CONTROL_V3' and
        pr_io.BASE.name=='temporal_production_runtime_v4' and pc_io.BASE.name=='temporal_production_control_v3' and
        pb_io.INPUT.name=='temporal_production_inputs_v4' and pb_io.RUNTIME.name=='temporal_production_runtime_v4' and
        pb_io.CONTROL.name=='temporal_production_control_v3','Final roots/schema generations differ')
    points=[str(F(i)*2/3) for i in range(66)];ordinals=list(range(64))
    meta=dict(kind='VERIFY',event_id='E',request_id='E.verify',original_case_id='W',original_segment_index=0,
        source_sha256='d'*64,original_interval_exact=['6','26'],original_window_exact=['0','30'],
        original_native_cut_interval_exact=['6','38'],original_native_cut_source_ordinals=[9,57],
        new_verify_window_exact=['0','128/3'],window_start='0',window_end='128/3',physical_end_exact='44',
        all_source_exact_pts=points,source_total_frames=66,verify_eligible_source_ordinal_bounds=[0,64],
        verify_original_frame_ordinals=ordinals,source_frame_ordinals=ordinals,sample_exact_pts=points[:64],
        candidate_visible_sample_count=48,allowed_decisions=['KEEP','UNKNOWN','DROP'],candidate_window_local_exact=['6','38'],
        audio_observed=False,reference_available_to_inference=False,reference_labels_read=False,new_candidate_created=False,
        uncertainty_gate='NONE',verify_view_kind='NEW_VERIFY_TIMING_CONTEXT_ORIGINAL64_PIXELS',
        dual_coordinate_schema='TEMPORAL_PRODUCTION_INPUTS_V4_DUAL_RECIPE_READER_NATIVE_VERIFY_ORDINAL_CONTEXT')
    result=independent_verify(meta,'{"decision":"KEEP"}')
    c.require(result['retained_interval_exact']==['6','26'] and F(meta['new_verify_window_exact'][1])>30,
        'True >30s ordinal context was truncated or replaced recipe interval')
    bad=copy.deepcopy(meta);bad.update(new_verify_window_exact=['0','30'],window_end='30')
    rejected(lambda:independent_verify(bad,'{"decision":"UNKNOWN"}'))
    bad=copy.deepcopy(meta);bad['source_frame_ordinals'][5]=65
    rejected(lambda:independent_verify(bad,'{"decision":"KEEP"}'))
    # Full canonical raw forecast can exceed capacity without pretending it fits;
    # grouping reserves two live complete-source raw fallbacks, not all future raw.
    sources=[dict(source_id='S'+str(i),source_sha256='e'*64,width=1,height=1) for i in range(10)]
    requests=[dict(request_id=s['source_id']+'.verify',source_id=s['source_id']) for s in sources]
    groups_meta={s['source_id']:dict(source_id=s['source_id'],source_frame_ordinals=list(range(64))) for s in sources}
    plan=dict(sources=sources,requests=requests,RGB_groups=groups_meta,_file_sha256='f'*64)
    estimates=dict(schema='FROZEN_SOURCE_STORAGE_ESTIMATES_FOR_PROSPECTIVE_INPUTS_V1',global_graph_sha256='f'*64,
        predictions_or_reference_metrics_used=False,actual_first_production_storage_observed=False,
        estimate_kind='CONSERVATIVE_UNCOMPRESSED_CODE_BOUND',sources=[dict(source_id=s['source_id'],source_sha256='e'*64,
        logical_request_ids=[s['source_id']+'.verify'],permanent_bytes=500,staging_bytes=200,transient_bytes=10,memory_bytes=10) for s in sources])
    groups,receipt=pb_contract.group_sources(plan,estimates,{'mem_available_bytes':100,'disk_available_bytes':3000},10,10,10)
    c.require([s for g in groups for s in g]==[s['source_id'] for s in sources] and len(groups)==5 and
        receipt['all_future_permanent_estimate_bytes']==5000 and receipt['global_forecast_is_not_fit_guarantee'] and
        not receipt['all_future_uncompressed_canonical_reserved_upfront'],'Future raw forecast became an artificial global admission or fit claim')
    return dict(status='PASS_NEW_V4_ROOT_SCHEMA_TRUE_ORDINAL_CONTEXT_AND_DOUBLE_BUFFER_FORECAST_SMOKE',checks=3,
        previous_seven_cases_rerun=False,synthetic_metadata_only=True,formal_project_init_prepare_GPU_calls=0,
        media_decodes=0,processor_encodes=0,model_calls=0,global_storage_fit_claim=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--control-code',required=True,type=Path)
    parser.add_argument('--bootstrap-code',required=True,type=Path);parser.add_argument('--result',required=True,type=Path)
    args=parser.parse_args();value=run(args.control_code,args.bootstrap_code)
    with args.result.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
    print(json.dumps(value))
