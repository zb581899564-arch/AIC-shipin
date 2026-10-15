"""Index only TAR headers over strict small HTTP ranges; never read video bodies."""
import datetime
import hashlib
import json
import math
import os
import socket
import time
import traceback
from pathlib import Path

import requests

BASE = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1')


def save(path, value):
    tmp = path.with_suffix(path.suffix + '.pending')
    with tmp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    tmp.replace(path)


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise RuntimeError('Unexpected host')
    out = BASE / 'archive_index_01'
    out.mkdir(exist_ok=False)
    reg = json.loads((BASE / 'archive_index_registration_01.json').read_text())
    routes = json.loads((BASE / 'archive_part_redirects_01.json').read_text())
    frozen = json.loads((BASE / 'metadata_02/source_registration_01.json').read_text())
    wanted = {row['video_id'] for row in frozen['selection']}
    save(out / 'launch_claim.json', {'pid': os.getpid(), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                   'new_model_calls': 0, 'new_video_files': 0})
    start = time.monotonic()
    offset, headers, requested, found = 0, 0, 0, {}
    etags = {}
    session = requests.Session()
    try:
        journal = (out / 'headers.jsonl').open('x', encoding='utf-8')
        while offset < reg['total_archive_bytes']:
            if time.monotonic() - start > reg['maximum_index_seconds']:
                raise RuntimeError('Registered metadata-index time budget reached; retain cursor and all successful headers')
            if requested + 512 > reg['maximum_header_payload_bytes']:
                raise RuntimeError('Registered header-only payload budget reached')
            part_index, part_offset = divmod(offset, reg['regular_part_bytes'])
            part = routes[part_index]
            if part_offset + 512 > part['bytes']:
                raise RuntimeError('TAR header would cross a part boundary')
            expected_range = f"bytes {part_offset}-{part_offset+511}/{part['bytes']}"
            request_headers = {'Range': f'bytes={part_offset}-{part_offset+511}', 'Accept-Encoding': 'identity'}
            if part_index in etags:
                request_headers['If-Range'] = etags[part_index]
            with session.get(part['publisher_redirect_url'], headers=request_headers, stream=True, timeout=(10, 25)) as response:
                if response.status_code != 206 or response.headers.get('Content-Range') != expected_range:
                    raise RuntimeError(f'Strict header range rejected at part{part_index}/offset{part_offset}: HTTP{response.status_code}; no whole-part fallback')
                etag = response.headers.get('ETag')
                if not etag or (part_index in etags and etags[part_index] != etag):
                    raise RuntimeError('Pinned publisher part ETag changed')
                etags[part_index] = etag
                raw = response.raw.read(513)
                if len(raw) != 512:
                    raise RuntimeError('TAR header range not exactly 512 bytes')
            requested += 512
            headers += 1
            if not any(raw):
                if wanted - set(found):
                    raise RuntimeError('TAR terminator before all frozen source identities were indexed')
                break
            stored_checksum = int(raw[148:156].rstrip(b'\0 ').lstrip() or b'0', 8)
            if stored_checksum != sum(raw[:148]) + 8 * 32 + sum(raw[156:]):
                raise RuntimeError('TAR header checksum mismatch')
            name = raw[:100].split(b'\0', 1)[0].decode('utf-8')
            prefix = raw[345:500].split(b'\0', 1)[0].decode('utf-8')
            if prefix:
                name = prefix + '/' + name
            if name.startswith('/') or '..' in Path(name).parts:
                raise RuntimeError('Unsafe public archive member name')
            size = int(raw[124:136].rstrip(b'\0 ').lstrip() or b'0', 8)
            kind = raw[156:157]
            if kind not in (b'0', b'\0', b'5'):
                raise RuntimeError('Unsupported TAR metadata type; do not guess extended headers')
            next_offset = offset + 512 + ((size + 511) // 512) * 512
            if next_offset > reg['total_archive_bytes']:
                raise RuntimeError('TAR member exceeds registered split archive')
            row = {'member_name': name, 'member_bytes': size, 'type': kind.decode('ascii'),
                   'header_global_offset': offset, 'body_global_offset': offset + 512,
                   'next_header_global_offset': next_offset, 'part_index': part_index,
                   'part_etag': etag, 'header_sha256': hashlib.sha256(raw).hexdigest()}
            journal.write(json.dumps(row, ensure_ascii=False) + '\n')
            journal.flush()
            vid = Path(name).stem
            if kind in (b'0', b'\0') and vid in wanted:
                if vid in found or Path(name).suffix.lower() != '.mp4' or size <= 0:
                    raise RuntimeError('Duplicate or invalid selected original media member')
                found[vid] = row
            offset = next_offset
            save(out / 'state.json', {'stage': 'HEADER_ONLY_INDEX_RUNNING_NO_VIDEO_BODIES_OR_MODEL',
                                     'headers': headers, 'header_payload_bytes': requested,
                                     'next_global_offset': offset, 'matched_sources': len(found),
                                     'expected_sources': len(wanted), 'members_found': found,
                                     'part_etags': etags, 'elapsed_seconds': time.monotonic() - start})
            if wanted == set(found):
                break
        journal.close()
        if set(found) != wanted:
            raise RuntimeError('Frozen source identity index incomplete')
        save(out / 'completion.json', {'status': 'PASS_FROZEN_TWENTY_PUBLIC_ARCHIVE_LOCATIONS_NOT_MEDIA_OR_RIGHTS_ADMISSION',
                                       'headers': headers, 'header_payload_bytes': requested,
                                       'members': found, 'elapsed_seconds': time.monotonic() - start,
                                       'new_video_files': 0, 'new_CPU_decodes': 0, 'new_model_calls': 0,
                                       'full_part_SHA_verified': False,
                                       'community_mirror_not_author_byte_identity_confirmation': True})
    except BaseException:
        save(out / 'failure.json', {'status': 'HEADER_INDEX_FAILED_RETAIN_ALL_SUCCESSFUL_ROWS_AND_CURSOR',
                                   'traceback': traceback.format_exc(), 'headers': headers,
                                   'header_payload_bytes': requested, 'next_global_offset': offset,
                                   'members_found': found, 'new_video_files': 0, 'new_model_calls': 0})
        raise


if __name__ == '__main__':
    main()
