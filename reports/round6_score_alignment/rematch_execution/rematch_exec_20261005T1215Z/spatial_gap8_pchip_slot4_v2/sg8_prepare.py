"""Seal predictions before any probe answer and prepare exact native CPU inputs."""
import argparse
import ast
import hashlib
import inspect
from pathlib import Path
import sys
import traceback

from sg8_common import (HERE,RUN,OLD,V14,BASE_SHA,read,rows,sha,digest,save,require,
                        state,utc,old_helpers,inputs)
from sg8_math import interpolate
from sg8_independent_math import rebuild


def method_identity(path):
    tree=ast.parse(Path(path).read_bytes())
    klass=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Qwen3VL')
    result={x.name:hashlib.sha256(ast.dump(x,include_attributes=False).encode()).hexdigest()
        for x in klass.body if isinstance(x,ast.FunctionDef) and x.name in ('__init__','_generate','predict_focus')}
    for x in tree.body:
        if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id in
            ('DEFAULT_MAX_PIXELS','DEFAULT_MAX_VIDEO_FRAMES','DEFAULT_CROP_TOKENS') for t in x.targets):
            result[x.targets[0].id]=hashlib.sha256(ast.dump(x.value,include_attributes=False).encode()).hexdigest()
    return result


def seal():
    require(read(HERE/'g0_asset_handoff.json')['status'].startswith('PASS_ACTUAL_ORIGINAL_ASSET'), 'actual asset handoff required')
    plan=read(HERE/'input_01/sample_plan.json')
    exposure=read(HERE/'g0_exposure_review.json')
    require(exposure['status']=='PASS_CURRENT_REPLAN_SAMPLE_EXPOSURE_PROVENANCE' and
        exposure['sample_plan_sha256']==sha(HERE/'input_01/sample_plan.json') and
        exposure['participated_in_current_formula_gate_sample'] is False,'NO_426: exposure provenance failed')
    _,p2j,_=old_helpers()
    config,manifest,_=inputs('nontest');meta={r['video_id']:r for r in manifest['records']}
    original={(r['video_id'],r['source_frame']):r for r in rows(V14/'nontest_01/anchor_output.jsonl')}
    predictions=[]
    for g in plan['groups']:
        q=g['support_ordinals'];vid=g['video_id'];m=meta[vid]
        supports={f:original[vid,f]['box_xyw'] for f in q}
        for f in g['probe_ordinals']:
            linear=p2j.interpolate_box(f,supports)[0]
            pchip=interpolate(f,supports,m['width'],m['height'],m['targetRatioWH'],p2j.interpolate_box)[0]
            independent=[rebuild(q,[supports[n][axis] for n in q],f)[1] for axis in (0,1)]+[supports[q[1]][2]]
            require(pchip==independent,'independent sealed polynomial differs')
            predictions.append(dict(group_index=g['group_index'],video_id=vid,source_frame=f,
                targetRatioWH=m['targetRatioWH'],linear=linear,pchip=pchip,
                support_output_sha256=[digest(original[vid,n]) for n in q]))
    require(len(predictions)==56,'complete phase denominator')
    value=dict(status='SEALED_SUPPORT_ONLY_L_AND_P_BEFORE_PROBE_REVEAL',utc=utc(),
        sample_plan_sha256=sha(HERE/'input_01/sample_plan.json'),exposure_review_sha256=sha(HERE/'g0_exposure_review.json'),
        old_support_file_sha256=sha(V14/'nontest_01/anchor_output.jsonl'),probe_answers_opened=0,predictions=predictions)
    save(HERE/'input_01/sealed_predictions.json',value)
    save(HERE/'input_01/seal_receipt.json',dict(utc=utc(),status=value['status'],
        predictions_sha256=sha(HERE/'input_01/sealed_predictions.json'),sample_plan_sha256=value['sample_plan_sha256'],
        groups=8,phases=56,probe_answers_opened=0,new_model_calls=0))
    state('G0_PREDICTIONS_SEALED_BEFORE_ANY_PROBE_REVEAL',new_spatial_calls=0)


