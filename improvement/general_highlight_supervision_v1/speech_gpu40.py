"""First frozen8B whole-source speech calls; no adapters, optimizer or video inference."""
from pathlib import Path
import sys
import time
import torch

from common import ROOT,WORK,read,ref,save
from pilot_common28 import checked,RUN
from score_contract39 import Constraint,ScorePattern,candidates

TARGET=ROOT/'speech_rank42'


def main():
    from transformers import AutoTokenizer,Qwen3VLForConditionalGeneration
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation();torch.set_num_threads(2)
    reg=read(TARGET/'registration.json');lock=read(TARGET/'source_input_lock.json')
    for record in lock['code'].values():checked(record)
    cfg=read(checked(reg['model_config']))
    tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    model=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
        local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model.eval().requires_grad_(False);before=canonical_frozen_hash(model,torch)
    if before['sha256']!=cfg['expected_base_sha256']:raise ValueError('Protected frozen base identity differs')
    count=sum(p.numel() for p in model.parameters())
    if count>8782557449 or reg['full_candidate_parameters']>9000000000:raise ValueError('Actual parameter combination exceeds budget')
    tokens=candidates(tokenizer);eos=tokenizer.convert_tokens_to_ids('<|im_end|>')
    if eos!=151645:raise ValueError('Original tokenizer EOS changed')
    (TARGET/'outputs').mkdir();outputs=[];started=time.monotonic()
    for record in reg['cases']:
        case=read(checked(record));values=torch.load(checked(case['tokens']),map_location='cpu',weights_only=True)
        if tokenizer.encode(case['expanded_text'],add_special_tokens=False)!=values['input_ids'][0].tolist():
            raise ValueError('Actual first text input differs from CPU acceptance')
        prefix=values['input_ids'].shape[1]
        constraint=Constraint(tokenizer,prefix,case['known'],tokens,eos)
        with torch.inference_mode():
            output=model.generate(**{k:v.cuda() for k,v in values.items()},max_new_tokens=256,do_sample=False,
                num_beams=1,use_cache=True,eos_token_id=eos,pad_token_id=eos,prefix_allowed_tokens_fn=constraint)
        tail=output[0,prefix:].detach().cpu().tolist()
        path=TARGET/'outputs'/(case['sid']+'_'+case['condition']+'.json')
        text=tokenizer.decode(tail[:-1] if tail and tail[-1]==eos else tail,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        raw=dict(sid=case['sid'],condition=case['condition'],input=record,generated_token_ids=tail,
            decoded_text=text,EOS_observed=bool(tail and tail[-1]==eos),new_frozen8B_text_only_call=True)
        save(path,raw)
        if not raw['EOS_observed']:raise ValueError('First model output incomplete; raw retained')
        scores=ScorePattern(case['known']).parse(text)
        save(path.with_name(path.stem+'_accepted.json'),dict(raw=ref(path),scores=scores))
        outputs.append(ref(path))
        print('WHOLE_SOURCE_TEXT_ACCEPTED',case['sid'],case['condition'],scores,flush=True)
    after=canonical_frozen_hash(model,torch)
    if before!=after:raise ValueError('Frozen base changed during inference')
    checked(read(ROOT/'media24/registration.json')['protected_baseline'])
    save(TARGET/'gpu_completion.json',dict(state='FIRST_WHOLE_SOURCE_SPEECH_RANK_COMPLETE',
        outputs=outputs,new8B_calls=len(outputs),new_training=0,actual_base_parameters=count,
        full_candidate_parameters=reg['full_candidate_parameters'],base_unchanged=True,
        no_TIME_or_spatial_changes=True,pure_text=True,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        seconds=time.monotonic()-started))


if __name__=='__main__':main()
