"""First independent candidate-output QA and local external comparison."""
import argparse
from bisect import bisect_left
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import sys

from diagnose_underselection28 import read,ref,bound,save


def main(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    import numpy as np
    from transformers import AutoTokenizer
    W=Path('/home/inspur/aic_video_work')
    P=W/'bottleneck_24h_20261019_v1';N=P/'summary_objective_v20'
    RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    reg=read(root/'registration38.json')
    qa_reg=read(root/'QA_registration39.json')
    assert ref(__file__)==qa_reg['code_ref'] and ref(root/'registration38.json')==qa_reg['generation_registration_ref']
    done=read(root/'completion38.json')
    assert done['status']=='COMPLETE_ONE_STEP_TWO_ARM_FIXED8_PROBABILITY_AND4_LOCAL_GENERATIONS'
    assert done['actual_new_forwards']==32 and done['free_generations']==8 and done['optimizer_updates']==0
    assert done['adopted_CPU_candidate_steps']==2 and done['base_unchanged'] and done['adapter_weights_unchanged']
    resource_path=RUN/'controller'/(reg['job_name']+'.resource.json')
    resource=read(resource_path)
    ledger=[json.loads(l) for l in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if l]
    assert [x for x in ledger if x.get('name')==reg['job_name']]==[resource]
    assert resource['status']=='completed' and resource['exit_code']==0
    sys.path.insert(0,str(N/'evaluation_code21'))
    from summary_grammar6 import BoundedSegmentsGrammar
    from summary_output import parse_summary
    from evaluate_summary import metric, native_interval_mask
    tok=AutoTokenizer.from_pretrained(reg['model_directory'],local_files_only=True)
    prepared=read(bound(reg['prepared_ref']))
    selected={x['uid']:x for x in prepared['samples']}
    assert len(selected)==8 and len(list(root.glob('forward38_*.json')))==32
    exact=read(root/'exact_adapter_load_acceptance38.json')
    assert all(x['post_restore_all288_bit_equal_saved'] for x in exact['roles'].values())
    old_probs=read(bound(qa_reg['adopted_probability31_QA_ref']))
    old_prob={x['uid']:x for x in old_probs['details']}
    probs=[]
    for item in done['results']:
        row=dict(uid=item['uid'],sid=item['sid'],domain=item['domain'],stratum=item['stratum'])
        old=old_prob[item['uid']]['role']['trained']['common_route_logodds_nonempty_vs_empty']
        row['old_final20_route_logodds']=old
        for role in ('KEEP_M','RESET_M'):
            pair=item['roles'][role]
            for kind,m in pair.items():
                raw=read(root/('forward38_%s_%s_%s.json'%(item['uid'],role,kind)))
                assert raw['measurements']==m
                assert len(m['token_CE'])==m['tokens'] and all(math.isfinite(x) and x>=0 for x in m['token_CE'])
                assert math.isclose(sum(m['token_CE']),m['sum_CE'],rel_tol=1e-6,abs_tol=1e-5)
                for name in ('common_prefix_decision','canonical_opening_decision'):
                    if name in m:
                        masses=m[name]['grammar_normalized_branch_mass']
                        assert all(0<=v<=1.00001 for v in masses.values()) and abs(sum(masses.values())-1)<1e-5
            c=pair['nonempty']['common_prefix_decision']
            odds=c['canonical_nonempty_route_log_probability']-c['canonical_empty_route_log_probability']
            row[role]=dict(route_logodds=odds,delta_from_old_final20=odds-old,
                           nonempty_path_mean_CE=pair['nonempty']['mean_CE'])
        row['RESET_minus_KEEP_logodds']=row['RESET_M']['route_logodds']-row['KEEP_M']['route_logodds']
        probs.append(row)
    assert len(probs)==8
    validated=[]
    for r in done['free_output_refs']:
        value=read(bound(r));uid,role=value['uid'],value['role']
        assert uid in selected and selected[uid]['domain']=='development'
        assert value['request_ref']==selected[uid]['request_ref'] and value['model_weights_ref']==reg[role+'_weights_ref']
        assert role in ('KEEP_M','RESET_M')
        raw=read(bound(value['raw_token_ref']))
        assert all(value[k]==raw[k] for k in ('uid','sid','role','request_ref','model_weights_ref','generated_ids'))
        ids=value['generated_ids']
        assert ids and ids[-1]==151645 and 151645 not in ids[:-1]
        text=tok.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        assert text==value['raw_text']
        request=read(bound(value['request_ref']))
        start,end=Fraction(request['plan']['window_start_exact']),Fraction(request['plan']['window_end_exact'])
        assert BoundedSegmentsGrammar(end-start,6,True).complete(text)
        segments=parse_summary(text,end-start)
        assert value['parsed_exact_segments']==[[str(a),str(b)] for a,b in segments]
        clock=read(bound(request['source_clock_ref']))
        points=list(map(Fraction,clock['normalized_exact_pts']))
        assert clock['source_sha256']==request['source_sha256'] and 0<=start<end<=Fraction(clock['physical_end_exact'])
        ranges=[]
        for a,b in segments:
            lo,hi=bisect_left(points,start+a),bisect_left(points,start+b)
            assert 0<=lo<=hi<=len(points)
            assert all(start+a<=points[i]<start+b for i in range(lo,hi))
            ranges.append([lo,hi])
        validated.append(dict(uid=uid,sid=value['sid'],role=role,native_ranges=ranges,
                              output_ref=r,empty=not segments))
    assert len(validated)==8 and len({(x['uid'],x['role']) for x in validated})==8
    save(root/'first_output_QA39.json',dict(status='PASS_ALL32_PROBABILITY_AND8_FIRST_CANDIDATE_TOKEN_GRAMMAR_NATIVE_OUTPUTS',
        QA_code_ref=ref(__file__),completion_ref=ref(root/'completion38.json'),resource_ref=ref(resource_path),
        unique_ledger_equal=True,probability_details=probs,generation_details=validated,
        invalid_output_to_empty=False,model_replay=False,reference_labels_read=False))
    # Labels are read only after all real outputs have passed their first checks.
    prior_eval=read(bound(qa_reg['adopted_final20_evaluation_ref']))
    source_refs={x['sid']:x for x in prior_eval['sources']}
    source_results=[]
    for uid,row in selected.items():
        if row['domain']!='development':
            continue
        request=read(bound(row['request_ref']))
        start,end=Fraction(request['plan']['window_start_exact']),Fraction(request['plan']['window_end_exact'])
        points=list(map(Fraction,read(bound(request['source_clock_ref']))['normalized_exact_pts']))
        domain=native_interval_mask(points,[(start,end)])
        assert domain.any()
        data_ref=source_refs[row['sid']]['baseline_human_data_ref']
        with np.load(bound(data_ref),allow_pickle=False) as data:
            labels=data['labels'];baseline=data['baseline']
        assert labels.dtype==baseline.dtype==np.bool_ and len(labels)==len(points)==len(baseline)
        masks={'BASELINE40_47':baseline&domain}
        output_rows={}
        for role,path in [('ORIGINAL_TIME',P/'summary_generation_10/INIT_TIME'/(uid+'.output.json')),
                          ('FINAL20',N/'summary_generation_10/TRAINED'/(uid+'.output.json'))]:
            output=read(bound(qa_reg['adopted_control_outputs'][uid][role]))
            assert Path(qa_reg['adopted_control_outputs'][uid][role]['path'])==path
            segments=parse_summary(output['raw_text'],end-start)
            masks[role]=native_interval_mask(points,[(start+a,start+b) for a,b in segments])
        for role in ('KEEP_M','RESET_M'):
            v=next(x for x in validated if x['uid']==uid and x['role']==role)
            output=read(bound(v['output_ref']))
            segments=parse_summary(output['raw_text'],end-start)
            masks[role]=native_interval_mask(points,[(start+a,start+b) for a,b in segments])
        assert all(not bool((mask&~domain).any()) for mask in masks.values())
        ms={role:metric(mask[domain],labels[domain]) for role,mask in masks.items()}
        differences={role:dict(added_from_final20=int((masks[role]&~masks['FINAL20']).sum()),
                               removed_from_final20=int((masks['FINAL20']&~masks[role]).sum()),
                               identical_to_final20=bool(np.array_equal(masks[role],masks['FINAL20'])))
                     for role in ('KEEP_M','RESET_M')}
        source_results.append(dict(uid=uid,sid=row['sid'],local_domain_frames=int(domain.sum()),
                                   metrics=ms,difference=differences,human_data_ref=data_ref))
    assert len(source_results)==4
    roles=('BASELINE40_47','ORIGINAL_TIME','FINAL20','KEEP_M','RESET_M')
    macro={role:{k:sum(x['metrics'][role][k] for x in source_results)/4
                 for k in ('precision','recall','f1','native_frame_coverage')} for role in roles}
    probability_aggregate={domain:dict(samples=sum(x['domain']==domain for x in probs),
        mean_RESET_minus_KEEP_logodds=float(np.mean([x['RESET_minus_KEEP_logodds'] for x in probs if x['domain']==domain])),
        RESET_greater_than_KEEP=sum(x['RESET_minus_KEEP_logodds']>0 for x in probs if x['domain']==domain))
        for domain in ('training','development')}
    result=dict(status='COMPLETE_FIXED_ONE_STEP_MOMENTUM_CONTROL_NOT_PROMOTION',
        first_output_QA_ref=ref(root/'first_output_QA39.json'),macro=macro,sources=source_results,
        probability_aggregate=probability_aggregate,probability_details=probs,
        local_windows_only_not_whole_source=True,historical_exposure=True,blind_test=False,
        official_joint_score=None,new_candidate_optimizer_steps=2,additional_GPU_updates=0,
        new_probability_forwards=32,new_free_generations=8,no_new_media_or_processor=True,
        baseline40_47_unchanged=True,automatic_production=False,
        no_extra_steps_threshold_or_learning_rate_search=True)
    save(root/'comparison39.json',result)
    print(json.dumps(dict(status=result['status'],macro=macro,probability_aggregate=probability_aggregate,
        source_changes=[dict(uid=x['uid'],difference=x['difference']) for x in source_results],
        charged_seconds=resource['charged_seconds'],peak_gpu_mib=resource['sampled_peak_memory_mib'],
        result_ref=ref(root/'comparison39.json')),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
