"""Production batch/activation contracts only; no model/data side effects."""
import hashlib
import json
import re

SCHEMA='TEMPORAL_PRODUCTION_RUNTIME_V3'
PARAMETERS=8782459120
BASE_PARAMETERS=8767123696
ADAPTER_PARAMETERS=PARAMETERS-BASE_PARAMETERS
LORA_LAYERS=144
WEIGHT_STRATEGY='FULL_ENGINE_LOAD_AND_FULL_BATCH_END_BASE_288_ADAPTER_REHASH_PER_CALL_FROZEN_INVENTORY'


def require(ok,why):
    if not ok:raise ValueError(why)


def safe_id(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',value) and '..' not in value,
            'Explicit safe frozen identifier required')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def source_video_projection(plan):
    result={};seen=set()
    for source in plan['sources']:
        value=source['video_id']
        require(type(value) in (int,str) and str(value)==str(int(value)),'Original canonical video_id must be integer 0..425')
        vid=int(value);sid=source['source_id']
        require(sid not in result and vid not in seen,'Source ID / original video_id projection is not one-to-one')
        result[sid]=vid;seen.add(vid)
    require(len(result)==426 and seen==set(range(426)),'Complete official 0..425 source projection required')
    return result


def batch_membership(batch,plan):
    safe_id(batch['batch_id'])
    sources=[source['source_id'] for source in plan['sources']]
    ids=batch['source_ids']
    require(isinstance(ids,list) and ids and len(set(ids))==len(ids) and all(sid in sources for sid in ids),
            'Batch requires unique registered source IDs')
    indices=[sources.index(sid) for sid in ids]
    require(indices==list(range(indices[0],indices[0]+len(ids))), 'Batch must be a contiguous frozen source-order block')
    rows=[row for row in plan['requests'] if row['source_id'] in ids]
    logical=[row['request_id'] for row in rows]
    actual=[row['request_id'] for row in rows if row['execution']=='MODEL']
    require(batch['logical_request_ids']==logical and batch['request_ids']==actual and batch['actual_model_call_budget']==len(actual),
            'Every source all consumers and typed pre-model skips must stay in one fixed batch')
    require(len(actual)>0 and len(actual)<=1995 and batch['membership_reason']=='FROZEN_SOURCE_ORDER_AND_ACTUAL_CAPACITY_ONLY' and
            batch['predictions_or_reference_metrics_used_for_membership'] is False,
            'Nonempty actual budget/capacity-only batch needed; empty batches use CPU-only global coverage receipt')
    return rows


def layer_state(model,disabled,expected_names=None):
    layers=[(name,layer) for name,layer in model.named_modules() if hasattr(layer,'disable_adapters') and hasattr(layer,'lora_A')]
    names=[name for name,_ in layers];flags=[bool(layer.disable_adapters) for _,layer in layers]
    require(len(names)==len(set(names))==LORA_LAYERS and flags==[disabled]*LORA_LAYERS and model.active_adapter=='default' and
            (expected_names is None or names==expected_names),'All actual 144 adapter states/identities must match')
    return dict(layer_names=names,disable_adapters=flags,layers=LORA_LAYERS,active_adapter='default',
        activated_parameters=BASE_PARAMETERS if disabled else PARAMETERS)


def serialized_state(state,disabled,names):
    require(state['layer_names']==names and len(set(names))==LORA_LAYERS and state['layers']==LORA_LAYERS and
        state['disable_adapters']==[disabled]*LORA_LAYERS and state['active_adapter']=='default' and
        state['activated_parameters']==(BASE_PARAMETERS if disabled else PARAMETERS),'Recorded adapter activation proof differs')


def inventory(model):
    seen=set();total=adapter=0
    for name,parameter in model.named_parameters():
        if id(parameter) in seen:continue
        seen.add(id(parameter));require(not parameter.requires_grad,'Production model parameter is trainable')
        total+=parameter.numel()
        if 'lora_' in name:adapter+=parameter.numel()
    require(total==PARAMETERS and adapter==ADAPTER_PARAMETERS and total-adapter==BASE_PARAMETERS,
            'Original physical/base/loaded TIME adapter count changed')
    return dict(actual_physical_parameters=total,loaded_adapter_parameters=adapter,base_parameters=total-adapter,
        adapter_unloaded=False,optimizer_updates=0)


def restore_gradients(model):
    before=[(name,p.numel()) for name,p in model.named_parameters() if p.requires_grad]
    model.requires_grad_(False)
    require(not any(p.requires_grad for p in model.parameters()),'Post-PEFT explicit gradient freeze failed')
    return dict(action='MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT',
        trainable_tensor_count_before_restore=len(before),trainable_parameters_before_restore=sum(n for _,n in before),
        trainable_tensor_count_after_restore=0,trainable_parameters_after_restore=0,optimizer_updates=0)
