"""Canonical original runtime, initialized once before importing any grammar module."""
from functools import lru_cache
import importlib
from pathlib import Path
import sys

from t_io import WORK


@lru_cache(maxsize=1)
def _bound():
    path = WORK / 'general_highlight_supervision_20261021_v1/code'
    sys.path.insert(0, str(path))
    from time_entry53 import original_runtime
    runtime, bindings = original_runtime()
    return runtime, bindings, sys.modules['common']


def runtime():
    original, _, common = _bound()
    if original.b_engine.require is not common.require or original.b_engine.sha is not common.sha:
        raise ValueError('Cached original engine helpers were rebound unexpectedly')
    return original


def grammar():
    runtime()
    _, bindings, _ = _bound()
    module = importlib.import_module('constrained_json')
    if Path(module.__file__).resolve() != Path(bindings['constrained_json']).resolve():
        raise ValueError('Grammar module does not match actual frozen helper binding')
    return module
