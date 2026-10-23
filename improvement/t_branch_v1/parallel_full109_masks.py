"""Complete native masks with unchanged D8/VERIFY/head/current40.48 routing."""
import numpy as np

from development_review48 import retained
from frozen_branch46 import semantic_prediction
from summary_full93_masks import accepted_semantic_cache
from t_io import ROOT, check, identity, read


def semantic_cache(sid):
    cache = accepted_semantic_cache(sid)
    prior = read(ROOT / 'summary_full93/frozen_all_masks_before_labels.json')[sid]
    for arm, row in prior.items():
        if arm == 'original40_48':
            continue
        with np.load(check(row['native']), allow_pickle=False) as data:
            cache.append(dict(VERIFY=data['VERIFY'].copy(), full=data['full40_47'].copy(),
                              residual=data['residual'].copy(), source=row['native']))
    return cache


def complete(source, arms, cpu, resolved, route, semantic_ref, folder):
    sid = source.sid
    expected = (len(source.timeline.points),)
    with np.load(check(route['intrinsic_keep']), allow_pickle=False) as data:
        keep = data['keep'].copy()
    previous = read(ROOT / 'event_full78/frozen_all_masks_before_labels.json')[sid]
    baseline_ref = previous['original40_48']['native']
    with np.load(check(baseline_ref), allow_pickle=False) as data:
        original = data['full40_48'].copy()
    if any(value.dtype != bool or value.shape != expected for value in [keep, original]):
        raise ValueError('Exact current40.48 source route/baseline native domain differs')
    masks = {'original40_48': original}
    binding = {'original40_48': dict(native=baseline_ref,
        original_first_full_QA=identity(ROOT / 'event_full78/independent_CPU_completion.json'),
        no_old_model_head_or_quality_repeated=True)}
    cache = semantic_cache(sid)
    accepted = read(ROOT / 'development_semantic46' / sid / 'semantic_CPU_completion.json')
    features = read(check(semantic_ref))['outputs']
    for arm in arms:
        d8, verified, guard = retained(source, cpu['source_policies'][sid][arm], cpu['tasks'], resolved)
        old = next((row for row in cache if np.array_equal(row['VERIFY'], verified)), None)
        if old is None:
            full, residual = semantic_prediction(verified, accepted, features)
            proof = dict(first_new_frozen_semantic_head_CPU=True, original_BASE_outputs=semantic_ref)
        else:
            full, residual = old['full'].copy(), old['residual'].copy()
            proof = dict(exact_old_or_first_current_head_result_adopted=old['source'])
        final = full & keep
        path = folder / (sid + '_' + arm + '_native.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, D8=d8, VERIFY=verified, full40_47=full,
                full40_48=final, route_keep=keep, residual=residual)
        ref = identity(path)
        masks[arm] = final
        binding[arm] = dict(native=ref, semantic=proof, exact40_48_route=route,
                             original_empty_source_guard=guard)
        if old is None:
            cache.append(dict(VERIFY=verified.copy(), full=full.copy(), residual=residual.copy(), source=ref))
    return masks, binding
