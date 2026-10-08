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
import zipfile


STRICT_CHECKS = frozenset(('strict_loader_ok', 'video_record_set_exact', 'selected_key_set_exact',
    'ratio_fields_exact', 'frames_sorted', 'provenance_key_set_exact',
    'provenance_boxes_match_predictions', 'provenance_all_legal', 'provenance_sources_allowed',
    'archive_single_file', 'archive_roundtrip_exact'))
CACHE_FILES = ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl',
    'anchor_output.jsonl', 'schedule.stage.json', 'spatial.stage.json',
    'package.stage.json', 'independent_validation.json')
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
BASE_PARAMETERS = 8767123696
BASE_HASH_METHOD = 'sorted canonical names and all unique frozen parameter bytes'


def check_independent(value, scope, expected_frames):
    require(scope in ('nontest', 'rematch'), 'unknown production scope')
    require(value.get('status') == 'PASS_INDEPENDENT_STRICT_VALIDATION' and
            set(value.get('checks', {})) == STRICT_CHECKS and
            all(value['checks'][key] is True for key in STRICT_CHECKS), 'fixed 11 strict checks did not pass')
    require(value.get('video_records') == (8 if scope == 'nontest' else 426) and
            value.get('expected_frames') == value.get('prediction_frames') == expected_frames and
            value.get('strict_loader_issues') == [] and
            all(value.get(key) == 0 for key in ('duplicate_frames', 'missing', 'extra')),
            'independent denominator or issue receipt differs')
    require(value.get('strict_loader_sha256') == sha(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader/aic6/scoring.py'),
            'independent original strict validator changed')


def check_base_hash(value, config):
    require(config.get('expected_base_sha256') == BASE_SHA and config.get('base_parameters') == BASE_PARAMETERS,
            'registered B2 base identity differs')
    require(value.get('sha256') == config['expected_base_sha256'] and
            value.get('parameters') == config['base_parameters'] and value.get('method') == BASE_HASH_METHOD,
            'spatial full frozen base identity differs')


def b2_cache_evidence(scope, source):
    """Consume the actual B2 terminal and historical receipts without inventing measurements."""
    require(scope in ('nontest', 'rematch'), 'unknown cache scope')
    b2 = RUN / 'b_score_aligned_package_v4'
    config, prior = read(b2 / 'config.json'), read(RUN / 'next_round_v1/config.json')
    terminal = read(b2 / 'completion.json')
    lock_sha = sha(b2 / 'source_lock.json')
    require(terminal.get('stage') == 'PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX' and
            terminal.get('source_lock_sha256') == lock_sha, 'B2 completion or source lock differs')
    require(read(b2 / 'source_lock.json')['files'].get(str(b2 / 'config.json')) == sha(b2 / 'config.json'),
            'B2 configuration lacks frozen byte binding')
    require(config['model_receipt'] == prior['model_receipt'] and config['model_dir'] == prior['model_dir'] and
            config.get('model_revision') == '0c351dd01ed87e9c1b53cbc748cba10e6187ff3b' and
            sha(config['model_receipt']['path']) == config['model_receipt']['sha256'], 'source spatial base receipt differs')
    require(read(HERE / 'config.json')['source_color_repair'] == config['source_color_repair'],
            'registered sample conversion changed')
    require(source == config['inputs'][scope] == prior['inputs'][scope] and
            sha(source['manifest']) == source['manifest_sha256'] and
            sha(source['registry']) == source['registry_sha256'], 'current scope inputs differ from B2')
    require(len(read(source['manifest'])['records']) == (8 if scope == 'nontest' else 426), 'scope source denominator differs')
    require(terminal.get('nontest_package_receipt_sha256') == sha(b2 / 'nontest_01/package.stage.json') and
            terminal.get('independent_validation_sha256') == sha(b2 / 'rematch_01/independent_validation.json'),
            'B2 completion internal receipt SHA differs')
    final = read(b2 / 'rematch_01/package.stage.json')
    require(terminal.get('videos') == 426 and terminal.get('crc_pass') is True and
            all(terminal.get(key) == final.get(key) for key in
                ('candidate', 'zip_bytes', 'zip_sha256', 'predictions_sha256', 'archive_names')),
            'B2 completion/package identity differs')
    measured_path = b2 / 'rematch_01/spatial.stage.json'
    measured = read(measured_path)
    require(measured.get('status') == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and measured.get('invalid') == 0 and
            measured.get('logical_parameters') == BASE_PARAMETERS and measured.get('time_adapter_enabled') is False,
            'B2 measured base authority incomplete')
    check_base_hash(measured.get('base_hash', {}), config)
    cache = b2 / (scope + '_01')
    require(all((cache / name).is_file() for name in CACHE_FILES), 'complete B2 cache lacks evidence')
    schedule, spatial = read(cache / 'schedule.stage.json'), read(cache / 'spatial.stage.json')
    package, independent = read(cache / 'package.stage.json'), read(cache / 'independent_validation.json')
    require(schedule.get('status') == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
            schedule.get('temporal_selection_used_for_boundaries') is False and schedule.get('max_gap') == 8,
            'source cache schedule algorithm differs')
    for name, key in (('field_frames.jsonl', 'field_frames_sha256'), ('field_shots.jsonl', 'shots_sha256'),
                      ('anchor_requests.jsonl', 'requests_sha256')):
        require(sha(cache / name) == schedule.get(key), 'source cache schedule SHA differs: ' + name)
    require(spatial.get('status') == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial.get('invalid') == 0 and
            spatial.get('logical_parameters') == BASE_PARAMETERS and spatial.get('time_adapter_enabled') is False and
            spatial.get('strict_units') == 'INTEGER_0_TO_1000' and spatial.get('failure_to_empty_conversions') == 0 and
            spatial.get('rows') == spatial.get('model_calls') == schedule.get('anchors'), 'source spatial receipt differs')
    if 'base_hash' in spatial:
        check_base_hash(spatial['base_hash'], config)
    else:
        bindings_path = b2 / 'cache_bindings.json'
        require(read(b2 / 'source_lock.json')['files'].get(str(bindings_path)) == sha(bindings_path),
                'historical reuse binding is not B2-frozen')
        binding = read(bindings_path)['scopes'][scope]
        origin = Path(binding['path'])
        require(spatial.get('reused_cache') is True and spatial.get('model_calls_this_B2_candidate') == 0 and
                spatial.get('source_cache') == str(origin) and spatial.get('cache_binding_sha256') == sha(bindings_path) and
                binding.get('cpu_eligible') is True and binding.get('spatial_eligible') is True and
                origin == Path(config['cpu_cache_root']) / (scope + '_01') and
                binding['manifest_sha256'] == source['manifest_sha256'] and
                binding['registry_sha256'] == source['registry_sha256'], 'historical spatial reuse lineage differs')
        require(set(binding['files']) == set(CACHE_FILES[:6]), 'historical spatial binding file set differs')
        for name, digest in binding['files'].items():
            require(sha(origin / name) == digest, 'historical source bytes changed: ' + name)
            if name.endswith('.jsonl'):
                require(sha(cache / name) == digest, 'B2 copied source bytes differ: ' + name)
        original = read(origin / 'spatial.stage.json')
        require(all(spatial.get(key) == value for key, value in original.items()), 'B2 historical spatial receipt changed')
    require(package.get('status') == 'PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX' and package.get('scope') == scope and
            package.get('video_records') == (8 if scope == 'nontest' else 426) and package.get('issues') == [] and
            package.get('prediction_frames') == schedule['selected_frames'] and package.get('source_lock_sha256') == lock_sha and
            package.get('complete_pipeline_parameters') == 8782459120 and
            all(package.get(key) == 0 for key in ('weak_roi_inputs_used', 'old_test_boxes_used', 'silent_fallbacks')),
            'B2 package status, denominator or issues differ')
    check_independent(independent, scope, schedule['selected_frames'])
    require(package.get('candidate') == str(cache / 'candidate_B2_8B.zip'), 'B2 candidate path differs')
    for name, key in (('predictions.jsonl', 'predictions_sha256'), ('provenance.jsonl', 'provenance_sha256'),
                      ('candidate_B2_8B.zip', 'zip_sha256')):
        require(sha(cache / name) == independent.get(key) and
                (key == 'provenance_sha256' or package.get(key) == independent[key]), 'B2 accepted artifact SHA differs: ' + name)
    archive_path = cache / 'candidate_B2_8B.zip'
    require(archive_path.stat().st_size == package['zip_bytes'] and
            package.get('archive_names') == independent.get('archive_names') == ['predictions.jsonl'], 'B2 archive receipt differs')
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                archive.read('predictions.jsonl') == (cache / 'predictions.jsonl').read_bytes(), 'B2 actual archive differs')
    return {'status': 'PASS_FROZEN_B2_SOURCE_FIELD_CACHE', 'cache': str(cache),
        'files': {name: sha(cache / name) for name in CACHE_FILES},
        'B2_completion_sha256': sha(b2 / 'completion.json'), 'B2_source_lock_sha256': lock_sha,
        'B2_config_sha256': sha(b2 / 'config.json'), 'manifest_sha256': source['manifest_sha256'],
        'clock_registry_sha256': source['registry_sha256'], 'model_receipt_sha256': config['model_receipt']['sha256'],
        'expected_base_sha256': config['expected_base_sha256'], 'base_parameters': config['base_parameters'],
        'B2_measured_base_receipt_sha256': sha(measured_path), 'base_hash_measured_in_this_scope': 'base_hash' in spatial,
        'historical_cache_binding_sha256': spatial.get('cache_binding_sha256'),
        'time_adapter_enabled': False, 'temporal_reuse_permitted': False}


