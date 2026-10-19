"""One shared original B load: first external VERIFY, first VideoXum context."""
from sr_common import *
from cache_loader_fast import cache_load
import time
import math

def main():
    import numpy as np
    import torch
    rt=runtime()
    from sft_contract import verify_live_gpu_reservation
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Frozen parent physical GPU0 visibility')
    verify_live_gpu_reservation();torch.set_num_threads(2)
    ac=read(ROOT/'cpu_completion.json');qa=read(ROOT/'input_qa.json')
    require(qa['status']=='PASS_FIRST_INDEPENDENT_NEW_INPUT_QA' and qa['cpu_completion_sha256']==sha(ROOT/'cpu_completion.json'),'All new actual inputs must pass before GPU')
    lock=read(ROOT/'source_lock.json')
    bound(lock['registration_ref']);bound(lock['CPU_ref']);bound(lock['first_input_QA_ref'])
    for code_ref in lock['code'].values():bound(code_ref)
    require(not (ROOT/'gpu_started.json').exists(),'No repeated successful/attempted GPU entry')
    save(ROOT/'gpu_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],utc=utc(),registration_sha256=sha(ROOT/'registration.json')))
    _,_,grammar_module=verify_modules();cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    model,processor,identity=rt.b_engine.load_model(cfg);model.requires_grad_(False)
    require(identity['logical_parameters']==8782459120 and identity['adapter']['adapter_enabled'],'Actual original B/TIME identity')
    save(ROOT/'model_identity.json',identity)
    from peft.tuners.tuners_utils import BaseTunerLayer
    layers=[m for m in model.modules()if isinstance(m,BaseTunerLayer)];require(len(layers)==144 and all(not m.disable_adapters for m in layers),'TIME role truly active')
    flags=[(p,p.requires_grad)for p in model.parameters()]
    eos=model.generation_config.eos_token_id;eos=[eos]if isinstance(eos,int)else list(eos)
    candidates=grammar_module.candidate_tokens(processor.tokenizer,('{"decision":"KEEP"}','{"decision":"UNKNOWN"}','{"decision":"DROP"}'))
    answers=[];begun=0;started=time.monotonic();(ROOT/'verify_outputs').mkdir()
    for r in ac['verify_inputs']:
        require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(lock['deadline'].replace('Z','+00:00')),'No new model call after four-hour registered window')
        x=read(bound(r));rid=x['request']['request_id'];folder=ROOT/'verify_outputs'/rid;folder.mkdir()
        vision=cache_load(bound(x['vision_ref']));text=torch.load(bound(x['text_ref']),map_location='cpu',weights_only=True)
        require(rt.tensor_signature({**vision,**text})==x['full_signature'],'GPU input adopted exact accepted CPU bytes')
        gpu={k:v.to('cuda:0')for k,v in {**vision,**text}.items()};require(rt.tensor_signature(gpu)==x['full_signature'],'Actual GPU tensors differ')
        prefix=gpu['input_ids'].shape[1];grammar=grammar_module.VerifyConstraint(processor.tokenizer,int(prefix),x['request'],eos,candidates)
        save(folder/'request.json',dict(input_ref=r,model_role='TIME_ENABLED',input_signature=x['full_signature'],labels_read=False))
        require(all(not m.disable_adapters for m in layers),'TIME unexpectedly disabled')
        begun+=1;event('BEGIN_VERIFY',request_id=rid,call=begun)
        t=time.monotonic()
        with torch.inference_mode():
            out=model.generate(**gpu,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=grammar,return_dict_in_generate=True,output_scores=True)
        torch.cuda.synchronize();ids=out.sequences[0,prefix:];raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        scores=[float(s[0,int(token)])for s,token in zip(out.scores,ids)]
        save(folder/'raw.json',dict(raw_output=raw,output_token_ids=ids.tolist(),input_tokens=int(prefix),eos=eos,selected_scores=[s if math.isfinite(s)else str(s)for s in scores],seconds=time.monotonic()-t,grammar_stats=grammar.stats))
        require(0<len(ids)<=256 and len(scores)==len(ids) and all(map(math.isfinite,scores)),'Actual token/finite score denominator')
        result=grammar.assert_complete(ids);require(json.dumps(result,separators=(',',':'))==raw,'Untouched raw/parser mismatch')
        done=dict(request_id=rid,sid=x['sid'],event_id=x['request']['event_id'],decision=result['decision'],raw_ref=ref(folder/'raw.json'),request_ref=ref(folder/'request.json'),input_ref=r)
        save(folder/'done.json',done);answers.append(ref(folder/'done.json'));event('ACCEPTED_VERIFY',call=begun,request_id=rid)
        if begun==4:save(ROOT/'first4_GPU_cost.json',dict(actual_calls=4,elapsed_seconds=time.monotonic()-started,remaining_verify=238-4,context_queries=qa['context_queries'],peak_MiB=torch.cuda.max_memory_allocated()/2**20))
        del out,ids,gpu,vision,text
    require(begun==len(answers)==238,'Complete unique first VERIFY denominator')
    save(ROOT/'verify_completion.json',dict(status='ALL238_FIRST_VERIFY_RAW_SUCCESS_PENDING_INDEPENDENT_REPLAY',outputs=answers,model_identity_sha256=sha(ROOT/'model_identity.json')))
    native=model.get_base_model();core=native.model;yes=processor.tokenizer.encode('Yes',add_special_tokens=False);no=processor.tokenizer.encode('No',add_special_tokens=False)
    require(len(yes)==len(no)==1,'Original single Yes/No tokens')
    sources=[];batches=queries=0
    try:
        with model.disable_adapter(),torch.inference_mode():
            require(all(m.disable_adapters for m in layers),'Actual BASE-only context role')
            for s in ac['context_sources']:
                folder=ROOT/'features'/s['sid'];folder.mkdir(parents=True);latents=[];pairs=[]
                for c in s['cases']:
                    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(lock['deadline'].replace('Z','+00:00')),'No new context forward after registered window')
                    x=torch.load(bound(c),map_location='cpu',weights_only=True);k=c['queries'];gpu={q:x[q].to('cuda:0')for q in ('input_ids','attention_mask')}
                    gpu['pixel_values']=x['pixel_values'].repeat(k,1).to('cuda:0');gpu['image_grid_thw']=x['image_grid_thw'].repeat(k,1).to('cuda:0')
                    event('BEGIN_CONTEXT',sid=s['sid'],case=c['index'],queries=k)
                    out=core(**gpu,use_cache=False,return_dict=True);last=out.last_hidden_state[:,-1,:];logits=native.lm_head(last).float();pair=logits[:,[yes[0],no[0]]].cpu();last=last.float().cpu()
                    require(torch.isfinite(last).all()and torch.isfinite(pair).all(),'New context outputs finite')
                    p=folder/('context_%04d.pt'%c['index']);torch.save(dict(language=last,yes_no=pair),p)
                    save(folder/('context_%04d.json'%c['index']),dict(input_ref=c,output_ref=ref(p),role='BASE_DISABLED'))
                    latents.append(last.numpy());pairs.append(pair.numpy());batches+=1;queries+=k
                    event('ACCEPTED_CONTEXT',sid=s['sid'],case=c['index'],batches=batches,queries=queries)
                    del out,gpu,last,logits,pair,x
                language=np.concatenate(latents);yn=np.concatenate(pairs);require(len(language)==s['cells'],'All new source target cells')
                np.save(folder/'language.npy',language);np.save(folder/'yes_no.npy',yn)
                sources.append(dict(sid=s['sid'],language_ref=ref(folder/'language.npy'),yes_no_ref=ref(folder/'yes_no.npy'),cells=len(language)))
    finally:
        for p,flag in flags:p.requires_grad_(flag)
    require(all(not m.disable_adapters for m in layers),'TIME activation restored')
    require(rt.b_engine.frozen_identity(model,cfg)==identity['base']and rt.b_engine.adapter_identity(model,cfg)==identity['adapter'],'Full base/TIME unchanged at terminal')
    save(ROOT/'gpu_completion.json',dict(status='ALL_NEW_EXTERNAL_GENERATION_AND_CONTEXT_SUCCESS_PENDING_INDEPENDENT_OUTPUT_QA',verify_calls=begun,context_batches=batches,context_queries=queries,context_sources=sources,all_parameter_flags_restored=True,base_updates=0,actual_parameters=8782459120,utc=utc()))

