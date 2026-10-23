"""Read bounded original-author ZIP metadata without a whole-archive fallback."""
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import time

from direct import ROOT, save

HOST = "www.gti.ssr.upm.es"
IP = "138.4.32.2"
SOURCES = {
    "sportclip": {
        "url": f"https://{HOST}/images/Data/Downloads/SportCLIP/SportCLIP.zip",
        "size": 85232672,
        "etag": '"5148c20-635013cebaf56"',
    },
    "matdat": {
        "url": f"https://{HOST}/images/Data/Downloads/MATDAT/MATDAT%20dataset.zip",
        "size": 12448638920,
        "etag": '"2e5ff27c8-5f5fac5f465cd"',
    },
}


def fetch_range(source, start, end, name):
    """Persist one immutable range, validating identity, TLS, length and route."""
    if not 0 <= start <= end < source["size"]:
        raise ValueError("Range outside original archive")
    path = ROOT / "metadata" / name
    if path.exists() or path.with_suffix(".route.json").exists():
        raise FileExistsError(path)
    command = [
        "curl", "--noproxy", "*", "--ipv4", "--resolve", f"{HOST}:443:{IP}",
        "--connect-timeout", "6", "--max-time", "40", "--max-filesize", str(end-start+1),
        "--silent", "--show-error", "--header", "If-Match: " + source["etag"],
        "--range", f"{start}-{end}", "--dump-header", str(path.with_suffix(".headers")),
        "--output", str(path), "--write-out", "%{remote_ip}|%{http_code}|%{url_effective}",
        source["url"],
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    route = subprocess.run(["ip", "route", "get", IP], capture_output=True, text=True).stdout
    headers = path.with_suffix(".headers").read_text(errors="replace")
    data = path.read_bytes() if path.exists() else b""
    receipt = dict(url=source["url"], range=[start, end], etag=source["etag"],
        exit_code=result.returncode, curl=result.stdout, stderr=result.stderr,
        route=route, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
        strict_TLS=True, explicit_no_proxy=True, time=time.time())
    save(path.with_suffix(".route.json"), receipt)
    expected = f"bytes {start}-{end}/{source['size']}"
    if (result.returncode or not result.stdout.startswith(IP + "|206|")
            or " dev eno2 " not in " " + route + " "
            or len(data) != end-start+1
            or expected.lower() not in headers.lower()):
        raise ValueError(f"Range/directness validation failed: {receipt}")
    return data


def central_location(source, tail, start, name):
    position = tail.rfind(b"PK\x05\x06")
    if position < 0:
        raise ValueError("No EOCD")
    end = struct.unpack_from("<4s4H2IH", tail, position)
    if end[1] or end[2]:
        raise ValueError("Multi-disk ZIP unsupported")
    count, size, offset = end[4:7]
    if count != 65535 and size != 0xffffffff and offset != 0xffffffff:
        return count, size, offset
    locator = struct.unpack_from("<4sIQI", tail, position - 20)
    if locator[0] != b"PK\x06\x07" or locator[1] != 0 or locator[3] != 1:
        raise ValueError("Invalid ZIP64 locator")
    address = locator[2]
    if start <= address and address+56 <= start+len(tail):
        record = tail[address-start:address-start+56]
    else:
        record = fetch_range(source, address, address+55, name+"_zip64.bin")
    fields = struct.unpack("<4sQ2H2I4Q", record)
    if fields[0] != b"PK\x06\x06" or fields[4] or fields[5]:
        raise ValueError("Invalid ZIP64 EOCD")
    return fields[7], fields[8], fields[9]


def extra64(extra, size, compressed, offset):
    position = 0
    while position+4 <= len(extra):
        tag, length = struct.unpack_from("<HH", extra, position)
        payload = extra[position+4:position+4+length]
        if tag == 1:
            values = iter(struct.unpack("<"+"Q"*(len(payload)//8), payload))
            return tuple(next(values) if value == 0xffffffff else value
                         for value in (size, compressed, offset))
        position += 4+length
    if 0xffffffff in (size, compressed, offset):
        raise ValueError("Missing ZIP64 extended info")
    return size, compressed, offset


def parse_members(data, expected_count):
    members, position = [], 0
    while position < len(data):
        fields = struct.unpack_from("<4s6H3I5H2I", data, position)
        if fields[0] != b"PK\x01\x02":
            raise ValueError("Invalid central member signature")
        name_length, extra_length, comment_length = fields[10:13]
        raw_name = data[position+46:position+46+name_length]
        extra = data[position+46+name_length:position+46+name_length+extra_length]
        name = raw_name.decode("utf-8" if fields[3] & 2048 else "cp437")
        path = pathlib.PurePosixPath(name.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", name):
            raise ValueError("Unsafe member path")
        size, compressed, offset = extra64(extra, fields[9], fields[8], fields[16])
        members.append(dict(name=name, flags=fields[3], method=fields[4],
            crc32=fields[7], size=size, compressed_size=compressed, offset=offset))
        position += 46+name_length+extra_length+comment_length
    if len(members) != expected_count:
        raise ValueError("Member count mismatch")
    return members


def index_source(name, source):
    tail_start = max(0, source["size"]-65557)
    tail = fetch_range(source, tail_start, source["size"]-1, name+"08_tail.bin")
    count, length, offset = central_location(source, tail, tail_start, name+"08")
    if length > 2_000_000:
        raise ValueError("Central-directory metadata cap exceeded")
    central = (tail[offset-tail_start:offset-tail_start+length]
        if offset >= tail_start and offset+length <= source["size"]
        else fetch_range(source, offset, offset+length-1, name+"08_central.bin"))
    members = parse_members(central, count)
    save(ROOT/(name+"08_index.json"), dict(source=source, members=members,
        total_expanded=sum(item["size"] for item in members)))
    print(json.dumps(dict(source=name, members=members,
        total_expanded=sum(item["size"] for item in members))), flush=True)


def main():
    save(ROOT/"upm_zip08_registration.json", dict(scope="Author ZIP central metadata only",
        sources=SOURCES, payload_cap_bytes=4_200_000, no_media_extraction=True,
        known_public_author_IP=IP, per_process_TLS_hostname_override_only=True))
    for name, source in SOURCES.items():
        index_source(name, source)


if __name__ == "__main__":
    main()
