"""Complete source masks with adopted BASE, head results and exact40.48 route."""
import numpy as np

from development_review48 import retained
from event_full79 import old_semantic_cache
from frozen_branch46 import semantic_prediction
from summary_context90 import ARMS
from t_io import ROOT, check, identity, read


def accepted_semantic_cache(sid):
    cache = old_semantic_cache(sid)
    prior = read(ROOT / 'event_full78/frozen_all_masks_before_labels.json')[sid]
    for arm in ('native_no_memory_control', 'native_event_memory_correct',
                'native_event_memory_half_source_shift'):
        ref = prior[arm]['native']
        with np.load(check(ref), allow_pickle=False) as data:
            cache.append(dict(VERIFY=data['VERIFY'].copy(), full=data['full40_47'].copy(),
                              residual=data['residual'].copy(), source=ref))
    return cache


def complete_source(source, cpu, resolved, route, semantic_ref, folder):
    sid = source.sid
    with np.load(check(route['intrinsic_keep']), allow_pickle=False) as data:
        keep = data['keep'].copy()
    expected = (len(source.timeline.points),)
    if keep.dtype != bool or keep.shape != expected:
        raise ValueError('Exact current40.48 source route/native dimensions differ')
    old = read(ROOT / 'event_full78/frozen_all_masks_before_labels.json')[sid]
    baseline = old['original40_48']['native']
    with np.load(check(baseline), allow_pickle=False) as data:
        original = data['full40_48'].copy()
    if original.dtype != bool or original.shape != expected:
        raise ValueError('Adopted complete40.48 mask dimensions differ')
    cache = accepted_semantic_cache(sid); masks, bindings = {}, {}
    accepted = read(ROOT / 'development_semantic46' / sid / 'semantic_CPU_completion.json')
    features = read(check(semantic_ref))['outputs']
    for arm in ARMS:
        d8, verified, guard = retained(source, cpu['source_policies'][sid][arm],
                                       cpu['tasks'], resolved)
        previous = next((x for x in cache if np.array_equal(x['VERIFY'], verified)), None)
        if previous is None:
            full, residual = semantic_prediction(verified, accepted, features)
            semantic = dict(first_new_frozen_head_CPU=True, original_BASE_outputs=semantic_ref)
        else:
            full, residual = previous['full'].copy(), previous['residual'].copy()
            semantic = dict(identity_equal_old_head_result_adopted=previous['source'])
        final = full & keep
        path = folder / (sid + '_' + arm + '_native.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, D8=d8, VERIFY=verified, full40_47=full,
                full40_48=final, route_keep=keep, residual=residual)
        ref = identity(path)
        bindings[arm] = dict(native=ref, semantic=semantic, exact40_48_route=route,
                             original_empty_source_guard=guard)
        masks[arm] = final
        if previous is None:
            cache.append(dict(VERIFY=verified.copy(), full=full.copy(),
                              residual=residual.copy(), source=ref))
    bindings['original40_48'] = dict(native=baseline,
        actual_original_first_QA=identity(ROOT / 'event_full78/independent_CPU_completion.json'),
        exact40_48_route=route, no_old_head_or_native_quality_repeated=True)
    return masks, bindings, original
