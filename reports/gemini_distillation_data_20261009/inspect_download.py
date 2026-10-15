"""Local archive identity, gzip integrity and bounded extraction; no model calls."""
from pathlib import Path, PurePosixPath, PureWindowsPath
from datetime import datetime, timezone
import gzip
import hashlib
import json
import shutil
import tarfile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "downloads/tvsum50_ver_1_1.tgz"
OUT = ROOT / "data/tvsum"
EXPECTED_BYTES = 671779858


def save(name, value):
    with (ROOT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def member_path(member):
    raw = member.name
    if "\\" in raw or ":" in raw or "\x00" in raw:
        raise ValueError("Unsupported member path: " + repr(raw))
    posix = PurePosixPath(raw)
    if posix.is_absolute() or PureWindowsPath(raw).is_absolute() or ".." in posix.parts:
        raise ValueError("Outside extraction root: " + repr(raw))
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        prefix + str(index) for prefix in ("COM", "LPT") for index in range(1, 10)
    }
    if not posix.parts or any(part.rstrip(". ") != part or part.split(".")[0].upper() in reserved
                              or any(char in part for char in '<>"|?*') for part in posix.parts):
        raise ValueError("Invalid Windows member path: " + repr(raw))
    target = OUT.joinpath(*posix.parts).resolve()
    if not target.is_relative_to(OUT.resolve()):
        raise ValueError("Resolved path outside extraction root")
    return target


def main():
    if ARCHIVE.stat().st_size != EXPECTED_BYTES:
        raise ValueError("Archive byte count mismatch")
    if OUT.exists():
        raise FileExistsError("Extraction root already exists; preserve and inspect it")
    if not OUT.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Unexpected extraction root")
    archive_sha = sha(ARCHIVE)
    gzip_bytes = 0
    with gzip.open(ARCHIVE, "rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            gzip_bytes += len(block)
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = archive.getmembers()
        targets = []
        regular_names = set()
        for member in members:
            if not (member.isdir() or member.isfile()):
                raise ValueError("Links and nonregular entries rejected: " + member.name)
            target = member_path(member)
            key = str(target).casefold()
            if member.isfile():
                if key in regular_names:
                    raise ValueError("Duplicate or case-colliding file")
                regular_names.add(key)
            targets.append((member, target))
        save("archive_preflight.json", {
            "status": "PASS_SIZE_SHA_GZIP_CRC_AND_ALL_MEMBER_PATHS",
            "utc": datetime.now(timezone.utc).isoformat(),
            "archive_bytes": EXPECTED_BYTES,
            "archive_sha256": archive_sha,
            "publisher_checksum_available": False,
            "decompressed_tar_bytes": gzip_bytes,
            "member_count": len(members),
            "regular_file_count": len(regular_names),
            "regular_payload_bytes": sum(m.size for m in members if m.isfile()),
        })
        OUT.mkdir(parents=True)
        extracted = []
        for member, target in targets:
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("Missing regular file body")
            with source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination, 1 << 20)
            if target.stat().st_size != member.size:
                raise ValueError("Extracted byte count mismatch")
            extracted.append({"path": target.relative_to(ROOT).as_posix(),
                              "archive_member": member.name,
                              "bytes": member.size, "sha256": sha(target)})
    save("extraction_receipt.json", {
        "status": "PASS_ALL_REGULAR_FILES_EXTRACTED_WITHOUT_OVERWRITE",
        "utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": archive_sha,
        "extraction_root": str(OUT),
        "files": extracted,
        "file_count": len(extracted),
        "payload_bytes": sum(item["bytes"] for item in extracted),
        "no_model_calls": True,
        "no_remote_transfer": True,
    })
    print(json.dumps({"status": "PASS_LOCAL_DOWNLOAD_AND_EXTRACTION",
                      "sha256": archive_sha, "files": len(extracted),
                      "payload_bytes": sum(item["bytes"] for item in extracted)}))


if __name__ == "__main__":
    main()
