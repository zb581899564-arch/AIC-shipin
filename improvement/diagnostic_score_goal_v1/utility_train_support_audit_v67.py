"""One train-only CPU metadata diagnostic; no images, tensors, models or fit.

CLI --root ROOT reads existing55/44/31 CPU metadata and writes an exclusive
ROOT/utility_train_support_audit_67/result.json. Mixed original31 catalogs and
targets are parsed solely to select role=train; no screen numeric target is
accessed or emitted. No training/evaluation/production policy is changed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def bound(reference):
    require(set(reference) == {'path', 'sha256'}, 'Exact immutable CPU metadata reference')
    path = Path(reference['path']).resolve()
    require(ref(path) == reference, 'CPU metadata SHA mismatch: '+str(path))
    return path


def statistics_of(values):
    values = sorted(float(v) for v in values)
    require(all(math.isfinite(v) for v in values), 'Nonfinite metadata statistic')
    if not values:
        return dict(n=0, min=None, mean=None, median=None, max=None, p10=None, p90=None)
    return dict(n=len(values), min=values[0], mean=statistics.fmean(values), median=statistics.median(values),
                max=values[-1], p10=values[math.ceil(.1*len(values))-1], p90=values[math.ceil(.9*len(values))-1])


def graph_support(size, pairs):
    require(type(size) is int and size > 1, 'Nonempty distinct-candidate graph')
    adjacency = [set() for _ in range(size)]
    edges = set()
    for a, b in pairs:
        require(type(a) is type(b) is int and 0 <= a < b < size and (a, b) not in edges,
                'Unique canonical unordered edges')
        edges.add((a, b)); adjacency[a].add(b); adjacency[b].add(a)
    remaining = set(range(size)); components = []
    while remaining:
        stack = [min(remaining)]; component = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node); stack.extend(adjacency[node]-component)
        remaining -= component; components.append(sorted(component))
    baseline_component = next(c for c in components if 0 in c)
    return dict(components=components, component_count=len(components), connected=len(components)==1,
                endpoint_candidates=[i for i, neighbors in enumerate(adjacency) if neighbors],
                isolated_candidates=[i for i, neighbors in enumerate(adjacency) if not neighbors],
                degrees=[len(v) for v in adjacency], baseline_in_loss=bool(adjacency[0]),
                direct_baseline_candidates=sorted(adjacency[0]), baseline_component=baseline_component)


def proposal_families(source, geometry):
    width, height = source['width'], source['height']; maximum = geometry.largest_width(width, height)
    center = Fraction(width, 2), Fraction(height, 2)
    raw = [('MAX_CENTER', geometry.place_crop(width, height, maximum, center))]
    small = 4*maximum//5
    if small:
        dx, dy = Fraction(maximum, 10), Fraction(9*maximum, 160)
        for name, ox, oy in [('SMALL_CENTER', 0, 0), ('SMALL_LEFT', -dx, 0), ('SMALL_RIGHT', dx, 0),
                             ('SMALL_UP', 0, -dy), ('SMALL_DOWN', 0, dy)]:
            raw.append((name, geometry.place_crop(width, height, small, (center[0]+ox, center[1]+oy))))
    require(source['pool'] == geometry.candidate_pool(width, height), 'Train pool is original GT-free geometry, not observed BASE')
    return [[name for name, box in raw if box == candidate] for candidate in source['pool']]


def target_counts(values):
    return dict(positive=sum(v>0 for v in values), negative=sum(v<0 for v in values), exact_zero=sum(v==0 for v in values),
                abs_at_most_point02=sum(abs(v)<=.02 for v in values),
                abs_above_point02=sum(abs(v)>.02 for v in values), signed=statistics_of(values),
                absolute=statistics_of(abs(v) for v in values))


def audit(prepared, catalog, plan, gain, targets, geometry):
    require(prepared['schema']=='UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55', 'Original55 CPU compiler required')
    sources = catalog['sources']; byid = {s['source_id']:s for s in sources}
    require(len(sources)==len(byid)==602 and len({s['source_sha256'] for s in sources})==602
            and all(s['role']=='train' for s in sources), 'Exactly602 train metadata sources')
    # The caller passes ONLY original train target rows; no dev target is used.
    labels = {r['source_id']:r for r in targets}
    require(set(labels)==set(byid) and all(r['role']=='train' for r in targets), 'Train-only original targets')
    require(plan['GT_used_for_input_or_pair_choice'] is False and set(plan['chosen_train_pairs'])==set(byid), 'Fixed SHA pair scope')
    pair_index = gain['pair_index']; canonical = {}; by_source = defaultdict(list)
    for p in pair_index:
        sid, a, b = p['source_id'], p['a'], p['b']; source = byid[sid]
        require(p['source_sha256']==source['source_sha256'] and [a,b] in plan['chosen_train_pairs'][sid]
                and 0<=a<b<len(source['pool']) and (sid,a,b) not in canonical, 'Original44 canonical pair binding')
        label = labels[sid]; truth = label['candidate_ious']
        require(label['source_sha256']==source['source_sha256'] and label['baseline_index']==0
                and label['reference_modified'] is False and len(truth)==len(source['pool'])
                and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in truth), 'Unchanged original train IoU metadata')
        canonical[sid,a,b] = float(truth[b])-float(truth[a]); by_source[sid].append([a,b])
    require(len(canonical)==1204 and all(len(by_source[sid])==2 for sid in byid), 'Exactly2 unique unordered pairs/source')
    rows = prepared['train_schedule']; draws=Counter(); mass=defaultdict(list); signed_targets=[]
    require(len(rows)==2000 and len({r['id'] for r in rows})==2000, 'Original2000 distinct micro draws')
    for row in rows:
        sid,a,b = row['source_id'],row['a'],row['b']; source=byid[sid]; key=(sid,min(a,b),max(a,b))
        require(row['source_sha256']==source['source_sha256'] and row['unordered_pair']==list(key[1:])
                and key in canonical and row['target']==canonical[key]*(1 if a<b else -1), 'Actual55 draw target/support changed')
        require(type(row['draw_weight']) in (int,float) and math.isfinite(row['draw_weight']) and row['draw_weight']>0,
                'Finite actual positive draw weight')
        draws[key]+=1; mass[key].append(row['draw_weight']/2000); signed_targets.append(row['target'])
    require(set(draws)==set(canonical), 'Every chosen pair has loss exposure')
    for row in rows:
        key=(row['source_id'],*row['unordered_pair'])
        require(row['draw_weight']==2000/(1204*draws[key]), 'Actual inverse pair-draw weight changed')
    pair_mass={k:math.fsum(v) for k,v in mass.items()}; source_mass={sid:math.fsum(v for k,v in pair_mass.items() if k[0]==sid) for sid in byid}
    require(all(math.isclose(v,1/1204,rel_tol=1e-14) for v in pair_mass.values())
            and all(math.isclose(v,1/602,rel_tol=1e-14) for v in source_mass.values()), 'Empirical objective is not exactly pair/source equal')
    expected_rms=math.sqrt(math.fsum(v*v for v in canonical.values())/1204)
    require(math.isclose(prepared['train_target_RMS'],expected_rms,rel_tol=1e-12), 'Frozen target RMS mismatch')
    details=[]; families=defaultdict(Counter); widths=defaultdict(Counter); transitions=defaultdict(list); pair_families=Counter()
    all_gains=[]; unseen_gains=[]; unreachable_gains=[]; index_coverage=defaultdict(Counter)
    for source in sources:
        sid=source['source_id']; pool=source['pool']; truth=labels[sid]['candidate_ious']; graph=graph_support(len(pool),by_source[sid])
        names=proposal_families(source,geometry); endpoint=set(graph['endpoint_candidates']); direct=set(graph['direct_baseline_candidates'])
        reachable=set(graph['baseline_component']); maximum=geometry.largest_width(source['width'],source['height']); candidates=[]
        for i,box in enumerate(pool):
            require(names[i], 'Candidate has no original proposal identity')
            gain_from_geom_base=float(truth[i])-float(truth[0]); all_gains.append(gain_from_geom_base)
            if i not in endpoint:unseen_gains.append(gain_from_geom_base)
            if i not in reachable:unreachable_gains.append(gain_from_geom_base)
            category='MAX_WIDTH' if box[2]==maximum else 'SMALL_WIDTH'
            for counts in [widths[category],index_coverage[str(i)]]+[families[name] for name in names[i]]:
                counts['available']+=1;counts['in_loss']+=int(i in endpoint);counts['direct_from_base']+=int(i in direct)
                counts['connected_to_base']+=int(i in reachable);counts['isolated']+=int(i not in endpoint)
            x,y,w=box; candidates.append(dict(index=i,box=box,families=names[i],degree=graph['degrees'][i],
                in_loss=i in endpoint,direct_from_base=i in direct,connected_to_base=i in reachable,
                width_over_max=w/maximum,cx_over_source_width=(x+w/2)/source['width'],
                cy_over_source_height=(y+9*w/32)/source['height'],IoU_gain_from_training_geometry_baseline=gain_from_geom_base))
        for a,b in by_source[sid]:
            wa='MAX_WIDTH' if pool[a][2]==maximum else 'SMALL_WIDTH';wb='MAX_WIDTH' if pool[b][2]==maximum else 'SMALL_WIDTH'
            transitions[wa+'__'+wb].append(canonical[sid,a,b])
            pair_families['+'.join(names[a])+'__'+'+'.join(names[b])]+=1
        details.append(dict(source_id=sid,source_sha256=source['source_sha256'],width=source['width'],height=source['height'],
            pool_size=len(pool),chosen_pairs=by_source[sid],graph=graph,candidates=candidates,
            canonical_targets=[canonical[(sid,*p)] for p in by_source[sid]],
            micro_draws=sum(draws[(sid,*p)] for p in by_source[sid]),
            empirical_source_mass=source_mass[sid],pair_draw_counts=[draws[(sid,*p)] for p in by_source[sid]]))
    candidate_total=sum(len(s['pool']) for s in sources); covered=sum(len(d['graph']['endpoint_candidates']) for d in details)
    baseline_in=sum(d['graph']['baseline_in_loss'] for d in details); direct=sum(len(d['graph']['direct_baseline_candidates']) for d in details)
    alternative_total=candidate_total-602; indirectly_reachable=sum(len(d['graph']['baseline_component'])-1 for d in details)
    aggregate=dict(sources=602,unordered_pairs=1204,draws=2000,full_pool_candidate_count=candidate_total,
        pool_size_histogram=dict(Counter(d['pool_size'] for d in details)), connected_source_count=sum(d['graph']['connected'] for d in details),
        component_count_histogram=dict(Counter(d['graph']['component_count'] for d in details)),
        candidates_in_loss=covered,candidates_never_in_loss=candidate_total-covered,
        sources_with_isolated_candidates=sum(bool(d['graph']['isolated_candidates']) for d in details),
        geometry_baseline_sources_in_loss=baseline_in,geometry_baseline_sources_never_in_loss=602-baseline_in,
        alternative_candidate_count=alternative_total,direct_baseline_pair_count=direct,
        baseline_reachable_alternatives=indirectly_reachable,baseline_unreachable_alternatives=alternative_total-indirectly_reachable,
        family_coverage={k:dict(v) for k,v in sorted(families.items())},width_coverage={k:dict(v) for k,v in sorted(widths.items())},
        index_coverage={k:dict(v) for k,v in sorted(index_coverage.items())},
        pair_family_count=dict(sorted(pair_families.items())),
        width_transition_targets={k:target_counts(v) for k,v in sorted(transitions.items())},
        canonical_unordered_targets=target_counts(list(canonical.values())),actual_oriented_draw_targets=target_counts(signed_targets),
        all_train_candidate_gains_from_geometry_baseline=target_counts(all_gains),
        never_in_loss_candidate_gains_from_geometry_baseline=target_counts(unseen_gains),
        baseline_unreachable_candidate_gains_from_geometry_baseline=target_counts(unreachable_gains),
        pair_draw_histogram=dict(Counter(draws.values())),source_draw_histogram=dict(Counter(d['micro_draws'] for d in details)),
        draw_weight=statistics_of(r['draw_weight'] for r in rows),pair_empirical_mass=statistics_of(pair_mass.values()),
        source_empirical_mass=statistics_of(source_mass.values()),train_target_RMS=expected_rms,
        source_equal_aggregate_objective_verified=True,individual_Adam_steps_equal_weight=False,
        both_order_graphs_used_per_micro=True,exact_reverse_targets_have_equal_magnitude_opposite_sign=True,
        global_proposal_families_without_any_loss_support=[k for k,v in sorted(families.items()) if not v['in_loss']])
    return dict(aggregate=aggregate,per_source=details,
        interpretation=dict(geometry_baseline_is_MAX_CENTER_not_actual_B0=True,
            direct_loss_support_is_not_generalization_bound=True,
            disconnected_within_source_graph_does_not_prove_nonidentifiability_of_shared_parametric_model=True,
            train_IoU_metadata_does_not_measure_development_or_official_quality=True,
            deployment_BASE_conditioned_pairs_not_audited_here=True,old_stops_unchanged=True))


def self_test():
    g=graph_support(6,[[1,2],[3,4]])
    require(g['component_count']==4 and g['isolated_candidates']==[0,5] and g['baseline_component']==[0], 'Disconnected graph test')
    g=graph_support(3,[[0,1],[1,2]])
    require(g['connected'] and g['baseline_component']==[0,1,2] and g['direct_baseline_candidates']==[1], 'Indirect support test')
    require(target_counts([-.1,0.,.01,.2])['abs_at_most_point02']==2, 'Target summary test')
    try:graph_support(3,[[1,0]])
    except ValueError:pass
    else:raise AssertionError('Noncanonical graph accepted')
    import crop_geometry_v31 as geometry
    sources=[];targets=[];chosen={};pair_index=[];raw=[]
    for i in range(602):
        sid='synthetic:'+str(i);sha=('%064x'%i);pool=geometry.candidate_pool(1920,1080)
        sources.append(dict(source_id=sid,source_sha256=sha,role='train',width=1920,height=1080,pool=pool))
        truth=[.1*(j+1) for j in range(len(pool))]
        targets.append(dict(source_id=sid,source_sha256=sha,role='train',candidate_ious=truth,baseline_index=0,reference_modified=False))
        chosen[sid]=[[0,1],[2,3]]
        for a,b in chosen[sid]:
            pair_index.append(dict(source_id=sid,source_sha256=sha,a=a,b=b))
            raw.append((sid,sha,a,b,truth[b]-truth[a]))
    selected=raw+raw[:796];counts=Counter((r[0],r[2],r[3]) for r in selected);rows=[]
    for i,(sid,sha,a,b,y) in enumerate(selected):
        if i%2:a,b,y=b,a,-y
        rows.append(dict(id='T'+str(i),source_id=sid,source_sha256=sha,a=a,b=b,unordered_pair=sorted([a,b]),target=y,
            draw_weight=2000/(1204*counts[sid,min(a,b),max(a,b)])))
    prepared=dict(schema='UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55',train_schedule=rows,
        train_target_RMS=math.sqrt(math.fsum(r[4]**2 for r in raw)/1204))
    fixture=audit(prepared,dict(sources=sources),dict(chosen_train_pairs=chosen,GT_used_for_input_or_pair_choice=False),
        dict(pair_index=pair_index),targets,geometry)['aggregate']
    require(fixture['candidates_never_in_loss']==1204 and fixture['geometry_baseline_sources_in_loss']==602
        and fixture['source_equal_aggregate_objective_verified'] and fixture['pair_draw_histogram']=={2:796,1:408},
        'Synthetic602 actual weighting/coverage regression')
    bad=dict(prepared);bad['train_schedule']=[dict(r) for r in rows];bad['train_schedule'][0]['draw_weight']+=.1
    try:audit(bad,dict(sources=sources),dict(chosen_train_pairs=chosen,GT_used_for_input_or_pair_choice=False),dict(pair_index=pair_index),targets,geometry)
    except ValueError:pass
    else:raise AssertionError('Wrong empirical objective weight accepted')
    print('SELF_TEST_6_PASS')


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CPU metadata audit must mask CUDA')
    root=Path(root).resolve(); cpu_path=root/'utility_value_CPU_registration_55.json'; cpu=read(cpu_path)
    prepared_path=root/'utility_value_inputs_55/prepared.json'; prepared=read(prepared_path)
    gate_path=root/'utility_value_inputs_55/input_acceptance.json'; gate=read(gate_path)
    require(gate['status']=='PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU'
            and gate['prepared']==ref(prepared_path) and gate['registration']==ref(cpu_path), 'Adopt actual55 CPU compiler gate')
    catalog=read(bound(prepared['source_catalog']));plan=read(bound(cpu['old_case_plan']));gain=read(bound(cpu['gain_prepared']))
    mixed_targets=read(bound(cpu['original_targets']))
    train_targets=[row for row in mixed_targets['sources'] if row['role']=='train']
    del mixed_targets
    reg31_path=root/'crop_CPU_registration_31.json';reg31=read(reg31_path)
    spec=importlib.util.spec_from_file_location('_audit67_geometry31',bound(reg31['geometry_code']))
    geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
    result=audit(prepared,catalog,plan,gain,train_targets,geometry)
    result.update(status='COMPLETE_TRAIN602_SUPPORT_METADATA_DIAGNOSTIC_ONLY_V67',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        references=dict(code=ref(__file__),CPU_registration=ref(cpu_path),prepared=ref(prepared_path),input_acceptance=ref(gate_path),
            source_catalog=prepared['source_catalog'],original_case_plan=cpu['old_case_plan'],gain_prepared=cpu['gain_prepared'],
            original_train_targets_in_mixed_file=cpu['original_targets'],geometry_code=reg31['geometry_code']),
        new_model_calls=0,new_fit=0,new_pixel_reads=0,new_processor_calls=0,
        evaluated_screen_sources=0,evaluated_confirm_sources=0,evaluated_official_sources=0,
        scope='ONLY602_TRAIN_SOURCES_ORIGINAL_GT_AND_FROZEN_TWO_SHA_PAIRS',not_a_new_policy_or_admission=True)
    out=root/'utility_train_support_audit_67';out.mkdir(exist_ok=False)
    with (out/'result.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps(dict(status=result['status'],result=ref(out/'result.json'),aggregate=result['aggregate']),ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test()
    else:require(args.root is not None,'Explicit root required');run(args.root)
