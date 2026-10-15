"""First-layer P upper bound on original known ORDINARY points; no later stage."""
import argparse
from fractions import Fraction as F
import os
from pathlib import Path

import facts_common as io
from registration import registration, metadata, ref, completed_job
from adoption import adopt


def upper_bound(views, ordinary, actual_outputs, require_full_counts=True):
    """Complete real unpadded B0 intervals only; touching O is inconclusive."""
    io.require(len(actual_outputs)==len(views) and len({o['case_id'] for o in actual_outputs})==len(views) and
        {o['case_id'] for o in actual_outputs}=={v['case_id'] for v in views}, 'Missing/duplicate output is never a legal EMPTY')
    by_id={o['case_id']:o for o in actual_outputs};touches=[]
    for view in views:
        actual=by_id[view['case_id']]
        io.require(actual['source_name']==view['source_name'] and
            F(actual['source_start_exact'])==F(view['window_start']) and actual['status'] in ('MODEL_OK','LEGAL_EMPTY') and
            ((actual['status']=='LEGAL_EMPTY') == (actual['segments']==[])) and
            len(actual['native_ranges'])==len(actual['segments']), 'Actual successful complete B0/native candidate denominator required')
        for index,(segment,native) in enumerate(zip(actual['segments'],actual['native_ranges'])):
            lo,hi=F(view['window_start']),F(view['window_end']);first,last=map(lambda x:F(str(x)),segment)
            io.require(0<=first<last<=hi-lo and len(native)==2 and native[0]<native[1], 'Actual B0 segment/native membership escaped original context')
            for point in ordinary[view['source_name']]:
                temporal=lo+first<=F(point['exact_pts'])<lo+last
                ordinal=native[0]<=point['ordinal']<native[1]
                io.require(temporal==ordinal, 'Actual same-source ordinal/exact-time membership disagrees')
                if temporal:
                    touches.append(dict(case_id=view['case_id'],source_name=view['source_name'],segment_index=index,
                        original_interval_exact=[str(lo+first),str(lo+last)],ordinary_ordinal=point['ordinal'],ordinary_exact_pts=point['exact_pts']))
    if require_full_counts:
        io.require(len(views)==17 and len(ordinary)==9 and sum(map(len,ordinary.values()))==222,
            'Full first-layer seventeen-window/nine-source/222-observation denominator required')
    return dict(status='B0_UPPER_BOUND_SUFFICIENT' if not touches else 'INCONCLUSIVE_PENDING_REGISTERED_VERIFY',
        complete_B0_P_avoids_original_ORDINARY=not touches,touching_B0_candidates=touches,
        known_ORDINARY_zero_new_additions_sufficiently_proved=not touches,
        baseline_nondeletion_by_frozen_union_rule=True, actual_production_baseline_retention_QA='NOT_RUN',
        complete_positive_recipe_executed=False, conservative_VERIFY_executed=False, strictpositive_executed=False,
        original_KEEP_coverage_proved=False, original_reference_coverage_FAILED_preserved=True,
        original_reference_quality_FAILED_preserved=True, original_UNKNOWN_semantics_preserved=True,
        production_admitted=False,next_level_started=False)


