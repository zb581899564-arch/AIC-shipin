#!/usr/bin/env python3
"""Minimal Video-ORA-4B inference verification: image spatial grounding,
short-video temporal grounding, short-video tracking.

Everything that defines a task is taken from the OraRL release at commit
e1ec91ff00f59ee0da04d285938c1f7247daa69c:

  * prompts          -> eval/task/eval_prompt.py      (verbatim strings)
  * sampling profiles-> data/eval/datasets.jsonl      (fps / max_frames / pixels)
  * loader recipe    -> eval/task/temporal_grounding/eval_timelens_hf.py
                        (AutoModelForImageTextToText + AutoProcessor)

Differences from the author's evaluation stack are recorded, not hidden:
  * attn_implementation=sdpa instead of flash_attention_2 (flash-attn is not
    installed; it needs a CUDA toolkit build). Set --attn to override.
  * no vLLM: single-sample HF Transformers generate().
  * no SAM2 / segmentation post-processing anywhere.

Guarantees:
  * raw model text is always saved, never replaced by a cleaned-up variant;
  * invalid JSON / out-of-range boxes / empty output are marked INVALID, never
    silently repaired;
  * every sampled video frame index is recorded so clip time is checkable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

# The author's evaluators pin the decord video backend
# (eval/task/*/eval_*.py do os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")).
# eval/README.md states the backend is "not cosmetic". Set it before
# qwen_vl_utils is imported so we match the published evaluation stack.
os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")

DR = 32  # qwen3.5 vision downsample rate (2x spatial merge x 16px patch)

# ---------------------------------------------------------------------------
# Prompts -- VERBATIM from eval/task/eval_prompt.py
# ---------------------------------------------------------------------------
QWEN_NATIVE_PROMPT_SG = (
    'Locate "{}" in the image. Output its bounding box in JSON format '
    'within <answer>...</answer> tags. '
    'Example: <answer>[{{"bbox_2d": [123, 30, 404, 846]}}]</answer>'
)
TEMPORAL_GROUNDING_PROMPT = (
    'To accurately pinpoint the event "{}" in the video, '
    "determine the precise time period of the event. "
    "Provide the start and end times (in seconds) "
    'in the format "start time to end time" within <answer> </answer> tags. '
    "Example: <answer> 12 to 18 </answer>"
)
GROUNDING_QUESTION_TEMPLATE_NO_THINK = (
    "{Question}\n"
    "Please answer this question based on the visual content. "
)
TRACKING_TAIL = (
    "Please track the target object throughout the video and provide one bounding box per second, "
    "ONLY up to 32 seconds, within the <answer>...</answer> tags.\n"
    "Example:\n"
    '<answer>{"boxes": {"1": [405, 230, 654, 463], "2": [435, 223, 678, 446], '
    '"32": [415, 203, 691, 487]}}</answer>\n'
    "Note: Each key in 'boxes' must correspond to a second (1, 2, 3, ..., 32) "
    "and contain a 4-number bounding box [x1, y1, x2, y2]."
)

# ---------------------------------------------------------------------------
# Budgets -- from data/eval/datasets.jsonl legacy_environment / preprocessing
# ---------------------------------------------------------------------------
BUDGETS = {
    "spatial_grounding": dict(kind="image", min_pixels=64 * DR * DR,
                              max_pixels=1024 * DR * DR),
    "temporal_grounding": dict(kind="video", min_pixels=1 * DR * DR,
                               max_pixels=409600, total_pixels=128000 * DR * DR,
                               max_frames=2048, fps=4),
    "tracking": dict(kind="video", min_pixels=4096, max_pixels=786432,
                     total_pixels=8388608, max_frames=32, fps=1),
}


def sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Parsers. Each returns (parsed_or_None, errors, warnings). Never repairs.
# ---------------------------------------------------------------------------
def extract_answer(text: str):
    m = re.findall(r"<answer>(.*?)</answer>", text, flags=re.S)
    return m[0].strip() if m else None


def parse_spatial_grounding(raw: str, ctx: dict):
    errors, warnings = [], []
    ans = extract_answer(raw)
    if ans is None:
        return None, ["no <answer> block found"], warnings
    try:
        obj = json.loads(ans)
    except Exception as exc:
        return None, [f"answer is not valid JSON: {exc}"], warnings
    if not isinstance(obj, list) or not obj:
        return None, ["JSON is not a non-empty list"], warnings
    boxes = []
    for i, item in enumerate(obj):
        if not isinstance(item, dict) or "bbox_2d" not in item:
            errors.append(f"item {i} lacks bbox_2d")
            continue
        b = item["bbox_2d"]
        if not (isinstance(b, list) and len(b) == 4
                and all(isinstance(v, (int, float)) for v in b)):
            errors.append(f"item {i} bbox_2d is not 4 numbers: {b!r}")
            continue
        boxes.append([float(v) for v in b])
    if not boxes:
        return None, errors or ["no usable bbox"], warnings
    parsed = {"boxes_norm1000": boxes}
    for i, b in enumerate(boxes):
        if min(b) < 0 or max(b) > 1000:
            errors.append(f"box {i} outside norm1000 range [0,1000]: {b}")
        if b[2] <= b[0] or b[3] <= b[1]:
            errors.append(f"box {i} has non-positive width/height: {b}")
    # pixel conversion is only an interpretation, computed for inspection
    w, h = ctx["image_w"], ctx["image_h"]
    parsed["boxes_px_from_norm1000"] = [
        [round(b[0] / 1000 * w, 2), round(b[1] / 1000 * h, 2),
         round(b[2] / 1000 * w, 2), round(b[3] / 1000 * h, 2)] for b in boxes]
    parsed["image_wh"] = [w, h]
    return parsed, errors, warnings


def parse_temporal_grounding(raw: str, ctx: dict):
    errors, warnings = [], []
    ans = extract_answer(raw)
    if ans is None:
        return None, ["no <answer> block found"], warnings
    nums = re.findall(r"[-+]?\d*\.?\d+", ans)
    if len(nums) < 2:
        return None, [f"could not find two numbers in answer {ans!r}"], warnings
    start, end = float(nums[0]), float(nums[1])
    parsed = {"span_sec": [start, end]}
    if start >= end:
        errors.append(f"start >= end ({start} >= {end})")
    dur = ctx["clip_duration_sec"]
    if start < 0 or end > dur:
        errors.append(f"span outside clip duration [0,{dur}]: [{start},{end}]")
    parsed["clip_duration_sec"] = dur
    parsed["span_as_fraction_of_clip"] = [round(start / dur, 4), round(end / dur, 4)]
    return parsed, errors, warnings


def parse_tracking(raw: str, ctx: dict):
    errors, warnings = [], []
    ans = extract_answer(raw)
    if ans is None:
        return None, ["no <answer> block found"], warnings
    try:
        obj = json.loads(ans)
    except Exception as exc:
        return None, [f"answer is not valid JSON: {exc}"], warnings
    if not isinstance(obj, dict) or not isinstance(obj.get("boxes"), dict):
        return None, ["JSON lacks a 'boxes' dict"], warnings
    boxes, bad = {}, []
    for k, v in obj["boxes"].items():
        try:
            sec = int(str(k).strip())
        except Exception:
            bad.append(f"key {k!r} is not an integer second")
            continue
        if not (isinstance(v, list) and len(v) == 4
                and all(isinstance(x, (int, float)) for x in v)):
            bad.append(f"second {sec} bbox is not 4 numbers: {v!r}")
            continue
        boxes[sec] = [float(x) for x in v]
    errors.extend(bad)
    if not boxes:
        return None, errors or ["no usable boxes"], warnings
    parsed = {"boxes_norm1000": {str(k): boxes[k] for k in sorted(boxes)}}
    for sec, b in sorted(boxes.items()):
        if sec < 1 or sec > 32:
            errors.append(f"second key {sec} outside 1..32")
        if min(b) < 0 or max(b) > 1000:
            errors.append(f"second {sec} box outside norm1000 range [0,1000]: {b}")
        if b[2] <= b[0] or b[3] <= b[1]:
            errors.append(f"second {sec} box has non-positive width/height: {b}")
    expected = set(range(1, 33))
    missing = sorted(expected - set(boxes))
    extra = sorted(set(boxes) - expected)
    parsed["seconds_present_n"] = len(boxes)
    parsed["seconds_present"] = sorted(boxes)
    if missing:
        warnings.append(f"missing seconds (n={len(missing)}): {missing}")
    if extra:
        warnings.append(f"unexpected seconds: {extra}")
    parsed["clip_duration_sec"] = ctx["clip_duration_sec"]
    return parsed, errors, warnings


PARSERS = {
    "spatial_grounding": parse_spatial_grounding,
    "temporal_grounding": parse_temporal_grounding,
    "tracking": parse_tracking,
}


def probe_media(path: str):
    """ffprobe a video OR a still image. `duration_sec` is None for images."""
    ffprobe = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
    out = subprocess.check_output(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames",
         "-show_entries", "format=duration,format_name", "-of", "json", path], text=True)
    d = json.loads(out)
    st = d["streams"][0]
    fmt = d.get("format", {})

    def frac(s):
        if not s:
            return None
        if "/" in s:
            n, dn = s.split("/")
            return float(n) / float(dn) if float(dn) else None
        return float(s)
    dur = fmt.get("duration")
    return {
        "width": int(st["width"]), "height": int(st["height"]),
        "fps_avg": frac(st.get("avg_frame_rate")),
        "r_frame_rate": frac(st.get("r_frame_rate")),
        "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
        "duration_sec": float(dur) if dur is not None else None,
        "format_name": fmt.get("format_name"),
    }


# backwards-compatible alias used for videos
probe_video = probe_media


def _md_get(md, key, default=None):
    """Video metadata may be a dict (decord/torchvision readers) or an object
    (transformers VideoMetadata). Read either without assuming."""
    if md is None:
        return default
    if isinstance(md, dict):
        return md.get(key, default)
    return getattr(md, key, default)


def _as_int_list(v):
    if v is None:
        return []
    if hasattr(v, "tolist"):
        v = v.tolist()
    return [int(x) for x in v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--samples", required=True, help="sample_manifest.json")
    ap.add_argument("--out", required=True, help="output dir")
    ap.add_argument("--attn", default="sdpa",
                    help="attn_implementation (author uses flash_attention_2)")
    ap.add_argument("--max-new-tokens-sg", type=int, default=1024)
    ap.add_argument("--max-new-tokens-tg", type=int, default=128)
    ap.add_argument("--max-new-tokens-tr", type=int, default=8192)
    ap.add_argument("--tasks", default="spatial_grounding,temporal_grounding,tracking")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    rawdir = outdir / "raw"
    rawdir.mkdir(exist_ok=True)

    manifest = json.load(open(args.samples))
    samples = manifest["tasks"]
    want = [t.strip() for t in args.tasks.split(",") if t.strip()]

    run = {
        "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
        "model_path": args.model,
        "attn_implementation": args.attn,
        "orarl_commit": "e1ec91ff00f59ee0da04d285938c1f7247daa69c",
        "hf_revision": "01850297d5ab2adaaf130f700ed7cec52993d956",
        "downsample_rate": DR,
        "deviations": [
            "attn_implementation=sdpa (author's HF evaluator uses flash_attention_2)",
            "HF Transformers generate() instead of vLLM 0.19.1",
            "no SAM2 segmentation post-processing",
            "one sample per task; task inputs are demonstration inputs, not ground truth",
        ],
        "tasks": {},
    }

    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    try:
        from qwen_vl_utils import process_vision_info
    except Exception as exc:
        print("FATAL: qwen_vl_utils unavailable:", exc, file=sys.stderr)
        raise

    print("=== FRAMEWORK / GPU CHECK (before model load) ===", flush=True)
    fw = {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if fw["cuda_available"]:
        p = torch.cuda.get_device_properties(0)
        fw.update(device_name=p.name, capability=f"{p.major}.{p.minor}",
                  total_memory_mib=round(p.total_memory / 2 ** 20))
        _ = (torch.randn(256, 256, device="cuda") @ torch.randn(256, 256, device="cuda"))
        torch.cuda.synchronize()
        fw["matmul_ok"] = True
    run["framework"] = fw
    for k, v in fw.items():
        print(f"  {k}: {v}", flush=True)
    if not fw["cuda_available"]:
        json.dump(run, open(outdir / "run_status.json", "w"), indent=2)
        raise SystemExit("CUDA not available; aborting (author evaluator also requires CUDA)")

    print("\n=== LOAD MODEL ===", flush=True)
    t0 = time.time()
    model = AutoModelForImageTextToText.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation=args.attn,
        device_map={"": "cuda:0"},
    ).eval()
    load_sec = time.time() - t0
    processor = AutoProcessor.from_pretrained(
        args.model, padding_side="left", do_resize=False, trust_remote_code=True)
    run["model_load_seconds"] = round(load_sec, 2)
    run["model_memory_allocated_mib_after_load"] = round(
        torch.cuda.memory_allocated() / 2 ** 20)
    run["model_param_dtype"] = str(next(model.parameters()).dtype)
    print(f"  loaded in {load_sec:.1f}s, "
          f"allocated {run['model_memory_allocated_mib_after_load']} MiB", flush=True)

    # author's build_spatial_grounding_prompt: strip, append '.' unless already punctuated
    expr = samples["spatial_grounding_image"]["expression"].strip()
    if expr and expr[-1] not in ".?!":
        expr += "."
    sg_prompt = QWEN_NATIVE_PROMPT_SG.format(expr)                      # .format == author's
    tg_event = samples["temporal_grounding_video"]["event"]
    tg_prompt = TEMPORAL_GROUNDING_PROMPT.format(tg_event)
    tr_target = samples["tracking_video"]["target_description"]
    tr_prompt = GROUNDING_QUESTION_TEMPLATE_NO_THINK.format(Question=tr_target) + TRACKING_TAIL

    def _vcontent(key, prof):
        return dict(type="video", video=samples[key]["input_video"],
                    **{k: BUDGETS[prof][k] for k in
                       ("min_pixels", "max_pixels", "total_pixels", "max_frames", "fps")})

    tasks = {
        "spatial_grounding": {
            "sample_key": "spatial_grounding_image",
            "prompt": sg_prompt,
            "content": lambda: [
                dict(type="image", image=samples["spatial_grounding_image"]["input_image"],
                     min_pixels=BUDGETS["spatial_grounding"]["min_pixels"],
                     max_pixels=BUDGETS["spatial_grounding"]["max_pixels"]),
                dict(type="text", text=sg_prompt),
            ],
            "max_new_tokens": args.max_new_tokens_sg,
        },
        "temporal_grounding": {
            "sample_key": "temporal_grounding_video",
            "prompt": tg_prompt,
            "content": lambda: [_vcontent("temporal_grounding_video", "temporal_grounding"),
                                dict(type="text", text=tg_prompt)],
            "max_new_tokens": args.max_new_tokens_tg,
        },
        "tracking": {
            "sample_key": "tracking_video",
            "prompt": tr_prompt,
            "content": lambda: [_vcontent("tracking_video", "tracking"),
                                dict(type="text", text=tr_prompt)],
            "max_new_tokens": args.max_new_tokens_tr,
        },
    }

    for name in want:
        spec = tasks[name]
        rec = {"status": "pending", "prompt": spec["prompt"],
               "sampling_profile": {k: v for k, v in BUDGETS[name].items()}}
        print(f"\n=== TASK {name} ===", flush=True)
        try:
            messages = [{"role": "user", "content": spec["content"]()}]
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=False)
            rec["chat_template_enable_thinking"] = False

            images, videos, video_kwargs = process_vision_info(
                messages, image_patch_size=16, return_video_kwargs=True,
                return_video_metadata=True)
            video_metadatas = None
            if videos:
                # process_vision_info returns [(tensor, metadata), ...] when
                # return_video_metadata=True. The processor requires a LIST of
                # metadata, not the tuple that zip() produces.
                videos, video_metadatas = zip(*videos)
                videos = list(videos)
                video_metadatas = list(video_metadatas)
            if video_metadatas:
                md = video_metadatas[0]
                fi = _as_int_list(_md_get(md, "frames_indices"))
                meta_fps = _md_get(md, "fps")
                rec["sampled_frames"] = {
                    "n_sampled": len(fi),
                    "frames_indices": fi,
                    "decoded_at_fps": meta_fps,
                    "source_total_num_frames": _md_get(md, "total_num_frames"),
                    "decoded_duration_sec": _md_get(md, "duration"),
                    "video_backend": _md_get(md, "video_backend"),
                    "sampling_convention": (
                        "nframes = clamp(round(duration*requested_fps), min_frames, "
                        "max_frames); indices = linspace(0, total_frames-1, nframes)"),
                }
                if meta_fps:
                    secs = [round(i / float(meta_fps), 4) for i in fi]
                    rec["sampled_frames"]["frames_seconds"] = secs
                    # explicit offset between the model's "second N" token and
                    # the timestamp actually sampled for that slot
                    rec["sampled_frames"]["secondN_vs_sampled_time"] = [
                        {"N": n + 1, "sampled_t_sec": secs[n]}
                        for n in range(len(secs))]
            rec["video_kwargs_from_processor"] = {
                k: v for k, v in (video_kwargs or {}).items() if k != "video_metadata"}

            inputs = processor(text=[text], images=images, videos=videos,
                               video_metadata=video_metadatas, padding=True,
                               return_tensors="pt", **video_kwargs)
            grid = {k: inputs[k].tolist() for k in
                    ("image_grid_thw", "video_grid_thw") if k in inputs}
            rec["grid_thw"] = grid
            if "video_grid_thw" in grid:
                tg = grid["video_grid_thw"][0]
                rec["video_tokens"] = int(tg[0] * tg[1] * tg[2] // (2 * 2))
            rec["input_ids_len"] = int(inputs["input_ids"].shape[-1])
            rec["processor_do_resize"] = False
            print(f"  input tokens={rec['input_ids_len']} grid={grid}", flush=True)

            inputs = inputs.to("cuda")
            torch.cuda.reset_peak_memory_stats()
            t1 = time.time()
            with torch.inference_mode():
                out_ids = model.generate(**inputs, do_sample=False,
                                         max_new_tokens=spec["max_new_tokens"])
            torch.cuda.synchronize()
            gen_sec = time.time() - t1
            trimmed = [o[len(inputs["input_ids"][0]):] for o in out_ids]
            raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=False)[0]

            rec["generate_seconds"] = round(gen_sec, 2)
            rec["output_tokens"] = int(out_ids.shape[-1] - inputs["input_ids"].shape[-1])
            rec["peak_memory_allocated_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
            rec["raw_output"] = raw
            (rawdir / f"{name}.raw.txt").write_text(raw)

            ctx = {}
            if name == "spatial_grounding":
                p = probe_media(samples["spatial_grounding_image"]["input_image"])
                ctx = {"image_w": p["width"], "image_h": p["height"]}
                rec["input_media_probe"] = p
            else:
                p = probe_media(samples[spec["sample_key"]]["input_video"])
                ctx = {"clip_duration_sec": p["duration_sec"]}
                rec["input_media_probe"] = p
                rec["time_mapping_note"] = (
                    "output times are relative to the derived clip; "
                    "t_source = t_clip + source_offset_sec (offset is 0.0 here)")
                rec["clip_zero_equals_source_zero"] = (
                    manifest["derived_clip"]["source_offset_sec"] == 0.0)

            parsed, errors, warnings = PARSERS[name](raw, ctx)
            rec["parsed"] = parsed
            rec["parse_errors"] = errors
            rec["parse_warnings"] = warnings
            rec["valid"] = (parsed is not None) and not errors
            rec["status"] = "ok" if rec["valid"] else "INVALID_OUTPUT"
            print(f"  valid={rec['valid']} errors={errors}", flush=True)
            print(f"  raw: {raw[:400]!r}", flush=True)
        except Exception as exc:
            rec["status"] = "ERROR"
            rec["valid"] = False
            rec["exception"] = f"{type(exc).__name__}: {exc}"
            rec["traceback"] = traceback.format_exc()
            print(f"  EXCEPTION: {rec['exception']}", flush=True)
            traceback.print_exc()
        run["tasks"][name] = rec
        json.dump(run, open(outdir / "run_status.json", "w"), indent=2, ensure_ascii=False)
        if "sampled_frames" in rec:
            json.dump(rec["sampled_frames"], open(outdir / f"sampled_frames_{name}.json", "w"),
                      indent=2)

    run["finished_utc"] = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
    run["total_seconds_gpu_stage"] = round(
        sum(v.get("generate_seconds", 0) for v in run["tasks"].values()), 2)
    json.dump(run, open(outdir / "run_status.json", "w"), indent=2, ensure_ascii=False)
    print(f"\n=== DONE valid_tasks="
          f"{[k for k, v in run['tasks'].items() if v.get('valid')]} ===", flush=True)
    if not any(v.get("valid") for v in run["tasks"].values()):
        raise SystemExit(3)


if __name__ == "__main__":
    main()
