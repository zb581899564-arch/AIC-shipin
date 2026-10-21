"""First complete acceptable-set inference using31 scores, no model work."""
import hashlib
import json
from pathlib import Path
import resource
import time
from acceptable_program32_math import scan


def ref(path):
    p = Path(path).resolve(strict=True)
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def main():
    n = Path(__file__).resolve().parent
    workspace = n.parent.parent
    started = time.monotonic()
    reg = json.loads((n / 'registration32.json').read_text())
    assert reg['code_ref'] == ref(__file__)

    def read(r):
        p = Path(r['path']).resolve(strict=True)
        assert p.is_relative_to(workspace) and ref(p) == r
        return json.loads(p.read_text())

    p = read(reg['protocol_ref'])
    previous = read(reg['completion31_ref'])
    assert previous['unique_ledger'] == 'PASS' and previous['new_updates'] == 0
    review = read(previous['review_ref'])
    root31 = Path(reg['completion31_ref']['path']).parent
    reg31 = read(ref(root31 / 'registration31.json'))
    support = read(reg31['completion30_ref'])
    new = read(ref(root31 / 'gpu_completion31.json'))
    assert new['labels_read'] is False and new['original288TIME_bytes_frozen']
    score_by_uid = {s['uid']: s for r in new['score_refs'] for s in [read(r)]}
    old_review = {r['sid']: r for r in review['rows']}
    refs = []
    rows = []
    for role, targets in support['target_refs_by_role'].items():
        for r in targets:
            target = read(r)
            sid = target['sid']
            assert role == target['cohort'] and sid in support['source_partition'][role]
            original = read(target['input_ref'])
            lengths = [[g['native_count'] for g in w['groups']] for w in target['windows']]
            tp = [[g['TP'] for g in w['groups']] for w in target['windows']]
            assert lengths == original['lengths'] and tp == original['TP']
            outputs = {}
            for arm in ['real', 'shifted']:
                scores = []
                for window in target['windows']:
                    groups = []
                    for group in window['groups']:
                        variants = []
                        for v in group['variants']:
                            if v['kind'] == 'OLD_ACCEPTED_SUFFIX':
                                variants.append(v['original_' + arm + '_logp'])
                            else:
                                assert v['kind'] == 'NEW_EXACT_BASELINE_NOOP'
                                variants.append(score_by_uid[window['uid']][arm])
                        groups.append(max(variants))
                    scores.append(groups)
                result = scan(lengths, tp, target['gt'], scores, target['one_witness_program'],
                              target['baseline_program'], original['overlaps'],
                              chunk=p['chunk_programs'], maximum_programs=p['maximum_programs_per_source'],
                              maximum_exact_keys=p['maximum_exact_utility_keys_per_arm'],
                              deadline=started + p['maximum_CPU_seconds'])
                assert abs(result['threshold'] - target['witness_F1']) < 1e-12
                old = old_review[sid]['arms'][arm]
                assert result['MAP']['score'] == old['total_MAP_logp']
                assert abs(result['MAP']['utility'] - old['F1']) < 1e-12
                assert result['MAP']['choices'] == [v['winner_native_group'] for v in old['windows']]
                assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 <= p['maximum_RSS_bytes']
                path = n / (role + '_' + sid + '_' + arm + '_inference32.json')
                with path.open('x') as f:
                    json.dump(dict(sid=sid, role=role, arm=arm, target_ref=r, **result), f, indent=2, allow_nan=False)
                refs.append(ref(path))
                outputs[arm] = dict(programs=result['programs'], acceptable_programs=result['acceptable_programs'],
                                    threshold=result['threshold'], MAP_F1=result['MAP']['utility'],
                                    gold_F1=result['highest_score_acceptable']['utility'],
                                    MAP_to_gold_logp_gap=result['MAP']['score']-result['highest_score_acceptable']['score'],
                                    structured_loss=result['loss'],
                                    positive_MAP_regret=result['positive_MAP_regret'],
                                    gold_equals_witness=result['highest_score_acceptable']['choices']==target['one_witness_program'],
                                    augmented_equals_MAP=result['loss_augmented']['choices']==result['MAP']['choices'])
            rows.append(dict(sid=sid, role=role, forced_B=False, arms=outputs))
    for role, sids in support['source_partition'].items():
        for sid in sids:
            if sid not in {r['sid'] for r in rows}:
                assert old_review[sid]['forced_B']
                rows.append(dict(sid=sid, role=role, forced_B=True, no_fake_gold_or_score=True,
                                 baseline_F1=old_review[sid]['baseline_F1'], proposed_source_training_loss=0.))
    assert len(rows) == 8
    summary = dict(status='COMPLETE_EXACT_ACCEPTABLE_PROGRAM_CPU_INFERENCE_ONLY_NO_TRAINING_ADMISSION',
                   completion31_ref=reg['completion31_ref'], protocol_ref=reg['protocol_ref'], outputs=refs, rows=rows,
                   seconds=time.monotonic()-started, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                   new_model_calls=0, new_gradients=0, new_updates=0, official_submissions=0, new_ZIP=0,
                   numerical_scope='All stored model scores summed in exact dyadic units; near utility/augmented comparisons use exact Fraction. Algorithm budget exhaustion fails, no approximate gold.',
                   scope='New witness-threshold acceptable set, not29 all-reference-optimal-gold objective; does not establish learnability.',
                   automatic_training=False, production_admitted=False)
    with (n / 'completion32.json').open('x') as f:
        json.dump(summary, f, indent=2, allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(n / 'completion32.json'), receipt={k:v for k,v in summary.items() if k!='outputs'})))


if __name__ == '__main__':
    main()
