"""Run same-frame Qwen only on pre-frozen P2-J anchor frames."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from a_contract import sha
from p2j_core import read_jsonl, sha256_file, write_jsonl
from pts_contract import BRANCH_NATIVE, VARIANT, load_clocks, validate_frame_request
from native_frames import VerifiedNativeReader

BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")
MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
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
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--expected-requests-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--clock-registry", type=Path, required=True)
    parser.add_argument("--expected-clock-registry-sha256", required=True)
    args = parser.parse_args()
    if sha(args.manifest) != args.expected_manifest_sha256:
        raise ValueError("spatial manifest identity changed")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clocks = load_clocks(manifest, args.clock_registry, args.expected_clock_registry_sha256)
    metadata = {r["video_id"]: r for r in manifest["records"]}
    native_decoders = {}
    run_path = args.output.with_suffix(args.output.suffix + ".run.json")
    partial = args.output.with_suffix(args.output.suffix + ".partial")
    if args.output.exists() or run_path.exists() or partial.exists():
        raise FileExistsError("refusing to overwrite anchor inference")
    if sha256_file(args.requests) != args.expected_requests_sha256:
        raise RuntimeError("anchor request hash differs from frozen input")
    if sha256_file(BASELINE) != PINNED_BASELINE:
        raise RuntimeError("baseline implementation hash changed")
    model_hashes = {name: sha256_file(MODEL / name) for name in PINNED_MODEL}
    if model_hashes != PINNED_MODEL:
        raise RuntimeError("model hashes changed")
    requests = read_jsonl(args.requests)
    keys = [(r["video_id"], int(r["source_frame"])) for r in requests]
    if not requests or len(keys) != len(set(keys)):
        raise ValueError("empty or duplicate anchor requests")

    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    import cv2
    from PIL import Image
    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started
    rows = []
    for request in requests:
        one = time.monotonic()
        rec = {"video_id": request["video_id"], "source_frame": int(request["source_frame"]),
               "anchor_request_sha256": request["anchor_request_sha256"],
               "spatial_source": "QWEN_ANCHOR_SAME_FRAME", "used_fallback": False,
               "box_xyw": None, "raw_output": "", "parse_error": None}
        try:
            source_row = validate_frame_request(request, metadata)
            clock = clocks[request["video_id"]]
            if clock["branch"] == BRANCH_NATIVE:
                if request["video_id"] not in native_decoders:
                    native_decoders[request["video_id"]] = VerifiedNativeReader(request["source_path"], source_row, clock)
                frame = native_decoders[request["video_id"]].read(request["source_frame"])
                rec.update(clock_branch=BRANCH_NATIVE, clock_record_sha256=clock["clock_record_sha256"],
                           decoder_identity="SEQUENTIAL_DECODED_SOURCE_ORDINAL")
            else:
                cap = cv2.VideoCapture(request["source_path"])
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(request["source_frame"]))
                ok, frame = cap.read()
                cap.release()
                if not ok:
                    raise RuntimeError("frame decode failed")
            pixel_hash = hashlib.sha256(memoryview(frame).cast("B")).hexdigest()
            rec["decoded_pixel_sha256"] = pixel_hash
            if pixel_hash != request["expected_pixel_sha256"]:
                raise RuntimeError("decoded frame identity changed")
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
            rec.update(status="DECODE_OR_MODEL_FAILURE",
                       parse_error=f"{type(exc).__name__}: {exc}")
        rec["seconds"] = round(time.monotonic() - one, 6)
        rec["peak_memory_mib"] = round(float(model.peak_memory_mib()), 2)
        rows.append(rec)
    write_jsonl(args.output, rows)
    invalid = sum(r["status"] != "MODEL_OK" for r in rows)
    report = {
        "status": "COMPLETED" if invalid == 0 else "COMPLETED_WITH_FAILURES",
        "requests_sha256": sha256_file(args.requests), "output_sha256": sha256_file(args.output),
        "rows": len(rows), "invalid": invalid, "model_load_seconds": load_seconds,
        "wall_seconds": time.monotonic() - started,
        "peak_memory_mib": max(r["peak_memory_mib"] for r in rows),
        "weak_roi_inputs_used": 0, "old_test_boxes_used": 0, "silent_fallbacks": 0,
        "baseline_sha256": sha256_file(BASELINE), "model_hashes": model_hashes,
    }
    run_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if invalid == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
