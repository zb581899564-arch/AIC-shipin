"""Prospective mild-context arm using the already accepted 0.5s full field."""
import json
import subprocess
import sys
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
from boundary_package import RUN, HERE, c, old, frames, production, require, save
from package_contract import keyset, validate_predictions, package
from contracts import validate_segments


def main():
    for path,digest in c.read(HERE/'CONTEXT025_SOURCE_LOCK.json')['files'].items():
        require(c.sha(path) == digest,'prospective mild-arm input changed: '+path)
    protocol = c.read(HERE/'CONTEXT025_PROTOCOL.json')
    require(protocol['padding_exact'] == '1/4' and protocol['user_risk_authorization'], 'mild recipe not registered')
    accepted050 = HERE/'boundary050_rematch'
    accepted = c.read(accepted050/'completion.json')
    require(accepted['status'] == 'PASS_COMPLETE_NEW_USER_AUTHORIZED_RISK_ZIP' and accepted['removed_frames'] == 0 and accepted['all_original_selected_boxes_equal'], '0.5 source package not fully accepted')
    require(c.sha(accepted050/'predictions.jsonl') == accepted['predictions_sha256'] and c.sha(accepted050/'independent_validation.json') == accepted['independent_validation_sha256'], 'accepted source artifact changed')
    prior = c.read(accepted050/'independent_validation.json')
    require(c.sha(accepted050/'provenance.jsonl') == prior['provenance_sha256'], 'accepted field provenance changed')
    _, manifest, clocks = old.inputs('rematch')
    best = RUN/'balanced_two_window_risk_v3/rematch_01'
    temporal = {r['video_id']:r for r in old.rows(best/'temporal.jsonl')}
    jobs = {j['video_id']:j for j in c.read(RUN/'balanced_two_window_risk_v3/input_01/rematch_plan.json')['jobs']}
    parent_selected = {(r['video_id'],r['source_frame']):r for r in old.rows(accepted050/'selected.jsonl')}
    selected, target, baseline = [], set(), set()
    require(set(temporal) == set(jobs) == set(clocks) and len(temporal) == 426, 'complete source denominator differs')
    for vid in sorted(temporal):
        a = clocks[vid]['arrays']; tick = F(a['raw_time_base']); origin = a['raw_first_pts_ticks']*tick
        points = [p*tick-origin for p in a['native_pts_ticks']]
        for value, part in zip(temporal[vid]['windows'],jobs[vid]['windows']):
            require(value['output_valid'] and not value['parse_errors'] and value['clock_record_sha256'] == clocks[vid]['clock_record_sha256'], 'original failure cannot become a mild selection')
            start = F(part['window']['exact_normalized_start']) if c.is_changed(part) else F(str(part['start_sec']))
            stop = F(part['window']['exact_normalized_end']) if c.is_changed(part) else F(str(part['end_sec']))
            segments = value['parsed_segments']; validate_segments(segments,part['end_sec']-part['start_sec'])
            require(value['status'] == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'original status differs')
            for lo,hi in segments:
                lo,hi = F(str(lo)),F(str(hi))
                baseline.update((vid,f) for f in range(bisect_left(points,start+lo),bisect_left(points,start+hi)))
                lower,upper = max(start,start+lo-F(1,4)),min(stop,start+hi+F(1,4))
                first,last = bisect_left(points,lower),bisect_left(points,upper)
                require(first < last, 'no actual native frames')
                target.update((vid,f) for f in range(first,last))
                # Independent direct clock predicate crosschecks the bisect path.
                require(list(range(first,last)) == [i for i,p in enumerate(points) if lower <= p < upper], 'independent PTS predicate differs')
    require(baseline == keyset(old.rows(best/'selected.jsonl')) and baseline <= target <= set(parent_selected), 'mild membership is not between original and accepted 0.5 arm')
    selected = [parent_selected[k] for k in sorted(target)]
    predictions = [dict(r,predictions=[p for p in r['predictions'] if (r['video_id'],p['frame']) in target]) for r in old.rows(accepted050/'predictions.jsonl')]
    provenance = [p for p in old.rows(accepted050/'provenance.jsonl') if (p['video_id'],p['source_frame']) in target]
    out = HERE/'boundary025_rematch'; out.mkdir(exist_ok=False)
    projected = frames.legacy_manifest(manifest)
    report = validate_predictions(projected,predictions,target,provenance)
    for name,rows in [('selected',selected),('predictions',predictions),('provenance',provenance)]:old.write_rows(out/(name+'.jsonl'),rows)
    save(out/'metadata.json',dict(records=manifest['records'],errors=[]))
    pending = out/'candidate_BOUNDARY_CONTEXT_025.PENDING.zip'
    report.update(package(out/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
        '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
        '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
        '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
        '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    independent = c.read(out/'independent_validation.json'); production.check_independent(independent,'rematch',len(target))
    require(independent['zip_sha256'] == c.sha(pending) and independent['predictions_sha256'] == c.sha(out/'predictions.jsonl'), 'independent SHA mismatch')
    final = out/'candidate_BOUNDARY_CONTEXT_025.zip'; pending.rename(final)
    report.update(status='PASS_COMPLETE_MILD_CONTEXT_RISK_ZIP',candidate=str(final),zip_bytes=final.stat().st_size,zip_sha256=c.sha(final),
        padding_exact='1/4',window_clamp=True,old_frames=len(baseline),candidate_frames=len(target),added_frames=len(target-baseline),removed_frames=0,
        within_accepted050=True,original_and_parent_boxes_unchanged=True,new_model_calls=0,new_optimizer_updates=0,complete_pipeline_parameters=8782459120,
        parent_completion_sha256=c.sha(accepted050/'completion.json'),protocol_sha256=c.sha(HERE/'CONTEXT025_PROTOCOL.json'),independent_validation_sha256=c.sha(out/'independent_validation.json'),
        official_score=None,scientific_quality_pass=False,user_risk_authorization=True,website_submitted=False)
    save(out/'completion.json',report)
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
