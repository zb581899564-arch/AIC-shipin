"""One bounded 8B space diagnostic. Supports and old successes are never regenerated."""
import hashlib
import os
import subprocess
import sys
import time
import traceback

from sg8_common import (HERE,OLD,PY,BASE_SHA,read,sha,digest,save,require,state,utc,
    old_helpers,verify,cached_output)
from sg8_prepare import tensor_binding


def main():
    verify()
    admission=read(HERE/'g0_admission.json')
    require(admission['status']=='PASS_FULL_G0_NATIVE_ASSET_INPUT_ISOLATION_AND_STRICT_ADMISSION','full G0 missing')
    plan=read(HERE/'input_01/sample_plan.json');cache=read(HERE/'input_01/cache_recipe_admission.json')
    cached={r['request_sha256']:r for r in cache['accepted_probe_caches']}
    probes=[r for r in plan['requests'] if r['observation_role']=='probe']
    probes.sort(key=lambda r:(r['group_index'],r['request']['source_frame']))
    common,_,_=old_helpers();config=read(OLD/'config.json')
    baseline=common.load(OLD/'spatial_baseline.py','sg8_gpu_original_spatial')
    import torch
    from verify_saved_smoke import canonical_frozen_hash
    state('G1_LOADING_ORIGINAL_SPACE_8B',fresh_calls=0,reused_probes=0)
    model=baseline.Qwen3VL(config['model_dir'],device_map='cuda:0',max_pixels=baseline.DEFAULT_MAX_PIXELS)
    model.model.eval()
    for parameter in model.model.parameters():parameter.requires_grad_(False)
    actual=canonical_frozen_hash(model.model,torch)
    require(actual['sha256']==BASE_SHA and actual['parameters']==8767123696 and
        not hasattr(model.model,'peft_config'),'live original base/adapter identity differs')
    save(HERE/'diagnostic_01/model.json',dict(status='PASS_LIVE_ORIGINAL_8B_SPACE_BASE_ADAPTER_OFF',utc=utc(),
        base_hash=actual,logical_parameters=actual['parameters'],adapter_enabled=False,
        model_revision=config['model_revision'],source_sha256=sha(OLD/'spatial_baseline.py'),
        new_optimizer_updates=0,teacher_32B_calls=0))
    fresh=reused=0;accepted=[];started=time.monotonic();first=None
    for index,obs in enumerate(probes,1):
        request=obs['request'];key=request['anchor_request_sha256'];group=obs['group_index']
        prepared=HERE/'input_01/observations'/key;inp=read(prepared/'input.json')
        require(inp['request']==request and inp['observation_role']=='probe','exact isolated probe input differs')
        if key in cached:
            old,line_sha=cached_output(cached[key])
            require(old['status']=='MODEL_OK' and old['used_fallback'] is False and
                old['decoded_pixel_sha256']==request['expected_pixel_sha256'] and old['spatial_source']=='QWEN_ANCHOR_SAME_FRAME',
                'old cached success is not exact native observation')
            parser=sys.modules['contracts'].parse_focus_norm
            center=parser(old['raw_output'],request['source_width'],request['source_height'])
            cw,ch=baseline.compute_crop_size(request['source_width'],request['source_height'],*request['target_ratio_wh'])
            require(center is not None and baseline.center_to_box(*center,request['source_width'],request['source_height'],cw,ch)==old['box_xyw'],
                'unchanged parser/raw-to-box rejects cached success')
            value=dict(status='PASS_EXACT_OLD_8B_PROBE_REFERENCE_NO_NEW_CALL',utc=utc(),group_index=group,
                request=request,output=old,source_cache=cached[key]['chosen'],source_raw_line_sha256=line_sha,
                current_native_processor_receipt_sha256=sha(prepared/'input.json'),
                old_logged_token_tensors=False,new_model_calls=0,old_cost_preserved=True)
            path=HERE/'diagnostic_01/reused'/(key+'.json');save(path,value);reused+=1
        else:
            folder=HERE/'diagnostic_01/new'/key;folder.mkdir(parents=True,exist_ok=False)
            require(sha(prepared/'processor_inputs.pt')==inp['processor_inputs_sha256'],'prepared input bytes changed')
            cpu_inputs=torch.load(prepared/'processor_inputs.pt',map_location='cpu',weights_only=True)
            tensors={k:tensor_binding(v) for k,v in cpu_inputs.items()}
            require(tensors==inp['input_tensors'],'actual tensors differ from admitted input')
            device_inputs={k:v.to(model.model.device) for k,v in cpu_inputs.items()}
            begin=time.monotonic()
            with torch.inference_mode():
                output=model.model.generate(**device_inputs,max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True)
            tokens=output[0,len(cpu_inputs['input_ids'][0]):].detach().cpu().tolist()
            text=model.processor.batch_decode([tokens],skip_special_tokens=True,clean_up_tokenization_spaces=False)[0]
            # Immutable response BEFORE any semantic/parse validation. Errors never become empty results.
            raw=dict(utc=utc(),request_sha256=key,input_receipt_sha256=sha(prepared/'input.json'),
                model_receipt_sha256=sha(HERE/'diagnostic_01/model.json'),actual_input_tensors=tensors,
                input_tokens=inp['input_tokens'],output_token_ids=tokens,raw_output=text,wall_seconds=time.monotonic()-begin,
                max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True,adapter_enabled=False,new_model_calls=1)
            save(folder/'raw.json',raw)
            del device_inputs,output
            with (folder/'cpu_replay.log').open('x') as log:
                result=subprocess.run([PY,'-B',str(HERE/'sg8_replay.py'),key],cwd=HERE,
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            require(result.returncode==0,'independent post-generation CPU replay failed; raw preserved')
            proof=read(folder/'cpu_replay.json')
            require(proof['status']=='PASS_REAL_NATIVE_SPACE_PROBE_AND_INDEPENDENT_CPU_REPLAY' and
                proof['raw_sha256']==sha(folder/'raw.json'),'independent probe acceptance differs')
            path=folder/'done.json'
            save(path,dict(status='PASS_NEW_REAL_8B_ISOLATED_SPACE_PROBE',utc=utc(),group_index=group,request=request,
                raw_sha256=sha(folder/'raw.json'),cpu_replay_sha256=sha(folder/'cpu_replay.json'),
                input_receipt_sha256=sha(prepared/'input.json'),model_receipt_sha256=sha(HERE/'diagnostic_01/model.json'),
                box_xyw=proof['box_xyw'],center_norm=proof['center_norm'],new_model_calls=1,new_optimizer_updates=0))
            fresh+=1
            if first is None:
                first=dict(path=str(folder/'cpu_replay.json'),sha256=sha(folder/'cpu_replay.json'),new_replay_calls=0)
                save(HERE/'diagnostic_01/first_real_acceptance.json',dict(status=proof['status'],utc=utc(),
                    reference=first,request_sha256=key,input_tokens=proof['input_tokens'],proof_not_rerun=True))
        accepted.append(dict(path=str(path),sha256=sha(path),group_index=group,request_sha256=key))
        state('G1_ENGINEERING_PROBES_RUNNING' if group<2 else 'G2_CONFIRMATION_PROBES_RUNNING',
            observations=index,total=56,fresh_calls=fresh,reused_probes=reused,
            completed_groups=index//7,wall_seconds=time.monotonic()-started)
        if index==14:
            save(HERE/'diagnostic_01/engineering_completion.json',dict(status='PASS_FIRST_TWO_ENGINEERING_GROUPS',utc=utc(),
                groups=2,observations=14,fresh_calls=fresh,reused_probes=reused,
                measured_wall_seconds=time.monotonic()-started,remaining_probes=42,formula_and_gates_unchanged=True))
    require(fresh==cache['new_probe_calls_expected']==53 and reused==3 and len(accepted)==56,'complete frozen call denominator differs')
    save(HERE/'diagnostic_01/inference_completion.json',dict(status='PASS_ALL_56_ISOLATED_PROBE_OBSERVATIONS',utc=utc(),
        observations=56,groups=8,fresh_calls=fresh,reused_probes=reused,accepted=accepted,
        first_real_acceptance=first,new_optimizer_updates=0,teacher_32B_calls=0,probe_used_as_support=False))
    state('G2_INFERENCE_COMPLETE_RESOURCE_TERMINAL_PENDING',fresh_calls=fresh,reused_probes=reused)


if __name__=='__main__':
    try:main()
    except Exception:
        save(HERE/'diagnostic_01/engine_failure.json',dict(utc=utc(),traceback=traceback.format_exc(),raw_preserved=True))
        raise
