"""Partial known-observation mechanisms only; no official score or quality PASS."""
import json
from fractions import Fraction
from pathlib import Path
from contract import selected

REPORT = Path(__file__).resolve().parents[2]/'reports/temporal_refinement_pilot_20261011'


def score(states, mask, weights):
    tp = sum(s == 'KEEP' and m for s,m in zip(states,mask))
    fn = sum(s == 'KEEP' and not m for s,m in zip(states,mask))
    fp = sum(s == 'ORDINARY' and m for s,m in zip(states,mask))
    return dict(known_positive_ids=tp+fn, known_negative_ids=states.count('ORDINARY'), true_positive_ids=tp,
        missed_keep_ids=fn, ordinary_selected_ids=fp,
        unknown_selected_ids=sum(s == 'UNKNOWN' and m for s,m in zip(states,mask)),
        recall=tp/(tp+fn) if tp+fn else None,
        partial_known_f1=2*tp/(2*tp+fp+fn) if tp+fn else None,
        ordinary_support_seconds_estimate=float(sum(w for s,m,w in zip(states,mask,weights) if s == 'ORDINARY' and m)))


def main():
    receipt = json.loads((REPORT/'inference_receipt_v2.json').read_text(encoding='utf-8'))
    if 'inference_completion.json' not in receipt['files']:
        raise ValueError('inference did not complete; do not fabricate missing rows')
    docs = {name: json.loads(entry['text']) for name,entry in receipt['files'].items() if name.endswith('.json')}
    completion = docs['inference_completion.json']
    replay = docs['independent_cpu_replay.json']
    if replay['CUDA_initialized'] or len(replay['proofs']) != completion['actual_model_calls']:
        raise ValueError('independent actual-call processor replay denominator differs')
    ref = json.loads((REPORT/'reference_review/consensus.json').read_text(encoding='utf-8'))
    predictions = {r['case_id']:r for r in completion['rows']}
    if set(predictions) != {r['case_id'] for r in ref['cases']}:
        raise ValueError('full six-source prediction/reference denominator mismatch')
    rows = []
    for c in ref['cases']:
        points = [Fraction(p) for p in c['sample_exact_pts']]
        lo, hi = Fraction(c['window_start']), Fraction(c['window_end'])
        relative = [p-lo for p in points]
        midpoints = [lo]+[(a+b)/2 for a,b in zip(points,points[1:])]+[hi]
        weights = [b-a for a,b in zip(midpoints,midpoints[1:])]
        r = predictions[c['case_id']]
        old = [selected(r['baseline_segments'],p) for p in relative]
        new = [selected(r['refined_segments'],p) for p in relative]
        if any(b and not a for a,b in zip(old,new)):
            raise ValueError('candidate-only verifier introduced a new observed selection')
        lost = [i for i,(s,a,b) in enumerate(zip(c['states'],old,new)) if s == 'KEEP' and a and not b]
        baseline_missed = [i for i,(s,a) in enumerate(zip(c['states'],old)) if s == 'KEEP' and not a]
        ordinary_removed = [i for i,(s,a,b) in enumerate(zip(c['states'],old,new)) if s == 'ORDINARY' and a and not b]
        core = [i for i,s in enumerate(c['states']) if s == 'KEEP']
        rows.append(dict(case_id=c['case_id'], counts=c['counts'], baseline=score(c['states'],old,weights),
            refined=score(c['states'],new,weights), baseline_missed_known_keep_ids=baseline_missed,
            verifier_deleted_known_keep_ids=lost, verifier_removed_known_ordinary_ids=ordinary_removed,
            baseline_segments=r['baseline_segments'], refined_segments=r['refined_segments'],
            known_core_first_last_observation=([dict(id=core[0],native_pts=str(points[core[0]])),
                dict(id=core[-1],native_pts=str(points[core[-1]]))] if core else []),
            exact_continuous_boundary_error='NOT_AVAILABLE_SPARSE_AI_REFERENCE'))
    positive = [r for r in rows if r['counts']['KEEP'] > 0]
    n = len(positive)
    lost = sum(len(r['verifier_deleted_known_keep_ids']) for r in rows)
    missed = sum(len(r['baseline_missed_known_keep_ids']) for r in rows)
    result = dict(status='STOP_MECHANISM_DELETES_KNOWN_CORE' if lost else 'BOUNDED_MECHANISM_OBSERVATION_ONLY_NO_QUALITY_ADMISSION',
        source_rows=6, observations=384, scored_consensus_ids=ref['consensus_known'], unknown_ids=384-ref['consensus_known'],
        positive_reference_sources=n, rows=rows, deleted_previously_selected_known_keep_ids=lost,
        original_baseline_missed_known_keep_ids=missed,
        removed_known_ordinary_ids=sum(len(r['verifier_removed_known_ordinary_ids']) for r in rows),
        partial_known_f1_macro_baseline=sum(r['baseline']['partial_known_f1'] for r in positive)/n if n else None,
        partial_known_f1_macro_refined=sum(r['refined']['partial_known_f1'] for r in positive)/n if n else None,
        metrics_are_partial_sampled_AI_reference_not_official=True,
        quality_pass=False, reference_quality_gate_passed=False, training_admitted=False, rematch_admitted=False,
        actual_model_calls=completion['actual_model_calls'], new_optimizer_updates=0, new_426_inference=0,
        official_score=None, new_submission_zip=None)
    with (REPORT/'mechanism_diagnostic.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))


if __name__ == '__main__':
    main()
