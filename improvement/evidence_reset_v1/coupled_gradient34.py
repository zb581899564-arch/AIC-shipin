"""One first source-program gradient audit; no update, generation or production."""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import traceback


def ref(path):
    p=Path(path).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


def context(root):
    n=Path(root).resolve(strict=True);r=n.parent;w=r.parent
    reg=json.loads((n/'registration34.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(rr):
        p=Path(rr['path']).resolve(strict=True);assert p.is_relative_to(w) and ref(p)==rr
        return json.loads(p.read_text())
    protocol=read(reg['protocol_ref'])
    p31=Path(reg['completion31_ref']['path']).parent
    assert ref(p31/'baseline_scores31.py')==reg['prior_context_code_ref']
    sys.path.insert(0,str(p31))
    from baseline_scores31 import context as context31
    _,_,_,_,_,collection,manifest,Store,_=context31(p31)
    return n,r,w,reg,protocol,collection,manifest,Store,read


def prepare(root):
    n,r,w,reg,p,collection,manifest,Store,read=context(root)
    started=time.monotonic();done32=read(reg['completion32_ref']);done33=read(reg['completion33_ref'])
    assert done32['new_model_calls']==done33['new_model_calls']==0
    assert done33['summary']['fit']['strict_reversals']==4 and done33['summary']['process']['strict_reversals']==5
    root31=Path(reg['completion31_ref']['path']).parent
    sources=[];fit_losses=[]
    for rr in done32['outputs']:
        result=read(rr)
        if result['arm']!='real':continue
        target=read(result['target_ref']);role=target['cohort'];sid=target['sid']
        assert sid in p[role+'_sources']
        def variant(group,uid):
            candidates=[]
            for v in group['variants']:
                if v['kind']=='OLD_ACCEPTED_SUFFIX':
                    old=read(v['window_ref']);slot=old['slots'][v['slot']]
                    assert old['labels_read'] is False and slot['status']=='ACCEPTED'
                    assert slot['real']['logprob']==v['original_real_logp'] and slot['permuted']['logprob']==v['original_shifted_logp']
                    candidates.append(dict(suffix=slot['ids'],cached=dict(real=slot['real']['logprob'],shifted=slot['permuted']['logprob']),proof=v))
                else:
                    assert v['kind']=='NEW_EXACT_BASELINE_NOOP'
                    old=read(v['source_noop_ref']);row=next(a for a in old['windows']if a['uid']==uid)
                    score_ref=ref(root31/(uid+'_scores31.json'));score=read(score_ref)
                    assert score['suffix']==row['suffix'] and row['status']=='PASS_EXACT_BASELINE_NOOP_NATIVE_TOKEN_GRAMMAR'
                    candidates.append(dict(suffix=row['suffix'],cached=dict(real=score['real'],shifted=score['shifted']),proof=dict(noop=v,score_ref=score_ref)))
            return max(candidates,key=lambda a:a['cached']['real'])
        cases=[]
        for window,mi,gi in zip(target['windows'],result['MAP']['choices'],result['highest_score_acceptable']['choices']):
            if mi==gi:continue
            uid=window['uid'];req=read(window['request_ref']);old=read(collection['window_refs'][uid])
            assert req['sid']==sid and req['source_sha256']==target['source_sha256']
            assert old['input_signature']==req['input_signature'] and old['labels_read'] is False
            branches={'gold':variant(window['groups'][gi],uid),'MAP':variant(window['groups'][mi],uid)}
            assert branches['gold']['suffix']!=branches['MAP']['suffix']
            assert all(0<len(b['suffix'])<=512 for b in branches.values())
            cases.append(dict(uid=uid,sid=sid,role=role,request_ref=window['request_ref'],
                input_signature=req['input_signature'],counterfactual_input_signature=old['counterfactual_input_signature'],branches=branches))
        sources.append(dict(sid=sid,role=role,cases=cases))
        if role=='fit':fit_losses.append(result['loss'])
    assert len(sources)==7 and len(fit_losses)==4
    counts={role:sum(len(s['cases'])for s in sources if s['role']==role)for role in ['fit','process']}
    assert counts==dict(fit=17,process=17)
    path=n/'cases34.json';save(path,dict(sources=sources,model_prefix_has_supervision=False,process_never_in_fit=True))
    save(n/'input_acceptance34.json',dict(status='PASS_ADOPTED_NATIVE_INPUT_AND_TARGET_VARIANT_METADATA34',cases_ref=ref(path),
        pair_counts=counts,logical_fit_derivatives=34,logical_process_derivatives=68,maximum_logical_derivatives=102,
        fit_sources=p['fit_sources'],process_sources=p['process_sources'],forced_B_source='S23',
        fit_mean_frozen_active_hinge_loss=math.fsum(fit_losses)/4,
        old_input_token_native_QA_adopted=True,new_decode=0,new_encode=0,new_tokenization=0,automatic_GPU=False,seconds=time.monotonic()-started))
    print(json.dumps(dict(acceptance_ref=ref(n/'input_acceptance34.json'),acceptance=json.loads((n/'input_acceptance34.json').read_text()))))


def gpu(root):
    import numpy as np
    from coupled_gradient34_math import bounded_dot,decide
    n,r,w,reg,p,collection,manifest,Store,read=context(root)
    admission=json.loads((n/'gpu_admission34.json').read_text());assert admission['approved'] and admission['code_ref']==ref(__file__)
    acceptance=read(admission['acceptance_ref']);cases=read(acceptance['cases_ref'])
    sys.path.insert(0,str(w/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from improvement.native_preference_v1.runtime import QwenPreferenceRuntime,freeze_except,canonical_frozen_hash,tensor_signature
    from improvement.content_choice_v1.runtime import permute_visual
    from safetensors.torch import save as tensor_bytes,load as tensor_load
    import torch
    start=time.monotonic()
    def event(kind,payload):
        with(n/'events34.jsonl').open('a')as f:
            f.write(json.dumps(dict(kind=kind,elapsed=time.monotonic()-start,**payload),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def budget(forward=False):assert time.monotonic()-start<p['maximum_GPU_seconds']
    runtime=QwenPreferenceRuntime(manifest['model_spec'],check_budget=budget,on_event=event);runtime.load()
    original=runtime._adapter_state();names=list(runtime._policy_names);parameters=list(runtime._policy_parameters)
    assert len(original)==len(names)==288
    assert all(torch.equal(q.detach().cpu().view(torch.uint8),original[k.replace('.policy.weight','.weight')].view(torch.uint8)) for k,q in zip(names,parameters))
    freeze_except(runtime.model,names);runtime.training=True;runtime.mode='coupled_gradient34'
    runtime.model.train();runtime._disable_dropout();runtime.model.config.use_cache=False;runtime.native.config.text_config.use_cache=False
    for name,module in runtime.model.named_modules():
        if name.endswith('.visual'):module.eval()
    runtime.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});runtime._inventory(True)
    store=Store(manifest,'train');cache={};logical=0;adopted=0
    def zero():return {key:np.zeros(q.shape,dtype=np.float64)for key,q in zip(names,parameters)}
    def digest(arrays):
        h=hashlib.sha256()
        for key in names:h.update(key.encode());h.update(np.asarray(arrays[key]).tobytes())
        return h.hexdigest()
    def derivative(case,arm,label,values):
        nonlocal logical,adopted
        logical+=1;branch=case['branches'][label]
        signature=tensor_signature(torch,values)
        assert signature==case['input_signature'if arm=='real'else'counterfactual_input_signature']
        key=(json.dumps(signature,sort_keys=True),tuple(branch['suffix']))
        if key in cache:
            item=cache[key];assert item['lp']==branch['cached'][arm];adopted+=1
            event('ADOPTED_IDENTICAL_SAME_THETA_RAM_DERIVATIVE',dict(uid=case['uid'],arm=arm,label=label,gradient_sha256=item['sha256']))
            return item['grad']
        budget();runtime.model.zero_grad(set_to_none=True)
        event('BEGIN_FIRST_PROGRAM_DERIVATIVE34',dict(sid=case['sid'],role=case['role'],uid=case['uid'],arm=arm,label=label))
        lp=runtime._sum_logprob(values,branch['suffix'],gradient=True);value=float(lp.detach().cpu())
        event('FIRST_DERIVATIVE_LP_RAW',dict(uid=case['uid'],arm=arm,label=label,logprob=value,cached=branch['cached'][arm]))
        assert value==branch['cached'][arm],'Fresh derivative score identity mismatch; no active-identity assumption or relaxation'
        runtime.counts['backward_calls']+=1;lp.backward();runtime.counts['backwards_completed']+=1
        grads={}
        for name,q in zip(names,parameters):
            assert q.grad is not None and q.grad.dtype==torch.float32 and bool(torch.isfinite(q.grad).all())
            grads[name]=q.grad.detach().cpu().numpy().copy()
        assert bounded_dot(grads,grads)['lower']>0
        item=dict(grad=grads,lp=value,sha256=digest(grads));cache[key]=item
        event('FIRST_DERIVATIVE_ACCEPTED_RAM34',dict(uid=case['uid'],arm=arm,label=label,gradient_sha256=item['sha256']))
        del lp;runtime.model.zero_grad(set_to_none=True);return grads
    def source_gradient(source,arm):
        result=zero()
        for case in source['cases']:
            req,values,_=store.case(case['uid']);assert req['input_signature']==case['input_signature']
            if arm=='shifted':values=permute_visual(values)
            runtime._values(values)
            for label,sign in [('gold',1.),('MAP',-1.)]:
                gradient=derivative(case,arm,label,values)
                for name in names:result[name]+=sign*gradient[name].astype(np.float64)
        return result
    aggregate=zero();fit_reports=[]
    for source in cases['sources']:
        if source['role']!='fit':continue
        part=source_gradient(source,'real')
        for key in names:aggregate[key]+=part[key]/4
        fit_reports.append(dict(sid=source['sid'],norm2=bounded_dot(part,part),gradient_sha256=digest(part),pairs=len(source['cases'])))
        del part
    assert logical==34
    direction={key:np.asarray(value,dtype=np.float32)for key,value in aggregate.items()}
    raw=tensor_bytes({key:torch.from_numpy(value)for key,value in direction.items()},metadata={'purpose':'rounded_four_source_program_direction34','dtype':'float32'})
    compressed=gzip.compress(raw,compresslevel=6,mtime=0);assert len(compressed)<63000000
    assert sum(q.stat().st_size for q in n.rglob('*')if q.is_file())+len(compressed)+1000000<p['maximum_output_bytes']
    assert shutil.disk_usage(n).free>len(compressed)+1000000
    path=n/'direction34.safetensors.gz'
    with path.open('xb')as f:f.write(compressed)
    loaded=tensor_load(gzip.decompress(path.read_bytes()))
    assert set(loaded)==set(direction) and all(torch.equal(loaded[k].view(torch.uint8),torch.from_numpy(direction[k]).view(torch.uint8))for k in direction)
    direction={k:v.numpy()for k,v in loaded.items()}
    direction_norm=bounded_dot(direction,direction)
    round_error={k:aggregate[k]-direction[k].astype(np.float64)for k in names}
    fit_summary=dict(source_reports=fit_reports,aggregate64_norm2=bounded_dot(aggregate,aggregate),stored_direction_norm2=direction_norm,
        aggregate64_dot_stored=bounded_dot(aggregate,direction),rounding_error_norm2=bounded_dot(round_error,round_error),
        artifact_ref=ref(path),raw_uncompressed_bytes=len(raw),compressed_bytes=len(compressed),stored_direction_FP32_byte_QA=True)
    save(n/'fit_direction34.json',fit_summary);del raw,compressed,aggregate,round_error,loaded
    process=[]
    if direction_norm['lower']>0:
        for source in cases['sources']:
            if source['role']!='process':continue
            real=source_gradient(source,'real');shifted=source_gradient(source,'shifted')
            stats=dict(real_norm2=bounded_dot(real,real),shifted_norm2=bounded_dot(shifted,shifted),direction_norm2=direction_norm,
                real_dot=bounded_dot(real,direction),shifted_dot=bounded_dot(shifted,direction),real_shifted_dot=bounded_dot(real,shifted))
            record=dict(sid=source['sid'],stats=stats,real_gradient_sha256=digest(real),shifted_gradient_sha256=digest(shifted),pairs=len(source['cases']))
            save(n/(source['sid']+'_process_stats34.json'),record);process.append(record);del real,shifted
        decision=decide(process,p['minimum_scale_removed_projection']);assert logical==102
    else:
        decision=dict(status='STOP_ZERO_OR_NUMERICALLY_AMBIGUOUS_FIT_DIRECTION',automatic_update=False,production_admitted=False)
    store.close();runtime.model.zero_grad(set_to_none=True);runtime._inference_mode();runtime._inventory(False)
    actual=runtime._adapter_state();assert all(torch.equal(actual[k].view(torch.uint8),original[k].view(torch.uint8))for k in original)
    base_after=canonical_frozen_hash(runtime.model,torch);assert base_after==runtime.base_before;runtime._original_files()
    assert runtime.counts['optimizer_steps']==runtime.counts['generation_calls']==0
    assert runtime.counts['top_level_forward_calls']==runtime.counts['sequence_scores_completed']==runtime.counts['backward_calls']==runtime.counts['backwards_completed']
    assert runtime.counts['top_level_forward_calls']+adopted==logical<=102
    save(n/'gpu_completion34.json',dict(status=decision['status'],decision=decision,process=process,fit=fit_summary,
        counts=dict(runtime.counts),logical_derivatives=logical,adopted_identical_derivatives=adopted,
        actual_updates=0,actual_generations=0,original288TIME_frozen=True,base_before=runtime.base_before,base_after=base_after,
        all_fresh_derivative_scores_exactly_match_cached=True,seconds=time.monotonic()-start,
        process_not_in_fit=True,automatic_update=False,production_admitted=False,new_ZIP=0,official_submissions=0))


def review(root):
    import numpy as np
    import torch
    from safetensors.torch import load
    from coupled_gradient34_math import bounded_dot,decide
    n,r,w,reg,p,c,m,Store,read=context(root);result=read(ref(n/'gpu_completion34.json'));fit=read(ref(n/'fit_direction34.json'))
    direction={k:v.numpy()for k,v in load(gzip.decompress(Path(fit['artifact_ref']['path']).read_bytes())).items()}
    assert ref(fit['artifact_ref']['path'])==fit['artifact_ref'] and len(direction)==288
    assert all(v.dtype==np.float32 and np.isfinite(v).all()for v in direction.values())
    assert sum(v.size for v in direction.values())==15335424
    norm=bounded_dot(direction,direction)
    for key in ['value','radius','lower','upper']:
        assert math.isclose(norm[key],fit['stored_direction_norm2'][key],rel_tol=1e-12,abs_tol=1e-12)
    decision=decide(result['process'],p['minimum_scale_removed_projection'])if result['process']else dict(status='STOP_ZERO_OR_NUMERICALLY_AMBIGUOUS_FIT_DIRECTION',automatic_update=False,production_admitted=False)
    assert decision==result['decision']
    assert result['original288TIME_frozen']and result['base_before']==result['base_after']
    assert result['actual_updates']==result['actual_generations']==0 and result['process_not_in_fit']
    assert result['counts']['top_level_forward_calls']+result['adopted_identical_derivatives']==result['logical_derivatives']
    baseline=ref(w/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    save(n/'review34.json',dict(status=decision['status'],decision=decision,fit=fit,process=result['process'],
        independent_QA='PASS_PERSISTED_FP32_DIRECTION_AND_SUFFICIENT_STAT_ARITHMETIC_NOT_REPEATED_BRANCH_AUTOGRAD',
        per_branch_QA='Live finite288/hash/norm inRAM; not persisted per-branch tensors or independent repeated backward.',
        protected_baseline_ref=baseline,actual_updates=0,automatic_update=False,production_admitted=False,new_ZIP=0,official_submissions=0))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','gpu','review'],required=True);ap.add_argument('--run-root',required=True);args=ap.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'34.json'),dict(status='ACTUAL_FAILURE_PRESERVE_NO_AUTOMATIC_REPLAY',traceback=traceback.format_exc()));raise
