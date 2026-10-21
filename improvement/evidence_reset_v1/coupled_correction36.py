"""One fixed fit-only correction; recipe checkpoint and complete same-pool MAP."""
import argparse,gzip,hashlib,json,math,os
from pathlib import Path
import sys,time,traceback
from metadata_json35 import native


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(p,v):
    with Path(p).open('x')as f:json.dump(native(v),f,indent=2,allow_nan=False)


def context(root):
    n=Path(root).resolve(strict=True);r=n.parent;w=r.parent
    reg=json.loads((n/'registration36.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(rr):
        p=Path(rr['path']).resolve(strict=True);assert p.is_relative_to(w)and ref(p)==rr
        return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);p31=Path(reg['completion31_ref']['path']).parent
    assert ref(p31/'baseline_scores31.py')==reg['prior_context_code_ref']
    sys.path.insert(0,str(p31));from baseline_scores31 import context as context31
    _,_,_,_,_,coll,manifest,Store,_=context31(p31)
    return n,r,w,reg,protocol,coll,manifest,Store,read


def prepare(root):
    from policy_recipe36_math import rate
    n,r,w,reg,p,coll,manifest,Store,read=context(root);started=time.monotonic()
    recovered=read(reg['recovery35_ref']);assert recovered['status']=='ELIGIBLE_FOR_SEPARATE_ONE_STEP_REVIEW_ONLY'
    assert all(recovered['decision']['conditions'].values())and recovered['scientific_thresholds_unchanged']
    done32=read(reg['completion32_ref']);fit=recovered['fit'];read35=Path(reg['recovery35_ref']['path']).parent
    accept34=read(ref(read35.parent/'coupled_gradient34/input_acceptance34.json'))
    L0=accept34['fit_mean_frozen_active_hinge_loss'];D=fit['aggregate64_dot_stored'];assert D['lower']>0
    alpha=rate(L0,D['value'])
    save(n/'recipe36.json',dict(schema='AIC_LOSSLESS_TIME_DELTA_RECIPE36',original_weights_ref=manifest['model_spec']['adapter_weights'],
        original_config_ref=manifest['model_spec']['adapter_config'],direction_ref=fit['artifact_ref'],alpha_hex=alpha.hex(),
        algorithm='NumPyCPU_FP64MultiplyThenFP64AddThenRoundFP32_noFMA',fit_active_loss=L0,fit_directional_derivative=D,
        basis_recovery_ref=reg['recovery35_ref'],policy_rank=16,alpha_lora=32,
        conservative_pipeline_parameters=8797892873,physical_candidate_parameters=8782459120,
        method='One fixed active-plane correction; no process-chosen dose or optimizer sweep. Materialization/reload is deterministic, not extra optimization.'))
    p31=Path(reg['completion31_ref']['path']).parent
    target_rows=[];cases={};logical=0
    for rr in done32['outputs']:
        inference=read(rr)
        if inference['arm']!='real':continue
        target=read(inference['target_ref']);windows=[]
        source_domain=set()
        for i,window in enumerate(target['windows']):
            uid=window['uid'];req=read(window['request_ref']);old=read(coll['window_refs'][uid])
            assert req['sid']==target['sid']and req['source_sha256']==target['source_sha256']
            assert old['input_signature']==req['input_signature']and old['labels_read']is False
            suffixes=[];index={};oldlog=dict(real=[],shifted=[]);groups=[]
            for group in window['groups']:
                frame_set=None;ii=[]
                for variant in group['variants']:
                    if variant['kind']=='OLD_ACCEPTED_SUFFIX':
                        slot=read(variant['window_ref'])['slots'][variant['slot']]
                        assert slot['status']=='ACCEPTED'
                        ids=slot['ids'];selected=slot['selected_ordinals']
                        lp=dict(real=variant['original_real_logp'],shifted=variant['original_shifted_logp'])
                        assert lp==dict(real=slot['real']['logprob'],shifted=slot['permuted']['logprob'])
                    else:
                        assert variant['kind']=='NEW_EXACT_BASELINE_NOOP'
                        noop=read(variant['source_noop_ref']);row=next(a for a in noop['windows']if a['uid']==uid)
                        score=read(ref(p31/(uid+'_scores31.json')))
                        assert score['suffix']==row['suffix'];ids=row['suffix'];selected=row['selected_ordinals'];lp={a:score[a]for a in ['real','shifted']}
                    current=set(selected);assert len(current)==len(selected)==group['native_count']
                    if frame_set is None:frame_set=current
                    assert current==frame_set
                    key=tuple(ids)
                    if key not in index:
                        index[key]=len(suffixes);suffixes.append(ids)
                        for arm in oldlog:oldlog[arm].append(lp[arm])
                    j=index[key]
                    assert all(oldlog[arm][j]==lp[arm]for arm in oldlog);ii.append(j)
                groups.append(dict(suffix_indices=ii,native_count=group['native_count'],TP=group['TP'],selected_ordinals=sorted(frame_set)))
            domain=set().union(*(set(g['selected_ordinals'])for g in groups))
            assert not(source_domain&domain),'Native window ownership must be disjoint before summing TP'
            source_domain|=domain
            mi=inference['MAP']['choices'][i];gi=inference['highest_score_acceptable']['choices'][i]
            original_max=lambda j:max(groups[j]['suffix_indices'],key=lambda k:oldlog['real'][k])
            windows.append(dict(uid=uid,groups=groups,baseline_group=window['baseline_group'],old_MAP_group=mi,old_gold_group=gi,
                frozen_active_MAP_suffix=original_max(mi),frozen_active_gold_suffix=original_max(gi),original_logprobs=oldlog))
            cases[uid]=dict(uid=uid,sid=target['sid'],role=target['cohort'],request_ref=window['request_ref'],
                input_signature=req['input_signature'],counterfactual_input_signature=old['counterfactual_input_signature'],suffixes=suffixes)
            logical+=2*len(suffixes)
        target_rows.append(dict(sid=target['sid'],role=target['cohort'],source_ref=inference['target_ref'],gt=target['gt'],
            baseline_F1=target['baseline_F1'],baseline_frames=target['baseline_frames'],windows=windows))
    assert len(target_rows)==7 and len(cases)==37 and 0<logical<=p['maximum_logical_scores']
    save(n/'score_cases36.json',cases);save(n/'targets36.json',dict(sources=target_rows,forced_B='S23',source_partition=dict(fit=p['fit_sources'],process=p['process_sources'])))
    save(n/'input_acceptance36.json',dict(status='PASS_ADOPTED_FULL_NATIVE_POOL_AND_LOSSLESS_RECIPE_METADATA36',
        cases_ref=ref(n/'score_cases36.json'),targets_ref=ref(n/'targets36.json'),recipe_ref=ref(n/'recipe36.json'),
        sources_supported=7,forced_B_source='S23',windows=37,logical_scores=logical,maximum_actual_forwards=logical,
        fixed_fit_alpha=alpha,alpha_hex=alpha.hex(),old_token_native_input_QA_adopted=True,
        new_decode=0,new_encode=0,new_tokenization=0,actual_policy_updates_so_far=0,automatic_GPU=False,seconds=time.monotonic()-started))
    print(json.dumps(native(dict(acceptance_ref=ref(n/'input_acceptance36.json'),acceptance=read(ref(n/'input_acceptance36.json'))))))


def gpu(root):
    import numpy as np
    import torch
    from safetensors.torch import load_file,load
    from policy_recipe36_math import materialize,state_digest
    n,r,w,reg,p,coll,manifest,Store,read=context(root)
    admission=json.loads((n/'gpu_admission36.json').read_text());assert admission['approved']and admission['code_ref']==ref(__file__)
    accepted=read(admission['acceptance_ref']);recipe=read(accepted['recipe_ref']);cases=read(accepted['cases_ref'])
    sys.path.insert(0,str(w/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from improvement.native_preference_v1.runtime import QwenPreferenceRuntime,canonical_frozen_hash,tensor_signature
    from improvement.content_choice_v1.runtime import permute_visual
    start=time.monotonic()
    def event(kind,payload):
        with(n/'events36.jsonl').open('a')as f:f.write(json.dumps(native(dict(kind=kind,elapsed=time.monotonic()-start,**payload)),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def budget(forward=False):assert time.monotonic()-start<p['maximum_GPU_seconds']
    runtime=QwenPreferenceRuntime(manifest['model_spec'],check_budget=budget,on_event=event);runtime.load()
    original=runtime._adapter_state();assert recipe['original_weights_ref']==manifest['model_spec']['adapter_weights']
    original_disk=load_file(str(Path(recipe['original_weights_ref']['path'])));assert ref(recipe['original_weights_ref']['path'])==recipe['original_weights_ref']
    assert all(torch.equal(v.view(torch.uint8),original_disk[k].view(torch.uint8))for k,v in original.items())
    assert ref(recipe['direction_ref']['path'])==recipe['direction_ref']
    direction={k:v.numpy()for k,v in load(gzip.decompress(Path(recipe['direction_ref']['path']).read_bytes())).items()}
    base_arrays={k:v.numpy()for k,v in original.items()}
    candidate,step=materialize(base_arrays,direction,recipe['alpha_hex'])
    state={k:torch.from_numpy(a)for k,a in candidate.items()}
    runtime._restore_fp32(state);runtime.counts['optimizer_steps']+=1
    event('ACTUAL_SINGLE_FIT_DERIVED_PARAMETER_UPDATE36',dict(step=step,optimization_updates=1))
    save(n/'materialized_policy36.json',dict(recipe_ref=accepted['recipe_ref'],step=step,canonical_state_sha256=state_digest(candidate),
        tensors={k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes()).hexdigest())for k,v in candidate.items()},
        checkpoint_format='Lossless recipe plus SHA-bound originalTIME and stored direction, not an unpersisted standalone safetensors claim.'))
    # Reload the persisted recipe/dependency, reset actual adapter, then rebuild.
    reloaded=read(accepted['recipe_ref']);direction2={k:v.numpy()for k,v in load(gzip.decompress(Path(reloaded['direction_ref']['path']).read_bytes())).items()}
    rebuilt,step2=materialize({k:v.numpy()for k,v in original_disk.items()},direction2,reloaded['alpha_hex'])
    assert step==step2 and all(np.array_equal(v.view(np.uint8),rebuilt[k].view(np.uint8))for k,v in candidate.items())
    runtime._restore_fp32(original);runtime._restore_fp32({k:torch.from_numpy(v)for k,v in rebuilt.items()})
    actual=runtime._adapter_state();assert all(torch.equal(actual[k].view(torch.uint8),torch.from_numpy(v).view(torch.uint8))for k,v in rebuilt.items())
    event('RECIPE_SAVE_RECONSTRUCTION_ACTUAL_MODULE_BYTES_PASS36',dict(matrices=288,recipe_materializations=2,optimization_updates=1,parameter_assignment_events=3))
    store=Store(manifest,'train');cache={};adopted=0;refs=[]
    for uid,case in cases.items():
        assert set(case)=={'uid','sid','role','request_ref','input_signature','counterfactual_input_signature','suffixes'}
        req,values,_=store.case(uid);assert req['input_signature']==case['input_signature']
        moved=permute_visual(values);assert tensor_signature(torch,moved)==case['counterfactual_input_signature']
        raw=dict(uid=uid,sid=case['sid'],role=case['role'],input_signature=case['input_signature'],counterfactual_input_signature=case['counterfactual_input_signature'],suffixes=case['suffixes'],scores={})
        for arm,inp in [('real',values),('shifted',moved)]:
            values_out=[];signature=tensor_signature(torch,inp)
            for j,suffix in enumerate(case['suffixes']):
                key=(json.dumps(signature,sort_keys=True),tuple(suffix));event('BEGIN_FIRST_FIXED_POLICY_SUFFIX_SCORE36',dict(uid=uid,arm=arm,suffix_index=j))
                if key in cache:value=cache[key];adopted+=1;event('ADOPTED_IDENTICAL_FIXED_POLICY_SCORE36',dict(uid=uid,arm=arm,suffix_index=j,logprob=value))
                else:
                    value=runtime.score(inp,suffix);cache[key]=value
                    event('FIXED_POLICY_SCORE_ACCEPTED36',dict(uid=uid,arm=arm,suffix_index=j,logprob=value))
                assert math.isfinite(value);values_out.append(value)
            raw['scores'][arm]=values_out
        path=n/(uid+'_scores36.json');save(path,raw);refs.append(ref(path))
    store.close();after=runtime._adapter_state()
    assert all(torch.equal(after[k].view(torch.uint8),torch.from_numpy(v).view(torch.uint8))for k,v in candidate.items())
    base_after=canonical_frozen_hash(runtime.model,torch);assert base_after==runtime.base_before;runtime._original_files();runtime._inventory(False)
    assert runtime.counts['optimizer_steps']==1 and runtime.counts['backward_calls']==runtime.counts['generation_calls']==0
    assert runtime.counts['top_level_forward_calls']==runtime.counts['sequence_scores_completed']
    assert runtime.counts['top_level_forward_calls']+adopted==accepted['logical_scores']
    save(n/'gpu_completion36.json',dict(status='ENGINEERING_COMPLETE_ONE_FIXED_RECIPE_CORRECTION_ALL_POOL_SCORES36',
        score_refs=refs,step=step,materialized_policy_ref=ref(n/'materialized_policy36.json'),recipe_ref=accepted['recipe_ref'],
        counts=dict(runtime.counts),actual_update=1,recipe_materializations=2,parameter_assignment_events=3,
        actual_forwards=runtime.counts['top_level_forward_calls'],adopted_identical_scores=adopted,logical_scores=accepted['logical_scores'],
        base_before=runtime.base_before,base_after=base_after,candidate288_recipe_load_and_after_bytes_exact=True,
        original_TIME_files_unchanged=True,seconds=time.monotonic()-start,automatic_more_updates=False,production_admitted=False,new_ZIP=0,official_submissions=0))


def review(root):
    import numpy as np
    from policy_recipe36_math import materialize,state_digest
    import torch
    from safetensors.torch import load,load_file
    n,r,w,reg,p,coll,manifest,Store,read=context(root)
    a=read(ref(n/'input_acceptance36.json'));targets=read(a['targets_ref']);cases=read(a['cases_ref']);done=read(ref(n/'gpu_completion36.json'))
    assert done['actual_update']==1 and done['base_before']==done['base_after']and done['candidate288_recipe_load_and_after_bytes_exact']
    recipe=read(a['recipe_ref']);orig={k:v.numpy()for k,v in load_file(str(Path(recipe['original_weights_ref']['path']))).items()}
    assert ref(recipe['original_weights_ref']['path'])==recipe['original_weights_ref']and ref(recipe['direction_ref']['path'])==recipe['direction_ref']
    direction={k:v.numpy()for k,v in load(gzip.decompress(Path(recipe['direction_ref']['path']).read_bytes())).items()}
    candidate,step=materialize(orig,direction,recipe['alpha_hex']);assert step==done['step']
    policy=read(done['materialized_policy_ref']);assert state_digest(candidate)==policy['canonical_state_sha256']
    assert all(hashlib.sha256(v.tobytes()).hexdigest()==policy['tensors'][k]['sha256']for k,v in candidate.items())
    original31=read(reg['completion31_ref']);oldreview=read(original31['review_ref']);old_by_sid={q['sid']:q for q in oldreview['rows']}
    root32=Path(reg['completion32_ref']['path']).parent
    assert ref(root32/'acceptable_program32_math.py')==reg['native_math_ref']
    sys.path.insert(0,str(root32));from acceptable_program32_math import exact_utility
    p31=Path(reg['completion31_ref']['path']).parent;assert ref(p31/'baseline_scores31.py')==reg['prior_context_code_ref']
    from baseline_scores31 import choose_native_group
    scores={v['uid']:v for rr in done['score_refs']for v in [read(rr)]};assert set(scores)==set(cases)
    rows=[]
    for source in targets['sources']:
        B=set().union(*(set(win['groups'][win['baseline_group']]['selected_ordinals'])for win in source['windows']))
        assert len(B)==source['baseline_frames'];arms={}
        for arm in ['real','shifted']:
            selected=set();control=set();tp=np.zeros(len(source['gt']),dtype=np.int64);oldtp=tp.copy();choices=[];fixed_new=0.;fixed_old=0.;count=0;oldcount=0
            for win in source['windows']:
                uid=win['uid'];raw=scores[uid];case=cases[uid]
                assert raw['suffixes']==case['suffixes']and raw['input_signature']==case['input_signature']and raw['counterfactual_input_signature']==case['counterfactual_input_signature']
                aa=[set(g['selected_ordinals'])for g in win['groups']]
                ll=[max(raw['scores'][arm][j]for j in g['suffix_indices'])for g in win['groups']]
                oo=[max(win['original_logprobs'][arm][j]for j in g['suffix_indices'])for g in win['groups']]
                j=choose_native_group(aa,ll,B);k=choose_native_group(aa,oo,B)
                selected|=aa[j];control|=aa[k];tp+=np.asarray(win['groups'][j]['TP']);oldtp+=np.asarray(win['groups'][k]['TP']);choices.append(j)
                count+=win['groups'][j]['native_count'];oldcount+=win['groups'][k]['native_count']
                g,m=win['frozen_active_gold_suffix'],win['frozen_active_MAP_suffix']
                fixed_new+=raw['scores'][arm][g]-raw['scores'][arm][m]
                fixed_old+=win['original_logprobs'][arm][g]-win['original_logprobs'][arm][m]
            assert count==len(selected)and oldcount==len(control)
            F=float(exact_utility(len(selected),tp,source['gt']));oldF=float(exact_utility(len(control),oldtp,source['gt']))
            assert abs(oldF-old_by_sid[source['sid']]['arms'][arm]['F1'])<1e-12
            arms[arm]=dict(F1=F,original_TIME_F1=oldF,delta_vs_original=F-oldF,delta_vs_B=F-source['baseline_F1'],
                selected_frames=len(selected),added_vs_B=len(selected-B),deleted_vs_B=len(B-selected),changed_vs_original=len(selected^control),
                successful_empty=len(selected)==0,chosen_native_groups=choices,fixed_active_pair_margin_before=fixed_old,
                fixed_active_pair_margin_after=fixed_new,actual_fixed_pair_margin_gain=fixed_new-fixed_old)
        rows.append(dict(sid=source['sid'],role=source['role'],forced_B=False,baseline_F1=source['baseline_F1'],arms=arms))
    baseline23=old_by_sid['S23']['baseline_F1']
    rows.append(dict(sid='S23',role='process',forced_B=True,baseline_F1=baseline23,arms={arm:dict(F1=baseline23,original_TIME_F1=baseline23,delta_vs_original=0.,delta_vs_B=0.,changed_vs_original=0)for arm in ['real','shifted']}))
    macro={}
    for role in ['fit','process']:
        rr=[q for q in rows if q['role']==role];assert len(rr)==4
        macro[role]=dict(baseline_F1=math.fsum(q['baseline_F1']for q in rr)/4,
            arms={arm:dict(F1=math.fsum(q['arms'][arm]['F1']for q in rr)/4,original_TIME_F1=math.fsum(q['arms'][arm]['original_TIME_F1']for q in rr)/4,
                gain=math.fsum(q['arms'][arm]['delta_vs_original']for q in rr)/4,
                improved_sources=sum(q['arms'][arm]['delta_vs_original']>1e-12 for q in rr),
                changed_sources=sum(q['arms'][arm]['changed_vs_original']>0 for q in rr))for arm in ['real','shifted']})
    proc=macro['process'];real=proc['arms']['real'];shift=proc['arms']['shifted']
    mechanism=real['gain']>1e-12 and real['gain']-shift['gain']>1e-12 and real['improved_sources']>=2
    if not mechanism:status='STOP_FIXED_SINGLE_CORRECTION_ACTUAL_MAP_TRANSFER'
    elif real['F1']<=proc['baseline_F1']+1e-12:status='MECHANISM_GAIN_BUT_BELOW_BASELINE_PROXY_NO_PRODUCTION'
    else:status='ELIGIBLE_FOR_SEPARATE_BROADER_EXTERNAL_REVIEW_ONLY'
    baseline=ref(w/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    save(n/'review36.json',dict(status=status,macro=macro,rows=rows,step=step,recipe_ref=a['recipe_ref'],
        independent_QA='PASS_FULL288_RECIPE_RECONSTRUCTION_AND_FULL_SOURCE_SAME_POOL_MAP36',
        scope='All historical external summary proxy, not officialjointscore/newblind/cross-window architecture.',
        protected_baseline_ref=baseline,actual_updates=1,automatic_more_updates=False,production_admitted=False,new_ZIP=0,official_submissions=0))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','gpu','review'],required=True);ap.add_argument('--run-root',required=True);args=ap.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'36.json'),dict(status='ACTUAL_FAILURE_PRESERVE_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()));raise
