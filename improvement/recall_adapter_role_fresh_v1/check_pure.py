"""Bounded synthetic checks for frozen native plan and pre-GPU first-QA order."""
import ast
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys

from source_plan import source_document, unique_view_plan
from native_helpers import capacity_geometry, capacity_numbers


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
    print('PASS: original native64/window/source parity, no shifted clock, capacity math, pre-GPU first-input QA, output-only post-GPU replay')


if __name__ == '__main__':
    main()
