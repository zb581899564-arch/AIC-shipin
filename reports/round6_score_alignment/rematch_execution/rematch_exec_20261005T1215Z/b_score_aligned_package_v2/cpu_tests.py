"""Real boundaries, old bug replay, cache separation and inherited spatial contracts."""
from common import *
from fractions import Fraction
import ast
import io
import unittest


def main():
    bind_helpers()
    from contracts import answer_string, parse_segments, parse_focus_norm, validate_segments
    from constrained_json import BoundedSegmentsGrammar
    from native_input import floor_indices, window_from_pts
    from native_segment_contract import native_segment_ranges
    from engine import plan_window
    tests = 0
    cases = []
    for duration in (30, 0.23333333333333334, 29.967666666666666):
        for endpoint in (duration, duration / 3, duration / 7):
            target = [[0, endpoint]]
            raw = answer_string(target, duration, allow_empty=False)
            require(BoundedSegmentsGrammar(duration, allow_empty=False).complete(raw), 'lossless endpoint not in actual B2 grammar')
            require(parse_segments(raw, duration, allow_empty=False) == (target, [], []), 'endpoint changed during parsing')
            tests += 1
    for raw in ('{"segments":[]}', '{"segments":[[0,31]]}', '{"segments":[[0,1],[0.5,2]]}',
                '{"segments":[[0,1]],"segments":[[0,2]]}', '{"segments":[[true,1]]}', '{"segments":[[0,NaN]]}'):
        require(parse_segments(raw, 30, allow_empty=False)[0] is None, 'invalid prediction became valid')
        tests += 1
    require(parse_focus_norm('{"center":[500,250]}') == [.5,.25], 'declared integer coordinates failed')
    for raw in ('{"center":[0.5,0.5]}', '{"center":[1001,500]}', '{"center":[true,500]}', 'text {"center":[1,2]}'):
        require(parse_focus_norm(raw) is None, 'unit guessing or fallback introduced')
        tests += 1
    for count in (1, 2, 3, 63, 64, 65, 719, 720, 901):
        ids = floor_indices(10, 10+count)
        require(len(ids) == min(64,count) and ids[0] == 10 and ids[-1] == 9+count and len(set(ids)) == len(ids),
                'floor endpoint or frame count differs')
        tests += 1
    require(native_segment_ranges([[.1,.5]], [0,.1,.3,.5,1], 0, 1) == [(1,3)], 'half-open native interval differs')
    try:
        native_segment_ranges([[.11,.12]], [0,.1,.3,.5,1], 0, 1)
    except ValueError:
        tests += 1
    else:
        raise ValueError('interval without a physical frame accepted')
    real_windows = endpoints = mismatches = original_rejections = 0
    old_engine = load(RUN / 'b_score_aligned_package_v1/engine.py', 'b2_original_engine_cpu')
    from production import select_frames
    replayed_endpoints = []
    for scope in ('nontest','rematch'):
        _, manifest, clocks = inputs(scope)
        from frame_contract import window_schedule
        for item in manifest['records']:
            clock = clocks[item['video_id']]
            for index, (start,end) in enumerate(window_schedule(item, manifest['kind'],clock)):
                window = plan_window(item,clock,start,end,index)
                require(window['planned_source_frame_ordinals'] == floor_indices(
                    window['planned_source_frame_ordinals'][0],
                    window['planned_source_frame_ordinals'][0]+window['eligible_source_frame_count']), 'real floor identity differs')
                duration = window['window_duration_sec']
                require(window == old_engine.plan_window(item, clock, start, end, index),
                        'v2 changed the original generated input or duration')
                old_duration = end - start
                mismatches += old_duration != duration
                try:
                    validate_segments([[0, duration]], old_duration)
                except ValueError:
                    original_rejections += 1
                synthetic = dict(video_id=item['video_id'], video_path=item['source_path'],
                    n_frames=item['n_frames'], fps=item['fps_num']/item['fps_den'],
                    targetRatioWH=item['targetRatioWH'], windows=[])
                for other_index, (a, b) in enumerate(window_schedule(item, manifest['kind'], clock)):
                    synthetic['windows'].append(dict(output_valid=True, parse_errors=[], status='LEGAL_EMPTY',
                        clock_record_sha256=clock['clock_record_sha256'], start_sec=a, end_sec=b, parsed_segments=[]))
                synthetic['windows'][index].update(status='MODEL_OK', parsed_segments=[[0, duration]])
                one_manifest = dict(manifest, records=[item])
                selected = select_frames(one_manifest, [synthetic], {item['video_id']: clock})
                bound_points = [float(p) for p in clock['pts']]
                expected = native_segment_ranges([[0,duration]], bound_points, start, duration)
                require([r['source_frame'] for r in selected] == list(range(*expected[0])),
                        'full endpoint was rejected or physical source-frame identity changed')
                from bisect import bisect_left
                require(expected == [(bisect_left(bound_points, start), bisect_left(bound_points, end))],
                        'canonical full endpoint does not realize exactly the registered natural window')
                replayed_endpoints.append(dict(scope=scope, video_id=item['video_id'], index=index,
                    canonical_duration=duration, selected_frames=len(selected)))
                raw = answer_string([[0,duration]], duration, allow_empty=False)
                require(parse_segments(raw,duration,allow_empty=False)[0] == [[0,duration]] and
                        BoundedSegmentsGrammar(duration,allow_empty=False).complete(raw), 'real final endpoint changed')
                import math
                try:
                    validate_segments([[0, math.nextafter(duration, math.inf)]], duration)
                except ValueError:
                    pass
                else:
                    raise ValueError('duration repair widened a real upper boundary')
                real_windows += 1; endpoints += len(window['planned_actual_pts_sec'])
        cases.append(dict(scope=scope, sources=len(manifest['records']), all_metadata_windows_plannable=True))
    # Replay the original accepted numeric values; this is not new supervision.
    old = RUN / 'teacher_student_autopilot_v5/pilot_01/validated/validated_records.jsonl'
    originals = rows(old)
    for record in originals:
        original = json.loads(record['target_json'])['segments']
        duration = record['window']['window_duration_sec']
        serialized = answer_string(original, duration)
        require(json.loads(serialized)['segments'] == original and
                parse_segments(serialized,duration)[0] == original and
                BoundedSegmentsGrammar(duration).complete(serialized), 'an original endpoint was rounded or replaced')
    require(real_windows == 529 and mismatches == 56 and original_rejections == 29,
            'the original 529-window/29-rejection symptom was not reproduced')
    config = settings()
    from temporal_reuse import verify_algorithm_equivalence, verify_temporal
    equivalence = verify_algorithm_equivalence()
    non_test = verify_temporal('nontest')
    tests += 4
    require(config['b_adapter_sha256'] == '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' and
            config['candidate_arm'].startswith('B2_TRAINED_B'), 'trained B identity is required')
    cache_tree = ast.parse((HERE / 'cache_contract.py').read_text())
    copied = [node.args[0].right.value for node in ast.walk(cache_tree) if isinstance(node, ast.Call) and
              isinstance(node.func, ast.Attribute) and node.func.attr == 'copyfile' and
              isinstance(node.args[0], ast.BinOp) and isinstance(node.args[0].right, ast.Constant)]
    require('temporal.jsonl' not in copied and 'selected.jsonl' not in copied, 'untrained Z time reused')
    suites = unittest.TestSuite()
    for name in ('test_field_contract', 'test_empty_pipeline'):
        module = load(HERE / (name+'.py'), 'b2_inherited_'+name)
        suites.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suites)
    print(stream.getvalue(), flush=True)
    require(result.wasSuccessful(), 'inherited source-field or empty/failure contracts regressed')
    bindings = bind_helpers()
    report = dict(status='PASS_B2_CPU_CONTRACTS', tests=tests+result.testsRun,
        additional_contract_cases=tests, inherited_tests=result.testsRun,
        actual_metadata_sources=434, actual_natural_windows=real_windows, actual_sampled_native_endpoints=endpoints,
        original_target_values_replayed=len(originals), original_target_values_changed=0,
        original_target_file_sha256=sha(old), cases=cases, helper_bindings=bindings,
        duration_mismatches_reproduced=mismatches,
        original_valid_endpoint_rejections_reproduced=original_rejections,
        repaired_full_endpoint_selection_windows=len(replayed_endpoints),
        strict_nextafter_upper_bound_rejections=real_windows,
        generation_algorithm_equivalence=equivalence,
        original_nontest_temporal_replayed=non_test,
        actual_CUDA_started=False, optimizer_updates=0, teacher_quality_not_admitted=True,
        source_media_pixels_read=False, official_score_reconstruction=False, confirm_read=False)
    write(HERE / 'cpu_acceptance.json', report)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
