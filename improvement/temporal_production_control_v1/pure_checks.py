"""New controller-only coverage/resource/journal/clock tests. No subprocess/cache."""
import copy
from fractions import Fraction as F
import threading
import types

import pc_contract as c


def run(batch_validator,exact_clock,Runner,control_io):
    passed=[]
    def reject(call,label):
        try:call()
        except (ValueError,KeyError,TypeError):passed.append(label);return
        raise AssertionError('Expected rejection: '+label)
    plan=dict(sources=[dict(source_id='S'+str(i)) for i in range(5)],requests=[])
    for source in plan['sources']:
        if source['source_id']=='S2':continue
        for side,execution in [('start','MODEL'),('end','STRUCTURAL_UNKNOWN_NO64'),('verify','MODEL')]:
            plan['requests'].append(dict(source_id=source['source_id'],request_id=source['source_id']+'.'+side,execution=execution))
    plan['consumers']=[row['request_id'] for row in plan['requests'] if row['execution']=='MODEL']
    def batch(bid,sources,empty=False):
        rows=[row for row in plan['requests'] if row['source_id'] in sources]
        actual=[row['request_id'] for row in rows if row['execution']=='MODEL']
        return dict(batch_id=bid,source_ids=sources,request_ids=actual,logical_request_ids=[row['request_id'] for row in rows],
            actual_model_call_budget=len(actual),gpu_job_name=None if empty else 'SYN_'+bid,cpu_only_empty_batch=empty,
            membership_reason='FROZEN_SOURCE_ORDER_AND_ACTUAL_CAPACITY_ONLY',predictions_or_reference_metrics_used_for_membership=False)
    batches=[batch('B0',['S0','S1']),batch('B1',['S2'],True),batch('B2',['S3','S4'])]
    complete=c.full_coverage(plan,batches,batch_validator)
    c.require(complete['source_count']==5 and complete['actual_model_calls']==8 and complete['logical_requests']==12,'Frozen complete denominator differs')
    passed.append('global_sources_actual_requests_typed_skips_and_empty_no_fake_GPU')
    reject(lambda:c.full_coverage(plan,batches[:2],batch_validator),'missing_source_and_request_batch_rejected')
    bad=copy.deepcopy(batches);bad[-1]['gpu_job_name']=bad[0]['gpu_job_name']
    reject(lambda:c.full_coverage(plan,bad,batch_validator),'duplicate_real_GPU_job_name_rejected')
    bad=copy.deepcopy(batches);bad[1]['gpu_job_name']='fake_zero_model_GPU'
    reject(lambda:c.full_coverage(plan,bad,batch_validator),'empty_source_fake_GPU_job_rejected')
    expected={('SOURCE_PREPARE','S0'),('FIRST_INPUT_REPLAY','S0.start')}
    journal=[dict(event='REUSE',phase='SOURCE_PREPARE',item='S0',exit_code=0,actual_new_calls=0),
        dict(event='BEGIN',phase='FIRST_INPUT_REPLAY',item='S0.start'),dict(event='COMPLETE',phase='FIRST_INPUT_REPLAY',item='S0.start',exit_code=0)]
    c.validate_stage_journal(journal,expected);passed.append('first_stage_journal_complete_and_explicit_success_reuse')
    reject(lambda:c.guard_no_repeat(journal,'FIRST_INPUT_REPLAY','S0.start'),'successful_first_replay_retry_rejected')
    reject(lambda:c.validate_stage_journal(journal[:-1],expected),'pending_first_replay_not_global_complete')
    reject(lambda:c.validate_stage_journal(journal+[journal[-1]],expected),'duplicate_complete_journal_rejected')
    snapshot=dict(mem_available_bytes=10,disk_available_bytes=30,affinity_cpus=4,load_1min=0)
    require_bound=dict(memory_bytes=6,disk_bytes=12)
    c.require(c.runnable(require_bound,snapshot,[]) and not c.runnable(require_bound,snapshot,[require_bound]),'Actual byte reservation admission differs')
    c.require(not c.runnable(require_bound,dict(snapshot,affinity_cpus=4,load_1min=4),[]),'CPU peer pressure ignored')
    passed.append('resource_slots_and_bytes_dynamic_no_fixed_workers_or_GB')
    old_snapshot=control_io.snapshot;control_io.snapshot=lambda root:snapshot
    try:
        runner=Runner(dict(store=types.SimpleNamespace(base='/not-read')))
        counter=[]
        def fake_start(phase,item,argv):
            counter.append(item);return (types.SimpleNamespace(pid=100+len(counter)),None,phase,item,None)
        runner.start=fake_start;results=[]
        def thread(item):results.append(runner.start_if_fits('SYN',item,['no-subprocess'],require_bound))
        workers=[threading.Thread(target=thread,args=(str(i),)) for i in range(2)]
        for worker in workers:worker.start()
        for worker in workers:worker.join()
        c.require(len(counter)==1 and sum(result is not None for result in results)==1 and len(runner.active)==1,
                  'Concurrent prep/replay resource reservation oversubscribed')
        passed.append('atomic_two_scheduling_threads_reserve_before_launch')
    finally:control_io.snapshot=old_snapshot
    original=dict(raw_time_base='1/15',raw_first_pts_ticks=5,native_pts_ticks=[5,8,11,14],native_frame_end_pts_ticks=[8,11,14,17])
    source=dict(source_id='SYN',source_sha256='a'*64,source_path='/synthetic/not-opened',width=8,height=8,fps_num=5,fps_den=1,
        old_clock=dict(n_frames=4,planned_physical_end_exact='4/5',old_terminal_evidence={'kind':'NATIVE_LAST_FRAME_PACKET_DURATION'}))
    clock=dict(n_frames=4,original_exact_pts=['1/3','8/15','11/15','14/15'],normalized_exact_pts=['0','1/5','2/5','3/5'],
        first_original_pts_exact='1/3',physical_end_exact='4/5',source_sha256='a'*64,source_path=source['source_path'],measured_geometry=[8,8],
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',last_frame_duration_exact='1/5',last_normalized_pts_exact='3/5'))
    exact_clock(source,clock,original);passed.append('independent_native_old_ticks_and_new_positive_terminal_match')
    legacy=copy.deepcopy(original);legacy['native_frame_end_pts_ticks']=None
    source['old_clock']['old_terminal_evidence']['kind']='LEGACY_CFR_N_DIV_FPS'
    exact_clock(source,clock,legacy);passed.append('explicit_legacy_CFR_planning_only_new_native_witness_still_required')
    bad=copy.deepcopy(clock);bad['physical_endpoint_evidence']['last_frame_duration_exact']='0'
    reject(lambda:exact_clock(source,bad,legacy),'legacy_zero_actual_duration_rejected')
    source['old_clock']['old_terminal_evidence']['kind']='UNKNOWN'
    reject(lambda:exact_clock(source,clock,legacy),'unknown_null_terminal_not_CFR_recovery')
    # Legal two-buffer ordering: B2 materialization only after B0 closes.
    trace=['PREP0','GPU0_BEGIN','PREP1','GPU0_END','QA0_BEGIN','GPU1_BEGIN','CLOSE0','PREP2','GPU1_END']
    c.require(trace.index('GPU1_BEGIN')<trace.index('CLOSE0')<trace.index('PREP2'),'Double-buffer control ordering differs')
    passed.append('GPU_next_overlaps_prior_QA_but_second_next_prep_waits_RGB_close')
    return dict(status='PASS_NEW_PURE_CONTROLLER_PIPELINE_NOT_REAL_PRODUCTION',checks=passed,
        real_subprocesses=0,source_or_GT_reads=0,media_decodes=0,processor_encodes=0,model_calls=0,cache_IO=0,
        lease_accepts_or_releases=0,old_successful_pure_suites_repeated=False)
