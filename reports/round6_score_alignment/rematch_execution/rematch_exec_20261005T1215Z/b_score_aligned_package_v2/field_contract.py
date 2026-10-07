"""CPU spatial-field contracts independent of any temporal selection.

The registered field domain is supplied by the caller; this module reads no
media. Full-domain shot analysis and same-frame anchors are frozen once. Every
anchor and interpolated field frame is validated before a selection is taken.
The caller supplies a legacy_manifest projection for native-clock manifests.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import PurePosixPath

try:
    from . import package_contract as package
except ImportError:
    import package_contract as package
from p2j_core import anchor_frames, box_is_legal, group_shots, interpolate_box


FIELD_FRAME_KEYS = {"video_id", "source_frame", "source_path", "source_width",
                    "source_height", "source_n_frames", "fps", "target_ratio_wh"}
REQUEST_KEYS = FIELD_FRAME_KEYS | {"kind", "expected_pixel_sha256", "anchor_request_sha256"}
MAX_GAP = 8


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _keys(rows, name):
    _require(isinstance(rows, list), name + " must be a list, including legal empty")
    for row in rows:
        _require(isinstance(row, dict) and isinstance(row.get("video_id"), str) and bool(row["video_id"]) and
                 type(row.get("source_frame")) is int and row["source_frame"] >= 0,
                 name + " has an invalid source-frame identity")
    return package.keyset(rows)


def _frame(row):
    _require(set(row) == FIELD_FRAME_KEYS, "field frame contains missing or unregistered fields")
    for name in ("source_width", "source_height", "source_n_frames"):
        _require(type(row[name]) is int and row[name] > 0, "invalid field source geometry")
    _require(row["source_frame"] < row["source_n_frames"], "field source frame is out of range")
    ratio = row["target_ratio_wh"]
    _require(isinstance(ratio, list) and ratio in ([9, 16], [16, 9]) and all(type(x) is int for x in ratio),
             "field target ratio is not registered")
    fps = row["fps"]
    _require(type(fps) in (int, float) and math.isfinite(fps) and fps > 0, "invalid field source fps")
    path = row["source_path"]
    _require(isinstance(path, str) and PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts,
             "invalid field source path")


def _shots(rows, metadata=None):
    keys = _keys(rows, "field shots")
    for row in rows:
        _require(type(row.get("is_shot_start")) is bool, "field shot start must be an explicit bool")
        _require(_sha(row.get("decoded_pixel_sha256")), "field shot pixel SHA256 is missing or invalid")
        if metadata is not None:
            m = metadata.get(row["video_id"])
            _require(m is not None and row["source_frame"] < m["n_frames"], "unregistered or out-of-range field shot")
    return keys


def _request_sha(row):
    # Identical canonical request identity to vendor/build_anchors.py.
    body = {key: row[key] for key in sorted(row) if key != "anchor_request_sha256"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _same_source(row, metadata):
    _frame(row)
    m = metadata.get(row["video_id"])
    _require(m is not None and row["source_path"] == m["source_path"] and
             row["source_width"] == m["width"] and row["source_height"] == m["height"] and
             row["source_n_frames"] == m["n_frames"] and row["target_ratio_wh"] == m["targetRatioWH"] and
             abs(row["fps"] - m["fps_num"] / m["fps_den"]) <= 1e-6,
             "field/selected source identity does not match registered manifest")


def build_field_requests(field_frames, field_shots, max_gap=8):
    """Freeze same-frame requests from the full registered field, never selected.

    Frame rows use the historical eight source fields. Shot rows use the
    sequential decoder's pixel SHA256 and explicit ``is_shot_start`` flag.
    Empty domains produce an empty request list without a call-reduction divide.
    """
    _require(type(max_gap) is int and max_gap == MAX_GAP, "the registered field anchor max gap is 8")
    frame_keys = _keys(field_frames, "field frames")
    shot_keys = _shots(field_shots)
    _require(frame_keys == shot_keys, "field shot keys must exactly cover field frame keys")
    frames = {(row["video_id"], row["source_frame"]): row for row in field_frames}
    identities = {}
    for row in field_frames:
        _frame(row)
        identity = {key: row[key] for key in FIELD_FRAME_KEYS - {"source_frame"}}
        previous = identities.setdefault(row["video_id"], identity)
        _require(identity == previous, "field source identity changes within a video")
    shot_map = {(row["video_id"], row["source_frame"]): row for row in field_shots}
    anchors = set()
    for shot in group_shots(field_shots):
        vid = shot[0]["video_id"]
        anchors.update((vid, f) for f in anchor_frames([row["source_frame"] for row in shot], MAX_GAP))
    result = []
    for key in sorted(anchors):
        source = dict(frames[key])
        source["target_ratio_wh"] = list(source["target_ratio_wh"])
        source["kind"] = "QWEN_ANCHOR_SAME_FRAME"
        source["expected_pixel_sha256"] = shot_map[key]["decoded_pixel_sha256"]
        source["anchor_request_sha256"] = _request_sha(source)
        result.append(source)
    return result


def compose_from_field(manifest, selected, field_shots, requests, outputs):
    """Validate/interpolate the entire frozen field, then take selected frames.

    A failure on an unselected field anchor still blocks composition. Predictions
    contain every registered video, including videos with an empty selection;
    provenance contains exactly selected frames and fixed field shot identities.
    """
    metadata = package.validate_manifest(manifest)
    chosen = _keys(selected, "selected")
    field_keys = _shots(field_shots, metadata)
    request_keys, output_keys = _keys(requests, "field requests"), _keys(outputs, "field outputs")
    _require(chosen <= field_keys, "selected frame lies outside the registered field")
    _require(request_keys == output_keys, "field request/output key coverage mismatch")
    for row in selected:
        _same_source(row, metadata)
    shot_map = {(row["video_id"], row["source_frame"]): row for row in field_shots}
    grouped = group_shots(field_shots)
    scheduled_keys = {
        (shot[0]["video_id"], frame)
        for shot in grouped
        for frame in anchor_frames([row["source_frame"] for row in shot], MAX_GAP)
    }
    _require(request_keys == scheduled_keys, "field anchor schedule lacks endpoint/intermediate or differs from actual-shot max-gap-8 rule")
    request_map = {(row["video_id"], row["source_frame"]): row for row in requests}
    output_map = {(row["video_id"], row["source_frame"]): row for row in outputs}
    for key, request in request_map.items():
        _require(set(request) == REQUEST_KEYS, "field request contains missing or unregistered fields")
        _same_source({name: request[name] for name in FIELD_FRAME_KEYS}, metadata)
        _require(request["kind"] == "QWEN_ANCHOR_SAME_FRAME" and
                 _sha(request["expected_pixel_sha256"]) and
                 request["expected_pixel_sha256"] == shot_map[key]["decoded_pixel_sha256"] and
                 _sha(request["anchor_request_sha256"]) and
                 request["anchor_request_sha256"] == _request_sha(request),
                 "field request SHA256 or same-frame pixel identity mismatch")
        output, m = output_map[key], metadata[key[0]]
        _require(output.get("status") == "MODEL_OK" and output.get("used_fallback") is False and
                 output.get("spatial_source") == "QWEN_ANCHOR_SAME_FRAME" and
                 output.get("anchor_request_sha256") == request["anchor_request_sha256"] and
                 output.get("decoded_pixel_sha256") == request["expected_pixel_sha256"] and
                 box_is_legal(output.get("box_xyw"), m["width"], m["height"], *m["targetRatioWH"]),
                 "field anchor failure, illegal box or source identity mismatch")
    full_predictions = {vid: [] for vid in metadata}
    full_provenance = []
    for shot_id, shot in enumerate(grouped):
        vid = shot[0]["video_id"]
        m = metadata[vid]
        frames = [row["source_frame"] for row in shot]
        anchors = {f: output_map[(vid, f)]["box_xyw"] for f in anchor_frames(frames, MAX_GAP)}
        for frame in frames:
            box, source = interpolate_box(frame, anchors)
            _require(box_is_legal(box, m["width"], m["height"], *m["targetRatioWH"]), "illegal interpolated field box")
            full_predictions[vid].append({"frame": frame, "bboxes": box})
            full_provenance.append({"video_id": vid, "source_frame": frame, "shot_id": shot_id,
                                    "box_xyw": box, "legal": True, **source})
    full_rows = [{"video_id": vid, "targetRatioWH": m["targetRatioWH"],
                  "predictions": sorted(full_predictions[vid], key=lambda item: item["frame"])}
                 for vid, m in sorted(metadata.items())]
    package.validate_predictions(manifest, full_rows, field_keys, full_provenance)
    rows = [{"video_id": row["video_id"], "targetRatioWH": row["targetRatioWH"],
             "predictions": [item for item in row["predictions"] if (row["video_id"], item["frame"]) in chosen]}
            for row in full_rows]
    provenance = [row for row in full_provenance if (row["video_id"], row["source_frame"]) in chosen]
    package.validate_predictions(manifest, rows, chosen, provenance)
    return rows, provenance
