"""Exact existing40.48 route assets, separate from Qwen's runtime namespace."""
from pathlib import Path
import sys

from t_io import ROOT, WORK, check, read

OUT = ROOT / 'event_route77'
GENERAL = WORK / 'general_highlight_supervision_20261021_v1'
ENGINEERING = WORK / 'i3d_umt_cross_domain_20261021_v1'
SPORT = WORK / 'highlight_source_admission_20261021_v1/matched_hl_pilot16'


def model_helpers():
    sys.path.insert(0, str(GENERAL / 'code'))
    from routing_production60_common import activate_i3d, CLASSES
    activate_i3d()
    import runtime
    import profile_gpu
    from pilot15_gpu import fingerprint
    if Path(runtime.__file__).resolve() != ENGINEERING / 'runtime.py':
        raise ValueError('Original route runtime binding changed')
    return runtime, profile_gpu, fingerprint, CLASSES


def source_inputs():
    inventory = read(ROOT / 'event_route_assets74/completion.json')
    prepared = read(ROOT / 'event_route_inputs75/completion.json')
    result = {}
    for sid, row in inventory['sources'].items():
        if row['new_I3D_needed']:
            input_ref = prepared['new_inputs'][sid]
            result[sid] = dict(source=row['source'], cells=row['original_native_cells'],
                input=input_ref, existing_feature=None)
        else:
            feature = read(check(row['cached_original_I3D_feature']))
            result[sid] = dict(source=row['source'], cells=row['original_native_cells'],
                input=feature['input'], existing_feature=feature['features'])
    if set(result) != set(read(ROOT / 'code/event_memory_protocol69.json')['development_sources']):
        raise ValueError('Exact current-best route source scope changed')
    return result


def old_model_registration():
    return read(GENERAL / 'routing_production62/registration.json')