def evaluate(root):
    io.host(cpu=True);reg=registration(root);sources,clocks,views,ordinary=metadata(root,reg)
    by_source={s['video_id']:s for s in sources};by_view={v['case_id']:v for v in views};actual=[]
    new_count=reg['gpu_budget']['max_actual_calls'];new_evidence=[]
    if new_count:
        gate,cpu,files,values,gate_path,_,_=io.accepted_b0(root,'facts');_,resource_sha=io.terminal(gate)
        gpu=root/'facts/B0/gpu_01';complete,done_by_id=completed_job(gpu,gate,gate_path,new_count)
        qa_path=root/'facts/B0/replay_01/completion.json';qa=io.read(qa_path)
        io.require(qa['status']=='PASS_ROLE_FIXED40_B0_NEW_OUTPUT_QA_NOT_FACT_QUALITY' and
            qa['calls']==len(qa['proofs'])==new_count and qa['gpu_completion_sha256']==io.sha(gpu/'completion.json') and
            qa['resource_terminal_sha256']==resource_sha and qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
            qa['new_model_calls']==0,'Complete actual first output QA and unique new GPU natural terminal required')
        proof_by_id={p['case_id']:p for p in qa['proofs']}
        io.require(list(proof_by_id)==list(done_by_id)==[e['case_id'] for e,_,_ in values], 'Full ordered new output/QA denominator differs')
        for entry,proof,meta in values:
            case=entry['case_id'];receipt=done_by_id[case];donepath=io.checked(receipt['done_path'],receipt['done_sha256'])
            qaref=proof_by_id[case];qapath=io.checked(qaref['proof_path'],qaref['proof_sha256']);outqa=io.read(qapath);done=io.read(donepath)
            rawpath=io.checked(done['raw_path'],done['raw_sha256']);requestpath=donepath.parent/'request.json';io.checked(requestpath,done['request_sha256'])
            raw,request=io.read(rawpath),io.read(requestpath)
            io.require(outqa['status']=='PASS_ROLE_FIXED40_B0_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA' and
                outqa['case_id']==done['case_id']==meta['case_id']==case and outqa['done_sha256']==receipt['done_sha256'] and
                outqa['raw_sha256']==done['raw_sha256'] and outqa['segments']==done['segments'] and
                outqa['native_ranges']==done['native_ranges'] and outqa['input_evidence']==done['input_evidence']==raw['input_evidence']==
                request['input_evidence']==proof['input_evidence'] and outqa['first_input_QA_sha256']==proof['first_input_QA_sha256'] and
                request['input_sha256']==entry['input_sha256'] and request['CPU_proof_sha256']==entry['proof_sha256'] and
                done['source_sha256']==meta['source_sha256']==by_view[case]['source_sha256'],
                'Actual untouched generated B0 and independent output QA/native/first-input proof binding differs')
            io.output_tokens(raw,done)
            actual.append(dict(case_id=case,source_name=meta['source_name'],segments=done['segments'],native_ranges=done['native_ranges'],
                source_start_exact=done['source_start_exact'],status=done['status'],adopted=False))
            new_evidence.append(dict(case_id=case,input_ref=ref(entry['input_path']),primary_or_accepted_proof_ref=ref(entry['proof_path']),
                done_ref=ref(donepath),raw_ref=ref(rawpath),output_QA_ref=ref(qapath)))
    for row in reg['execution_plan']:
        if row['mode']=='ADOPT':
            view=by_view[row['case_id']];item=adopt(row,view,by_source[view['source_name']],clocks[view['source_name']],reg['required_files'])
            item['status']='MODEL_OK' if item['segments'] else 'LEGAL_EMPTY';actual.append(item)
    result=upper_bound(views,ordinary,actual)
    io.save(root/'result.json',dict(result,utc=io.utc(),scope='FIRST_LAYER_B0_COMPLETE_UPPER_BOUND_ONLY',
        baseline='TEMPORAL_VERIFY_USER40.46',registration_ref=ref(root/'role_fixed40_registration.json'),
        protocol_ref=reg['protocol_ref'],dev_result_ref=reg['dev_result_ref'],confirm_result_ref=reg['confirm_result_ref'],
        source_audit_plan_ref=reg['source_audit_plan_ref'],source_audit_completion_ref=reg['source_audit_completion_ref'],reference_ref=reg['reference_ref'],
        actual_new_B0_calls=new_count,actual_new_first_input_QA=new_count,actual_new_first_output_QA=new_count,
        exact_identity_successful_B0_adoptions=17-new_count,full_B0_window_denominator=17,original_ORDINARY_observations=222,
        new_execution_evidence=new_evidence,old_failed_gates_changed=False,no_baseline30_VERIFY_strictpositive_426_or_package_started=True))
    print(__import__('json').dumps(dict(status=result['status'],touches=len(result['touching_B0_candidates']))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';evaluate(io.root_path(args.root))
