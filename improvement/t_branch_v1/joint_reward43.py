"""Whole current-source sample reward with action-independent counterfactual baselines."""
from native_sets import bool_mask, replace_component, union_components
from preference_reward import summary_agreement


def source_counterfactuals(sampled, greedy, allowed, reviews, expected_reviewers):
    if not sampled or set(sampled) != set(greedy) or set(sampled) != set(allowed):
        raise ValueError('Complete current-source sampled/greedy/window provenance required')
    size = len(next(iter(allowed.values())))
    for name in sampled:
        domain = bool_mask(allowed[name], size)
        for value in [sampled[name], greedy[name]]:
            value = bool_mask(value, size)
            if (value & ~domain).any():
                raise ValueError('Actual action leaves its registered source window')
    chosen = union_components(sampled, size)
    score = summary_agreement(chosen, reviews, expected_reviewers)
    coefficients = {}
    for name in sampled:
        other_with_greedy = replace_component(sampled, name, greedy[name], allowed[name])
        counterfactual = summary_agreement(other_with_greedy, reviews, expected_reviewers)
        coefficients[name] = dict(advantage=score['mean_f1'] - counterfactual['mean_f1'],
                                  counterfactual_f1=counterfactual['mean_f1'])
    whole_greedy = summary_agreement(union_components(greedy, size), reviews, expected_reviewers)
    return dict(sampled_source=score, greedy_source=whole_greedy, per_window=coefficients,
                baseline='Other current sampled actions plus this window current greedy action',
                all_current_source_actions_from_one_unchanged_actor=True,
                unselected_is_not_explicit_ordinary=True)
