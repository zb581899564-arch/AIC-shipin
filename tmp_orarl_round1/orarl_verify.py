#!/usr/bin/env python3
"""orarl_verify.py — round-2 verification entry for Video-ORA-4B.

Fixes the six defects found in the round-1 entry point
(`orarl_round1/scripts/run_inference.py`):

  D1 four separate states instead of one boolean `valid`
       output_parseable / protocol_complete / task_success / quality
     A tracking answer missing required second-keys is parseable but NOT
     protocol_complete, and therefore NOT task_success.
  D2 any requested case failing -> non-zero process exit; a per-case status
     table is always written and printed.
  D3 every run gets its own --run-id and output directory; an existing
     directory is refused (never overwritten).
  D4 strict JSON: NaN/Infinity rejected, booleans rejected as numbers,
     duplicate JSON keys rejected, multiple <answer> blocks rejected.
     Temporal parsing requires EXACTLY two numbers in the answer body and
     refuses to silently take the first two and ignore the rest.
  D5 the expected tracking key set comes from the case's declared protocol +
     sample configuration (`expected_seconds`), never a hard-coded 1..32.
  D6 tested by `test_orarl_verify.py`, which runs end-to-end with a canned
     generator (--fake-generator) so no GPU is needed.

Parsers are pure functions importable without torch.

Usage:
  orarl_verify.py --model M --cases cases.jsonl --out-root DIR --run-id ID
  orarl_verify.py --cases cases.jsonl --out-root DIR --run-id ID --dry-run
  orarl_verify.py --cases cases.jsonl --out-root DIR --run-id ID \
                  --fake-generator canned.jsonl          # TEST ONLY
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

DR = 32

# --- literals from eval/task/eval_prompt.py @ e1ec91f ----------------------
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


# ===========================================================================
# D4 — strict decoding primitives
# ===========================================================================

class StrictParseError(ValueError):
    pass


def split_single_answer(raw):
    """Return the single <answer> body. 0 or >1 blocks is an error.

    More than one block is an *ambiguous* output, not a formatting nuisance:
    the round-1 parser silently took the first match.
    """
    if not isinstance(raw, str):
        raise StrictParseError("output is not a string")
    blocks = re.findall(r"<answer>(.*?)</answer>", raw, flags=re.S | re.I)
    if len(blocks) == 0:
        raise StrictParseError("no <answer>...</answer> block found")
    if len(blocks) > 1:
        raise StrictParseError(
            f"ambiguous output: {len(blocks)} <answer> blocks found; expected exactly 1")
    return blocks[0].strip()


def _reject_constant(name):
    raise StrictParseError(f"non-finite JSON constant {name!r} is not a valid number")


def _no_duplicate_keys(pairs):
    seen, dup = set(), []
    for k, _ in pairs:
        if k in seen:
            dup.append(k)
        seen.add(k)
    if dup:
        raise StrictParseError(
            "duplicate JSON keys are ambiguous: " + ", ".join(sorted(set(dup))))
    return dict(pairs)


def strict_json_loads(text):
    try:
        return json.loads(text, parse_constant=_reject_constant,
                          object_pairs_hook=_no_duplicate_keys)
    except StrictParseError:
        raise
    except json.JSONDecodeError as exc:
        raise StrictParseError(f"answer is not valid JSON: {exc}") from exc


def is_real_number(v):
    """bool subclasses int in python; `true` must not pass as 1."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return False
    return True


def as_box4(v):
    if not isinstance(v, list) or len(v) != 4:
        raise StrictParseError(f"bounding box must be a list of 4 numbers, got {v!r}")
    if not all(is_real_number(x) for x in v):
        bad = [x for x in v if not is_real_number(x)]
        raise StrictParseError(f"bounding box has non-numeric or boolean entries: {bad!r}")
    return [float(x) for x in v]


def check_norm1000(box, where, errors):
    if min(box) < 0 or max(box) > 1000:
        errors.append(f"{where}: box outside norm1000 range [0,1000]: {box}")
    if box[2] <= box[0] or box[3] <= box[1]:
        errors.append(f"{where}: box has non-positive width/height: {box}")


