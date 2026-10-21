"""Original BASE spatial anchors and independent endpoint-only motion readout."""
import argparse,hashlib,json,math,os,sys,time,traceback
from pathlib import Path


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(p,v):
    with Path(p).open('x')as f:json.dump(v,f,indent=2,allow_nan=False)


def context(root):
    n=Path(root).resolve(strict=True);w=n.parent.parent
    r=json.loads((n/'registration43.json').read_text())
    def read(rr):
        p=Path(rr['path']).resolve(strict=True)
        assert p.is_relative_to(w)and ref(p)==rr
        return json.loads(p.read_text())
    assert r['code_ref']==ref(__file__)
    for rr in r['code_bindings']:assert ref(rr['path'])==rr
    a=read(r['input_acceptance_ref']);assert a['status']=='PASS_CPU_NATIVE_MOTION_INPUTS_REMAINING44_NOT_GPU_ADMISSION'
    return n,w,r,a,read


def focus(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('DuplicateJSONkey')
            out[k]=v
        return out
    try:
        v=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    except(ValueError,TypeError,RecursionError):return None
    if not isinstance(v,dict)or set(v)!={'center'}:return None
    c=v['center']
    if not isinstance(c,list)or len(c)!=2 or any(type(x)is not int or not 0<=x<=1000 for x in c):return None
    return [x/1000 for x in c]


def gpu(root):
    n,w,r,a,read=context(root)
    admitted=read(ref(n/'gpu_admission43.json'));assert admitted['approved']
    sys.path.insert(0,str(w/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    assert os.environ.get('CUDA_VISIBLE_DEVICES'),'Only CPU children may mask CUDA'
    import torch
    from transformers import AutoTokenizer,Qwen3VLForConditionalGeneration
    input_root=Path(r['input_acceptance_ref']['path']).parent
    sys.path.insert(0,str(input_root));from native_motion_remaining44 import model_case
    sys.path.insert(0,r['prior_code_root'])
    from improvement.native_preference_v1.runtime import canonical_frozen_hash,tensor_signature
    spec=a['model_spec'];started=time.monotonic();torch.set_num_threads(4)
    def event(kind,**extra):
        with(n/'events43.jsonl').open('a')as f:
            f.write(json.dumps(dict(kind=kind,elapsed=time.monotonic()-started,**extra),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def budget():assert time.monotonic()-started<r['maximum_GPU_seconds']
    model=Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,
        trust_remote_code=False,torch_dtype=torch.bfloat16,device_map='auto',low_cpu_mem_usage=True,attn_implementation='sdpa')
    model.eval()
    for p in model.parameters():p.requires_grad_(False)
    assert not any('lora_'in k for k,_ in model.named_parameters())
    before=canonical_frozen_hash(model,torch)
    assert before['parameters']==8767123696 and before['sha256']=='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
    tokenizer=AutoTokenizer.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,trust_remote_code=False)
    device=next(model.parameters()).device
    calls=0
    def guard(module,args,kwargs):
        nonlocal calls
        budget();assert not module.training and not any(p.requires_grad for p in module.parameters())
        calls+=1
    handle=model.register_forward_pre_hook(guard,with_kwargs=True)
    rows=[];cache={};generations=0;adoptions=0
    for rr in a['case_refs']:
        budget();case,values=model_case(input_root,rr)
        assert tensor_signature(torch,values)==case['input_signature']
        prefix=values['input_ids'][0].tolist();begin=calls
        key=json.dumps(dict(signature=case['input_signature'],recipe='ORIGINAL_BASE_BF16_SDPA_GREEDY_BEAM1_CACHE_128'),sort_keys=True)
        adopted_from=None
        if key in cache:
            suffix,raw,adopted_from=cache[key];adoptions+=1
            event('ADOPT_IDENTICAL_FOUR_TENSOR_SPATIAL_INPUT43',uid=case['uid'],original_raw_ref=adopted_from)
        else:
            event('BEGIN_FIRST_ORIGINAL_BASE_SPATIAL_ANCHOR',uid=case['uid'],evaluation_only=case['evaluation_only'])
            with torch.inference_mode():
                output=model.generate(**{k:v.to(device)for k,v in values.items()},do_sample=False,num_beams=1,use_cache=True,max_new_tokens=128)
            assert output.shape[0]==1 and output[0,:len(prefix)].tolist()==prefix
            suffix=output[0,len(prefix):].tolist();assert 0<len(suffix)<=128
            raw=tokenizer.decode(suffix,skip_special_tokens=True,clean_up_tokenization_spaces=False);generations+=1
        row=dict(uid=case['uid'],sid=case['sid'],case_ref=rr,input_signature=case['input_signature'],suffix=suffix,text=raw,
            evaluation_only=case['evaluation_only'],top_level_forwards=calls-begin,parser_result=focus(raw),new_training=0,
            generation_kind='ADOPT_IDENTICAL_INPUT'if adopted_from else'FIRST_NEW_GENERATION',adopted_from_ref=adopted_from)
        path=n/(case['uid']+'_raw43.json');save(path,row);rows.append(ref(path))
        if adopted_from is None:cache[key]=(suffix,raw,rows[-1])
        event('ORIGINAL_BASE_SPATIAL_ANCHOR_ACCEPTED',uid=case['uid'],raw_ref=rows[-1],top_level_forwards=calls-begin)
    handle.remove();after=canonical_frozen_hash(model,torch);assert after==before
    assert len(rows)==len(a['case_refs'])==generations+adoptions<=24
    save(n/'gpu_completion43.json',dict(status='ENGINEERING_COMPLETE_FIRST_ORIGINAL_BASE_SPATIAL_ANCHORS43',raw_refs=rows,
        generation_calls=generations,logical_anchors=len(rows),identical_input_adoptions=adoptions,
        top_level_forwards=calls,updates=0,backwards=0,base_before=before,base_after=after,
        complete_pipeline_parameters=8782557449,physical_parameters=8767123696,original_TIME_not_loaded=True,
        seconds=time.monotonic()-started,automatic_production=False,new_ZIP=0,official_submissions=0))


def review(root):
    n,w,r,a,read=context(root)
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    import numpy as np
    from transformers import AutoTokenizer
    from motion_transport43 import transport,box,normalized_center_error
    start=time.monotonic();g=read(ref(n/'gpu_completion43.json'))
    assert g['updates']==g['backwards']==0 and g['base_before']==g['base_after']
    spec=a['model_spec'];tokenizer=AutoTokenizer.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,trust_remote_code=False)
    raw={}
    for rr in g['raw_refs']:
        row=read(rr);case=read(row['case_ref']);assert row['case_ref']in a['case_refs']
        assert row['input_signature']==case['input_signature']and case['labels_read']is False
        assert row['text']==tokenizer.decode(row['suffix'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        center=focus(row['text']);assert center==row['parser_result']
        assert row['evaluation_only']==case['evaluation_only']
        if row['adopted_from_ref']:
            prior=read(row['adopted_from_ref'])
            assert prior['input_signature']==row['input_signature']and prior['suffix']==row['suffix']and prior['text']==row['text']
            assert row['top_level_forwards']==0 and row['generation_kind']=='ADOPT_IDENTICAL_INPUT'
        else:assert row['generation_kind']=='FIRST_NEW_GENERATION'and row['top_level_forwards']>0
        assert case['uid']==row['uid']and row['uid']not in raw
        raw[row['uid']]=dict(center=center,case=case)
    assert len(raw)==g['logical_anchors']==len(a['case_refs'])==g['generation_calls']+g['identical_input_adoptions']
    rows=[]
    for rr in a['source_refs']:
        source=read(rr);base=dict(sid=source['sid'],role=source['role'],source_ref=rr,eligible=source['eligible'])
        if not source['eligible']:
            rows.append(dict(base,status='INELIGIBLE_ORIGINAL_SHOT_CUT_NO_REPLACEMENT'));continue
        cases={read(z)['anchor_offset']:read(z)for z in source['cases']}
        assert set(cases)=={0,4,8}
        centers={k:raw[v['uid']]['center']for k,v in cases.items()}
        if any(v is None for v in centers.values()):
            rows.append(dict(base,status='INVALID_MODEL_ANCHOR_NOT_CENTER_FALLBACK'));continue
        grayref=source['gray_ref'];assert ref(grayref['path'])==grayref
        with np.load(grayref['path'],allow_pickle=False)as z:
            images=z['gray'];assert z['native_ordinals'].tolist()==source['native_ordinals']
            assert z['original_exact_pts'].tolist()==[v['original_pts_exact']for v in source['native_frames']]
        # Hidden center is deliberately absent from transport's API and inputs.
        outcome=transport(images,centers[0],centers[8],source['native_width'],source['native_height'])
        target=box(centers[4],source['native_width'],source['native_height'])
        control_error=normalized_center_error(outcome['control_boxes'][4],target,source['native_height'])
        motion_error=normalized_center_error(outcome['boxes'][4],target,source['native_height'])
        changed=any(x!=y for x,y in zip(outcome['boxes'],outcome['control_boxes']))
        rows.append(dict(base,status='COMPLETE_GEOMETRIC_SELF_CONSISTENCY_ONLY',outcome=outcome,
            hidden_model_box=target,control_error=control_error,motion_error=motion_error,improvement=control_error-motion_error,
            nonzero_path_change=changed,source_native_width=source['native_width'],source_native_height=source['native_height']))
    valid=[q for q in rows if q['status']=='COMPLETE_GEOMETRIC_SELF_CONSISTENCY_ONLY']
    process=[q for q in valid if q['role']=='process']
    summarize=lambda field:dict(mean=float(np.mean([q[field]for q in process])),p90=float(np.quantile([q[field]for q in process],.9,method='linear')))if process else None
    control=summarize('control_error');motion=summarize('motion_error')
    conditions=dict(all_fixed_sources_covered=len(rows)==8,valid_sources_at_least6=len(valid)>=6,
        valid_process_at_least3=len(process)>=3,all_model_anchors_valid=all(z['center']is not None for z in raw.values()),
        process_two_nonzero_changes=sum(q['nonzero_path_change']for q in process)>=2,
        process_two_improved=sum(q['improvement']>1e-12 for q in process)>=2,
        process_mean_better=bool(process and motion['mean']<control['mean']-1e-12),
        process_p90_not_worse=bool(process and motion['p90']<=control['p90']+1e-12),
        process_fallback_not_majority=sum(q['outcome']['status']=='EXACT_ORIGINAL_LINEAR_FALLBACK'for q in process)*2<=len(process))
    status='GEOMETRIC_SELF_CONSISTENCY_ELIGIBLE_SEPARATE_REVIEW_ONLY'if all(conditions.values())else'STOP_FIXED_NATIVE_MOTION_SELF_CONSISTENCY43'
    save(n/'review43.json',dict(status=status,conditions=conditions,sources=rows,process_control=control,process_motion=motion,
        independent_output_QA='PASS_TOKEN_DECODE_STRICT_PARSE_SOURCE_NATIVE_OWNERSHIP',
        first_input_QA_adopted_ref=r['input_acceptance_ref'],new_processor_calls=0,new_decode=0,new_model_calls=0,
        scope='No human crop truth: hidden ORIGINAL_BASE center is only a geometric self-consistency observation. Flow consistency may follow wrong subjects; no official-quality claim.',
        production_admitted=False,automatic_production=False,new_ZIP=0,official_submissions=0,seconds=time.monotonic()-start))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);p.add_argument('--phase',choices=['gpu','review'],required=True);a=p.parse_args()
    try:globals()[a.phase](a.run_root)
    except BaseException:
        save(Path(a.run_root)/('failure_'+a.phase+'43.json'),dict(status='ACTUAL_FAILURE_KEEP_ALL_SUCCESS_NO_AUTOMATIC_REPLAY',traceback=traceback.format_exc()));raise
