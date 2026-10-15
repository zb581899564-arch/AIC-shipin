"""Limited known-point veto after human comparison, never an alternative quality gate."""
import json
from fractions import Fraction as F

from evaluate_candidates_v3 import ROOT, REPORT, ARMS, read, sha, save
from intervals import expanded_windows


def main():
    comparison_path = REPORT / 'comparison_v3_01/human_comparison.json'
    comparison = read(comparison_path)
    assert comparison['status'] == 'HUMAN_PROXY_COMPLETE_PENDING_PARTIAL_SILVER_FACT_VETO'
    assert comparison['candidate_package_admitted'] is False
    candidates = comparison['human_eligible']
    assert all(arm in ('A', 'B', 'C') for arm in candidates) and len(set(candidates)) == len(candidates)
    output = REPORT / 'comparison_v3_01/partial_silver_veto.json'
    if output.exists():
        raise FileExistsError('Already completed known-point veto; never rerun successful comparison')
    checks = {arm: [] for arm in candidates}
    bindings = dict(human_comparison_sha256=sha(comparison_path))
    if candidates:
        reference_path = ROOT / 'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'
        reference = read(reference_path)
        assert reference['reference_quality_pass'] is False and reference['coverage_pass'] is False
        assert reference['coverage'] == dict(sources=40, keep_sources=6, ordinary_sources=9,
            two_ended_dense_events=1, KEEP=184, ORDINARY=222, UNKNOWN=2675)
        export_path = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
        entries = {row['video_id']: row for row in read(export_path)['entries']}
        bindings.update(partial_reference_sha256=sha(reference_path), external_B_export_sha256=sha(export_path))
        for row in reference['rows']:
            entry = entries[row['video_id']]
            assert entry['source_group'] == row['source_group'] and entry['source_key'] == row['source_key']
            assert entry['clock_sha256'] == row['clock_sha256']
            for point in row['points']:
                assert F(entry['native_clock']['exact_pts'][point['ordinal']]) == F(point['exact_pts'])
            intervals = {arm: expanded_windows(entry['windows'], *ARMS[arm]) for arm in ('baseline', *candidates)}
            chosen = {arm: {label: {F(p['exact_pts']) for p in row['points'] if p['label'] == label and
                       any(a <= F(p['exact_pts']) < b for a, b in spans)}
                       for label in ('KEEP', 'ORDINARY', 'UNKNOWN')} for arm, spans in intervals.items()}
            for arm in candidates:
                core_lost = chosen['baseline']['KEEP'] - chosen[arm]['KEEP']
                ordinary_added = chosen[arm]['ORDINARY'] - chosen['baseline']['ORDINARY']
                checks[arm].append(dict(case_id=row['case_id'], source_group=row['source_group'],
                    core_lost=sorted(str(t) for t in core_lost),
                    ordinary_added=sorted(str(t) for t in ordinary_added),
                    unknown_added=len(chosen[arm]['UNKNOWN'] - chosen['baseline']['UNKNOWN']),
                    known_point_veto_pass=not core_lost and not ordinary_added))
        assert len(reference['rows']) == 40 and all(len(rows) == 40 for rows in checks.values())
    eligible = [arm for arm in candidates if all(row['known_point_veto_pass'] for row in checks[arm])]
    result = dict(status='PASS_HUMAN_PROXY_AND_PARTIAL_FACT_RISK_SCREEN' if eligible else 'STOP_NO_ELIGIBLE_CANDIDATE',
        eligible=eligible, padding_exact={arm: ARMS[arm] for arm in eligible}, checks=checks, bindings=bindings,
        old_reference_quality_failed_preserved=True, missing_action_boundaries_remain_unknown=True,
        partial_fact_reference_does_not_replace_human_reference=True, human_proxy_not_official_quality=True,
        new_model_calls=0, new_optimizer_updates=0, official_score='UNKNOWN')
    save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