# ===========================================================================
# Task parsers -> (parsed_or_None, errors, warnings)
# `expected` always comes from the CASE (D5)
# ===========================================================================

def parse_tracking_strict(raw, expected):
    errors, warnings = [], []
    try:
        obj = strict_json_loads(split_single_answer(raw))
    except StrictParseError as exc:
        return None, [str(exc)], warnings
    if not isinstance(obj, dict):
        return None, ["answer JSON is not an object"], warnings
    extra_top = sorted(set(obj) - {"boxes"})
    if extra_top:
        warnings.append(f"unexpected top-level keys ignored: {extra_top}")
    if "boxes" not in obj:
        return None, ["answer JSON has no 'boxes' key"], warnings
    boxes_raw = obj["boxes"]
    if not isinstance(boxes_raw, dict):
        return None, [f"'boxes' must be an object, got {type(boxes_raw).__name__}"], warnings
    if not boxes_raw:
        return None, ["'boxes' is empty"], warnings

    boxes = {}
    for k, v in boxes_raw.items():
        if isinstance(k, str) and re.fullmatch(r"\s*[-+]?\d+\s*", k):
            sec = int(k.strip())
        else:
            errors.append(f"key {k!r} is not an integer second")
            continue
        try:
            boxes[sec] = as_box4(v)
        except StrictParseError as exc:
            errors.append(f"second {sec}: {exc}")
    if not boxes:
        return None, errors or ["no usable boxes"], warnings
    for sec in sorted(boxes):
        check_norm1000(boxes[sec], f"second {sec}", errors)

    exp = expected.get("expected_seconds")
    if not exp:
        errors.append("case does not declare expected_seconds; "
                      "cannot judge protocol completeness")
        exp = []
    exp_set, got_set = {int(s) for s in exp}, set(boxes)
    missing = sorted(exp_set - got_set)
    unexpected = sorted(got_set - exp_set)
    parsed = {
        "boxes_norm1000": {str(k): boxes[k] for k in sorted(boxes)},
        "seconds_present_n": len(boxes),
        "seconds_present": sorted(boxes),
        "expected_seconds_n": len(exp),
        "missing_expected_seconds": missing,
        "unexpected_seconds": unexpected,
        # descriptive only — NOT a quality metric (see REPORT.md)
        "distinct_boxes_n": len({tuple(boxes[k]) for k in boxes}),
    }
    if missing:
        errors.append(f"protocol incomplete: missing required seconds "
                      f"{missing[:12]}{' ...' if len(missing) > 12 else ''}")
    if unexpected:
        warnings.append(f"seconds outside the declared protocol: {unexpected[:12]}")
    return parsed, errors, warnings


def parse_spatial_grounding_strict(raw, expected):
    errors, warnings = [], []
    try:
        obj = strict_json_loads(split_single_answer(raw))
    except StrictParseError as exc:
        return None, [str(exc)], warnings
    if not isinstance(obj, list) or not obj:
        return None, ["answer JSON is not a non-empty list"], warnings
    boxes = []
    for i, item in enumerate(obj):
        if not isinstance(item, dict):
            errors.append(f"item {i} is not an object")
            continue
        if "bbox_2d" not in item:
            errors.append(f"item {i} has no 'bbox_2d'")
            continue
        try:
            boxes.append(as_box4(item["bbox_2d"]))
        except StrictParseError as exc:
            errors.append(f"item {i}: {exc}")
    if not boxes:
        return None, errors or ["no usable bbox"], warnings
    for i, b in enumerate(boxes):
        check_norm1000(b, f"box {i}", errors)
    w, h = expected.get("image_w"), expected.get("image_h")
    parsed = {"boxes_norm1000": boxes,
              "image_wh": [w, h] if w and h else None,
              "boxes_px_from_norm1000": ([[round(b[0] / 1000 * w, 2), round(b[1] / 1000 * h, 2),
                                           round(b[2] / 1000 * w, 2), round(b[3] / 1000 * h, 2)]
                                          for b in boxes] if w and h else None)}
    return parsed, errors, warnings