def helpers():
    import train_student as student
    student.helper_paths(RUN)
    import common as old
    import frame_contract as frames
    import production as source_production
    # These adapters belong only to this process/new recipe; frozen Z files are unchanged.
    source_production.select_frames = select_native_frames
    source_production.field_frames = native_field_frames
    from source_color import authorized_source, ColorNativeReader
    original_reader = source_production.OrdinalReader
    class RegisteredReader:
        def __init__(self, item, clock):
            self.reader = ColorNativeReader(item, clock) if authorized_source(item['source_sha256']) else original_reader(item, clock)
        def get(self, index): return self.reader.get(index)
        def close(self): return self.reader.close()
    source_production.OrdinalReader = RegisteredReader
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
            from native_segment_contract import native_segment_ranges
            for first, stop in native_segment_ranges(segments, points, start, end-start):
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
                window['window_duration_sec'] = end - start
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
    input_ref, manifest, clocks = old.inputs(scope)
    require(read(out / 'temporal.stage.json')['status'] == 'PASS_TEMPORAL_EXECUTION', 'temporal phase did not pass')
    selected = select_native_frames(manifest, rows(out / 'temporal.jsonl'), clocks)
    cache = RUN / 'b_score_aligned_package_v4' / (scope + '_01')
    freeze_path = HERE / 'cache_01' / (scope + '.json')
    usable = freeze_path.is_file()
    if selected and usable:
        freeze = read(freeze_path)
        evidence = b2_cache_evidence(scope, input_ref)
        require({key: value for key, value in freeze.items() if key != 'utc'} == evidence,
                'spatial cache freeze receipt or current input/base/completion binding differs')
        source_schedule = read(cache / 'schedule.stage.json')
        require(source_schedule['status'] == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
                source_schedule['temporal_selection_used_for_boundaries'] is False, 'space cache depends on Z time decisions')
        require(read(cache / 'spatial.stage.json')['logical_parameters'] == 8767123696 and
                read(cache / 'spatial.stage.json')['time_adapter_enabled'] is False, 'space cache model differs')
        for name, key in (('field_frames.jsonl', 'field_frames_sha256'),
                          ('field_shots.jsonl', 'shots_sha256'), ('anchor_requests.jsonl', 'requests_sha256')):
            require(sha(cache / name) == source_schedule[key], 'source field cache bytes changed')
        field = rows(cache / 'field_frames.jsonl')
        desired = source.field_frames(manifest, clocks)
        wanted = {(r['video_id'], r['source_frame']) for r in desired}
        require({(r['video_id'], r['source_frame']) for r in field} == wanted and
                len(field) == len(wanted) == source_schedule['field_frames'] and field == desired,
                'B2 cached native field differs from current source algorithm')
        outputs = rows(cache / 'anchor_output.jsonl'); requests = rows(cache / 'anchor_requests.jsonl')
        from field_contract import build_field_requests
        require(build_field_requests(field, rows(cache / 'field_shots.jsonl'), 8) == requests, 'B2 source cache requests differ from current field algorithm')
        require(len(outputs) == len(requests) == read(cache / 'spatial.stage.json')['rows'] and
                all(r['status'] == 'MODEL_OK' and r.get('used_fallback') is False for r in outputs),
                'cached source spatial inference incomplete')
        for request, output in zip(requests, outputs):
            require(request['anchor_request_sha256'] == output['anchor_request_sha256'] and
                    request['expected_pixel_sha256'] == output['decoded_pixel_sha256'] and
                    request['video_id'] == output['video_id'] and request['source_frame'] == output['source_frame'],
                    'cached anchor identity changed')
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
             'utc': utc(), 'frozen_cache_receipt_sha256': sha(freeze_path),
             'B2_completion_sha256': freeze['B2_completion_sha256'],
             'manifest_sha256': input_ref['manifest_sha256'], 'clock_registry_sha256': input_ref['registry_sha256'],
             'files': {name: sha(out / name) for name in
             ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl')}}, fresh=True)
    else:
        # A failed or incomplete old cache is never silently accepted.
        source.scheduling(scope, out)


def verify_spatial_base(model, config):
    import torch
    from verify_saved_smoke import canonical_frozen_hash
    require(not any('lora_' in name for name, _ in model.named_parameters()), 'space base unexpectedly contains an adapter')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    value = canonical_frozen_hash(model, torch)
    check_base_hash(value, config)
    return value


def spatial_with_base_identity(source, scope, out, config):
    """Keep the frozen inference algorithm; verify its loaded model before any prediction."""
    original_load, original_write = source.load, source.write
    measured = {}
    constructors = []
    def bound_load(path, name):
        module = original_load(path, name)
        if Path(path) == source.HERE / 'spatial_baseline.py' and name == 'next_strict_spatial_baseline':
            constructor = module.Qwen3VL
            constructors.append((module, constructor))
            def bound_constructor(*args, **kwargs):
                require(args and str(args[0]) == config['model_dir'], 'spatial load model path differs')
                wrapper = constructor(*args, **kwargs)
                measured['base_hash'] = verify_spatial_base(wrapper.model, config)
                return wrapper
            module.Qwen3VL = bound_constructor
        return module
    def bound_write(path, value):
        if Path(path) == Path(out) / 'spatial.stage.json' and value.get('status') != 'PASS_EMPTY_SPACE_NO_MODEL_CALL':
            require('base_hash' in measured, 'spatial execution lacks actual base byte identity')
            value = dict(value, base_hash=measured['base_hash'])
        original_write(path, value)
    source.load, source.write = bound_load, bound_write
    try:
        source.spatial(scope, out)
    finally:
        source.load, source.write = original_load, original_write
        for module, constructor in constructors:
            module.Qwen3VL = constructor


def spatial(scope, out):
    verify()
    _, old, _, source = helpers()
    out = Path(out)
    require(not (out / 'spatial.stage.json').exists(), 'spatial phase already completed')
    input_ref, _, _ = old.inputs(scope)
    evidence = b2_cache_evidence(scope, input_ref)
    frozen = read(HERE / 'cache_01' / (scope + '.json'))
    require({key: value for key, value in frozen.items() if key != 'utc'} == evidence,
            'fresh spatial base authority or input binding differs')
    spatial_with_base_identity(source, scope, out, read(RUN / 'b_score_aligned_package_v4/config.json'))


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
    check_independent(independent, scope, len(selected))
    require(independent.get('predictions_sha256') == sha(out / 'predictions.jsonl') and
            independent.get('provenance_sha256') == sha(out / 'provenance.jsonl') and
            independent.get('zip_sha256') == sha(pending), 'independent accepted artifact SHA differs')
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
