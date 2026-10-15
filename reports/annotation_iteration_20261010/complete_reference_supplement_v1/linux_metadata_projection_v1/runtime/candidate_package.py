"""Exact original spatial-field reuse and independent final 426 ZIP acceptance."""
from bisect import bisect_left
from fractions import Fraction as F
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from common import bound, read, require, save, sha, verify_lock
import candidate_support as cs


STRICT_CHECKS = frozenset(('strict_loader_ok', 'video_record_set_exact', 'selected_key_set_exact',
    'ratio_fields_exact', 'frames_sorted', 'provenance_key_set_exact', 'provenance_boxes_match_predictions',
    'provenance_all_legal', 'provenance_sources_allowed', 'archive_single_file', 'archive_roundtrip_exact'))


def accepted_replay(prepared, path, expected):
    require(sha(path) == expected, 'independent candidate replay SHA differs')
    r = read(path); cs.same_binding(r, prepared)
    ep, engine = cs.validate_engine(prepared)
    require(Path(path).resolve() == Path(prepared['contract']['config']['candidate_output_dir']).resolve()/'independent_temporal_replay.json' and
        r['status'] == 'PASS_ALL_521_FRESH_FINAL_TEMPORAL_INDEPENDENT_CPU_REPLAY' and
        r['attempts_reconstructed'] == 521 and r['records'] == 426 and r['new_model_calls'] == 0 and
        r['new_optimizer_updates'] == 0 and r['CUDA_initialized'] is False and r['first_successful_CPU_replay_reused'] is True and
        r['engine_receipt'] == cs.ref(ep), 'independent full 521 replay absent')
    require(len(r['attempts']) == 521 and [a['ordinal'] for a in r['attempts']] == list(range(521)), 'replay order/denominator differs')
    for a, e in zip(r['attempts'], engine['attempts']):
        require(all(a[k] == e[k] for k in ('input', 'raw', 'done')) and
            a['actual_native_processor_tensors_equal'] is True and a['actual_token_grammar_parser_native_equal'] is True,
            'independent CPU input/token/parser evidence differs')
        for k in ('input', 'raw', 'done'):
            bound(a[k])
        d = read(bound(a['done']))
        require(a['result'] == {k: d[k] for k in ('status', 'output_valid', 'parsed_segments', 'native_frame_ranges', 'parse_warnings')},
            'CPU replay result differs from bound actual done')
    return r, engine


def selected_frames(prepared, replay):
    """Registered116 BW exact /405 original float mapping; no time box labels."""
    metadata = {m['video_id']: m for m in prepared['manifest']['records']}
    chosen = set()
    for a, accepted in zip(prepared['attempts'], replay['attempts']):
        ranges = []
        for left, right in accepted['result']['parsed_segments']:
            x, y = F(left), F(right); duration = cs.duration(a)
            duration = duration if isinstance(duration, F) else F(str(duration))
            require(0 <= x < y <= duration, 'CPU accepted endpoint outside exact domain')
            if a.get('changed', True):
                points = list(map(F, a['eligible_points']))
                first = bisect_left(points, F(a['raw_start'])+x)
                stop = bisect_left(points, F(a['raw_start'])+y)
            else:
                points = [float(F(t)) for t in a['eligible_points']]
                # Identical to the original native_segment_ranges mapping:
                # original float window start, parsed float endpoint rendered
                # as str, then float comparison to actual source PTS.
                start = F(str(a['window']['window_pts_start_sec']))
                first = bisect_left(points, float(start+F(str(float(x)))))
                stop = bisect_left(points, float(start+F(str(float(y)))))
            require(0 <= first < stop <= len(points), 'CPU accepted segment has no registered native frame')
            ranges.append([first, stop])
            for ordinal in range(a['first_ordinal']+first, a['first_ordinal']+stop):
                chosen.add((a['video_id'], ordinal))
        require(ranges == accepted['result']['native_frame_ranges'] and
                (accepted['result']['status'] == 'LEGAL_EMPTY') == (not ranges), 'CPU native selection differs')
    selected = []
    for vid, ordinal in sorted(chosen):
        m = metadata[vid]
        selected.append(dict(video_id=vid, source_frame=ordinal, source_path=m['source_path'],
            source_width=m['width'], source_height=m['height'], source_n_frames=m['n_frames'],
            fps=m['fps_num']/m['fps_den'], target_ratio_wh=m['targetRatioWH']))
    return selected


