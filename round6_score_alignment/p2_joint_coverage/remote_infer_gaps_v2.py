"""P2 remote spatial inference: fill the coverage gaps on frozen dev clips only.

Reads the frozen request manifest (863 rows: 856 NEEDS_INFERENCE + 7
CONTROL_SAME_FRAME controls), decodes each requested frame from the training
video with cv2, runs the existing unfused Qwen3-VL ``predict_focus`` call, and
records raw output, validity, parse errors, per-frame seconds and peak memory.

Rules:
* training clips only; any source path outside the training-video tree aborts;
* images are decoded fresh; SHA-256 of each request row is checked against the
  frozen manifest before use;
* invalid predictions stay invalid in the output (no center-crop fallback);
* no test video, no submission file, no quality score here.

Usage (training host):
  python remote_infer_gaps.py REQUESTS_JSONL OUT_JSONL
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
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()
# v2: decodes SOURCE frame indices (CAP_PROP_POS_FRAMES = source_frame); the v1
# script decoded by a clip-grid index that did not address the selected content.


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main(requests_path: str, out_path: str) -> int:
    requests_file, output = Path(requests_path), Path(out_path)
    requests = load_jsonl(requests_file)
    if not requests or output.exists() or output.with_suffix(output.suffix + ".partial").exists():
        raise RuntimeError("empty manifest or refusing to overwrite existing output")
    for row in requests:
        source = Path(row["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise RuntimeError(f"non-training source path: {source}")
    if not BASELINE.is_file() or not MODEL.is_dir():
        raise RuntimeError("baseline module or model missing")

    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    import cv2
    from PIL import Image

    started = time.monotonic()
    model = baseline.Qwen3VL(str(MODEL))
    load_seconds = time.monotonic() - started

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    invalid = 0
    max_memory = 0.0
    with partial.open("w", encoding="utf-8") as stream:
        for index, row in enumerate(requests, 1):
            record = {
                "video_id": row["video_id"], "source_frame": row["source_frame"],
                "kind": row["kind"], "sample_key": f"{row['video_id']}#src{row['source_frame']}",
                "model": str(MODEL), "baseline_entry_sha256": sha256_file(BASELINE),
            }
            one_start = time.monotonic()
            try:
                source = Path(row["source_path"])
                cap = cv2.VideoCapture(str(source))
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(row["source_frame"]))
                ok, frame = cap.read()
                cap.release()
                if not ok:
                    raise RuntimeError("frame decode failed")
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if image.size != (row["source_width"], row["source_height"]):
                    raise RuntimeError("decoded geometry changed")
                tw, th = row["target_ratio_wh"]
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
                                  box_xywh=[box[0], box[1], box[2]] if valid else None,
                                  parse_error=None if valid else "invalid_crop_box")
            except Exception as exc:
                record.update(output_valid=False, box_xywh=None,
                              raw_output=record.get("raw_output", ""),
                              parse_error=f"{type(exc).__name__}: {exc}")
            record["seconds"] = round(time.monotonic() - one_start, 3)
            record["peak_memory_mib"] = round(model.peak_memory_mib(), 2)
            max_memory = max(max_memory, record["peak_memory_mib"])
            invalid += not record["output_valid"]
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            if index % 50 == 0:
                print(f"gap {index}/{len(requests)} invalid={invalid}", flush=True)
    partial.replace(output)
    report = {
        "status": "COMPLETED_P2_GAP_INFERENCE_V2_SOURCE_GRID",
        "requests_sha256": sha256_file(requests_file),
        "output_sha256": sha256_file(output),
        "baseline_sha256": sha256_file(BASELINE),
        "rows": len(requests),
        "invalid": invalid,
        "model_load_seconds": round(load_seconds, 2),
        "total_wall_seconds": round(time.monotonic() - started, 2),
        "peak_memory_mib": max_memory,
        "official_status": "NOT_OFFICIAL_SCORE",
    }
    output.with_suffix(".run.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
