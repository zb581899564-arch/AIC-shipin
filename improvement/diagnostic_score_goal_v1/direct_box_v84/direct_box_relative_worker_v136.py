"""Conditional, explicitly registered single-stage GEOM129 production worker.

No operation occurs on import. Every invocation names one immutable registry
and one stage. Old105/106 qualification is never used as production admission.
See CONTRACT below; source images are adopted chunk rows, not recovered RGB.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

_here=Path(__file__).resolve()
for _support in (_here.parents[1]/'pair_code_17',_here.parents[1],_here.parents[2]/'pair_code_17'):
    if (_support/'pair_common.py').is_file():sys.path.insert(0,str(_support));break
from pair_common import WORK,read,save as _save_base,ref,bound,require,utc,paths,append_event

SCHEMA='FROZEN_PROMOTED_GEOM129_PRODUCTION_STAGE_V136'
INPUT_SCHEMA='EXACT_NATIVE_SINGLE_SOURCE_CHUNK_REFERENCES_V136'
INPUT_PASS='PASS_GEOM136_NEW_STAGE_INPUTS_FIRST_CPU_QA'
RAW_PASS='PASS_GEOM136_NEW_STAGE_RAW_HEAD_NATIVE_CPU_QA'
FINAL_PASS='PASS_GEOM136_ALL_EXACT_NATIVE_SPATIAL_OUTPUTS_CPU_QA'
ROLE='DIRECT_BOX105_PROMOTED_GEOM129_FORMAL'
SOURCE='DIRECT_BOX105_TRUST124_PROMOTED_GEOM129_GAIN'
STAGES=('prepare32','gpu32','qa32','prepare_remaining','gpu_remaining','qa_merge','package')
CONTRACT="""Required common refs: code,contract_code132,contract,development_result,
promotion,promotion_code129,fresh8_result,critic_state,critic_code128,
training_completion,adapter_weights,head_weights,adapter_config,model_config,
frozen_GPU105_code/registration,frozen_GPU93_code,frozen_math93_code,
frozen_math84_code,math_code,old_TIME,old_PAIR,old_CROP,base_input_code87,
domain_code106,raw_QA_code127,source_catalog,domain,protected_baseline,metadata,
protocol. Every registry has schema,stage,explicit_stage_admitted=true,
production_admitted=true,deadline_utc,max_seconds,max_new_bytes,output_root
(must ROOT/relative_production_136),GPU_job for GPU/QA; GPU only parses a minimal
production_admission with status ADMIT_GEOM129_FIXED_FRESH8_PRODUCTION_V136,
production_admitted,true,model3refs,critic_state,promotion,fresh8_result,contract.
It SHA-binds rich result refs but never parses labels/quality rows.
prepare32 requires domain/source_catalog compiled by frozen106 pure metadata
only AFTER actual129 promotion and actual134 PASS. No latest/search/GT.
Remaining registries additionally require remaining_admission with actual
pilot_output_acceptance,input_acceptance,GPU_completion,resource refs,
remaining_source_ids exact,capacity_review_admitted=true,deadline_utc,
max_seconds,max_new_bytes. No successful pilot input/model/rawQA repeats.
GPU/QA require prepared/input_acceptance refs for this stage. QA additionally
resource_receipt_path and gpu_ledger_path explicit actual controller paths,
geometry_code31. package additionally output_acceptance(final merged ref),
package_helpers108_code,source_field_inputs,inherited_baseline_completion,
inherited_provenance,inherited_selected,historical_registry,strict_loader_root,
strict_loader_code_refs,original_independent_validator,cost_evidence_refs.
All outputs exclusive; failures preserve raw and never automatically resume.
"""


def json_primitive(value):
    """Explicit numpy scalar/array conversion; reject unknown or nonfinite data."""
    import math
    import numpy as np
    if value is None or type(value) in (str,bool,int):return value
    if type(value) is float:
        require(math.isfinite(value),'Nonfinite JSON value is not missing/zero');return value
    if isinstance(value,np.bool_):return bool(value)
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.floating):return json_primitive(float(value))
    if isinstance(value,np.ndarray):return json_primitive(value.tolist())
    if isinstance(value,(list,tuple)):return [json_primitive(x) for x in value]
    if isinstance(value,dict):
        require(all(type(k) is str for k in value),'JSON object keys must be original strings')
        return {k:json_primitive(v) for k,v in value.items()}
    raise TypeError('Unsupported JSON value: '+type(value).__name__)


def save(path,value):return _save_base(path,json_primitive(value))


def module(reference,name):
    p=bound(reference);key='_geom136_'+name
    if key in sys.modules:
        require(Path(sys.modules[key].__file__).resolve()==p,'Pinned module path changed');return sys.modules[key]
    sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location(key,p)
    m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m);return m


def load(reference):return read(bound(reference))
def events(reference):return [json.loads(x) for x in bound(reference).read_text().splitlines() if x.strip()]
def key(reference):return reference['path'],reference['sha256']
def group(stage):return 'pilot32' if stage in ('prepare32','gpu32','qa32') else 'remaining'


def validate_registry(root,rp,r,stage):
    require(root.is_relative_to(WORK) and rp.is_relative_to(root) and r['schema']==SCHEMA
        and r['stage']==stage and stage in STAGES and r['explicit_stage_admitted'] is True
        and r['production_admitted'] is True and bound(r['code'])==Path(__file__).resolve(), 'One explicitly admitted new136 stage/code/root')
    require(Path(r['output_root']).resolve()==root/'relative_production_136','No output path escape or old namespace')
    require(r['max_seconds']>0 and r['max_new_bytes']>0,'Explicit per-stage measured budget')
    deadline(r)


def deadline(r,started=None):
    end=dt.datetime.fromisoformat(r['deadline_utc'].replace('Z','+00:00'))
    require(end.tzinfo is not None and dt.datetime.now(dt.timezone.utc)<end,'Goal deadline reached; no domain shrink/fallback')
    if started is not None:require(time.monotonic()-started<r['max_seconds'],'Explicit136 stage time budget exceeded')


def admission(r,*,gpu=False):
    """CPU validates original evidence; GPU reads only its source-free binding."""
    if gpu:
        a=load(r['production_admission'])
        require(a['status']=='ADMIT_GEOM129_FIXED_FRESH8_PRODUCTION_V136' and a['production_admitted'] is True
            and all(a[k]==r[k] for k in ('training_completion','adapter_weights','head_weights','critic_state','promotion','fresh8_result','contract','domain','source_catalog','protected_baseline')),
            'Explicit real134 production binding, never old105/128PASS')
        for k in ('development_result','promotion','fresh8_result','critic_state','contract'):bound(r[k])
        return
    contract=module(r['contract_code132'],'contract132');c=load(r['contract'])
    for k in contract.REQUIRED_REFS:bound(c[k])
    require(all(c[k]==r[k] for k in ('development_result','promotion','fresh8_result','critic_state','training_completion','adapter_weights','head_weights','protected_baseline','domain','source_catalog'))
        and c['formal_metadata']==r['metadata'],
        'One actual promoted control/fresh8/model/domain contract')
    old=load(r['development_result']);p=load(r['promotion']);fresh=load(r['fresh8_result']);trained=load(r['training_completion'])
    promotion=module(r['promotion_code129'],'promotion129')
    promotion.validate_promotion(old,result_ref=r['development_result'],state_ref=r['critic_state'],
        model_refs={k:r[k] for k in contract.MODEL_REFS})
    contract.validate_lineage(c,old,p,fresh,trained)


def source_scope(r):
    sources=load(r['source_catalog'])['sources'];d=load(r['domain']);contract=module(r['contract_code132'],'contract132')
    with zipfile.ZipFile(bound(r['protected_baseline'])) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None,'Original40.47 ZIP/CRC')
        baseline=[json.loads(x) for x in z.read('predictions.jsonl').splitlines() if x]
    clocks={s['video_id']:load(s['clock']) for s in {x['video_id']:x for x in sources}.values()}
    contract.validate_owner_domain(load(r['contract']),d,sources,baseline,clocks)
    native={x['video_id']:x for x in load(r['metadata'])['records']}
    require(len(native)==426 and all(all(s[k]==native[s['video_id']][k] for k in ('source_sha256','width','height','targetRatioWH')) for s in sources), 'Actual original native dimensions/SHA/ratio')
    return sources,d,baseline,clocks


def selected_scope(r,stage,sources,d):
    if group(stage)=='pilot32':return sources[:32]
    a=load(r['remaining_admission']);pilot=load(a['pilot_output_acceptance'])
    require(a['schema']=='EXPLICIT_GEOM136_MEASURED_REMAINING_ADMISSION' and a['capacity_review_admitted'] is True
        and all(a[k]==r[k] for k in ('domain','source_catalog','training_completion','adapter_weights','head_weights','critic_state','promotion','fresh8_result'))
        and a['remaining_source_ids']==[s['source_id'] for s in sources[32:]]
        and a['deadline_utc']==r['deadline_utc'] and a['max_seconds']>=r['max_seconds']
        and a['max_new_bytes']>=r['max_new_bytes'], 'Exact remaining owner/capacity admission after measured32')
    require(pilot['status']==RAW_PASS and pilot['scope']=='pilot32' and pilot['source_ids']==d['pilot_source_ids']
        and pilot['actual_new_forwards']==32 and pilot['input_acceptance']==a['pilot_input_acceptance']
        and pilot['completion']==a['pilot_GPU_completion'] and pilot['resource']==a['pilot_resource'], 'Adopt actual successful32; no repeated model/QA')
    return sources[32:]


class ChunkReader:
    """At most one accepted chunk resident; tokens only are newly persisted."""
    def __init__(self,r,prepared=None):
        self.r=r;self.prepared=prepared;self.cached_key=None;self.raw=None
        self.base=module(r['base_input_code87'],'input87');self.domain=module(r['domain_code106'],'domain106')
        self.allowed={} if prepared is None else {key(e['input']):e for e in prepared['inference_inputs']}
        self.actual_chunk_loads=0
    def view(self,s):
        import torch
        k=key(s['source_vision'])
        if k!=self.cached_key:
            self.raw=None
            self.raw=torch.load(bound(s['source_vision']),map_location='cpu',weights_only=True)
            self.cached_key=k;self.actual_chunk_loads+=1
        return self.domain.extract_view(self.raw,s,self.base)
    def get(self,inputref):
        import torch
        require(key(inputref) in self.allowed,'Only exact stage input-ref whitelist')
        q=load(inputref);packed,_=self.view(q['source'])
        tokens=torch.load(bound(q['tokens']),map_location='cpu',weights_only=True)
        require(set(tokens)=={'input_ids','attention_mask'},'Only token tensors stored; no duplicated pixel payload')
        values=dict(**tokens,**packed)
        require(self.base.signature(values)==q['input_signature'],'Exact independently accepted F4 signature/chunk row/token bytes')
        return values,q


def tensor_file(path,value,torch):
    with Path(path).open('xb') as f:torch.save(value,f);f.flush();os.fsync(f.fileno())


def prepare(root,rp,r,stage):
    started=time.monotonic()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only136 new input stage');admission(r)
    import torch
    from transformers import AutoProcessor
    sources,d,_,_=source_scope(r);chosen=selected_scope(r,stage,sources,d);scope=group(stage)
    out=Path(r['output_root'])/('inputs_'+scope);out.parent.mkdir(exist_ok=True);out.mkdir(exist_ok=False)
    reader=ChunkReader(r);cfg=load(r['model_config']);processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    entries=[];proofs=[];tokens_by_grid={};newbytes=0
    try:
        for s in chosen:
            deadline(r,started);packed,layout=reader.view(s);grid=tuple(map(tuple,packed['image_grid_thw'].tolist()))
            if grid not in tokens_by_grid:tokens_by_grid[grid]=reader.base.build_text_input(processor,packed['image_grid_thw'])
            tokens,text=tokens_by_grid[grid];qa=reader.base.independent_text_check(processor,packed,tokens,text)
            values=dict(**tokens,**packed);identifier=reader.base.digest(['GEOM136',s['source_id'],s['source_sha256']])[:24]
            tp=out/(identifier+'.tokens.pt');tensor_file(tp,tokens,torch)
            actual=torch.load(tp,map_location='cpu',weights_only=True);require(reader.base.signature(actual)==reader.base.signature(tokens),'New token save/reload exact')
            q=dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role='formal',width=s['width'],height=s['height'],
                input_signature=reader.base.signature(values),image_grid_thw=packed['image_grid_thw'].tolist(),tokens=ref(tp),source=s,
                prompt=reader.base.PROMPT,text_evidence=text,source_layout=s['source_layout'],prefix_extraction=layout,
                native_RGB_recovered=False,actual_input_domain='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',reference_or_target_in_prompt=False,
                **{k:s[k] for k in ('video_id','native_ordinal','native_pts_exact','observation_index','clock','targetRatioWH')})
            qp=out/(identifier+'.json');save(qp,q);proof=out/(identifier+'.first_QA.json')
            save(proof,dict(request=ref(qp),text_QA=qa,source_layout=layout,tokens_roundtrip_exact=True,full_F4_signature=q['input_signature'],
                old_source_processor_repeated=False,new_original_decode=0,new_pixel_tensor_saved=False))
            entries.append(dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role='formal',input=ref(qp)));proofs.append(ref(proof))
            newbytes+=sum(p.stat().st_size for p in (tp,qp,proof));require(newbytes<=r['max_new_bytes'],'Actual new metadata/token bytes exceed budget')
        prepared=dict(schema=INPUT_SCHEMA,scope=scope,inference_inputs=entries,execution_entries=entries,sources=len(chosen),source_catalog=r['source_catalog'],domain=r['domain'],CPU_targets=None,
            training_completion=r['training_completion'],adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],official_source_count=426,
            affected_video_count=len({s['video_id'] for s in chosen}),selection='OBS_INDEX_EVEN',protected_baseline=r['protected_baseline'])
        save(out/'prepared.json',prepared)
        save(out/'input_acceptance.json',dict(status=INPUT_PASS,scope=scope,registration=ref(rp),prepared=ref(out/'prepared.json'),sources=len(chosen),inputs=len(entries),first_QA=proofs,
            elapsed_seconds=time.monotonic()-started,new_bytes=newbytes,actual_chunk_loads=reader.actual_chunk_loads,new_original_decode=0,old_source_processor_repeated=0,model_calls=0))
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),completed_first_QA=proofs,preserve_all_success=True,automatic_retry=False));raise


def validate_stage_inputs(r,p,g,scope):
    require(p['schema']==INPUT_SCHEMA and p['scope']==g['scope']==scope and p['CPU_targets'] is None
        and g['status']==INPUT_PASS and g['prepared']==r['prepared'] and g['registration']==r['CPU_registration']
        and p['inference_inputs']==p['execution_entries'] and len(p['inference_inputs'])==p['sources']==g['sources']==g['inputs']==r['expected_inputs'], 'Exact new stage input acceptance')
    entries=p['inference_inputs']
    require(len({e['id'] for e in entries})==len({e['source_id'] for e in entries})==len(entries)
        and all(e['role']=='formal' for e in entries),'One forward per exact observation owner; repeated videoSHA allowed')
    require(scope!='pilot32' or len(entries)==32,'First exact32 input denominator');return entries


def readonly_model(root,r,callback):
    """Minimal loader adapter, reusing frozen105 state/hidden/inventory helpers."""
    original=load(r['frozen_GPU105_registration']);trained=load(r['training_completion'])
    require(trained['GPU_registration']==r['frozen_GPU105_registration'] and trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY'
        and trained['completed_updates']==778 and trained['total_adopted_plus_new_updates']==798 and trained['adapter_reload_all288_exact'] is True
        and trained['head_reload_all2_exact'] is True and all(trained[k]==r[k] for k in ('adapter_weights','head_weights')),'Exact completed105 model; no failed adapter adoption')
    old18=load(original['original_GPU18']);old32=load(original['original_GPU32'])
    for item in old18['runtime_dependencies']:bound(item)
    old17=load(old18['pair_registration'])
    for name,sha in old17['new_code'].items():require(ref(root/'pair_code_17'/name)['sha256']==sha,'Frozen runtime helper identity')
    helper=module(r['frozen_GPU105_code'],'GPU105');frozen=module(old32['GPU_code'],'io32');math105=module(r['math_code'],'math105');paths()
    require(original['GPU_code']==r['frozen_GPU105_code'] and all(original[k]==r[k] for k in ('model_config','math_code','old_TIME','old_PAIR','old_CROP','frozen_GPU93_code','frozen_math93_code','frozen_math84_code'))
        and trained['recipe']==original['recipe']==math105.RECIPE
        and Path(math105.frozen93.__file__).resolve()==bound(r['frozen_math93_code'])
        and Path(math105.frozen93.frozen84.__file__).resolve()==bound(r['frozen_math84_code']),'Frozen105 L2/decoder/math/base configuration')
    import torch,transformers,peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    from sft_contract import REVISION,verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1','Pinned runtime');verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name']==r['GPU_job'],'One exact active shared GPU job')
    torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats();cfg=load(r['model_config'])
    base=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=REVISION,local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa').eval();base.requires_grad_(False);base.config.use_cache=False
    before=canonical_frozen_hash(base,torch);require(before==trained['base_fingerprint'] and before['sha256']==cfg['expected_base_sha256'],'Physical frozen BASE hash')
    directory=Path(r['adapter_directory']).resolve();adapter=bound(r['adapter_weights'])
    require(directory==adapter.parent==Path(trained['adapter_directory']).resolve() and bound(r['adapter_config'])==directory/'adapter_config.json','Exact final105 adapter directory/config')
    model=PeftModel.from_pretrained(base,str(directory),adapter_name='direct_box',is_trainable=False,local_files_only=True).eval();model.requires_grad_(False)
    head=torch.nn.Linear(4096,3,bias=True,device='cuda:0',dtype=torch.float32);saved=torch.load(bound(r['head_weights']),map_location='cpu',weights_only=True)
    require(set(saved)=={'weight','bias'} and all(v.dtype==torch.float32 and bool(torch.isfinite(v).all()) for v in saved.values()),'Actual F32 head2')
    head.load_state_dict(saved);head.requires_grad_(False);head.eval();_,inventory=helper._inventory(model,head,False,torch)
    initial=helper._trainables(model,head,torch,frozen)
    require(inventory==trained['inventory'] and frozen._same_state(initial['adapter_state_dict'],load_file(str(adapter),device='cpu'),torch)
        and frozen._same_state(initial['head_state_dict'],saved,torch),'All288+head2/inventory actual readonly model identity')
    result=callback(model,head,helper,math105,frozen,torch)
    require(helper._tree_equal(helper._trainables(model,head,torch,frozen),initial,torch) and canonical_frozen_hash(model,torch)==before,'Readonly new role changed bytes')
    for k in ('adapter_weights','head_weights','old_TIME','old_PAIR','old_CROP'):bound(r[k])
    return result,dict(inventory=inventory,base_fingerprint=before,adapter_all288_exact=True,head_all2_exact=True,all_weights_frozen=True,
        physical_GPU_parameters=8774803699,conservative_pipeline_parameters=8790372845,
        peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20)


def gpu_stage(root,rp,r,stage):
    started=time.monotonic()
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Actual parent physical GPU binding');admission(r,gpu=True)
    scope=group(stage);p=load(r['prepared']);g=load(r['input_acceptance']);entries=validate_stage_inputs(r,p,g,scope)
    out=Path(r['output_root'])/('GPU_'+scope);out.mkdir(exist_ok=False);trace=[];completed=[];forward_seconds=[];raw_bytes=0
    journal=out/'attempts.jsonl';journal.touch(exist_ok=False);reader=ChunkReader(r,p)
    def forward(model,head,helper,math105,frozen,torch):
        nonlocal raw_bytes
        for i,e in enumerate(entries):
            deadline(r,started);case_started=time.monotonic();values,q=helper._input(reader,e,torch)
            append_event(journal,event='BEGIN_NEW_ROLE_FORWARD',id=e['id'],input=e['input'],model_role=ROLE,scope=scope)
            trace.append(dict(id=e['id'],returned=False));gpu={k:v.to('cuda:0') for k,v in values.items()}
            with torch.inference_mode():h=helper._hidden(model,gpu,torch,False);cpu=h.float().cpu().contiguous()
            hp=out/('%06d.hidden.pt'%i);frozen._tensor_file(hp,cpu,torch);trace[-1].update(returned=True,raw_hidden=ref(hp))
            with torch.inference_mode():z=head(math105.normalize_hidden(h));zc=z.float().cpu().contiguous()
            zp=out/('%06d.head.pt'%i);frozen._tensor_file(zp,zc,torch);trace[-1]['raw_head']=ref(zp)
            append_event(journal,event='FIRST_RAW_PERSISTED',id=e['id'],model_role=ROLE,raw_hidden=ref(hp),raw_head=ref(zp))
            require(tuple(cpu.shape)==(4096,) and tuple(zc.shape)==(3,) and cpu.dtype==zc.dtype==torch.float32
                and bool(torch.isfinite(cpu).all()) and bool(torch.isfinite(zc).all()),'Persisted actual finite4096/3 first raw')
            with torch.inference_mode():decoded=math105.decode_torch(z,q['width'],q['height']).float().cpu().tolist()
            torch.cuda.synchronize();receipt=out/('%06d.receipt.json'%i)
            save(receipt,dict(id=e['id'],source_id=q['source_id'],source_sha256=q['source_sha256'],input=e['input'],role='formal',model_role=ROLE,scope=scope,
                width=q['width'],height=q['height'],input_signature=q['input_signature'],image_grid_thw=q['image_grid_thw'],raw_hidden=ref(hp),raw_head=ref(zp),decoded_xyw=decoded,
                hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],actual_new_forward=True,alias_of=None,
                native_binding={k:q[k] for k in ('video_id','native_ordinal','native_pts_exact','observation_index')},elapsed_seconds=time.monotonic()-case_started,targets_read=False,no_training=True,no_LM_generation=True))
            forward_seconds.append(time.monotonic()-case_started);raw_bytes+=hp.stat().st_size+zp.stat().st_size+receipt.stat().st_size
            require(raw_bytes+journal.stat().st_size<=r['max_new_bytes'],'Measured136 raw/receipt/journal bytes exceed registered budget')
            completed.append(dict(**e,receipt=ref(receipt)));append_event(journal,event='ACCEPTED_NEW_ROLE_RESULT',id=e['id'],receipt=ref(receipt),model_role=ROLE,alias=False)
            del values,gpu,h,cpu,z,zc
        return completed
    try:
        _,integrity=readonly_model(root,r,forward);deadline(r,started)
        save(out/'completion.json',dict(status='COMPLETE_GEOM136_NEW_STAGE_RAW_NOT_QUALITY',scope=scope,model_role=ROLE,entries=completed,expected_inputs=len(entries),sources=len(entries),
            actual_forward_calls=len(completed),aliases=0,attempts=ref(journal),GPU_registration=ref(rp),input_prepared=r['prepared'],CPU_registration=r['CPU_registration'],input_acceptance=r['input_acceptance'],
            elapsed_forward_seconds=sum(forward_seconds),elapsed_forward_seconds_max=max(forward_seconds,default=0.),new_raw_receipt_bytes=raw_bytes,
            **{k:r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result')},targets_read=False,no_training=True,automatic_next_stage=False))
        save(out/'model_integrity.json',dict(status='PASS_GEOM136_READONLY_MODEL_BYTE_IDENTITY',registration=ref(rp),completion=ref(out/'completion.json'),seconds=time.monotonic()-started,**integrity))
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),attempts=trace,completed=completed,preserve_all_success=True,automatic_retry=False));raise


def review_stage(root,rp,r,stage):
    started=time.monotonic()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent CPU raw QA');admission(r)
    import numpy as np,torch
    scope=group(stage);sources,d,_,_=source_scope(r);chosen=selected_scope(r,stage,sources,d)
    p=load(r['prepared']);g=load(r['input_acceptance']);entries=validate_stage_inputs(r,p,g,scope)
    done=load(r['GPU_completion']);integrity=load(r['model_integrity']);GPUreg=load(done['GPU_registration'])
    require(done['status']=='COMPLETE_GEOM136_NEW_STAGE_RAW_NOT_QUALITY' and done['scope']==scope and done['model_role']==ROLE
        and done['sources']==done['expected_inputs']==done['actual_forward_calls']==len(chosen) and done['aliases']==0
        and done['input_prepared']==r['prepared'] and done['input_acceptance']==r['input_acceptance']
        and all(done[k]==r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result')),'Actual new stage completion/weights/domain')
    trained=load(r['training_completion'])
    require(integrity['status']=='PASS_GEOM136_READONLY_MODEL_BYTE_IDENTITY' and integrity['registration']==done['GPU_registration']
        and integrity['completion']==r['GPU_completion'] and all(integrity[k] is True for k in ('adapter_all288_exact','head_all2_exact','all_weights_frozen'))
        and integrity['physical_GPU_parameters']==8774803699 and integrity['conservative_pipeline_parameters']==8790372845
        and integrity['inventory']==trained['inventory'] and integrity['base_fingerprint']==trained['base_fingerprint'], 'Actual model byte/inventory freeze matches completed105')
    resource_path=Path(r['resource_receipt_path']);ledger_path=Path(r['gpu_ledger_path']);resource=read(resource_path)
    rawqa=module(r['raw_QA_code127'],'rawQA127');rawqa.validate_resource(resource,events(ref(ledger_path)),GPUreg['GPU_job'])
    math105=module(r['math_code'],'math105');review84=module(r['frozen_review84_code'],'review84');geometry=module(r['geometry_code'],'geometry31')
    critic=module(r['critic_code128'],'critic128');promotion=module(r['promotion_code129'],'promotion129')
    with np.load(bound(r['critic_state']),allow_pickle=False) as f:state={k:f[k].copy() for k in f.files}
    critic.validate_state(state);head=torch.load(bound(r['head_weights']),map_location='cpu',weights_only=True)
    journal=events(done['attempts']);require(len(journal)==3*len(entries),'Every new owner has BEGIN/PERSIST/ACCEPT exactly once')
    predictions=[];rawpaths=set();case_proofs=[];records_dir=Path(r['output_root'])/('CPU_QA_records_'+scope);records_dir.mkdir(exist_ok=False)
    for i,(e,record,s) in enumerate(zip(entries,done['entries'],chosen)):
        deadline(r,started);require(all(e[k]==record[k] for k in ('id','source_id','source_sha256','input')) and e['source_id']==s['source_id'],'Fixed exact ordered stage owners')
        q=load(e['input']);receipt=load(record['receipt']);require(receipt['id']==e['id'] and receipt['input']==e['input'] and receipt['input_signature']==q['input_signature']
            and receipt['image_grid_thw']==q['image_grid_thw'] and receipt['scope']==scope and receipt['model_role']==ROLE
            and receipt['actual_new_forward'] is True and receipt['alias_of'] is None and receipt['targets_read'] is False and receipt['no_training'] is True
            and receipt['native_binding']=={k:s[k] for k in ('video_id','native_ordinal','native_pts_exact','observation_index')},'First raw source/grid/token/native/role identity')
        trio=journal[i*3:i*3+3];require([x['event'] for x in trio]==['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT']
            and all(x['id']==e['id'] and x['model_role']==ROLE for x in trio) and trio[0]['input']==e['input'] and trio[2]['receipt']==record['receipt']
            and all(trio[1][k]==receipt[k] for k in ('raw_hidden','raw_head')),'Exact actual BEGIN/raw-persist/accept journal references')
        for name in ('raw_hidden','raw_head'):
            require(receipt[name]['path'] not in rawpaths,'No duplicated successful new raw path');rawpaths.add(receipt[name]['path'])
        h=torch.load(bound(receipt['raw_hidden']),map_location='cpu',weights_only=True);z=torch.load(bound(receipt['raw_head']),map_location='cpu',weights_only=True)
        actual,_=rawqa.validate_raw(h,z,receipt,head,s,math105=math105,review84=review84,geometry=geometry,torch=torch,adapter_weights=r['adapter_weights'],head_weights=r['head_weights'])
        direct=actual['native_boxes']['DIRECT'];projected=critic.trust_project_native3(s['baseline_box'],direct,s['width'],s['height'])['box3']
        gain=promotion.geometry_gain(state,s['baseline_box'],projected,s['width'],s['height']);chosenbox=projected if gain>0 else s['baseline_box']
        predictions.append(dict(**e,receipt=record['receipt'],**actual,baseline_box=s['baseline_box'],trust_box=projected,predicted_gain=gain,chosen_box=chosenbox,
            native_binding=receipt['native_binding'],policy=promotion.POLICY,critic_uses_hidden=False))
        proof=records_dir/('%06d.json'%i);save(proof,dict(status='PASS_GEOM136_ONE_NEW_OWNER_FIRST_RAW_QA',prediction=predictions[-1],registration=ref(rp),model_role=ROLE,
            completion=r['GPU_completion'],training_completion=r['training_completion'],adapter_weights=r['adapter_weights'],head_weights=r['head_weights']))
        case_proofs.append(ref(proof))
    acceptance=dict(status=RAW_PASS,scope=scope,registration=ref(rp),source_ids=[s['source_id'] for s in chosen],predictions=predictions,
        actual_new_forwards=len(predictions),completion=r['GPU_completion'],input_acceptance=r['input_acceptance'],resource=ref(resource_path),gpu_ledger=ref(ledger_path),case_first_QA=case_proofs,
        **{k:r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result','protected_baseline')},
        elapsed_QA_seconds=time.monotonic()-started,input_elapsed_seconds=g['elapsed_seconds'],input_new_bytes=g['new_bytes'],GPU_resource=resource,
        GPU_forward_seconds=done['elapsed_forward_seconds'],GPU_forward_seconds_max=done['elapsed_forward_seconds_max'],automatic_next_stage=False)
    out=Path(r['output_root']);qa=out/('QA_'+scope+'.json');save(qa,acceptance)
    if scope=='remaining':
        a=load(r['remaining_admission']);pilot=load(a['pilot_output_acceptance']);combined=pilot['predictions']+predictions
        require([x['source_id'] for x in combined]==[s['source_id'] for s in sources],'Merged full D retains successful32 without raw reload/QA repeat')
        save(out/'output_acceptance.json',dict(status=FINAL_PASS,predictions=combined,sources=len(sources),actual_new_forwards=len(sources),pilot_acceptance=a['pilot_output_acceptance'],remaining_acceptance=ref(qa),
            official_source_count=426,affected_video_count=d['affected_video_count'],all_times_preserved=True,all_9_16_preserved=True,all_D_outside_preserved=True,
            **{k:r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result','protected_baseline')},no_new_fit=True,no_interpolation=True))


def package(root,rp,r):
    started=time.monotonic()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only independent136 package');admission(r)
    sources,d,base,clocks=source_scope(r);qa=load(r['output_acceptance'])
    require(qa['status']==FINAL_PASS and qa['sources']==len(sources) and all(qa[k]==r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result','protected_baseline')),'Actual complete new136 QA, never old109 qualification')
    helpers=module(r['package_helpers108_code'],'package108_pure');helpers.PARAMETERS=8790372845;helpers.SOURCE=SOURCE;helpers.ARMS=('GEOM11',)
    math105=module(r['math_code'],'math105');critic=module(r['critic_code128'],'critic128');promotion=module(r['promotion_code129'],'promotion129')
    import numpy as np
    with np.load(bound(r['critic_state']),allow_pickle=False) as f:state={k:f[k].copy() for k in f.files}
    boxes={}
    for s,p in zip(sources,qa['predictions']):
        require(s['source_id']==p['source_id'] and s['source_sha256']==p['source_sha256'],'Accepted exact owner order')
        direct=math105.decode_native(p['GPU_head_raw'],s['width'],s['height']);trust=critic.trust_project_native3(s['baseline_box'],direct,s['width'],s['height'])['box3']
        gain=promotion.geometry_gain(state,s['baseline_box'],trust,s['width'],s['height']);box=trust if gain>0 else s['baseline_box']
        require(direct==p['native_boxes']['DIRECT'] and trust==p['trust_box'] and gain==p['predicted_gain'] and box==p['chosen_box'],'Independent saved GPU-F32→native→trust→GEOM replay')
        boxes[s['source_id']]={'GEOM11':box}
    predictions,changes=helpers.patch_protected(base,sources,boxes,arm='GEOM11',clocks=clocks,legal=math105.legal_native)
    contract=module(r['contract_code132'],'contract132');contract.validate_protected_overlay(base,predictions,sources)
    history=helpers.history_digests(load(r['historical_registry']));disposition,canonical=helpers.disposition(predictions,base,changes,history,set())
    out=Path(r['output_root'])/'package';out.mkdir(exist_ok=False)
    if disposition!='NEW_DISTINCT_CANDIDATE':save(out/'STOP.json',dict(status=disposition,canonical_sha256=canonical,new_ZIP=0));return
    inherited=load(r['inherited_baseline_completion']);require(inherited['sha256']==contract.BASELINE_SHA and inherited['frames']==123506 and inherited['records']==426 and inherited['independent11strict'] is True,'Adopt original40.47 engineering receipt')
    field=load(r['source_field_inputs']);require(len(field['source_field_files'])==4,'Adopt complete original source spatial field')
    for x in [*field['source_field_files'].values(),field['source_manifest'],field['source_clocks']]:helpers.reference(x)
    for x in r['cost_evidence_refs']:bound(x)
    require(r['cost_evidence_refs'],'Actual adopted/train/pilot/remaining costs required')
    provenance=helpers.replace_provenance(events(r['inherited_provenance']),base,changes,arm='GEOM11',qa_ref=r['output_acceptance'],proof_ref=ref(rp))
    helpers.write_lines(out/'predictions.jsonl',predictions);helpers.write_lines(out/'provenance.jsonl',provenance)
    save(out/'complete_source_field_overlay.json',dict(schema='INHERITED_COMPLETE_FIELD_PLUS_GEOM129_EXACT_PTS_V136',inherited_source_field_inputs=r['source_field_inputs'],domain=r['domain'],changes=changes,
        whole426_preserved=True,all_original_times_unchanged=True,all_vertical_boxes_unchanged=True,outside_D_boxes_unchanged=True,new_interpolation=False))
    loader=Path(r['strict_loader_root']).resolve();require(r['strict_loader_code_refs'] and all(bound(x).is_relative_to(loader) for x in r['strict_loader_code_refs']),'Explicit frozen independent strict-loader code')
    validator=out/'independent_validate_geom136.py';text=helpers.strict_validator_text(bound(r['original_independent_validator']).read_text(encoding='utf-8'))
    with validator.open('x',encoding='utf-8') as f:f.write(text)
    pending=out/'candidate_GEOM129.PENDING.zip'
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(out/'predictions.jsonl','predictions.jsonl')
    deadline(r,started);end=dt.datetime.fromisoformat(r['deadline_utc'].replace('Z','+00:00'))
    argv=[sys.executable,'-B',str(validator),'--strict-loader-root',str(loader),'--metadata',str(bound(r['metadata'])),'--selected',str(bound(r['inherited_selected'])),
        '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent11.json')]
    subprocess.run(argv,check=True,timeout=max(1,int(min((end-dt.datetime.now(dt.timezone.utc)).total_seconds(),r['max_seconds']-(time.monotonic()-started)))),stdout=subprocess.DEVNULL)
    strict=read(out/'independent11.json');require(len(strict['checks'])==11 and all(v is True for v in strict['checks'].values()),'Actual independent11strict PASS')
    with zipfile.ZipFile(pending) as z:require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and helpers.file_sha(out/'predictions.jsonl')==__import__('hashlib').sha256(z.read('predictions.jsonl')).hexdigest(),'ZIP CRC/memberSHA')
    deadline(r);final=out/'candidate_GEOM129.zip';require(not final.exists(),'Exclusive final ZIP');pending.rename(final)
    save(out/'receipt.json',dict(status='PASS_GEOM136_ENGINEERING_FRESH8_FILE_QUALIFIED_OFFICIAL_UNKNOWN',zip=ref(final),canonical_sha256=canonical,official_sources=426,native_frames=123506,
        changed_boxes=len(changes),whole426_preserved=True,all_original_times_unchanged=True,all_vertical_boxes_unchanged=True,outside_D_boxes_unchanged=True,independent11strict=True,
        parameters=8790372845,additional_parameters=135393,source_tag=SOURCE,registration=ref(rp),output_acceptance=r['output_acceptance'],promotion=r['promotion'],fresh8_result=r['fresh8_result'],
        model={k:r[k] for k in ('training_completion','adapter_weights','head_weights','critic_state')},cost_evidence_refs=r['cost_evidence_refs'],old128_STOP_unchanged=True,official_score='UNKNOWN',automatic_website_submission=False))


def run(root,registration,stage):
    root=Path(root).resolve();rp=Path(registration).resolve();r=read(rp);validate_registry(root,rp,r,stage)
    try:
        if stage.startswith('prepare'):return prepare(root,rp,r,stage)
        if stage.startswith('gpu'):return gpu_stage(root,rp,r,stage)
        if stage in ('qa32','qa_merge'):return review_stage(root,rp,r,stage)
        return package(root,rp,r)
    except BaseException as error:
        out=Path(r['output_root'])
        if out.is_dir() and not (out/(stage+'_failure.json')).exists():
            save(out/(stage+'_failure.json'),dict(utc=utc(),stage=stage,registration=ref(rp),error=repr(error),traceback=traceback.format_exc(),
                preserve_all_success=True,automatic_retry=False,partial_first_QA_directory=str(out/('CPU_QA_records_'+group(stage))),failure_is_not_empty=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True);p.add_argument('--stage',choices=STAGES,required=True)
    a=p.parse_args();run(a.root,a.registration,a.stage)
