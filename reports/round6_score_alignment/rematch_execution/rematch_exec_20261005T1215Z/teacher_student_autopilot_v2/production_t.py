"""Selected T adapter, floor/native-PTS input, frozen source spatial field."""
from autopilot_common import *
import argparse
from fractions import Fraction
import shutil
import sys
import time
import subprocess
from bisect import bisect_left
import math


def helpers():
    import train_student as student
    student.helper_paths(RUN)
    import common as old
    import frame_contract as frames
    import production as source_production
    # These adapters belong only to this process/new recipe; frozen Z files are unchanged.
    source_production.select_frames = select_native_frames
    source_production.field_frames = native_field_frames
    return student, old, frames, source_production


def raw_window_bounds(arrays, start, end):
    tick = Fraction(arrays['raw_time_base'])
    origin = arrays['raw_first_pts_ticks'] * tick
    return float(origin + Fraction(str(start))), float(origin + Fraction(str(end)))


def native_field_frames(manifest, clocks):
    result = []
    for item in manifest['records']:
        clock = clocks[item['video_id']]
        points = [float(p) for p in clock['pts']]
        first = bisect_left(points, item['scope_start_sec'])
        stop = bisect_left(points, item['scope_end_sec'])
        for ordinal in range(first, stop):
            result.append(dict(video_id=item['video_id'], source_frame=ordinal,
                source_path=item['source_path'], source_width=item['width'], source_height=item['height'],
                source_n_frames=item['n_frames'], fps=item['fps_num'] / item['fps_den'],
                target_ratio_wh=item['targetRatioWH']))
    return result


def select_native_frames(manifest, temporal, clocks):
    """T uses actual PTS in every branch; nominal FPS never decides a boundary."""
    import frame_contract as frames
    from contracts import validate_segments
    metadata = {r['video_id']: r for r in manifest['records']}
    predictions = {r.get('video_id'): r for r in temporal}
    require(len(metadata) == len(manifest['records']) and len(predictions) == len(temporal) and
            set(predictions) == set(metadata) == set(clocks), 'T temporal/source/clock denominator differs')
    result = []
    for video_id in sorted(metadata):
        item, record, clock = metadata[video_id], predictions[video_id], clocks[video_id]
        fps = item['fps_num'] / item['fps_den']
        require(record.get('n_frames') == item['n_frames'] and record.get('video_path') == item['source_path'] and
                record.get('targetRatioWH') == item['targetRatioWH'] and math.isfinite(record.get('fps', float('nan'))) and
                abs(record['fps'] - fps) <= max(1e-6, fps * 1e-6), 'T source identity mismatch')
        expected = frames.window_schedule(item, manifest['kind'], clock)
        require(len(record.get('windows', [])) == len(expected), 'T natural window count differs')
        points = [float(p) for p in clock['pts']]
        chosen = set()
        for window, (start, end) in zip(record['windows'], expected):
            require(window.get('output_valid') is True and not window.get('parse_errors') and
                    window.get('clock_record_sha256') == clock['clock_record_sha256'] and
                    abs(window.get('start_sec', -1) - start) <= 1e-6 and
                    abs(window.get('end_sec', -1) - end) <= 1e-6, 'T failed or wrong-clock window blocks candidate')
            segments = window.get('parsed_segments')
            validate_segments(segments, end - start)
            require(window.get('status') == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'T empty/failure status mismatch')
            for segment in segments:
                a = float(Fraction(str(start)) + Fraction(str(segment[0])))
                b = float(Fraction(str(start)) + Fraction(str(segment[1])))
                first, stop = bisect_left(points, a), bisect_left(points, b)
                require(0 <= first < stop <= item['n_frames'], 'T nonempty segment contains no actual source frame')
                chosen.update(range(first, stop))
        for ordinal in sorted(chosen):
            result.append(dict(video_id=video_id, source_frame=ordinal, source_path=item['source_path'],
                source_width=item['width'], source_height=item['height'], source_n_frames=item['n_frames'],
                fps=fps, target_ratio_wh=item['targetRatioWH']))
    return result


