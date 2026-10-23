"""First new frozen VERIFY decisions and exact BASE semantic features; no B0 rerun."""
import math
import sys
import time
from pathlib import Path
import numpy as np
import torch
from baseline_bridge57_common import ROOT,RUN,read,ref,save,checked,legacy_runtime,verify_modules


def verify(model,processor,rt):
    contract,grammar,_=verify_modules();accepted=read(ROOT/'verify_CPU_completion.json')
    folder=ROOT/'verify_outputs';folder.mkdir();results=[]
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    candidates=grammar.candidate_tokens(processor.tokenizer,contract.responses())
    for index,row in enumerate(accepted['cases']):
        req=read(checked(row['request']));cpu=read(checked(row['CPU']))
        with np.load(checked(cpu['encoded']),allow_pickle=False) as values:
            x={k:torch.from_numpy(values[k].copy()) for k in values.files}
        x.update(cpu['non_tensor_inputs'])
        if rt.tensor_signature(x)!=cpu['detail']['tensor_signature']:raise ValueError('Actual new VERIFY input differs from accepted CPU')
        prefix=int(x['input_ids'].shape[1]);constraint=grammar.VerifyConstraint(processor.tokenizer,prefix,req,eos,candidates)
        target=folder/req['request_id'];target.mkdir();start=time.monotonic()
        save(target/'request.json',dict(request=row['request'],CPU=row['CPU'],prefix=prefix))
        with torch.inference_mode():
            output=model.generate(**{k:v.cuda() if torch.is_tensor(v) else v for k,v in x.items()},
                do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint,
                return_dict_in_generate=True,output_scores=True)
        torch.cuda.synchronize();tokens=output.sequences[0,prefix:]
        text=processor.tokenizer.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        scores=[float(s[0,int(t)]) for s,t in zip(output.scores,tokens)]
        save(target/'raw.json',dict(text=text,tokens=tokens.tolist(),scores=[s if math.isfinite(s) else str(s) for s in scores],
            prefix=prefix,eos=eos,seconds=time.monotonic()-start))
        if not all(math.isfinite(s) for s in scores) or len(scores)!=len(tokens):raise ValueError('New VERIFY token/score count invalid')
        constraint.assert_complete(tokens);decision=contract.resolve(text,req,execution_status='MODEL_OK')
        save(target/'acceptance.json',dict(decision=decision,raw=ref(target/'raw.json'),input=row))
        results.append(ref(target/'acceptance.json'))
        print('FULL_BASELINE_VERIFY_ACCEPTED',index+1,len(accepted['cases']),flush=True)
        del output,tokens,x
    save(ROOT/'verify_GPU_completion.json',dict(state='ALL_FIRST_VERIFY_DECISIONS_COMPLETE',outputs=results))


def semantic(model):
    from peft.tuners.tuners_utils import BaseTunerLayer
    accepted=read(ROOT/'semantic_CPU_completion.json');folder=ROOT/'semantic_outputs';folder.mkdir()
    native=model.get_base_model();core=native.model;layers=[m for m in model.modules() if isinstance(m,BaseTunerLayer)]
    if len(layers)!=144:raise ValueError('Original actual adapter module count differs')
    parts=[]
    with model.disable_adapter(),torch.inference_mode():
        if not all(m.disable_adapters for m in layers):raise ValueError('Actual BASE role not enabled')
        for index,row in enumerate(accepted['chunks']):
            data=torch.load(checked(row['input']),map_location='cpu',weights_only=True);k=row['queries']
            x={key:data[key].cuda() for key in ['input_ids','attention_mask']}
            x['pixel_values']=data['pixel_values'].repeat(k,1).cuda();x['image_grid_thw']=data['image_grid_thw'].repeat(k,1).cuda()
            output=core(**x,use_cache=False,return_dict=True);last=output.last_hidden_state[:,-1,:]
            logits=native.lm_head(last).float()
            pair=logits[:,[accepted['words']['Yes'],accepted['words']['No']]]
            path=folder/f'context_{index:04d}.pt'
            with path.open('xb') as out:torch.save(dict(language=last.float().cpu(),yes_no=pair.cpu(),input=row['input'],samples=row['samples']),out)
            if not torch.isfinite(last).all() or not torch.isfinite(pair).all():raise ValueError('New saved semantic outputs nonfinite')
            parts.append(ref(path));print('FULL_BASELINE_SEMANTIC_ACCEPTED',index+1,len(accepted['chunks']),flush=True)
            del output,last,logits,pair,x,data
    if any(m.disable_adapters for m in layers):raise ValueError('Original TIME role not restored')
    save(ROOT/'semantic_GPU_completion.json',dict(state='ALL_FIRST_SEMANTIC_FEATURES_COMPLETE',outputs=parts,
        actual_batches=len(parts),actual_target_queries=accepted['cells'],BASE_role_only=True))


def main():
    rt=legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();torch.set_num_threads(2)
    for value in read(ROOT/'source_input_lock.json')['code'].values():checked(value)
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');model,processor,identity=rt.b_engine.load_model(cfg)
    if identity['logical_parameters']!=8782459120:raise ValueError('Actual original model parameters differ')
    save(ROOT/'model_identity.json',identity)
    verify(model,processor,rt);semantic(model)
    if rt.b_engine.frozen_identity(model,cfg)!=identity['base'] or rt.b_engine.adapter_identity(model,cfg)!=identity['adapter']:
        raise ValueError('Original frozen model/adapter changed')
    save(ROOT/'gpu_completion.json',dict(state='FULL_EXTERNAL_BASELINE_BRANCH_MODELS_COMPLETE',
        VERIFY_calls=len(read(ROOT/'verify_GPU_completion.json')['outputs']),
        semantic_batches=read(ROOT/'semantic_GPU_completion.json')['actual_batches'],
        semantic_queries=read(ROOT/'semantic_GPU_completion.json')['actual_target_queries'],
        actual_resident_base_and_TIME_parameters=8782459120,no_training=True))


if __name__=='__main__':main()
