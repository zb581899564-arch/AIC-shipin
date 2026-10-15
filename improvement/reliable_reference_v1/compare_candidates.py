"""Open cached external predictions only after the explicit reference admission."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/reliable_reference_20261012_v1'
sys.path.insert(0, str(ROOT / 'improvement/boundary_refinement_v1'))
from intervals import expanded_windows, duration, overlap

ARMS = {'baseline': ('3/4', '1/2'), 'A': ('1', '1/2'), 'B': ('3/4', '1/4')}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def inside(t, intervals):
    return any(lo <= t < hi for lo, hi in intervals)


def average(values):
    return sum(values, F(0)) / len(values) if values else None


def local_iou(intervals, start, end, domain):
    lo, hi = domain
    clipped = [(max(a, lo), min(b, hi)) for a, b in intervals if max(a, lo) < min(b, hi)]
    start, end = max(start, lo), min(end, hi)
    assert start < end
    common = overlap(clipped, [(start, end)])
    union = duration(clipped) + end - start - common
    return common / union if union else F(0)


def evaluate(reference, entries, approved, role, arm_names):
    records = []
    for row in reference['rows']:
        if row['role'] != role:
            continue
        entry = entries[row['video_id']]
        assert entry['source_group'] == row['source_group'] and entry['source_key'] == row['source_key']
        assert entry['clock_sha256'] == row['clock_sha256']
        clock = entry['native_clock']['exact_pts']
        for point in row['points']:
            assert F(clock[point['ordinal']]) == F(point['exact_pts'])
        arms = {name: expanded_windows(entry['windows'], *ARMS[name]) for name in arm_names}
        known = {label: [F(p['exact_pts']) for p in row['points'] if p['label'] == label]
                 for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
        selections = {name: {label: {t for t in times if inside(t, intervals)} for label, times in known.items()}
                      for name, intervals in arms.items()}
        metrics = {}
        for name in arm_names:
            selected = selections[name]
            base = selections['baseline']
            metrics[name] = dict(
                keep_fraction=F(len(selected['KEEP']), len(known['KEEP'])) if known['KEEP'] else None,
                ordinary_fraction=F(len(selected['ORDINARY']), len(known['ORDINARY'])) if known['ORDINARY'] else None,
                unknown_selected=len(selected['UNKNOWN']),
                core_lost=sorted(str(t) for t in base['KEEP'] - selected['KEEP']),
                ordinary_added=sorted(str(t) for t in selected['ORDINARY'] - base['ORDINARY']),
                selected_duration=duration(arms[name]),
                boundary_delta=[[] for _ in range(4)],
            )
        events = []
        for event in row['dense_events']:
            event_id = f"{row['case_id']}:{event['evidence_kind']}:{event['event_index']}"
            if event_id not in approved:
                continue
            starts = list(map(F, event['start_band_exact']))
            ends = list(map(F, event['end_band_exact']))
            assert starts[1] < ends[0], 'Overlapping start/end uncertainty must be adjudicated before comparison'
            domain = (max(F(row['clip_start']), starts[0]-1), min(F(row['clip_end']), ends[1]+1))
            corners = [(a, b) for a in starts for b in ends]
            values = {name: [local_iou(intervals, a, b, domain) for a, b in corners]
                      for name, intervals in arms.items()}
            for name in arm_names:
                for corner in range(4):
                    metrics[name]['boundary_delta'][corner].append(values[name][corner] - values['baseline'][corner])
            events.append(dict(event_id=event_id, start_band_exact=event['start_band_exact'],
                               end_band_exact=event['end_band_exact'], local_iou=values))
        for name in arm_names:
            metrics[name]['boundary_delta'] = [average(values) for values in metrics[name]['boundary_delta']]
        records.append(dict(case_id=row['case_id'], source_group=row['source_group'], role=row['role'],
                            denominators={label: len(values) for label, values in known.items()},
                            metrics=metrics, events=events))
    return records


def summarize(records, role, arm):
    subset = [record for record in records if record['role'] == role]
    keep = [r['metrics'][arm]['keep_fraction'] - r['metrics']['baseline']['keep_fraction']
            for r in subset if r['denominators']['KEEP']]
    ordinary = [r['metrics'][arm]['ordinary_fraction'] - r['metrics']['baseline']['ordinary_fraction']
                for r in subset if r['denominators']['ORDINARY']]
    corners = [average([r['metrics'][arm]['boundary_delta'][i] for r in subset
                        if r['metrics'][arm]['boundary_delta'][i] is not None]) for i in range(4)]
    factual_harm = [r['case_id'] for r in subset if r['metrics'][arm]['core_lost'] or r['metrics'][arm]['ordinary_added']]
    enough = bool(keep and ordinary and all(c is not None for c in corners))
    viable = enough and not factual_harm and all(c >= 0 for c in corners)
    return dict(role=role, arm=arm, keep_sources=len(keep), ordinary_sources=len(ordinary),
                core_delta=average(keep), ordinary_delta=average(ordinary), corner_deltas=corners,
                factual_harm_sources=factual_harm, viable=viable)


def encode(value):
    if isinstance(value, F):
        return dict(exact=str(value), value=float(value))
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    return value


def main():
    admission_path = REPORT / 'reference_admission_01.json'
    admission = read(admission_path)
    assert admission['reference_quality_pass'] is True, 'Reference-first gate has not passed'
    assert admission['candidate_predictions_read'] is False
    reference_path = REPORT / 'aggregate_reference_01.json'
    assert sha(reference_path) == admission['aggregate_sha256']
    assert sha(REPORT / 'COMPARISON_POLICY.md') == admission['comparison_policy_sha256']
    output = REPORT / 'comparison_01'
    output.mkdir(exist_ok=False)
    save(output / 'launch_claim.json', dict(reference_admission_sha256=sha(admission_path),
                                           script_sha256=sha(Path(__file__)), new_model_calls=0))
    reference = read(reference_path)
    export_path = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
    export = read(export_path)  # No prediction access occurs before the admission above.
    entries = {row['video_id']: row for row in export['entries']}
    approved = set(admission['approved_dense_event_ids'])
    records = evaluate(reference, entries, approved, 'screen', ('baseline', 'A', 'B'))
    screen = {arm: summarize(records, 'screen', arm) for arm in ('A', 'B')}
    eligible = [arm for arm in ('A', 'B') if screen[arm]['viable']]
    def ranking(arm):
        score = screen[arm]
        return (score['core_delta'], -score['ordinary_delta'], average(score['corner_deltas']), arm == 'A')
    chosen = max(eligible, key=ranking) if eligible else None
    save(output / 'screen_selection.json', encode(dict(chosen=chosen, screen=screen,
                                                       frozen_before_confirm=True, padding_exact=ARMS.get(chosen))))
    if chosen:
        records += evaluate(reference, entries, approved, 'confirm', ('baseline', chosen))
    confirm = summarize(records, 'confirm', chosen) if chosen else None
    passed = bool(confirm and confirm['viable'])
    result = dict(status='PASS_FACT_DIAGNOSTIC_RISK_CANDIDATE' if passed else 'STOP_FACT_DIAGNOSTIC',
                  chosen=chosen, padding_exact=ARMS.get(chosen), screen=screen, confirm=confirm,
                  candidate_admitted=passed, records=records,
                  reference_admission_sha256=sha(admission_path), cached_export_sha256=sha(export_path),
                  candidate_predictions_read=True, new_model_calls=0, optimizer_updates=0,
                  official_score='UNKNOWN', not_human_editorial_gold=True,
                  no_confirm_fallback_or_retuning=True)
    save(output / 'comparison_result.json', encode(result))
    print(json.dumps(encode({key: value for key, value in result.items() if key != 'records'}), ensure_ascii=False))


if __name__ == '__main__':
    main()