def temporal(scope, out):
    verify()
    student, old, frames, _ = helpers()
    from sft_contract import verify_live_gpu_reservation
    from engine import load_model
    from constrained_json import ascii_token_candidates
    verify_live_gpu_reservation()
    completion = read(HERE / 'student_01/student_completion.json')
    require(completion['status'] == 'PASS_TRAINED_SELECTED_STUDENT_ADAPTER', 'selected student not ready')
    require(sha(Path(completion['selected_adapter_dir']) / 'adapter_model.safetensors') ==
            completion['selected_adapter_sha256'], 'selected T adapter changed')
    require(sha(Path(completion['selected_adapter_dir']) / 'adapter_config.json') ==
            completion['selected_adapter_config_sha256'], 'selected T adapter configuration changed')
    config = old.verify()
    config['b_adapter'] = completion['selected_adapter_dir']
    model, processor, count = load_model(config, adapter=True)
    candidates = ascii_token_candidates(processor.tokenizer)
    _, manifest, clocks = old.inputs(scope)
    out = Path(out); out.mkdir(exist_ok=False)
    failed = window_count = 0
    started = time.monotonic()
    with (out / 'temporal.jsonl').open('x', encoding='utf-8') as stream:
        for n, item in enumerate(manifest['records'], 1):
            require(sha(item['source_path']) == item['source_sha256'], 'contest source bytes changed')
            clock = clocks[item['video_id']]
            arrays = clock['arrays']
            tick = Fraction(arrays['raw_time_base'])
            points = [float(value * tick) for value in arrays['native_pts_ticks']]
            exact_origin = arrays['raw_first_pts_ticks'] * tick
            origin = float(exact_origin)
            record = dict(video_id=item['video_id'], targetRatioWH=item['targetRatioWH'],
                          video_path=item['source_path'], n_frames=item['n_frames'],
                          fps=item['fps_num'] / item['fps_den'], arm='T_STRONG_TEACHER_SFT_ALLOW_EMPTY', windows=[])
            for j, (start, end) in enumerate(frames.window_schedule(item, manifest['kind'], clock)):
                one = time.monotonic(); window_count += 1
                raw_start, raw_end = raw_window_bounds(arrays, start, end)
                window = student.window_from_pts(item['source_path'], item['source_sha256'], points,
                                                raw_start, raw_end,
                                                item['video_id'] + ':T:' + str(j))
                window['window_duration_sec'] = float(Fraction(str(end)) - Fraction(str(start)))
                try:
                    encoded, details = student.production_encode(processor, window)
                    result = student.production_generate(model, processor, window, encoded, details, candidates)
                    del encoded
                except Exception as error:
                    result = dict(status='INFERENCE_FAILURE', output_valid=False, parsed_segments=None,
                                  parse_errors=[type(error).__name__ + ': ' + str(error)], parse_warnings=[])
                result.update(start_sec=start, end_sec=end, index=j, seconds=time.monotonic() - one,
                              clock_record_sha256=clock['clock_record_sha256'],
                              raw_source_pts_origin_sec=origin, clock_branch=clock['branch'])
                failed += not result['output_valid']; record['windows'].append(result)
            stream.write(json.dumps(record, ensure_ascii=False) + '\n'); stream.flush()
            write(out / 'progress.json', dict(stage='T_TEMPORAL', videos=n, total=len(manifest['records']),
                                             windows=window_count, failures=failed,
                                             wall_seconds=time.monotonic() - started))
    write(out / 'temporal.stage.json', dict(status='PASS_TEMPORAL_EXECUTION' if not failed else 'STOP_TEMPORAL_FAILURES',
          videos=len(manifest['records']), windows=window_count, invalid_windows=failed,
          output_sha256=sha(out / 'temporal.jsonl'), logical_parameters=count,
          allow_empty=True, input_contract=student.INPUT_CONTRACT,
          selected_adapter_sha256=completion['selected_adapter_sha256'],
          decoder='SAME_STUDENT_PRODUCTION_FUNCTION_AS_WEAK_DEV',
          wall_seconds=time.monotonic() - started), fresh=True)
    require(failed == 0, 'failed temporal generation blocks candidate; never convert failure to empty')


