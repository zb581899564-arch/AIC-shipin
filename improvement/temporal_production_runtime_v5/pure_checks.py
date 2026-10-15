"""Only the newly added short-VERIFY structural interface; no previous suites."""
import argparse
import copy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

from output_checks import independent_structural_result
import pr_contract as c


def rejected(action):
    try:action()
    except (ValueError,KeyError,TypeError):return
    raise AssertionError('Expected strict structural-result rejection')


def run(control_code,bootstrap_code,input_code):
    sys.path.insert(0,str(input_code));sys.path.insert(0,str(control_code));sys.path.insert(0,str(bootstrap_code))
    import tp_contract,pc_contract,pb_contract,pr_io,pc_io,pb_io
    scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V5_VERIFY_SHORT_CONTEXT_UNKNOWN'
    c.input_generation('temporal_production_inputs_v5',scope,'LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE')
    c.require(c.SCHEMA=='TEMPORAL_PRODUCTION_RUNTIME_V5' and pc_contract.SCHEMA=='TEMPORAL_PRODUCTION_CONTROL_V4' and
        pb_contract.SCHEMA=='TEMPORAL_PRODUCTION_METADATA_BOOTSTRAP_V2' and
        pr_io.BASE.name=='temporal_production_runtime_v5' and pc_io.INPUT.name=='temporal_production_inputs_v5' and
        pb_io.BASE.name=='temporal_production_bootstrap_v2','Only the new independent generations may be used')
    event=dict(event_id='S_W000_E00',original_case_id='S_W000',original_segment_index=0,
        original_interval_exact=['0','9/10'],original_window_exact=['0','1'],
        original_native_cut_interval_exact=['0','23/25'],original_native_cut_source_ordinals=[0,23])
    window=dict(original_case_id='S_W000',eligible_source_ordinal_bounds=[0,23],original_frame_ordinals=list(range(23)),
        original_frame_pixel_sha256=['d'*64]*23,original_visual_sample_count=23,
        original_window_exact=['0','1'],events=[event])
    source=dict(source_id='S',windows=[window],physical_plan_clock=dict(
        normalized_exact_pts=[str(F(i,25)) for i in range(200)],physical_end_exact='8'))
    plan=tp_contract.request_skeletons([source]);row=next(row for row in plan['requests'] if row['kind']=='VERIFY')
    output=independent_structural_result(row,source)
    c.require(len(plan['requests'])==3 and len(plan['consumers'])==2 and row['request_id'] not in plan['consumers'] and
        all(row['request_id'] not in lease['consumers'] for lease in plan['RGB_groups'].values()) and
        output['decision']=='UNKNOWN' and output['candidate_kept'] is True and output['retained_interval_exact']==['0','9/10'] and
        output['actual_model_call'] is False and output['successful_model_call_required'] is False,
        'Short VERIFY must remain a counted logical output with no call/consumer/RGB lease and preserve original recipe')
    bad=copy.deepcopy(row);bad['structural_verify_result']['decision']='DROP'
    rejected(lambda:independent_structural_result(bad,source))
    bad=copy.deepcopy(row);bad['structural_verify_result']['successful_model_call_required']=True
    rejected(lambda:independent_structural_result(bad,source))
    bad=copy.deepcopy(row);bad['original_visual_sample_count']=64
    rejected(lambda:independent_structural_result(bad,source))
    return dict(status='PASS_NEW_SHORT_VERIFY_STRUCTURAL_OUTPUT_INTERFACE',positive_cases=1,rejected_malformed_cases=3,
        prior_root_context_capacity_boundary_suites_rerun=False,synthetic_metadata_only=True,
        formal_project_init_prepare_GPU_calls=0,media_decodes=0,processor_encodes=0,model_calls=0,quality_claim=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--control-code',required=True,type=Path)
    parser.add_argument('--bootstrap-code',required=True,type=Path);parser.add_argument('--input-code',required=True,type=Path)
    parser.add_argument('--result',required=True,type=Path);args=parser.parse_args()
    value=run(args.control_code,args.bootstrap_code,args.input_code)
    with args.result.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2)
    print(json.dumps(value))
