"""Frozen geometry-only Charades boundary diagnostics; never highlight truth.

No media, inference or source selection. Fine answers cannot change
correspondence. Role advice is a conservative diagnostic, never qualification.
Semantic identity remains UNKNOWN even with unique temporal overlap.
"""
from collections import Counter, defaultdict
from fractions import Fraction as F

SCHEMA='CHARADES_FIXED_GEOMETRIC_BOUNDARY_PROXY_V1'
ROLES=('TIME','BASE')
AVAILABLE='AVAILABLE_NATIVE_CONTEXT'
SHORT='SHORT_NATIVE_CONTEXT_UNAVAILABLE'
SKIP_DECISION='UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE'
SELECTION_RULE=dict(fixed_endpoint_set='geometric diagnostic + target strictly in context + predeclared available',
    minimum_distinct_sources=3, BASE_pointwise_not_worse_than_both_TIME_and_coarse=True,
    BASE_mean_strictly_less_than_both_TIME_and_coarse=True,
    BASE_declared_action_support_covers_both_TIME_and_coarse=True,
    engineering_all_planned_outputs_required=True, tolerance_seconds_exact='0',
    semantic_identity='UNKNOWN', scientific_role_winner=False)
RULE=dict(unique_positive_action_intersection=True, censored_intersection_is_unknown=True,
    both_overlap_fractions_strictly_greater_than='1/2', half_window_exact='3',
    anchors='coarse start+min(1,length/2), coarse end-min(1,length/2)',
    touching_intervals_are_not_positive_overlap=True, same_event_semantics='UNKNOWN',
    fine_outputs_read_for_matching=False, whole_source_precision_recall_F1=False)


def exact(value):
    if isinstance(value,(float,bool)) or not isinstance(value,(str,int)):
        raise ValueError('Frozen exact seconds required')
    return F(value)


def overlap(a,b):return max(F(0),min(a[1],b[1])-max(a[0],b[0]))
def mean(values):return float(sum(values,F(0))/len(values)) if values else None


def _actions(source):
    result=[];invalid=[];physical=exact(source['physical_end_exact'])
    for row in source['actions']:
        try:
            interval=(exact(row['start_exact']),exact(row['end_exact']))
            if interval[0]>=interval[1]:raise ValueError('Nonpositive author interval')
        except (ValueError,TypeError,ZeroDivisionError):
            invalid.append(row['action_index']);continue
        eligibility=row['eligibility']
        if eligibility not in ('FULLY_IN_DOMAIN','CENSORED_UNKNOWN'):
            raise ValueError('Original eligibility schema changed')
        if (0<=interval[0]<interval[1]<=physical)!=(eligibility=='FULLY_IN_DOMAIN'):
            raise ValueError('Original strict author/physical-domain classification changed')
        result.append(dict(action_index=row['action_index'],interval=interval,
            eligibility=eligibility,contains_native_frame=row['contains_native_frame']))
    if len({row['action_index'] for row in source['actions']})!=len(source['actions']):
        raise ValueError('Duplicate original action identity')
    return result,invalid


