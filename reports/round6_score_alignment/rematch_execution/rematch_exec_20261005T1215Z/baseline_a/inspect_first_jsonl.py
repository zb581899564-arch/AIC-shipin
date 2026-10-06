#!/usr/bin/env python3
"""Bounded keys/types-only inspection of ONE paired rematch JSONL.

Never json.load a contest member. Stop BEFORE consuming a disallowed field's
value. No values, model input, media decode, extraction, or network operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ALLOWED = {
    "video_id": {"string", "number"},
    "targetRatioWH": {"array", "string"},
    "width": {"number"}, "height": {"number"},
    "n_frames": {"number"}, "fps_num": {"number"}, "fps_den": {"number"},
    "fps": {"number"}, "duration_sec": {"number"}, "video_path": {"string"},
}
SUSPECT = ("label", "segment", "frame", "box", "crop", "roi", "groundtruth",
           "annotation", "prediction", "highlight", "saliency", "score", "gt")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def recovered(name):
    try:
        return name.encode("cp437").decode("utf-8")
    except (UnicodeError, LookupError):
        return name


class Reader:
    def __init__(self, stream, limit=65536, single_line=False):
        self.stream, self.limit, self.count, self.saved = stream, limit, 0, None
        self.single_line = single_line

    def read(self):
        if self.saved is not None:
            x, self.saved = self.saved, None
            return x
        if self.count >= self.limit:
            raise ValueError("BOUNDED_INSPECTION_LIMIT")
        x = self.stream.read(1)
        self.count += len(x)
        if self.single_line and x in (b"\n", b"\r"):
            raise ValueError("MULTILINE_JSON_OBJECT_FORBIDDEN")
        return x

    def nonspace(self):
        x = self.read()
        while x and x in b" \t\r\n":
            x = self.read()
        return x

    def string(self, decode=False):
        data = bytearray(b'"') if decode else None
        escaped = False
        while True:
            x = self.read()
            if not x:
                raise ValueError("TRUNCATED_STRING")
            if data is not None:
                data.extend(x)
            if not escaped and x == b'"':
                return json.loads(data.decode("utf-8")) if decode else None
            escaped = not escaped and x == b"\\"

    def skip_value(self, first):
        # Allowed scalar metadata and target-ratio arrays only. Disallow objects
        # before reading their keys; metadata objects are outside this contract.
        if first == b'"':
            self.string()
            return
        if first == b"{":
            raise ValueError("NESTED_OBJECT_OUTSIDE_METADATA_CONTRACT")
        if first == b"[":
            first_item = self.nonspace()
            if first_item == b"]":
                return
            while True:
                if first_item in (b"[", b"{"):
                    raise ValueError("NESTED_CONTAINER_OUTSIDE_METADATA_CONTRACT")
                self.skip_value(first_item)
                delimiter = self.nonspace()
                if delimiter == b"]":
                    return
                if delimiter != b",":
                    raise ValueError("INVALID_ARRAY_DELIMITER")
                first_item = self.nonspace()
        else:
            if not first:
                raise ValueError("TRUNCATED_VALUE")
            x = self.read()
            while x and x not in b",]} \r\n\t":
                x = self.read()
            if x:
                self.saved = x


def inspect_keys(stream, limit=65536, allowed=None, single_line=False):
    allowed = ALLOWED if allowed is None else allowed
    r = Reader(stream, limit, single_line)
    fields, seen = [], set()
    if r.nonspace() != b"{":
        return {"status": "BLOCK_ROOT_NOT_OBJECT", "fields": [], "bytes_consumed": r.count}
    next_char = r.nonspace()
    while next_char != b"}":
        if next_char != b'"':
            raise ValueError("INVALID_FIELD_KEY")
        key = r.string(decode=True)
        if r.nonspace() != b":":
            raise ValueError("INVALID_FIELD_COLON")
        normalized = re.sub(r"[^a-z0-9]", "", key.lower())
        if key not in allowed:
            suspicious = any(token in normalized for token in SUSPECT)
            return {"status": "BLOCK_SUSPECTED_LABEL_KEY" if suspicious else "BLOCK_UNKNOWN_KEY",
                    "fields": fields + [{"key": key, "type": "NOT_READ"}],
                    "stopped_before_value": True, "bytes_consumed": r.count}
        if key in seen:
            return {"status": "BLOCK_DUPLICATE_METADATA_KEY", "fields": fields,
                    "stopped_before_value": True, "bytes_consumed": r.count}
        seen.add(key)
        first = r.nonspace()
        typ = ("string" if first == b'"' else "array" if first == b"[" else
               "object" if first == b"{" else "null" if first == b"n" else
               "boolean" if first in (b"t", b"f") else "number")
        fields.append({"key": key, "type": typ})
        if typ not in allowed[key]:
            return {"status": "BLOCK_METADATA_TYPE", "fields": fields,
                    "bytes_consumed": r.count}
        r.skip_value(first)
        next_char = r.nonspace()
        if next_char == b",":
            next_char = r.nonspace()
        elif next_char != b"}":
            raise ValueError("INVALID_OBJECT_DELIMITER")
    return {"status": "KEYS_TYPES_ONLY_METADATA_CANDIDATE_ROLE_UNCONFIRMED", "fields": fields,
            "bytes_consumed": r.count, "stopped_before_value": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-bytes", type=int, default=65536)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite inspection evidence")
    if not 1 <= args.max_bytes <= 65536:
        raise ValueError("inspection is bounded to at most 65536 bytes")
    if sha(args.zip) != args.expected_sha256:
        raise RuntimeError("archive identity mismatch")
    with zipfile.ZipFile(args.zip) as z:
        substantive = [i for i in z.infolist() if not i.is_dir()
                       and not recovered(i.filename).startswith("__MACOSX/")]
        videos = {PurePosixPath(recovered(i.filename)).stem for i in substantive
                  if i.filename.lower().endswith(".mp4")}
        members = [i for i in substantive if i.filename.lower().endswith(".jsonl")
                   and PurePosixPath(recovered(i.filename)).stem in videos]
        if len(videos) != 426 or len(members) != 426:
            raise ValueError("expected 426 unique paired video/JSONL names")
        members.sort(key=lambda i: (int(PurePosixPath(i.filename).stem)
                                   if PurePosixPath(i.filename).stem.isdigit() else 10**12,
                                   i.filename))
        member = members[0]
        with z.open(member) as stream:
            try:
                result = inspect_keys(stream, args.max_bytes)
            except (ValueError, UnicodeError, json.JSONDecodeError):
                result = {"status": "BLOCK_BOUNDED_OR_INVALID_METADATA", "fields": []}
    result.update(schema="aic_rematch_keys_types_only_v1", archive_sha256=args.expected_sha256,
                  member_name=recovered(member.filename), member_bytes=member.file_size,
                  members_content_opened=1, records_inspected=1, values_reported=0,
                  metadata_role_approved=False, inference_allowed=False,
                  note="Even a whitelist pass needs official role/use evidence. No expanded inspection.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"].startswith("KEYS_TYPES_ONLY") else 4


if __name__ == "__main__":
    raise SystemExit(main())
