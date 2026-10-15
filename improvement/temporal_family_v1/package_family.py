"""Prospective Linux-only renderer; requires actual production/risk admission.

This file performs no model call, source decoding, reference selection or
implicit production admission. Each candidate is published only once after
complete actual answer/replay evidence, distinctness and independent 11 checks.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile
from combine_events import ARMS, combine
from fractions import Fraction as F

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROOT = HOME/'twenty_hour_five_20261014_v1/temporal_family_package_v1'
PARAMETERS = 8782459120


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def save(path, value):
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush(); os.fsync(f.fileno())


def write(path, values):
    with Path(path).open('x', encoding='utf8') as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n')
        f.flush(); os.fsync(f.fileno())


def canonical(values):
    relevant = [{'video_id':v['video_id'], 'targetRatioWH':v['targetRatioWH'], 'predictions':v['predictions']}
                for v in sorted(values, key=lambda v: v['video_id'])]
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checked_inputs():
    require(sys.platform == 'linux' and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU packaging only')
    require(Path(__file__).resolve().parent == ROOT/'code', 'Independent fixed package code root')
    permit = read(ROOT/'package_admission.json')
    require(permit['status'] == 'PASS_COMPLETE_REAL_TEMPORAL_PRODUCTION_AND_EXPLICIT_RISK_PACKAGE_ADMISSION', 'No actual production/risk permission')
    require(permit['model_parameters'] == PARAMETERS and permit['old_scientific_failed_gates_changed'] is False and
            permit['known_severe_degradation_veto_passed'] is True and permit['test_labels_or_manual_edits_used'] is False,
            'Risk/science/model identity boundary')
    lock_path = ROOT/'source_package_lock.json'
    require(permit['source_package_lock_sha256'] == sha(lock_path), 'Frozen package/source lock changed')
    lock = read(lock_path)['files']
    required = {str(ROOT/n) for n in ['package_inputs.json', 'protocol.json', 'authorization.json', 'official_rule_check.json']}
    required |= {str(p.resolve()) for p in (ROOT/'code').glob('*.py')}
    dependency_roots = (RUN/'b_score_aligned_package_v4', RUN/'baseline_a_pts_v1')
    required |= {str(p.resolve()) for directory in dependency_roots for p in directory.glob('*.py')}
    required |= {str(p.resolve()) for p in (RUN/'baseline_a_pts_v1/vendor').glob('*.py')}
    required |= {str(p.resolve()) for p in (RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader').rglob('*.py')}
    require(required <= set(lock), 'Package code, protocol, authorization or current rule receipt not bound')
    for path, digest in lock.items():
        require(Path(path).resolve().is_relative_to(HOME) and sha(path) == digest, 'Frozen actual evidence changed '+path)
    inputs = read(ROOT/'package_inputs.json')
    def bound(name):
        ref = inputs[name]
        require(ref['path'] in lock and lock[ref['path']] == ref['sha256'], 'Actual artifact absent from complete source lock '+name)
        return Path(ref['path'])
    artifacts = {name:bound(name) for name in ['events', 'endpoints', 'verification', 'source_clocks', 'baseline_zip',
                                             'metadata', 'source_manifest', 'history', 'production_completion', 'development_selection']}
    for ref in inputs['source_field_files'].values():
        require(lock.get(ref['path']) == ref['sha256'], 'Original source field absent from frozen package lock')
    production = read(artifacts['production_completion'])
    for name in ['events', 'endpoints', 'verification', 'source_clocks']:
        require(production['accepted_export_refs'][name] == inputs[name], 'Package projection differs from actually accepted production export '+name)
    require(production['frozen_development_selection_ref'] == inputs['development_selection'], 'Production did not consume this frozen development selection')
    selection = read(artifacts['development_selection'])
    require(production['global_refiner_role'] == selection['global_refiner_role'] and
            production['global_VERIFY_role'] == selection['global_VERIFY_role'], 'Uniform frozen model activation roles changed')
    require(production['status'] == 'PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS' and
            production['engineering_failed_requests'] == 0 and production['missing_requests'] == 0 and
            production['physical_model_parameters'] == PARAMETERS and production['optimizer_updates'] == 0 and
            production['test_GT_or_annotation_read'] is False and production['native_clock_matches_original_full_PTS'] is True,
            'Incomplete actual production cannot be packaged')
    require(permit['production_completion_sha256'] == sha(artifacts['production_completion']), 'Actual production terminal binding')
    protocol = read(ROOT/'protocol.json')
    require(protocol['arms'] == list(ARMS) and protocol['original_length_padding_preserved'] is True and
            protocol['empty_source_guard'] == 'PRESERVE_ORIGINAL_D8_SOURCE_SELECTION' and protocol['test_content_or_leaderboard_parameter_selection'] is False,
            'Prospective family/format guard changed')
    return inputs, artifacts, permit, production


def main():
    inputs, paths, permit, production = checked_inputs()
    save(ROOT/'started.json', dict(pid=os.getpid(), utc=dt.datetime.now(dt.timezone.utc).isoformat(), new_model_calls=0))
    events, endpoints, verification, clocks = [read(paths[n]) for n in ['events', 'endpoints', 'verification', 'source_clocks']]
    require(len(events) == 665 and len(clocks) == 426, 'Frozen 426/665 source-event denominator')
    require(set(production['accepted_endpoint_request_ids']) == set(endpoints) and
            set(production['accepted_verification_event_ids']) == set(verification) and
            set(production['actual_source_ids']) == set(clocks), 'Actual complete request/source receipt identities')
    with zipfile.ZipFile(paths['baseline_zip']) as z:
        require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None, 'D8 original member/CRC')
        baseline = [json.loads(line) for line in z.read('predictions.jsonl').splitlines()]
    wanted = {(v['video_id'],p['frame']) for v in baseline for p in v['predictions']}
    require(len(baseline) == 426 and len(wanted) == 122050 and all(v['predictions'] for v in baseline), 'Actual protected D8 membership')
    baseline_boxes = {(v['video_id'],p['frame']):p['bboxes'] for v in baseline for p in v['predictions']}
    # Arithmetic baseline reconstruction uses synthetic KEEP constants only as
    # a deterministic code check, never as an alleged model call/proof.
    original = {e['event_id']+'.'+side:dict(event_id=e['event_id'], side=side, applied_decision='KEEP',
        original_endpoint_exact=e['original_interval_exact'][index], endpoint_exact=e['original_interval_exact'][index])
        for e in events for index,side in enumerate(('start','end'))}
    keep = {e['event_id']:dict(event_id=e['event_id'], decision='KEEP') for e in events}
    reconstructed = combine(events, original, keep, clocks)['BOTH']['selected_ordinals']
    require({(s,f) for s,fs in reconstructed.items() for f in fs} == wanted, 'D8 original endpoint padding/native predicate not exactly reproduced')
    combined = combine(events, endpoints, verification, clocks)
    metadata = read(paths['metadata']); meta = {v['video_id']:v for v in metadata['records']}
    source_manifest = read(paths['source_manifest'])
    source_records = {v['video_id']:v for v in source_manifest['records']}
    require(len(source_records) == len(source_manifest['records']) == 426 and set(source_records) == set(meta), 'Source manifest identities/duplicates')
    identity_fields = ('video_id','source_path','source_sha256','width','height','n_frames','fps_num','fps_den','targetRatioWH')
    require(all(all(source_records[k][field] == meta[k][field] for field in identity_fields) for k in meta), 'Spatial manifest source identity/geometry/count/ratio differs from original metadata')
    require(set(meta) == set(clocks) == {str(i) for i in range(426)}, 'Exact complete source set')
    package_file_lock = read(ROOT/'source_package_lock.json')['files']
    for source_id, clock in clocks.items():
        m = meta[source_id]
        require(len(clock['normalized_exact_pts']) == m['n_frames'] and clock['source_sha256'] == m['source_sha256'] and
                clock['source_path'] == m['source_path'] and clock['video_id'] == source_id,
                'Accepted full new native clock/source identity does not match original metadata')
        witness = clock['physical_endpoint_evidence']
        require(witness['kind'] == 'LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION' and
                production['native_clock_terminal_witnesses'][source_id] == witness,
                'Actual newly measured positive native endpoint witness required, not a legacy CFR n/fps claim')
        require(F(witness['last_frame_duration_exact']) > 0 and
                F(witness['last_normalized_pts_exact']) == F(clock['normalized_exact_pts'][-1]) and
                F(clock['physical_end_exact']) == F(witness['last_normalized_pts_exact']) + F(witness['last_frame_duration_exact']),
                'Actual last native PTS plus positive measured duration does not equal accepted physical end')
        bindings = production['native_clock_original_bindings'][source_id]
        for role, ref in bindings.items():
            require(ref['path'] in package_file_lock and
                    package_file_lock[ref['path']] == ref['sha256'],
                    'Actual new/original clock and independent equality witness omitted from package closure')
        original_clock = read(bindings['original_clock_ref']['path'])
        original_clock = original_clock.get('arrays', original_clock)
        tick = F(original_clock['raw_time_base'])
        raw_pts = [F(value)*tick for value in original_clock['native_pts_ticks']]
        origin = F(original_clock['raw_first_pts_ticks'])*tick
        require(raw_pts and raw_pts[0] == origin and
                [F(p) for p in clock['original_exact_pts']] == raw_pts and
                [F(p) for p in clock['normalized_exact_pts']] == [p-origin for p in raw_pts] and
                F(clock['physical_end_exact']) == F(original_clock['native_frame_end_pts_ticks'][-1])*tick-origin,
                'New full native PTS/origin/end differs from the original successful clock')
    field_paths = {}
    for name, ref in inputs['source_field_files'].items():
        require(sha(ref['path']) == ref['sha256'], 'Original spatial field changed')
        field_paths[name] = Path(ref['path'])
    sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'), str(RUN/'baseline_a_pts_v1'), str(RUN/'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    projected = legacy_manifest(source_manifest)
    require(projected['kind'] == 'REMATCH426' and {v['video_id'] for v in projected['records']} == set(meta), 'Explicit original spatial manifest projection')
    shots = rows(field_paths['field_shots.jsonl'])
    anchor_requests = rows(field_paths['anchor_requests.jsonl'])
    anchor_outputs = rows(field_paths['anchor_output.jsonl'])
    field = rows(field_paths['field_frames.jsonl'])
    field_by_key = {(v['video_id'],v['source_frame']):v for v in field}
    require(len(field_by_key) == len(field) and wanted <= set(field_by_key), 'Complete automatic source field')
    history = {v['canonical_SHA256'] for v in read(paths['history'])}
    history.add(canonical(baseline))
    results, skipped = [], []
    for arm in ARMS:
        selected = {(s,f) for s,fs in combined[arm]['selected_ordinals'].items() for f in fs}
        guarded = []
        for source in meta:
            if not any(s == source for s,f in selected):
                selected |= {(s,f) for s,f in wanted if s == source}; guarded.append(source)
        require(selected and selected <= set(field_by_key), 'New frame outside complete original spatial field')
        chosen = [field_by_key[key] for key in sorted(selected)]
        predictions, provenance = compose_from_field(projected, chosen, shots, anchor_requests, anchor_outputs)
        for prediction in predictions:
            prediction['model_params_b'] = PARAMETERS/1e9
        require({v['video_id'] for v in predictions} == set(meta) and all(v['predictions'] for v in predictions), '426 nonempty automatic output')
        new_boxes = {(v['video_id'],p['frame']):p['bboxes'] for v in predictions for p in v['predictions']}
        require(set(new_boxes) == selected and all(new_boxes[key] == baseline_boxes[key] for key in selected & wanted), 'Original kept D8 boxes changed')
        require(all(v['model_params_b'] == PARAMETERS/1e9 for v in predictions), 'Actual total parameters')
        semantic = canonical(predictions)
        if semantic in history:
            skipped.append(dict(arm=arm, status='NOT_PUBLISHABLE_DUPLICATE_ACTUAL_PREDICTIONS', canonical_SHA256=semantic))
            continue
        history.add(semantic)
        out = ROOT/('package_'+arm); out.mkdir(exist_ok=False)
        write(out/'selected.jsonl', chosen); write(out/'predictions.jsonl', predictions); write(out/'provenance.jsonl', provenance)
        save(out/'metadata.json', metadata)
        save(out/'automatic_decisions.json', dict(arm=arm, decisions=combined[arm]['decisions'], empty_source_format_guard=guarded))
        pending = out/('candidate_TEMPORAL_'+arm+'.PENDING.zip')
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:
            z.write(out/'predictions.jsonl','predictions.jsonl')
        subprocess.run([sys.executable, str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root', str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata', str(out/'metadata.json'), '--selected', str(out/'selected.jsonl'),
            '--predictions', str(out/'predictions.jsonl'), '--provenance', str(out/'provenance.jsonl'),
            '--zip', str(pending), '--report', str(out/'independent_validation.json')], check=True, stdout=subprocess.DEVNULL)
        validation = read(out/'independent_validation.json')
        require(len(validation['checks']) == 11 and all(validation['checks'].values()) and validation['prediction_frames'] == len(selected), 'Independent11strict')
        member = sha(out/'predictions.jsonl')
        with zipfile.ZipFile(pending) as z:
            require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None and
                    hashlib.sha256(z.read('predictions.jsonl')).hexdigest() == member, 'Single-member CRC/exact bytes')
        final = out/('candidate_TEMPORAL_'+arm+'.zip'); pending.rename(final)
        receipt = dict(status='PASS_ENGINEERING_NEW_TEMPORAL_EXPLICIT_RISK_ZIP_NOT_OFFICIAL_SCORE', arm=arm,
            zip=str(final), bytes=final.stat().st_size, SHA256=sha(final), member_SHA256=member, canonical_SHA256=semantic,
            records=426, frame_count=len(selected), added_frames=len(selected-wanted), removed_frames=len(wanted-selected),
            empty_source_format_guard=guarded, kept_D8_spatial_boxes_unchanged=True, independent11strict=True,
            independent_validation_sha256=sha(out/'independent_validation.json'), actual_parameters=PARAMETERS,
            source_package_lock_sha256=permit['source_package_lock_sha256'], actual_production_completion_sha256=sha(paths['production_completion']),
            official_score='UNKNOWN', quality_pass_claimed=False, old_scientific_gates_changed=False, model_calls_in_packaging=0, website_submitted=False)
        save(out/'completion.json',receipt); results.append(receipt)
        print('NEW_READY',arm,json.dumps(receipt),flush=True)
    save(ROOT/'completion.json',dict(status='COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES',
        packages=results, unpublished_duplicates=skipped, required_goal_count=5, actual_packages=len(results), goal_complete_claimed=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if not (ROOT/'failure.json').exists():
            save(ROOT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_completed_packages=True))
        raise