def cache_recipes():
    """Only recipe/terminal metadata. Actual cached probe rows stay sealed."""
    plan=read(HERE/'input_01/sample_plan.json');cache=read(HERE/'input_01/cache_inventory.json')
    require(read(HERE/'input_01/seal_receipt.json')['predictions_sha256']==sha(HERE/'input_01/sealed_predictions.json'),
            'seal missing or altered')
    old_source=RUN.parents[2]/'inference/baseline_qwen3vl.py'
    current_source=OLD/'spatial_baseline.py'
    require(method_identity(old_source)==method_identity(current_source),'old and current effective spatial generation differ')
    accepted=[];rejected=[];verified_routes=set()
    for observation in cache['observations']:
        if observation['observation_role']!='probe':continue
        candidates=[]
        for found in observation['caches']:
            folder=Path(found['request_index']).parent
            route=folder.parent
            if route.name not in ('b_sft8b_package_v2','mac8b_delivery_v2'):
                rejected.append(dict(request_sha256=observation['request_sha256'],path=str(folder),reason='OTHER_MODEL_OR_UNREGISTERED_RECIPE'))
                continue
            stage=read(folder/'spatial.stage.json')
            require(stage['status']=='PASS_SAME_FRAME_NATIVE_8B_SPACE' and stage['invalid']==0 and
                stage['base_hash']['sha256']==BASE_SHA and stage['spatial_base_parameters']==8767123696 and
                stage['temporal_adapter_enabled'] is False and stage['output_sha256']==sha(folder/'anchor_output.jsonl') and
                stage['requests_sha256']==sha(folder/'anchor_requests.jsonl'),'old successful 8B spatial cache terminal/bytes differ')
            lock=read(route/'source_lock.json')
            if route not in verified_routes:
                for path,expected in lock['files'].items():
                    require(sha(path)==expected,'old candidate cache frozen dependency changed: '+path)
                verified_routes.add(route)
            runtime=(route/'runtime.py').read_text()
            require("ROOT/'inference/baseline_qwen3vl.py'" in runtime and "model.predict_focus" in runtime,
                    'old cache consumer spatial generator owner differs')
            candidates.append(dict(folder=str(folder),source_lock_sha256=sha(route/'source_lock.json'),
                stage_sha256=sha(folder/'spatial.stage.json'),output_sha256=sha(folder/'anchor_output.jsonl'),
                request_index_sha256=sha(folder/'anchor_requests.jsonl')))
        if candidates:
            # A metadata-fixed authority choice, not a choice based on raw coordinates.
            chosen=min(candidates,key=lambda x:(0 if Path(x['folder']).parent.name=='b_sft8b_package_v2' else 1,x['folder']))
            accepted.append(dict(request_sha256=observation['request_sha256'],group_index=observation['group_index'],
                chosen=chosen,all_matching_8B_authorities=candidates,probe_answer_revealed=False,
                old_prefix_logging='OLD_EFFECTIVE_CONSUMER_RECONSTRUCTED_NOT_OLD_LOGGED_TOKEN_TENSOR'))
    save(HERE/'input_01/cache_recipe_admission.json',dict(status='PASS_CACHE_RECIPE_METADATA_NOT_PROBE_REVEAL',utc=utc(),
        sample_plan_sha256=sha(HERE/'input_01/sample_plan.json'),sealed_predictions_sha256=sha(HERE/'input_01/sealed_predictions.json'),
        accepted_probe_caches=accepted,rejected_other_recipe_matches=rejected,new_probe_calls_expected=56-len(accepted),
        same_generation_method_ast=method_identity(current_source),current_source_sha256=sha(current_source),
        old_source_sha256=sha(old_source),probe_answer_rows_opened=0,
        limitations=['Old cached runs did not log processor token tensors; exact input contract is reconstructed from pinned generation code, request pixels and model.',
                     'Other-model responses are never substituted for this 8B request. Existence and historic exposure remain disclosed.']))
    state('G0_CACHE_RECIPES_ACCEPTED_PROBE_ANSWERS_STILL_SEALED',new_spatial_calls=0,
          reusable_probe_observations=len(accepted),expected_new_probe_calls=56-len(accepted))


def tensor_binding(tensor):
    import torch
    t=tensor.detach().cpu().contiguous()
    return dict(shape=list(t.shape),dtype=str(t.dtype),sha256=hashlib.sha256(t.view(torch.uint8).numpy().tobytes()).hexdigest())


def messages_for(baseline,image,ratio):
    # Call the original prompt-construction function without creating a model.
    shell=object.__new__(baseline.Qwen3VL);shell.max_pixels=baseline.DEFAULT_MAX_PIXELS
    shell._generate=lambda messages,max_new_tokens:(messages,max_new_tokens)
    return shell.predict_focus(image,tuple(ratio),max_new_tokens=baseline.DEFAULT_CROP_TOKENS)


def actual_processor(processor,messages):
    from qwen_vl_utils import process_vision_info
    try:
        text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    except (TypeError,ValueError):
        text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    images,videos,kwargs=process_vision_info(messages,return_video_kwargs=True,return_video_metadata=True,image_patch_size=16)
    inputs=processor(text=[text],images=images,videos=videos,padding=True,return_tensors='pt',**kwargs)
    return text,inputs


