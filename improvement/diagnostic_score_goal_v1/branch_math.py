"""Pure math for complete, unprocessed three-branch VERIFY likelihoods.

UNKNOWN is its own response, never an ordinary-content label. Callers supply
raw model log-softmax values for every answer token, including any terminator
they registered. This module neither invokes a model nor applies a grammar.
"""
from collections.abc import Mapping
import math
from numbers import Integral, Real


CANONICAL_RESPONSES = {
    'KEEP': '{"decision":"KEEP"}',
    'UNKNOWN': '{"decision":"UNKNOWN"}',
    'DROP': '{"decision":"DROP"}',
}
BRANCHES = tuple(CANONICAL_RESPONSES)


def _branch_mapping(value):
    if not isinstance(value, Mapping) or set(value) != set(BRANCHES):
        raise ValueError('Exactly KEEP, UNKNOWN and DROP branches are required')


def _token_ids(values, name):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(name + ' must be a nonempty list or tuple of token IDs')
    if any(isinstance(v, bool) or not isinstance(v, Integral) or v < 0 for v in values):
        raise ValueError(name + ' must contain nonnegative integer token IDs')
    return [int(v) for v in values]


def validate_branch_token_ids(branch_token_ids):
    """Copy three distinct complete answer ID sequences; decoding is external."""
    _branch_mapping(branch_token_ids)
    result = {name: _token_ids(branch_token_ids[name], name) for name in BRANCHES}
    if len({tuple(ids) for ids in result.values()}) != len(BRANCHES):
        raise ValueError('Complete canonical branches must have distinct token sequences')
    return result


def build_teacher_forced_sequence(prefix_ids, answer_ids):
    """Build prompt + answer[:-1] and positions predicting every answer token.

    The logit at prefix_length - 1 predicts answer_ids[0]. No answer token is
    scored at its own input position. The returned lists do not alias inputs.
    """
    prefix = _token_ids(prefix_ids, 'prefix_ids')
    labels = _token_ids(answer_ids, 'answer_ids')
    start = len(prefix) - 1
    return {
        'input_ids': prefix + labels[:-1],
        'labels': labels,
        'logit_positions': list(range(start, start + len(labels))),
        'prefix_length': len(prefix),
    }


def _sequence_log_prob(values, name):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(name + ' must have nonempty per-token raw log probabilities')
    converted = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(name + ' log probabilities must be real numbers')
        value = float(value)
        if not math.isfinite(value) or value > 0:
            raise ValueError(name + ' log probabilities must be finite and nonpositive')
        converted.append(value)
    try:
        total = math.fsum(converted)
    except OverflowError as error:
        raise ValueError(name + ' sequence log probability overflowed') from error
    if not math.isfinite(total):
        raise ValueError(name + ' sequence log probability must be finite')
    return total


def _logsumexp(values):
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(v - maximum) for v in values))


def summarize_branch_log_probs(branch_token_log_probs):
    """Sum complete sequences, normalize over all three, and return two margins.

    Sequence length is not averaged. Finite-branch probabilities are conditional
    on this three-response set, not calibrated highlight probabilities. A common
    shift is removed before normalization and margins for numerical stability.
    """
    _branch_mapping(branch_token_log_probs)
    sequence = {name: _sequence_log_prob(branch_token_log_probs[name], name)
                for name in BRANCHES}
    maximum = max(sequence.values())
    shifted = {name: value - maximum for name, value in sequence.items()}
    normalizer = _logsumexp(list(shifted.values()))
    probabilities = {name: math.exp(value - normalizer) for name, value in shifted.items()}
    return {
        'sequence_log_probs': sequence,
        'probabilities': probabilities,
        'M_KEEP': shifted['KEEP'] - _logsumexp([shifted['UNKNOWN'], shifted['DROP']]),
        'M_DROP': shifted['DROP'] - _logsumexp([shifted['KEEP'], shifted['UNKNOWN']]),
    }
