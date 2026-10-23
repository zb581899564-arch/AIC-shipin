"""One fixed local native card plus an unverified source-summary content goal."""
from t_io import check, identity, read

ARMS = ('untrained_BASE_summary_correct', 'trained_summary_correct', 'trained_summary_cross_source_goal_shift')


def context_card(table, index, case, goal_text):
    card = table['correct'][index]
    original = table['original_native_binding'][index]
    if original['case'] != case.name or original['original_CPU'] != case.CPU:
        raise ValueError('Local event card belongs to another original native window')
    if not isinstance(goal_text, str):
        raise ValueError('An execution failure cannot become an empty content goal')
    # All condition/provider identity stays in provenance, never in this payload.
    return [dict(card, quoted_unverified_source_summary_goal=goal_text)]


def owner_key(case, proof):
    import hashlib
    import json
    row = read(check(proof))
    value = dict(original_CPU=case.CPU, actual_signature=row['actual_signature'],
                 model_role='original_frozen_TIME', native_case=case.name)
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
