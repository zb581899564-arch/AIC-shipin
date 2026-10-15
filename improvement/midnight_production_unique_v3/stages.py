import argparse
from contextlib import nullcontext
import datetime as dt
import hashlib,json,os,socket,subprocess,sys,time,traceback
from pathlib import Path
from mf_common import *
from alias_contract import accepted_cpu

def setup(stage):
    require(socket.gethostname()=='inspur-NP5570M5','Unexpected training host')
    root=ROOT/stage;reg=read(root/'registration.json')
    for path,digest in reg['code_files'].items():require(sha(path)==digest,'New frozen code changed')
    return root,reg

def prepare(stage):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU prep hides only own CUDA')
    root,reg=setup(stage)
    if reg.get('input_QA_mode')=='ADOPT_FROZEN_VISION_COMPOSE_NEW_TOKENS':
        from composed_input import prepare_composed
        return prepare_composed(root,reg)
    requests=read(checked(reg['requests_ref']))['entries'];out=root/'cpu_01';out.mkdir(exist_ok=False)
    import torch
    from transformers import AutoProcessor
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True)
    runtime,tokens,_,codec=library();entries=[]
    for req in requests:
        case=req['case_id'];folder=out/case;folder.mkdir(exist_ok=False)
        values=original(req)
        sig=runtime.tensor_signature(values)
        expected=req.get('full_signature')
        if expected is not None:require(codec.signature(values)==expected,'Adopted exact source tensor signature differs')
        question=prompt(req)
        new,combined,evidence=tokens.retarget(values,processor.tokenizer,req['original_prompt'],question,runtime.tensor_signature)
        path=folder/'tokens.pt';torch.save(new,path)
        # Independent reconstruction partitions the complete expanded prompt,
        # rather than invoking retarget a second time or running a vision encoder.
        old_text=processor.tokenizer.decode(values['input_ids'][0].tolist(),skip_special_tokens=False,clean_up_tokenization_spaces=False)
        prefix,separator,suffix=old_text.partition(req['original_prompt'])
        require(separator and req['original_prompt'] not in suffix,'Unique old prompt must be bound')
        alternate=processor.tokenizer.encode(prefix+question+suffix,add_special_tokens=False)
        require(alternate==new['input_ids'][0].tolist() and torch.all(new['attention_mask']==1),'First independent new token QA differs')
        restored=torch.load(path,map_location='cpu',weights_only=True)
        require(all(torch.equal(new[k],restored[k]) for k in new),'New token serialization differs')
        require(runtime.tensor_signature(combined)==evidence['full_tensor_signature'],'Actual full input differs')
        doc=dict(req,prompt=question,token_ref=ref(path),input_tokens=int(new['input_ids'].shape[1]),retarget=evidence,original_signature=sig)
        save(folder/'input.json',doc)
        save(folder/'first_input_qa.json',dict(status='PASS_FIRST_NEW_PROMPT_INPUT_QA_ADOPT_OLD_NATIVE_VISION',input_ref=ref(folder/'input.json'),native_vision_adopted=True,vision_processor_calls=0,media_decodes=0,first_qa_not_repeated=True))
        entries.append(dict(case_id=case,input_ref=ref(folder/'input.json'),first_qa_ref=ref(folder/'first_input_qa.json')))
        print('PREPARED',len(entries),len(requests),case,flush=True)
        del values,new,combined,restored
    require(not torch.cuda.is_initialized(),'CPU child initialized CUDA')
    save(out/'completion.json',dict(status='PASS_ALL_FIRST_INPUT_QA',entries=entries,actual_count=len(entries),registration_ref=ref(root/'registration.json'),media_decodes=0,vision_processor_calls=0))

