"""Fixed sparse-context development only; exposed confirm8 cannot enter this script."""
from fractions import Fraction as F
from pathlib import Path
import json
import random
from sparse_context_v1 import ARMS, window_spans
from evaluate_l16_intervals_07 import membership
from native_profile_04 import native64_windows, validate_original_origin, validate_reference_endpoints
from reference_intervals import paired_duration_metrics, measure
from qualify_l16_08 import admission
from stage_common_04 import read, save, sha
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/sparse_context_iteration_20261013_v1'
OUT=REPORT/'screen_01'


def source_comparison(prediction, reference, arm):
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
    baseline, candidate = [window_spans(windows, arm) for arm in ('D8_BASELINE', arm)]
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

def evaluate_group(predictions, references, group, arm):
    if group != 'screen':
        raise ValueError('Old confirmation is exposed; this module only permits screen12')
    expected = 12
    rows = [x for x in predictions if x['group'] == group]
    if len(rows) != expected or len({x['video_id'] for x in rows}) != expected:
        raise ValueError('Original 12/8 source denominator changed')
    results = [source_comparison(row, references[row['video_id']], arm) for row in rows]
    deltas = [F(x['delta_exact']) for x in results]
    macro = sum(deltas, F(0)) / expected
    changed = sum(x['actual_interval_changed'] and x['actual_native_frame_changed'] for x in results)
    passed = macro >= 0 and changed >= 3 and all(x['source_drop_gate'] for x in results)
    rng = random.Random(20261013)
    boot = sorted(float(sum((deltas[rng.randrange(expected)] for _ in range(expected)), F(0))/expected) for _ in range(5000))
    return dict(status='PASS_SPARSE_CONTEXT_FIXED_TEMPORAL_PROXY_GROUP' if passed else 'REJECT_SPARSE_CONTEXT_FIXED_TEMPORAL_PROXY_GROUP',
                group=group, sources=expected, macro_delta_exact=str(macro), macro_delta=float(macro),
                paired_bootstrap95=[boot[125], boot[4874]], bootstrap_seed=20261013, bootstrap_samples=5000,
                actual_changed_sources=changed, minimum_changed_sources=3, source_drop_limit_exact='1/100',
                original_fixed_gates_pass=passed, rows=results, new_model_calls=0, new_optimizer_updates=0,
                interpretation='All ten original manual interval duration-F1 averaged; not crop, author1fps GT or official score')

def fact_veto(arm):
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
        for recipe in ('D8_BASELINE', arm):
            spans = window_spans(entry['windows'], recipe)
            selected[recipe] = {label: set() for label in ('KEEP', 'ORDINARY', 'UNKNOWN')}
            for point in row['points']:
                time = F(point['exact_pts'])
                if time != F(entry['native_clock']['exact_pts'][point['ordinal']]):
                    raise ValueError('Fixed native fact timestamp changed')
                if any(a <= time < b for a, b in spans):
                    selected[recipe][point['label']].add(time)
        lost = selected['D8_BASELINE']['KEEP'] - selected[arm]['KEEP']
        added = selected[arm]['ORDINARY'] - selected['D8_BASELINE']['ORDINARY']
        checks.append(dict(case_id=row['case_id'], source_group=row['source_group'], core_lost=sorted(map(str, lost)),
                           ordinary_added=sorted(map(str, added)), unknown_added=len(selected[arm]['UNKNOWN']-selected['D8_BASELINE']['UNKNOWN']),
                           known_point_veto_pass=not lost and not added))
    if len(checks) != 40:
        raise ValueError('All forty unchanged facts required')
    passed = all(x['known_point_veto_pass'] for x in checks)
    return dict(pass_gate=passed, checks=checks, old40_quality_failed_preserved=True, UNKNOWN_not_relabelled=True,
                bindings=dict(reference_sha256=sha(ref_path), prediction_sha256=sha(pred_path)), new_model_calls=0)


def main():
    if OUT.exists():raise ValueError('Sparse screen already exists; do not rerun successful comparison')
    reg=read(REPORT/'registration_01.json')
    if reg['candidates']!=list(ARMS) or reg['coverage_ceiling_exact']!='1/2' or reg['minimum_raw_segment_seconds']!='8':
        raise ValueError('Registered density/length recipe changed')
    for key,path in [('rule_sha256',Path(__file__).with_name('sparse_context_v1.py')),('evaluation_sha256',Path(__file__)),('protocol_sha256',REPORT/'PROTOCOL.md')]:
        if reg[key]!=sha(path):raise ValueError('Before-results code/protocol changed')
    payload,references=admission()
    if reg['original_export_sha256']!=sha(ROOT/'reports/videoxum_reference_iteration_20261013_v1/cohort_external_export_08/developer_prediction_export.json'):
        raise ValueError('Original immutable B92 export changed')
    OUT.mkdir()
    save(OUT/'launch_claim.json',dict(registration_sha256=sha(REPORT/'registration_01.json'),old_confirm_not_reused=True,new_model_calls=0,new_optimizer_updates=0))
    facts={arm:fact_veto(arm) for arm in ARMS}
    save(OUT/'fixed_fact_veto.json',facts)
    scores={}
    for arm in ARMS:
        if facts[arm]['pass_gate']:
            scores[arm]=evaluate_group(payload['rows'],references,'screen',arm)
            save(OUT/(arm+'_screen.json'),scores[arm])
    eligible=[arm for arm in ARMS if arm in scores and scores[arm]['original_fixed_gates_pass']]
    chosen=None
    if eligible:
        chosen=min(eligible,key=lambda arm:(-F(scores[arm]['macro_delta_exact']),sum((F(row['added_duration_exact']) for row in scores[arm]['rows']),F(0)),ARMS.index(arm)))
        save(OUT/'selection_before_new_confirm.json',dict(chosen=chosen,coverage_ceiling_exact='1/2',minimum_raw_segment_seconds='8',extra_seconds='1/4',registration_sha256=sha(REPORT/'registration_01.json'),screen_sha256=sha(OUT/(chosen+'_screen.json')),fact_sha256=sha(OUT/'fixed_fact_veto.json'),new_unexposed_confirm_sources_required=8,old_confirm8_forbidden=True,no_threshold_retuning=True))
    result=dict(status='PASS_SPARSE_SCREEN_PENDING_NEW_UNEXPOSED_CONFIRM8' if chosen else 'STOP_SPARSE_CONTEXT_SCREEN_OR_FACT_REJECTED',chosen=chosen,qualified_for_package=False,eligible=eligible,scores={arm:dict(macro_delta=x['macro_delta'],changed_sources=x['actual_changed_sources'],gate=x['original_fixed_gates_pass']) for arm,x in scores.items()},fact_pass={arm:x['pass_gate'] for arm,x in facts.items()},confirmation_evaluated=False,new_model_calls=0,new_optimizer_updates=0,new_submission_zips=0,old_confirm_not_reused=True,all_old_failures_preserved=True)
    save(OUT/'result.json',result)
    print(json.dumps(result))
if __name__=='__main__':main()
