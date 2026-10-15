"""New CPU-only risk recipe, preserving frozen best outputs and source field."""
import datetime as dt
import json
import subprocess
import sys
import zipfile
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN/'balanced_two_window_risk_v3'))
import bw_common as c
_, _, cc, _, old, frames, production = c.helpers()
from field_contract import compose_from_field
from package_contract import keyset, package, validate_predictions
from contracts import validate_segments


def require(ok, why):
    if not ok:
        raise ValueError(why)


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main(scope='rematch'):
    lock = c.read(HERE/'boundary_source_lock.json')
    for path, digest in lock['files'].items():
        require(c.sha(path) == digest, 'new risk frozen input changed: '+path)
    protocol = c.read(HERE/'PROTOCOL.json')
    require(protocol['risks_accepted_for_new_prospective_candidates'] is True, 'new user risk scope not registered')
    require(protocol['first_candidate']['boundary_padding_seconds'] == 0.5, 'recipe differs from registration')
    best = RUN/'balanced_two_window_risk_v3'/(scope+'_01')
    out = HERE/('boundary050_'+scope)
    out.mkdir(exist_ok=False)
    source_cache = RUN/'b_score_aligned_package_v4'/(scope+'_01')
    frozen = RUN/'teacher_student_autopilot_v14/cache_01'/(scope+'.json')
    ref, manifest, clocks = old.inputs(scope)
    plan = c.read(RUN/'balanced_two_window_risk_v3/input_01'/(scope+'_plan.json'))
    evidence = production.b2_cache_evidence(scope, ref)
    require({k:v for k,v in c.read(frozen).items() if k != 'utc'} == evidence, 'complete source field cache binding differs')
    temporal = old.rows(best/'temporal.jsonl')
    field = old.rows(source_cache/'field_frames.jsonl')
    old_selected = old.rows(best/'selected.jsonl')
    records = {m['video_id']: m for m in manifest['records']}
    jobs = {j['video_id']: j for j in plan['jobs']}
    by_id = {r['video_id']: r for r in temporal}
    require(len(by_id) == len(temporal) == len(records) and set(records) == set(by_id) == set(jobs) == set(clocks), 'source IDs differ')
    field_map = {(r['video_id'], r['source_frame']): r for r in field}
    selected, baseline_keys, expanded_keys, changes, windows = [], set(), set(), [], 0
    for vid in sorted(records):
        m, row, job, clock = records[vid], by_id[vid], jobs[vid], clocks[vid]
        require(row['n_frames'] == m['n_frames'] and row['video_path'] == m['source_path'] and row['targetRatioWH'] == m['targetRatioWH'], 'source metadata mismatch')
        require(c.sha(m['source_path']) == m['source_sha256'], 'actual source bytes changed')
        arrays = clock['arrays']; tick = F(arrays['raw_time_base'])
        origin = arrays['raw_first_pts_ticks']*tick
        points = [p*tick-origin for p in arrays['native_pts_ticks']]
        require(len(points) == m['n_frames'] and all(a < b for a,b in zip(points, points[1:])), 'actual native clock malformed')
        require(len(row['windows']) == len(job['windows']), 'window denominator differs')
        chosen, before = set(), set()
        for value, part in zip(row['windows'], job['windows']):
            require(value['output_valid'] is True and not value['parse_errors'] and value['clock_record_sha256'] == clock['clock_record_sha256'], 'failed or wrong clock original window')
            require(value['start_sec'] == part['start_sec'] and value['end_sec'] == part['end_sec'], 'original window changed')
            start = F(part['window']['exact_normalized_start']) if c.is_changed(part) else F(str(part['start_sec']))
            end = F(part['window']['exact_normalized_end']) if c.is_changed(part) else F(str(part['end_sec']))
            segments = value['parsed_segments']; validate_segments(segments, part['end_sec']-part['start_sec'])
            require(value['status'] == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'failure cannot become empty')
            windows += 1
            for a,b in segments:
                a,b = F(str(a)), F(str(b))
                first,last = bisect_left(points,start+a),bisect_left(points,start+b)
                require(first < last, 'original has zero actual source frames')
                before.update(range(first,last))
                first,last = bisect_left(points,max(start,start+a-F(1,2))),bisect_left(points,min(end,start+b+F(1,2)))
                require(first < last, 'expanded interval has no actual source frames')
                chosen.update(range(first,last))
        baseline_keys.update((vid,f) for f in before)
        expanded_keys.update((vid,f) for f in chosen)
        require(before <= chosen, 'uniform context extension removed an original selection')
        require(all((vid,f) in field_map for f in chosen), 'new selection outside proven full-source spatial field')
        selected.extend(dict(field_map[(vid,f)]) for f in sorted(chosen))
        changes.append(dict(video_id=vid,before=len(before),after=len(chosen),added=len(chosen-before)))
    require(baseline_keys == keyset(old_selected), 'zero-padding exact native membership does not reproduce best')
    require(len(records) == (426 if scope == 'rematch' else 8), 'scope count differs')
    old.write_rows(out/'selected.jsonl', selected)
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected,
        old.rows(source_cache/'field_shots.jsonl'), old.rows(source_cache/'anchor_requests.jsonl'), old.rows(source_cache/'anchor_output.jsonl'))
    old_predictions = { (r['video_id'],p['frame']):p['bboxes'] for r in old.rows(best/'predictions.jsonl') for p in r['predictions'] }
    new_predictions = { (r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions'] }
    require(set(old_predictions) == baseline_keys and all(new_predictions[k] == v for k,v in old_predictions.items()), 'original selected box changed')
    old.write_rows(out/'predictions.jsonl', predictions); old.write_rows(out/'provenance.jsonl', provenance)
    accepted = validate_predictions(projected, predictions, keyset(selected), provenance)
    save(out/'metadata.json', dict(records=manifest['records'], errors=[]))
    pending = out/'candidate_BOUNDARY_CONTEXT_050.PENDING.zip'
    accepted.update(package(out/'predictions.jsonl', pending))
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
        '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
        '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
        '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
        '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    independent = c.read(out/'independent_validation.json')
    production.check_independent(independent,scope,len(selected))
    require(independent['zip_sha256'] == c.sha(pending) and independent['predictions_sha256'] == c.sha(out/'predictions.jsonl'), 'independent artifact SHA differs')
    with zipfile.ZipFile(pending) as z:
        require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None and z.read('predictions.jsonl') == (out/'predictions.jsonl').read_bytes(), 'actual CRC/roundtrip failed')
    final = out/'candidate_BOUNDARY_CONTEXT_050.zip'; pending.rename(final)
    save(out/'selection_change_audit.json', dict(rows=changes,original=len(baseline_keys),candidate=len(expanded_keys),added=len(expanded_keys-baseline_keys),removed=len(baseline_keys-expanded_keys),all_common_boxes_equal=True))
    accepted.update(status='PASS_COMPLETE_NEW_USER_AUTHORIZED_RISK_ZIP',utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=str(final),zip_bytes=final.stat().st_size,zip_sha256=c.sha(final),
        scope=scope,window_count=windows,boundary_context_seconds=0.5,exact_native_membership=True,window_clamp=True,original_selected_frames=len(baseline_keys),new_selected_frames=len(selected),
        added_frames=len(expanded_keys-baseline_keys),removed_frames=0,all_original_selected_boxes_equal=True,source_cache=str(source_cache),cache_receipt_sha256=c.sha(frozen),
        source_field_files=evidence['files'],protocol_sha256=c.sha(HERE/'PROTOCOL.json'),new_model_calls=0,new_optimizer_updates=0,new_spatial_model_calls=0,
        complete_pipeline_parameters=8782459120,independent_validation_sha256=c.sha(out/'independent_validation.json'),scientific_quality_reference='FAILED_PRESERVED',
        effect='More temporal context; possible ordinary-frame precision loss',user_accepted_risk=True,official_score=None,website_submitted=False)
    save(out/'completion.json', accepted)
    print(json.dumps(accepted),flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'rematch')
