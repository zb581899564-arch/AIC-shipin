"""First metadata lineage QA for adopted scores; never repeat neural work."""
import hashlib
import json
import math
from pathlib import Path
import sys
import time


def ref(path):
    p = Path(path).resolve(strict=True)
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def main(root):
    n = Path(root).resolve(strict=True)
    workspace = n.parent.parent
    started = time.monotonic()
    adopted = []

    def read(r):
        path = Path(r['path']).resolve(strict=True)
        assert path.is_relative_to(workspace) and ref(path) == r
        return json.loads(path.read_text())

    registration = json.loads((n / 'registration31.json').read_text())
    support = read(registration['completion30_ref'])
    targets = []
    for role, refs in support['target_refs_by_role'].items():
        for target_ref in refs:
            target = read(target_ref)
            assert target['cohort'] == role
            targets.append(target_ref)
            for window in target['windows']:
                request = read(window['request_ref'])
                assert request['sid'] == target['sid'] and request['uid'] == window['uid']
                for group in window['groups']:
                    for variant in group['variants']:
                        if variant['kind'] != 'OLD_ACCEPTED_SUFFIX':
                            continue
                        original = read(variant['window_ref'])
                        assert original['labels_read'] is False
                        assert original['input_signature'] == request['input_signature']
                        slot = original['slots'][variant['slot']]
                        for arm, old_arm in [('real', 'real'), ('shifted', 'permuted')]:
                            copied = variant['original_' + arm + '_logp']
                            raw = slot[old_arm]['logprob']
                            assert math.isfinite(copied) and copied == raw, (window['uid'], variant['slot'], arm)
                        adopted.append((window['uid'], variant['slot']))
    acceptance = json.loads((n / 'acceptance31.json').read_text())
    assert len(adopted) * 2 == acceptance['old_logical_scores_adopted']
    output = dict(
        status='PASS_FIRST_OLD_SCORE_COPY_TO_RAW_LINEAGE_QA31',
        registration_ref=ref(n / 'registration31.json'),
        support_ref=registration['completion30_ref'], target_refs=targets,
        old_variants_checked=len(adopted), logical_real_shifted_scores_checked=2 * len(adopted),
        raw_neural_calls_repeated=0, new_model_calls=0, new_updates=0,
        numerical_scope='Exact stored scalar equality. 1e-6 readout flag is not an established old/new numerical error bound.',
        source_supervision_passed_to_GPU=False, seconds=time.monotonic() - started,
    )
    with (n / 'old_score_adoption_QA31.json').open('x') as f:
        json.dump(output, f, indent=2, allow_nan=False)
    print(json.dumps(dict(receipt_ref=ref(n / 'old_score_adoption_QA31.json'), receipt=output)))


if __name__ == '__main__':
    main(sys.argv[1])
