#!/usr/bin/env python3
"""Independent A_NATIVE_PTS_COMPAT_V1; no test labels or training."""
from __future__ import annotations

import argparse
import faulthandler
import importlib.util
import json
import sys
import time
from pathlib import Path

faulthandler.enable(all_threads=True)
sys.dont_write_bytecode = True


def diagnostic(phase, **details):
    print("A_DIAG " + json.dumps({"phase": phase, "python": sys.executable,
                                  **details}, ensure_ascii=False, sort_keys=True), flush=True)


diagnostic("before_a_contract_import")
from a_contract import ADAPTER_SHA256, sha, write_json
from pts_contract import (VARIANT, BRANCH_CFR, load_clocks, legacy_manifest,
                          window_schedule, native_clip_plan)
from native_frames import build_native_clip
from exact_pts import exact_native_pts, verify_native_encoding
diagnostic("after_a_contract_import")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--expected-manifest-sha256", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--admission", type=Path, required=True)
    ap.add_argument("--clock-registry", type=Path, required=True)
    ap.add_argument("--expected-clock-registry-sha256", required=True)
    args = ap.parse_args()
    diagnostic("before_run_a_import")
    from run_pts import CONFIG_SHA256, verify_admission, verify_vendor, verify_models
    diagnostic("after_run_a_import")
    if args.output.exists() or args.output.with_suffix(".jsonl.run.json").exists():
        raise FileExistsError("refusing to overwrite temporal evidence")
    if sha(args.manifest) != args.expected_manifest_sha256:
        raise ValueError("manifest identity changed")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clocks = load_clocks(manifest, args.clock_registry, args.expected_clock_registry_sha256)
    verify_admission(args.admission, args.expected_manifest_sha256, manifest["kind"], args.output.parent,
                     args.expected_clock_registry_sha256, "temporal")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if sha(args.config) != CONFIG_SHA256:
        raise ValueError("frozen A configuration changed")
    verify_vendor()
    verify_models(config)
    common = Path(__file__).parent / "vendor/temporal_common.py"
    spec = importlib.util.spec_from_file_location("temporal_common", common)
    tc = importlib.util.module_from_spec(spec)
    diagnostic("before_temporal_common_import")
    spec.loader.exec_module(tc)
    diagnostic("after_temporal_common_import")
    # Attempt03 reached first CUDA init after decord import and failed with
    # random_device could not be read. Test initialization order alone: perform
    # torch/CUDA initialization before decord or other native consumers.
    diagnostic("before_torch_import")
    import torch
    diagnostic("after_torch_import", torch_version=torch.__version__)
    diagnostic("before_torch_thread_query")
    diagnostic("after_torch_thread_query", cpu_threads=torch.get_num_threads(),
               cpu_interop_threads=torch.get_num_interop_threads())
    diagnostic("before_cuda_initialize", cuda_compiled_version=torch.version.cuda)
    torch.cuda.init()
    diagnostic("after_cuda_initialize", cuda_available=torch.cuda.is_available(),
               cuda_device_count=torch.cuda.device_count(), current_device=torch.cuda.current_device(),
               device_name=torch.cuda.get_device_name(0))
    diagnostic("before_cuda_tiny_allocation")
    diagnostic_tensor = torch.empty((1,), device="cuda:0", dtype=torch.bfloat16)
    torch.cuda.synchronize()
    diagnostic("after_cuda_tiny_allocation", bytes=diagnostic_tensor.numel()*diagnostic_tensor.element_size())
    del diagnostic_tensor
    diagnostic("before_decord_import")
    import decord
    diagnostic("after_decord_import", decord_version=getattr(decord, "__version__", "UNKNOWN"))
    diagnostic("before_peft_import")
    from peft import PeftModel
    diagnostic("after_peft_import")
    diagnostic("before_transformers_import")
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    diagnostic("after_transformers_import")

    started = time.monotonic()
    diagnostic("before_base_from_pretrained")
    base = Qwen3VLForConditionalGeneration.from_pretrained(
        config["base_model"], torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    diagnostic("after_base_from_pretrained")
    diagnostic("before_peft_from_pretrained")
    model = PeftModel.from_pretrained(base, config["adapter"], is_trainable=False)
    diagnostic("after_peft_from_pretrained")
    model.eval()
    seen = set()
    n_parameters = 0
    for p in model.parameters():
        if id(p) not in seen:
            n_parameters += p.numel()
            seen.add(id(p))
    if n_parameters > 9_000_000_000:
        raise RuntimeError("logical complete A parameter count exceeds 9B")
    diagnostic("before_processor_from_pretrained")
    processor = AutoProcessor.from_pretrained(config["base_model"], min_pixels=tc.MAX_PIXELS,
                                              max_pixels=tc.MAX_PIXELS)
    diagnostic("after_processor_from_pretrained")
    messages = [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
    prompt = prompt.replace("<|im_start|>user\n",
                            "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    failures, windows_total, peak = 0, 0, 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for i, item in enumerate(manifest["records"], 1):
            if sha(item["source_path"]) != item["source_sha256"]:
                raise RuntimeError("source media identity changed")
            vr = decord.VideoReader(item["source_path"])
            n_frames, fps = len(vr), float(vr.get_avg_fps())
            exact_fps = item["fps_num"] / item["fps_den"]
            if n_frames != item["n_frames"] or abs(fps-exact_fps) > max(1e-6, exact_fps*1e-6):
                raise RuntimeError("source metadata changed")
            del vr
            result = {"video_id": item["video_id"], "targetRatioWH": item["targetRatioWH"],
                      "video_path": item["source_path"], "n_frames": n_frames, "fps": fps,
                      "arm": VARIANT, "windows": []}
            clock = clocks[item["video_id"]]
            for j, (start, end) in enumerate(window_schedule(item, manifest["kind"], clock)):
                windows_total += 1
                row = {"index": j, "start_sec": start, "end_sec": end, "output_valid": False,
                       "status": "INFERENCE_FAILURE", "parsed_segments": None,
                       "parse_errors": [], "parse_warnings": [], "raw_output": ""}
                one = time.monotonic()
                try:
                    if clock["branch"] == BRANCH_CFR:
                        array, metadata, info = tc.build_virtual_clip(item["source_path"], start, end)
                        video = torch.from_numpy(array).permute(0, 3, 1, 2)
                        inputs = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                                           padding=True, do_sample_frames=False, return_tensors="pt").to("cuda")
                    else:
                        plan = native_clip_plan(clock, start, end)
                        array, metadata = build_native_clip(item["source_path"], item, clock, plan)
                        if sha(item["source_path"]) != item["source_sha256"]:
                            raise RuntimeError("native source bytes changed during decode")
                        video = torch.from_numpy(array).permute(0, 3, 1, 2)
                        with exact_native_pts(processor, plan, fps) as identity:
                            encoded = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                                                padding=True, do_sample_frames=False, return_tensors="pt")
                            verify_native_encoding(processor, encoded, identity)
                        inputs = encoded.to("cuda")
                        info = {"n_sampled": plan["n_sampled"]}
                        row.update(clock_branch=clock["branch"], clock_record_sha256=clock["clock_record_sha256"],
                                   source_frame_ids=plan["source_frame_ids"], native_processor_identity=identity)
                    torch.cuda.reset_peak_memory_stats()
                    with torch.inference_mode():
                        generated = model.generate(**inputs, do_sample=False, max_new_tokens=256)
                    torch.cuda.synchronize()
                    trimmed = [g[len(inputs["input_ids"][0]):] for g in generated]
                    raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                                 clean_up_tokenization_spaces=False)[0]
                    parsed, errors, warnings = tc.parse_segments(raw, end-start)
                    row.update(raw_output=raw, parsed_segments=parsed, parse_errors=errors,
                               parse_warnings=warnings, output_valid=parsed is not None,
                               sampled_frames=info["n_sampled"],
                               status="MODEL_OK" if parsed is not None else
                                      "EMPTY_OUTPUT_UNSUPPORTED_LEGACY_A" if "'segments' is empty" in errors
                                      else "PARSE_FAILURE",
                               peak_memory_mib=round(torch.cuda.max_memory_allocated()/2**20, 2))
                    peak = max(peak, row["peak_memory_mib"])
                except Exception as exc:
                    row.update(parse_errors=[f"{type(exc).__name__}: {exc}"], status="INFERENCE_FAILURE")
                row["seconds"] = round(time.monotonic()-one, 6)
                failures += int(not row["output_valid"])
                result["windows"].append(row)
            stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True)+"\n")
            stream.flush()
            print(f"[{i}/{len(manifest['records'])}] windows={len(result['windows'])} failures={failures}", flush=True)
    report = {"status": "PASS_TEMPORAL_EXECUTION" if failures == 0 else "BLOCK_TEMPORAL_FAILURES",
              "videos": len(manifest["records"]), "windows": windows_total, "invalid_windows": failures,
              "manifest_sha256": args.expected_manifest_sha256, "output_sha256": sha(args.output),
              "adapter_sha256": ADAPTER_SHA256, "temporal_common_sha256": sha(common),
              "wall_seconds": time.monotonic()-started, "peak_memory_mib": peak,
              "logical_A_parameters_unique": n_parameters, "parameter_count_pass": n_parameters <= 9_000_000_000,
              "shared_base_counted_once": True, "space_model_same_base_weights_no_adapter": True,
              "legal_empty_supported": False, "failure_to_empty_conversions": 0,
              "environment": sys.executable}
    report.update(variant=VARIANT, clock_registry_sha256=args.expected_clock_registry_sha256,
                  strict_original_A=False, native_source_count=sum(c["branch"] != BRANCH_CFR for c in clocks.values()))
    write_json(args.output.with_suffix(".jsonl.run.json"), report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if failures == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
