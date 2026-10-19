"""Exact integer-cost multiple-choice knapsack with an explicit null action.

No data, labels, models or experiment entry points are read by this module.
Utilities are the supplied finite float64 values: no clipping, rescaling,
rounding or epsilon is introduced. "Exact" describes the complete discrete DP,
not arbitrary-precision arithmetic on real numbers.
"""
from collections.abc import Mapping
import itertools
import math
import operator

import numpy as np


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(name+' must be an integer, not bool')
    try:
        return operator.index(value)
    except TypeError as error:
        raise ValueError(name+' must be an integer') from error


def _frontier(sid, actions, budget):
    """Cost/gain dominance includes the implicit zero-cost, zero-gain null."""
    actions = [] if actions is None else list(actions)
    by_index = {}
    nulls = zeros = duplicates = 0
    for action in actions:
        if action is None:
            nulls += 1
            continue
        if not isinstance(action, Mapping):
            raise ValueError('Each action must be a mapping or None')
        index = action.get('candidate_index')
        if index is None:
            if action.get('added_frames', 0) != 0 or action.get('predicted_gain', 0.) != 0:
                raise ValueError('An explicit null must have zero cost/utility')
            nulls += 1
            continue
        index = _integer(index, 'candidate_index')
        cost = _integer(action['added_frames'], 'added_frames')
        gain = float(action['predicted_gain'])
        if index < 0 or cost < 0 or not math.isfinite(gain) or gain < 0:
            raise ValueError('Candidate index/cost must be nonnegative and gain finite/nonnegative')
        if gain == 0:
            zeros += 1  # Null dominates every zero-utility real action.
            continue
        if cost == 0:
            raise ValueError('A positive real action must add at least one native frame')
        value = dict(candidate_index=index, added_frames=cost, predicted_gain=gain)
        if index in by_index:
            if by_index[index] != value:
                raise ValueError('Ambiguous duplicate candidate_index for source '+str(sid))
            duplicates += 1
        else:
            by_index[index] = value
    positive = list(by_index.values())
    # For a common cost, larger utility wins; exact utility ties retain the
    # lower original candidate index. Across costs, equal gain at higher cost
    # is dominated irrespective of index, because total cost precedes index.
    ordered = sorted(positive, key=lambda a: (a['added_frames'], -a['predicted_gain'], a['candidate_index']))
    frontier = []
    largest_gain = 0.
    for action in ordered:
        if action['predicted_gain'] > largest_gain:
            frontier.append(action)
            largest_gain = action['predicted_gain']
    feasible = [action for action in frontier if action['added_frames'] <= budget]
    original_indices = sorted(by_index)
    key = {index: rank for rank, index in enumerate(original_indices)}
    statistics = dict(input_entries=len(actions), explicit_null_entries=nulls,
        zero_utility_dominated_by_null=zeros, identical_duplicate_entries=duplicates,
        positive_candidates=len(positive), individually_budget_feasible=sum(a['added_frames'] <= budget for a in positive),
        pareto_candidates=len(frontier), pareto_budget_feasible=len(feasible),
        positive_dominated_candidates=len(positive)-len(frontier))
    return feasible, statistics, key, len(original_indices)


