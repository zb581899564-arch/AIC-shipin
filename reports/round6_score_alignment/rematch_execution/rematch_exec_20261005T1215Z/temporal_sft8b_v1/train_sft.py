#!/usr/bin/env python3
"""One explicitly admitted 8B interval SFT smoke. No C/BCE or implicit next stage."""
from __future__ import annotations
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback

from sft_contract import (AdmissionRejected, BASE_PARAMS, LORA_PARAMS, TOTAL_PARAMS, MODEL_ID, REVISION,
    SCOPE, EffectiveAccumulation, admit, answer_string, assistant_labels, language_target_names,
    legacy_clip_plan, require, sha256, validate_trainable_names, verify_live_gpu_reservation)


def load_helper(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def decode_cfr_clip(row,tc,np,decord):
    """New byte binding plus actual selected numeric clocks; old R7 geometry."""
    plan=legacy_clip_plan(row)
    reader=decord.VideoReader(row["source_path"],ctx=decord.cpu(0))
    fps=float(reader.get_avg_fps())
    require(len(reader)==row["n_frames"] and abs(fps-plan["source_fps"])<=max(1e-6,fps*1e-6),
            "current Decord source count/FPS mismatch")
    local=[int(round(x)) for x in np.linspace(0,plan["n_frames_in_clip"]-1,plan["n_sampled"])]
    require(local==plan["clip_local_indices"],"legacy R7 sampling arithmetic mismatch")
    numeric_ids=sorted(set([0]+plan["absolute_indices"]))
    clock=reader.get_frame_timestamp(numeric_ids)
    clock=np.asarray(clock.asnumpy() if hasattr(clock,"asnumpy") else clock)
    require(clock.shape==(len(numeric_ids),2) and np.isfinite(clock).all() and
            np.all(clock[:,1]>clock[:,0]) and np.all(clock[1:,0]>clock[:-1,0]),"current source timestamp identity invalid")
    origin=float(clock[0,0]); tolerance=1/fps+1e-6
    residual=max(abs((float(pair[0])-origin)-index/fps) for index,pair in zip(numeric_ids,clock))
    require(abs(origin)<=tolerance and residual<=tolerance,"current selected source clock violates R7 CFR/origin gate")
    frames=reader.get_batch(plan["absolute_indices"]).asnumpy()
    require(tuple(frames.shape)==(plan["n_sampled"],row["height"],row["width"],3),"current decoded geometry mismatch")
    metadata={"fps":fps,"frames_indices":local,"total_num_frames":plan["n_frames_in_clip"],"video_backend":"decord"}
    info={**plan,"current_clock_numeric_ids":numeric_ids,"current_decord_timestamps":clock.tolist(),
          "current_source_origin_sec":origin,"max_selected_cfr_residual_sec":residual,
          "one_frame_tolerance_sec":tolerance,"clock_contract":"R7_APPROXIMATE_CFR_SELECTED_FRAME_GATE",
          "old_pts_source_byte_equality_claimed":False,"exact_native_pts_binding_claimed":False}
    return frames,metadata,info


def verify_video_encoding(processor,encoded,metadata,info):
    ids=encoded["input_ids"][0].tolist(); mask=encoded["attention_mask"][0].tolist()
    require("pixel_values_videos" in encoded and "video_grid_thw" in encoded,"processor omitted video tensors")
    grid=encoded["video_grid_thw"].tolist()
    merge=processor.video_processor.merge_size
    require(merge==2 and len(grid)==1 and all(type(x) is int and x>0 for x in grid[0]) and
            grid[0][0]==(info["n_sampled"]+1)//2,"processor video grid/temporal padding changed")
    expected_tokens=math.prod(grid[0])//(merge*merge)
    actual_tokens=sum(token==processor.video_token_id and active for token,active in zip(ids,mask))
    require(actual_tokens==expected_tokens and actual_tokens>0,"expanded processor video-token identity mismatch")
    decoded=processor.tokenizer.decode([token for token,active in zip(ids,mask) if active],
                                     skip_special_tokens=False,clean_up_tokenization_spaces=False)
    times=[float(x) for x in re.findall(r"<([0-9]+(?:\.[0-9]+)?) seconds>",decoded)]
    padded=list(metadata["frames_indices"])
    if len(padded)%2: padded.append(padded[-1])
    expected=[(padded[i]+padded[i+1])/(2*metadata["fps"]) for i in range(0,len(padded),2)]
    require(len(times)==len(expected) and all(abs(a-b)<=.05000001 for a,b in zip(times,expected)),
            "processor timestamp text does not match supplied source-frame/FPS clock")
    return {"video_grid_thw":grid,"video_token_count":actual_tokens,"expected_patch_times_sec":expected,
            "actual_timestamp_text_sec":times,"timestamp_text_rounding_max_error":max(abs(a-b) for a,b in zip(times,expected))}


def build_example(processor,row,config,tc,torch,np,decord):
    frames,metadata,info=decode_cfr_clip(row,tc,np,decord)
    answer=answer_string(row["segments_clip_local"],row["clip_end_sec"]-row["clip_start_sec"])
    prompt=processor.apply_chat_template([{"role":"user","content":[{"type":"text","text":tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    boundary="<|im_start|>user\n"
    require(prompt.count(boundary)==1,"processor chat user boundary mismatch")
    prompt=prompt.replace(boundary,boundary+"<|vision_start|><|video_pad|><|vision_end|>",1)
    video=torch.from_numpy(frames).permute(0,3,1,2)
    options=dict(videos=[video],video_metadata=[metadata],padding=True,truncation=False,
                 do_sample_frames=False,return_tensors="pt")
    suffix=answer+"<|im_end|>\n"
    full=processor(text=[prompt+suffix],**options)
    only_prompt=processor(text=[prompt],**options)
    full_identity=verify_video_encoding(processor,full,metadata,info)
    prompt_identity=verify_video_encoding(processor,only_prompt,metadata,info)
    require(full_identity==prompt_identity and torch.equal(full["video_grid_thw"],only_prompt["video_grid_thw"]) and
            torch.equal(full["pixel_values_videos"],only_prompt["pixel_values_videos"]),"assistant text changed video encoding")
    require(full["input_ids"].shape[1]<=config["max_sequence_length"],"expanded SFT sequence too long; truncation forbidden")
    identity=assistant_labels(full["input_ids"][0].tolist(),full["attention_mask"][0].tolist(),
                              only_prompt["input_ids"][0].tolist(),only_prompt["attention_mask"][0].tolist())
    decoded_answer=processor.tokenizer.decode(identity["assistant_token_ids"],skip_special_tokens=False,
                                             clean_up_tokenization_spaces=False)
    require(decoded_answer==suffix,"assistant-only JSON/termination token identity mismatch")
    full["labels"]=torch.tensor([identity["tail_labels"]],dtype=torch.long)
    evidence={"window_id":row["window_id"],"parent_sample_id":row["parent_sample_id"],
        "source_sha256":row["source_sha256"],"answer_json":answer,"assistant_suffix":suffix,
        "assistant_mask":identity,"video_identity":full_identity,"clip_identity":info,
        "expanded_sequence_length":int(full["input_ids"].shape[1])}
    return dict(full),identity["logits_to_keep"],evidence


def unique_parameters(model):
    seen=set()
    for name,parameter in model.named_parameters(remove_duplicate=False):
        if id(parameter) not in seen:
            seen.add(id(parameter)); yield name,parameter


def fingerprint_base(model,torch):
    import hashlib
    digest=hashlib.sha256(); count=0
    for name,parameter in unique_parameters(model):
        if "lora_" in name: continue
        require(not parameter.requires_grad,"base/vision became trainable")
        digest.update(name.encode()); digest.update(str(tuple(parameter.shape)).encode()); digest.update(str(parameter.dtype).encode())
        flat=parameter.detach().reshape(-1)
        for offset in range(0,flat.numel(),1<<22):
            digest.update(flat[offset:offset+(1<<22)].contiguous().view(torch.uint8).cpu().numpy().tobytes())
        count+=parameter.numel()
    return {"sha256":digest.hexdigest(),"parameters":count,"method":"all unique frozen tensor bytes; chunked CPU hashing"}


def gradient_evidence(trainable,torch,update_number):
    evidence={family:{"tensors":0,"connected":0,"finite":0,"nonzero":0} for family in ("lora_A","lora_B")}
    for name,parameter in trainable:
        family="lora_A" if ".lora_A." in name else "lora_B" if ".lora_B." in name else None
        require(family is not None,"unexpected trainable LoRA family")
        item=evidence[family]; item["tensors"]+=1
        if parameter.grad is None: continue
        item["connected"]+=1
        item["finite"]+=int(bool(torch.isfinite(parameter.grad).all()))
        item["nonzero"]+=int(bool(torch.count_nonzero(parameter.grad)))
    for family,item in evidence.items():
        require(item["tensors"]>0 and item["connected"]==item["tensors"] and item["finite"]==item["tensors"],
                family+" missing/nonfinite gradient connection")
        require((family=="lora_A" and update_number==1) or item["nonzero"]>0,
                family+" has no nonzero gradients after initialization update")
    return evidence


def execute(contract,config_path,admission_path):
    # Entry admission/source/model checks already completed using only stdlib.
    require(sha256(config_path)==contract["config_sha256"] and sha256(admission_path)==contract["admission_sha256"],
            "SFT authority changed between admission and execution")
    verify_live_gpu_reservation()
    config=contract["config"]; output=Path(config["out_dir"])
    output.mkdir(parents=True,exist_ok=True)
    report={"status":"RUNNING_SFT_SMOKE_ONLY","scope":SCOPE,"formal_c_bce_admitted":False,
            "config_sha256":sha256(config_path),"admission_sha256":sha256(admission_path),
            "input_manifest_sha256":config["train_manifest"]["sha256"],
            "origin_train_manifest_sha256":contract["origin_train_manifest_sha256"],
            "quality_claim":False,"full_training_completed":False,"rows":len(contract["rows"])}
    started=time.monotonic()
    try:
        os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
        import numpy as np
        import torch
        import transformers
        import peft
        from peft import LoraConfig,PeftModel,get_peft_model
        from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
        require(transformers.__version__=="4.57.1" and peft.__version__=="0.17.1","unreviewed SFT runtime versions")
        require(torch.cuda.is_available(),"SFT smoke requires separately registered CUDA job")
        random.seed(config["seed"]); np.random.seed(config["seed"]); torch.manual_seed(config["seed"])
        torch.cuda.set_device(0); torch.cuda.init(); torch.cuda.manual_seed_all(config["seed"])
        import decord  # Preserve the verified torch/CUDA-before-Decord ordering.
        tc=load_helper(contract["bound"]["temporal_common"],"sft_frozen_temporal_common")
        require(tc.MAX_FRAMES==64 and tc.MAX_PIXELS==131072,"frozen processor recipe mismatch")
        report["environment"]={"python":sys.executable,"torch":torch.__version__,"transformers":transformers.__version__,
            "peft":peft.__version__,"decord":decord.__version__}
        torch.cuda.reset_peak_memory_stats()
        base=Qwen3VLForConditionalGeneration.from_pretrained(config["model_dir"],revision=REVISION,local_files_only=True,
            torch_dtype=torch.bfloat16,device_map={"":"cuda:0"},low_cpu_mem_usage=True,attn_implementation="sdpa")
        require(base.config.model_type=="qwen3_vl" and base.config.text_config.hidden_size==4096,"wrong loaded 8B architecture")
        for parameter in base.parameters(): parameter.requires_grad_(False)
        base.config.use_cache=False
        targets=language_target_names([name for name,module in base.named_modules() if isinstance(module,torch.nn.Linear)],
                                     base.config.text_config.num_hidden_layers)
        model=get_peft_model(base,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,bias="none",target_modules=targets,
                                             modules_to_save=None,task_type="CAUSAL_LM"))
        trainable=[(name,p) for name,p in unique_parameters(model) if p.requires_grad]
        validate_trainable_names([name for name,_ in trainable])
        require(all("modules_to_save" not in name for name,_ in model.named_parameters()),"unapproved modules_to_save copies")
        inventory={"base":sum(p.numel() for name,p in unique_parameters(model) if "lora_" not in name),
                   "lora":sum(p.numel() for name,p in unique_parameters(model) if "lora_" in name)}
        inventory["total"]=sum(inventory.values())
        require((inventory["base"],inventory["lora"],inventory["total"])==(BASE_PARAMS,LORA_PARAMS,TOTAL_PARAMS),"actual SFT parameter inventory mismatch")
        report.update(parameter_inventory=inventory,exact_language_targets=targets,modules_to_save=None,
                      gradient_checkpointing_use_reentrant=False,head_added=False)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
        require(not model.get_input_embeddings().weight.requires_grad,"embeddings must remain frozen")
        model.train()
        for name,module in model.named_modules():
            if name.endswith(".visual"): module.eval()
        frozen_before=fingerprint_base(model,torch)
        initial={name:p.detach().cpu().clone() for name,p in trainable}
        previous_lora=dict(initial)
        processor=AutoProcessor.from_pretrained(config["model_dir"],revision=REVISION,local_files_only=True,
                                                min_pixels=131072,max_pixels=131072)
        optimizer=torch.optim.AdamW([p for _,p in trainable],lr=config["lr"],weight_decay=0.0,
                                   betas=tuple(config["adamw_betas"]),eps=config["adamw_eps"])
        optimizer.zero_grad(set_to_none=True)
        counters=EffectiveAccumulation(config["grad_accum"],config["updates"])
        losses=[]; updates=[]; rows=contract["rows"]
        report.update(losses=losses,updates=updates,optimizer_steps=0,effective_batches=0)
        source_stats={path:(Path(path).stat().st_size,Path(path).stat().st_mtime_ns) for path in contract["sources"]}
        order=[]; epoch=0; position=0
        with (output/"example_evidence.jsonl").open("x",encoding="utf-8") as evidence_stream:
            while counters.completed<config["updates"]:
                require(time.monotonic()-started<=config["max_wall_seconds"],"registered SFT wall-time exceeded")
                if position==len(order):
                    order=list(range(len(rows))); random.Random(config["seed"]+epoch).shuffle(order); epoch+=1; position=0
                row=rows[order[position]]; position+=1
                stat=Path(row["source_path"]).stat()
                require((stat.st_size,stat.st_mtime_ns)==source_stats[row["source_path"]],"source file metadata changed during SFT")
                encoded,keep,evidence=build_example(processor,row,config,tc,torch,np,decord)
                encoded={key:value.to("cuda:0") for key,value in encoded.items()}
                result=model(**encoded,logits_to_keep=keep)
                require(result.loss is not None and bool(torch.isfinite(result.loss)),"missing/nonfinite assistant CE loss; no update")
                loss=result.loss
                (loss/config["grad_accum"]).backward()
                ready=counters.record_backward(True,True); losses.append(float(loss.detach().cpu()))
                report["effective_batches"]=counters.effective_batches
                evidence.update(effective_batch=counters.effective_batches,loss=losses[-1])
                evidence_stream.write(json.dumps(evidence,ensure_ascii=False)+"\n"); evidence_stream.flush()
                if ready:
                    gradients=gradient_evidence(trainable,torch,counters.completed+1)
                    norm=torch.nn.utils.clip_grad_norm_([p for _,p in trainable],1.0)
                    require(bool(torch.isfinite(norm)) and float(norm)>0,"no nonzero connected LoRA gradient")
                    optimizer.step(); optimizer.zero_grad(set_to_none=True); counters.record_step()
                    current_lora={name:p.detach().cpu().clone() for name,p in trainable}
                    changed=[name for name in current_lora if not torch.equal(current_lora[name],previous_lora[name])]
                    require(changed,"LoRA weights unchanged after optimizer update")
                    previous_lora=current_lora
                    report["optimizer_steps"]=counters.completed
                    updates.append({"optimizer_step":counters.completed,"effective_batches":counters.effective_batches,
                        "accumulated_batches":config["grad_accum"],"gradient_norm":float(norm),"changed_lora_tensors":len(changed)})
                    updates[-1]["lora_gradient_evidence"]=gradients
                    print(json.dumps(updates[-1]),flush=True)
        counters.finish()
        frozen_after=fingerprint_base(model,torch)
        require(frozen_after==frozen_before,"frozen base/vision tensor bytes changed")
        trained={name:p.detach().cpu().clone() for name,p in trainable}
        adapter=output/"adapter"; model.save_pretrained(str(adapter),safe_serialization=True)
        saved_config=json.loads((adapter/"adapter_config.json").read_text())
        require(saved_config.get("modules_to_save") is None and saved_config.get("r")==16 and
                saved_config.get("lora_alpha")==32 and set(saved_config.get("target_modules",[]))==set(targets),"saved adapter recipe changed")
        reloaded=PeftModel.from_pretrained(model.unload(),str(adapter),is_trainable=False)
        actual={name:p.detach().cpu() for name,p in unique_parameters(reloaded) if "lora_" in name}
        require(set(actual)==set(trained) and all(torch.equal(actual[name],trained[name]) for name in trained),"saved adapter reload byte mismatch")
        for name,path in contract["bound"].items():
            require(sha256(path)==config[name]["sha256"],"bound input/helper changed during SFT")
        for path,digest in contract["sources"].items(): require(sha256(path)==digest,"source bytes changed during SFT")
        require(sha256(config_path)==report["config_sha256"] and sha256(admission_path)==report["admission_sha256"],"run authority changed")
        require(all(sha256(Path(__file__).parent/name)==digest for name,digest in contract["admission"]["source_code_sha256"].items()),"SFT source changed during run")
        report.update(status="PASS_INTERVAL_SFT_SMOKE_ENGINEERING_ONLY",optimizer_steps=counters.completed,
            effective_batches=counters.effective_batches,losses=losses,updates=updates,loss_finite=all(math.isfinite(x) for x in losses),
            base_frozen=True,vision_frozen=True,freeze_evidence={"before":frozen_before,"after":frozen_after},
            adapter_reload_succeeded=True,adapter_model_sha256=sha256(adapter/"adapter_model.safetensors"),
            peak_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,negative_targets_created=False,
            assistant_json_and_turn_termination_ce_only=True)
    except Exception as exc:
        report.update(status="STOP_INTERVAL_SFT_SMOKE",failure={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()})
    report["wall_seconds"]=time.monotonic()-started
    with (output/"train_report.json").open("x",encoding="utf-8") as target:
        json.dump(report,target,ensure_ascii=False,indent=2); target.write("\n")
    print(json.dumps({"status":report["status"],"report":str(output/"train_report.json")}),flush=True)
    return 0 if report["status"].startswith("PASS_") else 4


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",type=Path,required=True); parser.add_argument("--admission",type=Path,required=True)
    parser.add_argument("--check-only",action="store_true")
    args=parser.parse_args()
    try:
        contract=admit(args.config,args.admission)
    except Exception as exc:
        print(json.dumps({"status":"STOP_BEFORE_RUNTIME_IMPORTS","failure":type(exc).__name__+": "+str(exc)}),file=sys.stderr)
        return 3
    if args.check_only:
        print(json.dumps({"status":"PASS_STDLIB_AUTHORITY_AND_BYTE_CONTRACT_ONLY","rows":len(contract["rows"]),
                          "training_started":False,"scope":SCOPE})); return 0
    return execute(contract,args.config,args.admission)


if __name__=="__main__": raise SystemExit(main())
