"""Unique prospective double-buffer control; main alone admits/starts this file."""
import argparse
from concurrent.futures import Future
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

import pc_contract as c
import pc_io as io


class Runner:
    def __init__(self,context):
        self.ctx=context;self.lock=threading.Lock();self.journal=io.BASE/'run_01/journal.jsonl'
        self.resources_lock=threading.Lock();self.active={};self.GPU_bound=None
        self.stop_sources=threading.Event()
    def start(self,phase,item,argv,cpu=True,bound=None):
        with self.lock:
            c.guard_no_repeat(io.rows(self.journal),phase,item)
            io.append(self.journal,dict(event='BEGIN',phase=phase,item=item,argv=list(map(str,argv)),utc=io.utc()))
        log=io.BASE/'run_01/logs'/(phase+'_'+item+'.log');log.parent.mkdir(parents=True,exist_ok=True)
        env=dict(os.environ)
        env.update(self.ctx['reg']['explicit_child_environment'])
        if cpu:env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        stream=log.open('x')
        try:process=subprocess.Popen(list(map(str,argv)),stdout=stream,stderr=subprocess.STDOUT,env=env)
        except BaseException:
            stream.close();self.record(phase,item,'FAILED',-1);raise
        with self.resources_lock:
            if bound:self.active[process.pid]=bound
        return process,stream,phase,item,log
    def record(self,phase,item,event,code,**extra):
        with self.lock:io.append(self.journal,dict(event=event,phase=phase,item=item,exit_code=code,utc=io.utc(),**extra))
    def finish(self,handle):
        process,stream,phase,item,log=handle;code=process.wait();stream.close()
        with self.resources_lock:self.active.pop(process.pid,None)
        self.record(phase,item,'COMPLETE' if code==0 else 'FAILED',code,log_path=str(log),log_sha256=io.sha(log))
        c.require(code==0,'Started operation failed; preserve successes/raw, no whole-chain retry: '+phase+'/'+item)
    def run(self,phase,item,argv,cpu=True,bound=None):self.finish(self.start(phase,item,argv,cpu,bound))
    def can_start(self,bound):
        with self.resources_lock:
            active=list(self.active.values())+([self.GPU_bound] if self.GPU_bound else [])
        return c.runnable(bound,io.snapshot(self.ctx['store'].base),active)
    def start_if_fits(self,phase,item,argv,bound):
        reservation=(phase,item)
        with self.resources_lock:
            active=list(self.active.values())+([self.GPU_bound] if self.GPU_bound else [])
            if not c.runnable(bound,io.snapshot(self.ctx['store'].base),active):return None
            self.active[reservation]=bound # Atomic resource reservation across prepare/replay scheduling threads.
        try:handle=self.start(phase,item,argv)
        except BaseException:
            with self.resources_lock:self.active.pop(reservation,None)
            raise
        with self.resources_lock:self.active.pop(reservation);self.active[handle[0].pid]=bound
        return handle
    def run_bounded(self,phase,item,argv,bound):
        while True:
            handle=self.start_if_fits(phase,item,argv,bound)
            if handle:self.finish(handle);return
            time.sleep(1)


def async_task(call):
    future=Future()
    def work():
        try:future.set_result(call())
        except BaseException as error:future.set_exception(error)
    thread=threading.Thread(target=work,daemon=False);thread.start();return future,thread


def source_bounds(ctx,sid):
    source=next(source for source in ctx['plan']['sources'] if source['source_id']==sid)
    rows=[row for row in ctx['plan']['requests'] if row['source_id']==sid]
    groups={key:row for key,row in ctx['plan']['RGB_groups'].items() if row['source_id']==sid}
    config=io.read(io.RUN/'b_score_aligned_package_v4/config.json')
    bound=c.source_bound(source,rows,groups,config['video_size'])
    bound['memory_bytes']+=ctx['reg']['CPU_process_overhead_bound_bytes']
    return bound


