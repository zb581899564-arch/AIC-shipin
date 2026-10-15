"""Prospective +/-1/4-second context around accepted dense128 outputs."""
import subprocess
import sys
import zipfile
from bisect import bisect_left
from pathlib import Path
import dense_runtime as r


def main():
    from dense_production import PREP, GPU, prepared, key
    acceptance, extra = prepared()
    lock = r.verify_lock('rematch', extra)
    protocol_path = r.HERE/'DENSE_CONTEXT025_PROTOCOL.json'
    protocol = r.read(protocol_path)
    r.require(protocol['padding_exact'] == '1/4' and protocol['user_risk_authorization'] is True and
              protocol['parent_recipe'] == r.RECIPE, 'context arm was not prospectively registered')
    r.require(r.sha(protocol_path) == lock['value']['context_protocol_sha256'] and
              r.sha(r.HERE/'dense_context_package.py') == lock['value']['context_script_sha256'],
              'prospective context registration or code changed')
    parent_dir = r.HERE/'rematch_01/package_01'
    parent = r.read(parent_dir/'completion.json')
    parent_report = r.read(parent_dir/'independent_validation.json')
    r.require(parent['status'] == 'PASS_COMPLETE_NEW_DENSE128_USER_AUTHORIZED_RISK_ZIP' and
              r.sha(parent['candidate']) == parent['zip_sha256'] and
              r.sha(parent_dir/'predictions.jsonl') == parent_report['predictions_sha256'] and
              r.sha(parent_dir/'provenance.jsonl') == parent_report['provenance_sha256'] and
              r.sha(parent_dir/'independent_validation.json') == parent['independent_validation_sha256'],
              'parent dense128 artifact is not actually accepted')
    replay_path = r.HERE/'rematch_01/replay_01/completion.json'
    replay = r.read(replay_path)
    terminal = r.read(GPU/'completion.json')
    r.require(replay['status'] == 'PASS_521_DENSE128_INDEPENDENT_CPU_REPLAYS' and
              replay['source_lock_sha256'] == terminal['source_lock_sha256'] == lock['sha256'] and
              replay['gpu_completion_sha256'] == r.sha(GPU/'completion.json') and
              parent['independent_replay_sha256'] == r.sha(replay_path), 'complete parent independent replay missing')
    by_key = {e['key']: e for e in terminal['entries']}
    r.require(len(by_key) == 521, 'parent actual-call denominator differs')
    baseline, chosen = set(), set()
    for job in acceptance['jobs']:
        for window in job['windows']:
            entry = by_key[key(window)]
            done = r.read(entry['done_path'])
            r.require(r.sha(entry['done_path']) == entry['done_sha256'] and
                      done['source_window'] == window and done['output_valid'] and not done['parse_errors'],
                      'parent failed or changed raw cannot become a context selection')
            points = [r.F(x) for x in window['all_source_exact_pts']]
            start, end = r.F(window['exact_raw_start']), r.F(window['exact_raw_end'])
            for a, b in done['parsed_segments']:
                a, b = start+r.F(str(a)), start+r.F(str(b))
                first, stop = bisect_left(points, a), bisect_left(points, b)
                baseline.update((window['source_id'], i) for i in range(first, stop))
                lower, upper = max(start, a-r.F(1,4)), min(end, b+r.F(1,4))
                first, stop = bisect_left(points, lower), bisect_left(points, upper)
                r.require(window['eligible_first'] <= first < stop <= window['eligible_stop'], 'context escaped original window')
                r.require(list(range(first,stop)) == [i for i,p in enumerate(points) if lower <= p < upper],
                          'independent direct PTS predicate differs')
                chosen.update((window['source_id'], i) for i in range(first, stop))
    common, (_,_,_,_,old,frames,production) = r.original_helpers()
    ref, manifest, clocks = old.inputs('rematch')
    from package_contract import keyset, package, validate_predictions
    from field_contract import compose_from_field
    r.require(baseline == keyset(old.rows(parent_dir/'selected.jsonl')) and baseline <= chosen and chosen,
              'context baseline does not exactly reproduce accepted native selection')
    cache = r.RUN/'b_score_aligned_package_v4/rematch_01'
    cache_evidence = production.b2_cache_evidence('rematch', ref)
    frozen = r.read(r.RUN/'teacher_student_autopilot_v14/cache_01/rematch.json')
    r.require({k:v for k,v in frozen.items() if k != 'utc'} == cache_evidence, 'time-independent full source field changed')
    field = old.rows(cache/'field_frames.jsonl')
    field_by_key = {(x['video_id'],x['source_frame']):x for x in field}
    r.require(len(field_by_key) == len(field) and chosen <= set(field_by_key), 'context membership outside complete source field')
    selected = [field_by_key[k] for k in sorted(chosen)]
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, old.rows(cache/'field_shots.jsonl'),
                                                 old.rows(cache/'anchor_requests.jsonl'), old.rows(cache/'anchor_output.jsonl'))
    out = r.HERE/'rematch_01/context025_package_01'
    out.mkdir(exist_ok=False)
    try:
        report = validate_predictions(projected, predictions, chosen, provenance)
        for name, rows in [('selected',selected),('predictions',predictions),('provenance',provenance)]:
            old.write_rows(out/(name+'.jsonl'), rows)
        r.save(out/'metadata.json', dict(records=manifest['records'],errors=[]))
        pending = out/'candidate_DENSE128_CONTEXT025.PENDING.zip'
        report.update(package(out/'predictions.jsonl',pending))
        subprocess.run([sys.executable,'-B',str(r.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root',str(r.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
            '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
        independent = r.read(out/'independent_validation.json')
        production.check_independent(independent,'rematch',len(selected))
        r.require(independent['zip_sha256'] == r.sha(pending) and
                  independent['predictions_sha256'] == r.sha(out/'predictions.jsonl') and
                  independent['provenance_sha256'] == r.sha(out/'provenance.jsonl'), 'independent artifact SHA differs')
        with zipfile.ZipFile(pending) as archive:
            r.require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                      archive.read('predictions.jsonl') == (out/'predictions.jsonl').read_bytes(), 'ZIP CRC or roundtrip differs')
        common_boxes = {(x['video_id'],p['frame']):p['bboxes'] for x in old.rows(parent_dir/'predictions.jsonl') for p in x['predictions']}
        new_boxes = {(x['video_id'],p['frame']):p['bboxes'] for x in predictions for p in x['predictions']}
        r.require(all(new_boxes[k] == v for k,v in common_boxes.items()), 'original dense spatial boxes changed')
        final = out/'candidate_DENSE128_CONTEXT025.zip'
        pending.rename(final)
        report.update(status='PASS_COMPLETE_DENSE128_CONTEXT025_RISK_ZIP',utc=r.utc(),candidate=str(final),
            zip_bytes=final.stat().st_size,zip_sha256=r.sha(final),video_records=426,prediction_frames=len(selected),
            parent_frames=len(baseline),added_frames=len(chosen-baseline),removed_frames=0,original_boxes_unchanged=True,
            padding_exact='1/4',parent_completion_sha256=r.sha(parent_dir/'completion.json'),
            independent_validation_sha256=r.sha(out/'independent_validation.json'),protocol_sha256=r.sha(protocol_path),
            source_lock_sha256=lock['sha256'],parent_actual_model_calls=521,new_model_calls_this_arm=0,
            new_optimizer_updates=0,complete_pipeline_parameters=8782459120,scientific_quality_pass=False,
            official_score=None,website_submitted=False)
        r.save(out/'completion.json', report)
        print(__import__('json').dumps(report),flush=True)
    except BaseException as exc:
        r.failure(out,exc)
        raise


if __name__ == '__main__':
    main()