def replay():
    cpu();import numpy as np
    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(1);_,_,gm=verify_modules();cfg=read(RUN/'b_score_aligned_package_v4/config.json');tok=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    done=read(ROOT/'gpu_completion.json');verify=read(ROOT/'verify_completion.json');decisions={}
    for r in verify['outputs']:
        d=read(bound(r));raw=read(bound(d['raw_ref']));inp=read(bound(d['input_ref']));ids=raw['output_token_ids']
        grammar=gm.VerifyConstraint(tok,raw['input_tokens'],inp['request'],raw['eos'],candidates=())
        parsed=grammar.assert_complete(ids);text=tok.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        require(parsed['decision']==d['decision']and text==raw['raw_output']==json.dumps(parsed,separators=(',',':')),'Independent raw/generated-token/finite-grammar replay')
        require(d['event_id']not in decisions,'Duplicate event decisions');decisions[d['event_id']]=d['decision']
    queries=0
    ac=read(ROOT/'cpu_completion.json');by={s['sid']:s for s in done['context_sources']}
    for src in ac['context_sources']:
        languages=[];pairs=[]
        for c in src['cases']:
            r=read(ROOT/'features'/src['sid']/('context_%04d.json'%c['index']));p=torch.load(bound(r['output_ref']),map_location='cpu',weights_only=True)
            require(r['input_ref']==c and p['language'].shape==(c['queries'],4096)and p['yes_no'].shape==(c['queries'],2),'Actual context/source/input-order output binding')
            require(torch.isfinite(p['language']).all()and torch.isfinite(p['yes_no']).all(),'Finite first context outputs')
            languages.append(p['language'].numpy());pairs.append(p['yes_no'].numpy());queries+=c['queries']
        require(np.array_equal(np.concatenate(languages),np.load(bound(by[src['sid']]['language_ref'])))and np.array_equal(np.concatenate(pairs),np.load(bound(by[src['sid']]['yes_no_ref']))),'Independent complete source concatenation')
    require(len(decisions)==238 and queries==done['context_queries']and not torch.cuda.is_initialized(),'Full independent output denominator')
    save(ROOT/'decisions.json',decisions)
    save(ROOT/'output_qa.json',dict(status='PASS_FIRST_INDEPENDENT_ALL_EXTERNAL_TOKEN_CONTEXT_REPLAY',verify=238,context_queries=queries,decisions_ref=ref(ROOT/'decisions.json'),gpu_completion_sha256=sha(ROOT/'gpu_completion.json'),no_new_model_calls=True,utc=utc()))

if __name__=='__main__':
    try:{'infer':main,'replay':replay}[sys.argv[1]]()
    except BaseException as e:failure('infer_'+sys.argv[1],e);raise