_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"
_TEMPORAL_BODY_RE = re.compile(
    r"^\s*(" + _NUM + r")\s*(?:to|until|through|-|–|—|,|~)\s*(" + _NUM + r")\s*$", re.I)


def parse_temporal_grounding_strict(raw, expected):
    """The body must contain EXACTLY two numbers and nothing else.

    Round-1 behaviour ('findall numbers, take the first two') silently accepted
    e.g. '12 to 18 to 25' and ignored trailing content. Rejected here.
    """
    errors, warnings = [], []
    try:
        body = split_single_answer(raw)
    except StrictParseError as exc:
        return None, [str(exc)], warnings
    all_nums = re.findall(_NUM, body)
    if len(all_nums) != 2:
        return None, [f"temporal answer body must contain exactly 2 numbers, found "
                      f"{len(all_nums)} in {body!r}"], warnings
    m = _TEMPORAL_BODY_RE.match(body)
    if not m:
        return None, [f"temporal answer body is not '<start> to <end>' with exactly two "
                      f"numbers and no extra text: {body!r}"], warnings
    start, end = float(m.group(1)), float(m.group(2))
    parsed = {"span_sec": [start, end], "clip_duration_sec": expected.get("clip_duration_sec")}
    if start >= end:
        errors.append(f"start >= end ({start} >= {end})")
    dur = expected.get("clip_duration_sec")
    if dur is not None:
        if start < 0 or end > dur:
            errors.append(f"span outside clip duration [0,{dur}]: [{start},{end}]")
        if dur:
            parsed["span_as_fraction_of_clip"] = [round(start / dur, 4), round(end / dur, 4)]
    return parsed, errors, warnings


PARSERS = {
    "tracking": parse_tracking_strict,
    "spatial_grounding": parse_spatial_grounding_strict,
    "temporal_grounding": parse_temporal_grounding_strict,
}


def evaluate_states(raw, task, expected, exec_error=None):
    """Return the four-state record for one case (D1)."""
    rec = {"output_parseable": False, "protocol_complete": False, "task_success": False,
           "quality": {"status": "NOT_COMPUTABLE",
                       "reason": "no trusted ground truth declared for this case"},
           "parse_errors": [], "parse_warnings": [], "parsed": None,
           "execution_error": exec_error, "protocol_error_kinds": []}
    if exec_error:
        return rec
    parser = PARSERS.get(task)
    if parser is None:
        rec["parse_errors"] = [f"unknown task {task!r}"]
        return rec
    parsed, errors, warnings = parser(raw, expected or {})
    rec["parsed"], rec["parse_errors"], rec["parse_warnings"] = parsed, errors, warnings
    rec["output_parseable"] = parsed is not None
    rec["protocol_complete"] = bool(parsed is not None and not errors)
    rec["task_success"] = rec["output_parseable"] and rec["protocol_complete"]
    rec["protocol_error_kinds"] = sorted(
        {"protocol_incomplete" if e.startswith("protocol incomplete") else "shape_or_range"
         for e in errors})
    if parsed is not None and errors:
        rec["quality"] = {"status": "NOT_COMPUTABLE",
                          "reason": "output failed protocol/range checks: "
                                    + "; ".join(errors[:3])}
    return rec


# ===========================================================================
# D5 — expected key set from the case's protocol + sample config
# ===========================================================================

def resolve_expected_seconds(case):
    """Never a blanket 1..32.

    1. explicit case["expected_seconds"] (frozen in the case file), else
    2. derived: n = clamp(round(duration*fps), min_frames, max_frames);
       seconds = 1..n. Key N is the N-th one-second bin, matching
       eval_tracking_vllm.py lines 529-535 ("GT-second labels ... are REAL
       seconds ... NOT sampled-frame indices").
    """
    if case.get("expected_seconds"):
        return [int(s) for s in case["expected_seconds"]]
    prof = case.get("sampling") or {}
    fps = float(prof.get("fps", 1))
    mx = int(prof.get("max_frames", 32))
    mn = int(prof.get("min_frames", 4))
    dur = case.get("clip_duration_sec")
    if dur is None:
        raise ValueError("case needs either expected_seconds or clip_duration_sec")
    n = int(round(float(dur) * fps))
    n = max(mn, min(mx, n))
    return list(range(1, n + 1))


