"""New pre-registered length-gated tail direction: old12screen and known facts only."""
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from evaluate_candidates_v3 import ROOT, REPORT, read, sha, save, admission, expanded_windows, native_membership
from human_metrics import mean_pairwise, paired_summary

NEW = ROOT/'reports/duration_guard_iteration_20261013_v1'
ARMS = {'D2': F(2), 'D4': F(4), 'D8': F(8)}


def spans(windows, minimum_length=None):
    result = []
    for window in windows:
        origin, limit = F(window['start_exact']), F(window['end_exact'])
        for first, last in window['segments']:
            first, last = F(str(first)), F(str(last))
            post = F(1, 2)
            if minimum_length is not None and last-first >= minimum_length:
                post += F(1, 4)
            left, right = max(origin, origin+first-F(3, 4)), min(limit, origin+last+post)
            if left < right:
                result.append((left, right))
    return result


def main():
    out = NEW/'screen_01'
    out.mkdir(exist_ok=False)
    original = REPORT/'comparison_v3_01'
    comparison = read(original/'human_comparison.json')
    veto = read(original/'partial_silver_veto.json')
    if comparison['human_eligible'] != ['B', 'C'] or veto['status'] != 'STOP_NO_ELIGIBLE_CANDIDATE':
        raise ValueError('Independent new direction must preserve the actual old failure')
    external = REPORT/'external_export_01'
    accepted = admission(external)
    export_path = external/'developer_prediction_export.json'
    export = read(export_path)
    if sha(export_path) != read(external/'developer_export_acceptance.json')['developer_prediction_export_sha256']:
        raise ValueError('Accepted original export changed')
    catalog = read(REPORT/'human_source_registration_01.json')
    predicted = {row['source_name']: row for row in export['rows']}
    save(out/'launch_claim.json', dict(protocol_sha256=sha(NEW/'PROTOCOL.md'), script_sha256=sha(__file__),
        original_failed_comparison_sha256=sha(original/'human_comparison.json'),
        original_failed_veto_sha256=sha(original/'partial_silver_veto.json'),
        actual_export_sha256=sha(export_path), input_admission_sha256=sha(external/'native_input_acceptance.json'),
        minimum_segment_lengths={name:str(value) for name,value in ARMS.items()},
        original_screen_only=True, old8confirm_not_evaluated=True,
        new_model_calls=0, new_optimizer_updates=0))
    values = []
    for expected in catalog['rows']:
        if expected['role'] != 'screen':
            continue
        row = predicted[expected['source_name']]
        annotation = Path(expected['annotation_path'])
        if sha(annotation) != expected['annotation_sha256']:
            raise ValueError('Original human annotation changed')
        human = loadmat(annotation)['user_score']
        points = [F(p) for p in row['native_clock']['normalized_exact_pts']]
        base = native_membership(points, spans(row['windows']))
        if base != native_membership(points, expanded_windows(row['windows'], '3/4', '1/2')):
            raise ValueError('New direction must exactly reproduce original baseline membership')
        metrics = {}
        for name, threshold in [('baseline', None), *ARMS.items()]:
            indices = native_membership(points, spans(row['windows'], threshold))
            if not base <= indices:
                raise ValueError('Length guard removed baseline frames')
            mask = np.zeros(len(points), dtype=bool)
            mask[list(indices)] = True
            metrics[name] = dict(mean_pairwise(mask, human), added_frames=len(indices-base))
            if name != 'baseline' and any(new < old for new, old in zip(
                    metrics[name]['user_recall'], metrics['baseline']['user_recall'])):
                raise ValueError('Length guard decreased an original human-summary recall')
        values.append(dict(source_name=expected['source_name'], role='screen', metrics=metrics))
    if len(values) != 12:
        raise ValueError('Registered original12screen denominator changed')
    summary = {name:paired_summary([r['metrics']['baseline']['f1'] for r in values],
        [r['metrics'][name]['f1'] for r in values]) for name in ARMS}
    reference_path = ROOT/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'
    reference = read(reference_path)
    if reference['reference_quality_pass'] or reference['coverage_pass'] or len(reference['rows']) != 40:
        raise ValueError('Old failed partial-reference scope changed')
    old_export_path = ROOT/'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
    old_entries = {r['video_id']:r for r in read(old_export_path)['entries']}
    checks = {name:[] for name in ARMS}
    for ref in reference['rows']:
        entry = old_entries[ref['video_id']]
        if entry['source_key'] != ref['source_key'] or entry['clock_sha256'] != ref['clock_sha256']:
            raise ValueError('Known non-test facts changed source')
        for point in ref['points']:
            if F(entry['native_clock']['exact_pts'][point['ordinal']]) != F(point['exact_pts']):
                raise ValueError('Known native fact timestamp changed')
        base_spans = spans(entry['windows'])
        base = {label:{F(p['exact_pts']) for p in ref['points'] if p['label']==label and
            any(a<=F(p['exact_pts'])<b for a,b in base_spans)} for label in ['KEEP','ORDINARY']}
        for name, threshold in ARMS.items():
            interval = spans(entry['windows'], threshold)
            new = {label:{F(p['exact_pts']) for p in ref['points'] if p['label']==label and
                any(a<=F(p['exact_pts'])<b for a,b in interval)} for label in ['KEEP','ORDINARY']}
            lost, added = base['KEEP']-new['KEEP'], new['ORDINARY']-base['ORDINARY']
            checks[name].append(dict(case_id=ref['case_id'],core_lost=sorted(map(str,lost)),
                ordinary_added=sorted(map(str,added)),known_point_veto_pass=not lost and not added))
    chosen = [name for name in ARMS if summary[name]['diagnostic_risk_pass'] and
              all(row['known_point_veto_pass'] for row in checks[name]) and
              sum(row['metrics'][name]['added_frames'] for row in values)>0]
    selection = NEW/'screen_01/selection_before_new5_confirm.json'
    save(selection,dict(chosen=chosen, thresholds_seconds={name:str(ARMS[name]) for name in chosen},
        protocol_sha256=sha(NEW/'PROTOCOL.md'),script_sha256=sha(__file__),
        frozen_before_new5_media_and_prediction=True, old8confirm_not_evaluated=True,
        new5confirmation_required=True,candidate_package_admitted=False))
    result = dict(status='SCREEN_COMPLETE_NEW5_CONFIRMATION_REQUIRED' if chosen else 'STOP_NO_NEW_DURATION_SCREEN_CANDIDATE',
        screen=summary,known_fact_checks=checks,chosen=chosen,screen_rows=values,
        selection_sha256=sha(selection),partial_reference_sha256=sha(reference_path),
        partial_original_export_sha256=sha(old_export_path),old_reference_failed_preserved=True,
        new_model_calls=0,new_optimizer_updates=0,new_submission_zips=0,candidate_package_admitted=False)
    save(out/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['known_fact_checks','screen_rows']},ensure_ascii=False))


if __name__ == '__main__':
    main()