def knapsack(actions_by_source, budget):
    """Return a source->candidate selection and exact-cost DP audit statistics.

    ``actions_by_source`` is an insertion-ordered mapping from sid to a sequence
    of ``{candidate_index, added_frames, predicted_gain}`` or ``None``. Null is
    always available, including for an empty source. Exact zero-utility options
    are dominated by null; negative/nonfinite gains and positive zero-cost
    options are errors, never silent nulls.

    Deterministic objective order: greatest utility, least total native cost,
    then lexicographically lowest original candidate indices in the supplied
    source order (null sorts after all real indices for its source). Only the
    previous source row may feed a transition, so no source can contribute two
    candidates. Per-source Pareto pruning preserves this objective order.

    Returns ``chosen`` (sid->original candidate_index; ``selected`` is an alias), ``total_cost``,
    ``total_utility``, and ``per_source`` counts before/after Pareto/budget
    filtering. No caller action is mutated.
    """
    if not isinstance(actions_by_source, Mapping):
        raise ValueError('actions_by_source must be a source-ordered mapping')
    budget = _integer(budget, 'budget')
    if budget < 0:
        raise ValueError('budget must be nonnegative')
    source_order = list(actions_by_source)
    if any(not isinstance(sid, (str, int)) or isinstance(sid, bool) for sid in source_order):
        raise ValueError('Source IDs must be JSON-serializable strings or integer IDs')
    prepared = [_frontier(sid, actions_by_source[sid], budget) for sid in source_order]
    score = np.full(budget+1, -np.inf, np.float64)
    score[0] = 0.
    infinity_rank = np.iinfo(np.int64).max
    rank = np.full(budget+1, infinity_rank, np.int64)
    rank[0] = 0
    choices = []
    for frontier, _, index_key, null_key in prepared:
        # Every transition below reads score/rank from the previous source row.
        following = score.copy()
        parent_rank = rank.copy()
        current_key = np.full(budget+1, null_key, np.int64)
        choice = np.where(np.isfinite(score), -1, -2).astype(np.int32)
        for code, action in enumerate(frontier):
            cost, gain = action['added_frames'], action['predicted_gain']
            candidate = score[:-cost]+gain
            old = following[cost:]
            previous_rank = rank[:-cost]
            candidate_key = index_key[action['candidate_index']]
            reachable = np.isfinite(candidate)
            tied_better = ((previous_rank < parent_rank[cost:]) |
                           ((previous_rank == parent_rank[cost:]) & (candidate_key < current_key[cost:])))
            better = reachable & ((candidate > old) | ((candidate == old) & tied_better))
            old[better] = candidate[better]
            parent_rank[cost:][better] = previous_rank[better]
            current_key[cost:][better] = candidate_key
            choice[cost:][better] = code
        # Rank complete prefixes by (old-prefix rank, current original index).
        # This supplies lexicographic ties without storing a path per DP state.
        reachable = np.flatnonzero(np.isfinite(following))
        order = np.lexsort((current_key[reachable], parent_rank[reachable]))
        next_rank = np.full(budget+1, infinity_rank, np.int64)
        next_rank[reachable[order]] = np.arange(len(reachable), dtype=np.int64)
        choices.append(choice)
        score, rank = following, next_rank
    best_utility = float(score.max())
    best_cost = int(np.flatnonzero(score == best_utility)[0])
    remaining = best_cost
    selected = {}
    selected_details = {}
    for source_index in range(len(source_order)-1, -1, -1):
        sid = source_order[source_index]
        code = int(choices[source_index][remaining])
        if code >= 0:
            action = prepared[source_index][0][code]
            selected[sid] = action['candidate_index']
            selected_details[sid] = action
            remaining -= action['added_frames']
        elif code != -1:
            raise RuntimeError('Unreachable state in multiple-choice backtracking')
    if remaining != 0 or sum(a['added_frames'] for a in selected_details.values()) != best_cost:
        raise RuntimeError('Multiple-choice native-cost backtracking mismatch')
    per_source = {}
    for sid, (_, statistics, _, _) in zip(source_order, prepared):
        chosen = selected_details.get(sid)
        per_source[sid] = dict(statistics, selected_candidate_index=None if chosen is None else chosen['candidate_index'],
            selected_cost=0 if chosen is None else chosen['added_frames'],
            selected_utility=0. if chosen is None else chosen['predicted_gain'], null_selected=chosen is None)
    chosen = {sid: selected[sid] for sid in source_order if sid in selected}
    return dict(chosen=chosen, selected=chosen,
        total_cost=best_cost, total_utility=best_utility, budget=budget, per_source=per_source,
        source_order=source_order, positive_options=sum(v['positive_candidates'] for v in per_source.values()),
        pareto_options=sum(v['pareto_candidates'] for v in per_source.values()),
        selected_sources=len(selected), null_sources=[sid for sid in source_order if sid not in selected],
        tie_policy='max original utility; min total cost; lexicographic original candidate index in registered source order; null last',
        algorithm='previous-source-row exact integer-cost multiple-choice DP, float64 utilities unchanged')