def native():
    require((HERE/'input_01/seal_receipt.json').is_file(),'must seal predictions before any native request stage')
    cache=read(HERE/'input_01/cache_recipe_admission.json')
    common,_,production=old_helpers();config,manifest,clocks=inputs('nontest')
    plan=read(HERE/'input_01/sample_plan.json');meta={r['video_id']:r for r in manifest['records']}
    import cv2
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    import qwen_vl_utils
    baseline=common.load(OLD/'spatial_baseline.py','sg8_original_prepare_spatial')
    processor=AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,
        min_pixels=baseline.DEFAULT_MAX_PIXELS,max_pixels=baseline.DEFAULT_MAX_PIXELS)
    receipts=[];current=None;reader=None
    try:
        for number,observation in enumerate(sorted(plan['requests'],key=lambda x:(x['request']['video_id'],x['request']['source_frame'])),1):
            request=observation['request'];vid=request['video_id'];m=meta[vid]
            if current!=vid:
                if reader is not None:reader.close()
                require(sha(m['source_path'])==m['source_sha256'],'actual native source changed')
                reader=production.OrdinalReader(m,clocks[vid]);current=vid
            frame,pixel=reader.get(request['source_frame'])
            require(pixel==request['expected_pixel_sha256'],'actual original native BGR pixel identity differs')
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);image=Image.fromarray(rgb)
            messages,max_output=messages_for(baseline,image,request['target_ratio_wh'])
            text,model_inputs=actual_processor(processor,messages)
            require(model_inputs['input_ids'].shape[-1]>0 and model_inputs['input_ids'].shape[-1]+max_output<=16384,
                    'input overflow/truncation forbidden')
            folder=HERE/'input_01/observations'/request['anchor_request_sha256'];folder.mkdir(parents=True,exist_ok=False)
            image.save(folder/'native.png',format='PNG')
            torch.save(dict(model_inputs),folder/'processor_inputs.pt')
            receipt=dict(utc=utc(),request=request,source_sha256=m['source_sha256'],group_index=observation['group_index'],
                observation_role=observation['observation_role'],native_bgr_sha256=pixel,
                native_rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),native_png_sha256=sha(folder/'native.png'),
                processor_inputs_sha256=sha(folder/'processor_inputs.pt'),prefix=text,prefix_sha256=hashlib.sha256(text.encode()).hexdigest(),
                input_tokens=int(model_inputs['input_ids'].shape[-1]),input_tensors={k:tensor_binding(v) for k,v in model_inputs.items()},
                max_new_tokens=max_output,do_sample=False,num_beams=1,use_cache=True,adapter_enabled=False,
                image_max_pixels=baseline.DEFAULT_MAX_PIXELS,base_canonical_sha256=BASE_SHA,
                model_revision=config['model_revision'],new_model_calls=0,new_optimizer_updates=0,
                decoding='SEQUENTIAL_SOURCE_ORDINAL_ZERO_TO_LAST_REQUEST_NOT_FULL_SOURCE_CLAIM',
                actual_native_pts=str(clocks[vid]['pts'][request['source_frame']]),truncation=False)
            save(folder/'input.json',receipt);receipts.append(str(folder/'input.json'))
            state('G0_RUNNING_ACTUAL_NATIVE_PROCESSOR_CPU',observations=number,total=88,new_spatial_calls=0)
    finally:
        if reader is not None:reader.close()
    save(HERE/'g0_native_processor.json',dict(status='PASS_ALL_88_NATIVE_SOURCE_AND_ACTUAL_SPACE_PROCESSOR_NOT_MODEL_CALL',utc=utc(),
        sample_plan_sha256=sha(HERE/'input_01/sample_plan.json'),sealed_predictions_sha256=sha(HERE/'input_01/sealed_predictions.json'),
        observations=88,files={p:sha(p) for p in receipts},
        processor_class_source_sha256=sha(inspect.getfile(type(processor))),
        vision_utils_source_sha256=sha(inspect.getfile(qwen_vl_utils.process_vision_info)),
        expected_missing_calls=cache['new_probe_calls_expected'],
        actual_max_input_tokens=max(read(p)['input_tokens'] for p in receipts),new_model_calls=0,new_optimizer_updates=0))
    state('G0_NATIVE_PROCESSOR_PASS_NEW_FIELD_STRICT_AND_FREEZE_PENDING',new_spatial_calls=0)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['seal','cache_recipes','native']);a=p.parse_args()
    try:globals()[a.stage]()
    except Exception:
        save(HERE/('g0_prepare_'+a.stage+'_failure_'+utc().replace(':','').replace('+','_')+'.json'),
             dict(utc=utc(),stage=a.stage,traceback=traceback.format_exc(),new_model_calls=0,new_optimizer_updates=0))
        raise
