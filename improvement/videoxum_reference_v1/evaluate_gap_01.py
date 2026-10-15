"""One registered continuity recipe: fact veto, twelve screen, freeze, eight confirm."""
from fractions import Fraction as F
from pathlib import Path
import json
import random

from gap_bridge_v1 import window_spans
from evaluate_l16_intervals_07 import membership
from native_profile_04 import native64_windows, validate_original_origin, validate_reference_endpoints
from reference_intervals import paired_duration_metrics, measure
from qualify_l16_08 import admission
from stage_common_04 import read, save, sha

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/gap_bridge_iteration_20261013_v1'
OUT = REPORT / 'comparison_01'


def source_comparison(prediction, reference):
    clock = prediction['native_clock']
    validate_original_origin(clock)
    human = reference['annotator_intervals_exact_seconds']
    validate_reference_endpoints(clock, human)
    if len(human) != 10:
        raise ValueError('All ten original human summaries required')
    plan, windows = native64_windows(clock), prediction['windows']
    if len(plan) != len(windows) or any(F(a['start_exact']) != F(b['start_exact']) or F(a['end_exact']) != F(b['end_exact']) for a, b in zip(plan, windows)):
        raise ValueError('Actual original native64 window plan changed')
    if any(w['original_status'] != ('MODEL_OK' if w['segments'] else 'LEGAL_EMPTY') for w in windows):
        raise ValueError('Failed window cannot become an empty prediction')
    baseline, candidate = [window_spans(windows, arm) for arm in ('D8_BASELINE', 'GAP100')]
    points = [F(x) for x in clock['original_exact_pts']]
    old_frames, frames = membership(points, baseline), membership(points, candidate)
    # Independent direct PTS predicate checks interval-to-native-frame conversion.
    if frames != {i for i, t in enumerate(points) if any(a <= t < b for a, b in candidate)} or not old_frames <= frames:
        raise ValueError('Exact native membership or D8 preservation failed')
    old = [paired_duration_metrics(baseline, spans) for spans in human]
    new = [paired_duration_metrics(candidate, spans) for spans in human]
    if any(a['recall'] > b['recall'] for a, b in zip(old, new)):
        raise ValueError('Original annotator recall decreased')
    a, b = [sum((x['f1'] for x in rows), F(0)) / 10 for rows in (old, new)]
    return dict(video_id=prediction['video_id'], group=prediction['group'], baseline_mean_f1_exact=str(a),
                candidate_mean_f1_exact=str(b), delta_exact=str(b-a), baseline_mean_f1=float(a), candidate_mean_f1=float(b),
                annotator_baseline=[{k: str(v) for k, v in row.items()} for row in old],
                annotator_candidate=[{k: str(v) for k, v in row.items()} for row in new],
                actual_interval_changed=baseline != candidate, actual_native_frame_changed=old_frames != frames,
                added_native_frames=len(frames-old_frames), added_duration_exact=str(measure(candidate)-measure(baseline)),
                baseline_frames_preserved=True, all_original_annotator_recalls_preserved=True, source_drop_gate=b-a >= -F(1, 100))


def evaluate_group(predictions, references, group):
    if group not in ('screen', 'confirm'):
        raise ValueError('Undeclared group')
    expected = 12 if group == 'screen' else 8
    rows = [x for x in predictions if x['group'] == group]
    if len(rows) != expected or len({x['video_id'] for x in rows}) != expected:
        raise ValueError('Original 12/8 source denominator changed')
    results = [source_comparison(row, references[row['video_id']]) for row in rows]
    deltas = [F(x['delta_exact']) for x in results]
    macro = sum(deltas, F(0)) / expected
    changed = sum(x['actual_interval_changed'] and x['actual_native_frame_changed'] for x in results)
    passed = macro >= 0 and changed >= 3 and all(x['source_drop_gate'] for x in results)
    rng = random.Random(20261013)
    boot = sorted(float(sum((deltas[rng.randrange(expected)] for _ in range(expected)), F(0))/expected) for _ in range(5000))
    return dict(status='PASS_GAP100_FIXED_TEMPORAL_PROXY_GROUP' if passed else 'REJECT_GAP100_FIXED_TEMPORAL_PROXY_GROUP',
                group=group, sources=expected, macro_delta_exact=str(macro), macro_delta=float(macro),
                paired_bootstrap95=[boot[125], boot[4874]], bootstrap_seed=20261013, bootstrap_samples=5000,
                actual_changed_sources=changed, minimum_changed_sources=3, source_drop_limit_exact='1/100',
                original_fixed_gates_pass=passed, rows=results, new_model_calls=0, new_optimizer_updates=0,
                interpretation='All ten original manual interval duration-F1 averaged; not crop, author1fps GT or official score')