multiple_choice_knapsack = knapsack


def _checks():
    """Six bounded synthetic groups; never imports or reads experiment inputs."""
    def action(index, cost, utility):
        return dict(candidate_index=index, added_frames=cost, predicted_gain=utility)

    def brute(groups, budget):
        source_order = list(groups)
        null_keys = [max((a['candidate_index'] for a in groups[sid] if a), default=-1)+1 for sid in source_order]
        best = None
        for values in itertools.product(*[[None]+groups[sid] for sid in source_order]):
            cost = sum(a['added_frames'] for a in values if a)
            if cost > budget:
                continue
            utility = sum(a['predicted_gain'] for a in values if a)
            key = (-utility, cost, tuple(null_keys[i] if a is None else a['candidate_index'] for i, a in enumerate(values)))
            if best is None or key < best[0]:
                best = key, {sid: a['candidate_index'] for sid, a in zip(source_order, values) if a}
        return best

    passed = []
    rng = np.random.default_rng(20261018)
    for _ in range(12):
        groups = {sid: [action(j, int(rng.integers(1, 7)), int(rng.integers(1, 13))/4) for j in range(3)] for sid in ('a', 'b', 'c')}
        budget = int(rng.integers(0, 13))
        result = knapsack(groups, budget); expected, chosen = brute(groups, budget)
        assert result['selected'] == chosen and result['total_cost'] == expected[1] and result['total_utility'] == -expected[0]
    passed.append('tiny_instances_equal_full_bruteforce')

    result = knapsack({'a': [action(0, 9, 2.), action(1, 2, .5)]}, 3)
    assert result['selected'] == {'a': 1} and result['total_cost'] == 2
    passed.append('overbudget_top1_keeps_cheaper_feasible_alternative')

    result = knapsack({'a': [action(0, 2, 3.), action(1, 3, 4.)]}, 5)
    assert result['selected'] == {'a': 1} and result['total_utility'] == 4. and result['total_cost'] == 3
    passed.append('previous_row_prevents_two_choices_from_same_source')

    result = knapsack({'a': [None, action(0, 3, 0.)], 'b': []}, 8)
    assert result['selected'] == {} and result['total_cost'] == result['total_utility'] == 0
    assert result['per_source']['a']['zero_utility_dominated_by_null'] == 1
    assert knapsack({}, 4)['selected'] == {}
    passed.append('explicit_implicit_null_zero_utility_and_empty_sources')

    result = knapsack({'a': [action(0, 1, 3.)]}, 0)
    assert result['selected'] == {} and result['per_source']['a']['individually_budget_feasible'] == 0
    passed.append('zero_budget_has_only_null')

    groups = {'a': [action(9, 4, .5), action(8, 3, .5), action(5, 3, .75), action(2, 3, .75), action(1, 5, .625)]}
    result = knapsack(groups, 5)
    assert result['selected'] == {'a': 2} and result['total_cost'] == 3 and result['pareto_options'] == 1
    tie = knapsack({'a': [action(7, 1, 1.)], 'b': [action(0, 1, 1.)]}, 1)
    assert tie['selected'] == {'a': 7}
    passed.append('pareto_equal_cost_original_index_and_registered_source_ties')
    return dict(status='PASS6_SYNTHETIC_MULTIPLE_CHOICE_CHECK_GROUPS', checks=passed,
                actual_data_reads=0, actual_model_calls=0, actual_experiments=0)


if __name__ == '__main__':
    import json
    print(json.dumps(_checks(), ensure_ascii=False))
