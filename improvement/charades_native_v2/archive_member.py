"""Exact pinned HTTP ranges for one author ZIP member; no retries or full ZIP."""
import hashlib
import os
import re
import struct
import traceback
import urllib.request
import zlib
from pathlib import Path
from charades_v2_common import ROOT, V1ROOT, append, check_deadline, read, require, save, sha, utc


def range_bytes(archive, start, length, destination, phase, source_id):
    check_deadline()
    require(length > 0 and 0 <= start < start+length <= archive['bytes'], 'Registered archive byte range')
    previous = []
    log = ROOT/'media_01/http.jsonl'
    for entry in [V1ROOT/'media_01/http.jsonl', log]:
        if entry.exists():
            previous += [__import__('json').loads(x) for x in entry.read_text().splitlines() if x]
    protocol = read(ROOT/'partial_native_protocol_01.json')
    if phase == 'compressed_member_body':
        require(sum(x['requested_bytes'] for x in previous if x['phase'] == phase)+length
                + protocol['preserved_old_unlogged_partial_body_bytes']
                <= protocol['all60_compressed_media_bytes_budget'], 'Frozen required-member payload cap exceeded')
    else:
        require(sum(x['requested_bytes'] for x in previous if x['phase'] != 'compressed_member_body')+length
                <= protocol['max_header_overhead_bytes'], 'Frozen local header byte cap exceeded')
    etag = archive['etag'].strip('"')
    request = urllib.request.Request(archive['url'], headers={
        'Range': 'bytes='+str(start)+'-'+str(start+length-1), 'If-Match': '"'+etag+'"',
        'Accept-Encoding': 'identity'})
    received, digest = 0, hashlib.sha256()
    with urllib.request.urlopen(request, timeout=45) as response:
        require(response.status == 206, 'Pinned partial HTTP206 required; no whole archive fallback')
        require(response.headers.get('ETag', '').strip('"') == etag, 'Author archive ETag changed')
        require(response.headers.get('Content-Range') == 'bytes '+str(start)+'-'+str(start+length-1)+'/'+str(archive['bytes']),
                'Exact ContentRange and total author ZIP bytes required')
        require(int(response.headers['Content-Length']) == length, 'Pinned partial ContentLength required')
        require(response.headers.get('Content-Encoding', 'identity') in ('identity', ''), 'Unexpected transfer encoding')
        require(response.geturl() == archive['url'], 'No unregistered alternate publisher route')
        with destination.open('xb') as stream:
            while chunk := response.read(min(1 << 20, length-received+1)):
                received += len(chunk)
                require(received <= length, 'Range returned excess payload')
                stream.write(chunk)
                digest.update(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        headers = dict(response.headers.items())
    require(received == length, 'Range returned incomplete payload; preserve partial and stop')
    receipt = dict(source_id=source_id, phase=phase, status=206, start=start, requested_bytes=length,
                   received_bytes=received, sha256=digest.hexdigest(), url=archive['url'], headers=headers, utc=utc())
    save(destination.with_suffix(destination.suffix+'.http.json'), receipt)
    append(ROOT/'media_01/http.jsonl', receipt)
    return receipt


def download_member(source, archive, known_hashes, registration_sha256):
    source_id, member = source['source_id'], source['member']
    require(not (V1ROOT/'media_01'/source_id).exists(),
            'Old complete/failed/partial member must never be requested in the new chain')
    require(re.fullmatch(r'[A-Za-z0-9]{5}', source_id) is not None, 'Unexpected author source ID')
    require(member['name'] == 'Charades_v1/'+source_id+'.mp4' and not member['encrypted']
            and not member['directory'] and member['compression'] in (0, 8), 'Only registered safe original MP4 member')
    folder = ROOT/'media_01'/source_id
    require(not folder.exists(), 'Member already attempted; no original download/header repetition')
    folder.mkdir()
    save(folder/'claim.json', dict(source_id=source_id, registration_sha256=registration_sha256,
                                  member=member, pid=os.getpid(), utc=utc()))
    try:
        offset = member['header_offset']
        fixed = folder/'local_header_fixed.bin'
        range_bytes(archive, offset, 30, fixed, 'local_header_fixed', source_id)
        signature, version, flags, method, mtime, mdate, crc, compressed, raw, name_len, extra_len = struct.unpack('<4s5H3I2H', fixed.read_bytes())
        require(signature == b'PK\x03\x04' and flags == member['flags'] and method == member['compression'],
                'Local header differs from frozen CD or signature')
        require(not flags & 1 and not flags & 8 and compressed != 0xffffffff and raw != 0xffffffff,
                'Encrypted/descriptor/ZIP64 local member unsupported; no repair')
        require(crc == int(member['crc32'], 16) and compressed == member['compressed_bytes']
                and raw == member['bytes'], 'Frozen CD vs local sizes/CRC mismatch')
        require(0 < name_len <= 4096 and extra_len <= 65535, 'Safe registered local member metadata length')
        variable = folder/'local_header_name_extra.bin'
        range_bytes(archive, offset+30, name_len+extra_len, variable, 'local_header_name_extra', source_id)
        require(variable.read_bytes()[:name_len].decode('utf-8' if flags & 2048 else 'cp437') == member['name'],
                'Frozen local member name mismatch')
        payload_start = offset+30+name_len+extra_len
        save(folder/'local_header_acceptance.json', dict(status='PASS_LOCAL_HEADER_BOUND_TO_FROZEN_CD',
             source_id=source_id, data_start=payload_start, header_bytes=30+name_len+extra_len,
             header_sha256=sha(fixed), variable_header_sha256=sha(variable), member=member))
        partial = folder/(source_id+'.compressed.partial')
        range_bytes(archive, payload_start, compressed, partial, 'compressed_member_body', source_id)
        compressed_path = folder/(source_id+'.compressed')
        partial.rename(compressed_path)
        target_partial = folder/(source_id+'.mp4.partial')
        decompressor = zlib.decompressobj(-15) if method == 8 else None
        crc_observed, written, digest = 0, 0, hashlib.sha256()
        with compressed_path.open('rb') as src, target_partial.open('xb') as dst:
            while block := src.read(1 << 20):
                unpacked = decompressor.decompress(block) if decompressor else block
                written += len(unpacked)
                require(written <= raw, 'Expanded member exceeds registered raw bytes')
                dst.write(unpacked); digest.update(unpacked); crc_observed = zlib.crc32(unpacked, crc_observed)
            tail = decompressor.flush() if decompressor else b''
            written += len(tail)
            require(written <= raw, 'Expanded final payload exceeds registered raw bytes')
            dst.write(tail); digest.update(tail); crc_observed = zlib.crc32(tail, crc_observed)
            dst.flush(); os.fsync(dst.fileno())
        require(decompressor is None or decompressor.eof and not decompressor.unused_data and not decompressor.unconsumed_tail,
                'Raw deflate member incomplete or trailing data')
        require(written == raw and crc_observed == crc, 'Member size/CRC failed')
        target = folder/(source_id+'.mp4')
        target_partial.rename(target)
        known_separated = digest.hexdigest() not in known_hashes
        receipt = dict(status='PASS_MEMBER_206_IFMATCH_CD_CRC_SHA_NOT_NATIVE',
             source_id=source_id, path=str(target), bytes=written, sha256=digest.hexdigest(),
             crc32=f'{crc_observed:08x}', compressed_path=str(compressed_path),
             compressed_bytes=compressed, compressed_sha256=sha(compressed_path),
             local_header_acceptance_sha256=sha(folder/'local_header_acceptance.json'),
             registration_sha256=registration_sha256, publisher_url=archive['url'], publisher_ETag=archive['etag'],
             known_byte_separation_pass=known_separated,
             semantic_pretraining_or_hidden_source_separation='UNKNOWN', new_model_calls=0, new_optimizer_updates=0)
        save(folder/'completion.json', receipt)
        return receipt
    except BaseException as err:
        save(folder/'failure.json', dict(status='STOP_PRESERVE_ALL_SUCCESSFUL_HEADERS_AND_PARTIAL_BODY',
             source_id=source_id, error=repr(err), traceback=traceback.format_exc(), utc=utc(),
             recovery='Explicit new recovery contract required; reference successful stored header/clock/cache receipts and fetch only remaining payload. Original run/HEAD/CD/annotation/member success must not repeat.',
             new_model_calls=0))
        raise
