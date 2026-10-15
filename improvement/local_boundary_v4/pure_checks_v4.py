"""Hand-oracle pure checks, never plan/prep/infer/replay entrypoints."""
import argparse
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import json
from lb_contract import plan_endpoint,prompt,resolve_endpoint
from lb_structural import independent_skip,independent_availability,validate_partition
from replay_local_boundaries import independent_event
import lb_io as io


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def synthetic(fps=F(7537,500),n=461):
    points=[F(i)/fps for i in range(n)];end=F(n)/fps
    clock=dict(original_exact_pts=list(map(str,points)),normalized_exact_pts=list(map(str,points)),
        first_original_pts_exact='0',n_frames=n,physical_end_exact=str(end),last_frame_duration_exact=str(1/fps),
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
            last_normalized_pts_exact=str(points[-1]),last_frame_duration_exact=str(1/fps)),
        source_id='SYN01',source_sha256='a'*64,source_bytes=100)
    event=dict(event_id='SYN.EVENT',original_case_id='CH_SYN01_W000',original_segment_index=0,
        original_interval_exact=['0','11'],source_id='SYN01',source_sha256='a'*64,source_bytes=100,
        source_total_frames=n,all_source_exact_pts=list(map(str,points)),
        original_clock_origin_exact='0',original_evidence={'clock':{'path':'synthetic-only.json','sha256':'b'*64}})
    return event,clock


def main(v3,builder):
    old=load('_pure_v3_contract_baseline',Path(v3)/'lb_contract.py')
    adapter=load('_pure_v4_metadata_adapter',builder)
    event,clock=synthetic()
    short={**event,**plan_endpoint(event,'start',clock)}
    assert short['actual_context_native_frames']==46 and short['window_start']=='0' and short['window_end']=='3'
    assert short['actionable'] is False and short['structural_status']=='SHORT_NATIVE_CONTEXT_UNAVAILABLE'
    assert independent_availability(short,clock)['status']=='SHORT_NATIVE_CONTEXT_UNAVAILABLE'
    proof=independent_skip(short,clock);a=proof['endpoint_result']
    assert a['endpoint_exact']=='0' and a['displacement_exact']=='0' and a['actual_model_call'] is False and a['predeclared_skip'] is True
    assert a['applied_decision']=='UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE' and a['raw_decision'] is None
    try:old.plan_endpoint(event,'start',clock)
    except ValueError:pass
    else:raise AssertionError('v3 original short context should still reject')
    active={**event,**plan_endpoint(event,'end',clock)};prior={**event,**old.plan_endpoint(event,'end',clock)}
    assert active['actual_context_native_frames']==91 and len(set(active['source_frame_ordinals']))==64
    assert independent_availability(active,clock)['status']=='AVAILABLE_NATIVE_CONTEXT'
    ignore={'schema','contract_revision','actionable','structural_skip','eligible_first_ordinal','eligible_stop_ordinal','actual_context_native_frames','required_native_frames'}
    assert {k:v for k,v in active.items() if k not in ignore}=={k:v for k,v in prior.items() if k not in ignore}
    assert prompt(active)==old.prompt(prior)
    active.update(original_endpoint_continuity_verified=True,continuity_by_sample={str(i):True for i in range(64)})
    prior.update(original_endpoint_continuity_verified=True,continuity_by_sample={str(i):True for i in range(64)})
    for decision in ({'decision':'KEEP'},{'decision':'UNKNOWN'},
                     {'decision':'REFINE','sample_index':active['allowed_sample_indices'][1]}):
        assert resolve_endpoint(decision,active)==old.resolve_endpoint(decision,prior)
    short['endpoint_result']=a
    counts=validate_partition([event],[active],[short]);assert counts==dict(nominal_endpoints=2,actionable_requests=1,structural_skips=1)
    pair=independent_event(event,{event['event_id']+'.start':a,event['event_id']+'.end':resolve_endpoint({'decision':'UNKNOWN'},active)})
    assert pair['refined_interval_exact']==['0','11'] and not pair['original_event_removed'] and len(pair['endpoint_results'])==2
    zero,zero_clock=synthetic(F(15),100);zero['original_interval_exact']=['0','20/3']
    z=[{**zero,**plan_endpoint(zero,side,zero_clock)} for side in ('start','end')]
    assert all(x['structural_skip'] for x in z) and validate_partition([zero],[],z)['nominal_endpoints']==2
    ze={x['request_id']:independent_skip(x,zero_clock)['endpoint_result'] for x in z}
    assert independent_event(zero,ze)['refined_interval_exact']==['0','20/3']
    tampered=dict(short,actual_context_native_frames=47)
    try:independent_skip(tampered,clock)
    except ValueError:pass
    else:raise AssertionError('wrong native count became a skip')
    malformed=dict(clock,physical_end_exact=clock['normalized_exact_pts'][-1])
    try:plan_endpoint(event,'start',malformed)
    except ValueError:pass
    else:raise AssertionError('bad clock became structural skip')
    reference={'path':'synthetic-only.json','sha256':'c'*64}
    dev=[dict(event_id='E'+str(i),source_role='dev',original_evidence={'input':reference},reuse_rgb_inputs=[reference]) for i in range(20)]
    confirm=[dict(event_id='C'+str(i),source_role='confirm',original_evidence={'input':reference},reuse_rgb_inputs=[reference]) for i in range(18)]
    rd=adapter.adapt({},'dev',dev,adapter.BASE/'dev',{},reference,reference,reference)
    rc=adapter.adapt({},'confirm',confirm,adapter.BASE/'confirm',{},reference,reference,reference,reference)
    assert rd['nominal_endpoint_count']==rd['max_model_call_budget']==40 and rd['actual_model_call_budget'] is None
    assert rc['nominal_endpoint_count']==rc['max_model_call_budget']==36 and len(rc['events'])==18
    assert io.base_path(io.EXPECTED_BASE/'dev')!=io.base_path(io.EXPECTED_BASE/'confirm')
    print(json.dumps(dict(status='PASS_V4_PURE_GEOMETRY_PARTITION_V3_ACTIONABLE_EQUIVALENCE',
        short_native_frames=46,actionable_native_frames=91,unchanged_v3_prompt_math=True,
        mixed_nominal_actionable_skip=[2,1,1],all_structural_keeps_all_events=True,
        dev_nominal_max=[40,40],confirm_nominal_max=[36,36],invalid_clock_is_failure=True,
        tampered_skip_is_failure=True,real_plan_runs=0,media_reads=0,RGB_decodes=0,
        processor_encodes=0,model_calls=0,replays=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v3-code',required=True);p.add_argument('--builder',required=True)
    a=p.parse_args();main(a.v3_code,a.builder)
