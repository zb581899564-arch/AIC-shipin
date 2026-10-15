"""Append immutable full discussion packets; no network or browser control."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('version')
    parser.add_argument('--previous', required=True)
    parser.add_argument('--append', nargs='+', required=True)
    args = parser.parse_args()
    output = HERE / ('context-' + args.version + '.md')
    if output.exists():
        raise FileExistsError(output)
    previous = HERE / args.previous
    body = bytearray(previous.read_bytes())
    sources = []
    for filename in args.append:
        source = HERE / filename
        data = source.read_bytes()
        sources.append(dict(file=filename, bytes=len(data), sha256=digest(data)))
        body.extend(('\n\n# 新增完整原文 ' + filename + '\n\n').encode())
        body.extend(data)
    body.extend(('\n\n# END_REPLAN_' + args.version.upper() + '\n').encode())
    output.write_bytes(body)
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), file=output.name,
                   bytes=len(body), lines=body.count(b'\n'), sha256=digest(body),
                   previous_file=previous.name, previous_sha256=digest(previous.read_bytes()),
                   previous_is_exact_prefix=body[:previous.stat().st_size] == previous.read_bytes(),
                   appended=sources)
    (HERE / ('packet-' + args.version + '-receipt.json')).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == '__main__':
    main()
