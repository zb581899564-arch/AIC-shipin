"""Portable receiving-end ZIP check. Copy only this file, delivery.json and ZIP.

Works on Windows with Python stdlib; no Linux private asset or model access.
It validates the delivered byte stream without unpacking or repacking it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def verify(manifest_path, zip_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema") != "AIC_FINAL_DELIVERY_V1":
        raise ValueError("Wrong Linux final delivery manifest")
    path = Path(zip_path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    if path.stat().st_size != manifest["zip_bytes"] or digest.hexdigest() != manifest["zip_sha256"]:
        raise ValueError("Transferred ZIP is not the Linux-approved byte stream")
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != ["predictions.jsonl"] or archive.testzip() is not None:
            raise ValueError("ZIP must contain exactly one CRC-valid predictions.jsonl")
        member = archive.read("predictions.jsonl")
    if hashlib.sha256(member).hexdigest() != manifest["member_sha256"]:
        raise ValueError("Transferred member SHA differs")
    rows = [json.loads(line) for line in member.splitlines() if line.strip()]
    if len(rows) != 426 or {row["video_id"] for row in rows} != {str(i) for i in range(426)}:
        raise ValueError("Transferred source denominator differs")
    return {"status": "TRANSFER_IDENTICAL", "candidate_id": manifest["candidate_id"],
            "zip_bytes": path.stat().st_size, "zip_sha256": digest.hexdigest(),
            "member_sha256": manifest["member_sha256"], "source_count": 426,
            "quality_validated": False, "website_submitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.zip), ensure_ascii=False))
