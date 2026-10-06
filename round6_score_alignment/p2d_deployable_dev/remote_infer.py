"""Bounded, same-frame Qwen spatial inference for the frozen P2-D slice."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

from p2d_core import load_jsonl, sha256_file

BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")
MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()
PINNED_BASELINE = "a522244712831e7fddc605bce73b083851b7353dac1ceb2a9e4f41b948733631"
PINNED_MODEL = {
    "model-00001-of-00002.safetensors": "30a01a0556622645a3cce87b655bbbbbc1f170c196099f1b666c93202c3339a9",
    "model-00002-of-00002.safetensors": "046296a2a387efb43b0c997d5833c789604d168834f6e0d3064bf7bb13d002a6",
    "model.safetensors.index.json": "58a7841d7bff2548dd91577d216274a83cf1b500bc6a534b809d6c1b1707cf2b",
    "config.json": "edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d",
    "tokenizer.json": "a5d85b6dcc535e6b93115a9ef287e6132fdbf30270da6218194ba742261173c7",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("requests")
    parser.add_argument("freeze")
    parser.add_argument("identity_gate")
    parser.add_argument("output")
    args = parser.parse_args()
    requests_path, freeze_path, identity_path, output = map(
        Path, (args.requests, args.freeze, args.identity_gate, args.output))
    run_path = output.with_suffix(".run.json")
    partial = output.with_suffix(output.suffix + ".partial")
    if output.exists() or run_path.exists() or partial.exists():
        raise FileExistsError("refusing to overwrite an inference artifact")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    if not identity.get("gate_pass"):
        raise RuntimeError("source identity gate did not pass")
    if sha256_file(requests_path) != freeze["request_manifest"]["sha256"]:
        raise RuntimeError("request manifest differs from freeze")
    if identity.get("requests_sha256") != sha256_file(requests_path):
        raise RuntimeError("identity gate applies to a different request manifest")
    if sha256_file(BASELINE) != PINNED_BASELINE:
        raise RuntimeError("baseline implementation hash changed")
    model_hashes = {name: sha256_file(MODEL / name) for name in PINNED_MODEL}
    if model_hashes != PINNED_MODEL:
        raise RuntimeError("model input hash changed")

    requests = load_jsonl(requests_path)
    if len(requests) != len({(row["video_id"], int(row["source_frame"])) for row in requests}):
        raise RuntimeError("duplicate inference request")
    for row in requests:
        source = Path(row["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise RuntimeError(f"non-training source path: {source}")

    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    import cv2
    from PIL import Image

    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started
    invalid = 0
    peak_memory = 0.0
    status_counts = {}
    with partial.open("x", encoding="utf-8", newline="\n") as stream:
        for index, request in enumerate(requests, 1):
            row_started = time.monotonic()
            record = {
                "video_id": request["video_id"],
                "source_frame": int(request["source_frame"]),
                "request_key": request["request_key"],
                "request_sha256": request["request_sha256"],
                "spatial_source": "REAL_QWEN_SAME_FRAME",
                "used_fallback": False,
                "box_xyw": None,
                "raw_output": "",
                "parse_error": None,
            }
            try:
                cap = cv2.VideoCapture(str(request["source_path"]))
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(request["source_frame"]))
                ok, frame = cap.read()
                cap.release()
                if not ok:
                    raise RuntimeError("frame decode failed")
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if image.size != (int(request["source_width"]), int(request["source_height"])):
                    raise RuntimeError("decoded geometry changed")
                record["decoded_pixel_sha256"] = hashlib.sha256(memoryview(frame).cast("B")).hexdigest()
                tw, th = request["target_ratio_wh"]
                raw = model.predict_focus(image, (tw, th),
                                          max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
                record["raw_output"] = raw
                center = baseline.parse_focus_norm(raw, image.width, image.height)
                if center is None:
                    record["status"] = "PARSE_FAILURE"
                    record["parse_error"] = "no_valid_focus"
                else:
                    crop_w, crop_h = baseline.compute_crop_size(image.width, image.height, tw, th)
                    box = baseline.center_to_box(center[0], center[1], image.width,
                                                 image.height, crop_w, crop_h)
                    if baseline.validate_box(box, image.width, image.height, tw, th):
                        record["status"] = "MODEL_OK"
                        record["box_xyw"] = [int(v) for v in box]
                    else:
                        record["status"] = "INVALID_BOX"
                        record["parse_error"] = "baseline_validate_box_rejected"
            except Exception as exc:
                record["status"] = "DECODE_OR_MODEL_FAILURE"
                record["parse_error"] = f"{type(exc).__name__}: {exc}"
            record["seconds"] = round(time.monotonic() - row_started, 6)
            record["peak_memory_mib"] = round(float(model.peak_memory_mib()), 2)
            peak_memory = max(peak_memory, record["peak_memory_mib"])
            status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
            invalid += record["status"] != "MODEL_OK"
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            if index % 25 == 0 or index == len(requests):
                print(f"p2d {index}/{len(requests)} invalid={invalid}", flush=True)
    partial.replace(output)
    report = {
        "schema": "aic6_p2d_real_inference_v1",
        "status": "COMPLETED" if invalid == 0 else "COMPLETED_WITH_FAILURES",
        "official_status": "NOT_OFFICIAL_SCORE",
        "requests_sha256": sha256_file(requests_path),
        "freeze_sha256": sha256_file(freeze_path),
        "identity_gate_sha256": sha256_file(identity_path),
        "baseline_sha256": sha256_file(BASELINE),
        "model_hashes": model_hashes,
        "output_sha256": sha256_file(output),
        "rows": len(requests),
        "invalid": invalid,
        "status_counts": status_counts,
        "model_load_seconds": round(load_seconds, 6),
        "total_wall_seconds": round(time.monotonic() - started, 6),
        "peak_memory_mib": peak_memory,
        "weak_roi_inputs_used": 0,
        "old_test_boxes_used": 0,
        "silent_fallbacks": 0,
    }
    run_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

