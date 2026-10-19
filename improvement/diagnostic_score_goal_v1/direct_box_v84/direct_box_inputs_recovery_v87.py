"""Explicit ULP-only recovery87 of frozen source-only84; no actions on import, CLI --root ROOT.

Reg direct_box_CPU_registration_87.json / DIRECT_BOX_SOURCE_ONLY_CPU_V84:
preparation_code,input_code,helper_code,model_config,old_catalog,old_prepared,
old_input_acceptance,original_targets,old55_prepared,old55_screen_targets,
old55_STOP,oldstar_STOP,protocol refs; deadline_utc,max_seconds,max_new_bytes,
new_original_decode=old_source_processor_repeated=0. All existing pixels are
adopted. Only a new one-image prefix/combination is prepared and first-QAd.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import time
import traceback
from unittest.mock import patch

WORK=Path('/home/inspur/aic_video_work')
SCHEMA='DIRECT_BOX_SOURCE_ONLY_INPUTS_V84'
CPU_SCHEMA='DIRECT_BOX_SOURCE_ONLY_CPU_V84'
GATE='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA'
FOUR={'input_ids','attention_mask','pixel_values','image_grid_thw'}
PROMPT='Locate a suitable 16:9 composition in the full source image. Preserve subjects and context.\n'
CODEC='TORCH_SAVE_GZIP_V1'


def require(value,message):
    if not value:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def ref(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))


def bound(reference):
    p=Path(reference['path']).resolve()
    require(set(reference)=={'path','sha256'} and p.is_relative_to(WORK) and p.is_file()
        and sha(p)==reference['sha256'],'Exact existing artifact inside Linux work root: '+str(p))
    return p


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def signature(values):
    import torch
    require(all(isinstance(v,torch.Tensor) and v.device.type=='cpu' and not v.requires_grad for v in values.values()),'Detached CPU tensors')
    return {k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()) for k,v in values.items()}


def source_id(source):return digest(['DIRECT_BOX84_SOURCE_ONLY',source['source_id'],source['source_sha256']])[:24]


def extract_source_prefix(payload,expected_grid):
    """First accepted source image, using actual grid product, never fixed240."""
    import torch
    p,g=payload['pixel_values'],payload['image_grid_thw']
    require(p.device.type==g.device.type=='cpu' and p.dtype==torch.float32 and g.dtype==torch.int64
        and p.ndim==2 and p.shape[1]==1536 and g.ndim==2 and g.shape[1]==3 and len(g)>0
        and bool((g>0).all()) and bool((g[:,0]==1).all()) and bool((g[:,1:]%2==0).all()),'Actual accepted static patch/grid tensor')
    require(g[0].tolist()==expected_grid and int(g.prod(dim=1).sum())==len(p),'Original full-source prefix grid/total patch rows')
    n=int(g[0].prod());pixels=p[:n].contiguous();grid=g[:1].contiguous()
    require(bool(torch.isfinite(pixels).all()) and not pixels.requires_grad,'Finite adopted source prefix')
    repeated=pixels.reshape(n,3,2,16,16)
    require(torch.equal(repeated[:,:,0].contiguous().view(torch.uint8),repeated[:,:,1].contiguous().view(torch.uint8)),'Original static temporal slices bit-equal')
    return dict(pixel_values=pixels,image_grid_thw=grid),dict(row_start=0,row_end_exclusive=n,grid_thw=expected_grid,
        source_total_grid_rows=len(g),source_total_patch_rows=len(p),source_prefix_signature=signature(dict(pixel_values=pixels,image_grid_thw=grid)))


def independent_prefix_check(payload,packed,expected_grid,meta):
    import torch
    n=math.prod(expected_grid);p,g=payload['pixel_values'],payload['image_grid_thw']
    require(n==meta['row_end_exclusive'] and meta['row_start']==0 and g[0].tolist()==expected_grid
        and signature(packed)==meta['source_prefix_signature'] and list(packed['pixel_values'].shape)==[n,1536]
        and torch.equal(p[:n].contiguous().view(torch.uint8),packed['pixel_values'].contiguous().view(torch.uint8))
        and torch.equal(g[:1],packed['image_grid_thw']),'Independent original source prefix pixel/grid order')
    return dict(status='PASS_EXACT_ACCEPTED_SOURCE_PREFIX_ADOPTION',new_image_processor_calls=0,new_decode=0,actual_prefix_rows=n)


def messages():return [dict(role='user',content=[dict(type='text',text=PROMPT),dict(type='image')])]


def tokenize(processor,text):
    import torch
    t=processor.tokenizer(text,return_tensors='pt',add_special_tokens=False,truncation=False)
    result={k:t[k].contiguous() for k in ('input_ids','attention_mask')}
    require(all(v.device.type=='cpu' and v.dtype==torch.int64 and v.ndim==2 and v.shape[0]==1 for v in result.values())
        and result['input_ids'].shape==result['attention_mask'].shape and bool((result['attention_mask']==1).all())
        and 0<result['input_ids'].shape[1]<=4096,'One complete unpadded source-only prefix, no truncation')
    return result


def build_text_input(processor,grid):
    import torch
    require(grid.device.type=='cpu' and grid.dtype==torch.int64 and tuple(grid.shape)==(1,3)
        and grid[0,0]==1 and bool((grid>0).all()) and bool((grid[0,1:]%2==0).all())
        and processor.image_processor.merge_size==2,'One actual static merge2 source image')
    raw=processor.apply_chat_template(messages(),tokenize=False,enable_thinking=False,add_generation_prompt=True)
    plain=processor.apply_chat_template(messages(),tokenize=False,enable_thinking=False,add_generation_prompt=False)
    require(isinstance(raw,str) and raw.startswith(plain) and len(raw)>len(plain),'Final assistant generation prefix')
    prefix=raw[len(plain):];marker=processor.vision_start_token+processor.image_token+processor.vision_end_token
    parts=raw.split(marker);require(len(parts)==2,'Exactly one Source marker')
    count=int(grid.prod())//4;text=parts[0]+processor.vision_start_token+processor.image_token*count+processor.vision_end_token+parts[1]
    require(text.endswith(prefix) and text.index(PROMPT)<text.index(processor.vision_start_token),'Task before image, assistant prefix final')
    tokens=tokenize(processor,text);image_id=processor.tokenizer.convert_tokens_to_ids(processor.image_token)
    require(type(image_id)==int and image_id>=0,'Actual image-token identity')
    positions=(tokens['input_ids'][0]==image_id).nonzero().flatten().tolist()
    require(len(positions)==count and positions==list(range(positions[0],positions[0]+count)),'One exact contiguous image token run')
    return tokens,dict(prompt=PROMPT,raw_template=raw,expanded_text=text,assistant_generation_prefix=prefix,
        last_hidden_position=int(tokens['input_ids'].shape[1])-1,sequence_tokens=int(tokens['input_ids'].shape[1]),
        image_grid_thw=grid.tolist(),image_token_id=image_id,image_tokens=count,token_signature=signature(tokens),
        new_real_image_processor_calls=0,reference_or_target_in_prompt=False)


def independent_text_check(processor,packed,tokens,meta):
    import torch
    old=processor.image_processor
    class AdoptedImage:
        def __getattr__(self,name):return getattr(old,name)
        def __call__(self,*args,**kwargs):return {k:v.clone() for k,v in packed.items()}
    require(meta['prompt']==PROMPT and meta['raw_template']==processor.apply_chat_template(messages(),tokenize=False,enable_thinking=False,add_generation_prompt=True),'Fixed new source-only prompt')
    with patch.object(processor,'image_processor',AdoptedImage()):
        actual=processor(text=[meta['raw_template']],images=[object()],return_tensors='pt',padding=False,add_special_tokens=False,truncation=False)
    require(all(torch.equal(actual[k],tokens[k]) for k in tokens) and signature({k:actual[k] for k in packed})==signature(packed),'Independent source-only stub processor four-input mapping')
    again,evidence=build_text_input(processor,packed['image_grid_thw'])
    require(signature(again)==signature(tokens) and evidence==meta,'Actual assistant terminal/prefix evidence')
    return dict(status='PASS_FIRST_SOURCE_ONLY_STUB_TEXT_AND_ADOPTED_PIXEL_QA',real_image_processor_calls=0,new_decode=0)


def bound_numeric(start,size,limit):
    require(all(type(v) in (int,float) and math.isfinite(v) for v in (start,size,limit))
        and start>=0 and size>0 and limit>0,'Original finite nonnegative boundary terms')
    endpoint=start+size; overflow=endpoint-limit
    allowance=math.fsum((math.ulp(float(start)),math.ulp(float(size)),math.ulp(float(limit))))
    require(overflow<=allowance,'Original endpoint exceeds sum-of-term ULP certificate')
    return dict(endpoint=endpoint,bound=limit,overflow=overflow,ulp_terms=[math.ulp(float(v)) for v in (start,size,limit)],
        allowed_ulp_sum=allowance,rounding_only_overflow=overflow>0,original_values_unchanged=True)


def native_reference_ulp_certificate(reference,width,height):
    require(len(reference)==4,'Original native XYWH4')
    x,y,w,h=reference
    return dict(x_endpoint=bound_numeric(x,w,width),y_endpoint=bound_numeric(y,h,height),
        fixed_epsilon_used=False,original_reference_modified=False)


def validate_failed84(root,reg):
    oldref=reg['original_failed_registration'];old=read(bound(oldref));exitref=reg['original_failed_exit']
    require(bound(oldref)==(root/'direct_box_CPU_registration_84.json').resolve()
        and bound(exitref)==(root/'direct_box_CPU_85_exit.json').resolve(),'Exact original84 failed registration/owned exit')
    diagnosis=reg['failure_diagnosis']
    require(diagnosis['sha256']=='9789bddca6e3811e6b8d18052938739bfabd1f557e263028360b2d6ca1029256'
        and bound(diagnosis)==(root/'direct_box_CPU_metadata_failure_diagnosis_87.json').resolve(),'Exact first metadata-only ULP failure diagnosis')
    done=read(bound(exitref));failure=read(root/'direct_box_CPU_85_failure.json');entry=done['entry']
    execution=read(bound(failure['registration']))
    require(done['actual_exit_code']==1 and entry['CPU_child'] is True and failure['entry']==entry
        and execution['science_registration']==oldref and execution['child_code']==old['preparation_code']
        and entry['argv']==[entry['argv'][0],'-B','-u',str(bound(old['preparation_code'])),'--root',str(root)],
        'Actual failed original84 CLI/CPU ownership, not successful prepare adoption')
    for k,v in old.items():
        if k not in ('preparation_code','input_code'):require(reg[k]==v,'Recovery changed original non-code registration: '+k)
    require(not (root/'direct_box_inputs_84').exists(),'Original84 produced no output; never overwrite or redo firstQA')
    return dict(original_failed_registration=oldref,original_failed_exit=exitref,failure_diagnosis=diagnosis,
        successful_inputs_adopted=0,old_failure_preserved=True)


def compile_targets(catalog,original_targets,train55,screen55):
    """Only source metadata and ORIGINAL native human XYWH, no pair IoU use."""
    sources=catalog['sources'];require(len(sources)==622 and len({s['source_id'] for s in sources})==622,'Fixed old31 scope')
    train=[s for s in sources if s['role']=='train'];screen=[s for s in sources if s['role']=='screen']
    require(len(train)==602 and len(screen)==20 and {s['source_sha256'] for s in train}.isdisjoint(s['source_sha256'] for s in screen),'Fixed602/20 source isolation')
    t55={s['source_id']:s for s in train55['sources']};d55={s['source_id']:s for s in screen55['sources']}
    require(set(t55)=={s['source_id'] for s in train} and set(d55)=={s['source_id'] for s in screen},'Actual55 training/development source sets')
    labels={s['source_id']:s for s in original_targets['sources']};outputs={'train':[],'screen':[]};aspects=[]
    for s in sources:
        t=labels[s['source_id']];old=t55[s['source_id']] if s['role']=='train' else d55[s['source_id']]
        require(s['source_sha256']==t['source_sha256']==old['source_sha256'] and t['role']==s['role']
            and t['reference_modified'] is False and t['baseline_index']==0,'Original human target/source binding')
        x,y,w,h=t['original_reference_xywh'];W,H=s['width'],s['height']
        require(all(type(v) in (int,float) and math.isfinite(v) for v in (x,y,w,h)) and x>=0 and y>=0 and w>0 and h>0
            and native_reference_ulp_certificate([x,y,w,h],W,H),'Original human reference with per-term ULP endpoint certificate; never repair')
        row=dict(numeric_boundary_certificate=native_reference_ulp_certificate(t['original_reference_xywh'],W,H),source_id=s['source_id'],source_sha256=s['source_sha256'],role=s['role'],width=W,height=H,
            original_reference_xywh=copy.deepcopy(t['original_reference_xywh']),reference_modified=False)
        if s['role']=='screen':
            require(s['pool'][0]==s['baseline_box'] and s['original_BASE_observed'] is True
                and old['pool'][0]==old['baseline_box']==s['baseline_box']
                and old['original_reference_xywh']==t['original_reference_xywh'],'Original observed screenBASE/native reference')
            row.update(baseline_box=copy.deepcopy(s['baseline_box']),pool=copy.deepcopy(s['pool']))
        outputs[s['role']].append(row);aspects.append(dict(role=s['role'],ratio=w/h,absolute_ratio_error=abs(w/h-16/9)))
    aspect={role:dict(sources=len([a for a in aspects if a['role']==role]),
        within_1e_6_of_16_9=sum(a['absolute_ratio_error']<=1e-6 for a in aspects if a['role']==role),
        min_ratio=min(a['ratio'] for a in aspects if a['role']==role),max_ratio=max(a['ratio'] for a in aspects if a['role']==role)) for role in outputs}
    return outputs,aspect


def source_schedule(train_sources,input_refs):
    require(len(train_sources)==len({s['source_id'] for s in train_sources})==602,'Exactly602 training sources')
    ordered=sorted(train_sources,key=lambda s:(s['source_sha256'],s['source_id']))
    extras={s['source_id'] for s in sorted(ordered,key=lambda s:digest([s['source_sha256'],'DIRECT84_EXTRA']))[:190]}
    draws=[(s,r) for s in ordered for r in range(6 if s['source_id'] in extras else 5)]
    draws.sort(key=lambda sr:digest([sr[0]['source_sha256'],sr[1],'DIRECT84_DRAW_ORDER']))
    counts=Counter(s['source_id'] for s,_ in draws)
    return [dict(id='D%04d'%i,source_id=s['source_id'],source_sha256=s['source_sha256'],input_id=source_id(s),
        input=copy.deepcopy(input_refs[source_id(s)]),draw_weight=3200/(602*counts[s['source_id']])) for i,(s,_) in enumerate(draws)]


class Writer:
    def __init__(self,out,limit):self.out,self.limit,self.bytes=out,limit,0
    def data(self,p,data):
        require(self.bytes+len(data)<=self.limit and shutil.disk_usage(self.out).free>=len(data),'Actual new bytes exceed admitted/live capacity')
        with Path(p).open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        self.bytes+=len(data);return ref(p)
    def json(self,p,value):return self.data(p,(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())


class DirectBoxInputs:
    def __init__(self,root):
        self.root=Path(root);rp=self.root/'direct_box_CPU_registration_87.json';self.reg=read(rp)
        require(bound(self.reg['input_code'])==Path(__file__).resolve(),'Exact source-only84 reader')
        gate=read(self.root/'direct_box_inputs_84/input_acceptance.json')
        require(gate['status']==GATE and gate['registration']==ref(rp),'Actual complete source-only first CPU QA')
        self.prepared=read(bound(gate['prepared']));require(self.prepared['schema']==SCHEMA and gate['prepared']==ref(self.root/'direct_box_inputs_84/prepared.json'),'Own84 prepared')
        entries=self.prepared['train_inputs']+self.prepared['screen_inputs'];self.allowed={e['id']:e for e in entries}
        require(len(self.allowed)==len(entries)==622 and len(self.prepared['train_inputs'])==602 and len(self.prepared['screen_inputs'])==20,'Fixed train/screen inventory')
        self.ref_to_id={(e['input']['path'],e['input']['sha256']):e['id'] for e in entries};require(len(self.ref_to_id)==622,'Unique exact request refs')
        self.current_id=None;self.cache=None
    def get_metadata(self,identifier):
        if isinstance(identifier,dict):identifier=self.ref_to_id.get((identifier['path'],identifier['sha256']))
        require(identifier in self.allowed,'Source-only input outside622 whitelist');e=self.allowed[identifier];q=read(bound(e['input']))
        require(all(q[k]==e[k] for k in ('id','source_id','source_sha256','role')) and q['reference_or_target_in_prompt'] is False
            and not any(k in q for k in ('target','labels','candidate_ious','original_reference_xywh')),'Exact label-free source-only owner')
        return q
    def get(self,identifier):
        import torch
        q=self.get_metadata(identifier)
        if self.current_id!=q['id']:
            payload=gzip.decompress(bound(q['encoded_input']).read_bytes())
            require(q['codec']['codec']==CODEC and len(payload)==q['codec']['uncompressed_bytes'],'Declared lossless source-only codec')
            values=torch.load(io.BytesIO(payload),map_location='cpu',weights_only=True)
            require(set(values)==FOUR and signature(values)==q['input_signature'] and values['image_grid_thw'].tolist()==q['image_grid_thw'],'Exact first-QAd fourtensor reload')
            self.current_id,self.cache=q['id'],values
        return self.cache,q


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU84 child masks CUDA')
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2);require(not torch.cuda.is_initialized(),'CPU-only84')
    root=Path(root);rp=root/'direct_box_CPU_registration_87.json';reg=read(rp)
    require(reg['schema']==CPU_SCHEMA and bound(reg['preparation_code'])==bound(reg['input_code'])==Path(__file__).resolve()
        and reg['new_original_decode']==reg['old_source_processor_repeated']==0,'New purpose84, no old decode/processor')
    recovery_adoption=validate_failed84(root,reg)
    for k in ('helper_code','protocol'):bound(reg[k])
    require(read(bound(reg['old55_STOP']))['status'].startswith('STOP_') and read(bound(reg['oldstar_STOP']))['status'].startswith('STOP_'),'All old quality STOPs preserved')
    old=read(bound(reg['old_prepared']));gate=read(bound(reg['old_input_acceptance']))
    require(gate['status']=='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA' and gate['prepared']==reg['old_prepared'],'Adopt actual original31 source input acceptance')
    catalog=read(bound(reg['old_catalog']));old55=read(bound(reg['old55_prepared']))
    require(old['source_catalog']==reg['old_catalog'] and old55['screen_prepared']==reg['old_prepared']
        and old55['screen_input_acceptance']==reg['old_input_acceptance'],'Same original31 source and55 screen input identities')
    labels,aspect=compile_targets(catalog,read(bound(reg['original_targets'])),read(bound(old55['source_catalog'])),read(bound(reg['old55_screen_targets'])))
    byid={s['source_id']:s for s in catalog['sources']};templates={}
    for entry in old['train_schedule']+old['screen_inputs']:
        sid=entry['source_id']
        if sid in templates:continue
        q=read(bound(entry['input']));s=byid[sid]
        require(q['source_id']==sid and q['source_sha256']==s['source_sha256'] and q['vision_inputs'][0]==s['source_vision']
            and q['reference_or_target_in_prompt'] is False,'Original accepted Source component binding')
        templates[sid]=(entry['input'],q)
    require(set(templates)==set(byid),'Every602+20 source has original accepted prefix')
    out=root/'direct_box_inputs_84';out.mkdir(exist_ok=False);writer=Writer(out,reg['max_new_bytes']);started=time.monotonic();completed=[]
    def budget():require(time.monotonic()-started<reg['max_seconds'] and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),'CPU84/Goal budget')
    writer.json(out/'claim.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),registration=ref(rp),model_calls=0,old_quality='STOP',recovery_adoption=recovery_adoption))
    try:
        cfg=read(bound(reg['model_config']));processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
        entries=[];token_cache={};uncompressed_total=compressed_total=0
        for s in catalog['sources']:
            budget();identifier=source_id(s);template_ref,template=templates[s['source_id']]
            raw=torch.load(bound(s['source_vision']),map_location='cpu',weights_only=True)
            packed,layout=extract_source_prefix(raw,template['image_grid_thw'][0]);pixel_QA=independent_prefix_check(raw,packed,template['image_grid_thw'][0],layout)
            token_key=json.dumps(packed['image_grid_thw'].tolist())
            if token_key not in token_cache:token_cache[token_key]=build_text_input(processor,packed['image_grid_thw'])
            tokens,text=token_cache[token_key];text_QA=independent_text_check(processor,packed,tokens,text)
            values=dict(**tokens,**packed);f4=signature(values);stream=io.BytesIO();torch.save(values,stream);uncompressed=stream.getvalue()
            encoded=gzip.compress(uncompressed,compresslevel=6,mtime=0);encoded_ref=writer.data(out/(identifier+'.pt.gz'),encoded)
            actual=torch.load(io.BytesIO(gzip.decompress(bound(encoded_ref).read_bytes())),map_location='cpu',weights_only=True)
            require(signature(actual)==f4,'First source-only compressed F4 roundtrip bit exact')
            codec=dict(codec=CODEC,compression_level=6,mtime=0,compressed_bytes=len(encoded),uncompressed_bytes=len(uncompressed))
            q=dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role=s['role'],width=s['width'],height=s['height'],
                prompt=PROMPT,text_evidence=text,input_signature=f4,image_grid_thw=packed['image_grid_thw'].tolist(),
                source_layout=layout,original_source_tensor=s['source_vision'],original_accepted_request=template_ref,original_proof=s['original_proof'],
                encoded_input=encoded_ref,codec=codec,reference_or_target_in_prompt=False,native_RGB_recovered=False,
                actual_input_domain='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',new_source_image_processor_calls=0)
            qr=writer.json(out/(identifier+'.json'),q)
            proof=writer.json(out/(identifier+'.first_QA.json'),dict(source_id=s['source_id'],source_sha256=s['source_sha256'],request=qr,
                pixel_QA=pixel_QA,text_QA=text_QA,compressed_four_tensor_roundtrip=True,first_new_source_only_combination=True,
                old_source_processor_repeated=False,new_original_decode=0))
            entries.append(dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role=s['role'],input=qr));completed.append(proof)
            uncompressed_total+=len(uncompressed);compressed_total+=len(encoded);del raw,packed,values,actual
        train_targets=writer.json(out/'train_targets.json',dict(schema='DIRECT_BOX84_ORIGINAL_TRAIN_TARGETS_ONLY',sources=labels['train'],reference_modified=False))
        screen_targets=writer.json(out/'screen_CPU_targets.json',dict(schema='DIRECT_BOX84_ORIGINAL_SCREEN_TARGETS_CPU_ONLY',sources=labels['screen'],reference_modified=False,historical_not_blind=True))
        source_rows=[]
        for s in catalog['sources']:
            row={k:copy.deepcopy(s[k]) for k in ('source_id','source_sha256','role','width','height')}
            row.update(baseline_box=copy.deepcopy(s['baseline_box']) if s['role']=='screen' else None,
                original_BASE_observed=s['role']=='screen')
            if s['role']=='screen':row['pool']=copy.deepcopy(s['pool'])
            source_rows.append(row)
        source_catalog=writer.json(out/'source_catalog.json',dict(sources=source_rows,GT_included=False,
            train_actual_B0_available=False,screen_B0_authority=reg['old55_screen_targets']))
        refs={e['id']:e['input'] for e in entries};schedule=source_schedule([s for s in catalog['sources'] if s['role']=='train'],refs)
        prepared=dict(schema=SCHEMA,train_inputs=[e for e in entries if e['role']=='train'],screen_inputs=[e for e in entries if e['role']=='screen'],
            train_schedule=schedule,schedule_sha256=digest(schedule),train_targets=train_targets,screen_CPU_targets=screen_targets,
            source_catalog=source_catalog,train_sources=602,screen_sources=20,train_micro=3200,prompt=PROMPT,
            observation_profile='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',new_image_processor_calls=0,new_original_decode=0,
            original55_STOP=reg['old55_STOP'],originalSTAR_STOP=reg['oldstar_STOP'],GPU_admitted=False,production_admitted=False)
        budget();require(len(entries)==622 and not torch.cuda.is_initialized(),'Complete622 new source-only combinations, no CUDA')
        pr=writer.json(out/'prepared.json',prepared)
        writer.json(out/'input_acceptance.json',dict(status=GATE,registration=ref(rp),prepared=pr,sources=622,train_sources=602,screen_sources=20,
            first_QA=completed,compressed_bytes=compressed_total,uncompressed_bytes=uncompressed_total,new_bytes_before_acceptance=writer.bytes,
            elapsed_seconds=time.monotonic()-started,aspect_diagnostic=aspect,aspect_used_as_rejection_gate=False,
            source_equal_schedule=True,pair_IoU_targets_used=False,new_original_decode=0,old_source_processor_repeated=0,GPU_admitted=False))
        print('DIRECT_BOX84_SOURCE_ONLY_FIRST_CPU_COMPLETE',len(entries),flush=True)
    except BaseException as error:
        with (out/'failure.json').open('x',encoding='utf-8') as stream:json.dump(dict(error=repr(error),traceback=traceback.format_exc(),completed=completed,preserve_all_success=True,automatic_retry=False),stream,ensure_ascii=False,indent=2)
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