def fact_veto():
    ref_path = ROOT / 'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'
    pred_path = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
    reference, payload = read(ref_path), read(pred_path)
    if reference['reference_quality_pass'] or reference['coverage_pass']:
        raise ValueError('Old insufficient coverage must remain FAILED')
    entries = {row['video_id']: row for row in payload['entries']}
    checks = []
    for row in reference['rows']:
        entry = entries[row['video_id']]
        if any(row[k] != entry[k] for k in ('source_group', 'source_key', 'clock_sha256')):
            raise ValueError('Fixed source identity changed')
        selected = {}
        for arm in ('D8_BASELINE', 'GAP100'):
            spans = window_spans(entry['windows'], arm)
            selected[arm] = {label: set() for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
            for point in row['points']:
                time = F(point['exact_pts'])
                if time != F(entry['native_clock']['exact_pts'][point['ordinal']]):
                    raise ValueError('Fixed native fact timestamp changed')
                if any(a <= time < b for a, b in spans):
                    selected[arm][point['label']].add(time)
        lost = selected['D8_BASELINE']['KEEP'] - selected['GAP100']['KEEP']
        added = selected['GAP100']['ORDINARY'] - selected['D8_BASELINE']['ORDINARY']
        checks.append(dict(case_id=row['case_id'], source_group=row['source_group'], core_lost=sorted(map(str, lost)),
                           ordinary_added=sorted(map(str, added)), unknown_added=len(selected['GAP100']['UNKNOWN']-selected['D8_BASELINE']['UNKNOWN']),
                           known_point_veto_pass=not lost and not added))
    if len(checks) != 40:
        raise ValueError('All forty unchanged facts required')
    passed = all(x['known_point_veto_pass'] for x in checks)
    return dict(pass_gate=passed, checks=checks, old40_quality_failed_preserved=True, UNKNOWN_not_relabelled=True,
                bindings=dict(reference_sha256=sha(ref_path), prediction_sha256=sha(pred_path)), new_model_calls=0)


def main():
    if OUT.exists():
        raise ValueError('Gap comparison already exists; never rerun or retune completed metrics')
    registration = read(REPORT/'registration_01.json')
    if registration['candidate'] != 'GAP100' or registration['max_gap_exact_seconds'] != '1':
        raise ValueError('Registered single recipe changed')
    for key, path in [('rule_sha256', Path(__file__).with_name('gap_bridge_v1.py')), ('evaluation_sha256', Path(__file__)),
                      ('protocol_sha256', REPORT/'PROTOCOL.md')]:
        if sha(path) != registration[key]:
            raise ValueError('Before-metrics registration changed')
    payload, references = admission()
    OUT.mkdir()
    save(OUT/'launch_claim.json', dict(registration_sha256=sha(REPORT/'registration_01.json'),
        old_L16_failure_sha256=sha(ROOT/'reports/videoxum_reference_iteration_20261013_v1/l16_comparison_08/result.json'),
        new_model_calls=0, new_optimizer_updates=0, confirmation_scored=False))
    fact = fact_veto()
    save(OUT/'fact_veto.json', fact)
    if not fact['pass_gate']:
        result = dict(status='STOP_GAP100_KNOWN_FACT_REJECTED', qualified=False, screen_evaluated=False, confirmation_evaluated=False)
    else:
        screen = evaluate_group(payload['rows'], references, 'screen')
        save(OUT/'screen_result.json', screen)
        if not screen['original_fixed_gates_pass']:
            result = dict(status='STOP_GAP100_SCREEN_REJECTED_CONFIRM_NOT_EVALUATED', qualified=False,
                          screen_sha256=sha(OUT/'screen_result.json'), confirmation_evaluated=False)
        else:
            save(OUT/'selection_before_confirm.json', dict(chosen='GAP100', max_gap_exact_seconds='1',
                screen_sha256=sha(OUT/'screen_result.json'), registration_sha256=sha(REPORT/'registration_01.json'),
                frozen_before_confirm_metrics=True, no_threshold_retuning=True))
            confirm = evaluate_group(payload['rows'], references, 'confirm')
            save(OUT/'confirm_result.json', confirm)
            qualified = confirm['original_fixed_gates_pass']
            result = dict(status='PASS_GAP100_FIXED_FACT_SCREEN_CONFIRM_RISK_ADMISSION' if qualified else 'STOP_GAP100_CONFIRM_REJECTED',
                          qualified=qualified, screen_sha256=sha(OUT/'screen_result.json'), confirm_sha256=sha(OUT/'confirm_result.json'),
                          selection_sha256=sha(OUT/'selection_before_confirm.json'), confirmation_evaluated=True)
    result.update(candidate='GAP100', fact_sha256=sha(OUT/'fact_veto.json'), registration_sha256=sha(REPORT/'registration_01.json'),
                  new_model_calls=0, new_optimizer_updates=0, new_submission_zips=0, official_score='UNKNOWN', old_failures_preserved=True)
    save(OUT/'result.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
