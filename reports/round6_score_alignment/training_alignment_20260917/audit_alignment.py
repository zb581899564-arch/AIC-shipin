"""Read-only audit of provided highlight labels against the prior source mapping.

Writes derived evidence only next to this script. Never reads competition test media.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
LABELS = HERE / "train.source_copy.jsonl"
MAPPING = HERE.parent.parent / "orarl_round4" / "evidence" / "mapping_rows.jsonl"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def issue(kind: str, i: int, detail: str):
    return {"kind": kind, "row_index": i, "detail": detail}


def main():
    rows = load_jsonl(LABELS)
    maps = load_jsonl(MAPPING)
    assert len(rows) == len(maps) == 987
    counts = Counter()
    problems = []
    candidates = []
    roi_widths = Counter()
    roi_heights = Counter()
    sample_strata = defaultdict(list)
    youtube_splits = defaultdict(set)
    youtube_rows = defaultdict(list)
    mapped_frame_out_of_range = []
    mapped_frame_duplicate_rows = []
    for i, (r, m) in enumerate(zip(rows, maps)):
        assert m["row_index"] == i and m["video_id"] == r["video_id"]
        assert m["source_vid"] == r["clip"]["source_vid"]
        c = r["clip"]
        segs = r.get("segments") or []
        rois = r.get("cropRois") or []
        kfs = r.get("crop_keyframes") or []
        counts["rows"] += 1
        counts["status_" + m["status"]] += 1
        counts["split_" + str(r.get("dataset_split"))] += 1
        counts["rows_with_segments"] += bool(segs)
        counts["rows_with_rois"] += bool(rois)
        counts["rows_with_keyframes"] += bool(kfs)
        counts["status_" + m["status"] + "_with_rois"] += bool(rois)
        counts["roi_entries"] += len(rois)
        counts["crop_keyframe_entries"] += len(kfs)
        if m["status"] == "usable":
            counts["usable_crop_keyframe_entries"] += len(kfs)
        counts["segment_entries"] += len(segs)
        counts["target_9_16"] += r.get("targetRatioWH") == [9.0, 16.0]
        if m.get("youtube_id"):
            youtube_splits[m["youtube_id"]].add(str(r.get("dataset_split")))
            youtube_rows[m["youtube_id"]].append(i)
        if r.get("video_path") or r.get("video_url"):
            counts["rows_with_video_locator"] += 1
        if not segs:
            problems.append(issue("no_segments", i, ""))
        for s in segs:
            for side in ("start", "end"):
                key = "source_" + side + "_sec"
                if abs(float(s[key]) - (float(c["start_sec"]) + float(s[side + "_sec"]))) > 1e-5:
                    problems.append(issue("source_offset_mismatch", i, str(s)))
            if s["end_frame"] < s["start_frame"] or s["end_sec"] < s["start_sec"]:
                problems.append(issue("reversed_segment", i, str(s)))
        roi_frames = []
        wh = m.get("source_probe") or {}
        width, height = wh.get("width"), wh.get("height")
        for item in rois:
            if not isinstance(item, list) or len(item) != 2 or not isinstance(item[1], list) or len(item[1]) != 4:
                problems.append(issue("roi_shape", i, repr(item)))
                continue
            f, (x, y, w, h) = item
            roi_frames.append(f)
            roi_widths[w] += 1
            roi_heights[h] += 1
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (f, x, y, w, h)):
                problems.append(issue("roi_type", i, repr(item)))
                continue
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                problems.append(issue("roi_nonpositive", i, repr(item)))
            if width and height and (x + w > width + 1e-6 or y + h > height + 1e-6):
                problems.append(issue("roi_out_of_source_bounds", i, repr(item)))
            if not any(s["start_frame"] <= f <= s["end_frame"] for s in segs):
                problems.append(issue("roi_outside_segments", i, repr(item)))
        if roi_frames:
            if roi_frames != sorted(roi_frames) or len(roi_frames) != len(set(roi_frames)):
                problems.append(issue("roi_nonmonotonic_or_duplicate", i, ""))
            expected = set().union(*(set(range(s["start_frame"], s["end_frame"] + 1)) for s in segs))
            if set(roi_frames) == expected:
                counts["roi_rows_exact_segment_frame_coverage"] += 1
            else:
                counts["roi_rows_partial_segment_frame_coverage"] += 1
        if m["status"] != "usable" or not rois or not m.get("source_path") or not m.get("clip_fps"):
            continue
        # Check the declared time conversion against the source's frame count.
        mapped_frames = []
        for frame, _ in rois:
            source_time = float(c["start_sec"]) + frame / float(m["clip_fps"])
            source_frame = round(source_time * float(m["source_probe"]["avg_fps"]))
            mapped_frames.append(source_frame)
            if source_frame < 0 or source_frame >= int(m["source_probe"]["nb_frames"]):
                mapped_frame_out_of_range.append({"row_index": i, "clip_frame": frame, "mapped_source_frame": source_frame})
        if len(set(mapped_frames)) != len(mapped_frames):
            mapped_frame_duplicate_rows.append(i)
        # Deterministic, stratified choice without looking at media or outcomes.
        start = float(c["start_sec"])
        stratum = "zero" if start < 1 else "middle" if start < 60 else "late"
        key = hashlib.sha256(r["video_id"].encode()).hexdigest()
        sample_strata[stratum].append((key, i, r, m))

    selected_youtube = set()
    for stratum in ("zero", "middle", "late"):
        for _, i, r, m in sorted(sample_strata[stratum]):
            if m.get("youtube_id") in selected_youtube:
                continue
            selected_youtube.add(m.get("youtube_id"))
            rois = r["cropRois"]
            positions = sorted(set([0, len(rois) // 2, len(rois) - 1]))
            items = []
            for pos in positions:
                frame, box = rois[pos]
                source_time = float(r["clip"]["start_sec"]) + frame / float(m["clip_fps"])
                source_frame = round(source_time * float(m["source_probe"]["avg_fps"]))
                items.append({"clip_frame": frame, "source_time_sec": source_time,
                              "source_frame_estimate": source_frame, "roi_xywh": box})
            candidates.append({"row_index": i, "stratum": stratum,
                               "video_id": r["video_id"], "youtube_id": m["youtube_id"],
                               "source_path": m["source_path"], "source_group": m["source_group"],
                               "clip_start_sec": r["clip"]["start_sec"],
                               "clip_fps": m["clip_fps"], "source_fps": m["source_probe"]["avg_fps"],
                               "source_width": m["source_probe"]["width"],
                               "source_height": m["source_probe"]["height"], "frames": items})
            if sum(x["stratum"] == stratum for x in candidates) >= 4:
                break

    report = {
        "input_label_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "mapping_rows_sha256": hashlib.sha256(MAPPING.read_bytes()).hexdigest(),
        "counts": dict(sorted(counts.items())),
        "roi_width_top": roi_widths.most_common(10),
        "roi_height_top": roi_heights.most_common(10),
        "mapped_source_frame_out_of_range_count": len(mapped_frame_out_of_range),
        "mapped_source_frame_out_of_range_first_30": mapped_frame_out_of_range[:30],
        "mapped_source_frame_duplicate_rows_count": len(mapped_frame_duplicate_rows),
        "mapped_source_frame_duplicate_rows_first_30": mapped_frame_duplicate_rows[:30],
        "youtube_groups": len(youtube_splits),
        "youtube_groups_crossing_original_train_val": sum(len(v) > 1 for v in youtube_splits.values()),
        "cross_split_youtube_groups": [
            {"youtube_id": key, "row_indices": youtube_rows[key]}
            for key in sorted(youtube_splits) if len(youtube_splits[key]) > 1
        ],
        "n_problems": len(problems), "problems_first_100": problems[:100],
        "selected": len(candidates), "selection_rule": "sha256(video_id) smallest per clip-start stratum; distinct youtube_id; 4 per stratum; first/mid/last ROI",
    }
    (HERE / "structural_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "sample_manifest.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["counts"], "n_problems": len(problems), "selected": len(candidates),
                      "roi_width_top": report["roi_width_top"][:3],
                      "source_frame_oob": report["mapped_source_frame_out_of_range_count"],
                      "source_frame_duplicate_rows": report["mapped_source_frame_duplicate_rows_count"],
                      "cross_split_youtube_groups": report["youtube_groups_crossing_original_train_val"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
