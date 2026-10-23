"""Acquire the small author archive once, adopting the accepted footer range."""
import hashlib
import json
import pathlib
import shutil
import time
import zipfile

from direct import ROOT, save
from upm_zip08 import SOURCES, fetch_range


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_adopted_tail(source):
    path = ROOT/"metadata"/"sportclip08_tail.bin"
    receipt = json.loads(path.with_suffix(".route.json").read_text())
    start = source["size"]-65557
    if (receipt["range"] != [start, source["size"]-1]
            or receipt["sha256"] != file_sha(path)
            or not receipt["curl"].startswith("138.4.32.2|206|")):
        raise ValueError("Original footer adoption failed")
    return start, path


def extract_verified(archive, expected):
    destination = ROOT/"media"/"sportclip10"
    destination.mkdir()
    records = []
    with zipfile.ZipFile(archive) as handle:
        if handle.namelist() != [item["name"] for item in expected]:
            raise ValueError("Archive differs from registered central directory")
        if handle.testzip() is not None:
            raise ValueError("Archive CRC failed")
        for member in handle.infolist():
            if member.is_dir():
                continue
            path = pathlib.PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or len(path.parts) != 2:
                raise ValueError("Unexpected extraction path")
            target = destination/path.name
            with handle.open(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            if target.stat().st_size != member.file_size:
                raise ValueError("Member size mismatch")
            records.append(dict(path=str(target), archive_member=member.filename,
                bytes=target.stat().st_size, sha256=file_sha(target), crc32=member.CRC))
    return records


def main():
    source = SOURCES["sportclip"]
    index = json.loads((ROOT/"sportclip08_index.json").read_text())
    tail_start, tail = validate_adopted_tail(source)
    required = source["size"]*2 + index["total_expanded"] + 16*1024*1024
    free = shutil.disk_usage(ROOT).free
    if free < required:
        raise RuntimeError(f"Insufficient for bounded stage: {free=} {required=}")
    save(ROOT/"sportclip_acquire10_registration.json", dict(
        source=source, purpose="Local noncommercial research benchmark and native alignment",
        permission_basis="Author expressly publishes videos+GT for benchmark use and asks citation",
        SPDX_license="not supplied; not claiming unrestricted redistribution rights",
        no_redistribution=True, no_training_or_GPU_in_this_stage=True,
        adopt_successful_tail=str(tail), new_payload_bytes=tail_start,
        extracted_bytes=index["total_expanded"], workspace_free_bytes=free,
        payload_route="Strict hostname TLS138.4.32.2 via physical eno2; explicit no proxy",
        no_network_configuration_change=True, no_whole_MATDAT_download=True))
    chunks, step = [], 4*1024*1024
    for number, start in enumerate(range(0, tail_start, step)):
        end = min(start+step-1, tail_start-1)
        name = f"sportclip10_chunk_{number:03d}.bin"
        fetch_range(source, start, end, name)
        chunks.append(ROOT/"metadata"/name)
        save(ROOT/f"sportclip10_chunk_{number:03d}_accepted.json", dict(
            path=str(chunks[-1]), range=[start,end], sha256=file_sha(chunks[-1])))
        print(json.dumps(dict(accepted=number+1, transferred=end+1,
            expected_new_payload=tail_start)), flush=True)
    media = ROOT/"media"
    media.mkdir(exist_ok=True)
    archive = media/"SportCLIP_author10.zip"
    with archive.open("xb") as output:
        for path in chunks+[tail]:
            with path.open("rb") as source_handle:
                shutil.copyfileobj(source_handle, output)
    if archive.stat().st_size != source["size"]:
        raise ValueError("Assembled archive size mismatch")
    records = extract_verified(archive, index["members"])
    save(ROOT/"sportclip_acquire10_completion.json", dict(
        state="COMPLETE", archive=str(archive), archive_bytes=archive.stat().st_size,
        archive_sha256=file_sha(archive), accepted_members=records,
        all_member_CRC_passed=True, new_payload_bytes=tail_start,
        accepted_tail_adopted=True, no_GPU=True, time=time.time()))
    print("COMPLETE",json.dumps(dict(members=len(records),bytes=archive.stat().st_size)),flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save(ROOT/"sportclip_acquire10_failure.json", dict(error=repr(error), time=time.time()))
        raise
