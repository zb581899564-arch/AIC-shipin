"""Preserve all valid v1 anchors and infer only anchors from one repaired decoder video."""
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
    parser.add_argument("--requests-v2", type=Path, required=True)
    parser.add_argument("--previous-output", type=Path, required=True)
    parser.add_argument("--frame-manifest", type=Path, required=True)
    parser.add_argument("--expected-requests-sha256", required=True)
    parser.add_argument("--expected-previous-sha256", required=True)
    parser.add_argument("--expected-frame-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_path = args.output.with_suffix(args.output.suffix + ".run.json")
    if args.output.exists() or run_path.exists():
        raise FileExistsError("refusing to overwrite decoder repair inference")
    if (sha(args.requests_v2) != args.expected_requests_sha256 or
            sha(args.previous_output) != args.expected_previous_sha256 or
            sha(args.frame_manifest) != args.expected_frame_manifest_sha256):
        raise RuntimeError("decoder repair input hash mismatch")
    if sha(BASELINE) != PINNED_BASELINE:
        raise RuntimeError("baseline hash changed")
    requests = read_jsonl(args.requests_v2)
    previous = read_jsonl(args.previous_output)
    frames = read_jsonl(args.frame_manifest)
    previous_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in previous}
    frame_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in frames}
    repair_requests = []
    preserved = []
    for request in requests:
        key = (str(request["video_id"]), int(request["source_frame"]))
        old = previous_by_key.get(key)
        if (old is None or old.get("status") != "MODEL_OK" or
                old.get("anchor_request_sha256") != request["anchor_request_sha256"]):
            repair_requests.append(request)
        else:
            preserved.append(request)
    if not repair_requests or any((str(x["video_id"]), int(x["source_frame"])) not in frame_by_key
                                  for x in repair_requests):
        raise ValueError("repair frame manifest does not cover repaired anchors")
    for request in preserved:
        key = (str(request["video_id"]), int(request["source_frame"]))
        old = previous_by_key.get(key)
        if not old or old.get("status") != "MODEL_OK" or \
                old.get("anchor_request_sha256") != request["anchor_request_sha256"]:
            raise ValueError("a non-repair anchor cannot be preserved exactly")
    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    import cv2
    from PIL import Image
    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started
    repaired = {}
    for request in repair_requests:
        key = (str(request["video_id"]), int(request["source_frame"]))
        source = frame_by_key[key]
        one = time.monotonic()
        rec = {"video_id": key[0], "source_frame": key[1],
               "anchor_request_sha256": request["anchor_request_sha256"],
               "spatial_source": "QWEN_ANCHOR_SAME_FRAME", "used_fallback": False,
               "box_xyw": None, "raw_output": "", "parse_error": None,
               "decoder_repair": "SEQUENTIAL_OR_DECORD_IDENTITY_REPAIR"}
        try:
            frame_path = Path(source["frame_npy"])
            if sha(frame_path) != source["frame_npy_sha256"]:
                raise RuntimeError("repair frame file hash changed")
            frame = np.load(frame_path, allow_pickle=False)
            actual = hashlib.sha256(memoryview(frame).cast("B")).hexdigest()
            if actual != request["expected_pixel_sha256"] or actual != source["decoded_pixel_sha256"]:
                raise RuntimeError("repair frame identity mismatch")
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
            rec.update(status="REPAIR_FAILURE", parse_error=f"{type(exc).__name__}: {exc}")
        rec["seconds"] = round(time.monotonic() - one, 6)
        rec["peak_memory_mib"] = round(float(model.peak_memory_mib()), 2)
        repaired[key] = rec
    merged = []
    for request in requests:
        key = (str(request["video_id"]), int(request["source_frame"]))
        merged.append(repaired[key] if key in repaired else previous_by_key[key])
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for row in merged:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    invalid = sum(x.get("status") != "MODEL_OK" for x in merged)
    report = {"status": "COMPLETED" if invalid == 0 else "COMPLETED_WITH_FAILURES",
              "rows": len(merged), "preserved_valid_rows": len(preserved),
              "repaired_anchor_calls": len(repaired), "invalid": invalid,
              "requests_sha256": sha(args.requests_v2),
              "previous_output_sha256": sha(args.previous_output),
              "frame_manifest_sha256": sha(args.frame_manifest),
              "output_sha256": sha(args.output), "model_load_seconds": load_seconds,
              "wall_seconds": time.monotonic() - started,
              "peak_memory_mib": max(x.get("peak_memory_mib", 0) for x in repaired.values()),
              "weak_roi_inputs_used": 0, "old_test_boxes_used": 0, "silent_fallbacks": 0}
    run_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if invalid == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
