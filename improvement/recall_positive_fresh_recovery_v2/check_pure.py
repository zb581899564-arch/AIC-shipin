"""Bounded synthetic checks for frozen native plan and pre-GPU first-QA order."""
import ast
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys

from source_plan import source_document, unique_view_plan
from native_helpers import capacity_geometry, capacity_numbers
from fresh_registration import validate_source_grouped_order, validate_recovery_documents


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Expected native contract rejection')


def main():
    clocks, rows = {}, []
    for index in range(4):
        vid = 'v_source'+str(index)
        rows.append(dict(video_id=vid, group='confirm', media=dict(group='confirm', video_id=vid,
            sha256=str(index+1)*64)))
        clocks[vid] = dict(original_exact_pts=[str(F(i, 10)) for i in range(510)], physical_end_exact='51',
            original_zero_origin_verified=True, first_original_pts_exact='0', last_frame_duration_exact='1/10',
            timeline_shift_applied=False, native_frames=510, fps_num=10, fps_den=1, width=320, height=240)
    sources = source_document(rows, clocks, 'confirm'); plan = unique_view_plan(sources, 'confirm')
    assert len(sources['sources']) == 4 and 0 < plan['actual_input_count'] <= 48
    for view in plan['unique_views']:
        eligible = [i for i, p in enumerate(map(F, clocks[view['source_name']]['original_exact_pts']))
                    if F(view['start_exact']) <= p < F(view['end_exact'])]
        assert view['source_frame_ordinals'] == [eligible[0]+j*(len(eligible)-1)//63 for j in range(64)]
        assert len(set(view['source_frame_ordinals'])) == 64
    # Byte-identical selected pure function implementations provide the same
    # original ceil/30, 15/7.5 and shared-view aliases for a fresh source set.
    original_path = Path(__file__).parents[1]/'recall_expansion_verify40_46_v1/prepare_inputs.py'
    tree = ast.parse(original_path.read_text(encoding='utf-8'))
    selected = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and
        node.name in ('source_document', 'unique_view_plan')], type_ignores=[])
    import source_plan
    namespace = {name: value for name, value in vars(source_plan).items() if not name.startswith('__')}
    exec(compile(selected, str(original_path), 'exec'), namespace)
    assert sources == namespace['source_document'](rows, clocks, 'confirm')
    assert plan == namespace['unique_view_plan'](sources, 'confirm')
    # Reproduce the actual v1 failure: primary preparation iterates sources,
    # each with their original baseline-then-overlap view order. The plan itself
    # groups all sources' baseline views before all sources' overlap views.
    source_order = [row['video_id'] for row in rows]
    source_grouped = [dict(case_id=v['case_id'], source_name=v['source_name'])
        for name in source_order for v in plan['unique_views'] if v['source_name'] == name]
    raw_role_order = [dict(case_id=v['case_id'], source_name=v['source_name']) for v in plan['unique_views']]
    assert source_grouped != raw_role_order
    frozen_before = __import__('json').dumps(source_grouped, sort_keys=True)
    assert validate_source_grouped_order(plan, source_grouped, source_order) == [e['case_id'] for e in source_grouped]
    assert frozen_before == __import__('json').dumps(source_grouped, sort_keys=True)
    rejects(lambda: validate_source_grouped_order(plan, raw_role_order, source_order))
    rejects(lambda: validate_source_grouped_order(plan, source_grouped[:-1], source_order))
    duplicate = source_grouped[:-1]+[source_grouped[0]]
    rejects(lambda: validate_source_grouped_order(plan, duplicate, source_order))
    within_source = list(source_grouped); within_source[0], within_source[1] = within_source[1], within_source[0]
    rejects(lambda: validate_source_grouped_order(plan, within_source, source_order))
    wrong_case = [dict(v) for v in source_grouped]; wrong_case[0]['case_id'] = 'foreign_case'
    rejects(lambda: validate_source_grouped_order(plan, wrong_case, source_order))
    wrong_source = [dict(v) for v in source_grouped]; wrong_source[0]['source_name'] = source_order[1]
    rejects(lambda: validate_source_grouped_order(plan, wrong_source, source_order))
    bad = {**clocks, 'v_source0': {**clocks['v_source0'], 'timeline_shift_applied': True}}
    rejects(lambda: source_document(rows, bad, 'confirm'))
    def resize(**kwargs):
        return (64, 96)
    geometry = capacity_geometry(dict(width=320, height=240), dict(shortest_edge=1024, longest_edge=64*64*96), 16, 2, 2, resize)
    assert geometry['pixel_tensor_bytes'] == 64*64*96*3*4
    bound = capacity_numbers(dict(width=320, height=240), 64, 2, geometry)
    assert bound['remaining_output_bound_bytes'] > 0 and bound['upcoming_memory_bound_bytes'] > 0
    # Every actual B0/conservative VERIFY replay may only adopt saved first QA,
    # never call the visual processor or encode new input tokens after GPU.
    for filename in ('pilot_runtime.py', 'pilot_verify.py'):
        path = Path(__file__).parent/filename
        module = ast.parse(path.read_text(encoding='utf-8'))
        replay = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'replay')
        forbidden = [n for n in ast.walk(replay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and
                     n.func.attr in ('encode', 'retarget', 'baseline_frames')]
        assert not forbidden, filename+' repeats actual input QA after GPU'
    chain = (Path(__file__).parent/'fresh_chain.py').read_text(encoding='utf-8')
    assert chain.index("child(state, 'first_input_qa'") < chain.index("stage = 'B0'; gate")
    assert chain.index("child(state, 'VERIFY_first_input_qa'") < chain.index("stage = 'VERIFY'; gate")
    assert "positive_runtime.py'" in chain and 'registration_confirm.json' in chain
    assert "child(state, 'prepare_inputs'" not in chain and "state = root/'confirm/chain_02'" in chain
    import prepare_inputs
    rejects(lambda: prepare_inputs.prepare(None, 'confirm'))
    # The recovery may not quietly change prior science, source, budget or
    # deadline. The original successful primary stays bound to its v1 receipt.
    original = dict(status='REGISTERED_POSITIVE_FIRST_FRESH_CONFIRM_V1', group='confirm',
        protocol_ref={'sha256':'p'}, authorization_ref={'sha256':'a'}, development_registration_ref={'sha256':'d'},
        dev_selection_ref={'sha256':'s'}, dev_result_ref={'sha256':'r'}, source_registration_ref={'sha256':'m'},
        reference_completion_ref={'sha256':'f'}, frozen_positive_code_dir='MAIN/code', capacity_contract={'size':123},
        deadline='original', model_parameters=8782459120, optimizer_updates=0, source_scope='EXTERNAL_NONTEST_ONLY',
        reference_available_to_inference=False, production_admitted=False,
        gpu_budget={stage:dict(max_actual_calls=calls,max_seconds=seconds,gpu_job_name=stage+'_20261015_v1')
            for stage,calls,seconds in [('B0',48,1800),('VERIFY',240,2400),('POSITIVE',80,1200)]})
    recovery = {**original, 'status':'REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2',
        'gpu_budget':{stage:{**value,'gpu_job_name':stage+'_20261015_v2'} for stage,value in original['gpu_budget'].items()}}
    primary=dict(status='PASS_POSITIVE_FIRST_FRESH_NATIVE64_PRIMARY_INPUTS_NOT_GPU_ADMISSION', group='confirm',
        CPU_only=True, CUDA_initialized=False, actual_input_count=28, entries=[{}]*28, sources=['a','b','c','d'],
        primary_encode_calls_started=28, primary_encode_calls_returned=28, actual_new_processor_encodes=28,
        actual_new_RGB_decode_passes=4, first_independent_input_replays_already_completed=0,
        new_model_calls=0, new_optimizer_updates=0, original_clock_measurements_repeated=0)
    failure=dict(stage='FIRST_ALL_NATIVE_INPUT_QA_PRE_GPU',error='first_input_qa',preserve_all_raw_and_success=True,
                 no_automatic_resume=True,production_admitted=False)
    diagnosis=dict(error='ROLE_ORDER_VS_SOURCE_GROUPED_COMPLETE_INPUT_ENTRY_ORDER',actual_primary_completion_status=primary['status'],
        actual_input_count=28,original_view_plan_contents_unchanged=True,complete_expected_source_grouped_order_matches=True,
        all_case_metadata_native_view_identity_matches=True,input_QA_output_directory_exists=False,input_QA_evidence_count=0,
        B0_gpu_output_directory_exists=False,complete_primary_encode_calls_started=28,complete_primary_encode_calls_returned=28,
        original_chain_failure=failure)
    validate_recovery_documents(original,recovery,primary,failure,diagnosis)
    rejects(lambda: validate_recovery_documents(original,{**recovery,'deadline':'later'},primary,failure,diagnosis))
    rejects(lambda: validate_recovery_documents(original,recovery,primary,failure,{**diagnosis,'input_QA_evidence_count':1}))
    print('PASS: actual source-group order regression; duplicate/missing/within-source/foreign veto; immutable recovery authority; no prepare; native64/capacity/pre-GPU QA/output-only parity')


if __name__ == '__main__':
    main()
