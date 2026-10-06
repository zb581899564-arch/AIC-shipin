"""Run the existing Qwen3-VL focus call on frozen training-dev frames only.

The output is a weak-proxy diagnostic input. Invalid predictions remain explicit
and are never replaced with a center crop in this arm.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path


BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")
MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def file_sha256(path: Path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main(frozen_path: str, extracted_path: str, out_path: str):
    frozen_file, extracted_file, output = Path(frozen_path), Path(extracted_path), Path(out_path)
    frozen, extracted = load_jsonl(frozen_file), load_jsonl(extracted_file)
    indexed = {item["sample_key"]: item for item in extracted}
    if len(frozen) != len(extracted) or len(indexed) != len(extracted):
        raise RuntimeError("frozen/extracted frame counts or keys invalid")
    if {r["sample_key"] for r in frozen} != set(indexed):
        raise RuntimeError("extracted keys differ from frozen keys")
    if output.exists():
        raise RuntimeError(f"refusing to overwrite output: {output}")
    if not BASELINE.is_file() or not MODEL.is_dir():
        raise RuntimeError("existing baseline or model missing")
    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    from PIL import Image

    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    if partial.exists():
        raise RuntimeError(f"refusing to overwrite partial output: {partial}")
    max_memory, failures = 0.0, 0
    with partial.open("w", encoding="utf-8") as stream:
        for index, item in enumerate(frozen, 1):
            image_meta = indexed[item["sample_key"]]
            image_path = Path(image_meta["image_path"])
            if file_sha256(image_path) != image_meta["image_sha256"]:
                raise RuntimeError(f"image hash mismatch: {item['sample_key']}")
            record = {"sample_key": item["sample_key"], "video_id": item["video_id"],
                      "youtube_id": item["youtube_id"], "image_sha256": image_meta["image_sha256"],
                      "model": str(MODEL), "baseline_entry_sha256": file_sha256(BASELINE)}
            model.reset_peak_memory()
            started_one = time.monotonic()
            try:
                with Image.open(image_path) as opened:
                    image = opened.convert("RGB")
                if image.size != (item["source_width"], item["source_height"]):
                    raise ValueError("image geometry changed")
                tw, th = item["target_ratio_wh"]
                raw = model.predict_focus(image, (tw, th),
                                          max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
                record["raw_output"] = raw
                center = baseline.parse_focus_norm(raw, image.width, image.height)
                if center is None:
                    record.update(output_valid=False, box_xywh=None, parse_error="no_valid_focus")
                else:
                    crop_w, crop_h = baseline.compute_crop_size(image.width, image.height, tw, th)
                    box = baseline.center_to_box(center[0], center[1], image.width,
                                                 image.height, crop_w, crop_h)
                    valid = bool(baseline.validate_box(box, image.width, image.height, tw, th))
                    record.update(output_valid=valid,
                                  box_xywh=[box[0], box[1], box[2], box[2] * th / tw] if valid else None,
                                  parse_error=None if valid else "invalid_crop_box")
            except Exception as exc:
                record.update(output_valid=False, box_xywh=None,
                              raw_output=record.get("raw_output", ""),
                              parse_error=f"{type(exc).__name__}: {exc}")
            record["seconds"] = round(time.monotonic() - started_one, 3)
            record["peak_memory_mib"] = round(model.peak_memory_mib(), 2)
            max_memory = max(max_memory, record["peak_memory_mib"])
            failures += not record["output_valid"]
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            if index % 20 == 0:
                print(f"spatial {index}/{len(frozen)} invalid={failures}", flush=True)
    partial.replace(output)
    report = {"status": "COMPLETED_WEAK_DEV_SPATIAL_BASELINE",
              "frozen_sha256": file_sha256(frozen_file),
              "extracted_sha256": file_sha256(extracted_file),
              "baseline_sha256": file_sha256(BASELINE),
              "output_sha256": file_sha256(output),
              "frames": len(frozen), "invalid": failures,
              "model_load_seconds": round(load_seconds, 2),
              "total_wall_seconds": round(time.monotonic() - started, 2),
              "peak_memory_mib": max_memory,
              "official_status": "NOT_OFFICIAL_SCORE"}
    (output.parent / "spatial_run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
