"""Fail the original reference gate honestly; admit only bounded fact diagnostics."""
import hashlib
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2]/'reports/temporal_refinement_pilot_20261011'


def main():
    review = REPORT/'reference_review'
    readers = []
    hashes = {}
    for name in ['reviewer_a.json', 'reviewer_b.json']:
        path = review/name
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        doc = json.loads(path.read_text(encoding='utf-8'))
        cases = doc['cases']
        if len(cases) != 6 or len({c['case_id'] for c in cases}) != 6:
            raise ValueError('independent review source denominator differs')
        readers.append({c['case_id']: c for c in cases})
    samples = json.loads((REPORT/'preparation_receipt.json').read_text(encoding='utf-8'))['source_samples']
    merged = []
    for sample in samples:
        key = sample['case_id']
        raw = [r[key]['states'] for r in readers]
        if any(len(s) != 64 or any(x not in ['KEEP','ORDINARY','UNKNOWN'] for x in s) for s in raw):
            raise ValueError('invalid reviewer frame denominator or state')
        contact = review/f'contact_{key}.jpg'
        if hashlib.sha256(contact.read_bytes()).hexdigest() != sample['contact_sha256']:
            raise ValueError('reviewed preview does not bind to native frames')
        states = [a if a == b and a != 'UNKNOWN' else 'UNKNOWN' for a, b in zip(*raw)]
        counts = {s: states.count(s) for s in ['KEEP','ORDINARY','UNKNOWN']}
        merged.append(dict(case_id=key, states=states, counts=counts,
            contradictory_known_states=sum(a != b and a != 'UNKNOWN' and b != 'UNKNOWN' for a,b in zip(*raw)),
            source_sha256=sample['source_sha256'], source_group=sample['source_group'],
            sample_exact_pts=sample['sample_exact_pts'], window_start=sample['window_start'], window_end=sample['window_end']))
    known = sum(64-c['counts']['UNKNOWN'] for c in merged)
    checks = dict(each_source_known_at_least8=all(64-c['counts']['UNKNOWN'] >= 8 for c in merged),
        total_known_at_least96=known >= 96,
        keep_sources_at_least4=sum(c['counts']['KEEP'] > 0 for c in merged) >= 4,
        ordinary_sources_at_least2=sum(c['counts']['ORDINARY'] > 0 for c in merged) >= 2)
    consensus = dict(schema='DUAL_AI_VISUAL_SILVER_NOT_HUMAN_GOLD_V1', cases=merged, reviewers=hashes,
        audio_observed=False, sampled_observations=384, consensus_known=known,
        fresh_holdout=False, complete_continuous_reference=False, training_admitted=False, rematch_admitted=False)
    with (review/'consensus.json').open('x',encoding='utf-8') as f:
        json.dump(consensus,f,ensure_ascii=False,indent=2)
    decision = dict(status='STOP_REFERENCE_QUALITY_GATE', original_reference_checks=checks,
        original_quality_gate_passed=all(checks.values()), consensus_known=known, total_observations=384,
        consensus_counts={s:sum(c['counts'][s] for c in merged) for s in ['KEEP','ORDINARY','UNKNOWN']},
        per_case=[dict(case_id=c['case_id'], **c['counts']) for c in merged],
        scope='LIMITED_VISUAL_FACT_MECHANISM_DIAGNOSTIC_ONLY', limited_mechanism_admitted=known > 0,
        max_model_calls=12, quality_pass_allowed=False, training_admitted=False, rematch_admitted=False,
        consensus_sha256=hashlib.sha256((review/'consensus.json').read_bytes()).hexdigest(), reviewers=hashes,
        note='No original quality criterion waived or rewritten. UNKNOWN cases and all six sources retained.')
    if decision['original_quality_gate_passed']:
        raise ValueError('expected recorded sparse-reference limitation differs; re-audit scope')
    with (REPORT/'reference_admission.json').open('x',encoding='utf-8') as f:
        json.dump(decision,f,ensure_ascii=False,indent=2)
    print(json.dumps(decision,ensure_ascii=False))


if __name__ == '__main__':
    main()
