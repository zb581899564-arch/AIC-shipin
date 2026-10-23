"""Explicit remaining-byte recovery after acquire10's network timeout."""
import hashlib
import json
import os
import shutil
import subprocess
import time

from direct import ROOT, save
from upm_acquire10 import extract_verified, file_sha, validate_adopted_tail
from upm_zip08 import SOURCES, HOST, IP


def adopt_fragment(name, start, expected_end):
    path = ROOT/"metadata"/name
    receipt = json.loads(path.with_suffix(".route.json").read_text())
    headers = path.with_suffix(".headers").read_text().lower()
    expected_range = f"bytes {start}-{expected_end}/{SOURCES['sportclip']['size']}"
    if (receipt["range"] != [start, expected_end]
            or not receipt["curl"].startswith(IP+"|206|")
            or receipt["sha256"] != file_sha(path)
            or receipt["bytes"] != path.stat().st_size
            or expected_range not in headers or not path.stat().st_size):
        raise ValueError("Existing fragment identity failed")
    return path, start+path.stat().st_size


def remaining_fragment(source, start, end, number):
    path = ROOT/"metadata"/f"sportclip11_fragment_{number:03d}.bin"
    if path.exists():
        raise FileExistsError(path)
    command = ["curl", "--noproxy", "*", "--ipv4", "--resolve", f"{HOST}:443:{IP}",
        "--connect-timeout", "6", "--max-time", "45", "--max-filesize", str(end-start+1),
        "--silent", "--show-error", "--header", "If-Match: "+source["etag"],
        "--range", f"{start}-{end}", "--dump-header", str(path.with_suffix(".headers")),
        "--output", str(path), "--write-out", "%{remote_ip}|%{http_code}|%{url_effective}",
        source["url"]]
    result = subprocess.run(command, capture_output=True, text=True, timeout=50)
    headers = path.with_suffix(".headers").read_text(errors="replace")
    route = subprocess.run(["ip", "route", "get", IP], capture_output=True, text=True).stdout
    length = path.stat().st_size if path.exists() else 0
    receipt = dict(range=[start,end], bytes=length, exit_code=result.returncode,
        curl=result.stdout, stderr=result.stderr, route=route,
        sha256=file_sha(path) if length else None, strict_TLS=True, no_proxy=True,
        partial_adoption_requires_final_archive_and_member_CRC=True)
    save(path.with_suffix(".route.json"), receipt)
    valid = (result.returncode in (0,28) and result.stdout.startswith(IP+"|206|")
        and " dev eno2 " in " "+route+" " and 0 < length <= end-start+1
        and f"bytes {start}-{end}/{source['size']}" in headers.lower())
    if not valid:
        return None, start
    return path, start+length


def main():
    if not (ROOT/"sportclip_acquire10_failure.json").exists():
        raise ValueError("Recovery requires actual original failure")
    source = SOURCES["sportclip"]
    tail_start, tail = validate_adopted_tail(source)
    first, position = adopt_fragment("sportclip10_chunk_000.bin",0,4194303)
    partial, position = adopt_fragment("sportclip10_chunk_001.bin",position,8388607)
    paths = [first,partial]
    save(ROOT/"sportclip_remaining11_registration.json", dict(
        actual_previous_failure="sportclip_acquire10_failure.json",
        adopted_bytes=position, previous_partial_kept=True, tail_adopted=str(tail),
        source=source, new_payload_bytes=tail_start-position,
        per_request_bytes=1048576, wall_seconds=1200, zero_progress_limit=3,
        no_repeat_successful_bytes=True, same_research_scope=True, no_GPU=True))
    started, number, zero = time.monotonic(), 0, 0
    while position < tail_start:
        if time.monotonic()-started > 1200 or zero >= 3:
            raise TimeoutError("Bounded remaining recovery exhausted")
        end = min(position+1048576-1, tail_start-1)
        path, next_position = remaining_fragment(source,position,end,number)
        number += 1
        if path is None:
            zero += 1
            continue
        zero = 0
        save(ROOT/f"sportclip11_fragment_{number-1:03d}_accepted.json",dict(
            path=str(path), range=[position,next_position-1],sha256=file_sha(path)))
        paths.append(path)
        position = next_position
        print(json.dumps(dict(contiguous_accepted_bytes=position,
            expected_prefix_bytes=tail_start,remaining=tail_start-position)),flush=True)
    media = ROOT/"media"
    media.mkdir(exist_ok=True)
    archive = media/"SportCLIP_author11.zip"
    with archive.open("xb") as output:
        for path in paths+[tail]:
            with path.open("rb") as source_handle:
                shutil.copyfileobj(source_handle,output)
    index=json.loads((ROOT/"sportclip08_index.json").read_text())
    records=extract_verified(archive,index["members"])
    save(ROOT/"sportclip_remaining11_completion.json",dict(
        state="COMPLETE",archive=str(archive),archive_bytes=archive.stat().st_size,
        archive_sha256=file_sha(archive),accepted_members=records,
        all_member_CRC_passed=True, original_failure_preserved=True,
        no_successful_range_repeated=True,time=time.time()))
    print("COMPLETE",len(records),flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save(ROOT/"sportclip_remaining11_failure.json",dict(error=repr(error),time=time.time()))
        raise
