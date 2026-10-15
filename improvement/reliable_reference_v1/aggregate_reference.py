"""Combine only observed same-source points; dense evidence supersedes coarse evidence."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/reliable_reference_20261012_v1'


def read(name):
    return json.loads((REPORT / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pre_dense = '--pre-dense-audit' in sys.argv[1:]
    selections = read('source_selection.json')['rows'] + read('supplement_review_selection.json')['rows']
    selected = {row['case_id']: row for row in selections}
    assert len(selected) == len(selections) == 40
    assert len({row['source_group'] for row in selections}) == 40
    assert len({row['source_key'] for row in selections}) == 40
    material_kinds = ('dense02', 'supplement01') if pre_dense else ('dense02', 'supplement01', 'supplement_dense01')
    for kind in material_kinds:
        assert read(kind + '_local_acceptance.json')['status'].startswith('PASS')
    adjudication = read('detail02_adjudication.json')
    assert adjudication['end_band_exact'] is None
    source_rows = {name: dict(selection=selection, points={}, dense_events=[])
                   for name, selection in selected.items()}
    inputs = ['source_selection.json', 'supplement_review_selection.json',
              'source_separation_audit.json', 'supplement_source_separation_audit.json',
              'detail02_adjudication.json', 'COMPARISON_POLICY.md']
    kinds = ('initial', 'supplement01', 'dense02') if pre_dense else ('initial', 'supplement01', 'dense02', 'supplement_dense01')
    for kind in kinds:
        name = kind + '_consensus.json'
        consensus = read(name)
        inputs.append(name)
        dense = 'dense' in kind
        assert consensus['reference_level'] == 'AI_REVIEWED_SILVER_NOT_HUMAN_GOLD'
        assert consensus['candidate_predictions_read'] is False
        for side in ('a', 'b'):
            review_name = f'reviewer_{side}.json' if kind == 'initial' else f'reviewer_{side}_{kind}.json'
            assert sha(REPORT / review_name) == consensus['review_sha256'][side]
            inputs.append(review_name)
        for row in consensus['rows']:
            target = source_rows[row['case_id']]
            selection = target['selection']
            assert row['source_group'] == selection['source_group']
            assert row['source_sha256'] == selection['source_key']
            lo, hi = F(selection['clip_start']), F(selection['clip_end'])
            assert len(row['observations']) == len(row['sample_labels'])
            assert all(label in ('KEEP', 'ORDINARY', 'UNKNOWN') for label in row['sample_labels'])
            for observation, label in zip(row['observations'], row['sample_labels']):
                t = F(observation['exact_pts'])
                if not lo <= t < hi:
                    continue  # Context proves clipping; it is not an evaluation denominator.
                point = dict(exact_pts=str(t), ordinal=observation['ordinal'], label=label,
                             evidence_kind=kind, dense=dense)
                old = target['points'].get(t)
                if old:
                    assert old['ordinal'] == point['ordinal']
                    if old['dense'] and not dense:
                        continue
                    if old['dense'] == dense and old['label'] != label:
                        point['label'] = 'UNKNOWN'
                target['points'][t] = point
            if dense:
                for index, event in enumerate(row['matched_events']):
                    event = dict(event, evidence_kind=kind, event_index=index)
                    if kind == 'dense02' and row['case_id'] == 'R19' and event['end_band_exact'] == adjudication['initial_claimed_end_band_exact']:
                        event.update(end_band_exact=None, both_boundaries_observed=False,
                                     dense_verified=False, correction='detail02_adjudication.json')
                    if event['both_boundaries_observed'] and event['dense_verified']:
                        assert event['start_band_exact'] and event['end_band_exact']
                        event['core_exact_pts'] = [row['observations'][i]['exact_pts'] for i in event['core_ids']]
                        if not any(lo <= F(t) < hi for t in event['core_exact_pts']):
                            continue
                        target['dense_events'].append(event)
    output_rows = []
    for name in sorted(source_rows):
        row = source_rows[name]
        points = [row['points'][t] for t in sorted(row['points'])]
        counts = {label: sum(p['label'] == label for p in points) for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
        output_rows.append(dict(row['selection'], points=points,
                                counts=counts, dense_events=row['dense_events']))
    coverage = dict(sources=len(output_rows), keep_sources=sum(bool(r['counts']['KEEP']) for r in output_rows),
                    ordinary_sources=sum(bool(r['counts']['ORDINARY']) for r in output_rows),
                    two_ended_dense_events=sum(len(r['dense_events']) for r in output_rows),
                    **{label: sum(r['counts'][label] for r in output_rows) for label in ('KEEP', 'ORDINARY', 'UNKNOWN')})
    adequate = coverage['keep_sources'] >= 12 and coverage['ordinary_sources'] >= 8 and coverage['two_ended_dense_events'] >= 12
    result = dict(status='COVERAGE_SUFFICIENT_PENDING_CONTROLLER_FACT_CHECK' if adequate else 'STOP_REFERENCE_COVERAGE_INSUFFICIENT',
                  coverage=coverage, coverage_pass=adequate, reference_quality_pass=False,
                  pre_dense_audit=pre_dense, supplemental_dense_preparation_run=not pre_dense,
                  rows=output_rows, source_files_sha256={name: sha(REPORT / name) for name in inputs},
                  reference_level='AI_REVIEWED_SILVER_NOT_HUMAN_GOLD', candidate_predictions_read=False,
                  old_formal_quality_failed_preserved=True)
    output_name = 'coverage_diagnostic_01.json' if pre_dense else 'aggregate_reference_01.json'
    with (REPORT / output_name).open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
