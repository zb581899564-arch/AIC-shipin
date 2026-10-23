"""Isolated binding to the existing native grammar; no original module rebinding."""
from functools import lru_cache
from fractions import Fraction
import importlib.util
import sys

from frozen_branch46 import RUN
from t_io import identity

OLD = RUN / 'overnight_risk_20261012_v1/dense128_v2'


def load_named(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def bindings():
    original = load_named(OLD / 'original_grammar.py', '_t_event_original_grammar71')
    previous = sys.modules.get('original_grammar')
    try:
        sys.modules['original_grammar'] = original
        native = load_named(OLD / 'native_grammar.py', '_t_event_native_grammar71')
    finally:
        if previous is None:
            sys.modules.pop('original_grammar', None)
        else:
            sys.modules['original_grammar'] = previous
    return native, original


def dependencies():
    return {name: identity(OLD / name) for name in ['original_grammar.py', 'native_grammar.py']}


def first_binding_contract():
    native, _ = bindings()
    rule = native.NativeSegmentsGrammar(Fraction(2), [Fraction(0), Fraction(1, 2), Fraction(1)], Fraction(0))
    checks = dict(legal_empty=rule.complete('{"segments":[]}'),
        between_native_frames_rejected=not rule.complete('{"segments":[[0.1,0.2]]}'),
        native_point_interval_allowed=rule.complete('{"segments":[[0.1,0.6]]}'),
        out_of_bounds_rejected=not rule.complete('{"segments":[[0,3]]}'))
    if not all(checks.values()):
        raise ValueError('Prospective exact-native grammar binding failed')
    return dict(checks=checks, code=dependencies(), new_model_or_old_successful_test_replay=False)


def constraint(tokenizer, prefix_length, case, source, eos, candidates):
    native, _ = bindings()
    start = Fraction(case.meta['window_start'])
    duration = Fraction(case.meta['window_end']) - start
    return native.make_native_constraint(tokenizer, prefix_length, duration, source.timeline.points, start,
        candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
