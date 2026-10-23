"""First bounded identity audit for the actual40.48 external temporal control."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'event_route_assets74'
GENERAL = WORK / 'general_highlight_supervision_20261021_v1'
ENGINEERING = WORK / 'i3d_umt_cross_domain_20261021_v1'
SPORT = WORK / 'highlight_source_admission_20261021_v1/matched_hl_pilot16'


def main():
    OUT.mkdir()
    protocol = read(ROOT / 'code/event_memory_protocol69.json')
    wanted = set(protocol['development_sources'])
    sources = {s['sid']: s for s in read(ROOT / 'source_registry09/registration.json')['sources'] if s['sid'] in wanted}
    if set(sources) != wanted or any(s['role'] == 'confirmation' for s in sources.values()):
        raise ValueError('Only registered historical development sources may be audited')
    old = {s['sid']: s for s in read(GENERAL / 'pilot28/registration.json')['sources']}
    assets = {}
    for sid, source in sources.items():
        clock = read(check(source['clock']))
        cells = math.ceil(clock['native_frames'] / 64)
        row = dict(source=source, original_native_cells=cells, original_native_frames=clock['native_frames'],
            prospective_new_RGB_uncompressed_bytes=cells * 8 * 224 * 224 * 3,
            cached_original_I3D_feature=None, new_I3D_needed=True)
        path = GENERAL / 'pilot28/features' / sid / 'acceptance.json'
        if sid in old and path.exists():
            prior = old[sid]
            if source['media']['sha256'] != prior['media']['sha256'] or source['clock']['sha256'] != prior['clock']['sha256']:
                raise ValueError('Existing same-name feature has a different original media/native clock')
            feature = read(path)
            if feature['input'] != prior['input'] or feature['cells'] != cells:
                raise ValueError('Existing I3D feature native input/denominator differs')
            check(feature['features'])
            row.update(cached_original_I3D_feature=identity(path), new_I3D_needed=False,
                       prospective_new_RGB_uncompressed_bytes=0)
        assets[sid] = row
    # These are original accepted assets, not new downloads or an unused model
    # family. Only their existing references are bound at this metadata stage.
    save(OUT / 'completion.json', dict(state='FIRST_CURRENT40_48_EXTERNAL_ROUTE_ASSET_INVENTORY_COMPLETE',
        sources=assets, original_I3D_weight_acceptance=identity(ENGINEERING / 'weight_acceptance.json'),
        original_kinetics_names=identity(GENERAL / 'semantic_route48/kinetics_classnames.json'),
        original_expert_registration=identity(SPORT / 'registration.json'),
        original_expert_completion=identity(SPORT / 'completion_remaining17.json'),
        original_source_remove_implementation=identity(GENERAL / 'code/routing_production60_review.py'),
        current_best_ZIP=protocol['protected_best'], new_model_calls=0, new_decode_or_RGB=0,
        fresh_confirmation_read=False, no_proxy_substituted_for_actual40_48=True,
        next='Adopt identity-equal original features; only missing native inputs/I3D features may be prepared once under the remaining fixed downstream budget. Apply original global K400 route and .5 expert removal unchanged before full source comparison.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