def replay_bound(ctx,rid):
    proof=io.read(ctx['store'].checked_ref(ctx['store'].ref('permanent/proofs/'+rid+'_CPU_input.json')))
    manifest=io.read(ctx['store'].checked_ref(proof['input_manifest_ref']));meta=manifest['original_metadata']
    rgb=64*meta['width']*meta['height']*3
    return dict(memory_bytes=ctx['reg']['CPU_process_overhead_bound_bytes']+2*rgb+4*proof['actual_storage_bytes'],
        disk_bytes=2*ctx['store'].ref('permanent/proofs/'+rid+'_CPU_input.json')['bytes']+proof['input_manifest_ref']['bytes']+4096)


def prepare_batch(ctx,runner,batch):
    """Dynamic resource pool. Source order/membership fixed; CPU launches only vary in concurrency."""
    pending=list(batch['source_ids']);active=[];completed={};error=None
    try:
        while pending or active:
            c.require(not runner.stop_sources.is_set(),'Fatal controller phase: no additional source operation')
            io.before_new_operation(ctx['reg'])
            while pending:
                sid=pending[0];bound=source_bounds(ctx,sid)
                reuse=ctx['reg'].get('preexisting_source_completion_refs',{}).get(sid)
                if reuse:
                    complete=io.read(ctx['store'].checked_ref(reuse))
                    c.require(complete['source_id']==sid and complete['status']=='PASS_COMPLETE_SOURCE_NEW_INPUTS_NOT_GPU_OR_QUALITY',
                        'Frozen successful source reuse receipt differs')
                    with runner.lock:
                        c.guard_no_repeat(io.rows(runner.journal),'SOURCE_PREPARE',sid)
                        io.append(runner.journal,dict(event='REUSE',phase='SOURCE_PREPARE',item=sid,exit_code=0,actual_new_calls=0,receipt=reuse,utc=io.utc()))
                    completed[sid]=reuse;pending.pop(0);continue
                io.before_new_operation(ctx['reg'])
                handle=runner.start_if_fits('SOURCE_PREPARE',sid,[sys.executable,'-u',io.INPUT/'code/prepare_source.py','source',
                    '--registration',ctx['lib']['input_reg']['_registration_path'],'--source-id',sid],bound)
                if handle is None:break
                active.append((sid,handle));pending.pop(0)
            for sid,handle in list(active):
                if handle[0].poll() is not None:
                    active.remove((sid,handle));runner.finish(handle)
                    completed[sid]=ctx['store'].ref('permanent/proofs/source_'+sid+'_completion.json')
            if pending or active:time.sleep(1)
    except BaseException as failure:error=failure
    finally:
        # Do not interrupt begun sources, including when deadline/pending work fails.
        for sid,handle in active:
            try:
                runner.finish(handle);completed[sid]=ctx['store'].ref('permanent/proofs/source_'+sid+'_completion.json')
            except BaseException as failure:
                if error is None:error=failure
    if error:raise error
    if batch.get('cpu_only_empty_batch') is True:
        for sid in batch['source_ids']:
            complete=io.read(ctx['store'].checked_ref(completed[sid]));c.require(not complete['consumers'],'CPU-only source block unexpectedly created model consumers')
        io.save(io.BASE/'run_01'/('empty_'+batch['batch_id']+'.json'),dict(status='PASS_CPU_ONLY_EMPTY_SOURCE_BLOCK_NO_GPU_JOB',
            source_completion_refs=completed,actual_model_calls=0,source_ids=batch['source_ids']))
        return
    root=io.RUNTIME/'runs'/batch['batch_id']
    io.save(root/'CPU_admission.json',dict(status='PASS_INDEPENDENT_COMPLETE_BATCH_CPU_INPUTS',
        batch_sha256=io.sha(io.RUNTIME/'batches'/(batch['batch_id']+'.json')),global_graph_sha256=ctx['reg']['global_graph_sha256'],
        source_ids=batch['source_ids'],request_ids=batch['request_ids'],source_completion_refs={sid:completed[sid] for sid in batch['source_ids']}))
    runner.run('BATCH_INPUT_ADMIT',batch['batch_id'],[sys.executable,'-u',io.RUNTIME/'code/admit_batch.py',
        '--protocol',ctx['runtime_protocol'],'--batch-id',batch['batch_id']])
    protocol=ctx['context']['protocol']
    io.save(root/'gpu_admission.json',dict(status='PASS_INDEPENDENT_PRODUCTION_BATCH_GPU_ADMISSION',
        protocol_sha256=io.sha(ctx['runtime_protocol']),batch_sha256=io.sha(io.RUNTIME/'batches'/(batch['batch_id']+'.json')),
        global_graph_sha256=ctx['reg']['global_graph_sha256'],batch_CPU_admission_sha256=io.sha(root/'CPU_admission.json'),
        input_admission_sha256=io.sha(root/'input_admission.json'),actual_model_call_budget=len(batch['request_ids']),
        gpu_job_name=batch['gpu_job_name'],actual_physical_parameters=8782459120,optimizer_updates=0,
        issuing_controller_registration_sha256=io.sha(ctx['registration_path']),main_execution_admission_sha256=io.sha(ctx['reg']['main_execution_admission_path'])))


