"""Replace one unsupported OpenCV color-transfer video with deterministic Decord frames."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import decord
import numpy as np

from p2j_core import read_jsonl, sha256_file, write_jsonl

HIST_THRESHOLD = 0.35
GRAY_MAD_THRESHOLD = 0.18


def descriptors(frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    small = cv2.resize(frame_bgr, (160, 90), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [32, 16], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return hist, cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)


def pixel_hash(frame: np.ndarray) -> str:
    return hashlib.sha256(memoryview(frame).cast("B")).hexdigest()


def decode_pass(path: str, frames: list[int]) -> dict[int, np.ndarray]:
    reader = decord.VideoReader(path)
    return {frame: reader[frame].asnumpy()[:, :, ::-1].copy() for frame in frames}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--shots-v1", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--shots-v2", type=Path, required=True)
    parser.add_argument("--frame-dir", type=Path, required=True)
    parser.add_argument("--frame-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if any(x.exists() for x in (args.shots_v2, args.frame_dir, args.frame_manifest, args.report)):
        raise FileExistsError("refusing to overwrite decoder repair artifacts")
    selected = read_jsonl(args.selected)
    old_shots = read_jsonl(args.shots_v1)
    target = sorted((x for x in selected if str(x["video_id"]) == args.video_id),
                    key=lambda x: int(x["source_frame"]))
    if not target:
        raise ValueError("decoder repair target has no selected frames")
    paths = {x["source_path"] for x in target}
    if len(paths) != 1:
        raise ValueError("decoder repair target maps to multiple files")
    path = next(iter(paths))
    frames = [int(x["source_frame"]) for x in target]
    passes = [decode_pass(path, frames) for _ in range(3)]
    stability_mismatches = [frame for frame in frames
                            if len({pixel_hash(values[frame]) for values in passes}) != 1]
    if stability_mismatches:
        raise RuntimeError("Decord pixel hashes are not deterministic")
    first = passes[0]
    repaired, previous = [], None
    for request in target:
        frame_number = int(request["source_frame"])
        frame = first[frame_number]
        if [frame.shape[1], frame.shape[0]] != [int(request["source_width"]),
                                                int(request["source_height"])]:
            raise RuntimeError("Decord geometry differs from frozen metadata")
        hist, gray = descriptors(frame)
        contiguous = previous is not None and previous["source_frame"] + 1 == frame_number
        reasons = []
        hist_distance = gray_mad = None
        if not contiguous:
            reasons.append("VIDEO_OR_SELECTION_DISCONTINUITY")
        else:
            hist_distance = float(cv2.compareHist(previous["hist"], hist,
                                                   cv2.HISTCMP_BHATTACHARYYA))
            gray_mad = float(np.mean(cv2.absdiff(previous["gray"], gray)) / 255.0)
            if hist_distance >= HIST_THRESHOLD:
                reasons.append("HSV_HIST_CUT")
            if gray_mad >= GRAY_MAD_THRESHOLD:
                reasons.append("GRAY_MAD_CUT")
        repaired.append({"video_id": args.video_id, "source_frame": frame_number,
                         "decoded_pixel_sha256": pixel_hash(frame),
                         "is_shot_start": bool(reasons), "boundary_reasons": reasons,
                         "hist_bhattacharyya": hist_distance, "gray_mad": gray_mad,
                         "decoder": "DECORD_RGB_TO_BGR_STABLE"})
        previous = {"source_frame": frame_number, "hist": hist, "gray": gray}
    combined = [x for x in old_shots if str(x["video_id"]) != args.video_id] + repaired
    combined.sort(key=lambda x: (str(x["video_id"]), int(x["source_frame"])))
    write_jsonl(args.shots_v2, combined)
    args.frame_dir.mkdir(parents=True, exist_ok=False)
    manifest = []
    for frame_number in frames:
        frame_path = args.frame_dir / f"{args.video_id}_{frame_number}.npy"
        np.save(frame_path, first[frame_number], allow_pickle=False)
        manifest.append({"video_id": args.video_id, "source_frame": frame_number,
                         "frame_npy": str(frame_path),
                         "frame_npy_sha256": sha256_file(frame_path),
                         "decoded_pixel_sha256": pixel_hash(first[frame_number])})
    write_jsonl(args.frame_manifest, manifest)
    report = {"status": "PASS_DETERMINISTIC_DECODER_REPAIR", "video_id": args.video_id,
              "decoder": "Decord RGB converted to BGR for the frozen OpenCV descriptor contract",
              "stability_passes": 3, "stability_mismatches": len(stability_mismatches),
              "selected_frames": len(frames), "old_shot_starts": sum(
                  bool(x["is_shot_start"]) for x in old_shots if str(x["video_id"]) == args.video_id),
              "new_shot_starts": sum(bool(x["is_shot_start"]) for x in repaired),
              "selected_sha256": sha256_file(args.selected),
              "shots_v1_sha256": sha256_file(args.shots_v1),
              "shots_v2_sha256": sha256_file(args.shots_v2),
              "frame_manifest_sha256": sha256_file(args.frame_manifest),
              "frame_bytes": sum(Path(x["frame_npy"]).stat().st_size for x in manifest)}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
