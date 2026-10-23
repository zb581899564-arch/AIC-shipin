"""CPU proof of joint-source counterfactual score gradient and idempotent runtime binding."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import itertools
import math
import traceback

import numpy as np

from joint_reward43 import source_counterfactuals
from native_sets import union_components
from preference_reward import SummaryReview, summary_agreement
from t_io import ROOT, save

OUT = ROOT / 'joint_contract43'


def action(index, selected):
    result = np.zeros(3, dtype=bool)
    if selected:
        result[[0, 1] if index == 0 else [1, 2]] = True
    return result


def expected(theta):
    p = 1 / (1 + math.exp(-theta))
    observed = np.ones(3, dtype=bool)
    review = SummaryReview('original_rater', np.array([True, False, True]), observed)
    total, score_gradient, naive_window_gradient = 0.0, 0.0, 0.0
    allowed = {name: observed for name in ['a', 'b']}
    greedy = {name: action(index, p >= .5) for index, name in enumerate(['a', 'b'])}
    for choices in itertools.product([0, 1], repeat=2):
        probability = math.prod(p if value else 1 - p for value in choices)
        sampled = {name: action(index, value) for index, (name, value) in enumerate(zip(['a', 'b'], choices))}
        reward = summary_agreement(union_components(sampled, 3), [review], 1)['mean_f1']
        counterfactual = source_counterfactuals(sampled, greedy, allowed, [review], 1)
        total += probability * reward
        score_gradient += probability * sum(counterfactual['per_window'][name]['advantage'] * (value - p)
                                            for name, value in zip(['a', 'b'], choices))
        naive_window_gradient += probability * reward * sum(value - p for value in choices)
    return total, score_gradient, naive_window_gradient


def main():
    OUT.mkdir()
    theta, step = .2, 1e-5
    _, actual, ordinary = expected(theta)
    difference = (expected(theta + step)[0] - expected(theta - step)[0]) / (2 * step)
    if abs(actual - difference) > 1e-9 or abs(actual - ordinary) > 1e-12:
        raise ValueError('Joint source counterfactual baseline changes expected score gradient')
    from t_runtime39 import runtime, grammar
    first, second = runtime(), runtime()
    if first is not second or grammar() is not grammar():
        raise ValueError('Canonical runtime binding is not idempotent')
    save(OUT / 'completion.json', dict(state='PASS_JOINT_SOURCE_COUNTERFACTUAL_AND_RUNTIME_CONTRACT',
        exact_enumerated_two_overlapping_window_states=4,
        counterfactual_expected_gradient=actual, direct_score_expected_gradient=ordinary,
        central_difference=difference, runtime_initialized_once=True, grammar_import_after_binding=True,
        actual8B_calls=0, optimizer_updates=0,
        scope='Finite CPU score-function example only, not exact low-precision8B rollout gradient or quality proof'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
