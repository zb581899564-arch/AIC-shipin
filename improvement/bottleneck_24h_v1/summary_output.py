"""Exact JSON output contract for the new source-summary task.

Invalid model raw is a recorded failure, never an accepted empty selection.
"""
import json
from decimal import Decimal
from fractions import Fraction


def _unique_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: '+key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Nonfinite JSON constant: '+value)


def parse_summary(text, duration):
    value = json.loads(text, parse_float=Decimal, parse_constant=_constant,
                       object_pairs_hook=_unique_object)
    if not (isinstance(value, dict) and set(value) == {'segments'}
            and isinstance(value['segments'], list) and len(value['segments']) <= 6):
        raise ValueError('Exact source-summary object with 0..6 segments required')
    previous = Fraction(0); result = []
    for pair in value['segments']:
        if not (isinstance(pair, list) and len(pair) == 2
                and all(type(x) in (int,Decimal) for x in pair)):
            raise ValueError('Exact finite JSON numeric pair required')
        a,b = (Fraction(x) for x in pair)
        if not previous <= a < b <= Fraction(duration):
            raise ValueError('Unordered/overlapping/out-of-domain summary interval')
        result.append((a,b)); previous = b
    return result