def freeze(events,sources):
    """Call once with B0-only intervals, before any fine role results."""
    if len({s['source_id'] for s in sources})!=len(sources) or len({e['event_id'] for e in events})!=len(events):
        raise ValueError('Unique frozen source/event denominator required')
    source_map={s['source_id']:s for s in sources};parsed={s['source_id']:_actions(s) for s in sources}
    matched=[]
    for event in events:
        source=source_map[event['source_id']];physical=exact(source['physical_end_exact'])
        c=tuple(map(exact,event['original_interval_exact']))
        if not 0<=c[0]<c[1]<=physical:raise ValueError('Original coarse source domain mismatch')
        distance=min(F(1),(c[1]-c[0])/2);anchors=(c[0]+distance,c[1]-distance)
        actions,invalid=parsed[event['source_id']]
        hits=[a for a in actions if overlap(c,a['interval'])>0]
        status='GEOMETRIC_DIAGNOSTIC_ONLY';reason=None;action=None
        if invalid:reason='INVALID_REFERENCE_GEOMETRY_UNKNOWN'
        elif any(a['eligibility']=='CENSORED_UNKNOWN' for a in hits):reason='CENSORED_ACTION_INTERSECTION_UNKNOWN'
        elif len(hits)!=1:reason='MULTIPLE_ACTION_INTERSECTIONS_UNKNOWN' if len(hits)>1 else 'NO_POSITIVE_ACTION_OVERLAP_UNKNOWN'
        else:
            action=hits[0];a=action['interval'];intersection=overlap(c,a)
            if action['contains_native_frame'] is not True:reason='NO_NATIVE_FRAME_SUPPORT_UNKNOWN'
            elif not intersection/(c[1]-c[0])>F(1,2) or not intersection/(a[1]-a[0])>F(1,2):
                reason='NO_STRICT_BOTH_MAJORITIES_UNKNOWN'
            elif not all(a[0]<=p<a[1] for p in anchors):reason='INNER_ANCHOR_OUTSIDE_ACTION_UNKNOWN'
        if reason:status='UNKNOWN';action=None
        endpoints=[]
        for i,side in enumerate(('start','end')):
            window=(max(F(0),c[i]-3),min(physical,c[i]+3))
            record=dict(side=side,original_endpoint_exact=str(c[i]),inner_anchor_exact=str(anchors[i]),
                context_exact=list(map(str,window)),metric_status=status,reason=reason,
                target_exact=None,action_index=None,GT_in_context=None,GT_two_sided_in_context=None,
                context_availability=AVAILABLE,same_event_semantics='UNKNOWN')
            if action is not None:
                target=action['interval'][i]
                ambiguous=any(other['action_index']!=action['action_index'] and
                              other['interval'][0]<target<other['interval'][1] for other in actions)
                record.update(target_exact=str(target),action_index=action['action_index'],
                    GT_in_context=window[0]<=target<=window[1],
                    GT_two_sided_in_context=window[0]<target<window[1])
                if ambiguous:
                    record.update(metric_status='UNKNOWN',reason='OVERLAPPING_REFERENCE_AT_BOUNDARY_UNKNOWN')
            endpoints.append(record)
        matched.append(dict(event_id=event['event_id'],source_id=event['source_id'],
            source_role=source['role'],original_case_id=event['original_case_id'],
            original_segment_index=event['original_segment_index'],
            original_interval_exact=list(map(str,c)),physical_end_exact=str(physical),
            match_status=status,reason=reason,action_index=action['action_index'] if action else None,
            action_interval_exact=list(map(str,action['interval'])) if action else None,
            endpoints=endpoints,same_event_semantics='UNKNOWN',scientific_quality_claim=False))
    coverage=[]
    for source in sources:
        rows=[e for e in matched if e['source_id']==source['source_id']]
        coverage.append(dict(source_id=source['source_id'],role=source['role'],
            original_actions=len(source['actions']),in_domain_actions=sum(a['eligibility']=='FULLY_IN_DOMAIN' for a in source['actions']),
            censored_actions=sum(a['eligibility']=='CENSORED_UNKNOWN' for a in source['actions']),
            original_coarse_events=len(rows),expected_endpoints=2*len(rows),
            geometrically_matched_events=sum(e['match_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' for e in rows),
            diagnostic_endpoints=sum(p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' for e in rows for p in e['endpoints']),
            unknown_endpoints=sum(p['metric_status']=='UNKNOWN' for e in rows for p in e['endpoints']),
            diagnostic_targets_outside_fixed_context=sum(p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' and
                p['GT_in_context'] is False for e in rows for p in e['endpoints']),
            zero_eligible_source_retained=not any(a['eligibility']=='FULLY_IN_DOMAIN' for a in source['actions'])))
    return dict(schema=SCHEMA,rule=RULE,events=matched,source_coverage=coverage,
        sources=len(sources),original_coarse_events=len(events),expected_endpoints=2*len(events),
        same_event_semantics_verified=False,scientific_quality_claim=False,
        whole_source_precision_recall_F1_admitted=False,fine_result_selected_correspondence=False)


def apply_predeclared_availability(frozen, rows):
    """Attach clock-only side availability; do not alter events or GT matches."""
    expected={(e['event_id'],p['side']) for e in frozen['events'] for p in e['endpoints']}
    seen=set();bykey={}
    for row in rows:
        key=(row['event_id'],row['side']);count=row['native_frame_count'];status=row['status']
        if key not in expected or key in seen or isinstance(count,bool) or not isinstance(count,int) or count<0:
            raise ValueError('Complete unique pre-fine native availability table required')
        if row['required_native_frames']!=64 or status not in (AVAILABLE,SHORT):
            raise ValueError('Frozen native64 availability contract changed')
        if (count>=64)!=(status==AVAILABLE):raise ValueError('Clock count/typed availability mismatch')
        seen.add(key);bykey[key]=row
    if seen!=expected:raise ValueError('Predeclared availability omitted a planned endpoint')
    # Use a new object: the original pre-fine correspondence remains immutable.
    events=[]
    for event in frozen['events']:
        endpoints=[{**p,'context_availability':bykey[(event['event_id'],p['side'])]['status'],
                    'native_frame_count':bykey[(event['event_id'],p['side'])]['native_frame_count']}
                   for p in event['endpoints']]
        events.append({**event,'endpoints':endpoints})
    return {**frozen,'events':events,'availability_rule':'clock-only pre-fine native64; short retains original for both roles'}


def _prediction(event,row):
    if row['event_id']!=event['event_id'] or row['original_interval_exact']!=event['original_interval_exact']:
        raise ValueError('Fine output belongs to another coarse candidate')
    if row.get('new_event_created') is not False or row.get('original_event_removed') is not False:
        raise ValueError('Boundary role may not create or remove an event')
    results=row['endpoint_results']
    if len(results)!=2 or {p['side'] for p in results}!={'start','end'}:raise ValueError('Two accepted endpoints required')
    byside={p['side']:p for p in results};values=[];decisions=[]
    for ref in event['endpoints']:
        result=byside[ref['side']];old=exact(ref['original_endpoint_exact']);value=exact(result['endpoint_exact'])
        if result['event_id']!=event['event_id'] or exact(result['original_endpoint_exact'])!=old:
            raise ValueError('Original endpoint identity mismatch')
        decision=result['applied_decision']
        if ref.get('context_availability',AVAILABLE)==SHORT:
            if (decision!=SKIP_DECISION or value!=old or result.get('actual_model_call') is not False
                    or result.get('predeclared_skip') is not True):
                raise ValueError('Predeclared short side needs no-call UNKNOWN at original endpoint')
        elif decision==SKIP_DECISION or result.get('predeclared_skip') is True:
            raise ValueError('A post-result skip may not conceal an available endpoint')
        if decision=='KEEP' or isinstance(decision,str) and decision.startswith('UNKNOWN'):
            if value!=old:raise ValueError('KEEP/UNKNOWN changed original point')
        elif decision=='REFINE':
            lo,hi=map(exact,ref['context_exact']);anchor=exact(ref['inner_anchor_exact'])
            if not lo<value<hi or not (value<anchor if ref['side']=='start' else value>anchor):
                raise ValueError('Refinement escaped fixed visible context/inside anchor')
            if (ref['side']=='start' and old==0 and value<=old) or (
                    ref['side']=='end' and old==exact(event['physical_end_exact']) and value>=old):
                raise ValueError('Source-edge refinement was not inward')
        else:raise ValueError('Bad output is an engineering failure, never UNKNOWN fallback')
        values.append(value);decisions.append(decision)
    conflict=values[0]>=values[1]
    resolved=tuple(map(exact,event['original_interval_exact'])) if conflict else tuple(values)
    if row['pair_conflict_preserved_original'] is not conflict or list(map(str,resolved))!=row['refined_interval_exact']:
        raise ValueError('Pair conflict/native resolved interval mismatch')
    return resolved,decisions


def evaluate(frozen,outputs):
    if frozen['schema']!=SCHEMA or frozen['rule']!=RULE or set(outputs)!=set(ROLES):
        raise ValueError('Frozen metric contract or paired role set changed')
    expected={e['event_id'] for e in frozen['events']};role_reports={};points={}
    for role in ROLES:
        given=outputs[role];counts=Counter(r.get('event_id') for r in given)
        byid={r.get('event_id'):r for r in given};invalid=[];details=[];decision_counts=Counter();per_source=defaultdict(list)
        missing=sorted(expected-set(byid));extra=sorted(str(x) for x in set(byid)-expected)
        duplicates=sorted(str(x) for x,n in counts.items() if n!=1)
        role_points={}
        for event in frozen['events']:
            eid=event['event_id'];resolved=None;decisions=None
            try:
                if counts[eid]!=1:raise ValueError('Missing/duplicate fine output')
                resolved,decisions=_prediction(event,byid[eid])
            except (ValueError,KeyError,TypeError,ZeroDivisionError) as error:
                invalid.append(dict(event_id=eid,source_id=event['source_id'],error=repr(error)))
            if resolved is None:
                details.append(dict(event_id=eid,source_id=event['source_id'],status='ENGINEERING_INVALID',
                                    expected_endpoint_count=2));continue
            old=tuple(map(exact,event['original_interval_exact']))
            support=tuple(map(exact,event['action_interval_exact'])) if event['action_interval_exact'] else None
            old_supported=(max(old[0],support[0]),min(old[1],support[1])) if support else None
            new_supported=(max(resolved[0],support[0]),min(resolved[1],support[1])) if support else None
            removed=max(F(0),overlap(old,support)-overlap(old_supported,new_supported)) if support else None
            for i,ref in enumerate(event['endpoints']):
                decision_counts[decisions[i]]+=1
                diagnostic=ref['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY'
                target=exact(ref['target_exact']) if diagnostic else None
                error=abs(resolved[i]-target) if diagnostic else None
                baseline=abs(old[i]-target) if diagnostic else None
                record=dict(event_id=eid,source_id=event['source_id'],side=ref['side'],
                    metric_status=ref['metric_status'],unknown_reason=ref['reason'],applied_decision=decisions[i],
                    effective_endpoint_exact=str(resolved[i]),target_exact=ref['target_exact'],
                    abs_error_seconds=float(error) if error is not None else None,
                    abs_error_exact=str(error) if error is not None else None,
                    signed_error_seconds=float(resolved[i]-target) if diagnostic else None,
                    old_abs_error_seconds=float(baseline) if diagnostic else None,
                    old_abs_error_exact=str(baseline) if diagnostic else None,
                    delta_abs_error_seconds=float(error-baseline) if diagnostic else None,
                    GT_in_fixed_context=ref['GT_in_context'],same_event_semantics='UNKNOWN',
                    GT_two_sided_in_fixed_context=ref['GT_two_sided_in_context'],
                    context_availability=ref.get('context_availability',AVAILABLE),
                    endpoint_outside_declared_action_interval=(not support[0]<=resolved[i]<=support[1]) if support else None,
                    newly_removed_declared_action_support_seconds=float(removed) if removed is not None else None,
                    declared_action_support_is_highlight_core=False)
                details.append(record)
                if diagnostic:
                    role_points[(eid,ref['side'])]=dict(error=error,baseline=baseline,record=record)
                    per_source[event['source_id']].append(error)
        all_errors=[p['error'] for p in role_points.values()]
        role_valid=not(invalid or missing or extra or duplicates)
        role_reports[role]=dict(expected_events=len(expected),expected_endpoints=2*len(expected),
            source_denominator=frozen['sources'],missing_event_ids=missing,unexpected_event_ids=extra,
            duplicate_event_ids=duplicates,engineering_invalid_events=invalid,
            engineering_pass=role_valid,decisions=dict(decision_counts),
            invalid_endpoint_count=2*len(invalid),diagnostic_endpoint_count=len(all_errors),
            diagnostic_MAE_seconds=mean(all_errors) if role_valid else None,
            partial_valid_diagnostic_MAE_seconds=mean(all_errors),
            covered_source_macro_MAE_seconds=mean([sum(v,F(0))/len(v) for v in per_source.values()]) if role_valid else None,
            partial_valid_covered_source_macro_MAE_seconds=mean([sum(v,F(0))/len(v) for v in per_source.values()]),
            covered_sources=len(per_source),uncovered_sources=frozen['sources']-len(per_source),details=details,
            scientific_quality_claim=False)
        points[role]=role_points
    paired=[]
    for key in sorted(set(points['TIME']) & set(points['BASE'])):
        t,b=points['TIME'][key],points['BASE'][key]
        paired.append(dict(event_id=key[0],side=key[1],source_id=t['record']['source_id'],
            TIME_abs_error_seconds=float(t['error']),BASE_abs_error_seconds=float(b['error']),
            TIME_abs_error_exact=str(t['error']),BASE_abs_error_exact=str(b['error']),
            coarse_abs_error_exact=str(t['baseline']),
            target_two_sided_in_context=t['record']['GT_two_sided_in_fixed_context'],
            context_availability=t['record']['context_availability'],
            BASE_minus_TIME_abs_error_seconds=float(b['error']-t['error'])))
    engineering=all(role_reports[r]['engineering_pass'] for r in ROLES)
    all_sides=[p for e in frozen['events'] for p in e['endpoints']]
    partial_mean=(sum((exact(p['BASE_abs_error_exact'])-exact(p['TIME_abs_error_exact']) for p in paired),F(0))/len(paired)) if paired else None
    report=dict(schema=SCHEMA,roles=role_reports,source_coverage=frozen['source_coverage'],paired=paired,
        nominal_endpoint_count=len(all_sides),
        actionable_endpoint_count=sum(p.get('context_availability',AVAILABLE)==AVAILABLE for p in all_sides),
        predeclared_short_endpoint_count=sum(p.get('context_availability',AVAILABLE)==SHORT for p in all_sides),
        paired_endpoint_count=len(paired),paired_expected_diagnostic_endpoints=sum(
            p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' for e in frozen['events'] for p in e['endpoints']),
        paired_mean_BASE_minus_TIME_seconds=float(partial_mean) if engineering and partial_mean is not None else None,
        partial_valid_paired_mean_BASE_minus_TIME_seconds=float(partial_mean) if partial_mean is not None else None,
        paired_comparison_engineering_admitted=engineering,
        role_qualification_admitted=False,same_event_semantics_verified=False,
        scientific_quality_claim=False,whole_source_precision_recall_F1_admitted=False,
        metric_scope='pre-D8-padding endpoints; unique geometry only; seconds not dense nativeframe GT',
        limitation='Automatic temporal overlap cannot confirm the same visual/semantic event. UNKNOWN coverage is retained.')
    report['diagnostic_role_advice']=diagnostic_role_advice(frozen,outputs,report)
    return report


def diagnostic_role_advice(frozen,outputs,report):
    """A global, exact and conservative proxy choice; never per-case selection."""
    chosen=[p for p in report['paired'] if p['target_two_sided_in_context'] is True and
            p['context_availability']==AVAILABLE]
    expected=[(e['event_id'],p['side']) for e in frozen['events'] for p in e['endpoints']
              if p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' and
              p['GT_two_sided_in_context'] is True and p.get('context_availability',AVAILABLE)==AVAILABLE]
    sources={p['source_id'] for p in chosen};reasons=[];worse=[];removed=[]
    if report['paired_comparison_engineering_admitted'] is not True:reasons.append('PLANNED_ENGINEERING_FAILURE')
    if {(p['event_id'],p['side']) for p in chosen}!=set(expected):reasons.append('FIXED_PAIRED_ENDPOINT_MISSING')
    if len(sources)<SELECTION_RULE['minimum_distinct_sources']:reasons.append('FEWER_THAN_THREE_DIAGNOSTIC_SOURCES')
    if not chosen:reasons.append('NO_AVAILABLE_TWO_SIDED_GEOMETRIC_PROXY')
    for p in chosen:
        b,t,c=map(exact,(p['BASE_abs_error_exact'],p['TIME_abs_error_exact'],p['coarse_abs_error_exact']))
        if b>t or b>c:worse.append(dict(event_id=p['event_id'],side=p['side'],BASE_exact=str(b),TIME_exact=str(t),coarse_exact=str(c)))
    if worse:reasons.append('BASE_ENDPOINT_WORSE_THAN_TIME_OR_COARSE')
    sums={role:sum((exact(p[role+'_abs_error_exact']) for p in chosen),F(0)) for role in ('TIME','BASE','coarse')}
    if not chosen or not(sums['BASE']<sums['TIME'] and sums['BASE']<sums['coarse']):
        reasons.append('BASE_MEAN_NOT_STRICTLY_BETTER_THAN_BOTH')
    # All geometrically matched planned events contribute support risk, including
    # unreachable/ambiguous endpoints. Action support never becomes highlight GT.
    maps={r:{x['event_id']:x for x in outputs[r]} for r in ROLES}
    if report['paired_comparison_engineering_admitted'] is True:
        for e in frozen['events']:
            if e['action_interval_exact'] is None:continue
            a=tuple(map(exact,e['action_interval_exact']));c=tuple(map(exact,e['original_interval_exact']))
            t,_=_prediction(e,maps['TIME'][e['event_id']]);b,_=_prediction(e,maps['BASE'][e['event_id']])
            bs=(max(b[0],a[0]),min(b[1],a[1]))
            for name,v in (('TIME',t),('coarse',c)):
                vs=(max(v[0],a[0]),min(v[1],a[1]))
                loss=overlap(v,a)-overlap(vs,bs)
                if loss>0:removed.append(dict(event_id=e['event_id'],source_id=e['source_id'],relative_to=name,
                    newly_removed_declared_action_support_exact=str(loss)))
    if removed:reasons.append('BASE_REMOVES_NEW_DECLARED_ACTION_SUPPORT')
    return dict(schema='CONSERVATIVE_GLOBAL_ROLE_PROXY_ADVICE_NOT_SCIENCE_PASS_V1',rule=SELECTION_RULE,
        chosen_role_advice='BASE' if not reasons else 'TIME',reasons=reasons,
        fixed_available_reachable_endpoint_count=len(expected),actual_paired_endpoint_count=len(chosen),
        distinct_diagnostic_sources=len(sources),pointwise_worse=worse,new_support_removal=removed,
        sum_absolute_error_exact={r:str(s) for r,s in sums.items()},
        mean_absolute_error_seconds={r:float(s/len(chosen)) if chosen and
            report['paired_comparison_engineering_admitted'] else None for r,s in sums.items()},
        semantic_identity_verified=False,scientific_role_winner=False,highlights_quality_pass=False,
        minimum_source_count_is_campaign_diversity_rule_not_statistical_proof=True,
        default_TIME_is_not_proof_of_quality=True)
