"""New context-conditioned BASE representation; old CPU image tensors reused."""
import sys
import os
from fractions import Fraction as F
from common_runtime import *

QUESTION='A visual highlight is a distinctive action peak, expressive reaction, informative reveal, or visually striking moment. Idle repetition and ordinary transitions need not be highlights. Consider visible evidence, not sound. '

def prepare():
    import torch
    from transformers import AutoProcessor
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU text-only preparation')
    proto=read(ROOT/'protocol.json');prior=Path(proto['prior_root']);accepted=read(prior/'cpu_acceptance.json')
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');p=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True)
    p.tokenizer.padding_side='left'
    ids={word:p.tokenizer.encode(word,add_special_tokens=False) for word in ['Yes','No']}
    require(all(len(x)==1 for x in ids.values()),'Single-token Yes/No readout fixed, no adaptive alternatives')
    image_id=p.tokenizer.convert_tokens_to_ids('<|image_pad|>');sources=[]
    for source in accepted['sources']:
        sid=source['id'];c=read(prior/'inputs'/sid/'clock.json');pts=[F(t) for t in c['normalized_exact_pts']]
        out=ROOT/'inputs'/sid;out.mkdir(parents=True,exist_ok=False);cases=[]
        for ci,chunk in enumerate(source['chunks']):
            k=len(chunk['samples']);texts=[]
            # Grid/pixel payload is adopted; only new text tokens are prepared.
            grids=chunk['grid'];require(len(grids)==k,'Adopted image/grid mapping')
            for target in range(k):
                content=[dict(type='text',text=QUESTION+'These are ordered frames from a short silent sequence.\n')]
                for j,ordinal in enumerate(chunk['samples']):
                    content.extend([dict(type='text',text='Frame %d, relative time %.3fs.\n'%(j+1,float(pts[ordinal]-pts[chunk['samples'][0]]))),dict(type='image')])
                content.append(dict(type='text',text='Does frame %d depict a visual highlight in this context? Answer exactly Yes or No.'%(target+1)))
                text=p.apply_chat_template([dict(role='user',content=content)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
                require(text.count('<|image_pad|>')==k,'Native image placeholders')
                for grid in grids:
                    count=grid[0]*grid[1]*grid[2]//4
                    text=text.replace('<|image_pad|>','<|placeholder|>'*count,1)
                texts.append(text.replace('<|placeholder|>','<|image_pad|>'))
            enc=p.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False)
            enc={key:enc[key].contiguous() for key in ['input_ids','attention_mask']}
            expected=sum(g[0]*g[1]*g[2]//4 for g in grids)
            require(bool(((enc['input_ids']==image_id).sum(1)==expected).all()) and enc['input_ids'].shape[1]<=4096,'Actual multimodal token/grid budget')
            path=out/('query_%04d.pt'%ci);torch.save(enc,path)
            cases.append(dict(query_path=str(path),query_sha256=sha(path),original_image_chunk=chunk,queries=k,tokens_per_query=int(enc['attention_mask'].sum(1).max()),text_sha256=[hashlib.sha256(t.encode()).hexdigest() for t in texts]))
        receipt=dict(id=sid,feature_cells=source['feature_cells'],cases=cases,source_CPU_acceptance_sha256=sha(prior/'inputs'/sid/'acceptance.json'))
        write(out/'acceptance.json',receipt);sources.append(receipt)
        event('SEMANTIC_TEXT_INPUT_SOURCE_ACCEPTED',id=sid,cases=len(cases))
    write(ROOT/'cpu_acceptance.json',dict(status='PASS_ALL25_NEW_CONTEXT_QUERY_TEXT_INPUTS',sources=sources,readout_token_ids={k:v[0] for k,v in ids.items()},original_unique_images=accepted['total_cells'],new_vision_processors=0,new_decodes=0,reference_labels_read=False))

def infer():
    import numpy as np
    import torch
    from peft.tuners.tuners_utils import BaseTunerLayer
    torch.set_num_threads(2)
    accepted=read(ROOT/'cpu_acceptance.json');require(accepted['status']=='PASS_ALL25_NEW_CONTEXT_QUERY_TEXT_INPUTS','CPU gate')
    require(read(ROOT/'independent_text_QA.json')['status']=='PASS_ALL_SERIALIZED_NEW_TEXT_INPUTS','Independent actual text QA gate')
    sys.path.insert(0,str(RUN/'b_score_aligned_package_v4'))
    import engine
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');model,processor,identity=engine.load_model(cfg)
    native=model.get_base_model();core=native.model
    flags=[(p,p.requires_grad) for p in model.parameters()];layers=[m for m in model.modules() if isinstance(m,BaseTunerLayer)]
    require(len(layers)==144,'Actual physical TIME layer inventory')
    records=[];forward_batches=0;target_queries=0;gray_done=False
    try:
        with model.disable_adapter(),torch.inference_mode():
            require(all(m.disable_adapters for m in layers),'BASE semantic role')
            for source in accepted['sources']:
                sid=source['id'];out=ROOT/'features'/sid;out.mkdir(parents=True,exist_ok=False)
                latent=[];scores=[]
                for ci,case in enumerate(source['cases']):
                    chunk=case['original_image_chunk'];require(sha(chunk['path'])==chunk['sha256'] and sha(case['query_path'])==case['query_sha256'],'Frozen saved images/new query changed')
                    original=torch.load(chunk['path'],map_location='cpu',weights_only=True);text=torch.load(case['query_path'],map_location='cpu',weights_only=True);k=case['queries']
                    gpu={key:value.to('cuda:0') for key,value in text.items()}
                    gpu['pixel_values']=original['pixel_values'].repeat(k,1).to('cuda:0')
                    gpu['image_grid_thw']=original['image_grid_thw'].repeat(k,1).to('cuda:0')
                    output=core(**gpu,use_cache=False,return_dict=True)
                    last=output.last_hidden_state[:,-1,:]
                    logits=native.lm_head(last).float()
                    pair=logits[:,[accepted['readout_token_ids']['Yes'],accepted['readout_token_ids']['No']]].cpu()
                    require(torch.isfinite(last).all() and torch.isfinite(pair).all(),'Finite actual language-context feature')
                    latent.append(last.float().cpu().numpy());scores.append(pair.numpy());forward_batches+=1;target_queries+=k
                    saved=out/('context_%04d.pt'%ci)
                    torch.save(dict(language=last.float().cpu(),yes_no=pair),saved)
                    write(out/('context_%04d.json'%ci),dict(status='NEW_CONTEXT_FORWARD_SAVED',path=str(saved),sha256=sha(saved),case=case,utc=utc()))
                    if not gray_done:
                        control={**gpu,'pixel_values':torch.zeros_like(gpu['pixel_values'])}
                        neutral=core(**control,use_cache=False,return_dict=True)
                        neutral_pair=native.lm_head(neutral.last_hidden_state[:,-1,:]).float()[:,[accepted['readout_token_ids']['Yes'],accepted['readout_token_ids']['No']]].cpu()
                        effect=((pair[:,0]-pair[:,1])-(neutral_pair[:,0]-neutral_pair[:,1])).abs()
                        require(bool((effect>1e-4).any()),'No measured visual influence on the semantic readout')
                        write(ROOT/'first_context_visual_readout_diagnostic.json',dict(real_yes_no=pair.tolist(),neutral_yes_no=neutral_pair.tolist(),maximum_logodds_effect=float(effect.max()),scope='Single OOD connectivity check only, not quality or negativeGT',additional_control_forward_batches=1));gray_done=True
                        del control,neutral,neutral_pair
                    del output,last,logits,gpu,original,text,pair
                language=np.concatenate(latent);yesno=np.concatenate(scores)
                require(len(language)==len(yesno)==source['feature_cells'],'Every registered target cell present')
                np.save(out/'language.npy',language);np.save(out/'yes_no.npy',yesno)
                rec=dict(id=sid,cells=len(language),dimension=language.shape[1],language_sha256=sha(out/'language.npy'),yes_no_sha256=sha(out/'yes_no.npy'))
                write(out/'completion.json',rec);records.append(rec);event('SEMANTIC_SOURCE_COMPLETE',id=sid,cells=len(language))
                if len(records)==4:write(ROOT/'engineering4.json',dict(status='PASS_FOUR_REAL_SOURCES_CONTEXT_FEATURES_AND_VISUAL_READOUT_INFLUENCE',sources=records))
    finally:
        # PEFT re-enables LoRA requires_grad on context exit; restore exact flags.
        for parameter,flag in flags:parameter.requires_grad_(flag)
    require(all(not m.disable_adapters for m in layers),'TIME activation not restored')
    require(engine.frozen_identity(model,cfg)==identity['base'] and engine.adapter_identity(model,cfg)==identity['adapter'],'Actual frozen model changed')
    write(ROOT/'completion.json',dict(status='PASS_ALL25_NEW_LANGUAGE_CONTEXT_FEATURES',sources=records,forward_batches=forward_batches,target_queries=target_queries,control_forward_batches=1,new_generation_calls=0,new_optimizer_updates=0,actual_resident_parameters=8782459120,physical_TIME_present_but_disabled_only_inside_forward=True,all_parameter_flags_restored=True))

def qa():
    import torch
    from transformers import AutoTokenizer
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent CPU QA')
    accepted=read(ROOT/'cpu_acceptance.json');cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    pad=tokenizer.convert_tokens_to_ids('<|image_pad|>');count=0;queries=0
    for source in accepted['sources']:
        for case in source['cases']:
            require(sha(case['query_path'])==case['query_sha256'],'Actual serialized new tokens')
            x=torch.load(case['query_path'],map_location='cpu',weights_only=True)
            ids=x['input_ids'];mask=x['attention_mask'];k=case['queries']
            expected=[g[0]*g[1]*g[2]//4 for g in case['original_image_chunk']['grid']]
            require(ids.dtype==mask.dtype==torch.int64 and ids.shape==mask.shape and ids.shape[0]==k,'Batch mapping/dtype')
            require(bool((mask[:,-1]==1).all()) and bool(((mask==0)|(mask==1)).all()),'Last position valid and binary attention')
            for target in range(k):
                row=ids[target][mask[target].bool()].tolist();lengths=[];running=0
                for token in row+[None]:
                    if token==pad:running+=1
                    elif running:lengths.append(running);running=0
                require(lengths==expected,'Ordered actual visual placeholder groups')
                decoded=tokenizer.decode(row,skip_special_tokens=False)
                require('Does frame %d depict a visual highlight'%(target+1) in decoded and 'Answer exactly Yes or No.' in decoded,'Actual target-specific task prefix')
            count+=1;queries+=k
    write(ROOT/'independent_text_QA.json',dict(status='PASS_ALL_SERIALIZED_NEW_TEXT_INPUTS',batches=count,queries=queries,original_vision_QA='Inherited unchanged proof, no repeated processor/decoding',labels_read=False))

if __name__=='__main__':
    try:{'prepare':prepare,'infer':infer,'qa':qa}[sys.argv[1]]()
    except BaseException as error:
        import traceback
        write(ROOT/(sys.argv[1]+'_failure.json'),dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
