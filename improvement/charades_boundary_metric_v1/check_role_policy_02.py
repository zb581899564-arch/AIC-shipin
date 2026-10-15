"""Synthetic role/skip tests only; never read real GT or media."""
import json
from pathlib import Path
from metric import freeze,evaluate,apply_predeclared_availability,AVAILABLE,SHORT,SKIP_DECISION
from check_metric import action,event,output


def main():
    sources=[dict(source_id='s'+str(i),role='dev',physical_end_exact='20',
                  actions=[action(0,'4','12')]) for i in range(3)]
    events=[event('e'+str(i),'s'+str(i),'5','11') for i in range(3)]
    frozen=freeze(events,sources)
    time=[output(e) for e in frozen['events']]
    base=[output(e,{'start':'4','end':'12'}) for e in frozen['events']]
    r=evaluate(frozen,{'TIME':time,'BASE':base})
    assert r['diagnostic_role_advice']['chosen_role_advice']=='BASE'
    assert r['diagnostic_role_advice']['distinct_diagnostic_sources']==3
    assert not r['diagnostic_role_advice']['scientific_role_winner']
    # Improved mean cannot conceal even one worse fixed endpoint.
    worse=[output(e,{'start':'11/2','end':'12'}) if i==0 else base[i]
           for i,e in enumerate(frozen['events'])]
    q=evaluate(frozen,{'TIME':time,'BASE':worse})
    assert 'BASE_ENDPOINT_WORSE_THAN_TIME_OR_COARSE' in q['diagnostic_role_advice']['reasons']
    # Crossing the declared action start can improve MAE but remove its support.
    wide=[output(e,{'start':'7/2','end':'25/2'}) for e in frozen['events']]
    cut=[output(e,{'start':'17/4','end':'47/4'}) for e in frozen['events']]
    q=evaluate(frozen,{'TIME':wide,'BASE':cut})
    assert 'BASE_REMOVES_NEW_DECLARED_ACTION_SUPPORT' in q['diagnostic_role_advice']['reasons']
    assert all(p['BASE_abs_error_seconds']<p['TIME_abs_error_seconds'] for p in q['paired'])
    # Predeclared shorts remain planned outputs with no call and original point.
    rows=[dict(event_id=e['event_id'],side=side,status=SHORT if i==0 else AVAILABLE,
               native_frame_count=46 if i==0 else 70,required_native_frames=64)
          for i,e in enumerate(frozen['events']) for side in ('start','end')]
    limited=apply_predeclared_availability(frozen,rows)
    before=json.dumps(frozen,sort_keys=True)
    t=json.loads(json.dumps(time));b=json.loads(json.dumps(base))
    b[0]=output(frozen['events'][0])
    for result in (t[0],b[0]):
        for p in result['endpoint_results']:
            p.update(applied_decision=SKIP_DECISION,actual_model_call=False,predeclared_skip=True)
    q=evaluate(limited,{'TIME':t,'BASE':b})
    assert q['paired_comparison_engineering_admitted']
    assert (q['nominal_endpoint_count'],q['actionable_endpoint_count'],q['predeclared_short_endpoint_count'])==(6,4,2)
    assert q['roles']['TIME']['decisions'][SKIP_DECISION]==2
    assert q['diagnostic_role_advice']['chosen_role_advice']=='TIME'
    assert 'FEWER_THAN_THREE_DIAGNOSTIC_SOURCES' in q['diagnostic_role_advice']['reasons']
    assert json.dumps(frozen,sort_keys=True)==before
    # A real missing row is not the typed short-side skip.
    q=evaluate(limited,{'TIME':t,'BASE':b[1:]})
    assert not q['paired_comparison_engineering_admitted']
    assert q['paired_mean_BASE_minus_TIME_seconds'] is None
    assert q['roles']['BASE']['diagnostic_MAE_seconds'] is None
    assert q['roles']['BASE']['partial_valid_diagnostic_MAE_seconds'] is not None
    assert 'PLANNED_ENGINEERING_FAILURE' in q['diagnostic_role_advice']['reasons']
    # Post-hoc skips cannot hide a callable side; changed skip is also invalid.
    assert not evaluate(frozen,{'TIME':t,'BASE':base})['roles']['TIME']['engineering_pass']
    fake=json.loads(json.dumps(t));fake[0]['endpoint_results'][0]['endpoint_exact']='4'
    assert not evaluate(limited,{'TIME':fake,'BASE':b})['roles']['TIME']['engineering_pass']
    try:apply_predeclared_availability(frozen,rows[:-1])
    except ValueError:pass
    else:raise AssertionError('Availability denominator omission accepted')
    result=dict(status='PASS_PURE_ROLE_NOT_WORSE_SUPPORT_SHORT_SKIP_CHECKS_NOT_REAL_QUALITY',
        checks=['three_source_pointwise_and_mean_proxy_advice','mean_cannot_hide_worse_endpoint',
          'better_MAE_cannot_hide_new_declared_support_removal','predeclared_short_not_missing_model_output',
          'short_nominal_actionable_denominators_retained','short_roles_both_original',
          'insufficient_available_source_no_winner','real_missing_primary_comparison_null',
          'post_hoc_skip_rejected','moved_skip_rejected','availability_omission_rejected',
          'original_correspondence_not_mutated','proxy_advice_never_SCI_or_highlight_PASS'],
        real_reference_reads=0,media_reads=0,processor_calls=0,model_calls=0)
    out=Path(__file__).resolve().parents[2]/'reports/twenty_hour_five_20261014_v1/critic/metric_08'
    with (out/'pure_role_check_02.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
