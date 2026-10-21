"""One four-source exact-risk gradient audit, sequential same-theta Jacobians.

No rollout, reference-label inference, test-data interface, optimizer sweep or
automatic production. Old model/runtime/input files remain immutable.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
from unittest.mock import patch


def save(path, value):
    with Path(path).open('x') as f: json.dump(value, f, indent=2, allow_nan=False)


def ref(path):
    p = Path(path).resolve(strict=True); b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def stable_kl(np, before, after):
    a=np.asarray(before,dtype=float); b=np.asarray(after,dtype=float)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all(): raise ValueError('Finite same action logits')
    x=a-a.max(); y=b-b.max()
    log0=x-np.log(np.exp(x).sum()); log1=y-np.log(np.exp(y).sum())
    value=float(np.sum(np.exp(log0)*(log0-log1)))
    if not np.isfinite(value) or value < -1e-12: raise ValueError('Finite nonnegative KL')
    return max(0.,value)


def checked(r, W):
    p = Path(r['path']).resolve(strict=True)
    assert p.is_relative_to(W) and ref(p) == r, 'Bound path/bytes mismatch'
    return p


def readref(r, W): return json.loads(checked(r, W).read_text())


def context(root):
    N = Path(root).resolve(strict=True); R = N.parent; W = R.parent
    a = json.loads((N/'registration20.json').read_text())
    revision = json.loads((N/'source_revision20.json').read_text())
    assert revision['original_registration_ref'] == ref(N/'registration20.json')
    assert revision['code_ref'] == ref(__file__)
    assert revision['original_code_ref'] == a['code_ref']
    protocol = readref(a['protocol_ref'], W)
    assert protocol['training_sources'] == ['S10', 'S07', 'S14', 'S00']
    sys.path.insert(0, a['prior_code_root'])
    from improvement.native_preference_v1 import inputs as inp
    class FastStore(inp.NativeInputStore):
        def _source_pixels(self, sid):
            def once(p, mode='rb', *args, **kwargs):
                assert mode == 'rb'; return io.BytesIO(gzip.decompress(Path(p).read_bytes()))
            with patch.object(inp.gzip, 'open', once): return super()._source_pixels(sid)
    collection = readref(a['collection_ref'], W)
    manifest = readref(collection['asset_manifest_ref'], W)
    return N, R, W, a, protocol, collection, manifest, FastStore


def prepare(root):
    import numpy as np
    N, R, W, a, protocol, collection, manifest, Store = context(root)
    store = Store(manifest, 'train'); completion = readref(a['risk19_ref'], W)
    assert completion['status'] == 'EXACT_SOURCE_RISK_CPU_FEASIBILITY_ONLY_NOT_TRAINING_ADMISSION'
    coeff = {readref(r,W)['source_id']: r for r in completion['training_coefficient_refs']}
    rows = []; total = 0; nbytes = 0; started = time.monotonic()
    for sid in protocol['training_sources']:
        record = readref(coeff[sid], W); assert record['metrics']['hashed_training4']
        h = store.source_supervision(sid); n = len(h['clock']['normalized_exact_pts'])
        assert h['source_sha256'] == record['source_sha256']
        assert all(len(v) == n and all(v) for v in h['known_masks'])
        labels = np.zeros((n, len(h['raters'])), bool)
        for j, truth in enumerate(h['raters']): labels[sorted(truth), j] = True
        windows = []; domains = []
        for w in record['windows']:
            request, v, clock = store.case(w['uid'])
            old = readref(w['window_ref'], W)
            assert old['input_signature'] == request['input_signature'] and old['labels_read'] is False
            slots = [old['slots'][s] for s in w['slots']]
            assert len({tuple(c['ids']) for c in slots}) == len(slots)
            actions = [c['selected_ordinals'] for c in slots]
            assert all(c['status'] == 'ACCEPTED' for c in slots)
            domains.append(set().union(*map(set,actions)))
            windows.append(dict(uid=w['uid'], window_ref=w['window_ref'], request_ref=w['original_request_ref'],
                input_signature=request['input_signature'], slots=w['slots'], suffixes=[c['ids'] for c in slots],
                lengths=list(map(len,actions)), overlap=[labels[c].sum(axis=0,dtype=np.int64).tolist() for c in actions],
                original_logits=w['original_logits'], input_bytes=sum(t.numel()*t.element_size() for t in v.values())))
            total += len(slots); nbytes = max(nbytes, windows[-1]['input_bytes'])
        assert len(set().union(*domains)) == sum(map(len,domains)), 'Disjoint native windows'
        rows.append(dict(sid=sid, source_sha256=h['source_sha256'], source_ref=store.sources[sid]['supervision_ref'],
                         coefficient19_ref=coeff[sid], gt=labels.sum(axis=0,dtype=np.int64).tolist(), windows=windows))
    store.close()
    assert sum(len(s['windows']) for s in rows) == 21 and total == 78
    path=N/'targets20.json'; save(path,dict(sources=rows, labels_in_model_input=False,
        source_equal=True, task='Historical external full-reviewer summary proxy only'))
    save(N/'input_acceptance20.json',dict(status='ADOPTED21_ORIGINAL_INPUTS_FOR_FIRST_SOURCE_RISK_DERIVATIVE',
        original_successful_inputs_not_reprepared=True, target_ref=ref(path), sources=4, windows=21, branches=total,
        maximum_input_bytes=nbytes, maximum_source_jacobian_bytes=max(sum(len(w['slots']) for w in s['windows']) for s in rows)*15335424*4,
        original_288_adapter_parameters=15335424, no_new_decode_or_encode=True, seconds=time.monotonic()-started))


def gpu(root):
    import numpy as np
    from source_risk19 import action_gradient, normalize
    from source_step20_math import combine_jacobians, fixed_step
    N,R,W,a,protocol,collection,manifest,Store=context(root)
    admission=json.loads((N/'gpu_admission20.json').read_text())
    assert admission['approved'] and admission['input_acceptance_ref']==ref(N/'input_acceptance20.json')
    accepted=readref(admission['input_acceptance_ref'],W); targets=readref(accepted['target_ref'],W)
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from improvement.native_preference_v1.runtime import QwenPreferenceRuntime, freeze_except, canonical_frozen_hash
    from safetensors.torch import load_file, save_file
    import torch
    start=time.monotonic(); events=N/'events20.jsonl'
    def event(kind, payload):
        with events.open('a') as f:
            f.write(json.dumps(dict(kind=kind,elapsed=time.monotonic()-start,**payload),allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
    def budget(forward=False):
        assert time.monotonic()-start < protocol['max_GPU_seconds'], 'Fixed stage elapsed'
    runtime=QwenPreferenceRuntime(manifest['model_spec'],check_budget=budget,on_event=event)
    identity=runtime.load(); runtime._inventory(False)
    original=runtime._adapter_state(); store=Store(manifest,'train')
    # Check exact PEFT saved-name mapping BEFORE any new derivative forward.
    named={k:p.detach().cpu() for k,p in runtime.model.named_parameters() if 'lora_' in k}
    assert {k.replace('.policy.weight','.weight') for k in named} == set(original)
    assert all(torch.equal(v.view(torch.uint8),original[k.replace('.policy.weight','.weight')].view(torch.uint8)) for k,v in named.items())
    event('PRE_FORWARD_EXACT_PEFT_KEY_AND_BYTES_PASS',dict(matrices=288))
    del named
    freeze_except(runtime.model,runtime._policy_names); runtime.training=True; runtime.mode='source_risk20'
    runtime.model.train(); runtime._disable_dropout()
    runtime.model.config.use_cache=False; runtime.native.config.text_config.use_cache=False
    for name,m in runtime.model.named_modules():
        if name.endswith('.visual'): m.eval()
    runtime.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    runtime._inventory(True)
    names=list(runtime._policy_names); parameters=list(runtime._policy_parameters)
    initial={k:p.detach().cpu().numpy().copy() for k,p in zip(names,parameters)}
    aggregate={k:np.zeros(p.shape,dtype=np.float64) for k,p in zip(names,parameters)}
    reports=[]; before_calls=0; backward=0
    for source in targets['sources']:
        jacobians=[]; logits=[]; flat=[]
        for w in source['windows']:
            request,values,_=store.case(w['uid']); runtime._values(values); row=[]
            assert request['input_signature']==w['input_signature']
            for j,suffix in enumerate(w['suffixes']):
                budget(); runtime.model.zero_grad(set_to_none=True)
                event('BEGIN_NEW_SAME_THETA_DERIVATIVE',dict(sid=source['sid'],uid=w['uid'],slot=w['slots'][j]))
                lp=runtime._sum_logprob(values,suffix,gradient=True); value=float(lp.detach().cpu()); before_calls+=1
                event('NEW_AUTOGRAD_SCORE_RAW',dict(sid=source['sid'],uid=w['uid'],slot=w['slots'][j],logprob=value,old_logprob=w['original_logits'][j]))
                assert abs(value-w['original_logits'][j]) <= .02, 'Original identity numerical hint exceeded; not an exact-gradient approximation'
                runtime.counts['backward_calls']+=1; lp.backward(); backward+=1; runtime.counts['backwards_completed']+=1
                grads={}
                for key,p in zip(names,parameters):
                    assert p.grad is not None and p.grad.dtype==torch.float32 and bool(torch.isfinite(p.grad).all())
                    grads[key]=p.grad.detach().cpu().numpy().copy()
                assert sum(float(np.sum(v.astype(np.float64)**2)) for v in grads.values())>0
                jacobians.append(grads); row.append(value); flat.append((w['uid'],w['slots'][j]))
                h=hashlib.sha256()
                for key in names: h.update(key.encode()); h.update(grads[key].tobytes())
                event('DERIVATIVE_ACCEPTED_IN_RAM',dict(sid=source['sid'],uid=w['uid'],slot=w['slots'][j],jacobian_sha256=h.hexdigest(),matrices=288,parameters=15335424))
                del lp; runtime.model.zero_grad(set_to_none=True)
            logits.append(row)
        q=[normalize(np,v) for v in logits]; lengths=[w['lengths'] for w in source['windows']]
        overlap=[w['overlap'] for w in source['windows']]
        value,stats,g,conditional=action_gradient(np,lengths,overlap,q,source['gt'])
        combined=combine_jacobians(np,jacobians,np.concatenate(g)/4.)
        for key in aggregate: aggregate[key]+=combined[key]
        reports.append(dict(sid=source['sid'],logits0=logits,J0=value,stats0=stats,
            conditional_utilities=conditional,coefficients=[v.tolist() for v in g],branches=flat,
            old_cache_J=action_gradient(np,lengths,overlap,[normalize(np,w['original_logits']) for w in source['windows']],source['gt'])[0]))
        event('SOURCE_JACOBIANS_COMBINED',dict(sid=source['sid'],J0=value,branches=len(jacobians),normalization='one_fourth_only_no_per_source_gradient_normalization'))
        del combined,jacobians,grads
    store.close(); assert before_calls==backward==78
    # Exact original theta remained unchanged for every derivative branch.
    actual=runtime._adapter_state(); assert all(torch.equal(actual[k].view(torch.uint8),original[k].view(torch.uint8)) for k in original)
    final,step=fixed_step(np,initial,aggregate,protocol['relative_global_step_norm'])
    gradient_path=N/'aggregate_gradient20.safetensors'; assert not gradient_path.exists()
    save_file({k:torch.from_numpy(v) for k,v in aggregate.items()},str(gradient_path),metadata={'purpose':'four_source_macro_exact_chain_rule','dtype':'float64'})
    grad_loaded=load_file(str(gradient_path)); assert all(np.array_equal(grad_loaded[k].numpy(),aggregate[k]) for k in aggregate)
    save(N/'pre_update20.json',dict(source_reports=reports,step=step,gradient_ref=ref(gradient_path),
        counts=dict(runtime.counts),same_initial_theta_all78=True,actual_current_logprob_coefficients=True))
    with torch.no_grad():
        for key,p in zip(names,parameters): p.copy_(torch.from_numpy(final[key]).to(p.device))
    runtime.counts['optimizer_steps']+=1; event('ACTUAL_SINGLE_GLOBAL_UPDATE',dict(step=step))
    # Same dropout-free training/grad-enabled forward path, no backward or graph retention.
    after_calls=0
    for source,report in zip(targets['sources'],reports):
        logits=[]
        for w in source['windows']:
            _,values,_=store.case(w['uid']); row=[]
            for j,suffix in enumerate(w['suffixes']):
                event('BEGIN_FIRST_POSTSTEP_SCORE',dict(sid=source['sid'],uid=w['uid'],slot=w['slots'][j]))
                lp=runtime._sum_logprob(values,suffix,gradient=True); row.append(float(lp.detach().cpu())); del lp
                after_calls+=1
                event('POSTSTEP_SCORE_ACCEPTED',dict(sid=source['sid'],uid=w['uid'],slot=w['slots'][j],logprob=row[-1]))
            logits.append(row)
        value,stats,_,_=action_gradient(np,[w['lengths'] for w in source['windows']],
            [w['overlap'] for w in source['windows']],[normalize(np,v) for v in logits],source['gt'])
        report.update(logits1=logits,J1=value,stats1=stats)
        report['mean_window_KL0to1']=float(np.mean([stable_kl(np,l0,l1) for l0,l1 in zip(report['logits0'],logits)]))
    store.close(); assert after_calls==78 and runtime.counts['top_level_forward_calls']==156
    runtime._inference_mode(); inventory=runtime._inventory(False)
    final_state=runtime._adapter_state(); finaldir=N/'final20'; finaldir.mkdir()
    runtime.model.peft_config['policy'].save_pretrained(str(finaldir))
    finalpath=finaldir/'adapter_model.safetensors'; save_file(final_state,str(finalpath),metadata={'format':'pt'})
    loaded=load_file(str(finalpath)); assert all(torch.equal(final_state[k].view(torch.uint8),loaded[k].view(torch.uint8)) for k in final_state)
    runtime._restore_fp32(loaded); runtime._inventory(False)
    assert all(np.array_equal(p.detach().cpu().numpy().view(np.uint8),final[k].view(np.uint8)) for k,p in zip(names,parameters))
    base_after=canonical_frozen_hash(runtime.model,torch); assert base_after==runtime.base_before
    runtime._original_files()
    J0=float(np.mean([r['J0'] for r in reports])); J1=float(np.mean([r['J1'] for r in reports]))
    # A conservative ambiguity test using actual original-cache implementation drift;
    # not a rigorous universal numeric bound, and not a generalization/production gate.
    drift=float(np.mean([abs(r['J0']-r['old_cache_J']) for r in reports])); ambiguity=max(1e-6,2*drift)
    status='PASS_ONE_STEP_OPTIMIZATION_MECHANISM_ONLY' if J1-J0>ambiguity else 'STOP_ONE_STEP_NOT_POSITIVE_OR_NUMERICALLY_AMBIGUOUS'
    save(N/'gpu_completion20.json',dict(status=status,J0=J0,J1=J1,delta=J1-J0,numerical_ambiguity_threshold=ambiguity,
        old_cache_mean_absolute_J_drift=drift,step=step,source_reports=reports,
        counts=dict(runtime.counts),first_autograd_forwards=before_calls,first_poststep_forwards=after_calls,
        actual_backwards=backward,actual_updates=1,gradient_ref=ref(gradient_path),final_weights_ref=ref(finalpath),
        final_config_ref=ref(finaldir/'adapter_config.json'),base_before=runtime.base_before,base_after=base_after,
        original_TIME_ref=identity['original_TIME_weights'],all_288_save_reload_exact=True,inventory=inventory,
        seconds=time.monotonic()-start,no_new_rollouts=True,automatic_next_update=False,production_admitted=False,new_ZIP=0,official_submissions=0))


def review(root):
    import numpy as np
    import torch
    from safetensors.torch import load_file
    from source_risk19 import action_gradient,normalize
    from source_step20_math import fixed_step
    N,R,W,a,p,c,m,Store=context(root); result=json.loads((N/'gpu_completion20.json').read_text())
    accepted=json.loads((N/'input_acceptance20.json').read_text()); targets=readref(accepted['target_ref'],W)
    pre=json.loads((N/'pre_update20.json').read_text())
    assert result['counts']['optimizer_steps']==result['actual_updates']==1
    assert result['actual_backwards']==78 and result['counts']['backwards_completed']==78
    assert result['counts']['sequence_scores_completed']==result['counts']['top_level_forward_calls']==156
    assert result['base_before']==result['base_after'] and result['all_288_save_reload_exact']
    # Rebuild the exact PEFT mapping without loading a model: saved keys retain
    # base_model.model. and remove only the .policy adapter name before .weight.
    old=load_file(str(checked(m['model_spec']['adapter_weights'],W)))
    grad={k:v.numpy() for k,v in load_file(str(checked(result['gradient_ref'],W))).items()}
    def statekey(name): return name.replace('.policy.weight','.weight')
    initial={k:old[statekey(k)].numpy() for k in grad}
    final,step=fixed_step(np,initial,grad,p['relative_global_step_norm'])
    saved=load_file(str(checked(result['final_weights_ref'],W)))
    assert len(saved)==len(final)==288 and all(np.array_equal(saved[statekey(k)].numpy().view(np.uint8),v.view(np.uint8)) for k,v in final.items())
    assert step==result['step'] and step==pre['step']
    for target,row in zip(targets['sources'],result['source_reports']):
        assert row['sid']==target['sid']
        for phase in [0,1]:
            value,_,_,_=action_gradient(np,[w['lengths'] for w in target['windows']],
                [w['overlap'] for w in target['windows']],[normalize(np,v) for v in row['logits'+str(phase)]],target['gt'])
            assert abs(value-row['J'+str(phase)])<1e-12
    baseline=ref(W/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    save(N/'review20.json',dict(status=result['status'],actual_updates=1,gradient_and_FP32_step_independent_QA='PASS_AGGREGATE_STEP_AND_OBJECTIVE_ONLY',
        per_branch_derivative_QA='finite288_and_hash_recorded_live_RAM; no independent repeated backward',
        J0=result['J0'],J1=result['J1'],delta=result['delta'],predicted_first_order_gain=step['predicted_first_order_gain'],
        numerical_ambiguity_threshold=result['numerical_ambiguity_threshold'],source_reports=result['source_reports'],
        production_admitted=False,more_updates_admitted=False,protected_baseline_ref=baseline,
        reason='Only local optimization sign. Random-program utility is not fixed-K deployment or official joint score; separate review required.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--phase',choices=['prepare','gpu','review'],required=True)
    parser.add_argument('--run-root',required=True); args=parser.parse_args()
    try: globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'20.json'),dict(status='ACTUAL_FAILURE_NO_AUTOMATIC_REPEAT',traceback=traceback.format_exc()))
        raise