def post_batch(ctx,runner,batch):
    bid=batch['batch_id'];args=['--protocol',ctx['runtime_protocol'],'--batch-id',bid]
    peak=max((replay_bound(ctx,rid) for rid in batch['request_ids']),key=lambda bound:bound['memory_bytes'])
    runner.run_bounded('TERMINAL_CAPTURE',bid,[sys.executable,'-u',io.RUNTIME/'code/replay_batch.py','terminal',*args],peak)
    pointer=io.read(io.RUNTIME/'runs'/bid/'terminal_pointer.json')
    # Independent first RGB replay once per consumer; pooled by actual full-source bound, not a fixed worker count.
    pending=list(batch['request_ids']);active=[];error=None
    try:
        while pending or active:
            while pending:
                rid=pending[0];bound=replay_bound(ctx,rid)
                handle=runner.start_if_fits('FIRST_INPUT_REPLAY',rid,[sys.executable,'-u',io.BASE/'code/input_replay_one.py',
                    '--registration',ctx['registration_path'],'--consumer',rid,'--batch-id',bid],bound)
                if handle is None:break
                active.append(handle);pending.pop(0)
            for handle in list(active):
                if handle[0].poll() is not None:active.remove(handle);runner.finish(handle)
            if pending or active:time.sleep(1)
    except BaseException as failure:error=failure
    finally:
        for handle in active:
            try:runner.finish(handle)
            except BaseException as failure:
                if error is None:error=failure
    if error:raise error
    runner.run_bounded('OUTPUT_REPLAY',bid,[sys.executable,'-u',io.RUNTIME/'code/replay_batch.py','replay',*args],peak)
    runner.run_bounded('LEASE_CLOSE',bid,[sys.executable,'-u',io.RUNTIME/'code/close_batch.py',*args],peak)