def scheduling(scope, out):
    verify()
    _, old, frames, source = helpers()
    out = Path(out)
    _, manifest, clocks = old.inputs(scope)
    require(read(out / 'temporal.stage.json')['status'] == 'PASS_TEMPORAL_EXECUTION', 'temporal phase did not pass')
    selected = select_native_frames(manifest, rows(out / 'temporal.jsonl'), clocks)
    cache = RUN / 'next_round_v1' / (scope + '_01')
    freeze_path = HERE / 'cache_01' / (scope + '.json')
    usable = freeze_path.is_file() and (cache / 'spatial.stage.json').is_file() and (
        read(cache / 'spatial.stage.json').get('status') == 'PASS_STRICT_SOURCE_FIELD_SPATIAL')
    if selected and usable:
        freeze = read(freeze_path)
        require(freeze['status'] == 'PASS_FROZEN_Z_SOURCE_FIELD_CACHE' and freeze['cache'] == str(cache),
                'spatial cache freeze receipt differs')
        for name, digest in freeze['files'].items():
            require(sha(cache / name) == digest, 'original frozen cache output changed: ' + name)
        source_schedule = read(cache / 'schedule.stage.json')
        require(source_schedule['status'] == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
                source_schedule['temporal_selection_used_for_boundaries'] is False, 'space cache depends on Z time decisions')
        require(read(cache / 'spatial.stage.json')['logical_parameters'] == 8767123696 and
                read(cache / 'spatial.stage.json')['time_adapter_enabled'] is False, 'space cache model differs')
        for name, key in (('field_frames.jsonl', 'field_frames_sha256'),
                          ('field_shots.jsonl', 'shots_sha256'), ('anchor_requests.jsonl', 'requests_sha256')):
            require(sha(cache / name) == source_schedule[key], 'source field cache bytes changed')
        field = rows(cache / 'field_frames.jsonl')
        wanted = {(r['video_id'], r['source_frame']) for r in source.field_frames(manifest, clocks)}
        if {(r['video_id'], r['source_frame']) for r in field} != wanted or len(field) != len(wanted):
            source.scheduling(scope, out)
            return
        outputs = rows(cache / 'anchor_output.jsonl'); requests = rows(cache / 'anchor_requests.jsonl')
        require(len(outputs) == len(requests) == read(cache / 'spatial.stage.json')['rows'] and
                all(r['status'] == 'MODEL_OK' for r in outputs), 'cached source spatial inference incomplete')
        for request, output in zip(requests, outputs):
            require(request['anchor_request_sha256'] == output['anchor_request_sha256'] and
                    request['expected_pixel_sha256'] == output['decoded_pixel_sha256'], 'cached anchor identity changed')
        old.write_rows(out / 'selected.jsonl', selected)
        for name in ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl'):
            shutil.copyfile(cache / name, out / name)
            require(sha(out / name) == freeze['files'][name], 'copied source cache bytes differ')
        schedule = dict(source_schedule, selected_frames=len(selected), source_cache=str(cache),
                        reused_time_independent_source_field=True)
        write(out / 'schedule.stage.json', schedule, fresh=True)
        space = dict(read(cache / 'spatial.stage.json'), reused_cache=True, model_calls_this_T_candidate=0,
                     source_cache=str(cache), anchor_output_sha256=sha(out / 'anchor_output.jsonl'))
        write(out / 'spatial.stage.json', space, fresh=True)
        write(out / 'cache_reuse_receipt.json', {'status': 'PASS_COMPLETE_TIME_INDEPENDENT_SOURCE_CACHE',
             'utc': utc(), 'files': {name: sha(out / name) for name in
             ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl')}}, fresh=True)
    else:
        # A failed or incomplete old cache is never silently accepted.
        source.scheduling(scope, out)


def spatial(scope, out):
    verify()
    _, _, _, source = helpers()
    out = Path(out)
    require(not (out / 'spatial.stage.json').exists(), 'spatial phase already completed')
    source.spatial(scope, out)


def finish(scope, out):
    verify()
    _, old, frames, _ = helpers()
    from field_contract import compose_from_field
    from package_contract import package, validate_predictions, keyset
    out = Path(out)
    _, manifest, _ = old.inputs(scope)
    require(read(out / 'temporal.stage.json')['invalid_windows'] == 0, 'temporal failures cannot be packaged')
    require(read(out / 'spatial.stage.json')['status'] in ('PASS_STRICT_SOURCE_FIELD_SPATIAL', 'PASS_EMPTY_SPACE_NO_MODEL_CALL'),
            'source spatial phase not complete')
    selected, shots = rows(out / 'selected.jsonl'), rows(out / 'field_shots.jsonl')
    requests, outputs = rows(out / 'anchor_requests.jsonl'), rows(out / 'anchor_output.jsonl')
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, shots, requests, outputs)
    old.write_rows(out / 'predictions.jsonl', predictions); old.write_rows(out / 'provenance.jsonl', provenance)
    result = validate_predictions(projected, predictions, keyset(selected), provenance)
    write(out / 'metadata.json', dict(records=manifest['records'], errors=[]), fresh=True)
    pending = out / 'candidate_T_8B.PENDING.zip'
    result.update(package(out / 'predictions.jsonl', pending))
    subprocess.run([sys.executable, '-B', str(RUN / 'baseline_a_pts_v1/vendor/independent_validate.py'),
         '--strict-loader-root', str(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader'),
         '--metadata', str(out / 'metadata.json'), '--selected', str(out / 'selected.jsonl'),
         '--predictions', str(out / 'predictions.jsonl'), '--provenance', str(out / 'provenance.jsonl'),
         '--zip', str(pending), '--report', str(out / 'independent_validation.json')], check=True)
    independent = read(out / 'independent_validation.json')
    require(independent['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and all(independent['checks'].values()),
            'independent source/CRC/format validation did not pass')
    candidate = out / 'candidate_T_8B.zip'; pending.rename(candidate)
    student = read(HERE / 'student_01/student_completion.json')
    result.update(status='PASS_COMPLETE_T_8B_PACKAGE_ON_LINUX', candidate=str(candidate), scope=scope,
         complete_pipeline_parameters=8782459120, shared_base_counted_once=True, offline_teacher_deployed=False,
         selected_adapter_sha256=student['selected_adapter_sha256'], official_score=None,
         uploaded=False, automatic_return=False, source_lock_sha256=sha(HERE / 'source_lock.json'),
         time_independent_source_field=True, comparison_to_B='NEW_COMPLETE_WINDOW_WEAK_TEACHER_AND_INPUT_RECIPE')
    write(out / 'package.stage.json', result, fresh=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('temporal', 'scheduling', 'spatial', 'finish'))
    parser.add_argument('scope', choices=('nontest', 'rematch'))
    parser.add_argument('out')
    args = parser.parse_args()
    globals()[args.stage](args.scope, args.out)
