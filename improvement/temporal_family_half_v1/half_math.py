"""Fixed half residual, over the recipe coordinate, with no new model call."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import importlib.util
from pathlib import Path
import sys

ARMS = ('HALF_START', 'HALF_END', 'HALF_BOTH')
ALPHA = F(1, 2)
OWNER = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_native_package_v3/code/combine_events.py')
OWNER_SHA = '8e508a7d8065edd0b282d2c235cdb2619730a2bce6bb416e82ea1240668b6ce6'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def exact(value):
    require(not isinstance(value, (float, bool)), 'Exact registered recipe/native seconds required')
    return F(value)


def original_candidate():
    require(OWNER.is_file() and hashlib.sha256(OWNER.read_bytes()).hexdigest() == OWNER_SHA,
            'The unchanged full-strength original family application is required')
    name = '_half_frozen_original_full_candidate'
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve() == OWNER, 'Full-candidate namespace owner changed')
        return sys.modules[name].candidate
    spec = importlib.util.spec_from_file_location(name, OWNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.candidate


def candidate(event, endpoints, verification, arm, full_candidate):
    require(arm in ARMS, 'Unregistered half arm')
    full_arm = arm.removeprefix('HALF_')
    # This exact corresponding original arm is checked first. A valid half
    # interval may never repair its full-strength conflict.
    full = full_candidate(event, endpoints, verification, full_arm)
    old = tuple(map(exact, event['original_interval_exact']))
    lo, hi = map(exact, event['original_window_exact'])
    physical = exact(event['physical_end_exact'])
    selected_sides = ('start',) if full_arm == 'START' else ('end',) if full_arm == 'END' else ('start', 'end')
    points = dict(start=old[0], end=old[1])
    half_applied = dict(start=False, end=False)
    outside = False
    for side, original in zip(('start', 'end'), old):
        result = endpoints[event['event_id']+'.'+side]
        if result['applied_decision'] == 'REFINE':
            require(type(result.get('native_cut_actually_moved')) is bool,
                    'Accepted REFINE must carry its independently bound native movement identity')
            moved = result['native_cut_actually_moved']
            if moved:
                require(exact(result['native_endpoint_exact']) != exact(result['original_native_cut_endpoint_exact']) and
                        exact(result['endpoint_exact']) == exact(result['native_endpoint_exact']),
                        'Moved native REFINE does not match its accepted applied recipe endpoint')
            else:
                require(exact(result['endpoint_exact']) == original and
                        exact(result['native_endpoint_exact']) == exact(result['original_native_cut_endpoint_exact']),
                        'Zero-native displacement must retain its original recipe')
            if moved and side in selected_sides and not full['pair_conflict_preserved_original']:
                point = original + ALPHA*(exact(result['endpoint_exact'])-original)
                outside |= not 0 <= point <= physical
                points[side] = point
                half_applied[side] = point != original
    if full['pair_conflict_preserved_original'] or outside:
        points = dict(start=old[0], end=old[1])
        half_applied = dict(start=False, end=False)
    require(points['start'] < points['end'], 'Half cannot rescue or create an invalid event')
    lead = F(3, 4)
    tail = F(1, 2)+(F(1, 4) if old[1]-old[0] >= 8 else 0)
    padded = (max(lo, points['start']-lead), min(hi, points['end']+tail))
    require(padded[0] < padded[1], 'Retained original-window half event has no support')
    return dict(event_id=event['event_id'], source_id=event['source_id'], arm=arm,
                original_interval_exact=list(map(str, old)),
                refined_interval_exact=[str(points['start']), str(points['end'])],
                selected_interval_exact=list(map(str, padded)), alpha_exact='1/2',
                corresponding_full_arm=full_arm,
                pair_conflict_preserved_original=full['pair_conflict_preserved_original'],
                halfpoint_outside_physical_domain_preserved_whole_original_event=outside,
                half_applied_sides=half_applied, original_length_padding_eligible=old[1]-old[0] >= 8,
                verification_decision=verification[event['event_id']]['decision'], verification_applied=False,
                event_removed=False, source_context_bounds_applied={'start': False, 'end': False},
                historical_recipe_window_is_not_new_physical_domain=True)


def combine(events, endpoints, verification, source_clocks, *, full_candidate=None):
    ids = [event['event_id'] for event in events]
    require(len(set(ids)) == len(ids) and set(endpoints) == {eid+'.'+side for eid in ids for side in ('start', 'end')} and
            set(verification) == set(ids), 'All original event/endpoint/VERIFY denominators must remain complete')
    full_candidate = full_candidate or original_candidate()
    clocks = {}
    for source, clock in source_clocks.items():
        pts = list(map(exact, clock['normalized_exact_pts']))
        end = exact(clock['physical_end_exact'])
        require(pts and pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:])) and pts[-1] < end,
                'Accepted complete native source clock is required')
        clocks[source] = pts
    outputs = {}
    for arm in ARMS:
        selected = {source: set() for source in clocks}
        decisions = []
        for event in events:
            source = event['source_id']
            require(source in clocks and exact(event['physical_end_exact']) == exact(source_clocks[source]['physical_end_exact']),
                    'Half event/source clock identity mismatch')
            result = candidate(event, endpoints, verification, arm, full_candidate)
            a, b = map(exact, result['selected_interval_exact'])
            selected[source].update(range(bisect_left(clocks[source], a), bisect_left(clocks[source], b)))
            decisions.append(result)
        outputs[arm] = dict(decisions=decisions, selected_ordinals={source: sorted(rows) for source, rows in selected.items()},
                            scientific_quality_claim=False, model_calls_in_this_module=0)
    return outputs
