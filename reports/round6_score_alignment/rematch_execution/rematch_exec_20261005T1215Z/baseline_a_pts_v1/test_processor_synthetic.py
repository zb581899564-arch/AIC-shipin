#!/usr/bin/env python3
"""Actual installed processor on synthetic CPU arrays; never loads a model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from a_contract import sha, write_json
from pts_contract import VARIANT, require
from exact_pts import exact_native_pts, verify_native_encoding
from native_frames import prepare_native_processor_input

HERE = Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-model",type=Path,required=True)
    ap.add_argument("--output-root",type=Path,required=True)
    args=ap.parse_args()
    root=args.output_root.resolve()
    require(HERE in root.parents,"CPU synthetic evidence must stay in baseline_a_pts_v1")
    if root.exists(): raise FileExistsError("preserve real processor evidence")
    from run_pts import verify_vendor, CONFIG_SHA256
    verify_vendor()
    require(sha(HERE/"config_a.json")==CONFIG_SHA256,"frozen A config changed")
    config=json.loads((HERE/"config_a.json").read_text(encoding="utf-8"))
    require(args.base_model.resolve()==Path(config["base_model"]).resolve(),"frozen processor model path required")
    for name in ("config.json","tokenizer.json"):
        require(sha(args.base_model/name)==config["model_hashes"][name],"frozen processor/tokenizer hash changed")
    import torch
    import numpy as np
    import transformers
    from transformers import AutoProcessor
    from vendor import temporal_common as tc
    processor=AutoProcessor.from_pretrained(str(args.base_model),min_pixels=tc.MAX_PIXELS,
                                          max_pixels=tc.MAX_PIXELS,local_files_only=True)
    prompt=processor.apply_chat_template([{"role":"user","content":[{"type":"text","text":tc.PROMPT}]}],
                                         tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace("<|im_start|>user\n","<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>",1)
    root.mkdir(parents=True)
    # Preserve the actual reason revision 01 blocked before testing this lock.
    reproduction={"case":"unpadded_single_frame_processor_limit","pass":False}
    try:
        lone=torch.zeros((1,3,64,64),dtype=torch.uint8)
        processor(text=[prompt],videos=[lone],video_metadata=[{"fps":25.0,"frames_indices":[5],
                  "total_num_frames":12,"video_backend":"decord"}],padding=True,
                  do_sample_frames=False,return_tensors="pt")
        reproduction["error"]="installed processor unexpectedly accepted unpadded t=1"
    except ValueError as exc:
        reproduction["error"]=str(exc)
        reproduction["pass"]="temporal_factor" in str(exc) and "t:1" in str(exc)
    except Exception as exc:
        reproduction["error"]=type(exc).__name__+": "+str(exc)
    write_json(root/"unpadded_single_frame_failure_reproduction.json",reproduction)
    records=[]
    for n in (1,3,63,64):
        record={"case":"native_frames_"+str(n),"pass":False}
        original=processor._calculate_timestamps
        try:
            ids=[5+2*i for i in range(n)]
            pts=[7.01+.04*i+(.4 if i>=max(1,n//2) else 0) for i in range(n)]
            plan={"source_frame_ids":ids,"source_relative_pts":pts,"window_start":7.0}
            frames=np.zeros((n,64,64,3),dtype=np.uint8)
            metadata={"fps":25.0,"frames_indices":ids,"total_num_frames":2*n+10,"video_backend":"decord"}
            frames, metadata=prepare_native_processor_input(frames,metadata,plan)
            require(frames.shape[0]==(2 if n==1 else n),"physical/processor padding count changed")
            video=torch.from_numpy(frames).permute(0,3,1,2)
            with exact_native_pts(processor,plan,25.0) as identity:
                encoded=processor(text=[prompt],videos=[video],video_metadata=[metadata],padding=True,
                                  do_sample_frames=False,return_tensors="pt")
                verify_native_encoding(processor,encoded,identity)
            require(processor._calculate_timestamps==original,"processor instance override not restored")
            require(identity["last_frame_padding_copies"]==n%2,"processor final duplicate padding count changed")
            require(identity["explicit_input_padding_copies"]==int(n==1) and
                    identity["implicit_processor_padding_copies"]==int(n%2 and n>1),
                    "explicit vs processor padding policy changed")
            require(abs(identity["exact_temporal_patch_local_pts"][-1]-
                    (pts[-1]-7.0 if n%2 else ((pts[-2]+pts[-1])/2-7.0)))<1e-12,
                    "last native patch timestamp is not the padded physical-time mean")
            record.update(pass_=True,identity=identity,encoded_input_tokens=int(encoded["input_ids"].shape[1]),
                          processor_instance_restored=True)
            record["pass"]=True
        except Exception as exc:
            record["error"]=type(exc).__name__+": "+str(exc)
        records.append(record)
        write_json(root/(record["case"]+".json"),record)
    passed=reproduction["pass"] and all(r["pass"] for r in records)
    verify_vendor()
    receipt={"schema":"aic_native_pts_actual_processor_synthetic_v1","variant":VARIANT,
             "status":"PASS_ACTUAL_PROCESSOR_SYNTHETIC_ONLY" if passed else "BLOCK_ACTUAL_PROCESSOR_SYNTHETIC",
             "records":records,"source_lock_sha256":sha(HERE/"source_lock.json"),"test_file_sha256":sha(__file__),
             "unpadded_single_frame_failure_reproduction":reproduction,
             "source_revision":json.loads((HERE/"source_lock.json").read_text())["revision"],
             "torch_version":torch.__version__,"transformers_version":transformers.__version__,
             "processor_class":type(processor).__name__,"processor_path":str(args.base_model),
             "synthetic_cpu_arrays":True,"decoder_source_frame_identity_proved":False,
             "contest_media_read":False,"labels_read":False,"models_run":False,"GPU_used":False,
             "images_exported_or_displayed":False,"inference_allowed":False}
    write_json(root/"processor_receipt.json",receipt)
    print(json.dumps({"status":receipt["status"],"receipt_sha256":sha(root/"processor_receipt.json")}))
    return 0 if passed else 4


if __name__=="__main__":
    raise SystemExit(main())