# ===========================================================================
# Prompt / media helpers
# ===========================================================================

def build_prompt(case):
    if case["task"] == "tracking":
        return GROUNDING_QUESTION_TEMPLATE_NO_THINK.format(
            Question=case["question"]) + TRACKING_TAIL
    if case["task"] == "spatial_grounding":
        expr = case["expression"].strip()
        if expr and expr[-1] not in ".?!":
            expr += "."
        return QWEN_NATIVE_PROMPT_SG.format(expr)
    if case["task"] == "temporal_grounding":
        return TEMPORAL_GROUNDING_PROMPT.format(case["event"])
    raise ValueError(f"unknown task {case['task']!r}")


def build_content(case):
    if case["task"] == "spatial_grounding":
        prof = case.get("sampling") or {}
        item = {"type": "image", "image": case["image"]}
        for k in ("min_pixels", "max_pixels"):
            if prof.get(k) is not None:
                item[k] = prof[k]
        return [item, {"type": "text", "text": build_prompt(case)}]
    prof = case.get("sampling") or {}
    item = {"type": "video", "video": case["video"],
            "fps": prof.get("fps", 1), "max_frames": prof.get("max_frames", 32)}
    for k in ("min_pixels", "max_pixels", "total_pixels"):
        if prof.get(k) is not None:
            item[k] = prof[k]
    for k in ("video_start", "video_end"):
        if case.get(k) is not None:
            item[k] = case[k]
    return [item, {"type": "text", "text": build_prompt(case)}]


def sha256_file(p, chunk=1 << 22):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def probe_media(path):
    ffprobe = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
    out = subprocess.check_output(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path], text=True)
    d = json.loads(out)
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    dur = d.get("format", {}).get("duration")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "fps": float(n) / float(dn) if float(dn) else None,
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration_sec": float(dur) if dur is not None else None}


def resolve_cases(cases):
    """Pin media facts + expected key sets BEFORE any GPU work."""
    for c in cases:
        media_path = c["image"] if c["task"] == "spatial_grounding" else c["video"]
        m = probe_media(media_path)
        c["_media"] = m
        c["_sha256"] = sha256_file(media_path)
        if c["task"] == "spatial_grounding":
            c["_expected"] = {"image_w": m["width"], "image_h": m["height"]}
        elif c["task"] == "tracking":
            if c.get("clip_duration_sec") is None:
                c["clip_duration_sec"] = m["duration_sec"]
            c["_expected"] = {"expected_seconds": resolve_expected_seconds(c)}
        else:
            if c.get("clip_duration_sec") is None:
                c["clip_duration_sec"] = m["duration_sec"]
            c["_expected"] = {"clip_duration_sec": c["clip_duration_sec"]}
    return cases


# ===========================================================================
# Generators
# ===========================================================================

