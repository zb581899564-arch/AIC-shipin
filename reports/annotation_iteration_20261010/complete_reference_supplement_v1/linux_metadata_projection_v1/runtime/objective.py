"""Pure token/target logic. Fractions stay exact until grammar serialization."""
from fractions import Fraction as F
from decimal import Decimal
import json
from common import require


def finite_decimal(value):
    value = F(value); d = value.denominator; twos = fives = 0
    while d % 2 == 0:
        twos += 1; d //= 2
    while d % 5 == 0:
        fives += 1; d //= 5
    digits = max(twos, fives)
    require(d == 1 and digits <= 18, 'exact target is not representable by original finite-decimal grammar')
    scaled = value.numerator * 2**(digits-twos) * 5**(digits-fives)
    sign = '-' if scaled < 0 else ''; scaled = abs(scaled)
    if digits:
        text = str(scaled).zfill(digits+1)
        text = sign + text[:-digits] + '.' + text[-digits:]
        return text.rstrip('0').rstrip('.')
    return sign + str(scaled)


def target(reference, window, reviewed_serialization=None, reference_sha=None):
    require(reference.get('training_admitted') is True and not reference['unknown_global_exact'], 'UNKNOWN/unadmitted target')
    start, end = F(window['domain_start_exact']), F(window['domain_end_exact'])
    exact = [[F(a)-start, F(b)-start] for a, b in reference['keep_global_exact']]
    require(len(exact) <= 5 and (not exact) == (reference.get('explicit_no_highlight') is True), 'empty semantics differ')
    require(all(0 <= a < b <= end-start for a, b in exact), 'target outside domain')
    if reviewed_serialization is None:
        serialized = [[finite_decimal(a), finite_decimal(b)] for a, b in exact]
    else:
        s = reviewed_serialization
        require(s['reference_sha256'] == reference_sha and s['window_id'] == window['window_id'] and
                s['reviewed'] is True and s['not_measured_cut'] is True, 'unreviewed/wrong-reference serialization')
        require(s['exact_target_local'] == [[str(a), str(b)] for a, b in exact], 'sidecar exact target differs')
        serialized = s['serialized_decimal_as_str']
        require(len(serialized) == len(exact), 'sidecar segment count differs')
        require(len(s['reviewed_boundary_ranges_local_exact']) == len(exact), 'reviewed boundary ranges absent')
        for ix, (old, numbers) in enumerate(zip(exact, serialized)):
            require(len(numbers) == 2 and all(type(x) is str for x in numbers), 'literal decimal strings required')
            for j, number in enumerate(numbers):
                value = F(Decimal(number))
                require(finite_decimal(value) == number and 'e' not in number.lower(), 'noncanonical decimal sidecar')
                lo, hi = map(F, s['reviewed_boundary_ranges_local_exact'][ix][j])
                require(lo <= old[j] <= hi and lo <= value <= hi, 'serialized boundary outside reviewed range')
        mapped = [[F(Decimal(a)), F(Decimal(b))] for a, b in serialized]
        require(all(0 <= a < b <= end-start for a, b in mapped) and
                all(x[1] <= y[0] for x, y in zip(mapped, mapped[1:])), 'mapped target bounds/order')
        # Exact membership, no epsilon, rounding, or PTS reconstruction.
        for field in ('planned_exact_pts', 'eligible_exact_pts'):
            points = [F(x)-start for x in window[field]]
            old_set = [i for i, p in enumerate(points) if any(a <= p < b for a, b in exact)]
            new_set = [i for i, p in enumerate(points) if any(a <= p < b for a, b in mapped)]
            require(old_set == new_set, 'serialized target changes native source selection: '+field)
    text = '{"segments":[' + ','.join('['+a+','+b+']' for a, b in serialized) + ']}'
    return text, exact


def assistant_mask(full_ids, full_attention, prompt_ids, prompt_attention, suffix_ids, terminator):
    require(len(full_ids) == len(full_attention) and len(prompt_ids) == len(prompt_attention), 'attention shape')
    require(all(type(x) is int and x in (0, 1) for x in full_attention+prompt_attention), 'attention values')
    active = [i for i, flag in enumerate(full_attention) if flag]
    prompt = [t for t, flag in zip(prompt_ids, prompt_attention) if flag]
    actual = [full_ids[i] for i in active]
    require(prompt and actual == prompt+suffix_ids and terminator in suffix_ids, 'assistant target/prefix/termination differs')
    labels = [-100]*len(full_ids)
    for i in active[len(prompt):]:
        labels[i] = full_ids[i]
    require(len(suffix_ids) > 1 and active[len(prompt)] > 0, 'no causal assistant labels')
    return labels


def classify(raw, duration, inference_error=None):
    """Strict exact JSON mirror for offline acceptance; runtime also calls original parser."""
    if inference_error is not None:
        return dict(status='INFERENCE_FAILURE', parsed_segments=None, error=str(inference_error))
    def pairs(rows):
        d = {}
        for k, v in rows:
            require(k not in d, 'duplicate JSON key'); d[k] = v
        return d
    try:
        obj = json.loads(raw, parse_float=Decimal, object_pairs_hook=pairs,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        require(type(obj) is dict and set(obj) == {'segments'} and type(obj['segments']) is list, 'segments schema')
        require(len(obj['segments']) <= 5, 'too many segments')
        seg = []; last = F(0)
        for row in obj['segments']:
            require(type(row) is list and len(row) == 2 and all(type(x) in (int, Decimal) for x in row), 'segment numeric bounds')
            a, b = map(F, row)
            require(last <= a < b <= F(duration), 'invalid ordered bounds')
            seg.append([a, b]); last = b
        return dict(status='MODEL_OK' if seg else 'LEGAL_EMPTY', parsed_segments=seg, error=None)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return dict(status='PARSE_FAILURE', parsed_segments=None, error=str(exc))
