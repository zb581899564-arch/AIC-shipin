"""One incremental synthetic23 case; no old V4/math/color suites rerun."""
import copy
from fractions import Fraction as F
from tp_contract import (SCHEMA,READER_SCOPE,request_skeletons,materialized_request,require,validate_reader_scope)


def run(scope):
    validate_reader_scope(scope)
    points=[F(i,30) for i in range(100)];ordinals=list(range(77,100))
    recipe=['257/100','321/100']
    event=dict(event_id='SYN_SHORT_E00',original_case_id='SYN_SHORT_W000',original_segment_index=0,
        original_interval_exact=recipe,original_window_exact=['77/30','10/3'],
        original_window_start_exact='77/30',original_window_end_exact='10/3',
        original_native_cut_interval_exact=['13/5','16/5'],original_native_cut_source_ordinals=[78,96],
        accepted_window_sha256='2'*64)
    source=dict(source_id='SYN_SHORT',physical_plan_clock=dict(normalized_exact_pts=list(map(str,points)),physical_end_exact='10/3'),
        windows=[dict(original_case_id=event['original_case_id'],original_window_exact=['77/30','10/3'],
            original_frame_ordinals=ordinals,original_frame_pixel_sha256=['1'*64]*23,
            original_visual_sample_count=23,eligible_source_ordinal_bounds=[77,100],events=[event])])
    original=copy.deepcopy(source)
    graph=request_skeletons([source]);row=next(x for x in graph['requests'] if x['kind']=='VERIFY')
    result=row['structural_verify_result']
    require(source==original and graph['nominal_requests']==3 and graph['nominal_endpoint_requests']==2 and
        graph['nominal_VERIFY_requests']==1 and graph['actual_MODEL_endpoint_requests']==2 and
        graph['actual_MODEL_VERIFY_requests']==0 and graph['structural_VERIFY_requests']==1 and
        len(graph['consumers'])==2 and row['request_id'] not in graph['consumers'] and
        graph['structural_unknown_requests']==[row['request_id']],
        'Short original view must preserve event and nominal denominator but have no model consumer')
    require(row['execution']=='STRUCTURAL_UNKNOWN_ORIGINAL_VIEW_NO64' and
        row['original_visual_sample_count']==23 and row['source_frame_ordinals']==ordinals and
        len(row['original_frame_pixel_sha256'])==23 and 'lease_id' not in row and
        row['new_processor_and_input_proof_required'] is False and
        all(row['request_id'] not in group['consumers'] and len(group['source_frame_ordinals'])==64
            for group in graph['RGB_groups'].values()),
        'Original23 must not produce any RGB group, synthetic samples, processor or model input')
    require(result['decision']=='UNKNOWN' and result['candidate_kept'] is True and
        result['retained_interval_exact']==recipe and result['original_interval_exact']==recipe and
        result['actual_model_call'] is False and result['successful_model_call_required'] is False and
        result['predeclared_skip'] is True and result['boundaries_changed'] is False and
        result['dual_coordinate_schema']==SCHEMA and
        result['original_native_cut_interval_exact']!=result['retained_interval_exact'],
        'Short UNKNOWN must preserve old recipe exactly, without leaking native pivots or fake calls')
    try:materialized_request(source,row,{},None,None,None,{})
    except ValueError:pass
    else:raise AssertionError('Structural short request reached the model-input materializer')
    return dict(status='PASS_ONE_INCREMENTAL_ORIGINAL23_PREMODEL_STRUCTURAL_UNKNOWN_CASE',
        schema=SCHEMA,reader_scope=READER_SCOPE,synthetic_original_count=23,
        nominal_requests=3,actual_MODEL_requests=2,structural_VERIFY_requests=1,
        original_event_preserved=True,old_recipe_retained=True,no_short_RGB_group=True,
        structural_model_materialization_blocked=True,old_V4_9_suite_repeated=False,
        old_color5_suite_repeated=False,old_checkpoint2_suite_repeated=False,
        actual_metadata_projection_calls=0,media_reads=0,pixel_reads=0,processor_calls=0,model_calls=0)
