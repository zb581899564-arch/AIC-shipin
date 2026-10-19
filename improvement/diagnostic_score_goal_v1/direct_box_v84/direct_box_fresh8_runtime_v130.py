"""Conditional NEW8 CPU/GPU/review workers. No work on import.

CLI --root NEWROOT --registration NEWROOT/fresh8_registration_130.json
    --stage cpu|gpu|review. Never a launcher or automatic production entry.
Only an actual128 PASS and separately registered fresh8 admission may execute.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback
import urllib.request
import direct_box_fresh8_contract_v130 as contract

WORK=Path('/home/inspur/aic_video_work')
CPU_PASS='PASS_FRESH8_ALL8_B0_AND_DIRECT_INPUTS_FIRST_CPU_QA_V130'
GPU_COMPLETE='COMPLETE_FRESH8_BASE8_DIRECT8_RAW_NOT_QUALITY_V130'
RAW_PASS='PASS_FRESH8_BASE_AND105_RAW_FIRST_CPU_QA_V130'
QUALITY_PASS='PASS_FRESH8_RELATIVE_CRITIC_FILE_CONFIRMATION_V130'
QUALITY_STOP='STOP_FRESH8_RELATIVE_CRITIC_FILE_CONFIRMATION_V130'
GATE=dict(mean_gain_min=.01,improved_min=2,worst_loss_max=.10,true_reject_min=1,true_retain_min=1,
    invalid_max=0,strictly_beat=['GEOM11','ALWAYS124','OLD70_GEOM','OLD47_GEOM11','OLD33_GEOM13'])


def require(v,m):
    if not v:raise ValueError(m)


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def ref(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def bound(r):
    p=Path(r['path']).resolve();require(set(r)=={'path','sha256'} and p.is_relative_to(WORK) and p.is_file() and sha(p)==r['sha256'],'Bound artifact changed: '+str(p));return p
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def load(r):return read(bound(r))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def data(p,b):
    with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return ref(p)
def tensor(p,v,torch):
    b=io.BytesIO();torch.save(v,b);return data(p,b.getvalue())
def module(r,name):
    p=bound(r);sys.path.insert(0,str(p.parent));s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def configuration(root,rp):
    root=Path(root).resolve();rp=Path(rp).resolve();r=read(rp)
    require(root.is_relative_to(WORK) and rp==root/'fresh8_registration_130.json' and r['root']==str(root)
        and r['schema']==contract.SCHEMA and bound(r['runtime_code'])==Path(__file__).resolve()
        and bound(r['contract_code'])==Path(contract.__file__).resolve(),'Independent exact130 root/code')
    require(r['quality_gate']==GATE and r['source_plan_sha256']==contract.validate_sources(r['sources'])
        and r['origin_url']==contract.ORIGIN and r['archive_bytes']==contract.ARCHIVE_BYTES
        and r['max_range_payload_bytes']==304262,'Fixed source plan/gates before fresh outputs')
    q=load(r['development_result']);require(q['status']==contract.DEVELOPMENT_PASS and q['admitted_arms']==['JOINT']
        and q['state']==r['critic_state'] and q['exact_save_reload'] is True and q['additional_parameters']==135393
        and q['pipeline_parameters']==contract.PIPELINE and all(q[k]==r[k] for k in ('training_completion','adapter_weights','head_weights')),
        'Only actual128 frozen39 development PASS/state and same final105 model')
    admission=load(r['fresh8_admission'])
    contract.validate_development(admission,q,result_ref=r['development_result'],
        model_refs={k:r[k] for k in ('training_completion','adapter_weights','head_weights')},
        critic_refs={k:r[k] for k in ('critic_state','critic_code')})
    require(admission['source_plan_sha256']==r['source_plan_sha256'] and admission['quality_gate']==GATE,'Actual new8 purpose, exact source/gate lock')
    for k in ('critic_state','critic_code','training_completion','adapter_weights','adapter_config','head_weights','math105_code','GPU105_code',
        'input_code87','original_baseline_code','original_baseline_encoder_code','baseline_geometry_code','geometry31_code','model_config',
        'raw_QA_code105','pair_common_code','sft_contract_code','identity_code','identity_registry','old_control_result70','policy33_code'):
        bound(r[k])
    require(load(r['purpose_reply'])['answer']=='仅学生参赛/科研，不涉及商业产品','Original actual student NC purpose retained')
    bound(r['license_notice'])
    for name,expected in contract.MEMBER_REFS.items():
        p=bound(r['source_metadata'][name]);require(p.stat().st_size==expected['bytes'] and r['source_metadata'][name]['sha256']==expected['sha256'],'Original cached metadata member')
    trained=load(r['training_completion']);require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY'
        and trained['completed_updates']==778 and trained['actual_training_forwards']==3112 and trained['total_adopted_plus_new_updates']==798
        and all(trained[k]==r[k] for k in ('adapter_weights','head_weights')),'Same complete final105 only')
    original=load(trained['GPU_registration'])
    require(original['GPU_code']==r['GPU105_code'] and original['math_code']==r['math105_code']
        and original['review_code']==r['raw_QA_code105'] and original['preparation_code']==r['input_code87']
        and original['old_control_result70']==r['old_control_result70'],'Actual frozen105 runtime/QA/control ancestry')
    adapter=load(r['adapter_config'])
    require(bound(r['adapter_config']).parent==bound(r['adapter_weights']).parent==Path(trained['adapter_directory']).resolve()
        and adapter['r']==8 and adapter['lora_alpha']==16 and adapter['lora_dropout']==0 and adapter['bias']=='none',
        'Exact saved final105 adapter configuration/scale/directory')
    return root,r,rp


def deadline(r,started,stage):
    require(time.monotonic()-started<r[stage+'_max_seconds'] and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(r['deadline_utc'].replace('Z','+00:00')),'Explicit130 stage budget/deadline')


def read_input(reference,helper,torch):
    q=load(reference);b=gzip.decompress(bound(q['encoded']).read_bytes());v=torch.load(io.BytesIO(b),map_location='cpu',weights_only=True)
    require(set(v)=={'input_ids','attention_mask','pixel_values','image_grid_thw'} and helper.signature(v)==q['input_signature']
        and v['image_grid_thw'].tolist()==q['image_grid_thw'] and q['reference_or_target_in_prompt'] is False
        and not any(k in q for k in ('target','labels','original_reference_xywh')),'Actual accepted GT-free F4/owner')
    return v,q


def cpu(root,r,rp):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU masked')
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    started=time.monotonic();helper=module(r['input_code87'],'_fresh130_input87');baseline=module(r['original_baseline_code'],'_fresh130_original_BASE')
    encoder=module(r['original_baseline_encoder_code'],'_fresh130_original_encoder');cfg=load(r['model_config'])
    baseprocessor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    directprocessor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    registry=load(r['identity_registry']);index=load(r['source_metadata']['zip_index.json'])
    out=root/'inputs';out.mkdir(exist_ok=False);sources=[];qa=[];network_bytes=0
    def fetch(offset,length):
        nonlocal network_bytes
        deadline(r,started,'CPU')
        request=urllib.request.Request(r['origin_url'],headers={'Range':f'bytes={offset}-{offset+length-1}','Accept-Encoding':'identity'})
        with urllib.request.urlopen(request,timeout=45) as response:
            require(response.status==206,'Range rejected; never consume a full archive response')
            payload=response.read(length+1)
            contract.range_response(response.status,response.headers.get('Content-Range'),payload,offset=offset,length=length)
        network_bytes+=len(payload);require(network_bytes<=304262,'Exact small range budget');return payload
    for i,row in enumerate(r['sources']):
        deadline(r,started,'CPU');old=index[row['member']]
        require(all(old[k]==row[k] for k in ('header_offset','compressed_bytes','bytes','crc32','compression')),'Fixed original index metadata')
        header=fetch(row['header_offset'],30);data(out/(str(i)+'.header'),header)
        packed=fetch(contract.member_data_offset(header,row),row['compressed_bytes']);data(out/(str(i)+'.packed'),packed)
        raw=contract.unpack_member(packed,row);jpeg=data(out/(str(i)+'.jpeg'),raw)
        with Image.open(io.BytesIO(raw)) as original:
            require(original.getexif().get(274,1)==1,'No silent EXIF rotation');image=original.convert('RGB');rgb=np.asarray(image).copy()
        W,H=image.size;require(W>0 and H>0 and rgb.shape==(H,W,3) and rgb.dtype==np.uint8,'Actual original RGB/native dimensions')
        rgbsha=hashlib.sha256(rgb.tobytes()).hexdigest();gray=np.asarray(image.convert('L').resize((9,8)))
        dh=sum(int(v)<<j for j,v in enumerate((gray[:,1:]>gray[:,:-1]).reshape(-1)))
        identity=contract.check_identity(row['source_id'],jpeg['sha256'],rgbsha,dh,registry)
        require(not any(jpeg['sha256']==s['source_sha256'] or rgbsha==s['RGB_sha256'] or (dh-s['dhash9x8']==0) or (dh^s['dhash9x8']).bit_count()<=6 for s in sources),'No within-new8 exact/near duplicate; no replacement')
        buf=io.BytesIO();np.save(buf,rgb,allow_pickle=False);rgbref=data(out/(str(i)+'.RGB.npy'),buf.getvalue())
        messages=[]
        class Capture:
            max_pixels=131072
            def _generate(self,content,limit):require(limit==128,'Original BASE128');messages.extend(content);return ''
        baseline.Qwen3VL.predict_focus(Capture(),image,[16,9],128)
        bv,btext=encoder.encode(baseprocessor,messages);bv=dict(bv)
        independent,_=encoder.encode(baseprocessor,messages)
        require(helper.signature(bv)==helper.signature(dict(independent)),'First independent new BASE encode QA')
        pixels=dict(directprocessor.image_processor(images=[image],return_tensors='pt'))
        independent=dict(directprocessor.image_processor(images=[image],return_tensors='pt'))
        require(helper.signature(pixels)==helper.signature(independent),'First independent new65536 image QA')
        p,layout=helper.extract_source_prefix(pixels,pixels['image_grid_thw'][0].tolist());helper.independent_prefix_check(pixels,p,pixels['image_grid_thw'][0].tolist(),layout)
        tokens,text=helper.build_text_input(directprocessor,p['image_grid_thw']);textqa=helper.independent_text_check(directprocessor,p,tokens,text);dv=dict(**tokens,**p)
        inputs={}
        for role,values,template in [('BASE',bv,btext),('DIRECT',dv,text)]:
            require(set(values)=={'input_ids','attention_mask','pixel_values','image_grid_thw'} and values['input_ids'].shape[1]<=4096,'Complete untruncated new one-image input')
            stream=io.BytesIO();torch.save(values,stream);encoded=data(out/(str(i)+'.'+role+'.pt.gz'),gzip.compress(stream.getvalue(),mtime=0))
            restored=torch.load(io.BytesIO(gzip.decompress(bound(encoded).read_bytes())),map_location='cpu',weights_only=True)
            require(helper.signature(restored)==helper.signature(values),'Lossless first F4 gzip roundtrip')
            request=dict(id='F%02d_'%i+role,source_id=row['source_id'],source_sha256=jpeg['sha256'],role=role,width=W,height=H,
                encoded=encoded,input_signature=helper.signature(values),image_grid_thw=values['image_grid_thw'].tolist(),
                reference_or_target_in_prompt=False,template=template,original_source=jpeg,RGB=rgbref)
            path=out/(str(i)+'.'+role+'.json');save(path,request);inputs[role]=ref(path)
        source=dict(source_id=row['source_id'],source_sha256=jpeg['sha256'],width=W,height=H,RGB=rgbref,RGB_sha256=rgbsha,
            dhash9x8=dh,original_JPEG=jpeg,inputs=inputs,identity=identity,original_reference_in_inputs=False)
        sources.append(source);proof=out/(str(i)+'.first_QA.json');save(proof,dict(source_id=row['source_id'],source_sha256=jpeg['sha256'],inputs=inputs,
            independent_BASE_encoder=True,independent_DIRECT_pixels=True,DIRECT_text=textqa,lossless_roundtrip=True,GT_read=False));qa.append(ref(proof))
        require(sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=r['CPU_max_new_bytes'],'Actual bounded new130 output bytes')
    require(len(sources)==8 and network_bytes==304262 and not torch.cuda.is_initialized(),'Complete8 CPU scope/no CUDA')
    save(out/'prepared.json',dict(schema='FRESH8_SOURCE_BASE_DIRECT_INPUTS_V130',sources=sources,registration=ref(rp),GT_read=False))
    save(out/'input_acceptance.json',dict(status=CPU_PASS,registration=ref(rp),prepared=ref(out/'prepared.json'),sources=8,inputs=16,first_QA=qa,
        network_bytes=network_bytes,new_JPEG_decodes=8,new_image_prepare_encodings=16,new_image_first_QA_encodings=16,GT_read=False,
        elapsed_seconds=time.monotonic()-started,new_bytes_before_acceptance=sum(p.stat().st_size for p in out.iterdir() if p.is_file())))


def gpu(root,r,rp):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Physical unique GPU child')
    pair=module(r['pair_common_code'],'_fresh130_pair');pair.paths()
    import torch
    from transformers import Qwen3VLForConditionalGeneration,AutoTokenizer
    from peft import PeftModel
    contract_sft=module(r['sft_contract_code'],'_fresh130_sft');contract_sft.verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name']==r['GPU_job'],'Actual unique shared GPU job')
    identity=module(r['identity_code'],'_fresh130_identity');helper=module(r['GPU105_code'],'_fresh130_GPU105')
    math105=module(r['math105_code'],'_fresh130_math105');inputhelper=module(r['input_code87'],'_fresh130_input87_gpu')
    baseline=module(r['original_baseline_code'],'_fresh130_original_gpu');geom=module(r['baseline_geometry_code'],'_fresh130_old_geometry')
    cfg=load(r['model_config']);gate=read(root/'inputs/input_acceptance.json');prepared=load(gate['prepared'])
    require(gate['status']==CPU_PASS and gate['registration']==ref(rp) and gate['sources']==8 and gate['inputs']==16,'All new8 CPU QA before model')
    sources=prepared['sources'];out=root/'GPU';out.mkdir(exist_ok=False);started=time.monotonic();entries=[]
    model=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=contract_sft.REVISION,local_files_only=True,
        torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa').eval()
    model.requires_grad_(False);model.config.use_cache=False;before=identity.canonical_frozen_hash(model,torch)
    require(before['parameters']==8767123696 and before['sha256']==cfg['expected_base_sha256']
        and not any('lora_' in n for n,_ in model.named_parameters()),'Actual original bare BASE bytes/no adapter')
    tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    for i,s in enumerate(sources):
        deadline(r,started,'GPU');values,q=read_input(s['inputs']['BASE'],inputhelper,torch);values={k:v.to('cuda:0') for k,v in values.items()};prefix=values['input_ids'].shape[1]
        save(out/(str(i)+'.BASE.attempt.json'),dict(source_id=s['source_id'],source_sha256=s['source_sha256'],input=s['inputs']['BASE'],model_role='ORIGINAL_BARE_BASE_131072_GREEDY128'))
        with torch.inference_mode():generated=model.generate(**values,max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True)
        ids=generated[0,prefix:].detach().cpu().tolist();raw=tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        bp=out/(str(i)+'.BASE.raw.json');save(bp,dict(source_id=s['source_id'],source_sha256=s['source_sha256'],input=s['inputs']['BASE'],
            raw=raw,output_ids=ids,prefix_tokens=int(prefix),first_BASE_generation=True,BASE_only_no_adapter=True,GT_read=False))
        center=baseline.parse_focus_norm(raw,s['width'],s['height']);require(center is not None and ids,'Persist invalid raw; no fallback')
        oldbox=geom.place_crop(s['width'],s['height'],center)
        cw,hf=baseline.compute_crop_size(s['width'],s['height'],16,9)
        require(oldbox==baseline.center_to_box(*center,s['width'],s['height'],cw,hf),'Original BASE placement exactly matches frozen behavior')
        entries.append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],BASE_raw=ref(bp),baseline_box=oldbox));del values,generated
    require(identity.canonical_frozen_hash(model,torch)==before,'Bare BASE8 generation changed bytes')
    model=PeftModel.from_pretrained(model,str(bound(r['adapter_weights']).parent),adapter_name='direct_box',is_trainable=False,local_files_only=True).eval();model.requires_grad_(False)
    head=torch.nn.Linear(4096,3,bias=True,device='cuda:0',dtype=torch.float32);head.load_state_dict(torch.load(bound(r['head_weights']),map_location='cpu',weights_only=True));head.eval().requires_grad_(False)
    _,inventory=helper._inventory(model,head,False,torch);initial=helper._adapter_state(model,torch,type('CPU',(),{'_cpu_tree':staticmethod(lambda d,t:{k:v.detach().cpu().clone() for k,v in d.items()})}))
    for i,(s,e) in enumerate(zip(sources,entries)):
        deadline(r,started,'GPU');values,q=read_input(s['inputs']['DIRECT'],inputhelper,torch);values={k:v.to('cuda:0') for k,v in values.items()}
        save(out/(str(i)+'.DIRECT.attempt.json'),dict(source_id=s['source_id'],source_sha256=s['source_sha256'],input=s['inputs']['DIRECT'],model_role='FROZEN105_SOURCE_ONLY_L2_HEAD3'))
        with torch.inference_mode():hidden=helper._hidden(model,values,torch,False)
        h=tensor(out/(str(i)+'.hidden.pt'),hidden.float().cpu().contiguous(),torch)
        with torch.inference_mode():raw=head(math105.normalize_hidden(hidden))
        z=tensor(out/(str(i)+'.head.pt'),raw.float().cpu().contiguous(),torch)
        with torch.inference_mode():decoded=math105.decode_torch(raw,s['width'],s['height']).float().cpu().tolist()
        receipt=dict(id=q['id'],source_id=s['source_id'],source_sha256=s['source_sha256'],width=s['width'],height=s['height'],
            input=s['inputs']['DIRECT'],raw_hidden=h,raw_head=z,decoded_xyw=decoded,adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],
            hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',input_signature=q['input_signature'],GT_read=False)
        path=out/(str(i)+'.DIRECT.receipt.json');save(path,receipt);e.update(DIRECT_receipt=ref(path));del values,hidden,raw
    require(identity.canonical_frozen_hash(model,torch)==before,'Readonly105 changed BASE bytes')
    from safetensors.torch import load_file
    after=helper._adapter_state(model,torch,type('CPU',(),{'_cpu_tree':staticmethod(lambda d,t:{k:v.detach().cpu().clone() for k,v in d.items()})}))
    require(helper._tree_equal(initial,after,torch) and helper._tree_equal(after,load_file(str(bound(r['adapter_weights'])),device='cpu'),torch)
        and helper._tree_equal(head.state_dict(),torch.load(bound(r['head_weights']),map_location='cpu',weights_only=True),torch),'Exact frozen all288+2 bytes after16 tasks')
    save(out/'completion.json',dict(status=GPU_COMPLETE,registration=ref(rp),input_acceptance=ref(root/'inputs/input_acceptance.json'),
        entries=entries,sources=8,BASE_generations=8,DIRECT_hidden_head_forwards=8,training_updates=0,GT_read=False,inventory=inventory,
        base_fingerprint=before,adapter_all288_exact=True,head_all2_exact=True,
        training_completion=r['training_completion'],adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],elapsed_seconds=time.monotonic()-started))


def selected_annotation_rows(text,names):
    """Parse numerical annotations ONLY for registered names; skip other objects."""
    result={};depth=0;string=False;escape=False;start=None
    for i,char in enumerate(text):
        if string:
            if escape:escape=False
            elif char=='\\':escape=True
            elif char=='"':string=False
            continue
        if char=='"':string=True
        elif char=='{':
            if depth==0:start=i
            depth+=1
        elif char=='}':
            depth-=1
            if depth==0:
                fragment=text[start:i+1];match=re.search(r'"filename"\s*:\s*"([^"\\]+)"',fragment)
                if match and match[1] in names:
                    require(match[1] not in result,'Duplicate original annotation owner');result[match[1]]=json.loads(fragment)
    require(depth==0 and set(result)==set(names),'Exactly registered8 original annotation objects')
    return result


def quality(rows,controls):
    require(len(rows)==8 and len({x['source_id'] for x in rows})==8,'Exact new8 denominator')
    summary=dict(sources=8,mean_gain=sum(x['gain'] for x in rows)/8,improved=sum(x['gain']>0 for x in rows),
        worst_loss=max(0.,max(-x['gain'] for x in rows)),changed=sum(x['changed'] for x in rows),
        true_reject=sum(x['true_reject'] for x in rows),true_retain=sum(x['true_retain'] for x in rows),invalid=0)
    mean=sum(x['selected_iou'] for x in rows)/8
    checks=dict(exact8=True,minimum_gain=summary['mean_gain']>=.01,at_least2_improve=summary['improved']>=2,
        worst_loss=summary['worst_loss']<=.1,true_reject=summary['true_reject']>=1,true_retain=summary['true_retain']>=1,invalid0=True)
    require(set(controls)==set(GATE['strictly_beat']),'All five same8 fixed controls')
    checks.update({'beats_'+k:mean>v for k,v in controls.items()});return summary,dict(admitted=all(checks.values()),checks=checks)


def review(root,r,rp):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent CPU review')
    started=time.monotonic()
    import numpy as np
    import torch
    from transformers import AutoTokenizer
    helper=module(r['input_code87'],'_fresh130_input_review');rawqa=module(r['raw_QA_code105'],'_fresh130_rawQA105')
    math105=module(r['math105_code'],'_fresh130_math_review');critic=module(r['critic_code'],'_fresh130_frozen128')
    baseline=module(r['original_baseline_code'],'_fresh130_baseline_review');geom=module(r['baseline_geometry_code'],'_fresh130_original_geom_review')
    geometry31=module(r['geometry31_code'],'_fresh130_pool31');policy=module(r['policy33_code'],'_fresh130_geo13')
    gate=read(root/'inputs/input_acceptance.json');prepared=load(gate['prepared']);done=read(root/'GPU/completion.json')
    require(gate['status']==CPU_PASS and gate['registration']==done['registration']==ref(rp) and done['status']==GPU_COMPLETE
        and done['input_acceptance']==ref(root/'inputs/input_acceptance.json') and done['sources']==8
        and done['BASE_generations']==done['DIRECT_hidden_head_forwards']==8 and done['training_updates']==0
        and all(done[k]==r[k] for k in ('training_completion','adapter_weights','head_weights')),'Complete actual16 new tasks')
    require(len(prepared['sources'])==len(done['entries'])==8
        and [s['source_id'] for s in prepared['sources']]==[s['source_id'] for s in contract.fixed_sources()]
        and len({e['source_id'] for e in done['entries']})==8,'All8 exact ordered owners before any raw QA or target access')
    trained=load(r['training_completion'])
    require(done['base_fingerprint']==trained['base_fingerprint'] and done['inventory']==trained['inventory']
        and done['adapter_all288_exact'] is True and done['head_all2_exact'] is True,'Actual saved final105 byte identity/inventory')
    tokenizer=AutoTokenizer.from_pretrained(load(r['model_config'])['model_dir'],local_files_only=True)
    review_admission=read(root/'review_admission_130.json')
    require(review_admission['schema']=='FRESH8_ACTUAL_GPU_REVIEW_ADMISSION_V130' and review_admission['registration']==ref(rp)
        and review_admission['completion']==ref(root/'GPU/completion.json'),'Separate actual post-GPU resource/ledger refs, never future SHA')
    resource=load(review_admission['GPU_resource']);ledger=[v for v in [json.loads(s) for s in bound(review_admission['GPU_ledger']).read_text().splitlines() if s] if v.get('name')==r['GPU_job']]
    require(ledger==[resource] and resource['status']=='completed' and resource['exit_code']==0,'One actual shared GPU completed record')
    head=torch.load(bound(r['head_weights']),map_location='cpu',weights_only=True);predictions=[];choices=[]
    with np.load(bound(r['critic_state']),allow_pickle=False) as f:state={k:f[k].copy() for k in f.files}
    old=load(r['old_control_result70']);oldvalue=torch.load(bound(old['value_weights']),map_location='cpu',weights_only=True)
    beta70=oldvalue['geometry_beta'].double().numpy()
    with np.load(bound(old['old_gain_state']),allow_pickle=False) as f:rms=f['RMS'].copy();beta47=f['GEOM11_beta'].copy()
    original33=load(old['original_geometry_control'])
    with np.load(bound(original33['coefficients']),allow_pickle=False) as f:beta33=f['beta'].copy()
    control_parameters=sum(v.numel() for v in oldvalue.values())+rms.size+beta47.size+beta33.size
    require(contract.PIPELINE+control_parameters<=9000000000,'Conservative predictor plus all loaded frozen evaluation control arrays <=9B')
    for s,e in zip(prepared['sources'],done['entries']):
        deadline(r,started,'review')
        require(s['source_id']==e['source_id'] and s['source_sha256']==e['source_sha256'],'Ordered exact fresh owners')
        base=load(e['BASE_raw']);require(base['input']==s['inputs']['BASE'] and base['source_id']==s['source_id'] and base['source_sha256']==s['source_sha256']
            and base['first_BASE_generation'] is True and base['BASE_only_no_adapter'] is True and base['GT_read'] is False,'Actual original BASE input/raw identity')
        q=load(s['inputs']['BASE']);center=baseline.parse_focus_norm(base['raw'],s['width'],s['height']);require(center is not None and base['output_ids'] and base['prefix_tokens']==q['input_signature']['input_ids']['shape'][1],'BASE raw grammar/prefix')
        require(tokenizer.decode(base['output_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==base['raw'],'Independent original BASE output token/raw identity')
        B=geom.place_crop(s['width'],s['height'],center);require(B==e['baseline_box'],'Original BASE native placement replay')
        receipt=load(e['DIRECT_receipt']);require(receipt['input']==s['inputs']['DIRECT'],'Direct original accepted input')
        source=dict(s,pool=[B],baseline_box=B,original_BASE_observed=True)
        actual=rawqa.validate_raw(torch.load(bound(receipt['raw_hidden']),map_location='cpu',weights_only=True),
            torch.load(bound(receipt['raw_head']),map_location='cpu',weights_only=True),receipt,head,source,
            adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],geometry=geometry31)
        D=actual['native_boxes']['DIRECT'];projection=critic.trust_project_native3(B,D,s['width'],s['height']);P=projection['box3']
        h=torch.load(bound(receipt['raw_hidden']),map_location='cpu',weights_only=True)
        normalized=math105.normalize_hidden(h).numpy()
        joint=float(critic.predict_gain(state,normalized,B,P,s['width'],s['height'],arm='JOINT'))
        geometric=float(critic.predict_gain(state,normalized,B,P,s['width'],s['height'],arm='GEOM11'))
        require(math.isfinite(joint) and math.isfinite(geometric),'Finite frozen critic gains')
        pool=geometry31.candidate_pool(s['width'],s['height'],baseline_box=B);g=np.stack([policy.geometry_features(b,s['width'],s['height']) for b in pool]);delta=(g-g[0])[:,1:12]
        control_boxes=dict(GEOM11=P if geometric>0 else B,ALWAYS124=P,
            OLD70_GEOM=pool[int(np.argmax(delta@beta70))],OLD47_GEOM11=pool[int(np.argmax((delta/rms[3:])@beta47))],
            OLD33_GEOM13=pool[int(np.argmax(g@beta33-(g@beta33)[0]))])
        choices.append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],width=s['width'],height=s['height'],B=B,P=P,
            selected=P if joint>0 else B,predicted_gain=joint,controls=control_boxes,projection=projection))
        predictions.append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],receipt=e['DIRECT_receipt'],BASE_raw=e['BASE_raw'],**actual))
    acceptance=root/'output_acceptance.json';save(acceptance,dict(status=RAW_PASS,registration=ref(rp),input_acceptance=ref(root/'inputs/input_acceptance.json'),
        completion=ref(root/'GPU/completion.json'),predictions=predictions,choices=choices,sources=8,GT_read=False,
        development_result=r['development_result'],critic_state=r['critic_state'],training_completion=r['training_completion'],
        adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],resource=review_admission['GPU_resource'],review_admission=ref(root/'review_admission_130.json')))
    # First reference-coordinate access follows persisted complete raw QA/choices.
    annotations=selected_annotation_rows(bound(r['source_metadata']['test.json']).read_text(),[x['filename'] for x in r['sources']])
    rows=[];control_iou={k:[] for k in GATE['strictly_beat']}
    for s,c in zip(prepared['sources'],choices):
        deadline(r,started,'review')
        name=s['source_id'].split(':')[-1];a=annotations[name]['crop_bboxes']['16:9'];require(len(a)==4 and all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=1 for v in a),'Original normalized human XYXY')
        x1,y1,x2,y2=map(float,a);require(x2>x1 and y2>y1,'Positive original GT')
        target=[x1*s['width'],y1*s['height'],(x2-x1)*s['width'],(y2-y1)*s['height']];math105.target_xywh(target,s['width'],s['height'])
        oldiou=math105.crop_iou(c['B'],target,s['width'],s['height']);newiou=math105.crop_iou(c['selected'],target,s['width'],s['height'])
        rows.append(dict(source_id=s['source_id'],baseline_iou=oldiou,selected_iou=newiou,gain=newiou-oldiou,changed=c['selected']!=c['B'],
            true_reject=c['P']!=c['B'] and c['selected']==c['B'],true_retain=c['P']!=c['B'] and c['selected']==c['P'],original_reference_xywh=target))
        for k,b in c['controls'].items():control_iou[k].append(math105.crop_iou(b,target,s['width'],s['height']))
    controls={k:sum(v)/8 for k,v in control_iou.items()};summary,q=quality(rows,controls)
    save(root/'result.json',dict(status=QUALITY_PASS if q['admitted'] else QUALITY_STOP,admitted_arms=['JOINT'] if q['admitted'] else [],
        quality=q,summary=summary,rows=rows,controls=controls,registration=ref(rp),development_result=r['development_result'],critic_state=r['critic_state'],
        training_completion=r['training_completion'],adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],
        output_acceptance=ref(acceptance),input_acceptance=ref(root/'inputs/input_acceptance.json'),pipeline_parameters=contract.PIPELINE,
        frozen_evaluation_control_parameters=int(control_parameters),conservative_pipeline_including_evaluation_controls=int(contract.PIPELINE+control_parameters),
        file_level_only=True,source_global_independence='UNKNOWN',pretraining_overlap='UNKNOWN',new_fit=0,automatic_production=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True);p.add_argument('--stage',choices=['cpu','gpu','review'],required=True)
    a=p.parse_args();root,r,rp=configuration(a.root,a.registration)
    claim=root/(a.stage+'_claim.json');save(claim,dict(registration=ref(rp),stage=a.stage,pid=os.getpid(),automatic_next=False))
    try:globals()[a.stage](root,r,rp)
    except BaseException as error:
        save(root/(a.stage+'_failure.json'),dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,no_automatic_retry=True));raise


if __name__=='__main__':main()
