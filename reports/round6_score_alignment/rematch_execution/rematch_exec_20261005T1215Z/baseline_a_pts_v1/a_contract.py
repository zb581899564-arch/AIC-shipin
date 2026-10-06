"""Pure CPU contracts for the frozen 4B/P2-T2 rematch baseline.

No labels are accepted here. Every inference/parse failure blocks composition.
The legacy A prompt/parser has no legal-empty capability and keeps 1-5 segments.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent / "vendor"))
from p2j_core import anchor_frames, box_is_legal, group_shots, interpolate_box

ADAPTER_SHA256 = "c9bf3754a05a42d69ee8c4d11f56c41346d927094fd643863f0cb55626b8e6a0"
RECORD_KEYS = {"video_id", "source_group", "source_path", "source_sha256", "width",
               "height", "n_frames", "fps_num", "fps_den", "targetRatioWH",
               "scope_start_sec", "scope_end_sec"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, payload):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


def read_rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def write_rows(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def exact_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_manifest(manifest):
    if manifest.get("schema") != "aic_rematch_A_input_v1":
        raise ValueError("unrecognized manifest schema")
    kind = manifest.get("kind")
    expected = 8 if kind == "NONTEST_FROZEN8" else 426 if kind == "REMATCH426" else None
    contract = manifest.get("input_contract", {})
    if expected is None or manifest.get("expected_count") != expected:
        raise ValueError("input role/count not registered")
    if contract.get("status") != "APPROVED_METADATA_ONLY":
        raise ValueError("INPUT_ROLE_UNCONFIRMED: fail closed")
    for evidence in ("data_use_evidence", "target_ratio_evidence", "metadata_role_evidence"):
        if not isinstance(contract.get(evidence), str) or not contract[evidence].strip():
            raise ValueError("missing input use/role evidence")
    if kind == "REMATCH426" and contract.get("contest_jsonl_values_used") not in (False, "APPROVED_METADATA_ONLY"):
        raise ValueError("contest JSONL values are outside the approved clean-manifest input")
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != expected:
        raise ValueError("input record count mismatch")
    ids, paths = set(), set()
    roots = [PurePosixPath(x) for x in manifest.get("allowed_source_roots", [])]
    if not roots:
        raise ValueError("no allowed source roots")
    for r in records:
        if not isinstance(r, dict) or set(r) != RECORD_KEYS:
            raise ValueError("input record has unknown, label, or missing fields")
        vid = r["video_id"]
        if not isinstance(vid, str) or not vid or vid in ids:
            raise ValueError("duplicate/invalid video ID")
        ids.add(vid)
        if kind == "REMATCH426" and not vid.isdigit():
            raise ValueError("rematch video ID must come from numeric archive stem")
        path = PurePosixPath(r["source_path"])
        if (not path.is_absolute() or ".." in path.parts or path in paths or
                not any(root in path.parents for root in roots)):
            raise ValueError("invalid, duplicate, or unauthorized source path")
        paths.add(path)
        for field in ("width", "height", "n_frames", "fps_num", "fps_den"):
            if not exact_int(r[field]) or r[field] <= 0:
                raise ValueError("invalid source geometry/timebase")
        if (not isinstance(r["source_sha256"], str) or len(r["source_sha256"]) != 64 or
                any(c not in "0123456789abcdef" for c in r["source_sha256"])):
            raise ValueError("unfrozen media identity")
        ratio = r["targetRatioWH"]
        if ratio not in ([9, 16], [16, 9]) or any(not exact_int(x) for x in ratio):
            raise ValueError("ratio must be explicitly registered 9:16 or 16:9")
        start, end = r["scope_start_sec"], r["scope_end_sec"]
        duration = r["n_frames"] * r["fps_den"] / r["fps_num"]
        if not all(finite_number(x) for x in (start, end)) or not 0 <= start < end <= duration + 1e-6:
            raise ValueError("invalid temporal source scope")
        if kind == "REMATCH426" and (start != 0 or abs(end-duration) > 1e-6):
            raise ValueError("rematch inference must cover the complete source")
    if kind == "NONTEST_FROZEN8" and len({r["source_group"] for r in records}) != 8:
        raise ValueError("non-test regression must keep eight independent source groups")
    return {r["video_id"]: r for r in records}


def window_schedule(record, kind):
    start, end = record["scope_start_sec"], record["scope_end_sec"]
    if kind == "NONTEST_FROZEN8":
        # Same P2-J clips; engineering regression, no weak labels loaded.
        return [(float(start), float(end))]
    result = []
    while start < end - 1e-6:
        stop = min(start + 30.0, end)
        # Legacy P2-Final omitted <0.2s trailing windows. Explicitly recorded.
        if stop - start >= 0.2:
            result.append((float(start), float(stop)))
        start = stop
    if not result:
        raise ValueError("no eligible legacy A window; cannot convert to empty")
    return result


def select_frames(manifest, temporal):
    meta = validate_manifest(manifest)
    by_id = {r.get("video_id"): r for r in temporal}
    if len(by_id) != len(temporal) or set(by_id) != set(meta):
        raise ValueError("temporal row ID coverage mismatch")
    selected = []
    for vid in sorted(meta):
        m, row = meta[vid], by_id[vid]
        fps = m["fps_num"] / m["fps_den"]
        if (row.get("n_frames") != m["n_frames"] or row.get("targetRatioWH") != m["targetRatioWH"]
                or row.get("video_path") != m["source_path"] or
                not finite_number(row.get("fps")) or abs(row["fps"]-fps) > max(1e-6, fps*1e-6)):
            raise ValueError("temporal source identity/timebase/ratio mismatch")
        windows = row.get("windows", [])
        expected_windows = window_schedule(m, manifest["kind"])
        if len(windows) != len(expected_windows):
            raise ValueError("temporal window coverage mismatch")
        chosen = set()
        for w, (start, end) in zip(windows, expected_windows):
            if (w.get("status") != "MODEL_OK" or w.get("output_valid") is not True or
                    w.get("parse_errors") or w.get("parsed_segments") is None):
                raise ValueError("TEMPORAL_FAILURE_BLOCKS_CANDIDATE: no conversion to empty")
            if abs(w.get("start_sec", -1)-start) > 1e-6 or abs(w.get("end_sec", -1)-end) > 1e-6:
                raise ValueError("temporal window schedule changed")
            segs = w["parsed_segments"]
            if not isinstance(segs, list) or not 1 <= len(segs) <= 5:
                raise ValueError("legacy A requires 1-5 segments; legal-empty unverified")
            for s in segs:
                if (not isinstance(s, list) or len(s) != 2 or
                        not all(finite_number(x) for x in s) or not 0 <= s[0] < s[1] <= end-start+1e-6):
                    raise ValueError("invalid parsed temporal segment")
                if manifest["kind"] == "NONTEST_FROZEN8":
                    # Keep historical P2-J source-grid mapping exactly.
                    first = math.ceil(start*fps) + math.ceil(s[0]*fps)
                    last = min(math.ceil(start*fps)+math.ceil(s[1]*fps), math.ceil(end*fps))
                else:
                    first, last = math.ceil((start+s[0])*fps), math.ceil((start+s[1])*fps)
                first, last = max(0, first), min(m["n_frames"], last)
                if last <= first:
                    raise ValueError("segment has no legal mapped frames")
                chosen.update(range(first, last))
        if not chosen:
            raise ValueError("legacy A empty selection unsupported")
        for frame in sorted(chosen):
            selected.append({"video_id": vid, "source_frame": frame, "source_path": m["source_path"],
                             "source_width": m["width"], "source_height": m["height"],
                             "source_n_frames": m["n_frames"], "fps": fps,
                             "target_ratio_wh": m["targetRatioWH"]})
    return selected


def keyset(rows):
    keys = [(str(r["video_id"]), r["source_frame"]) for r in rows]
    if any(not exact_int(k[1]) for k in keys) or len(keys) != len(set(keys)):
        raise ValueError("duplicate/invalid frame identity")
    return set(keys)


def compose(manifest, selected, shots, requests, outputs):
    metadata = validate_manifest(manifest)
    chosen, shot_keys = keyset(selected), keyset(shots)
    request_keys, output_keys = keyset(requests), keyset(outputs)
    if chosen != shot_keys or request_keys != output_keys or not request_keys <= chosen:
        raise ValueError("spatial key coverage mismatch")
    request_map = {(r["video_id"], r["source_frame"]): r for r in requests}
    output_map = {(r["video_id"], r["source_frame"]): r for r in outputs}
    for k, o in output_map.items():
        r = request_map[k]
        m = metadata.get(k[0])
        if (o.get("status") != "MODEL_OK" or o.get("used_fallback") is not False or
                o.get("spatial_source") != "QWEN_ANCHOR_SAME_FRAME" or
                o.get("anchor_request_sha256") != r.get("anchor_request_sha256") or
                o.get("decoded_pixel_sha256") != r.get("expected_pixel_sha256") or m is None or
                not box_is_legal(o.get("box_xyw"), m["width"], m["height"], *m["targetRatioWH"])):
            raise ValueError("anchor failure or source identity mismatch blocks candidate")
    predictions, provenance = defaultdict(list), []
    scheduled_keys = set()
    for shot_id, shot in enumerate(group_shots(shots)):
        vid, frames = str(shot[0]["video_id"]), [r["source_frame"] for r in shot]
        if vid not in metadata:
            raise ValueError("unregistered source in shots")
        m = metadata[vid]
        scheduled = anchor_frames(frames, 8)
        scheduled_keys.update((vid, f) for f in scheduled)
        if not all((vid, f) in output_map for f in scheduled):
            raise ValueError("missing endpoint or intermediate anchor")
        anchors = {f: output_map[(vid, f)]["box_xyw"] for f in scheduled}
        for f in frames:
            box, source = interpolate_box(f, anchors)
            if not box_is_legal(box, m["width"], m["height"], *m["targetRatioWH"]):
                raise ValueError("illegal anchor/interpolated box")
            predictions[vid].append({"frame": f, "bboxes": box})
            provenance.append({"video_id": vid, "source_frame": f, "shot_id": shot_id,
                               "box_xyw": box, "legal": True, **source})
    if scheduled_keys != request_keys:
        raise ValueError("anchor schedule does not match frozen max-gap-8 rule")
    rows = [{"video_id": vid, "targetRatioWH": m["targetRatioWH"],
             "predictions": sorted(predictions[vid], key=lambda x: x["frame"])}
            for vid, m in sorted(metadata.items())]
    validate_predictions(manifest, rows, chosen, provenance)
    return rows, provenance


def validate_predictions(manifest, predictions, expected_keys, provenance):
    meta = validate_manifest(manifest)
    ids = [r.get("video_id") for r in predictions]
    if len(ids) != len(set(ids)) or set(ids) != set(meta):
        raise ValueError("candidate must contain every unique input video")
    actual = set()
    boxes = {}
    for row in predictions:
        vid, m = row["video_id"], meta[row["video_id"]]
        if set(row) != {"video_id", "targetRatioWH", "predictions"} or row["targetRatioWH"] != m["targetRatioWH"]:
            raise ValueError("official row contract mismatch")
        items = row["predictions"]
        if not isinstance(items, list) or not items:
            raise ValueError("legacy A empty output unsupported")
        previous = -1
        for item in items:
            f = item.get("frame")
            if (set(item) != {"frame", "bboxes"} or not exact_int(f) or
                    not previous < f < m["n_frames"] or
                    not box_is_legal(item["bboxes"], m["width"], m["height"], *m["targetRatioWH"])):
                raise ValueError("duplicate, unordered, out-of-range frame or illegal box")
            previous = f
            actual.add((vid, f))
            boxes[(vid, f)] = item["bboxes"]
    if actual != expected_keys or keyset(provenance) != actual:
        raise ValueError("selected/provenance/candidate frame coverage mismatch")
    for r in provenance:
        k = (r["video_id"], r["source_frame"])
        if (r.get("legal") is not True or r.get("box_xyw") != boxes[k] or
                r.get("spatial_source") not in {"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}):
            raise ValueError("provenance mismatch")
    return {"video_records": len(ids), "prediction_frames": len(actual), "issues": [],
            "official_status": "NOT_SCORED_NOT_UPLOADED", "legal_empty_supported": False,
            "weak_roi_inputs_used": 0, "old_test_boxes_used": 0, "silent_fallbacks": 0}


def package(path, output):
    if Path(output).exists():
        raise FileExistsError("refusing to overwrite candidate ZIP")
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(path, "predictions.jsonl")
    with zipfile.ZipFile(output) as z:
        if z.namelist() != ["predictions.jsonl"] or z.testzip() is not None or z.read("predictions.jsonl") != Path(path).read_bytes():
            raise ValueError("ZIP content/CRC/roundtrip mismatch")
    return {"zip_sha256": sha(output), "predictions_sha256": sha(path),
            "zip_bytes": Path(output).stat().st_size, "archive_names": ["predictions.jsonl"],
            "uploaded": False}