def exact_field(prepared):
    space = prepared['spec']['space']
    field_frames = cs.rows(bound(space['field_frames']))
    expected = []
    for m in prepared['manifest']['records']:
        clock = prepared['clocks'][m['video_id']]
        # This deliberately reproduces the frozen field domain, whose source
        # frames and shot boundaries predate every candidate temporal answer.
        pts = [float(t) for t in clock['pts']]
        first, stop = bisect_left(pts, m['scope_start_sec']), bisect_left(pts, m['scope_end_sec'])
        for ordinal in range(first, stop):
            expected.append(dict(video_id=m['video_id'], source_frame=ordinal, source_path=m['source_path'],
                source_width=m['width'], source_height=m['height'], source_n_frames=m['n_frames'],
                fps=m['fps_num']/m['fps_den'], target_ratio_wh=m['targetRatioWH']))
    require(field_frames == expected, 'original time-independent full field native domain differs')
    shots = cs.rows(bound(space['field_shots'])); requests = cs.rows(bound(space['anchor_requests']))
    outputs = cs.rows(bound(space['anchor_output']))
    require(len(requests) == len(outputs) == 31295 and
        prepared['modules']['field'].build_field_requests(field_frames, shots, 8) == requests,
        'original full-field max-gap8 31295 anchors differ')
    return shots, requests, outputs


