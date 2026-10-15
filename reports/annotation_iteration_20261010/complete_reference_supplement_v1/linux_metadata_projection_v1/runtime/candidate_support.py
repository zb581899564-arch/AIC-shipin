"""Candidate-only bindings and exact selection; import has no model/media IO."""
import argparse
from bisect import bisect_left
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys

from common import admit, bound, helpers, load, read, require, save, sha, BASE_SHA, INITIAL_SHA
from evaluate import validate_final

DEPENDENCIES = (
    'balanced_two_window_risk_v3/bw_common.py', 'balanced_two_window_risk_v3/bw_native.py',
    'teacher_student_autopilot_v14/native_segment_contract.py',
    'b_score_aligned_package_v4/package_contract.py', 'b_score_aligned_package_v4/frame_contract.py',
    'b_score_aligned_package_v4/field_contract.py',
    'baseline_a_pts_v1/vendor/independent_validate.py',
)
FIXED_INPUT_SHAS = {
    'plan': '6ac37ae102836fdf2a44cbf676129a2678019fda34f81874601fe1c5dc055ae7',
    'changed_cpu_acceptance': 'cc6117d720ad8c472ed60c48f79ff22640dbf54395242f6c737a38bf5b342fdf',
    'manifest': 'ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8',
    'clock_registry': '1058aba02e5e959bc8e4842cbde0eadced192a8201d5c833ae50a7c0aac07909',
}
FIXED_SPACE_SHAS = {
    'field_frames': '17ba37aadc4cf705e1ff95a78a58d8befcab9e34f7132ef0775f1ed1df0d8bca',
    'field_shots': '8e81df10c685527145069cd9c65316ab6341c9da7d6e39bb282ed6c60ce12f1e',
    'anchor_requests': '9cb7c4e36597dc8ae723ac3b686b2c3b1f04d5982503478fdf19ee72b18c4798',
    'anchor_output': '8f83cd967d7d1f95243ac4ae3cddc7fdb78abb3d4842a78f81f6b187fb1562ab',
    'schedule_stage': '4c5ad1daf0817e252eca7dc484eb627f9f6ce3933afdd68484883834f32d4603',
    'spatial_stage': 'd71d74607cb784f661af3b43b168a9e3770120633686bd759aa7717015876700',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def rows(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_rows(path, values):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        for row in values:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n')


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def parser():
    p = argparse.ArgumentParser()
    for name in ('config', 'lock', 'expected-lock', 'final-receipt',
                 'expected-final-receipt', 'quality-receipt', 'expected-quality-receipt'):
        p.add_argument('--'+name, required=True)
    return p


def cli_args(args):
    values = []
    for name in ('config', 'lock', 'expected_lock', 'final_receipt',
                 'expected_final_receipt', 'quality_receipt', 'expected_quality_receipt'):
        values.extend(['--'+name.replace('_', '-'), getattr(args, name)])
    return values


def quality(contract, args, final_receipt):
    require(sha(args.quality_receipt) == args.expected_quality_receipt, 'independent quality SHA differs')
    q = read(args.quality_receipt)
    require(Path(args.quality_receipt).resolve() == Path(contract['config']['evaluate_output_dir']).resolve()/'independent_quality_receipt.json',
        'independent quality receipt must belong to this final evaluation')
    require(q['status'] == 'PASS_INDEPENDENT_CPU_FINAL_ONLY_EVALUATION_RECONSTRUCTION' and
        q['scientific_status'] == 'PASS_FIXED_SILVER_QUALITY_GATE' and q['quality_gate_passed'] is True and
        q['model_calls_reconstructed'] == 24 and q['new_model_calls'] == 0 and
        q['new_optimizer_updates'] == 0 and q['new_native_decodes'] == 0 and
        q['actual_completed_CPU_inputs_referenced'] is True and
        q['config_sha256'] == contract['config_sha'] and q['lock_sha256'] == contract['lock_sha'] and
        q['final_adapter_sha256'] == final_receipt['final_adapter_sha256'], 'independent quality admission absent')
    require(q['training_receipt'] == ref(args.final_receipt), 'quality/final receipt differs')
    e = read(bound(q['evaluation_receipt']))
    require(bound(q['evaluation_receipt']) == Path(contract['config']['evaluate_output_dir']).resolve()/'evaluation_receipt.json',
        'quality cites a foreign evaluation')
    require(e['status'] == 'PASS_FINAL_ONLY_EVALUATION_ENGINEERING' and e['model_calls'] == 24 and
        e['quality_gate_passed'] is True and e['lock_sha256'] == contract['lock_sha'] and
        e['config_sha256'] == contract['config_sha'] and
        e['final_training_receipt_sha256'] == args.expected_final_receipt and
        e['scientific_gate_sha256'] == sha(Path(contract['config']['evaluate_output_dir'])/'scientific_gate.json'),
        'quality/evaluation binding differs')
    require(q['scientific_gate'] == read(Path(contract['config']['evaluate_output_dir'])/'scientific_gate.json'),
        'independent scientific gate differs')
    bindings = q['bindings']
    expected = {(k, arm) for k in contract['config']['final_only_evaluation_window_ids']
                for arm in ('original_B', 'new_final')}
    require(len(bindings) == 24 and {(b['window_id'], b['arm']) for b in bindings} == expected,
        'independent quality 24 identities differ')
    for b in bindings:
        for key in ('done', 'raw', 'completed_input_receipt'):
            bound(b[key])
        require(b['adapter_sha256'] == (INITIAL_SHA if b['arm'] == 'original_B' else q['final_adapter_sha256']),
            'independent arm adapter differs')
    return q


def locked_ref(contract, reference):
    p = bound(reference)
    require(contract['lock']['files'].get(str(p)) == reference['sha256'], 'candidate input absent from lock: '+str(p))
    return p


def scientific_modules(contract):
    run = Path(contract['config']['historical_run_root'])
    student, changed_video, sft, smoke = helpers(contract['config'])
    load(run/'balanced_two_window_risk_v3/bw_common.py', 'bw_common')
    native = load(run/'balanced_two_window_risk_v3/bw_native.py', 'candidate_original_balanced_native')
    ordinary_video = load(run/'next_round_v1/video_contract.py', 'candidate_original_unmodified_video')
    load(run/'teacher_student_autopilot_v14/native_segment_contract.py', 'native_segment_contract')
    package = load(run/'b_score_aligned_package_v4/package_contract.py', 'package_contract')
    frames = load(run/'b_score_aligned_package_v4/frame_contract.py', 'candidate_source_clock_contract')
    field = load(run/'b_score_aligned_package_v4/field_contract.py', 'candidate_source_field_contract')
    return dict(student=student, changed_video=changed_video, ordinary_video=ordinary_video,
                native=native, sft=sft, smoke=smoke, package=package, frames=frames, field=field)


def prepare(contract):
    spec_path = locked_ref(contract, contract['config']['candidate_contract'])
    spec = read(spec_path)
    require(spec['schema'] == 'FIXED_SILVER_426_FRESH_TEMPORAL_CANDIDATE_V1', 'candidate schema differs')
    require(set(spec) == {'schema', 'plan', 'manifest', 'clock_registry', 'changed_cpu_acceptance', 'space', 'strict_loader_root'} and
        set(spec['space']) == set(FIXED_SPACE_SHAS), 'candidate contract field whitelist differs')
    for name, expected in FIXED_INPUT_SHAS.items():
        require(spec[name]['sha256'] == expected, 'fixed historical candidate input differs: '+name)
    for name, expected in FIXED_SPACE_SHAS.items():
        require(spec['space'][name]['sha256'] == expected, 'original spatial field differs: '+name)
    run = Path(contract['config']['historical_run_root']).resolve()
    for name in DEPENDENCIES:
        p = (run/name).resolve(strict=True)
        require(contract['lock']['files'].get(str(p)) == sha(p), 'candidate scientific dependency absent: '+name)
    strict_root = Path(spec['strict_loader_root']).resolve(strict=True)
    require(strict_root == (run/'baseline_a_pts_v1/vendor/frozen_strict_loader').resolve(strict=True),
            'foreign strict loader')
    for p in strict_root.rglob('*'):
        if p.is_file():
            require(contract['lock']['files'].get(str(p)) == sha(p), 'strict loader file absent from lock')
    modules = scientific_modules(contract)
    manifest = read(locked_ref(contract, spec['manifest']))
    registry = locked_ref(contract, spec['clock_registry'])
    for r in read(registry)['records']:
        locked_ref(contract, r['clock_arrays'])
    clocks = modules['frames'].load_clocks(manifest, str(registry), spec['clock_registry']['sha256'])
    plan = read(locked_ref(contract, spec['plan']))
    require(plan['scope'] == 'rematch' and plan['records'] == 426 and plan['windows'] == 521 and
            len(plan['jobs']) == 426 and plan['input_ref'] == dict(manifest=spec['manifest']['path'],
                manifest_sha256=spec['manifest']['sha256'], registry=spec['clock_registry']['path'],
                registry_sha256=spec['clock_registry']['sha256']), '426/521 native plan binding differs')
    metadata = {r['video_id']: r for r in manifest['records']}
    require(len(metadata) == 426 and {j['video_id'] for j in plan['jobs']} == set(metadata), 'candidate source identities differ')
    attempts = []; changed = 0
    for job in plan['jobs']:
        vid = job['video_id']; clock = clocks[vid]; item = metadata[vid]
        require(job['metadata'] == item, 'plan source metadata differs')
        source = Path(item['source_path']).resolve(strict=True)
        require(contract['lock']['files'].get(str(source)) == item['source_sha256'] and sha(source) == item['source_sha256'],
                'candidate source media absent/changed')
        original = [(p.get('base_start_sec', p['start_sec']), p.get('base_end_sec', p['end_sec'])) for p in job['windows']]
        require(original == modules['frames'].window_schedule(item, manifest['kind'], clock),
                'historical base schedule differs')
        schedule = modules['native'].balanced_schedule(original)
        require(len(schedule) == len(job['windows']), 'candidate window denominator differs')
        origin = F(clock['arrays']['raw_first_pts_ticks'])*F(clock['arrays']['raw_time_base'])
        points = [origin+t for t in clock['pts']]
        for ix, (part, (a, b)) in enumerate(zip(job['windows'], schedule)):
            w = part['window']; base = part['base_window']; is_changed = w != base
            changed += int(is_changed)
            require(part['clock_record_sha256'] == clock['clock_record_sha256'] and
                part['clock_branch'] == clock['branch'] and part['raw_source_pts_origin_sec'] == float(origin),
                'plan/clock authority differs')
            require(float(a) == part['start_sec'] and float(b) == part['end_sec'], 'balanced schedule differs')
            raw_a, raw_b = origin+a, origin+b
            if is_changed:
                first, stop = bisect_left(points, raw_a), bisect_left(points, raw_b)
            else:
                # Keep the unchanged registered float boundary/sampling
                # protocol. Exact clock values verify each real ordinal;
                # they never silently reschedule an original window.
                raw_a, raw_b = F(str(w['window_pts_start_sec'])), F(str(w['window_pts_end_exclusive_sec']))
                first = w['planned_source_frame_ordinals'][0]
                stop = first+w['eligible_source_frame_count']
                float_points = list(map(float, points))
                require((first, stop) == (bisect_left(float_points, w['window_pts_start_sec']),
                    bisect_left(float_points, w['window_pts_end_exclusive_sec'])), 'unchanged original eligible ordinals differ')
            ids = modules['native'].floor_indices(first, stop)
            require(w['source_path'] == item['source_path'] and w['source_sha256'] == item['source_sha256'] and
                w['source_total_frames'] == item['n_frames'] and
                w['planned_source_frame_ordinals'] == ids and w['planned_actual_pts_sec'] == [float(points[i]) for i in ids],
                'actual native floor64 input differs')
            if is_changed:
                require(w['sampling_recipe'] == 'EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64' and
                    w['planned_exact_pts'] == [str(points[i]) for i in ids] and
                    w['eligible_exact_pts'] == [str(t) for t in points[first:stop]] and
                    F(w['exact_raw_start']) == raw_a and F(w['exact_raw_end']) == raw_b and
                    F(w['exact_normalized_start']) == a and F(w['exact_normalized_end']) == b, 'changed exact domain differs')
            else:
                require(w == base, 'unchanged window must retain full protocol')
            require(float(raw_a) == w['window_pts_start_sec'] and float(raw_b) == w['window_pts_end_exclusive_sec'],
                    'window exact/processor domain differs')
            if is_changed:
                require(float(b-a) == w['window_duration_sec'], 'balanced exact duration differs')
            attempts.append(dict(video_id=vid, index=ix, window=w, changed=is_changed,
                raw_start=str(raw_a), raw_end=str(raw_b), eligible_points=[str(t) for t in points[first:stop]],
                first_ordinal=first, stop_ordinal=stop, ordinal=len(attempts)))
    require(len(attempts) == 521 and changed == 116, 'fresh 521/changed116 denominator differs')
    require(len({a['window']['window_id'] for a in attempts}) == 521, 'candidate window IDs duplicated')
    proof_rows = [p for p in read(locked_ref(contract, spec['changed_cpu_acceptance']))['proofs'] if p['scope'] == 'rematch']
    proofs = {(p['video_id'], p['index']): p for p in proof_rows}
    require(len(proof_rows) == len(proofs) == 116, 'changed CPU proofs duplicated/missing')
    require(set(proofs) == {(a['video_id'], a['index']) for a in attempts if a['changed']}, 'changed CPU proof set differs')
    for a in attempts:
        if a['changed']:
            require(proofs[(a['video_id'], a['index'])]['window'] == a['window'], 'changed input proof window differs')
    for key in ('field_frames', 'field_shots', 'anchor_requests', 'anchor_output', 'schedule_stage', 'spatial_stage'):
        locked_ref(contract, spec['space'][key])
    schedule_stage = read(bound(spec['space']['schedule_stage'])); spatial = read(bound(spec['space']['spatial_stage']))
    require(schedule_stage['status'] == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and schedule_stage['anchors'] == 31295 and
        schedule_stage['max_gap'] == 8 and schedule_stage['temporal_selection_used_for_boundaries'] is False and
        all(schedule_stage[k+'_sha256'] == spec['space'][k]['sha256'] for k in ('field_frames',)) and
        schedule_stage['shots_sha256'] == spec['space']['field_shots']['sha256'] and
        schedule_stage['requests_sha256'] == spec['space']['anchor_requests']['sha256'], 'time-independent field binding differs')
    require(spatial['status'] == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial['rows'] == 31295 and spatial['invalid'] == 0 and
        spatial['strict_units'] == 'INTEGER_0_TO_1000' and spatial['time_adapter_enabled'] is False and
        spatial['failure_to_empty_conversions'] == 0 and spatial['model_calls'] == 31295 and
        spatial['base_hash']['sha256'] == BASE_SHA and spatial['logical_parameters'] == 8767123696,
        'original spatial evidence differs')
    return dict(spec=spec, modules=modules, manifest=manifest, clocks=clocks,
                attempts=attempts, proofs=proofs, space_stage=spatial, spec_ref=ref(spec_path))


def entry(args, phase):
    contract = admit(args.config, args.lock, args.expected_lock, phase)
    final, training = validate_final(contract, args.final_receipt, args.expected_final_receipt)
    q = quality(contract, args, training)
    prepared = prepare(contract)
    prepared.update(contract=contract, final=final, training=training, quality=q,
        binding=dict(config_sha256=contract['config_sha'], lock_sha256=contract['lock_sha'],
            final_adapter_sha256=training['final_adapter_sha256'], final_receipt=ref(args.final_receipt),
            quality_receipt=ref(args.quality_receipt), candidate_contract=prepared['spec_ref']))
    return prepared


def tensor_signature(encoded):
    import torch
    return {k: dict(shape=list(v.shape), dtype=str(v.dtype),
        sha256=hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        for k, v in encoded.items() if torch.is_tensor(v)}


def duration(a):
    # Do not unify the registered405 float semantics with the116 BW Fraction
    # semantics. Both original parser and original grammar receive this value.
    return F(a['raw_end'])-F(a['raw_start']) if a.get('changed', True) else a['window']['window_duration_sec']


def encode(prepared, a, processor):
    import torch
    from contracts import EMPTY_PROMPT
    from exact_pts import exact_native_pts, verify_native_encoding
    from native_runtime import prompt
    modules = prepared['modules']; w = a['window']
    decoded = (modules['native'].decode_balanced_window(w) if a['changed'] else modules['student'].decode_window(w))
    arr, metadata, plan, evidence = decoded
    require(evidence['source_frame_ids'] == w['planned_source_frame_ordinals'] and
        evidence['actual_pts_sec'] == w['planned_actual_pts_sec'] and
        evidence['window_source_pts_sec'] == [float(F(t)) for t in a['eligible_points']],
        'actual full native processor input differs from clock')
    video = modules['changed_video'] if a['changed'] else modules['ordinary_video']
    with exact_native_pts(processor, plan, metadata['fps']) as native:
        encoded = video.encode(processor, text=[prompt(processor)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=modules['student'].VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    identity = dict(**evidence, native_processor_identity=native,
        **video.identity(processor, encoded, len(arr)), registered_prompt_sha256=digest(EMPTY_PROMPT))
    signature = tensor_signature(encoded)
    if a['changed']:
        proof = prepared['proofs'][(a['video_id'], a['index'])]
        require(proof['video_identity'] == identity and proof['vision_signature'] ==
            {k: v for k, v in signature.items() if k in ('pixel_values_videos', 'video_grid_thw')},
            'actual changed input differs from original accepted CPU evidence')
    return encoded, dict(video_identity=identity, encoded_signature=signature,
        window=w, attempt_identity={k: a[k] for k in ('video_id', 'index', 'ordinal', 'changed', 'raw_start', 'raw_end')})


def result(raw, a, evidence, balanced_native=None):
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    from objective import classify
    clip_duration = duration(a)
    parsed, errors, warnings = parse_segments(raw, clip_duration, allow_empty=True)
    require(parsed is not None and not errors, 'original temporal parser rejected: '+repr(errors))
    exact = classify(raw, clip_duration if isinstance(clip_duration, F) else F(str(clip_duration)))
    require(exact['status'] in ('MODEL_OK', 'LEGAL_EMPTY') and
        exact['parsed_segments'] == [[F(str(x)), F(str(y))] for x, y in parsed], 'exact/original parser differs')
    physical = [list(p) for p in native_segment_ranges(parsed, evidence['window_source_pts_sec'],
        a['window']['window_pts_start_sec'], clip_duration)]
    ranges = physical
    if a.get('changed', True):
        if balanced_native is not None:
            ranges = balanced_native.exact_ranges(parsed, a['window'])
        else:
            # Pure logic fixture path. Production always invokes the actual
            # frozen BW exact_ranges helper supplied by prepare().
            points = list(map(F, a['eligible_points'])); ranges = []
            for x, y in exact['parsed_segments']:
                first, stop = bisect_left(points, F(a['raw_start'])+x), bisect_left(points, F(a['raw_start'])+y)
                require(0 <= first < stop <= len(points), 'interval has no exact source frame')
                ranges.append([first, stop])
        require(physical == ranges, 'float/exact BW native segment membership differs')
    # The405 unchanged route keeps its original float-PTS realizability
    # authority. It is independently rebuilt; no new rational equality gate.
    return dict(status=exact['status'], output_valid=True, parsed_segments=[[str(x), str(y)] for x, y in exact['parsed_segments']],
                native_frame_ranges=ranges, parse_warnings=warnings)


def attempt_paths(out, ordinal):
    folder = Path(out)/'attempts'; stem = '%03d'%ordinal
    return tuple(folder/(stem+'.'+kind+'.json') for kind in ('input', 'raw', 'done'))


def same_binding(receipt, prepared):
    require(receipt['binding'] == prepared['binding'], 'candidate receipt admission binding differs')


def validate_engine(prepared):
    out = Path(prepared['contract']['config']['candidate_output_dir'])
    p = out/'engine_receipt.json'; r = read(p); same_binding(r, prepared)
    require(r['status'] == 'PASS_ALL_521_FRESH_FINAL_TEMPORAL_MODEL_CALLS' and r['records'] == 426 and
        r['fresh_temporal_model_calls'] == 521 and r['old_temporal_outputs_reused'] == 0 and
        r['new_spatial_model_calls'] == 0 and r['actual_loaded_final_tensor_equality_count'] == 288 and
        len(r['attempts']) == 521, 'fresh engine completion absent')
    require([x['ordinal'] for x in r['attempts']] == list(range(521)), 'engine receipt attempt order differs')
    for row in r['attempts']:
        for name in ('input', 'raw', 'done'):
            require(bound(row[name]) == attempt_paths(out, row['ordinal'])[('input', 'raw', 'done').index(name)].resolve(),
                'foreign attempt receipt')
    expected = {p.name for a in prepared['attempts'] for p in attempt_paths(out, a['ordinal'])}
    require({p.name for p in (out/'attempts').iterdir()} == expected,
            'candidate attempt files contain missing/extra/failure records')
    return p, r


def failure(path, exc):
    import traceback
    save(path, dict(status='STOP_CANDIDATE_ENGINEERING', utc=utc(), failure_type=type(exc).__name__,
        failure=str(exc), traceback=traceback.format_exc(), failure_converted_to_empty=False))
