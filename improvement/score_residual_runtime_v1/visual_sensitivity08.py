"""Two new diagnostic forwards, real vs neutral visual tensors, not generation."""
import sys
import gzip
import io
from common_runtime import *

def cache(path):
    import torch
    with gzip.open(path,'rb') as f:raw=f.read()
    return torch.load(io.BytesIO(raw),map_location='cpu',weights_only=True)

def sig(tensors):
    return {k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest()) for k,v in tensors.items()}

def original():
    import torch
    p=read(ROOT/'protocol.json');ref=p['request_ref']
    require(sha(ref['path'])==ref['sha256'],'Actual adopted external input changed')
    req=read(ref['path']);t=cache(req['token_cache_path']);v=cache(req['original_vision_cache_path'])
    require(sha(req['token_cache_path'])==req['token_cache_sha256'] and sha(req['original_vision_cache_path'])==req['original_vision_cache_sha256'],'Adopted actual lossless input changed')
    combined={**t,'pixel_values_videos':v['pixel_values_videos'],'video_grid_thw':v['video_grid_thw']}
    require(sig(combined)==req['input_evidence']['tensor_signature'],'Actual prior successful input tensors differ')
    return req,combined

def prepare():
    import torch
    from transformers import AutoProcessor
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU diagnostic input preparation')
    req,combined=original();cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True)
    suffix=processor.tokenizer.encode('{"decision":"',add_special_tokens=False)
    require(suffix and '<|video_pad|>' not in processor.tokenizer.decode(suffix),'Only actual new decision prefix text')
    prefix=torch.tensor([suffix],dtype=combined['input_ids'].dtype)
    torch.save(prefix,ROOT/'prefix.pt')
    combined['input_ids']=torch.cat([combined['input_ids'],prefix],dim=1)
    combined['attention_mask']=torch.cat([combined['attention_mask'],torch.ones_like(prefix)],dim=1)
    require(torch.isfinite(combined['pixel_values_videos']).all(),'Finite actual visual input')
    actual=sig(combined);neutral=dict(combined,pixel_values_videos=torch.zeros_like(combined['pixel_values_videos']))
    write(ROOT/'cpu_acceptance.json',dict(status='PASS_FIRST_DIAGNOSTIC_INPUT_REAL_NEUTRAL_SAME_TEXT_GRID',real=actual,neutral=sig(neutral),prefix_sha256=sha(ROOT/'prefix.pt'),source=req['source_name'],note='Normalized zero visual tensors mean neutral input; OOD connectivity control, not a natural negative/ground truth',new_media_decodes=0,new_vision_processor_calls=0,new_prompt_tokenizer_calls=1))

def infer():
    import torch
    import numpy as np
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Explicit GPU parent')
    accepted=read(ROOT/'cpu_acceptance.json');_,combined=original()
    require(sha(ROOT/'prefix.pt')==accepted['prefix_sha256'],'Diagnostic prefix changed')
    prefix=torch.load(ROOT/'prefix.pt',weights_only=True)
    combined['input_ids']=torch.cat([combined['input_ids'],prefix],dim=1)
    combined['attention_mask']=torch.cat([combined['attention_mask'],torch.ones_like(prefix)],dim=1)
    require(sig(combined)==accepted['real'],'First diagnostic input QA binding')
    sys.path.insert(0,str(RUN/'b_score_aligned_package_v4'))
    import engine
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');model,processor,identity=engine.load_model(cfg)
    vectors=[]
    for condition in ('real','neutral'):
        tensors={**combined}
        if condition=='neutral':tensors['pixel_values_videos']=torch.zeros_like(combined['pixel_values_videos'])
        require(sig(tensors)==accepted[condition],'Only declared visual treatment may differ')
        gpu={k:v.to('cuda:0') for k,v in tensors.items()}
        # Same BASE role previously used for positive admission; physical TIME
        # adapter remains resident and is counted, temporarily disabled only here.
        with model.disable_adapter(),torch.inference_mode():
            out=model(**gpu,use_cache=False,return_dict=True,logits_to_keep=1)
            vector=out.logits[0,-1].float().cpu()
        require(torch.isfinite(vector).all(),'Diagnostic forward invalid')
        vectors.append(vector)
        torch.save(vector,ROOT/(condition+'_last_logits.pt'))
        write(ROOT/(condition+'_forward.json'),dict(status='PASS_ONE_NEW_BASE_DIAGNOSTIC_FORWARD',condition=condition,input_signature=accepted[condition],new_generate_calls=0,logit_count=vector.numel(),sha256=sha(ROOT/(condition+'_last_logits.pt'))))
        del out,gpu,tensors
    a,b=vectors;p=a.softmax(0);q=b.softmax(0);kl=(p*(a.log_softmax(0)-b.log_softmax(0))).sum().item()
    result=dict(status='COMPLETE_TWO_NEW_DIAGNOSTIC_FORWARDS',max_absolute_logit_difference=(a-b).abs().max().item(),mean_absolute_logit_difference=(a-b).abs().mean().item(),KL_real_to_neutral=kl,argmax_equal=bool(a.argmax()==b.argmax()),actual_forward_calls=2,new_generate_calls=0,new_optimizer_updates=0,actual_resident_parameters=8782459120,scope='Single external matched input, fixed decision prefix. Detects input influence only; neutral is OOD, not proof of rejection ability/highlight quality or absence of visual reliance elsewhere.')
    require(engine.frozen_identity(model,cfg)==identity['base'] and engine.adapter_identity(model,cfg)==identity['adapter'],'Actual model changed')
    write(ROOT/'completion.json',result)

if __name__=='__main__':
    try:
        {'prepare':prepare,'infer':infer}[sys.argv[1]]()
    except BaseException as error:
        import traceback
        write(ROOT/(sys.argv[1]+'_failure.json'),dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