def infer(stage):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'GPU parent CUDA cannot be empty')
    root,reg=setup(stage);cpu,aliases=accepted_cpu(reg)
    out=root/'gpu_01';out.mkdir(exist_ok=False);save(out/'started.json',dict(pid=os.getpid(),utc=utc(),registration_ref=ref(root/'registration.json')))
    import torch
    from grammar import Constraint
    runtime,_,_,_=library()
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');model,processor,identity=runtime.b_engine.load_model(cfg);model.requires_grad_(False)
    require(sum(p.numel() for p in model.parameters())==PARAMETERS,'Actual resident base+adapter exceeds/differs from frozen count')
    require(identity['base']['sha256']==cfg['expected_base_sha256'] and identity['adapter']['sha256']==cfg['b_adapter_sha256'],'Frozen model identity differs')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();require(read(HOME/'improvement_round1/active_gpu_job.json')['name']==reg['gpu_job_name'],'Unique shared GPU job binding differs')
    save(out/'model_identity.json',dict(identity=identity,actual_parameters=PARAMETERS,training=False))
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos);entries=[];actual_count=0;done_by_case={}
    for row in cpu['entries']:
        require(dt.datetime.now(dt.timezone.utc)<DEADLINE,'No new call after tonight deadline')
        req=read(checked(row['input_ref']));checked(row['first_qa_ref']);case=req['case_id'];folder=out/case;folder.mkdir(exist_ok=False)
        if case in aliases:
            alias=aliases[case];canonical_ref=done_by_case[alias['canonical_case_id']];canonical=read(checked(canonical_ref))
            save(folder/'done.json',dict(status='ADOPTED_IDENTICAL_NEW_INPUT_MODEL_OUTPUT_NO_NEW_CALL',actual_model_call=False,case_id=case,alias_of=alias['canonical_case_id'],canonical_model_done_ref=canonical_ref,identical_input_equality_ref=reg['identical_input_alias_table_ref'],input_ref=row['input_ref'],first_input_qa_ref=row['first_qa_ref'],raw_ref=canonical['raw_ref'],parsed=canonical['parsed']))
            done_ref=ref(folder/'done.json');done_by_case[case]=done_ref
            entries.append(dict(case_id=case,decision_ref=done_ref,input_ref=row['input_ref'],actual_model_call=False,alias_of=alias['canonical_case_id']))
            append(out/'journal.jsonl',dict(event='ALIAS_ADOPTED_NO_MODEL_CALL',case_id=case,canonical_case_id=alias['canonical_case_id'],utc=utc()))
            continue
        values=original(req);new=torch.load(checked(req['token_ref']),map_location='cpu',weights_only=True)
        vision={k:v for k,v in values.items() if k not in ('input_ids','attention_mask')};combined={**new,**vision}
        require(runtime.tensor_signature(combined)==req['retarget']['full_tensor_signature'],'GPU-facing exact input binding differs')
        gpu={k:v.to(model.device) for k,v in combined.items()};constraint=Constraint(processor.tokenizer,req['input_tokens'],len(req['candidate_events']),eos)
        before=[bool(m.disable_adapters) for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')]
        require(before==[False]*144,'TIME layers must enter enabled/frozen')
        append(out/'journal.jsonl',dict(event='BEGIN',case_id=case,utc=utc()))
        started=time.monotonic()
        try:
            with model.disable_adapter():
                inside=[bool(m.disable_adapters) for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')]
                require(inside==[True]*144,'BASE-only role must disable exactly all144 layers')
                with torch.inference_mode():
                    generated=model.generate(**gpu,do_sample=False,max_new_tokens=192,prefix_allowed_tokens_fn=constraint,return_dict_in_generate=True,output_scores=False)
                torch.cuda.synchronize();ids=generated.sequences[0,req['input_tokens']:].tolist()
        finally:model.requires_grad_(False)
        after=[bool(m.disable_adapters) for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')]
        require(after==before and not any(p.requires_grad for p in model.parameters()),'Adapter/gradient state not restored')
        text=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        save(folder/'raw.json',dict(case_id=case,raw_output=text,output_token_ids=ids,input_tokens=req['input_tokens'],seconds=time.monotonic()-started,eos_token_ids=eos,actual_model_call=True,adapter_before=before,adapter_inside=inside,adapter_after=after,input_ref=row['input_ref'],first_input_qa_ref=row['first_qa_ref']))
        parsed=constraint.finish(ids)
        save(folder/'done.json',dict(actual_model_call=True,case_id=case,parsed=parsed,raw_ref=ref(folder/'raw.json'),input_ref=row['input_ref'],first_input_qa_ref=row['first_qa_ref']))
        done_by_case[case]=ref(folder/'done.json');actual_count+=1
        entries.append(dict(case_id=case,decision_ref=done_by_case[case],input_ref=row['input_ref'],actual_model_call=True))
        append(out/'journal.jsonl',dict(event='ACCEPTED',case_id=case,done_ref=ref(folder/'done.json'),utc=utc()))
        print('ACCEPTED',len(entries),len(cpu['entries']),case,flush=True)
        del values,new,vision,combined,gpu,generated
    final=dict(base=runtime.b_engine.frozen_identity(model,cfg),adapter=runtime.b_engine.adapter_identity(model,cfg))
    require(final==dict(base=identity['base'],adapter=identity['adapter']),'Model byte identity changed without training')
    require(actual_count==reg['expected_actual_model_calls'] and len(entries)==reg['logical_count'],'Actual new-call denominator differs')
    save(out/'completion.json',dict(status='PASS_ALL_NEW_INFERENCE_NOT_QUALITY',actual_model_calls=actual_count,logical_cases=len(entries),adopted_identical_input_aliases=len(aliases),identical_input_alias_table_ref=reg['identical_input_alias_table_ref'],actual_parameters=PARAMETERS,entries=entries,identity_ref=ref(out/'model_identity.json'),journal_ref=ref(out/'journal.jsonl'),weights_unchanged=True))

def output_qa(stage):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Output QA must be CPU-only')
    root,reg=setup(stage);gpu=read(root/'gpu_01/completion.json');out=root/'output_qa_01';out.mkdir(exist_ok=False)
    from transformers import AutoProcessor
    tokenizer=AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True).tokenizer
    resource=RUN/'controller'/(reg['gpu_job_name']+'.resource.json');terminal=read(resource)
    ledger=[json.loads(s) for s in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip()]
    require(terminal['status']=='completed' and terminal['exit_code']==0 and [v for v in ledger if v['name']==reg['gpu_job_name']]==[terminal],'Unique natural terminal not proven')
    cpu,aliases=accepted_cpu(reg);entries=[];qa_by_case={};actual_qa_count=0
    for row in gpu['entries']:
        done=read(checked(row['decision_ref']));req=read(checked(row['input_ref']))
        if row['case_id'] in aliases:
            alias=aliases[row['case_id']];canonical_qa=qa_by_case[alias['canonical_case_id']]
            previous=read(checked(canonical_qa));canonical=read(checked(done['canonical_model_done_ref']))
            require(done['actual_model_call'] is False and done['alias_of']==alias['canonical_case_id'],'Alias is not a new model call')
            require(previous['done_ref']==done['canonical_model_done_ref'] and done['parsed']==canonical['parsed']==previous['parsed'],'Alias must reuse exactly already QA accepted canonical output')
            proof=out/(row['case_id']+'.json');save(proof,dict(status='PASS_IDENTICAL_INPUT_ALIAS_NATIVE_APPLICATION_QA',done_ref=row['decision_ref'],canonical_model_done_ref=done['canonical_model_done_ref'],canonical_output_QA_ref=canonical_qa,identical_input_equality_ref=reg['identical_input_alias_table_ref'],first_input_qa_ref=done['first_input_qa_ref'],parsed=done['parsed'],CPU_only=True,new_model_calls=0))
            kept={k:v for k,v in req.items() if k not in ('retarget','original_signature','full_signature','original_prompt','prompt')}
            entries.append(dict(kept,decision_ref=row['decision_ref'],output_qa_ref=ref(proof),actual_model_call=False,alias_of=alias['canonical_case_id'],canonical_model_done_ref=done['canonical_model_done_ref'],canonical_output_QA_ref=canonical_qa,identical_input_equality_ref=reg['identical_input_alias_table_ref']))
            continue
        raw=read(checked(done['raw_ref']))
        require(done['actual_model_call'] is True and raw['actual_model_call'] is True,'Canonical must have a real new call')
        text=tokenizer.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        parsed=validate(json.loads(text),len(req['candidate_events']))
        require(text==raw['raw_output']==json.dumps(parsed,separators=(',',':')) and parsed==done['parsed'],'First independent output decode/parser differs')
        require(raw['adapter_before']==raw['adapter_after']==[False]*144 and raw['adapter_inside']==[True]*144,'Actual activation contract differs')
        proof=out/(row['case_id']+'.json');save(proof,dict(status='PASS_FIRST_INDEPENDENT_OUTPUT_QA',done_ref=row['decision_ref'],raw_ref=done['raw_ref'],first_input_qa_ref=done['first_input_qa_ref'],parsed=parsed,CPU_only=True,new_model_calls=0,model_calls=0,vision_encodes=0))
        kept={k:v for k,v in req.items() if k not in ('retarget','original_signature','full_signature','original_prompt','prompt')}
        qa_by_case[row['case_id']]=ref(proof);actual_qa_count+=1
        entries.append(dict(kept,decision_ref=row['decision_ref'],output_qa_ref=ref(proof),actual_model_call=True))
    save(root/'completion.json',dict(status='COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY',stage=stage,actual_parameters=PARAMETERS,actual_model_calls=gpu['actual_model_calls'],logical_cases=len(entries),adopted_identical_input_aliases=len(aliases),first_model_output_QA_count=actual_qa_count,alias_application_QA_count=len(aliases),alias_application_QA_complete=True,identical_input_alias_table_ref=reg['identical_input_alias_table_ref'],adopted_CPU_completion_ref=reg['adopted_CPU_completion_ref'],first_input_QA_complete=True,first_output_QA_complete=True,entries=entries,structural_skips=read(checked(reg['requests_ref'])).get('structural_skips',[]),unique_gpu_terminal_ref=ref(resource),reference_labels_in_inference=False,old_successful_calls_repeated=0,original_vision_QA_adopted=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','infer','output_qa']);p.add_argument('--stage',required=True);args=p.parse_args()
    try:globals()[args.operation](args.stage)
    except BaseException as e:
        path=ROOT/args.stage/(args.operation+'_failure.json')
        if not path.exists():save(path,dict(error=repr(e),traceback=traceback.format_exc(),utc=utc(),automatic_retry=False,preserve_all_successful=True))
        raise