def make_model_generator(model_path, attn):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from qwen_vl_utils import process_vision_info
    t0 = time.time()
    model = AutoModelForImageTextToText.from_pretrained(
        model_path, dtype=torch.bfloat16, attn_implementation=attn,
        device_map={"": "cuda:0"}).eval()
    load_s = round(time.time() - t0, 2)
    processor = AutoProcessor.from_pretrained(
        model_path, padding_side="left", do_resize=False, trust_remote_code=True)

    def generate(case):
        messages = [{"role": "user", "content": build_content(case)}]
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        images, videos, video_kwargs = process_vision_info(
            messages, image_patch_size=16, return_video_kwargs=True,
            return_video_metadata=True)
        vmd = None
        if videos:
            videos, vmd = zip(*videos)
            videos, vmd = list(videos), list(vmd)
        extra = {}
        if vmd:
            g = (lambda k: vmd[0].get(k)) if isinstance(vmd[0], dict) \
                else (lambda k: getattr(vmd[0], k, None))
            fi = g("frames_indices")
            fi = fi.tolist() if hasattr(fi, "tolist") else fi
            mfps = g("fps")
            extra["sampling_observed"] = {
                "n_sampled": len(fi or []), "frames_indices": fi,
                "decoded_at_fps": mfps, "video_backend": g("video_backend"),
                "second_bin_per_slot": ([int(i // mfps) for i in fi]
                                        if mfps and fi else None),
                "method": "nframes=clamp(round(duration*fps),min_frames,max_frames); "
                          "indices=linspace(0,total_frames-1,nframes)",
            }
        inputs = processor(text=[text], images=images, videos=videos, video_metadata=vmd,
                           padding=True, return_tensors="pt", **video_kwargs)
        extra["input_ids_len"] = int(inputs["input_ids"].shape[-1])
        inputs = inputs.to("cuda")
        torch.cuda.reset_peak_memory_stats()
        ts = time.time()
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False,
                                 max_new_tokens=case.get("max_new_tokens", 8192))
        torch.cuda.synchronize()
        extra["generate_seconds"] = round(time.time() - ts, 2)
        extra["peak_memory_allocated_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
        trimmed = [o[len(inputs["input_ids"][0]):] for o in out]
        raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                     clean_up_tokenization_spaces=False)[0]
        return raw, extra

    return generate, load_s


def make_fake_generator(path):
    """TEST ONLY: canned outputs so D1/D2/D3 can be tested without a GPU."""
    table = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            table[d["case_id"]] = d

    def generate(case):
        d = table.get(case["case_id"], {})
        if d.get("raise"):
            raise RuntimeError(d["raise"])
        return d.get("raw_output", ""), {"fake": True}

    return generate, 0.0


# ===========================================================================
# Runner
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description="round-2 Video-ORA verification entry")
    ap.add_argument("--model", default="")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--tasks", default="")
    ap.add_argument("--case-ids", default="")
    ap.add_argument("--attn", default="sdpa")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve the plan and exit; no model, no GPU")
    ap.add_argument("--fake-generator", default="",
                    help="TEST ONLY: JSONL case_id -> canned raw_output; bypasses the model")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        print("FATAL: --run-id may contain only [A-Za-z0-9._-]", file=sys.stderr)
        return 2

    run_dir = Path(args.out_root) / args.run_id
    if run_dir.exists():                                   # D3
        print(f"FATAL: run directory already exists, refusing to overwrite: {run_dir}",
              file=sys.stderr)
        return 3

    cases = [json.loads(l) for l in Path(args.cases).read_text().splitlines() if l.strip()]
    if args.tasks:
        want = {t.strip() for t in args.tasks.split(",") if t.strip()}
        cases = [c for c in cases if c["task"] in want]
    if args.case_ids:
        want = {t.strip() for t in args.case_ids.split(",") if t.strip()}
        cases = [c for c in cases if c["case_id"] in want]
    if not cases:
        print("FATAL: no cases selected", file=sys.stderr)
        return 2

    resolve_cases(cases)
    plan = [{"case_id": c["case_id"], "task": c["task"], "condition": c.get("condition"),
             "expected_seconds_n": len(c["_expected"].get("expected_seconds", [])),
             "media": c["_media"], "sha256": c["_sha256"]} for c in cases]
    print(f"resolved {len(cases)} cases:")
    for p in plan:
        print("  ", json.dumps(p, ensure_ascii=False))

    if args.dry_run:
        run_dir.mkdir(parents=True)
        (run_dir / "cases_resolved.json").write_text(
            json.dumps({"cases": cases, "plan": plan}, indent=2, ensure_ascii=False) + "\n")
        print(f"\nDRY RUN ok; wrote {run_dir/'cases_resolved.json'}")
        return 0

    run_dir.mkdir(parents=True)                            # D3: created once
    (run_dir / "raw").mkdir()

    run = {"run_id": args.run_id, "cases_file": str(Path(args.cases).resolve()),
           "cases_file_sha256": sha256_file(args.cases),
           "model": args.model, "attn_implementation": args.attn,
           "fake_generator": args.fake_generator or None,
           "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
           "requested_case_ids": [c["case_id"] for c in cases],
           "state_definitions": {
               "output_parseable": "model text decodes under the task schema",
               "protocol_complete": ("parseable AND every protocol-required field present and "
                                     "in range, no duplicate keys, no ambiguous multi-answer output"),
               "task_success": "protocol_complete AND no execution error",
               "quality": "NOT_COMPUTABLE unless a trusted ground truth is declared"},
           }
    if args.fake_generator:
        generate, load_s = make_fake_generator(args.fake_generator)
        run["generator"] = "FAKE (test only)"
    else:
        if not args.model:
            print("FATAL: --model is required unless --dry-run/--fake-generator",
                  file=sys.stderr)
            return 2
        import torch  # noqa: F401
        generate, load_s = make_model_generator(args.model, args.attn)
        run["generator"] = "Video-ORA-4B via HF Transformers"
        run["of"] = {"python": sys.version.split()[0],
                     "torch": __import__("torch").__version__,
                     "transformers": __import__("transformers").__version__,
                     "torch_cuda": __import__("torch").version.cuda,
                     "cuda_available": __import__("torch").cuda.is_available()}
        if __import__("torch").cuda.is_available():
            p = __import__("torch").cuda.get_device_properties(0)
            run["of"].update(device_name=p.name, total_memory_mib=round(p.total_memory / 2 ** 20))
    run["model_load_seconds"] = load_s
    print("framework:", json.dumps(run.get("of", {}), ensure_ascii=False))

    results, n_failed = [], 0
    for c in cases:
        cid = c["case_id"]
        print(f"\n=== CASE {cid} ({c['task']}, condition={c.get('condition')}) ===")
        rec = {"case_id": cid, "task": c["task"], "condition": c.get("condition"),
               "sample_id": c.get("sample_id"), "video": c.get("video") or c.get("image"),
               "video_sha256": c["_sha256"], "prompt": build_prompt(c),
               "init_box_norm1000": c.get("init_box_norm1000"),
               "init_box_source": c.get("init_box_source"),
               "ground_truth": c.get("ground_truth"),
               "is_test_set": bool(c.get("is_test_set", False)),
               "expected": c["_expected"], "media": c["_media"]}
        try:
            raw, extra = generate(c)
            rec.update(extra)
            rec["raw_output"] = raw
            (run_dir / "raw" / f"{cid}.raw.txt").write_text(raw)
            rec.update(evaluate_states(raw, c["task"], c["_expected"]))
        except Exception as exc:
            rec["traceback"] = traceback.format_exc()
            rec.update(evaluate_states("", c["task"], c["_expected"],
                                       exec_error=f"{type(exc).__name__}: {exc}"))
        if not rec["task_success"]:
            n_failed += 1
        print(f"  parseable={rec['output_parseable']} "
              f"protocol_complete={rec['protocol_complete']} "
              f"task_success={rec['task_success']} quality={rec['quality']['status']}")
        if rec["parse_errors"]:
            print(f"  errors={rec['parse_errors'][:3]}")
        results.append(rec)
        json.dump({"run": run, "cases": results},
                  open(run_dir / "run_status.json", "w"), indent=2, ensure_ascii=False)

    run["finished_utc"] = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
    run.update(n_cases=len(cases), n_task_success=len(cases) - n_failed, n_failed=n_failed)
    run["exit_code"] = 0 if n_failed == 0 else 5
    json.dump({"run": run, "cases": results},
              open(run_dir / "run_status.json", "w"), indent=2, ensure_ascii=False)
    json.dump(run, open(run_dir / "summary.json", "w"), indent=2, ensure_ascii=False)

    print("\n================ PER-CASE STATUS (D2) ================")
    for r in results:
        print(f"  {r['case_id']:30s} {r['task']:20s} "
              f"parseable={str(r['output_parseable']):5s} "
              f"protocol={str(r['protocol_complete']):5s} "
              f"success={str(r['task_success']):5s} quality={r['quality']['status']}")
    print(f"\n{n_failed} of {len(cases)} cases FAILED -> exit code {run['exit_code']}")
    print("wrote", run_dir / "run_status.json")
    return run["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
