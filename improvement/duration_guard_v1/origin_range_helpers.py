"""Explicitly authorized direct-origin range download; resumable, no full ZIP fallback."""
import hashlib
import json
import os
import socket
import struct
import urllib.request
import zlib
from pathlib import Path

OUT = Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1/media_01')
ETAG = '"8eda8f60-4fde5b6612300"'


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def range_response(url, start, length, total):
    request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{start+length-1}',
        'If-Range': ETAG, 'Accept-Encoding': 'identity'})
    response = urllib.request.urlopen(request, timeout=45)
    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{start+length-1}/{total}':
        response.close()
        raise ValueError('Original range identity rejected; never read a full-archive response')
    return response


def identity(path):
    digest = hashlib.sha256()
    crc = 0
    size = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            size += len(chunk)
            crc = zlib.crc32(chunk, crc)
            digest.update(chunk)
    return dict(bytes=size, crc32=f'{crc & 0xffffffff:08x}', sha256=digest.hexdigest())


def main(registration, authorization, resume=False):
    assert socket.gethostname() == 'inspur-NP5570M5'
    assert authorization['approved'] is True
    canonical = hashlib.sha256(json.dumps(registration, sort_keys=True, ensure_ascii=False,
                                          separators=(',', ':')).encode('utf-8')).hexdigest()
    assert authorization['registration_canonical_sha256'] == canonical
    assert authorization['compressed_media_bytes'] == registration['exact_compressed_media_payload_bytes'] == 861654036
    assert authorization['route'] == 'ETH_ORIGINAL_ORIGIN_TO_LINUX_DIRECT'
    assert len(registration['rows']) == 20
    OUT.mkdir(parents=True, exist_ok=resume)
    if not resume:
        save(OUT / 'launch_claim.json', dict(pid=os.getpid(), new_model_calls=0,
                registration_sha256=authorization['registration_sha256'], authorization=authorization))
    else:
        assert (OUT / 'launch_claim.json').exists()
        claim = json.loads((OUT / 'launch_claim.json').read_text())
        assert claim['authorization']['registration_canonical_sha256'] == canonical
        assert claim['registration_sha256'] == authorization['registration_sha256']
    accepted = []
    for row in registration['rows']:
        info = row['member']
        assert '/' not in row['source_name'] and '..' not in row['source_name']
        target = OUT / (row['source_name'] + '.webm')
        proof_path = OUT / (row['source_name'] + '.download.json')
        if proof_path.exists():
            proof = json.loads(proof_path.read_text())
            assert identity(target) == proof['identity']
            accepted.append(proof)
            continue  # A completed real source transfer is never repeated.
        assert not target.exists()
        header_path = OUT / (row['source_name'] + '.local_header.bin')
        if header_path.exists():
            header = header_path.read_bytes()
        else:
            with range_response(registration['original_source_url'], info['header_offset'], 30,
                                registration['archive_bytes']) as response:
                header = response.read(31)
            assert len(header) == 30
            header_path.write_bytes(header)
        values = struct.unpack('<4s5H3I2H', header)
        assert values[0] == b'PK\x03\x04' and values[3] == info['compression']
        offset = info['header_offset'] + 30 + values[-2] + values[-1]
        packed = OUT / (row['source_name'] + '.packed.partial')
        already = packed.stat().st_size if packed.exists() else 0
        assert 0 <= already <= info['compressed_bytes']
        remaining = info['compressed_bytes'] - already
        if remaining:
            with range_response(registration['original_source_url'], offset+already, remaining,
                                registration['archive_bytes']) as response, packed.open('ab') as stream:
                count = 0
                while count < remaining:
                    chunk = response.read(min(1 << 20, remaining-count))
                    if not chunk:
                        raise ValueError('Truncated media range; retain partial for explicit recovery')
                    stream.write(chunk)
                    count += len(chunk)
                    stream.flush()
                os.fsync(stream.fileno())
                assert not response.read(1), 'Range exceeded declared length'
        assert packed.stat().st_size == info['compressed_bytes']
        decoded = target.with_suffix('.webm.pending')
        assert not decoded.exists(), 'Unaccepted decode requires explicit recovery review'
        decompressor = zlib.decompressobj(-15) if info['compression'] == 8 else None
        assert info['compression'] in (0, 8)
        with packed.open('rb') as stream, decoded.open('xb') as destination:
            for chunk in iter(lambda: stream.read(1 << 20), b''):
                destination.write(decompressor.decompress(chunk) if decompressor else chunk)
            if decompressor:
                destination.write(decompressor.flush())
                assert decompressor.eof and not decompressor.unused_data
            destination.flush()
            os.fsync(destination.fileno())
        actual = identity(decoded)
        assert actual['bytes'] == info['bytes'] and actual['crc32'] == info['crc32']
        decoded.rename(target)
        proof = dict(status='PASS_ORIGINAL_ZIP_MEMBER_CRC_SHA', source_name=row['source_name'],
                     source_group=row['source_group'], path=str(target), identity=actual,
                     range_compressed_bytes=info['compressed_bytes'], original_member=info['name'],
                     original_archive_url=registration['original_source_url'])
        save(proof_path, proof)
        accepted.append(proof)
        save(OUT / 'progress.json', dict(completed_sources=len(accepted), expected_sources=20,
                                       last_source=row['source_name'], new_model_calls=0))
        print(json.dumps(dict(source=row['source_name'], accepted=len(accepted), bytes=actual['bytes'])), flush=True)
    assert len(accepted) == 20
    result = dict(status='PASS_TWENTY_AUTHORIZED_ORIGINAL_MEDIA_TRANSFERS_NOT_INPUT_ADMISSION',
                  rows=accepted, sources=20, native_mapping='UNVERIFIED', new_model_calls=0,
                  total_media_file_bytes=sum(row['identity']['bytes'] for row in accepted))
    save(OUT / 'completion.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
