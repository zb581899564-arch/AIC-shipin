from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from reference_loader import load_jsonl


def phash_from_gray(gray: np.ndarray) -> int:
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    coeff = cv2.dct(small)[:8, :8]
    flat = coeff.flatten()
    threshold = float(np.median(flat[1:]))
    bits = flat > threshold
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def phash_image(path: Path) -> int:
    with Image.open(path) as im:
        gray = np.asarray(im.convert("L"))
    return phash_from_gray(gray)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--media-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    pilot = json.loads((args.root / "round6_score_alignment/p1b/pilot_manifest.json").read_text(encoding="utf-8"))
    weak_rows = [json.loads(x) for x in (args.root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    candidates = load_jsonl(args.manifest)
    candidate_hashes = {r["item_id"]: phash_image(args.media_root / r["media_rel_path"]) for r in candidates}
    aic_hashes: list[tuple[str, int]] = []
    decode_failures = []
    for sample in pilot.get("samples", []):
        media = Path(sample["media_abs_path"])
        cap = cv2.VideoCapture(str(media))
        if not cap.isOpened():
            decode_failures.append({"sample_id": sample["sample_id"], "error": "open_failed"})
            continue
        for probe in sample.get("verified_sample_frames", []):
            frame_index = int(probe["index"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok:
                decode_failures.append({"sample_id": sample["sample_id"], "frame": frame_index, "error": "decode_failed"})
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            aic_hashes.append((f"{sample['sample_id']}:{frame_index}", phash_from_gray(gray)))
        cap.release()
    distances = []
    for item_id, ch in candidate_hashes.items():
        for aic_id, ah in aic_hashes:
            distances.append({"candidate": item_id, "aic_probe": aic_id, "distance": hamming(ch, ah)})
    distances.sort(key=lambda x: x["distance"])
    gnmc_ids = {Path(r["original_filename"]).stem for r in candidates}
    aic_ids = {r["video_id"] for r in weak_rows} | {r["youtube_id"] for r in weak_rows}
    near = [r for r in distances if r["distance"] <= 6]
    result = {
        "schema": "p2r_bounded_leakage_audit_v1",
        "identifier_intersection": sorted(gnmc_ids & aic_ids),
        "candidate_images": len(candidates),
        "aic_non_test_groups_probed": len(pilot.get("samples", [])),
        "aic_frames_probed": len(aic_hashes),
        "pairwise_phash_comparisons": len(distances),
        "phash_algorithm": "32x32 grayscale DCT, top-left 8x8 median bits, Hamming distance",
        "near_duplicate_threshold": 6,
        "near_duplicate_matches": near,
        "minimum_distances": distances[:20],
        "decode_failures": decode_failures,
        "bounded_result": "NO_MATCH_IN_BOUNDED_PROBES" if not near and not decode_failures else "REVIEW_REQUIRED",
        "full_source_leakage": "UNKNOWN",
        "limitation": "GNMC does not publish per-image origin URLs in the archive, and only 96 frames from 8 AIC non-test pilot groups were compared; this cannot prove corpus-wide source isolation.",
    }
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["candidate_images", "aic_frames_probed", "pairwise_phash_comparisons", "bounded_result", "full_source_leakage"]}, ensure_ascii=False))
    return 0 if not decode_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
