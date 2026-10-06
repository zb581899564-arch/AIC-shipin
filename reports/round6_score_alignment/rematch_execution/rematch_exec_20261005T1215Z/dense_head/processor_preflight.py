#!/usr/bin/env python3
"""Actual pinned processor test on CPU; loads no model weights and uses no CUDA."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time
import traceback

from dense_time import REVISION, query_text, resolve_queries
from probe_8b import encode_video, synthetic_video, verify_receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--model-receipt", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise RuntimeError("refusing nonempty preflight output")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    started = time.monotonic()
    report = {"status": "RUNNING_REAL_PROCESSOR_CPU_ONLY", "scope": "synthetic video; processor only; no weights/GPU/quality"}
    try:
        import torch
        import transformers
        from transformers import AutoProcessor
        if transformers.__version__ != "4.57.1":
            raise RuntimeError("processor entry point is reviewed against transformers4.57.1")
        report["environment"] = {"torch": torch.__version__, "transformers": transformers.__version__}
        report["receipt"] = verify_receipt(args.model_dir, args.model_receipt, metadata_only=True)
        processor = AutoProcessor.from_pretrained(str(args.model_dir), revision=REVISION,
                                                  local_files_only=True, min_pixels=224 * 224,
                                                  max_pixels=224 * 224)
        vocab_before = len(processor.tokenizer)
        text, video = query_text(4, 1.0, 4.0), synthetic_video(torch)
        encoded = encode_video(processor, torch, text, video)
        contract = resolve_queries(encoded, processor.tokenizer, 4, processor.video_token_id)
        decoded = processor.tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=False,
                                              clean_up_tokenization_spaces=False)
        timestamps = [float(x) for x in re.findall(r"<([0-9]+(?:\.[0-9]+)?) seconds>", decoded)]
        expected_pts = processor._calculate_timestamps(list(range(8)), 2.0, processor.video_processor.merge_size)
        if len(timestamps) != len(expected_pts) or any(abs(a - b) > 0.05000001 for a, b in zip(timestamps, expected_pts)):
            raise RuntimeError("processor timestamps disagree with supplied source frame indices/fps")
        grid = encoded["video_grid_thw"].tolist()
        if len(grid) != 1 or grid[0][0] != len(expected_pts):
            raise RuntimeError("video temporal grid differs from source-frame temporal merge")
        padded = encode_video(processor, torch, text, video, padding="max_length",
                             max_length=contract.sequence_length + 17)
        padded_contract = resolve_queries(padded, processor.tokenizer, 4, processor.video_token_id)
        original_start = int(torch.where(encoded["attention_mask"][0] != 0)[0][0])
        padded_start = int(torch.where(padded["attention_mask"][0] != 0)[0][0])
        padding_offset = padded_start - original_start
        expected_positions = tuple(p + padding_offset for p in contract.positions)
        if padded_contract.positions != expected_positions or int((padded["attention_mask"] == 0).sum()) != 17:
            raise RuntimeError("processor padding changed query positions or padding count")
        truncated = encode_video(processor, torch, text, video, truncation=True,
                                max_length=contract.positions[-1] - 1)
        rejected = False
        try:
            resolve_queries(truncated, processor.tokenizer, 4, processor.video_token_id)
        except ValueError:
            rejected = True
        if not rejected:
            raise RuntimeError("query truncation was not rejected")
        if len(processor.tokenizer) != vocab_before:
            raise RuntimeError("processor test modified tokenizer vocabulary")
        report.update(status="PASS_REAL_PROCESSOR_CPU_ONLY",
                      query_positions=contract.positions, marker_token_ids=contract.marker_token_ids,
                      query_markers=contract.markers, last_video_position=contract.last_video_position,
                      sequence_length=contract.sequence_length, video_grid_thw=grid,
                      video_token_count=int((encoded["input_ids"] == processor.video_token_id).sum()),
                      source_frame_indices=list(range(8)), source_frame_pts=[i / 2 for i in range(8)],
                      temporal_patch_expected_pts=expected_pts, processor_timestamp_text_values=timestamps,
                      timestamp_text_rounding_max_error=max(abs(a - b) for a, b in zip(timestamps, expected_pts)),
                      padded_query_positions=padded_contract.positions,
                      padding_side=processor.tokenizer.padding_side, padding_offset=padding_offset,
                      padding_query_correspondence_valid=True, truncated_query_rejected=True,
                      vocabulary_size_before_after=[vocab_before, len(processor.tokenizer)])
        (args.out_dir / "expanded_prompt.txt").write_text(decoded, encoding="utf-8")
    except Exception as exc:
        report["status"] = "FAIL_REAL_PROCESSOR_CPU_ONLY"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    report["wall_seconds"] = time.monotonic() - started
    output = args.out_dir / "processor_preflight_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(output),
                      "failure": report.get("failure", {}).get("message")}, ensure_ascii=False), flush=True)
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
