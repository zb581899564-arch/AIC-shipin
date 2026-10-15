"""Small pure diagnostic checks; no real reference/media/model read."""
import json
from pathlib import Path
from metric import freeze,evaluate


def action(index,a,b,eligible=True,native=True):
    return dict(action_index=index,start_exact=a,end_exact=b,
        eligibility='FULLY_IN_DOMAIN' if eligible else 'CENSORED_UNKNOWN',contains_native_frame=native)


def event(eid,sid,a,b):
    return dict(event_id=eid,source_id=sid,original_case_id=eid+'_W000',
                original_segment_index=0,original_interval_exact=[a,b])


def output(e,changes=None):
    values=e['original_interval_exact'].copy();results=[]
    for i,side in enumerate(('start','end')):
        value=(changes or {}).get(side,values[i]);decision='REFINE' if value!=values[i] else 'UNKNOWN'
        results.append(dict(event_id=e['event_id'],side=side,original_endpoint_exact=values[i],
                            endpoint_exact=value,applied_decision=decision))
        values[i]=value
    return dict(event_id=e['event_id'],original_interval_exact=e['original_interval_exact'],
        refined_interval_exact=values,pair_conflict_preserved_original=False,
        endpoint_results=results,new_event_created=False,original_event_removed=False)


def main():
    sources=[dict(source_id='unique',role='dev',physical_end_exact='20',actions=[action(0,'4','12')]),
      dict(source_id='overlap',role='dev',physical_end_exact='20',actions=[action(0,'4','12'),action(1,'6','10')]),
      dict(source_id='censored',role='confirm',physical_end_exact='20',actions=[action(0,'4','12'),action(1,'0','21',False)]),
      dict(source_id='zero',role='confirm',physical_end_exact='20',actions=[action(0,'0','21',False)]),
      dict(source_id='half',role='dev',physical_end_exact='20',actions=[action(0,'4','12')]),
      dict(source_id='boundary',role='dev',physical_end_exact='20',actions=[action(0,'4','12'),action(1,'1','5')])]
    events=[event('e1','unique','5','11'),event('e2','overlap','5','11'),event('e3','censored','5','11'),
            event('e4','zero','1','19'),event('e5','half','4','8'),event('e6','boundary','6','11')]
    frozen=freeze(events,sources);by={e['event_id']:e for e in frozen['events']}
    assert by['e1']['match_status']=='GEOMETRIC_DIAGNOSTIC_ONLY'
    assert by['e2']['reason']=='MULTIPLE_ACTION_INTERSECTIONS_UNKNOWN'
    assert by['e3']['reason']=='CENSORED_ACTION_INTERSECTION_UNKNOWN'
    assert by['e4']['match_status']=='UNKNOWN'
    assert by['e5']['reason']=='NO_STRICT_BOTH_MAJORITIES_UNKNOWN'
    assert by['e6']['endpoints'][0]['metric_status']=='UNKNOWN' and by['e6']['endpoints'][1]['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY'
    assert len(frozen['source_coverage'])==6 and any(s['zero_eligible_source_retained'] for s in frozen['source_coverage'])
    before=json.dumps(frozen,sort_keys=True)
    time=[output(e) for e in frozen['events']];base=[output(e,{'start':'4','end':'12'}) if e['event_id']=='e1' else output(e) for e in frozen['events']]
    report=evaluate(frozen,{'TIME':time,'BASE':base})
    assert json.dumps(frozen,sort_keys=True)==before
    assert report['roles']['TIME']['decisions']['UNKNOWN']==12
    assert report['paired_comparison_engineering_admitted'] and report['paired_endpoint_count']==3
    assert report['role_qualification_admitted'] is False and report['scientific_quality_claim'] is False
    broken=base[:-1]
    bad=evaluate(frozen,{'TIME':time,'BASE':broken})
    assert not bad['paired_comparison_engineering_admitted']
    assert bad['roles']['BASE']['expected_endpoints']==12 and bad['roles']['BASE']['invalid_endpoint_count']==2
    assert bad['roles']['BASE']['missing_event_ids']==['e6']
    # Engineering UNKNOWN cannot conceal a moved endpoint.
    fake=json.loads(json.dumps(time));fake[0]['endpoint_results'][0]['endpoint_exact']='4'
    wrong=evaluate(frozen,{'TIME':fake,'BASE':base})
    assert not wrong['roles']['TIME']['engineering_pass']
    result=dict(status='PASS_PURE_FIXED_MATCH_CENSOR_AMBIGUITY_PAIRED_DENOMINATOR_CHECKS_NOT_REAL_QUALITY',
      checks=['unique_geometric_semantics_still_unknown','multi_overlap_unknown','censored_overlap_unknown',
              'exact_half_not_strict_majority','single_endpoint_overlap_unknown','zero_eligible_source_retained',
              'fine_answers_do_not_change_matches','KEEP_UNKNOWN_counted','bad_missing_output_full_denominator',
              'fake_UNKNOWN_moving_point_rejected','paired_proxy_not_SCI_PASS'],
      media_or_GPU_or_model_calls=0)
    out=Path(__file__).resolve().parents[2]/'reports/twenty_hour_five_20261014_v1/critic/metric_08'
    out.mkdir(exist_ok=True)
    with (out/'pure_check_01.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