def strict_validate(prepared, out, archive):
    run = Path(prepared['contract']['config']['historical_run_root'])
    report = out/'independent_strict_validation.json'
    require(not report.exists(), 'successful strict validation must not repeat')
    command = [sys.executable, '-B', str(run/'baseline_a_pts_v1/vendor/independent_validate.py'),
        '--strict-loader-root', prepared['spec']['strict_loader_root'], '--metadata', str(out/'metadata.json'),
        '--selected', str(out/'selected_frames.jsonl'), '--predictions', str(out/'predictions.jsonl'),
        '--provenance', str(out/'crop_provenance.jsonl'), '--zip', str(archive), '--report', str(report)]
    with (out/'strict_validation.log').open('x', encoding='utf-8') as stream:
        subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
    r = read(report)
    require(r['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and set(r['checks']) == STRICT_CHECKS and
        all(value is True for value in r['checks'].values()) and r['video_records'] == 426 and
        r['missing'] == r['extra'] == r['duplicate_frames'] == 0, 'independent 11strict failed')
    return report


def assemble(prepared, args):
    out = Path(prepared['contract']['config']['candidate_output_dir'])
    replay, engine = accepted_replay(prepared, args.replay_receipt, args.expected_replay_receipt)
    require(not (out/'package_start.json').exists() and not (out/'completion.json').exists(),
        'candidate package requires fresh single attempt')
    save(out/'package_start.json', dict(binding=prepared['binding'], utc=cs.utc(),
        replay_receipt=cs.ref(args.replay_receipt), new_spatial_model_calls=0))
    try:
        selected = selected_frames(prepared, replay)
        shots, requests, outputs = exact_field(prepared)
        m = prepared['modules']; projected = m['frames'].legacy_manifest(prepared['manifest'])
        predictions, provenance = m['field'].compose_from_field(projected, selected, shots, requests, outputs)
        details = m['package'].validate_predictions(projected, predictions, m['package'].keyset(selected), provenance)
        require(details['video_records'] == 426, 'all 426 official rows required including legal empty')
        cs.write_rows(out/'selected_frames.jsonl', selected)
        cs.write_rows(out/'predictions.jsonl', predictions)
        cs.write_rows(out/'crop_provenance.jsonl', provenance)
        save(out/'metadata.json', dict(records=prepared['manifest']['records'], errors=[]))
        archive = out/('candidate_FIXED_SILVER_426_'+prepared['training']['final_adapter_sha256'][:16]+'.zip')
        package = m['package'].package(out/'predictions.jsonl', archive)
        strict = strict_validate(prepared, out, archive)
        save(out/'package_manifest.json', dict(binding=prepared['binding'], records=426,
            replay_receipt=cs.ref(args.replay_receipt), engine_receipt=cs.ref(out/'engine_receipt.json'),
            selected=cs.ref(out/'selected_frames.jsonl'), predictions=cs.ref(out/'predictions.jsonl'),
            provenance=cs.ref(out/'crop_provenance.jsonl'), metadata=cs.ref(out/'metadata.json'),
            archive=cs.ref(archive), strict_validation=cs.ref(strict), spatial_source=prepared['spec']['space'],
            original_spatial_cost_preserved=True, new_spatial_model_calls=0, **package))
        final_receipt = out/'independent_final_zip_acceptance.json'
        command = [sys.executable, '-B', str(Path(__file__).resolve())]+cs.cli_args(args)
        command += ['--replay-receipt', args.replay_receipt, '--expected-replay-receipt', args.expected_replay_receipt,
                    '--verify-final-only', '--output', str(final_receipt)]
        with (out/'independent_final_zip_acceptance.log').open('x', encoding='utf-8') as stream:
            subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        accepted = read(final_receipt); cs.same_binding(accepted, prepared)
        require(accepted['status'] == 'PASS_INDEPENDENT_FINAL_426_ZIP_AND_FRESH_ADAPTER' and
            accepted['all_11_strict_checks_passed'] is True and accepted['archive'] == cs.ref(archive),
            'independent final ZIP acceptance absent')
        verify_lock(prepared['contract']['lock_path'], prepared['contract']['lock_sha'])
        require(sha(prepared['final']/'adapter_model.safetensors') == prepared['training']['final_adapter_sha256'],
                'fresh final adapter changed before completion')
        report = dict(status='PASS_COMPLETE_FIXED_SILVER_426_CANDIDATE_ON_LINUX', utc=cs.utc(),
            binding=prepared['binding'], records=426, fresh_temporal_model_calls=521,
            final_adapter_sha256=prepared['training']['final_adapter_sha256'], all_11_strict_checks_passed=True,
            candidate=str(archive), zip_bytes=archive.stat().st_size, zip_sha256=sha(archive),
            independent_final_acceptance=cs.ref(final_receipt), independent_strict_validation=cs.ref(strict),
            independent_temporal_replay=cs.ref(args.replay_receipt), new_spatial_model_calls=0,
            original_spatial_model_calls=31295, original_spatial_cost_preserved=True,
            original_spatial_wall_seconds=prepared['space_stage']['wall_seconds'],
            old_temporal_outputs_reused=0, new_optimizer_updates=0, uploaded=False, official_score=None)
        save(out/'completion.json', report)
        return report
    except BaseException as exc:
        cs.failure(out/'package_failure.json', exc)
        raise


def verify_final(prepared, args):
    """Separate CPU process reopens actual final ZIP and all admission bytes."""
    out = Path(prepared['contract']['config']['candidate_output_dir']).resolve()
    target = Path(args.output).resolve()
    require(target == out/'independent_final_zip_acceptance.json' and not target.exists() and
        not (out/'completion.json').exists(), 'fresh final independent ZIP receipt required')
    replay, unused = accepted_replay(prepared, args.replay_receipt, args.expected_replay_receipt)
    pm = read(out/'package_manifest.json'); cs.same_binding(pm, prepared)
    require(pm['records'] == 426 and pm['replay_receipt'] == cs.ref(args.replay_receipt) and
        pm['engine_receipt'] == cs.ref(out/'engine_receipt.json') and pm['new_spatial_model_calls'] == 0 and
        pm['original_spatial_cost_preserved'] is True and pm['spatial_source'] == prepared['spec']['space'],
        'final package evidence differs')
    for key, name in (('selected', 'selected_frames.jsonl'), ('predictions', 'predictions.jsonl'),
                      ('provenance', 'crop_provenance.jsonl'), ('metadata', 'metadata.json'),
                      ('strict_validation', 'independent_strict_validation.json')):
        require(bound(pm[key]) == out/name, 'foreign final package file')
    archive = bound(pm['archive'])
    require(archive.parent == out and archive.name == 'candidate_FIXED_SILVER_426_'+prepared['training']['final_adapter_sha256'][:16]+'.zip',
            'archive does not identify admitted fresh final adapter')
    selected = selected_frames(prepared, replay)
    require(cs.rows(bound(pm['selected'])) == selected, 'final selected exact native membership changed')
    # Independently recompute full-field interpolation and its selected output;
    # this performs no model, decoder or repeated native processor replay.
    shots, requests, outputs = exact_field(prepared); m = prepared['modules']
    projected = m['frames'].legacy_manifest(prepared['manifest'])
    predictions, provenance = m['field'].compose_from_field(projected, selected, shots, requests, outputs)
    require(cs.rows(bound(pm['predictions'])) == predictions and cs.rows(bound(pm['provenance'])) == provenance,
            'independent original field composition differs from actual package')
    m['package'].validate_predictions(projected, predictions, m['package'].keyset(selected), provenance)
    strict = read(bound(pm['strict_validation']))
    require(strict['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and set(strict['checks']) == STRICT_CHECKS and
        all(x is True for x in strict['checks'].values()) and strict['video_records'] == 426 and
        strict['expected_frames'] == strict['prediction_frames'] == len(selected) and
        strict['zip_sha256'] == sha(archive) and strict['predictions_sha256'] == sha(bound(pm['predictions'])) and
        strict['provenance_sha256'] == sha(bound(pm['provenance'])) and
        strict['missing'] == strict['extra'] == strict['duplicate_frames'] == 0, 'final independent 11strict binding differs')
    with zipfile.ZipFile(archive) as z:
        require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None and
            z.read('predictions.jsonl') == bound(pm['predictions']).read_bytes(), 'actual final ZIP CRC/content mismatch')
    require(pm['zip_sha256'] == sha(archive) and pm['zip_bytes'] == archive.stat().st_size and
        sha(prepared['final']/'adapter_model.safetensors') == prepared['training']['final_adapter_sha256'],
        'actual final ZIP/adapter SHA changed')
    verify_lock(prepared['contract']['lock_path'], prepared['contract']['lock_sha'])
    r = dict(status='PASS_INDEPENDENT_FINAL_426_ZIP_AND_FRESH_ADAPTER', utc=cs.utc(), binding=prepared['binding'],
        records=426, archive=cs.ref(archive), zip_bytes=archive.stat().st_size,
        final_adapter_sha256=prepared['training']['final_adapter_sha256'], all_11_strict_checks_passed=True,
        independent_strict_validation=cs.ref(bound(pm['strict_validation'])), package_manifest=cs.ref(out/'package_manifest.json'),
        new_model_calls=0, new_native_decodes=0, new_optimizer_updates=0)
    save(target, r)
    return r


def main():
    p = cs.parser()
    p.add_argument('--replay-receipt', required=True); p.add_argument('--expected-replay-receipt', required=True)
    p.add_argument('--verify-final-only', action='store_true'); p.add_argument('--output')
    args = p.parse_args(); prepared = cs.entry(args, 'candidate_package')
    report = verify_final(prepared, args) if args.verify_final_only else assemble(prepared, args)
    print(__import__('json').dumps({k: report[k] for k in ('status', 'records')}))


if __name__ == '__main__':
    main()
