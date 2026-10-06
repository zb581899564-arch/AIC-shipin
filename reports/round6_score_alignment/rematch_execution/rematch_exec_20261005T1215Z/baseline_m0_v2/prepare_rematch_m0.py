#!/usr/bin/env python3
"""Authorized rematch metadata-only intake. No model or media display.

Each JSONL is inspected for keys/types before ANY metadata values are parsed.
Only approved ratio and optional literal ID are accepted. Only MP4 members are
extracted into a new root, never JSONL/Apple metadata/scripts. No full PTS pass.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import zipfile
from fractions import Fraction
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True
from a_contract import sha, validate_manifest, write_json
from inspect_first_jsonl import inspect_keys, recovered

ARCHIVE_SHA = "8e4aa94f19c4e495952300ae19d37019fea4d2cbb3237120934c6b8d546c28e3"
METADATA_KEYS = {"targetRatioWH": {"array"}, "video_id": {"string"}}


def paired_members(infos, expected_count=426):
    videos, metadata = {}, {}
    for info in infos:
        display = recovered(info.filename)
        if info.is_dir() or display.startswith("__MACOSX/") or PurePosixPath(display).name == ".DS_Store":
            continue
        p = PurePosixPath(display)
        if p.is_absolute() or ".." in p.parts or "\\" in display:
            raise ValueError("UNSAFE_ARCHIVE_MEMBER_NAME")
        if p.suffix.lower() not in (".mp4", ".jsonl"):
            raise ValueError("UNEXPECTED_SUBSTANTIVE_ARCHIVE_MEMBER")
        if not re.fullmatch(r"[0-9]+", p.stem):
            raise ValueError("NON_NUMERIC_ARCHIVE_ID")
        mapping = videos if p.suffix.lower() == ".mp4" else metadata
        if p.stem in mapping:
            raise ValueError("DUPLICATE_ARCHIVE_ID")
        mapping[p.stem] = info
    if len(videos) != expected_count or set(videos) != set(metadata):
        raise ValueError("PAIRED_ARCHIVE_VIDEO_SET_MISMATCH")
    return videos, metadata


def read_approved_metadata(archive, info, stem):
    if not 1 <= info.file_size <= 65536:
        raise ValueError("BOUNDED_METADATA_MEMBER_SIZE")
    with archive.open(info) as stream:
        gate = inspect_keys(stream, 65536, METADATA_KEYS, single_line=True)
        if not gate["status"].startswith("KEYS_TYPES_ONLY"):
            # No suspect values parsed; error contains no field values.
            return None, gate
        # Detect any second record before reopening/parsing approved values.
        if stream.read(3) not in (b"", b"\n", b"\r\n"):
            return None, {**gate, "status": "BLOCK_TRAILING_OR_ADDITIONAL_JSONL_CONTENT"}
    # This second read is permitted only after ALL keys/types have passed.
    raw = archive.read(info)
    # Exactly one JSONL record. No second line, blank second line, or multiline object.
    lines = raw.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        return None, {**gate, "status": "BLOCK_NOT_EXACTLY_ONE_JSONL_RECORD"}
    try:
        data = json.loads(lines[0].decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None, {**gate, "status": "BLOCK_INVALID_METADATA_JSON"}
    if not isinstance(data, dict) or set(data) not in ({"targetRatioWH"}, {"targetRatioWH", "video_id"}):
        return None, {**gate, "status": "BLOCK_METADATA_FIELDS"}
    ratio = data["targetRatioWH"]
    if (not isinstance(ratio, list) or len(ratio) != 2 or
            any(type(x) is not int for x in ratio) or ratio not in ([16, 9], [9, 16])):
        return None, {**gate, "status": "BLOCK_OFFICIAL_RATIO_CONTRACT"}
    if "video_id" in data and (not isinstance(data["video_id"], str) or data["video_id"] != stem):
        return None, {**gate, "status": "BLOCK_LITERAL_STEM_ID_MISMATCH"}
    return {"video_id": stem, "targetRatioWH": ratio}, {**gate, "status": "PASS_APPROVED_METADATA_ONLY",
                                                             "values_reported": 0}


def probe(path, ffprobe):
    command = [str(ffprobe), "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,duration,time_base,start_time",
               "-of", "json", str(path)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    if len(streams) != 1:
        raise ValueError("INVALID_VIDEO_STREAM_METADATA")
    s = streams[0]
    fps = Fraction(s.get("avg_frame_rate", "0/1"))
    width, height = s.get("width"), s.get("height")
    if any(type(x) is not int or x <= 0 for x in (width, height)) or fps <= 0:
        raise ValueError("INVALID_VIDEO_GEOMETRY_OR_FPS")
    nb = s.get("nb_frames")
    mode = "CONTAINER_NB_FRAMES"
    if not isinstance(nb, str) or not nb.isdigit() or int(nb) <= 1:
        # Metadata-only count pass; no frame image/pixel output or PTS table.
        count = subprocess.run([str(ffprobe), "-v", "error", "-select_streams", "v:0", "-count_frames",
                                "-show_entries", "stream=nb_read_frames", "-of", "json", str(path)],
                               check=True, capture_output=True, text=True, timeout=600)
        nb = json.loads(count.stdout)["streams"][0].get("nb_read_frames")
        mode = "FFPROBE_COUNT_ONLY_NO_IMAGES_OR_PTS"
    if not isinstance(nb, str) or not nb.isdigit() or int(nb) <= 1:
        raise ValueError("UNCONFIRMED_FRAME_COUNT")
    n = int(nb)
    avg = fps
    try:
        nominal = Fraction(s.get("r_frame_rate", "0/1"))
    except (ValueError, ZeroDivisionError):
        nominal = None
    try:
        start = float(s.get("start_time", "0") or 0)
        start = start if math.isfinite(start) else None
    except (TypeError, ValueError):
        start = None
    flags = []
    if nominal != avg:
        flags.append("AVG_NOMINAL_FPS_DIFFER_PENDING_ACTUAL_PTS")
    if start is None:
        flags.append("UNKNOWN_START_PENDING_ACTUAL_PTS")
    elif abs(start) > float(1/fps)+1e-6:
        flags.append("NONZERO_START_PENDING_ACTUAL_PTS")
    return dict(width=width, height=height, n_frames=n, fps_num=fps.numerator, fps_den=fps.denominator,
                duration_sec=n/float(fps), ffprobe_time_base=s.get("time_base"), frame_count_mode=mode,
                source_start_sec=start, full_pts_verified=False, require_full_pts=True,
                nominal_fps_num=nominal.numerator if nominal is not None else None,
                nominal_fps_den=nominal.denominator if nominal is not None else None,
                metadata_timebase_status="PENDING_SEPARATE_PTS", timebase_flags=flags)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--approval", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, default=Path("/home/inspur/anaconda3/envs/Andy/bin/ffprobe"))
    args = ap.parse_args()
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    if (approval.get("status") != "APPROVED_METADATA_ONLY" or approval.get("archive_sha256") != ARCHIVE_SHA or
            approval.get("allowed_keys") != ["targetRatioWH", "video_id"] or
            approval.get("allow_jsonl_metadata_values") is not True or
            approval.get("allow_video_extraction") is not True or
            approval.get("allow_ffprobe_metadata") is not True):
        raise ValueError("INPUT_ROLE_APPROVAL_REQUIRED")
    if sha(args.zip) != ARCHIVE_SHA:
        raise RuntimeError("ARCHIVE_HASH_MISMATCH")
    root = args.output_root.resolve()
    if args.output_root.exists():
        raise FileExistsError("M0 needs a completely new root; preserve previous evidence")
    if sys.platform.startswith("linux") and not Path("/home/inspur/aic_video_work") in root.parents:
        raise ValueError("M0 outputs must stay under aic_video_work")
    root.mkdir(parents=True)
    media = root/"media"
    gates, records, probes, failure = [], [], [], None
    try:
        with zipfile.ZipFile(args.zip) as archive:
            videos, jsonls = paired_members(archive.infolist())
            allowed_metadata = {}
            for stem in sorted(videos, key=lambda x: (int(x), x)):
                data, gate = read_approved_metadata(archive, jsonls[stem], stem)
                gate.update(video_id=stem, member_name=recovered(jsonls[stem].filename))
                gates.append(gate)
                if data is None:
                    raise ValueError(gate["status"])
                allowed_metadata[stem] = data
            # No video extraction occurs until every metadata object passed.
            media.mkdir()
            for index, stem in enumerate(sorted(videos, key=lambda x: (int(x), x)), 1):
                target = media/(stem+".mp4")
                with archive.open(videos[stem]) as source, target.open("xb") as destination:
                    for chunk in iter(lambda: source.read(1 << 20), b""):
                        destination.write(chunk)
                if target.stat().st_size != videos[stem].file_size:
                    raise ValueError("EXTRACTED_VIDEO_BYTE_COUNT_MISMATCH")
                source_sha = sha(target)  # Full ZipExtFile read verifies member CRC.
                meta = probe(target, args.ffprobe)
                probes.append({"video_id": stem, "source_sha256": source_sha,
                               "member_crc32": f"{videos[stem].CRC:08x}", "bytes": target.stat().st_size, **meta})
                record = {k: meta[k] for k in ("width", "height", "n_frames", "fps_num", "fps_den")}
                record.update(video_id=stem, source_group="rematch:"+stem, source_path=str(target),
                              source_sha256=source_sha, targetRatioWH=allowed_metadata[stem]["targetRatioWH"],
                              scope_start_sec=0.0, scope_end_sec=meta["duration_sec"])
                records.append(record)
                print(f"M0 metadata {index}/426", flush=True)
        manifest = dict(schema="aic_rematch_A_input_v1", kind="REMATCH426", expected_count=426,
                        allowed_source_roots=[str(media)], records=records,
                        input_contract=dict(status="APPROVED_METADATA_ONLY",
                           data_use_evidence=str(args.approval)+" SHA256 "+sha(args.approval),
                           target_ratio_evidence=approval.get("official_target_ratio_evidence", "Controller approved current official targetRatioWH input contract"),
                           metadata_role_evidence="426 keys/types gates, exact one record each, only approved targetRatioWH/optional literal video_id",
                           contest_jsonl_values_used="APPROVED_METADATA_ONLY",
                           source_pts_status="PENDING_SEPARATE_FULL_PTS"))
        validate_manifest(manifest)
        write_json(root/"clean_manifest_426.json", manifest)
        state = "PASS_M0_METADATA_ONLY_NOT_FULL_PTS_NOT_INFERENCE"
    except Exception as exc:
        failure = type(exc).__name__
        failure_code = str(exc) if re.fullmatch(r"[A-Z][A-Z0-9_]+", str(exc)) else "UNCLASSIFIED_ERROR_NO_VALUES_REPORTED"
        # No stderr/object values/frames from failures are copied into reports.
        state = "BLOCK_M0_PRESERVE_PARTIAL_NO_INFERENCE"
        print(state, failure, failure_code, flush=True)
    write_json(root/"jsonl_keys_types_gate.json", {"status": state, "gates": gates, "metadata_values_reported": 0,
                                                 "jsonl_members_opened": len(gates), "jsonl_files_extracted": 0})
    write_json(root/"media_metadata.json", {"status": state, "records": probes, "full_pts_verified": False})
    result = {"status": state, "archive_sha256": ARCHIVE_SHA, "approval_sha256": sha(args.approval),
              "videos_extracted": len(probes), "clean_manifest_written": failure is None,
              "full_pts_verified": False, "GPU_used": False, "models_run": False,
              "media_images_displayed": False, "jsonl_files_extracted": 0, "failure_type": failure,
              "failure_code": failure_code if failure else None}
    if failure is None:
        result["manifest_sha256"] = sha(root/"clean_manifest_426.json")
    write_json(root/"m0_receipt.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if failure is None else 4


if __name__ == "__main__":
    raise SystemExit(main())
