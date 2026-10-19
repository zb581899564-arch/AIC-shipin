"""Conditional final559 source-summary generation. No launcher, retries or labels.

CLI: python -B summary_formal_generate.py --registration /absolute/registration.json
Only the registered shared GPU runner may invoke this entry after true admission.
"""
import argparse
from collections import defaultdict
from datetime import datetime,timezone
from fractions import Fraction as F
import os
from pathlib import Path
import re
import sys
import time
import traceback
import torch
from summary_contract import build_pixels,signature,require
from summary_grammar6 import PrefixConstraint,ascii_token_candidates
from summary_output import parse_summary
from summary_generate import read,sha,ref,bound,save,event,W,RUN

SCHEMA='SUMMARY_TWO_VIEW_FORMAL_426_V14'
ROLE='SUMMARY_FINAL'
SOURCE_KIND='ADOPTED_FORMAL_2HZ_ORIGINAL_IMAGE_PATCHES'
LORA_NAME=re.compile(r'language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.summary\.weight$')


def same_ref(first,second):
    return bound(first)==bound(second) and first['sha256']==second['sha256']


def checked_registration(path):
    path=Path(path).resolve(strict=True)
    require(path.is_relative_to(W),'Explicit registration must remain in work root')
    reg=read(path)
    require(reg['schema']==SCHEMA and reg['role']==ROLE and reg['expected_sources']==426 and
            type(reg['expected_windows']) is int and reg['expected_windows']>0,'Explicit426 formal schema/role/counts')
    here=Path(__file__).resolve().parent
    required={'summary_formal_generate.py','summary_formal_output_qa.py','summary_generate.py',
              'summary_contract.py','summary_grammar6.py','summary_output.py'}
    require(required<=set(reg['code']),'All executed formal code dependencies must be bound')
    for name,reference in reg['code'].items():
        require(Path(name).name==name and bound(reference)==here/name,'Actual formal code component differs: '+name)
    cfg=read(bound(reg['model_config_ref']))
    require(bound(reg['model_config_ref'])==RUN/'b_score_aligned_package_v4/config.json','Original fixed model config required')
    require(reg['actual_resident_parameters']==cfg['complete_parameters']==8782459120 and
            type(reg['actual_pipeline_parameters']) is int and
            8782459120<=reg['actual_pipeline_parameters']<=9_000_000_000,'Actual complete parameter accounting')
    frozen=read(bound(reg['final_freeze_ref']))
    require(frozen['status']=='FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS' and
            same_ref(frozen['final_adapter_ref'],reg['final_adapter_ref']),'Fixed final559 freeze identity')
    trained=read(bound(frozen['training_completion_ref']))
    require(trained['status']=='PASS_SUMMARY_FINAL559_SINGLE_EPOCH' and trained['completed_updates']==559 and
            trained['successful_micro']==2236 and same_ref(trained['adapter_weights_ref'],reg['final_adapter_ref']),
            'Actual full single epoch final559 completion required')
    admission=read(bound(reg['production_admission_ref']))
    require(admission['status']=='ADMIT_FIXED_SUMMARY_FINAL559_426' and admission['production_allowed'] is True and
            admission['main_review_completed'] is True and
            same_ref(admission['final_adapter_ref'],reg['final_adapter_ref']) and
            same_ref(admission['final_freeze_ref'],reg['final_freeze_ref']) and
            admission['actual_pipeline_parameters']==reg['actual_pipeline_parameters'],
            'External capability result must explicitly admit this frozen formal model')
    # Bound historical reader dependencies remain explicit; formal pixels are
    # ordinary PTs and neither module is imported or used to decompress them.
    bound(reg['pixel_dictionary_ref']);bound(reg['pixel_codec_ref'])
    directory=Path(reg['output_directory']).resolve()
    require(directory.is_relative_to(W) and directory!=W and isinstance(reg['job_name'],str) and
            re.fullmatch(r'[A-Za-z0-9_-]+',reg['job_name']) and reg['max_gpu_seconds']>0,
            'Explicit new output directory/job/budget')
    deadline=datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))
    require(deadline.tzinfo is not None,'Explicit aware generation deadline')
    return path,reg,cfg,directory


