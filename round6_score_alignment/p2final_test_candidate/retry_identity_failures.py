"""Retry only pinned identity failures from lossless sequential-decoder frames."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")
MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
PINNED_BASELINE = "a522244712831e7fddc605bce73b083851b7353dac1ceb2a9e4f41b948733631"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--previous-output", type=Path, required=True)
    parser.add_argument("--retry-manifest", type=Path, required=True)
    parser.add_argument("--expected-requests-sha256", required=True)
    parser.add_argument("--expected-previous-sha256", required=True)
    parser.add_argument("--expected-retry-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_path = args.output.with_suffix(args.output.suffix + ".run.json")
    if args.output.exists() or run_path.exists():
        raise FileExistsError("refusing to overwrite retry output")
    if sha(args.requests) != args.expected_requests_sha256 or \
            sha(args.previous_output) != args.expected_previous_sha256 or \
            sha(args.retry_manifest) != args.expected_retry_sha256:
        raise RuntimeError("retry input hash mismatch")
    if sha(BASELINE) != PINNED_BASELINE:
        raise RuntimeError("baseline hash changed")
    requests = read_jsonl(args.requests)
    previous = read_jsonl(args.previous_output)
    retry = read_jsonl(args.retry_manifest)
    request_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in requests}
    previous_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in previous}
    retry_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in retry}
    bad_keys = {key for key, row in previous_by_key.items() if row.get("status") != "MODEL_OK"}
    if set(request_by_key) != set(previous_by_key) or set(retry_by_key) != bad_keys:
        raise ValueError("retry keys do not equal the exact previous failure set")
    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    import cv2
    from PIL import Image
    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started
    replacements = {}
    for key in sorted(retry_by_key):
        item, request = retry_by_key[key], request_by_key[key]
        one = time.monotonic()
        rec = {"video_id": key[0], "source_frame": key[1],
               "anchor_request_sha256": request["anchor_request_sha256"],
               "spatial_source": "QWEN_ANCHOR_SAME_FRAME", "used_fallback": False,
               "box_xyw": None, "raw_output": "", "parse_error": None,
               "retry_reason": "RANDOM_SEEK_IDENTITY_MISMATCH"}
        try:
            frame_path = Path(item["frame_npy"])
            if sha(frame_path) != item["frame_npy_sha256"]:
                raise RuntimeError("lossless retry frame file hash changed")
            frame = np.load(frame_path, allow_pickle=False)
            pixel_hash = hashlib.sha256(memoryview(frame).cast("B")).hexdigest()
            rec["decoded_pixel_sha256"] = pixel_hash
            if pixel_hash != request["expected_pixel_sha256"]:
                raise RuntimeError("sequential retry frame identity changed")
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tw, th = request["target_ratio_wh"]
            raw = model.predict_focus(image, (tw, th), max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
            rec["raw_output"] = raw
            center = baseline.parse_focus_norm(raw, image.width, image.height)
            if center is None:
                rec.update(status="PARSE_FAILURE", parse_error="no_valid_focus")
            else:
                crop_w, crop_h = baseline.compute_crop_size(image.width, image.height, tw, th)
                box = baseline.center_to_box(center[0], center[1], image.width, image.height,
                                             crop_w, crop_h)
                if baseline.validate_box(box, image.width, image.height, tw, th):
                    rec.update(status="MODEL_OK", box_xyw=[int(x) for x in box])
                else:
                    rec.update(status="INVALID_BOX", parse_error="validate_box_rejected")
        except Exception as exc:
            rec.update(status="RETRY_FAILURE", parse_error=f"{type(exc).__name__}: {exc}")
        rec["seconds"] = round(time.monotonic() - one, 6)
        rec["peak_memory_mib"] = round(float(model.peak_memory_mib()), 2)
        replacements[key] = rec
    merged = [replacements.get((str(row["video_id"]), int(row["source_frame"])), row)
              for row in previous]
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for row in merged:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    invalid = sum(x.get("status") != "MODEL_OK" for x in merged)
    report = {"status": "COMPLETED" if invalid == 0 else "COMPLETED_WITH_FAILURES",
              "rows": len(merged), "retried": len(replacements), "invalid": invalid,
              "preserved_valid_rows": len(merged) - len(replacements),
              "requests_sha256": sha(args.requests), "previous_output_sha256": sha(args.previous_output),
              "retry_manifest_sha256": sha(args.retry_manifest), "output_sha256": sha(args.output),
              "model_load_seconds": load_seconds, "wall_seconds": time.monotonic() - started,
              "peak_memory_mib": max(x.get("peak_memory_mib", 0) for x in replacements.values()),
              "weak_roi_inputs_used": 0, "old_test_boxes_used": 0, "silent_fallbacks": 0}
    run_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if invalid == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
