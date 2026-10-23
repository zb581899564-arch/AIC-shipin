"""Read-only accounting of the frozen R funnel; no inference or new predictions.

Detailed per-source counts stay on Linux. The short summary contains no media,
model tensors, test labels or source-specific recipe suggestions.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile


WORK = Path('/home/inspur/aic_video_work')
RUN = WORK / 'final_sprint_temporal_r_production_20261023_v6'
CONTROL = WORK / 'final_sprint_temporal_field_chain_20261023_v6'
OUTPUT = WORK / 'r_failure_diagnosis_20261024_v1'
BASE = WORK / 'general_highlight_supervision_20261021_v1/routing_package63/source_remove/candidate_SPORT_ROUTE_REMOVE_8B.zip'
EXPECTED = {
    'baseline': '85778a086f3fb0152947ece40b8dc258c7fef717b40519fe3e23fd4f7b0fabbe',
    'r_time_event': '0d114eb7428fc01feef010640d748f39792ca1d6342bc5995e016fa18fc7a279',
    'r_time_apex': '1c7d2c0c894e5d7a3ca4b35e2be101305ef20ab3a64c4a3ce6a0b6406800df6d',
}
PHASES = ['ordinary', 'setup', 'apex', 'resolution']


def read(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    with (OUTPUT / name).open('x') as stream:
        json.dump(value, stream, indent=2)


def zip_rows(path, expected):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    with zipfile.ZipFile(path) as archive:
        rows = [json.loads(line) for line in archive.read('predictions.jsonl').splitlines()]
    assert len(rows) == 426
    return {str(row['video_id']): row for row in rows}


def frames(row):
    return {p['frame'] for p in row['predictions']}


def event_frames(events):
    return {i for event in events for cell in event['cells']
            for i in range(cell['first'], cell['stop'])}


def quantiles(values):
    if not values:
        return None
    values = sorted(values)
    return dict(min=values[0], median=statistics.median(values), max=values[-1],
                p10=values[int((len(values) - 1) * .1)],
                p90=values[int((len(values) - 1) * .9)])


def phase_results(source_id, adopted):
    packets = {}
    for task, path in adopted.items():
        if task.startswith('phase_' + source_id + '_clip_'):
            packets[task] = read(path)['result']
    for folder in (RUN / 'journal/tasks').glob('phase_' + source_id + '_clip_*'):
        successes = list((folder / 'attempts').glob('*/success.json'))
        assert len(successes) <= 1
        if successes:
            success = read(successes[0])
            packet = read(success['artifacts']['result']['path'])['result']
            if folder.name in packets:
                assert packet == packets[folder.name]
            packets[folder.name] = packet
    return [packets[key] for key in sorted(packets)]


def phase_diagnostics(packets, counts, values):
    nonordinary, support = set(), set()
    for packet in packets:
        counts['clips'] += 1
        values['clip_seconds'].append(float(Fraction(packet['clip']['end_exact']) -
                                             Fraction(packet['clip']['start_exact'])))
        counts['role_' + packet['role']] += 1
        counts['all_ordinary_clips'] += packet['status'] == 'LEGAL_EMPTY'
        previous = None
        for row in packet['phases']:
            cell = set(range(row['cell']['first'], row['cell']['stop']))
            assert not support.intersection(cell)
            support.update(cell)
            phase = row['phase']
            counts['cells_' + phase] += 1
            counts['frames_' + phase] += len(cell)
            counts['first_cells' if row['group'] == 0 else 'later_cells'] += 1
            if phase == 'ordinary':
                counts['ordinary_first' if row['group'] == 0 else 'ordinary_later'] += 1
            else:
                nonordinary.update(cell)
            alt = row['alternatives']
            mean_winner = max(range(4), key=lambda i: (alt[i]['mean_log_probability'], -i))
            sum_winner = max(range(4), key=lambda i: (alt[i]['log_probability_sum'], -i))
            counts['mean_sum_argmax_differ'] += mean_winner != sum_winner
            counts['unconstrained_winner_' + PHASES[mean_winner]] += 1
            blocked = PHASES[mean_winner] not in row['allowed_phases']
            counts['transition_blocked_argmax'] += blocked
            counts['transition_blocked_to_ordinary'] += blocked and phase == 'ordinary'
            if previous:
                counts['transition_' + previous + '_' + phase] += 1
            previous = phase
            for alternative in alt:
                counts['tokens_' + alternative['phase'] + '_' +
                       str(len(alternative['token_ids']))] += 1
            values['selected_margin'].append(row['selected_minus_ordinary'])
    return nonordinary, support


def analyze_source(source, clock, base_row, event_row, apex_row, adopted, totals, values):
    sid = source['video_id']
    points = [Fraction(p) for p in clock['normalized_exact_pts']]
    end = Fraction(clock['physical_end_exact'])
    weights = [float(b - a) for a, b in zip(points, points[1:] + [end])]
    base, chosen, apex = frames(base_row), frames(event_row), frames(apex_row)
    original = read(RUN / 'candidates/r_time_event/sources' / sid / 'result.json')
    derived = read(RUN / 'candidates/r_time_apex/sources' / sid / 'result.json')
    assert original['predictions'] == event_row['predictions']
    assert derived['predictions'] == apex_row['predictions']
    assert apex <= chosen
    assert all(0 <= i < len(points) for i in base | chosen | apex)
    baseline_boxes = {p['frame']: p['bboxes'] for p in base_row['predictions']}
    common_boxes = {p['frame']: p['bboxes'] for p in event_row['predictions'] if p['frame'] in base}
    assert all(box == baseline_boxes[i] for i, box in common_boxes.items())
    selection = original['selection']
    packets = phase_results(sid, adopted)
    nonordinary, support = phase_diagnostics(packets, totals['phase'], values)
    assert support == set(range(len(points)))
    events = selection['events']
    assembled = event_frames(events)
    selected_ids = set(selection['selected_event_ids'])
    selected_events = [e for e in events if e['event_id'] in selected_ids]
    after_dp = event_frames(selected_events)
    assert chosen == after_dp - set(selection['unsupported_proposals_unknown'])
    rejected = set(i for arc in selection['rejected_partial_arcs']
                   for i in range(arc['first'], arc['stop']))
    assert assembled | rejected == nonordinary and not assembled.intersection(rejected)
    stages = {'all_native': support, 'baseline': base, 'nonordinary': nonordinary,
              'has_apex_events': assembled, 'event_after_budget': after_dp,
              'event_final': chosen, 'apex_final': apex}
    detail = {'video_id': sid, 'native_frames': len(points), 'ratio': source['targetRatioWH']}
    for name, selected in stages.items():
        duration = sum(weights[i] for i in selected)
        totals['frames'][name] += len(selected)
        totals['seconds'][name] += duration
        totals['baseline_kept'][name] += len(selected & base)
        totals['empty'][name] += not selected
        detail[name] = {'frames': len(selected), 'seconds': duration,
                        'baseline_kept': len(selected & base)}
    budgets = selection['budget']
    totals['events']['assembled'] += len(events)
    totals['events']['selected'] += len(selected_events)
    duration_budget = Fraction(budgets['duration_budget_exact'])
    for event, utility in zip(events, budgets['event_utilities']):
        if event['event_id'] in selected_ids:
            reason = 'selected'
        elif Fraction(event['duration_exact']) > duration_budget:
            reason = 'too_long_for_source_cap'
        elif utility <= 0:
            reason = 'nonpositive_net_utility'
        else:
            reason = 'positive_but_not_selected_under_cap'
        totals['event_rejection'][reason] += 1
        values['event_seconds'].append(float(Fraction(event['duration_exact'])))
    if not chosen:
        reason = ('all_groups_ordinary' if not nonordinary else
                  'no_apex_in_local_arcs' if not events else
                  'no_event_selected_by_budget_utility' if not selected_ids else 'no_spatial_support')
        totals['empty_causes'][reason] += 1
    totals['events']['rejected_partial_arcs'] += len(selection['rejected_partial_arcs'])
    totals['events']['cap_binding_sources'] += (
        sum(Fraction(e['duration_exact']) for e in events) > duration_budget)
    totals['events']['positive_utility_exceeds_budget_sources'] += (
        sum(Fraction(e['duration_exact']) for e, u in zip(events, budgets['event_utilities'])
            if u > 0) > duration_budget)
    totals['events']['underfilled_sources'] += (
        Fraction(budgets['actual_event_duration_exact']) < duration_budget * Fraction(9, 10))
    return detail


def main():
    OUTPUT.mkdir(exist_ok=True)
    save('scope.json', dict(at=datetime.now(timezone.utc).isoformat(),
        diagnostic_only=True, no_model_or_decode=True, no_new_candidate=True,
        no_test_labels_or_per_source_tuning=True, submitted_zip_sha256=EXPECTED,
        analysis_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    assets = read(RUN / 'assets.json')
    manifest = read(CONTROL / 'r_phase_adoption.json')
    adopted = {row['task_id']: row['returned']['path'] for row in manifest['rows']}
    baseline = zip_rows(BASE, EXPECTED['baseline'])
    event = zip_rows(RUN / 'candidates/r_time_event/package/candidate_FINAL_R_TIME_EVENT.zip',
                     EXPECTED['r_time_event'])
    apex = zip_rows(RUN / 'candidates/r_time_apex/package/candidate_FINAL_R_TIME_APEX.zip',
                    EXPECTED['r_time_apex'])
    assert set(baseline) == set(event) == set(apex)
    clocks = {}
    totals = {key: Counter() for key in ['frames', 'seconds', 'baseline_kept', 'empty',
              'phase', 'events', 'event_rejection', 'empty_causes']}
    values = defaultdict(list)
    detail = []
    for source in assets['sources']:
        ref = source['clock']
        if ref['path'] not in clocks:
            clocks[ref['path']] = read(ref['path'])
        clock = clocks[ref['path']][ref['source_key']]
        sid = source['video_id']
        detail.append(analyze_source(source, clock, baseline[sid], event[sid], apex[sid],
                                     adopted, totals, values))
    summary = dict(source_count=len(detail), totals=totals,
        distributions={key: quantiles(value) for key, value in values.items()},
        package_vs_cached_source_mismatches=0, common_baseline_box_mismatches=0,
        all_phase_cells_partition_full_native_clock=True, apex_is_exact_parent_subset=True,
        evidence_limit='Baseline overlap is not recall against hidden official GT; language scores are not calibrated highlight probabilities.')
    save('source_counts_private.json', detail)
    save('summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
