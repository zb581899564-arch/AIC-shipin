#!/usr/bin/env python3
"""Finalize an existing complete M0 into new evidence without copying media.

Expected prior failure: old deployed contract rejected approved ratio metadata
after all 426 gates/extractions/probes completed. Bind its report by SHA and
recheck every source byte hash and every contest keys/type gate. No ffprobe,
PTS scan, pixel display, model, GPU, file mutation outside the new evidence root.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import sha, validate_manifest, write_json
from prepare_rematch_m0 import ARCHIVE_SHA, paired_members, read_approved_metadata

REPORT_KEYS = {"status", "records", "full_pts_verified"}
REQUIRED_METADATA_KEYS = {"video_id", "source_sha256", "member_crc32", "bytes", "width", "height",
                          "n_frames", "fps_num", "fps_den", "duration_sec", "full_pts_verified"}
ALLOWED_METADATA_KEYS = REQUIRED_METADATA_KEYS | {
    "ffprobe_time_base", "frame_count_mode", "source_start_sec", "nominal_fps_num", "nominal_fps_den",
    "metadata_timebase_status", "timebase_flags", "require_full_pts"}


def validate_existing_metadata(payload):
    if not isinstance(payload, dict) or set(payload) != REPORT_KEYS or payload["full_pts_verified"] is not False:
        raise ValueError("PRIOR_METADATA_REPORT_CONTRACT")
    rows = payload["records"]
    if not isinstance(rows, list) or len(rows) != 426:
        raise ValueError("PRIOR_METADATA_REPORT_NOT_COMPLETE_426")
    by_id = {}
    for row in rows:
        if (not isinstance(row, dict) or not REQUIRED_METADATA_KEYS <= set(row) or
                not set(row) <= ALLOWED_METADATA_KEYS):
            raise ValueError("PRIOR_METADATA_FIELD_OUTSIDE_WHITELIST")
        vid = row["video_id"]
        if not isinstance(vid, str) or not re.fullmatch(r"[0-9]+", vid) or vid in by_id:
            raise ValueError("PRIOR_METADATA_ID_DUPLICATE_OR_NOT_LITERAL_STEM")
        for key in ("bytes", "width", "height", "n_frames", "fps_num", "fps_den"):
            if type(row[key]) is not int or row[key] <= 0:
                raise ValueError("PRIOR_METADATA_GEOMETRY_TIMEBASE_OR_SIZE")
        expected_duration = row["n_frames"]*row["fps_den"]/row["fps_num"]
        if (type(row["duration_sec"]) not in (int, float) or
                not math.isfinite(row["duration_sec"]) or abs(row["duration_sec"]-expected_duration) > 1e-6):
            raise ValueError("PRIOR_METADATA_DURATION_INCONSISTENT")
        if row["full_pts_verified"] is not False:
            raise ValueError("PRIOR_PTS_STATUS_MUST_REMAIN_UNVERIFIED")
        if not isinstance(row["source_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]):
            raise ValueError("PRIOR_SOURCE_HASH_INVALID")
        if not isinstance(row["member_crc32"], str) or not re.fullmatch(r"[0-9a-f]{8}", row["member_crc32"]):
            raise ValueError("PRIOR_CRC_INVALID")
        by_id[vid] = row
    return by_id


def validate_approval(payload):
    if (payload.get("status") != "APPROVED_METADATA_ONLY" or payload.get("archive_sha256") != ARCHIVE_SHA or
            payload.get("allowed_keys") != ["targetRatioWH", "video_id"] or
            payload.get("allow_jsonl_metadata_values") is not True or
            payload.get("allow_video_extraction") is not True or
            payload.get("allow_ffprobe_metadata") is not True):
        raise ValueError("APPROVED_METADATA_ROLE_EVIDENCE_REQUIRED")


def validate_source_file(media_root, vid, row, info):
    # Use numeric literal IDs only; do not discover paths from unchecked metadata.
    target = media_root/(vid+".mp4")
    if target.is_symlink() or not target.is_file() or target.resolve().parent != media_root:
        raise ValueError("PRIOR_MEDIA_MISSING_OR_OUTSIDE_REGISTERED_REAL_ROOT")
    if target.stat().st_size != row["bytes"] or row["bytes"] != info.file_size:
        raise ValueError("PRIOR_MEDIA_SIZE_ARCHIVE_MISMATCH")
    if row["member_crc32"] != f"{info.CRC:08x}":
        raise ValueError("PRIOR_MEDIA_CRC_ARCHIVE_MISMATCH")
    if sha(target) != row["source_sha256"]:
        raise ValueError("PRIOR_MEDIA_BYTE_HASH_MISMATCH")
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--approval", type=Path, required=True)
    ap.add_argument("--media-metadata", type=Path, required=True)
    ap.add_argument("--expected-media-metadata-sha256", required=True)
    ap.add_argument("--existing-media-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    args = ap.parse_args()
    if sha(args.media_metadata) != args.expected_media_metadata_sha256:
        raise ValueError("PRIOR_METADATA_REPORT_HASH_CHANGED")
    prior = json.loads(args.media_metadata.read_text(encoding="utf-8"))
    by_id = validate_existing_metadata(prior)
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    validate_approval(approval)
    if sha(args.zip) != ARCHIVE_SHA:
        raise ValueError("ORIGINAL_ARCHIVE_IDENTITY_MISMATCH")
    media = args.existing_media_root.resolve(strict=True)
    root = args.output_root.resolve()
    if args.existing_media_root.is_symlink() or not media.is_dir():
        raise ValueError("PRIOR_MEDIA_ROOT_MUST_BE_REAL_DIRECTORY")
    if args.output_root.exists():
        raise FileExistsError("preserve prior evidence; output root must be entirely new")
    if media == root or media in root.parents or root in media.parents:
        raise ValueError("NEW_EVIDENCE_ROOT_MUST_BE_SEPARATE_FROM_PRIOR_MEDIA")
    if sys.platform.startswith("linux"):
        allowed = Path("/home/inspur/aic_video_work")
        if allowed not in root.parents or allowed not in media.parents:
            raise ValueError("M0_FINALIZATION_MUST_REMAIN_UNDER_AIC_VIDEO_WORK")
    root.mkdir(parents=True)
    gates, verification, records, failure_code = [], [], [], None
    try:
        with zipfile.ZipFile(args.zip) as archive:
            videos, jsonls = paired_members(archive.infolist())
            if set(videos) != set(by_id):
                raise ValueError("PRIOR_METADATA_ARCHIVE_ID_SET_MISMATCH")
            approved_metadata = {}
            # Finish all 426 keys/type gates before generating a clean manifest.
            for vid in sorted(videos, key=lambda x: (int(x), x)):
                data, gate = read_approved_metadata(archive, jsonls[vid], vid)
                gate.update(video_id=vid)
                gates.append(gate)
                if data is None:
                    raise ValueError(gate["status"])
                approved_metadata[vid] = data
            for index, vid in enumerate(sorted(videos, key=lambda x: (int(x), x)), 1):
                row = by_id[vid]
                target = validate_source_file(media, vid, row, videos[vid])
                clean = {key: row[key] for key in ("width", "height", "n_frames", "fps_num", "fps_den")}
                clean.update(video_id=vid, source_group="rematch:"+vid, source_path=str(target),
                             source_sha256=row["source_sha256"], targetRatioWH=approved_metadata[vid]["targetRatioWH"],
                             scope_start_sec=0.0, scope_end_sec=row["duration_sec"])
                records.append(clean)
                verification.append({"video_id": vid, "source_sha256": row["source_sha256"],
                                     "bytes": row["bytes"], "member_crc32": row["member_crc32"],
                                     "hash_matches_prior": True, "archive_size_crc_matches_prior": True})
                print(f"Existing M0 verified {index}/426", flush=True)
        contract = dict(status="APPROVED_METADATA_ONLY",
                        data_use_evidence=str(args.approval)+" SHA256 "+sha(args.approval),
                        target_ratio_evidence=approval.get("official_target_ratio_evidence", "Controller approved official targetRatioWH algorithm input"),
                        metadata_role_evidence="All 426 approved keys/type gates reverified; optional ID equals literal archive stem; one record only",
                        contest_jsonl_values_used="APPROVED_METADATA_ONLY", source_pts_status="PENDING_SEPARATE_FULL_PTS",
                        prior_media_metadata_evidence=str(args.media_metadata)+" SHA256 "+args.expected_media_metadata_sha256)
        manifest = dict(schema="aic_rematch_A_input_v1", kind="REMATCH426", expected_count=426,
                        allowed_source_roots=[str(media)], input_contract=contract, records=records)
        validate_manifest(manifest)
        write_json(root/"clean_manifest_426.json", manifest)
        status = "PASS_EXISTING_M0_FINALIZED_METADATA_ONLY_PTS_PENDING"
    except Exception as exc:
        failure_code = str(exc) if re.fullmatch(r"[A-Z][A-Z0-9_]+", str(exc)) else type(exc).__name__
        status = "BLOCK_EXISTING_M0_FINALIZATION_PRESERVE_PRIOR"
    write_json(root/"jsonl_keys_types_reverification.json", {"status": status, "gates": gates,
                                                            "values_reported": 0, "jsonl_files_extracted": 0})
    write_json(root/"existing_media_verification.json", {"status": status, "records": verification})
    receipt = dict(status=status, archive_sha256=ARCHIVE_SHA, approval_sha256=sha(args.approval),
                   prior_media_metadata_sha256=args.expected_media_metadata_sha256,
                   prior_media_metadata_status=prior["status"], prior_media_root=str(media),
                   verified_media_count=len(verification), jsonl_gates_checked=len(gates),
                   prior_reports_modified=False, existing_media_modified=False, videos_copied=0,
                   media_images_exported_or_displayed=False, full_pts_verified=False,
                   models_run=False, gpu_used=False, inference_allowed=False, failure_code=failure_code)
    if failure_code is None:
        receipt["clean_manifest_sha256"] = sha(root/"clean_manifest_426.json")
    write_json(root/"repair_receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if failure_code is None else 4


if __name__ == "__main__":
    raise SystemExit(main())