def accepted_inputs(reg):
    gate=read(bound(reg['first_input_acceptance_ref']))
    require(gate['status']=='PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS' and
            gate['sources']==reg['expected_sources'] and gate['windows']==reg['expected_windows'],
            'Complete actual first formal input acceptance required')
    require(same_ref(gate['registration_ref'],reg['input_phase_registration_ref']),
            'Actual CPU input acceptance must bind the original immutable input-phase registration')
    prepared=read(bound(gate['prepared_ref']))
    sources=read(bound(prepared.get('source_catalog_ref',prepared.get('source_catalog'))))['sources']
    require(len(sources)==reg['expected_sources'] and len(prepared['inputs'])==reg['expected_windows'],
            'Exact426 catalog/registered windows denominator')
    catalog={s['id']:s for s in sources}
    require(len(catalog)==426 and set(catalog)=={str(i) for i in range(426)} and
            all(s['kind']==SOURCE_KIND for s in sources),'Formal IDs0..425 and retained original patch kind only')
    by_source=defaultdict(list);requests={};ordered=[]
    for request_ref in prepared['inputs']:
        request=read(bound(request_ref));uid=request['uid'];sid=request['sid']
        require(isinstance(uid,str) and re.fullmatch(r'[A-Za-z0-9_.:-]+',uid) and
                uid not in requests and sid in catalog and request['source_sha256']==catalog[sid]['source_sha256'] and
                request['source_clock_ref']==catalog[sid]['clock'] and
                request['first_new_pixel_text_native_QA'] is True and request['labels_read'] is False,
                'Unique safe window/native source identity and first acceptance')
        requests[uid]=(request_ref,request);by_source[sid].append(uid);ordered.append(uid)
    require(set(by_source)==set(catalog),'Every formal source must have actual accepted windows')
    # Preserve the accepted per-source window order, group sources numerically.
    sequence=[uid for sid in sorted(catalog,key=int) for uid in by_source[sid]]
    require(len(sequence)==len(set(sequence))==reg['expected_windows'],'Complete source-major accepted plan')
    return gate,prepared,catalog,requests,by_source,sequence


def load_formal_source(source):
    """Read one immutable original source at a time, without dictionary/codec use."""
    require(source['kind']==SOURCE_KIND,'Only accepted original formal2Hz patches')
    frames=[];grids=[];ordinals=[]
    for case in source['context_cases']:
        path=bound(case)
        with path.open('rb') as stream:require(stream.read(2)!=b'\x1f\x8b','Formal source must be original uncompressed PT')
        payload=torch.load(path,map_location='cpu',weights_only=True)
        require(set(payload)=={'pixel_values','image_grid_thw','sample_ordinals'},'Original ordinary PT keys only')
        pixels,grid=payload['pixel_values'],payload['image_grid_thw']
        require(grid.dtype==torch.int64 and grid.tolist()==case['grids'] and
                payload['sample_ordinals']==case['samples'] and len(grid)==len(case['samples']) and
                pixels.device.type==grid.device.type=='cpu' and pixels.dtype==torch.float32 and pixels.ndim==2,
                'Actual retained grid/sample/pixel mapping')
        offset=0
        for t,h,w in grid.tolist():
            require(t==1 and h>0 and w>0,'Individual original image observations only')
            frames.append(pixels[offset:offset+h*w]);grids.append([h,w]);offset+=h*w
        require(offset==len(pixels),'Complete retained patch slice accounting')
        ordinals.extend(case['samples'])
    require(frames and len(frames)==source['cells']==len(ordinals) and ordinals==sorted(set(ordinals)) and
            all(g==grids[0] for g in grids),'Complete source-local native observation list')
    return frames,grids[0],ordinals


def reconstruct(request,source,source_values,clock):
    frames,grid,ordinals=source_values;plan=request['plan']
    values,actual=build_pixels(frames,grid,ordinals,clock['normalized_exact_pts'],plan['window_start_exact'],
        plan['window_end_exact'],dict(source_id=request['sid'],source_sha256=source['source_sha256']))
    require(actual==plan,'Accepted formal Overview/Excerpt native plan changed')
    prefix=torch.load(bound(request['prefix_ref']),map_location='cpu',weights_only=True)
    require(set(prefix)=={'input_ids','attention_mask'} and prefix['input_ids'].dtype==torch.int64 and
            prefix['input_ids'].shape==prefix['attention_mask'].shape and prefix['input_ids'].shape[0]==1,
            'Accepted original prefix batch1')
    values.update(prefix)
    require(signature(values)==request['input_signature'],'Runtime composed input differs from first accepted signature')
    return values


