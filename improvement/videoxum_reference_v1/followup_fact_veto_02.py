"""New preregistered external fact-only screening for L16/L32, not blind confirmation."""
import json
from fractions import Fraction

from known_fact_veto import ROOT, REPORT, read, sha
from lead_guard_v2 import ARMS, window_spans


def main():
    output = REPORT / 'followup_fact_veto_02.json'
    if output.exists():
        raise FileExistsError('Already completed new follow-up fact screen')
    registration = read(REPORT / 'followup_registration_02.json')
    rejected = read(REPORT / 'known_fact_veto_01.json')
    if rejected['pass'] or rejected['candidate'] != 'LONG8_LEAD025':
        raise RuntimeError('Original L8 factual failure must remain rejected')
    if registration['thresholds_seconds'] != {k: str(v) for k, v in ARMS.items()}:
        raise RuntimeError('Before-results threshold registration changed')
    reference_path = ROOT / 'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'
    export_path = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
    reference = read(reference_path)
    if reference['reference_quality_pass'] or reference['coverage_pass']:
        raise RuntimeError('Old insufficient coverage must remain failed')
    entries = {entry['video_id']: entry for entry in read(export_path)['entries']}
    checks = {arm: [] for arm in ARMS}
    for row in reference['rows']:
        entry = entries[row['video_id']]
        if any(entry[key] != row[key] for key in ('source_group', 'source_key', 'clock_sha256')):
            raise RuntimeError('Unchanged known fact source binding required')
        spans = {arm: window_spans(entry['windows'], arm) for arm in ('D8_BASELINE', *ARMS)}
        selected = {}
        for arm, intervals in spans.items():
            selected[arm] = {label: set() for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
            for point in row['points']:
                time = Fraction(point['exact_pts'])
                if time != Fraction(entry['native_clock']['exact_pts'][point['ordinal']]):
                    raise RuntimeError('Original native fact timestamp changed')
                if any(a <= time < b for a, b in intervals):
                    selected[arm][point['label']].add(time)
        for arm in ARMS:
            lost = selected['D8_BASELINE']['KEEP'] - selected[arm]['KEEP']
            added = selected[arm]['ORDINARY'] - selected['D8_BASELINE']['ORDINARY']
            checks[arm].append({'case_id': row['case_id'], 'source_group': row['source_group'],
                                'core_lost': sorted(str(x) for x in lost),
                                'ordinary_added': sorted(str(x) for x in added),
                                'unknown_added': len(selected[arm]['UNKNOWN'] - selected['D8_BASELINE']['UNKNOWN']),
                                'known_point_veto_pass': not lost and not added})
    if any(len(rows) != 40 for rows in checks.values()):
        raise RuntimeError('All forty unchanged external fact cases required')
    eligible = [arm for arm in ARMS if all(row['known_point_veto_pass'] for row in checks[arm])]
    result = {'status': 'NEW_EXTERNAL_FACT_SCREEN_COMPLETE_NOT_HUMAN_CONFIRMATION',
              'eligible_for_new_human_screen': eligible, 'checks': checks,
              'original_L8_factual_failure_preserved': True, 'old40_quality_failed_preserved': True,
              'new_model_calls': 0, 'candidate_package_admitted': False,
              'bindings': {'registration_sha256': sha(REPORT / 'followup_registration_02.json'),
                           'original_L8_failure_sha256': sha(REPORT / 'known_fact_veto_01.json'),
                           'original_reference_sha256': sha(reference_path),
                           'original_B_external_export_sha256': sha(export_path)}}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'eligible': eligible,
                      'ordinary_added': {arm: sum(len(row['ordinary_added']) for row in rows) for arm, rows in checks.items()},
                      'new_model_calls': 0}))


if __name__ == '__main__':
    main()
