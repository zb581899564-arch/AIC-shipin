"""Adopt the exact successful original TIME context and its pixel codec."""
import importlib.util
import sys
from common import ROOT, OLD, read, checked


def legacy():
    registration = read(OLD/'audio_visual_registration_25.json')
    config = read(checked(registration['adopted_generation_registration_ref']))
    for value in config['code'].values():
        checked(value)
    path = checked(registration['code_ref'])
    spec = importlib.util.spec_from_file_location('adopted_audio_visual_context25', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.insert(0, str(checked(config['code']['summary_generate.py']).parent))
    return registration, config, module
