"""Frozen Tiny encoder on exact8s inputs, then independent CPU modality controls."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def read(p):return json.loads(Path(p).read_text())


def ref(p):
    p=Path(p).resolve(strict=True);h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())


def check(r):
    assert ref(r['path'])==r,'Bound successful bytes';return Path(r['path'])


def save(p,v):
    with Path(p).open('x')as f:json.dump(v,f,indent=2,allow_nan=False)


def pool_np(np,valid):
    assert valid.shape==(396,384) and valid.dtype==np.float32 and np.isfinite(valid).all()
    return np.r_[valid.mean(axis=0),valid.std(axis=0,ddof=0)].astype(np.float32)


def permutation(keys):
    order=sorted(keys,key=lambda s:hashlib.sha256(s.encode()).hexdigest())
    assert len(order)>1
    return {s:order[(i+1)%len(order)]for i,s in enumerate(order)}


def state_sha(model):
    h=hashlib.sha256()
    for n,v in sorted(model.state_dict().items()):
        h.update(n.encode());h.update(str(tuple(v.shape)).encode());h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def context(root):
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent
    a=read(N/'model_admission15.json');assert a['approved'] and a['code_ref']==ref(__file__)
    inputs=read(check(a['input_acceptance_ref']));assert inputs['status']=='PASS_QUALIFIED_EXACT8S_ACOUSTIC_INPUT_SUBSET'
    inv=read(check(inputs['inventory_ref']))
    return N,R,W,a,inputs,inv


def features(root):
    import numpy as np,torch,resource
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    N,R,W,a,inputs,inv=context(root);start=time.monotonic();usage=resource.getrusage(resource.RUSAGE_SELF)
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and not torch.cuda.is_available(),'Own CPU process only'
    old=module(check(inv['original_author_code_ref']),'accepted_whisper15');core,_,proof=old.original_modules(W/'bottleneck_24h_20261019_v1/audio_semantic23/author')
    data=torch.load(check(inv['model_ref']),map_location='cpu',weights_only=True)
    model=core.Whisper(core.ModelDimensions(**data['dims']));model.load_state_dict(data['model_state_dict'],strict=True)
    for p in model.parameters():p.requires_grad_(False)
    model.eval();assert sum(p.numel()for p in model.parameters())==37184640
    before=state_sha(model);out=N/'features15';out.mkdir();refs={};cache={};calls=0;decoder_calls=0
    def guard(m,args):
        nonlocal calls
        assert time.monotonic()-start<a['max_CPU_model_seconds'] and not any(p.requires_grad for p in model.parameters())
        calls+=1
    def decoder_guard(m,args):
        nonlocal decoder_calls
        decoder_calls+=1;raise AssertionError('Decoder not admitted for acoustic features')
    hook=model.encoder.register_forward_pre_hook(guard);dh=model.decoder.register_forward_pre_hook(decoder_guard)
    for uid,r in sorted(inputs['case_refs'].items()):
        c=read(check(r));key=c['mel_ref']['sha256']
        if key in cache:
            prior=cache[key];row=read(check(prior));output_ref=row['feature_ref'];adopted=True
        else:
            prior=None;adopted=False
            with np.load(check(c['mel_ref']),allow_pickle=False)as z:mel=torch.from_numpy(z['mel'].copy())
            assert mel.shape==(80,3000) and torch.isfinite(mel).all() and c['samples']==128000
            with torch.inference_mode():h=model.encoder(mel[None])
            assert tuple(h.shape)==(1,1500,384) and torch.isfinite(h).all()
            valid=h[0,2:398].float().cpu().contiguous()
            pooled=torch.cat((valid.mean(dim=0),valid.std(dim=0,unbiased=False)))
            fp=out/(uid+'.npz');np.savez_compressed(fp,valid_hidden=valid.numpy(),pooled=pooled.numpy())
            output_ref=ref(fp)
        row=dict(uid=uid,feature_ref=output_ref,input_ref=r,source_sha256=c['source_sha256'],
            mel_ref=c['mel_ref'],model_ref=inv['model_ref'],valid_encoder_start=2,valid_encoder_stop=398,
            pooling='mean and population std over396 real8second inner positions, 768dimensions',
            audio_encoder_attention_still_sees_input_padding=True,labels_in_model=False,
            actual_encoder_calls=0 if adopted else 1,adopted_identical_mel_output_ref=prior,author_AST_proof=proof)
        rp=out/(uid+'.json');save(rp,row);refs[uid]=ref(rp);cache[key]=refs[uid]
        with (N/'encoder_events15.jsonl').open('a')as f:
            f.write(json.dumps(dict(event='FIRST_ACOUSTIC_FEATURE_ACCEPTED',uid=uid,adopted=adopted))+'\n');f.flush();os.fsync(f.fileno())
    hook.remove();dh.remove();after=state_sha(model);assert before==after and decoder_calls==0
    assert calls<=100 and len(refs)==len(inputs['case_refs'])
    save(N/'encoder_completion15.json',dict(status='COMPLETE_FROZEN_CPU_ACOUSTIC_FEATURES_NOT_QUALITY',feature_refs=refs,
        logical_cases=len(refs),actual_encoder_calls=calls,adopted_identical_inputs=len(refs)-calls,
        model_before=before,model_after=after,model_parameters=37184640,model_updates=0,decoder_calls=0,
        wall_seconds=time.monotonic()-start,CPU_user_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime-usage.ru_utime,
        CPU_system_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_stime-usage.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def metric(np,rows,values,w):
    out=[]
    for r in rows:
        z=float((values[r['left']]-values[r['right']])@w);y=r['preference_left']
        prob=float(np.exp(-np.logaddexp(0,-z)))
        out.append(dict(source_id=r['source_id'],pair_id=r['pair_id'],probability=prob,target=y,
            correct=.5 if z==0 else float((z>0)==(y>.5)),brier=(prob-y)**2))
    ids=sorted({r['source_id']for r in out})
    means={k:sum(sum(r[k]for r in out if r['source_id']==s)/sum(r['source_id']==s for r in out)for s in ids)/len(ids)for k in ['correct','brier']}
    return dict(source_macro_accuracy=means['correct'],source_macro_brier=means['brier'],sources=len(ids),pairs=len(out),rows=out)


def fit(root):
    import numpy as np,torch
    N,R,W,a,inputs,inv=context(root);start=time.monotonic();c=read(N/'encoder_completion15.json')
    assert c['status']=='COMPLETE_FROZEN_CPU_ACOUSTIC_FEATURES_NOT_QUALITY' and c['model_before']==c['model_after']
    acoustic={};qa=0
    for uid,r in c['feature_refs'].items():
        row=read(check(r));original=read(check(inputs['case_refs'][uid]));assert row['mel_ref']==original['mel_ref'] and row['input_ref']==inputs['case_refs'][uid]
        with np.load(check(row['feature_ref']),allow_pickle=False)as z:
            raw=z['valid_hidden'];f=z['pooled'];expected=pool_np(np,raw)
            assert f.shape==(768,) and np.allclose(f,expected,rtol=2e-5,atol=2e-6)
        assert row['valid_encoder_start']==2 and row['valid_encoder_stop']==398
        q=f.astype(float);norm=float(np.linalg.norm(q));assert norm>0 and np.isfinite(norm)
        acoustic[uid]=q/norm;qa+=1
    assert qa==len(inputs['case_refs'])
    visual={};old=read(R/'relative_ranker06/gpu_completion07.json');new=read(R/'domain_rank11/gpu_completion12.json')
    for r in old['initial_feature_refs']+new['feature_refs']:
        row=read(check(r));uid=row['uid']
        if uid not in acoustic:continue
        t=torch.load(check(row['feature_ref']),map_location='cpu',weights_only=True)
        assert t.shape==(4096,) and t.dtype==torch.float32 and torch.isfinite(t).all()
        visual[uid]=t.numpy().astype(float)/64
    assert set(visual)==set(acoustic)
    targets=inputs['targets'];train=targets['train'];check_rows=targets['check'];perm={}
    for group in targets.values():perm.update(permutation({r[k]for r in group for k in ['left','right']}))
    assert all(k!=v for k,v in perm.items())
    values=dict(video=visual,audio=acoustic,
        fused={k:np.r_[visual[k],acoustic[k]]/np.sqrt(2)for k in acoustic},
        permuted_audio={k:np.r_[visual[k],acoustic[perm[k]]]/np.sqrt(2)for k in acoustic})
    solver=module(check(a['convex_solver_code_ref']),'adopted_fixed_convex_solver15')
    metrics={};receipts={}
    for arm,v in values.items():
        X=np.vstack([v[r['left']]-v[r['right']]for r in train]);y=np.asarray([r['preference_left']for r in train])
        w,receipt=solver.convex_fit(np,X,y)
        fp=N/(arm+'_head15.npz');np.savez_compressed(fp,weight=w)
        with np.load(fp,allow_pickle=False)as z:assert np.array_equal(z['weight'],w)
        probe=v[check_rows[0]['left']];delta=abs(float(torch.from_numpy(w)@torch.from_numpy(probe))-float(w@probe));assert delta<1e-10
        receipt.update(weight_ref=ref(fp),parameters=len(w),independent_Torch_readout_difference=delta)
        save(N/(arm+'_solver15.json'),receipt);receipts[arm]=receipt
        metrics[arm]=dict(train=metric(np,train,v,w),check=metric(np,check_rows,v,w))
    fused=metrics['fused']['check'];reasons=[]
    if fused['source_macro_accuracy']<.75:reasons.append('FUSED_REAL_ACCURACY_BELOW_POINT75')
    for arm in ['video','permuted_audio']:
        q=metrics[arm]['check']
        if not fused['source_macro_accuracy']>q['source_macro_accuracy']:reasons.append('NO_ACCURACY_ADVANTAGE_OVER_'+arm.upper())
        if not fused['source_macro_brier']<q['source_macro_brier']:reasons.append('NO_BRIER_ADVANTAGE_OVER_'+arm.upper())
    improved=[]
    for sid in sorted({r['source_id']for r in check_rows}):
        def avg(arm):
            rows=[r for r in metrics[arm]['check']['rows']if r['source_id']==sid];return sum(r['correct']for r in rows)/len(rows)
        if avg('fused')>avg('video'):improved.append(sid)
    if len(improved)<2:reasons.append('TOO_FEW_SOURCE_ACCURACY_GAINS')
    result=dict(status='STOP_FIXED_WHISPER_POOLED_LINEAR_FUSION' if reasons else 'ELIGIBLE_FOR_SEPARATE_FULL_SOURCE_ACOUSTIC_REVIEW',
        stop_reasons=reasons,metrics=metrics,solver_receipts=receipts,first_independent_output_QA=qa,
        acoustic_permutation=perm,improved_sources=improved,training_sources=inputs['training_sources'],check_sources=8,
        input_excluded_sources=inputs['excluded_sources'],actual_encoder_calls=c['actual_encoder_calls'],new_Qwen_calls=0,
        new_neural_model_updates=0,CPU_head_fits=4,actual_Newton_updates=sum(r['updates']for r in receipts.values()),
        new_heads_total_parameters=sum(r['parameters']for r in receipts.values()),
        conservative_formal_fused_pipeline_parameters=8819746953,
        all_historical_exposed=True,new_blind_test=False,official_joint_score='UNKNOWN',automatic_production=False,
        new_ZIP=0,official_submissions=0,seconds=time.monotonic()-start)
    save(N/'review15.json',result)
    print(json.dumps({k:v for k,v in result.items()if k not in ['metrics','solver_receipts','acoustic_permutation','input_excluded_sources']}|
        {'metrics':{k:{g:{n:x for n,x in vv.items()if n!='rows'}for g,vv in v.items()}for k,v in metrics.items()}}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);a.add_argument('--phase',choices=['features','fit'],required=True);args=a.parse_args()
    try:features(args.run_root)if args.phase=='features'else fit(args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'15.json'),dict(status='ACTUAL_FAILURE_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()))
        raise
