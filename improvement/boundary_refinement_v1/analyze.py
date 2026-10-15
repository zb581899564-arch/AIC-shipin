"""Rank predeclared context probes on frozen non-test weak references only."""
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from intervals import expanded_windows, merged, duration, overlap, native_membership

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/boundary_refinement_20261012_v1'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    registration_path = REPORT/'analysis_registration.json'
    export_path = REPORT/'developer_readonly_export.json'
    registration = json.loads(registration_path.read_text())
    exported = json.loads(export_path.read_text())
    entries = exported['entries']
    assert len(entries) == len({e['video_id'] for e in entries}) == 104
    assert sum(len(e['windows']) for e in entries) == 112
    assert len({e['source_group'] for e in entries}) == 96
    scores = []
    baseline_membership = {}
    exact_ranks = []
    for before, after in registration['analysis_grid_exact']:
        per_group = defaultdict(list)
        rows = []
        for entry in entries:
            assert entry['reference_role'] == 'FIXED_EXTERNAL_DOUBAO_WEAK_REFERENCE_NOT_HUMAN_TRUTH'
            start = F(entry['clip_start'])
            ref = merged([(start+F(str(a)), start+F(str(b)))
                          for a, b in entry['weak_reference']])
            pred = expanded_windows(entry['windows'], before, after)
            intersection = overlap(pred, ref)
            pred_seconds, ref_seconds = duration(pred), duration(ref)
            union = pred_seconds+ref_seconds-intersection
            iou = intersection/union if union else F(1)
            precision = intersection/pred_seconds if pred_seconds else F(0)
            recall = intersection/ref_seconds if ref_seconds else F(0)
            points = entry['native_clock']['exact_pts']
            chosen = native_membership(points, pred)
            if (before, after) == ('1/2', '1/2'):
                baseline_membership[entry['video_id']] = chosen
            else:
                assert baseline_membership[entry['video_id']] <= chosen
            per_group[entry['source_group']].append((iou, precision, recall))
            rows.append(dict(video_id=entry['video_id'], source_group=entry['source_group'],
                             weak_interval_iou=float(iou), weak_precision=float(precision),
                             weak_positive_recall=float(recall), selected_seconds=float(pred_seconds),
                             selected_native_frames=len(chosen),
                             added_native_frames=len(chosen-baseline_membership[entry['video_id']])))
        macro = tuple(sum((sum((v[k] for v in vs), F(0))/len(vs)
                           for vs in per_group.values()), F(0))/len(per_group)
                      for k in range(3))
        name = before+'_'+after
        exact_ranks.append((macro[0], -F(before)-F(after), -F(before), name))
        scores.append(dict(name=name, padding_exact=[before, after],
                           source_group_macro_iou=float(macro[0]), macro_iou_exact=str(macro[0]),
                           source_group_macro_weak_precision=float(macro[1]),
                           source_group_macro_weak_positive_recall=float(macro[2]),
                           selected_native_frames=sum(r['selected_native_frames'] for r in rows),
                           added_native_frames=sum(r['added_native_frames'] for r in rows),
                           rows=rows))
    ranked = sorted(exact_ranks, reverse=True)
    selected_name = ranked[0][3]
    if selected_name == '1/2_1/2':
        alternative = ranked[1]
        if alternative[0] == ranked[0][0]:
            selected_name = alternative[3]
            reason = 'Weak proxy exact tie; least added-duration nonbaseline probe'
        else:
            selected_name = '3/4_3/4'
            reason = 'Every probe weak proxy regresses; preregistered conservative risk fallback'
    else:
        reason = 'Highest predeclared source-group macro weak-reference interval IoU'
    selected = next(s for s in scores if s['name'] == selected_name)
    baseline = scores[0]
    b = {r['video_id']: r for r in baseline['rows']}
    for arm in scores:
        arm['videos_weak_proxy_improved'] = sum(r['weak_interval_iou'] > b[r['video_id']]['weak_interval_iou'] for r in arm['rows'])
        arm['videos_weak_proxy_regressed'] = sum(r['weak_interval_iou'] < b[r['video_id']]['weak_interval_iou'] for r in arm['rows'])
    consensus = json.loads((ROOT/'reports/temporal_refinement_pilot_20261011/reference_review/consensus.json').read_text())
    refs = {x['case_id']: x for x in consensus['cases']}
    partial = []
    for arm in scores:
        diagnostics = []
        for e in exported['accepted_partial_silver_baselines']:
            ref = refs[e['case_id']]
            assert e['source_sha256'] == ref['source_sha256']
            windows = [dict(start_exact=e['source_start'], end_exact=e['source_end'], segments=e['baseline_segments'])]
            intervals = expanded_windows(windows, *arm['padding_exact'])
            hits = {s:0 for s in ('KEEP','ORDINARY','UNKNOWN')}
            for state, point in zip(ref['states'], ref['sample_exact_pts']):
                hits[state] += any(a <= F(point) < b for a, b in intervals)
            diagnostics.append(dict(case_id=e['case_id'], selected_observations=hits, counts=ref['counts']))
        partial.append(dict(padding_exact=arm['padding_exact'], diagnostics=diagnostics))
    result = dict(status='PASS_PREDECLARED_NONTEST_WEAK_BOUNDARY_SCREEN_NOT_QUALITY',
                  source_group_count=96, developer_jobs=104, accepted_windows=112,
                  registration_sha256=sha(registration_path), export_sha256=sha(export_path),
                  arms=scores, selected_padding_exact=selected['padding_exact'], selection_reason=reason,
                  baseline_weak_macro_iou=baseline['source_group_macro_iou'],
                  selected_weak_macro_iou=selected['source_group_macro_iou'],
                  partial_silver_diagnostics=partial,
                  limitations=['External weak positive references; outside intervals not proven ordinary',
                               '32 prior-teacher source intersections retained as exposed, not independent human evaluation',
                               'Six-source silver reference has only two accepted original-B baselines; four failed/unrun excluded explicitly'],
                  historical_failed_quality_gate_preserved=True, formal_quality_pass=False,
                  new_model_calls=0, new_decoder_calls=0, new_optimizer_updates=0, rematch_inputs_read=False)
    with (REPORT/'developer_boundary_screen.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('arms','partial_silver_diagnostics')},ensure_ascii=False))
    print(json.dumps([dict(padding=a['padding_exact'],iou=a['source_group_macro_iou'],precision=a['source_group_macro_weak_precision'],recall=a['source_group_macro_weak_positive_recall'],added=a['added_native_frames'],improved=a['videos_weak_proxy_improved'],regressed=a['videos_weak_proxy_regressed']) for a in scores]))


if __name__ == '__main__':
    main()
