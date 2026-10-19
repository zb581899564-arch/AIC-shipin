"""Independent first raw QA, then fixed profile policy; no model/processor IO."""
import argparse
import datetime as dt
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read,save,ref,bound,require,utc


def module(reference,name):
    path=bound(reference);sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result);return result


def run(root,scope,rp):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent CPU-only utility60 review')
    import torch
    torch.set_num_threads(2)
    reg=read(rp);require(bound(reg['review_code'])==Path(__file__).resolve() and reg['scope']==scope,'Exact registered CPU review')
    topref=ref(root/'utility_inference_59'/scope/'completion.json');top=read(bound(topref))
    require(top['status']=='COMPLETE_UTILITY_V59_READONLY_SCOPE_NOT_QUALITY' and top['GPU_registration']==ref(rp)
        and top['input_acceptance']==reg['input_acceptance'] and top['prepared']==reg['prepared']
        and top['training_completion']==reg['training_completion'] and top['labels_read'] is False
        and top['new_optimizer_updates']==0,'Actual complete readonly new scope')
    qa56=module(reg['frozen_review56_code'],'_utility60_frozen_review56')
    gpu=module(reg['GPU_code'],'_utility60_registered_gpu59');math60=module(reg['policy_math_code'],'_utility60_fixed_math')
    qa56.validate_inventory(top,read(bound(reg['model_config'])))
    require(top['adapter_weights']==reg['adapter_weights'] and top['value_weights']==reg['value_weights'],'Actual saved model identity')
    resource_ref=ref(root/('utility_'+scope+'_resource_receipt_60.json'));resource=read(bound(resource_ref))
    require(resource['unique_ledger_entries']==1 and resource['record']['status']=='completed' and resource['record']['exit_code']==0,
        'Unique naturally completed shared GPU terminal')
    gate=read(bound(reg['input_acceptance']));prepared=read(bound(reg['prepared']))
    entries=gpu.validate_prepared(reg,gate,prepared)
    external=gpu.adopted_index(reg['adopted_output_acceptances'],reg['adapter_weights'],reg['value_weights'],reg['training_completion'])
    ordered=read(bound(top['completion']));require(ordered['GPU_registration']==ref(rp)
        and ordered['scope']==scope and ordered['model_role']==reg['model_role'] and ordered['expected_inputs']==len(entries)
        and len(ordered['entries'])==len(entries),'Exact complete ordered scope')
    value_state=torch.load(bound(reg['value_weights']),map_location='cpu',weights_only=True)
    _,beta=qa56.validate_value(value_state)
    out=root/'utility_review_60'/scope;out.mkdir(parents=True,exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),registration=ref(rp),new_model_calls=0,old_first_QA_repeated=False))
    try:
        events=[json.loads(s) for s in bound(ordered['attempts']).read_text().splitlines() if s]
        offset=0;seen={};previous={};values={};predictions=[];calls=aliases=external_count=0;maximum_error=0.
        for expected,record in zip(entries,ordered['entries']):
            require(all(record[k]==expected[k] for k in ('id','source_id','source_sha256','input')),'Ordered accepted input/output identities')
            receipt=read(bound(record['receipt']));request=read(bound(expected['input']))
            require(all(receipt[k]==expected[k] for k in ('id','source_id','source_sha256','input'))
                and request['id']==expected['id'] and request['source_id']==expected['source_id']
                and request['source_sha256']==expected['source_sha256'] and receipt['input_signature']==request['input_signature']
                and receipt['class_token_ids']==prepared['class_token_ids']==request['class_token_ids']
                and receipt['image_grid_thw']==request['image_grid_thw'] and receipt['adapter_weights']==reg['adapter_weights']
                and receipt['value_weights']==reg['value_weights'] and receipt['model_role']==reg['model_role']
                and receipt['scope']==scope and receipt['profile']==reg['profile'] and receipt['screen_reference_read'] is False
                and receipt['native_RGB_recovered'] is False and request['reference_or_target_in_prompt'] is False,
                'Raw receipt owner/model/input/geometry scope')
            flags=[receipt[k] for k in ('actual_new_forward','external_alias','internal_alias')]
            require(all(type(x)==bool for x in flags) and sum(flags)==1,'Exclusive actual forward/external/internal alias')
            key=gpu.exact_key(request,reg['adapter_weights'],reg['value_weights'])
            if receipt['actual_new_forward']:
                require(key not in seen and key not in external and receipt['alias_of'] is None,'Never repeat a successful exact forward')
                raw=torch.load(bound(receipt['raw_hidden']),map_location='cpu',weights_only=True)
                actual=qa56.validate_raw(raw,receipt,value_state);cpu_value=actual['CPU_value'];maximum_error=max(maximum_error,actual['absolute_error'])
                del raw
                names=['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT'];calls+=1
            elif receipt['external_alias']:
                prior=external[key]
                require(receipt['raw_hidden']==prior['raw_hidden'] and receipt['alias_of']==prior['receipt']
                    and receipt['adopted_from_acceptance']==prior['acceptance'] and receipt['adopted_input']==prior['input']
                    and receipt['adopted_model_role']==prior['model_role'] and receipt['head_value']==prior['GPU_value']
                    and 'CPU_value' in prior,'Adopt exact already first-QAd raw/value without raw reload')
                cpu_value=prior['CPU_value'];names=['ADOPTED_PREVIOUSLY_QA_RAW','ACCEPTED_NEW_ROLE_RESULT'];external_count+=1
            else:
                prior=previous.get(receipt['alias_of']['path'])
                require(prior is not None and prior['key']==key and prior['raw_hidden']==receipt['raw_hidden']
                    and prior['GPU_value']==receipt['head_value'] and prior['receipt']==receipt['alias_of'],
                    'Only earlier exact same-input alias')
                cpu_value=prior['CPU_value'];names=['ACCEPTED_NEW_ROLE_RESULT'];aliases+=1
            block=events[offset:offset+len(names)];offset+=len(names)
            require([x['event'] for x in block]==names and all(x['id']==record['id'] and x['model_role']==reg['model_role'] for x in block),
                'Exact raw-first ordered journal')
            require(block[-1]['receipt']==record['receipt'] and block[-1]['external_alias']==receipt['external_alias']
                and block[-1]['internal_alias']==receipt['internal_alias'],'Journal receipt and alias flags')
            if receipt['actual_new_forward']:require(block[0]['input']==record['input'] and block[1]['raw_hidden']==receipt['raw_hidden'],'Raw persisted before acceptance')
            if receipt['external_alias']:require(block[0]['raw_hidden']==receipt['raw_hidden'] and block[0]['adopted_from_acceptance']==receipt['adopted_from_acceptance'],'External adoption journal')
            require(math.isfinite(cpu_value),'Finite accepted CPU value')
            values[record['id']]=dict(source_id=record['source_id'],source_sha256=record['source_sha256'],CPU_value=cpu_value)
            prediction=dict(**record,raw_hidden=receipt['raw_hidden'],CPU_value=cpu_value,GPU_value=receipt['head_value'],
                adapter_weights=reg['adapter_weights'],value_weights=reg['value_weights'])
            predictions.append(prediction);seen.setdefault(key,prediction)
            previous[record['receipt']['path']]=dict(key=key,**prediction)
        require(offset==len(events) and calls==ordered['actual_forward_calls'] and aliases==ordered['aliases']
            and external_count==ordered['external_aliases'] and calls+aliases+external_count==len(entries), 'Exact unique complete raw scope/counts')
        require(not torch.cuda.is_initialized(),'CPU reviewer cannot initialize CUDA')
        accepted=out/'output_acceptance.json'
        save(accepted,dict(status='PASS_UTILITY59_FIRST_OUTPUT_QA',scope=scope,registration=ref(rp),completion=top['completion'],
            top_completion=topref,training_completion=reg['training_completion'],resource=resource_ref,
            adapter_weights=reg['adapter_weights'],value_weights=reg['value_weights'],predictions=predictions,
            actual_new_forwards=calls,external_adopted=external_count,internal_aliases=aliases,
            maximum_absolute_dot_error=maximum_error,old_first_QA_repeated=False,quality_established=False,production_admitted=False))
        sources=read(bound(prepared['source_catalog']))['sources'];plan=read(bound(prepared['case_plan']))
        require(plan['GT_used_for_input_or_pair_choice'] is False,'Fixed label-free pool')
        policy=module(reg['frozen_policy33_code'],'_utility60_original_policy33')
        with np.load(bound(reg['old_gain_state']),allow_pickle=False) as data:old_gain={k:data[k].copy() for k in data.files}
        old_geometry=read(bound(reg['old_geometry_control']))
        with np.load(bound(old_geometry['coefficients']),allow_pickle=False) as data:old_beta=data['beta'].copy()
        policy_outputs,proof=math60.policy_predictions(sources,plan['pair_index'],values,beta,old_gain,old_beta,policy.geometry_features)
        if scope=='production':
            save(out/'policy.json',dict(status='COMPLETE_UTILITY_NATIVE_COORDINATE_CHOICES_ENGINEERING_ONLY',scope=scope,
                output_acceptance=ref(accepted),predictions=policy_outputs,proof=proof,GT_read=False,packaging_admitted=False));return
        targets=read(bound(prepared['CPU_targets']))
        require(targets['status']=='UTILITY58_ORIGINAL_REFERENCES_AND_AFFINE_CPU_ONLY' and targets['scope']==scope,
            'Separate unchanged original reference plus exact-affine CPU evidence')
        result=math60.evaluate(sources,policy_outputs,targets['sources'],proof,policy);admitted=result['quality']['admitted']
        save(out/'result.json',dict(status=('PASS_UTILITY_RESIZED20_PROFILE_ONLY' if scope=='resized20' else 'PASS_UTILITY_RESIZED19_CONFIRM_ONLY')
            if admitted else 'STOP_UTILITY_'+scope.upper()+'_REJECTED',primary='UTILITY',quality=result['quality'],evaluation=result,
            adapter_weights=reg['adapter_weights'],value_weights=reg['value_weights'],fixed_final_checkpoint=True,
            confirm_admitted=admitted if scope=='resized20' else False,production_admitted=False,
            output_acceptance=ref(accepted),scope=scope,registration=ref(rp),CPU_targets=prepared['CPU_targets'],
            historical_not_blind=True,official_joint_quality=False,new_model_calls=0))
    except BaseException as e:
        save(out/'failure.json',dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),preserve_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--scope',choices=['resized20','resized19','production'],required=True)
    p.add_argument('--registration',type=Path,required=True);a=p.parse_args();run(a.root,a.scope,a.registration)
