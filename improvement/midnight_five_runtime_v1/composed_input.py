"""Adopt frozen successful vision QA, materialize only new prompt tokens.

This is not a new vision encoding or a repeated old QA.  Each compressed vision
payload is bound byte-for-byte before admission; GPU materialization later
checks its actual original tensor signature against this accepted composition.
"""
from pathlib import Path
import hashlib
from mf_common import *

def prepare_composed(root,reg):
    import torch
    from transformers import AutoProcessor
    requests=read(checked(reg['requests_ref']))['entries'];out=root/'cpu_01';out.mkdir(exist_ok=False)
    runtime,token_module,_,_=library();vision_prefix=token_module.vision_prefix
    tokenizer=AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True).tokenizer
    source_lock=read(checked(reg['adopted_source_package_lock_ref']))['files'];entries=[];payloads={}
    for req in requests:
        case=req['case_id'];folder=out/case;folder.mkdir(exist_ok=False)
        mp=checked(req['cache_manifest_ref']);m=read(mp);qp=checked(req['original_first_QA_ref']);qa=read(qp)
        require(source_lock.get(str(mp))==req['cache_manifest_ref']['sha256'] and source_lock.get(str(qp))==req['original_first_QA_ref']['sha256'],'Source manifest/first QA not bound by unchanged successful package closure')
        require(qa['status']=='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE' and qa['first_independent_input_replay'] is True and qa['normal_processor_from_original_RGB_verified'] is True,'Real prior CPU vision processor QA is required')
        require(qa['input_manifest_ref']['sha256']==req['cache_manifest_ref']['sha256'] and qa['input_manifest_ref']['relative']==str(mp.relative_to(Path(req['cache_root']))),'Inherited first QA is for another actual source tensor')
        require(m['private_keys']==['attention_mask','input_ids'] and m['visual_keys']==['pixel_values_videos','video_grid_thw'] and not m['full_signature']['alias_groups'],'Only proven disjoint native private/vision composition is supported')
        base=Path(req['cache_root']);refs=[]
        for r in (m['private_ref'],m['visual_ref']):
            value=dict(r,path=str(base/r['relative']))
            if value['path'] not in payloads:checked(value);payloads[value['path']]=value['sha256']
            require(payloads[value['path']]==value['sha256'],'Shared payload identity conflict')
            refs.append(value)
        old=tensor_load(refs[0]);require(torch.all(old['attention_mask']==1),'Original unpadded actual private tokens required')
        oldtext=tokenizer.decode(old['input_ids'][0].tolist(),skip_special_tokens=False,clean_up_tokenization_spaces=False)
        require(oldtext.count(req['original_prompt'])==1,'Unique frozen original question not found')
        roundtrip=tokenizer.encode(oldtext,add_special_tokens=False);require(roundtrip==old['input_ids'][0].tolist(),'Original expanded token roundtrip differs')
        question=prompt(req);newtext=oldtext.replace(req['original_prompt'],question,1)
        new=tokenizer([newtext],return_tensors='pt',padding=False,truncation=False,add_special_tokens=False)
        require(set(new)=={'input_ids','attention_mask'} and new['input_ids'].shape[1]<=16384 and torch.all(new['attention_mask']==1),'Actual new input token count/keys/padding invalid')
        oldprefix,olde=vision_prefix(old['input_ids'],tokenizer);newprefix,newe=vision_prefix(new['input_ids'],tokenizer)
        require(torch.equal(oldprefix,newprefix) and olde==newe,'Original expanded vision/timestamp prefix changed')
        prefix,sep,suffix=oldtext.partition(req['original_prompt'])
        alternate=tokenizer.encode(prefix+question+suffix,add_special_tokens=False)
        require(alternate==new['input_ids'][0].tolist(),'First independent new prompt construction differs')
        path=folder/'tokens.pt';torch.save(dict(new),path);restored=torch.load(path,map_location='cpu',weights_only=True)
        require(all(torch.equal(new[k],restored[k]) for k in new),'New actual token serialization differs')
        vision={k:{field:m['full_signature']['tensors'][k][field] for field in ('shape','dtype','sha256')} for k in m['visual_keys']}
        signature={**runtime.tensor_signature(dict(new)),**vision}
        evidence=dict(full_tensor_signature=signature,unchanged_vision_tensor_signature=vision,input_tokens=int(new['input_ids'].shape[1]),vision_prefix=olde,
            original_expanded_text_sha256=hashlib.sha256(oldtext.encode()).hexdigest(),new_expanded_text_sha256=hashlib.sha256(newtext.encode()).hexdigest(),
            source_vision_QA_adopted_ref=req['original_first_QA_ref'],new_vision_tensor_deserializations=0,vision_processor_calls=0,media_decodes=0,adopted_payload_refs=refs)
        doc=dict(req,prompt=question,token_ref=ref(path),input_tokens=evidence['input_tokens'],retarget=evidence,original_signature=None)
        save(folder/'input.json',doc)
        save(folder/'first_input_qa.json',dict(status='PASS_FIRST_NEW_PROMPT_INPUT_QA_ADOPT_OLD_NATIVE_VISION',input_ref=ref(folder/'input.json'),native_vision_adopted=True,source_vision_QA_ref=req['original_first_QA_ref'],source_payloads_exact_before_GPU=True,new_vision_tensor_deserializations=0,vision_processor_calls=0,media_decodes=0,first_qa_not_repeated=True))
        entries.append(dict(case_id=case,input_ref=ref(folder/'input.json'),first_qa_ref=ref(folder/'first_input_qa.json')))
        print('COMPOSED_INPUT_QA',len(entries),len(requests),case,flush=True)
    require(not torch.cuda.is_initialized(),'CPU-only composition initialized CUDA')
    save(out/'completion.json',dict(status='PASS_ALL_FIRST_INPUT_QA',entries=entries,actual_count=len(entries),registration_ref=ref(root/'registration.json'),adopted_vision_QA_not_repeated=True,new_vision_tensor_deserializations=0,vision_processor_calls=0,media_decodes=0,exact_bound_payload_count=len(payloads)))