def inventory(model,pipeline):
    counts=dict(base=0,summary=0);matrices=0
    for name,p in model.named_parameters():
        require(not p.requires_grad,'Every formal inference parameter must remain frozen')
        if 'lora_' in name:
            match=LORA_NAME.search(name)
            require(match is not None and p.ndim==2 and (p.shape[0] if match[2]=='A' else p.shape[1])==16,
                    'Only144 language rank16 summary matrices allowed')
            counts['summary']+=p.numel();matrices+=1
        else:counts['base']+=p.numel()
    layers=[m for m in model.modules() if hasattr(m,'lora_A')]
    require(counts==dict(base=8767123696,summary=15335424) and matrices==288 and len(layers)==144 and
            model.active_adapter=='summary' and all(set(m.lora_A)=={'summary'} and
            list(m.active_adapters)==['summary'] and not m.disable_adapters for m in layers),
            'Actual formal summary-only adapter inventory/role differs')
    return dict(**counts,resident_parameters=sum(counts.values()),actual_pipeline_parameters=pipeline,
                all_frozen=True,active_adapter='summary',matrices=288,language_targets=144)


def run(registration_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,''),'Only shared runner may expose CUDA for formal generation')
    path,reg,cfg,out=checked_registration(registration_path)
    gate,prepared,catalog,requests,by_source,sequence=accepted_inputs(reg)
    out.mkdir(parents=True,exist_ok=False)
    save(out/'claim.json',dict(role=ROLE,registration_ref=ref(path),pid=os.getpid(),job_name=reg['job_name'],
        final_adapter_ref=reg['final_adapter_ref'],expected_sources=426,expected_windows=reg['expected_windows']))
    started=time.monotonic();outputs=[];source_completions=[];raw_saved=[]
    def deadline():
        require(datetime.now(timezone.utc)<datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')) and
                time.monotonic()-started<reg['max_gpu_seconds'],'No new formal call beyond registered deadline/budget')
    try:
        sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
        from sft_contract import verify_live_gpu_reservation
        from verify_saved_smoke import canonical_frozen_hash
        verify_live_gpu_reservation();deadline()
        import transformers,peft
        from transformers import Qwen3VLForConditionalGeneration,AutoTokenizer
        from peft import PeftModel,get_peft_model_state_dict
        from safetensors.torch import load_file
        require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1' and torch.cuda.is_available(),'Pinned actual Qwen CUDA runtime')
        base=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
            local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
        for parameter in base.parameters():parameter.requires_grad_(False)
        before=canonical_frozen_hash(base,torch)
        require(before['parameters']==8767123696 and before['sha256']==cfg['expected_base_sha256'],'Actual original BASE bytes')
        weights=bound(reg['final_adapter_ref']);old_time=Path(cfg['b_adapter'])/'adapter_model.safetensors'
        require(sha(old_time)==cfg['b_adapter_sha256'],'Original protected TIME weights changed')
        model=PeftModel.from_pretrained(base,str(weights.parent),adapter_name='summary',is_trainable=False).eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        flags=[(p,p.requires_grad)for p in model.parameters()]
        inv=inventory(model,reg['actual_pipeline_parameters'])
        state=get_peft_model_state_dict(model,adapter_name='summary');saved=load_file(str(weights),device='cpu')
        require(set(state)==set(saved) and len(state)==288 and all(torch.equal(state[k].detach().cpu(),saved[k].to(state[k].dtype))for k in state),
                'Actual model exactly equals frozen final559 adapter')
        del state,saved
        tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
        eos=tokenizer.convert_tokens_to_ids('<|im_end|>');require(eos==151645,'Exact trained EOS')
        candidates=ascii_token_candidates(tokenizer)
        for sid in sorted(catalog,key=int):
            source=catalog[sid];clock=read(bound(source['clock']))
            require(clock['source_sha256']==source['source_sha256'],'Original source clock bytes identity')
            source_values=load_formal_source(source);directory=out/('source_'+sid);directory.mkdir(exist_ok=False)
            local_outputs=[]
            for uid in by_source[sid]:
                deadline();request_ref,request=requests[uid]
                values=reconstruct(request,source,source_values,clock)
                duration=F(request['plan']['window_end_exact'])-F(request['plan']['window_start_exact'])
                prefix=int(values['input_ids'].shape[1])
                constraint=PrefixConstraint(tokenizer,prefix,duration,max_segments=6,candidate_token_ids=candidates,
                    eos_token_ids=[eos],allow_empty=True)
                gpu={key:value.to('cuda:0')for key,value in values.items()}
                event(out/'journal.jsonl','BEGIN_GENERATION',uid=uid,sid=sid,role=ROLE,request_ref=request_ref)
                with torch.inference_mode():
                    generated=model.generate(**gpu,max_new_tokens=512,do_sample=False,num_beams=1,num_return_sequences=1,
                        use_cache=True,eos_token_id=eos,pad_token_id=eos,prefix_allowed_tokens_fn=constraint)
                torch.cuda.synchronize();ids=generated[0,prefix:].detach().cpu().tolist()
                raw_path=directory/(uid+'.tokens.json')
                save(raw_path,dict(uid=uid,sid=sid,request_ref=request_ref,generated_ids=ids,model_role=ROLE,
                    model_weights_ref=reg['final_adapter_ref'],actual_prefix_signature=signature({'input_ids':generated[:,:prefix].detach().cpu()}),
                    expected_prefix_signature=signature({'input_ids':values['input_ids']})))
                raw_saved.append(ref(raw_path))
                require(generated.shape[0]==1 and torch.equal(generated[0,:prefix].detach().cpu(),values['input_ids'][0]),'Actual generated prefix identity')
                constraint.assert_complete(ids)
                require(ids and ids[-1]==eos and eos not in ids[:-1] and len(ids)<=512,'Natural complete single EOS/length')
                text=tokenizer.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                segments=parse_summary(text,duration)
                destination=directory/(uid+'.output.json')
                save(destination,dict(uid=uid,sid=sid,request_ref=request_ref,raw_token_ref=ref(raw_path),raw_text=text,
                    generated_ids=ids,model_role=ROLE,model_weights_ref=reg['final_adapter_ref'],
                    parsed_exact_segments=[[str(a),str(b)]for a,b in segments],grammar_stats=constraint.stats))
                output_ref=ref(destination);outputs.append(output_ref);local_outputs.append(output_ref)
                event(out/'journal.jsonl','RAW_ACCEPTED',uid=uid,sid=sid,output_ref=output_ref)
                del gpu,generated,values
            save(directory/'completion.json',dict(status='PASS_FORMAL_SOURCE_SUMMARY_GENERATIONS',sid=sid,
                source_sha256=source['source_sha256'],source_clock_ref=source['clock'],outputs=local_outputs,
                windows=len(by_source[sid]),model_role=ROLE,model_weights_ref=reg['final_adapter_ref']))
            source_completions.append(ref(directory/'completion.json'))
            del source_values,clock
        require(len(outputs)==reg['expected_windows'] and len(source_completions)==426,'Every registered426 source/window exactly once')
        require(canonical_frozen_hash(model,torch)==before and sha(old_time)==cfg['b_adapter_sha256'] and
                sha(weights)==reg['final_adapter_ref']['sha256'] and all(p.requires_grad==flag for p,flag in flags),
                'Frozen base/adapter/original TIME/flags changed')
        inventory(model,reg['actual_pipeline_parameters'])
        save(out/'completion.json',dict(status='PASS_ALL426_FORMAL_SUMMARY_GENERATIONS',model_role=ROLE,
            registration_ref=ref(path),outputs=outputs,source_completion_refs=source_completions,
            sources=426,windows=reg['expected_windows'],model_weights_ref=reg['final_adapter_ref'],
            input_acceptance_ref=reg['first_input_acceptance_ref'],final_freeze_ref=reg['final_freeze_ref'],
            production_admission_ref=reg['production_admission_ref'],base_fingerprint=before,inventory=inv,
            old_TIME_unchanged=True,all_parameter_flags_unchanged=True,optimizer_updates=0,
            elapsed_seconds=time.monotonic()-started,labels_read=False,automatic_retry=False))
    except BaseException as exc:
        save(out/'failure.json',dict(error=repr(exc),traceback=traceback.format_exc(),outputs=outputs,
            first_raw_token_generations=raw_saved,source_completion_refs=source_completions,
            completed_sources=len(source_completions),completed_windows=len(outputs),model_role=ROLE,
            automatic_retry=False,failure_to_empty=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True)
    run(parser.parse_args().registration)
