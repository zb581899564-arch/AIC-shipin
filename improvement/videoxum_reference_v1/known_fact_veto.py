"""Evaluate the new declared recipe once on the unchanged forty external fact cases."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

from reference_intervals import candidate_spans, merged

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/videoxum_reference_iteration_20261013_v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projected_windows(windows, arm):
    result = []
    for window in windows:
        start, end = Fraction(window['start_exact']), Fraction(window['end_exact'])
        absolute = [(start + Fraction(str(a)), start + Fraction(str(b))) for a, b in window['segments']]
        result.extend(candidate_spans(absolute, start, end, arm))
    return merged(result)


def main():
    output = REPORT / 'known_fact_veto_01.json'
    if output.exists():
        raise FileExistsError('Do not repeat completed fact check')
    reference_path = ROOT / 'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'
    export_path = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
    reference = read(reference_path)
    if reference['reference_quality_pass'] or reference['coverage_pass']:
        raise RuntimeError('Original insufficient coverage must remain failed')
    entries = {row['video_id']: row for row in read(export_path)['entries']}
    checks = []
    for row in reference['rows']:
        entry = entries[row['video_id']]
        if any(entry[key] != row[key] for key in ('source_group', 'source_key', 'clock_sha256')):
            raise RuntimeError('Original reference/source identity changed')
        intervals = {arm: projected_windows(entry['windows'], arm)
                     for arm in ('D8_BASELINE', 'LONG8_LEAD025')}
        chosen = {}
        for arm, spans in intervals.items():
            chosen[arm] = {label: set() for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
            for point in row['points']:
                time = Fraction(point['exact_pts'])
                if time != Fraction(entry['native_clock']['exact_pts'][point['ordinal']]):
                    raise RuntimeError('Exact native reference point mismatch')
                if any(a <= time < b for a, b in spans):
                    chosen[arm][point['label']].add(time)
        lost = chosen['D8_BASELINE']['KEEP'] - chosen['LONG8_LEAD025']['KEEP']
        added = chosen['LONG8_LEAD025']['ORDINARY'] - chosen['D8_BASELINE']['ORDINARY']
        checks.append({'case_id': row['case_id'], 'source_group': row['source_group'],
                       'core_lost': sorted(str(t) for t in lost),
                       'ordinary_added': sorted(str(t) for t in added),
                       'unknown_added': len(chosen['LONG8_LEAD025']['UNKNOWN'] - chosen['D8_BASELINE']['UNKNOWN']),
                       'known_point_veto_pass': not lost and not added})
    if len(checks) != 40 or len({row['case_id'] for row in checks}) != 40:
        raise RuntimeError('Expected all unchanged forty external cases')
    passed = all(row['known_point_veto_pass'] for row in checks)
    result = {'status': 'PASS_NEW_RECIPE_PARTIAL_FACT_VETO_NOT_HUMAN_QUALITY' if passed else 'REJECT_NEW_RECIPE_KNOWN_FACT_VETO',
              'candidate': 'LONG8_LEAD025', 'baseline': 'D8_BASELINE', 'pass': passed,
              'checks': checks, 'old_reference_quality_failed_preserved': True,
              'UNKNOWN_not_relabelled': True, 'bindings': {
                  'protocol_sha256': sha(REPORT / 'PROTOCOL.md'),
                  'recipe_code_sha256': sha(Path(__file__).parent / 'reference_intervals.py'),
                  'original_reference_sha256': sha(reference_path),
                  'original_B_external_export_sha256': sha(export_path)},
              'new_model_calls': 0, 'new_optimizer_updates': 0, 'candidate_package_admitted': False}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'status': result['status'], 'failed_cases': [row['case_id'] for row in checks if not row['known_point_veto_pass']],
                      'ordinary_added': sum(len(row['ordinary_added']) for row in checks), 'new_model_calls': 0}))


if __name__ == '__main__':
    main()
