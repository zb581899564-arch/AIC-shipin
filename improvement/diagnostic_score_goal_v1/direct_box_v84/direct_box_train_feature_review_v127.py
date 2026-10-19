"""First CPU QA of the new train602 raw feature pass; labels are never read."""
from __future__ import annotations
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import numpy as np

_here=Path(__file__).resolve()
for _support in (_here.parents[1]/'pair_code_17',_here.parents[1],_here.parents[2]/'pair_code_17'):
    if (_support/'pair_common.py').is_file():sys.path.insert(0,str(_support));break
from pair_common import WORK,read,save,ref,bound,require

STATUS='PASS_DIRECT_BOX127_TRAIN602_FIRST_RAW_HEAD_NATIVE_CPU_QA'
FEATURE_SCHEMA='DIRECT_BOX127_ACCEPTED_TRAIN602_SOURCE_FEATURES'


def module(reference,name):
    p=bound(reference);sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def validate_raw(hidden,raw,receipt,head,source,*,math105,review84,geometry,torch,adapter_weights,head_weights):
    require(isinstance(hidden,torch.Tensor) and hidden.device.type=='cpu' and hidden.dtype==torch.float32
        and tuple(hidden.shape)==(4096,) and not hidden.requires_grad and bool(torch.isfinite(hidden).all()),'Actual finite raw F32CPU hidden4096')
    require(isinstance(raw,torch.Tensor) and raw.device.type=='cpu' and raw.dtype==torch.float32 and tuple(raw.shape)==(3,)
        and not raw.requires_grad and bool(torch.isfinite(raw).all()),'Actual finite raw F32CPU head3')
    require(receipt['adapter_weights']==adapter_weights and receipt['head_weights']==head_weights
        and all(receipt[k]==source[k] for k in ('source_id','source_sha256','width','height'))
        and receipt['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS','Actual model/source/dims/L2 identity')
    weights=review84.validate_head(head);normalized=math105.normalize_hidden(hidden)
    cpu=weights['weight']@normalized.double().numpy()+weights['bias'];actual=raw.double().numpy()
    require(bool(np.all(np.abs(cpu-actual)<=review84.ATOL+review84.RTOL*np.abs(cpu))),'Independent CPU64 head replay')
    W,H=source['width'],source['height'];decoded=math105.decode_numpy(actual,W,H);saved=np.asarray(receipt['decoded_xyw'],np.float64)
    require(saved.shape==(3,) and bool(np.isfinite(saved).all()) and bool(np.all(np.abs(decoded-saved)<=1e-5*max(W,H))),
        'GPU continuous decode matches independent CPU raw-head geometry')
    native=[int(v) for v in review84.independent_native(actual,W,H)]
    require(native==math105.decode_native(actual,W,H) and geometry.legal(native,W,H),'Independent legal native DIRECT')
    return dict(CPU_head_raw64=[float(x) for x in cpu],GPU_head_raw=[float(x) for x in actual],
        native_boxes=dict(DIRECT=native),continuous_xyw64=[float(x) for x in decoded],
        maximum_absolute_linear_error=float(np.max(np.abs(cpu-actual))),hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',
        original_hidden_l2_norm=float(torch.linalg.vector_norm(hidden)),normalized_hidden_l2_norm=float(torch.linalg.vector_norm(normalized))),normalized


def validate_resource(resource,ledger,job):
    require(resource['name']==job and resource['status']=='completed' and resource['exit_code']==0
        and [r for r in ledger if r.get('name')==job]==[resource],'Unique actual127 resource terminal/ledger')


def review_scope(reg,registration_ref,done,integrity,expected,sources,head,*,load_json,load_tensor,load_events,math105,review84,geometry,torch,expected_count=602):
    """Callbacks allow a bounded synthetic loop test, with actual math/head QA."""
    require(done['status']=='COMPLETE_DIRECT_BOX127_TRAIN602_RAW_NOT_QUALITY' and done['model_role']=='DIRECT_BOX105_TRAIN602_FEATURES'
        and done['purpose']==reg['purpose']=='CRITIC_TRAIN_FEATURES_ONLY'
        and done['GPU_registration']==registration_ref and done['input_prepared']==reg['prepared']
        and done['CPU_registration']==reg['CPU_registration'] and done['input_acceptance']==reg['input_acceptance']
        and done['training_completion']==reg['training_completion']
        and done['adapter_weights']==reg['adapter_weights'] and done['head_weights']==reg['head_weights']
        and done['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS' and done['targets_read'] is False and done['no_training'] is True,
        'Actual new train-only127 completed artifact binding')
    require(integrity['status']=='PASS_DIRECT_BOX127_READONLY_MODEL_BYTE_IDENTITY' and integrity['registration']==registration_ref
        and integrity['training_completion']==reg['training_completion'] and integrity['adapter_all288_exact'] is True
        and integrity['head_all2_exact'] is True and integrity['all_weights_frozen'] is True
        and integrity['targets_read'] is False and integrity['no_training'] is True,'Independent model byte freeze receipt')
    owners={s['source_id']:s for s in sources};entries=done['entries']
    require(len(expected)==len(entries)==len(owners)==len(sources)==expected_count
        and len({e['source_sha256'] for e in expected})==expected_count
        and done['expected_inputs']==done['sources']==done['actual_forward_calls']==expected_count and done['aliases']==0,
        'Every unique registered train source has one new raw, no hidden alias')
    events=load_events(done['attempts']);require(len(events)==3*expected_count,'Exact BEGIN/PERSIST/ACCEPT event inventory')
    predictions=[];hidden_rows=[];normalized_rows=[];raw_rows=[];native_rows=[];seen=set()
    for index,(entry,record) in enumerate(zip(expected,entries)):
        require(entry['role']=='train' and all(entry[k]==record[k] for k in ('id','source_id','source_sha256','input')),'Original train602 ordered entry bindings')
        q=load_json(entry['input']);receipt=load_json(record['receipt']);source=owners[entry['source_id']]
        require(source['role']=='train' and q['role']==receipt['role']=='train' and q['id']==entry['id']
            and all(q[k]==receipt[k]==source[k] for k in ('source_id','source_sha256','width','height'))
            and all(receipt[k]==record[k] for k in ('id','source_id','source_sha256','input'))
            and q['reference_or_target_in_prompt'] is False and receipt['model_role']=='DIRECT_BOX105_TRAIN602_FEATURES'
            and receipt['input_signature']==q['input_signature'] and set(q['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'}
            and receipt['image_grid_thw']==q['image_grid_thw'] and len(q['image_grid_thw'])==1
            and receipt['actual_new_forward'] is True and receipt['alias_of'] is None and receipt['targets_read'] is False
            and not any(k in q for k in ('labels','target','candidate_ious','original_reference_xywh')),'Actual label-free source-only input and new train purpose')
        for name in ('raw_hidden','raw_head'):
            key=(receipt[name]['path'],receipt[name]['sha256']);require(key not in seen,'Each new train owner must have distinct raw');seen.add(key)
        hidden,raw=load_tensor(receipt['raw_hidden']),load_tensor(receipt['raw_head'])
        actual,normalized=validate_raw(hidden,raw,receipt,head,source,math105=math105,review84=review84,geometry=geometry,torch=torch,
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'])
        block=events[3*index:3*index+3]
        require([r['event'] for r in block]==['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT']
            and all(r['id']==entry['id'] and r['model_role']==done['model_role'] for r in block)
            and block[0]['input']==entry['input'] and block[1]['raw_hidden']==receipt['raw_hidden']
            and block[1]['raw_head']==receipt['raw_head'] and block[2]['receipt']==record['receipt'] and block[2]['alias'] is False,
            'Actual first persistence journal and owner identity')
        predictions.append(dict(**record,raw_hidden=receipt['raw_hidden'],raw_head=receipt['raw_head'],
            width=int(source['width']),height=int(source['height']),adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],**actual))
        hidden_rows.append(hidden.numpy().copy());normalized_rows.append(normalized.numpy().copy());raw_rows.append(raw.numpy().copy());native_rows.append(actual['native_boxes']['DIRECT'])
    features=dict(ids=np.asarray([e['id'] for e in expected]),source_ids=np.asarray([e['source_id'] for e in expected]),
        source_sha256=np.asarray([e['source_sha256'] for e in expected]),width=np.asarray([owners[e['source_id']]['width'] for e in expected],np.int64),
        height=np.asarray([owners[e['source_id']]['height'] for e in expected],np.int64),hidden4096=np.stack(hidden_rows),
        normalized_hidden4096=np.stack(normalized_rows),raw_head3=np.stack(raw_rows),native_DIRECT3=np.asarray(native_rows,np.int64))
    return dict(status=STATUS,feature_schema=FEATURE_SCHEMA,predictions=predictions,sources=expected_count,actual_new_forwards=expected_count,
        aliases=0,model_calls=0,labels_read=False,prior_first_QA_repeated=False,quality_established=False,
        purpose=reg['purpose'],registration=registration_ref,training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights']),features


def run(root,registration):
    root=Path(root).resolve();rp=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and root.is_relative_to(WORK)
        and rp==root/'direct_box_train_feature_GPU_registration_127.json','One CPU-only127 first output review')
    acceptance=root/'direct_box_train_feature_output_acceptance_127.json'
    require(not acceptance.exists(),'Never repeat successful127 first QA')
    reg=read(rp);registration_ref=ref(rp)
    require(bound(reg['review_code'])==Path(__file__).resolve(),'Exact independent127 CPU reviewer')
    gpu=module(reg['GPU_code'],'_review127_gpu_contract');math105=module(reg['math_code'],'_review127_math105')
    review84=module(reg['frozen_review84_code'],'_review127_independent84');geometry=module(reg['geometry_code'],'_review127_geometry31')
    prepared=read(bound(reg['prepared']));gate=read(bound(reg['input_acceptance']));expected=gpu.validate_inputs(reg,prepared,gate)
    original=read(bound(reg['frozen_GPU105_registration']));trained=read(bound(reg['training_completion']));gpu.validate_training(reg,original,trained)
    prior=read(bound(reg['training_output_acceptance']))
    require(prior['status']=='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA' and prior['training_completion']==reg['training_completion']
        and prior['registration']==reg['frozen_GPU105_registration'] and all(prior[k]==reg[k] for k in ('adapter_weights','head_weights')),
        'Adopt successful105 training/oldraw QA, never repeat it')
    require(Path(math105.frozen93.__file__).resolve()==bound(reg['frozen_math93_code'])
        and Path(math105.frozen93.frozen84.__file__).resolve()==bound(reg['frozen_math84_code']),'Exact normalizer/decoder dependencies')
    resource_path=Path(reg['resource_receipt_path']).resolve();ledger_path=Path(reg['gpu_ledger_path']).resolve()
    require(resource_path.is_relative_to(WORK) and ledger_path.is_relative_to(WORK),'Explicit shared-resource paths stay in work root')
    resource_ref,ledger_ref=ref(resource_path),ref(ledger_path);resource=read(bound(resource_ref))
    ledger=[json.loads(row) for row in bound(ledger_ref).read_text().splitlines() if row]
    validate_resource(resource,ledger,reg['GPU_job'])
    out=Path(reg['output_directory']).resolve();require(out==root/'direct_box_train_features_127','Exact new output directory')
    completion_ref=ref(out/'completion.json');done=read(bound(completion_ref));integrity_ref=ref(out/'model_integrity.json');integrity=read(bound(integrity_ref))
    require(integrity['completion']==completion_ref and integrity['inventory']==trained['inventory']
        and integrity['base_fingerprint']==trained['base_fingerprint'],'Full model/inventory and completion identity')
    catalog=read(bound(reg['source_catalog']));sources=[s for s in catalog['sources'] if s['role']=='train']
    import torch
    torch.set_num_threads(2);require(not torch.cuda.is_initialized(),'CPU first QA never initializes CUDA')
    head=torch.load(bound(reg['head_weights']),map_location='cpu',weights_only=True)
    accepted,features=review_scope(reg,registration_ref,done,integrity,expected,sources,head,load_json=lambda r:read(bound(r)),
        load_tensor=lambda r:torch.load(bound(r),map_location='cpu',weights_only=True),
        load_events=lambda r:[json.loads(x) for x in bound(r).read_text().splitlines() if x],math105=math105,review84=review84,geometry=geometry,torch=torch)
    cache=out/'accepted_features.npz'
    with cache.open('xb') as f:np.savez(f,**features);f.flush();os.fsync(f.fileno())
    with np.load(cache,allow_pickle=False) as loaded:
        require(set(loaded.files)==set(features) and all(np.array_equal(loaded[k],v) for k,v in features.items()),'Exact newly persisted compact feature reload')
    accepted.update(accepted_features=ref(cache),completion=completion_ref,model_integrity=integrity_ref,resource=resource_ref,gpu_ledger=ledger_ref,
        input_prepared=reg['prepared'],input_acceptance=reg['input_acceptance'],source_catalog=reg['source_catalog'],training_output_acceptance=reg['training_output_acceptance'])
    save(acceptance,accepted)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.registration)
