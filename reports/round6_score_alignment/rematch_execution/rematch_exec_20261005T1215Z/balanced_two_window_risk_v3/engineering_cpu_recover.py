"""Recover the one actual valid raw by independent CPU, never regenerate it."""
import json,os,math
from pathlib import Path
from fractions import Fraction
import bw_common as c

def main():
    previous=c.RUN/'balanced_two_window_risk_v2';lock=c.read(previous/'source_lock.json')
    c.require(c.sha(previous/'source_lock.json')=='9174b4bfb56c54c0e49db0a2d8eb5a600fb9bd5d5ac5edd540d81a867c3c2214','v2 source authority')
    for p,s in lock['files'].items():c.require(c.sha(p)==s,'old frozen source changed: '+p)
    c.require(not (c.HERE/'first_real_acceptance.json').exists(),'do not repeat completed CPU replay')
    rt,ex,cc,student,old,frames,production=c.helpers()
    raws=list((previous/'developer_01').rglob('raw.json'))
    c.require(len(raws)==1 and not list((previous/'developer_01').rglob('done.json')),'exact one recovery denominator')
    rawpath=raws[0];raw=c.read(rawpath);w=raw['window'];_,jobs=c.jobs_for('developer')
    job=next(j for j in jobs if any(p['window']==w for p in j['windows']));ix=next(i for i,p in enumerate(job['windows']) if p['window']==w)
    identity=c.read(previous/'developer_01/model.json');c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'actual GPU original model authority')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    from bw_native import exact_ranges
    from bw_engine import replay
    segments,errors,warnings=parse_segments(raw['raw_output'],Fraction(w['exact_raw_end'])-Fraction(w['exact_raw_start']),allow_empty=True)
    c.require(not errors and raw['actual_model_call'] is True and raw['overview_adapter_disabled'] is False and raw['selected_token_scores'] and all(isinstance(x,(int,float)) and math.isfinite(x) for x in raw['selected_token_scores']),'actual raw original validator/scores failed')
    legacy=native_segment_ranges(segments,raw['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    rational=exact_ranges(segments,w)
    c.require(rational!=legacy and rational==[list(pair) for pair in legacy],'actual list tuple mismatch not reproduced/value changed')
    admitted=next(p for p in c.read(c.HERE/'cpu_acceptance.json')['proofs'] if p['scope']=='developer' and p['video_id']==job['video_id'] and p['index']==ix)
    c.require(admitted['video_identity']==raw['video_identity'] and admitted['window']==w,'actual raw input differs from original accepted input')
    value=dict(status='MODEL_OK' if segments else 'LEGAL_EMPTY',output_valid=True,parsed_segments=segments,parse_errors=errors,parse_warnings=warnings,
        native_frame_realizability=dict(status='PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY',ranges=rational,not_limited_to_64_teacher_samples=True),
        raw_output=raw['raw_output'],raw_receipt=str(rawpath),video_identity=raw['video_identity'],constraint_stats=raw['constraint_stats'],generation_time_constraint=True,
        input_tokens=raw['input_tokens'],output_tokens=len(raw['output_token_ids']),generation_seconds=raw['generation_seconds'],
        request_sha256=cc.digest(c.local_request(job,ix,'BW',identity,ex)),bound_files={str(rawpath):c.sha(rawpath)},arm='BW',window=w,model_identity=identity,
        context_audit={},vision_tensor_signature=admitted['vision_signature'],exact_success_recovered_from_previous_version=True,new_model_calls_this_version=0)
    done=c.done_path('developer',job,ix,'BW',cc);c.save(done,value)
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    proof=replay(done,job,ix,ex,rt,student,processor)
    import torch
    c.require(not torch.cuda.is_initialized(),'CPU initialized CUDA')
    first=dict(proof,status='PASS_REAL_FIRST_BALANCED_WINDOW_AND_INDEPENDENT_CPU_REPLAY',utc=c.utc(),pid=os.getpid(),separate_CPU_process=True,CUDA_initialized=False,
        original_raw_sha256=c.sha(rawpath),actual_old_rejection_reproduced=True,integer_range_values_unchanged=True,recovered_prior_model_call=True)
    c.save(c.HERE/'first_real_acceptance.json',first)
    oldnt=previous/'nontest_01';nt=c.HERE/'nontest_01';accepted=c.read(oldnt/'independent_validation.json')
    production.check_independent(accepted,'nontest',len(old.rows(oldnt/'selected.jsonl')))
    c.require(len(accepted['checks'])==11 and all(accepted['checks'].values()),'old NT complete11 strict')
    references=[]
    for name in ('cpu_acceptance.json','prefix_cpu_acceptance.json','prepared.json','accounting_origin.json'):
        c.require(c.sha(c.HERE/name)==c.sha(previous/name),'CPU successful bytes changed');references.append(dict(path=str(previous/name),sha256=c.sha(previous/name)))
    for p in oldnt.iterdir():
        if p.is_file():c.require(c.sha(nt/p.name)==c.sha(p),'exact NT bytes changed');references.append(dict(path=str(p),sha256=c.sha(p)))
    resource=c.RUN/'controller/aic_BW_risk_v2_developer.resource.json';v=c.read(resource)
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    c.require([r for r in ledger if r.get('name')==v['name']]==[v] and v['status']=='failed' and v['exit_code']==1 and v['stop_reason'] is None and v['charged_seconds']>0,'old unique failed GPU cost')
    for p in (rawpath,previous/'developer_01/model.json',resource,previous/'execution_failure.json',previous/'source_lock.json',c.RUN/'controller/aic_BW_risk_v2_developer.log'):
        references.append(dict(path=str(p),sha256=c.sha(p)))
    c.save(c.HERE/'engineering_handoff.json',dict(status='PASS_V2_TYPE_REPRESENTATION_REPAIR_EXACT_RAW_CPU_AND_NT_HANDOFF',utc=c.utc(),
        previous_lock_sha256=c.sha(previous/'source_lock.json'),recovered_successes=[dict(path=str(done),sha256=c.sha(done),bound_files=value['bound_files'])],references=references,
        prior_failed_resource=dict(path=str(resource),sha256=c.sha(resource),charged_seconds=v['charged_seconds']),nontest_exact_acceptance_reused=True,
        old_raw_bytes_unchanged=True,old_window_and_native_range_values_unchanged=True,new_decoder_replays=1,new_model_calls=0,new_optimizer_updates=0,
        scientific_route_actual_calls_total_expected=132,new_model_calls_in_v3_expected=131,first_real_acceptance_sha256=c.sha(c.HERE/'first_real_acceptance.json')))
    print(json.dumps(dict(status='PASS_V2_TYPE_REPRESENTATION_REPAIR_EXACT_RAW_CPU_AND_NT_HANDOFF',utc=c.utc(),first_proof_sha256=c.sha(c.HERE/'first_real_acceptance.json'),raw_sha256=c.sha(rawpath),new_model_calls=0,new_optimizer_updates=0)))
if __name__=='__main__':main()