def control(registration_path):
    io.host(parent=True);ctx=io.load(registration_path)
    from pr_contract import batch_membership
    coverage=c.full_coverage(ctx['plan'],ctx['batches'],batch_membership)
    root=io.BASE/'run_01';root.mkdir(exist_ok=False) # Unique whole-chain launch; failures never auto-restart.
    io.save(root/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),registration_path=str(ctx['registration_path']),
        registration_sha256=io.sha(ctx['registration_path']),main_execution_admission_sha256=io.sha(ctx['reg']['main_execution_admission_path']),
        frozen_batch_index_sha256=io.sha(ctx['reg']['frozen_batch_index_ref']['path']),global_graph_sha256=ctx['reg']['global_graph_sha256'],
        code_SHA=ctx['reg']['required_code_files'],coverage=coverage,parent_CUDA_nonempty=True,new_model_calls_in_controller=0,
        explicit_child_environment=ctx['reg']['explicit_child_environment'],
        explicit_import_environment_recovery_ref=ctx['reg']['explicit_import_environment_recovery_ref'],
        original_control_registration_ref=ctx['reg']['original_control_registration_ref']))
    (root/'journal.jsonl').touch(exist_ok=False);runner=Runner(ctx);threads=[];prep=None;post=None;GPU=None
    try:
        prep=async_task(lambda:prepare_batch(ctx,runner,ctx['batches'][0]));threads.append(prep[1])
        for ix,batch in enumerate(ctx['batches']):
            prep[0].result()
            if batch.get('cpu_only_empty_batch') is True:
                if ix+1<len(ctx['batches']):prep=async_task(lambda b=ctx['batches'][ix+1]:prepare_batch(ctx,runner,b));threads.append(prep[1])
                continue
            io.before_new_operation(ctx['reg'])
            if post and post[0].done():post[0].result();post=None # Known QA failure must block another GPU job.
            # Previous batch post/close can overlap this GPU; B+2 prep waits for its release to keep only two staged buffers.
            with runner.resources_lock:runner.GPU_bound=ctx['reg']['GPU_host_resource_bound']
            argv=[sys.executable,io.RUN/'resource_unlimited_v1_20261007/gpu_run.py','--name',batch['gpu_job_name'],
                '--max-seconds',str(batch['gpu_max_seconds']),'--queue-seconds',str(batch['gpu_queue_seconds']),
                '--planned-output-bytes',str(batch['planned_GPU_output_bytes']),
                '--capacity-reason','Frozen complete source batch; exact inputs retained; single base load, independent natural terminal and first replay.',
                '--',sys.executable,'-u',io.RUNTIME/'code/infer_batch.py','--protocol',ctx['runtime_protocol'],'--batch-id',batch['batch_id']]
            GPU=runner.start('GPU_WRAPPER',batch['batch_id'],argv,cpu=False)
            if post:post[0].result();post=None
            if ix+1<len(ctx['batches']):prep=async_task(lambda b=ctx['batches'][ix+1]:prepare_batch(ctx,runner,b));threads.append(prep[1])
            current_GPU=GPU;GPU=None
            runner.finish(current_GPU)
            with runner.resources_lock:runner.GPU_bound=None
            post=async_task(lambda b=batch:post_batch(ctx,runner,b));threads.append(post[1])
        if post:post[0].result()
        runner.run('GLOBAL_AGGREGATE','ALL426',[sys.executable,'-u',io.BASE/'code/aggregate.py','--registration',ctx['registration_path']])
        io.save(root/'completion.json',dict(status='PASS_CONTROLLER_ALL_BATCHES_NATURAL_TERMINALS_AND_FIRST_REPLAYS_NOT_QUALITY',
            coverage=coverage,global_completion_path=str(io.BASE/'exports_01/global_completion.json'),
            global_completion_sha256=io.sha(io.BASE/'exports_01/global_completion.json'),actual_new_model_calls=coverage['actual_model_calls']))
    except BaseException as error:
        # Await owned begun work naturally; no terminate/whole-chain retry or fabricated fallbacks.
        runner.stop_sources.set()
        with runner.resources_lock:runner.GPU_bound=None
        if GPU:
            try:runner.finish(GPU)
            except BaseException:pass
        for thread in threads:thread.join()
        io.save(root/'failure.json',dict(status='FAILED_CONTROL_PRESERVE_ALL_ATTEMPTS_SUCCESS_RAW_COSTS',error=repr(error),
            traceback=traceback.format_exc(),no_whole_chain_retry=True,no_external_process_killed=True,journal_sha256=io.sha(root/'journal.jsonl')))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);args=parser.parse_args();control(args.registration)
