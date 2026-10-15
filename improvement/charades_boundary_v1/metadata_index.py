"""One registered Linux-only Charades annotation/ZIP64-directory acquisition.

Never requests a video member header or body. No HEAD/probe, retry, model,
training, decoder, or automatic replacement is performed. All evidence remains
under the new registered root; only a compact completion is printed.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import socket
import stat
import struct
import traceback
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REMOTE_ROOT = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1')
ANNOTATION = dict(url='https://ai2-public-datasets.s3-us-west-2.amazonaws.com/charades/Charades.zip',
                  bytes=3519822, etag='8f64f8d7d4cdf0e207e53f8e1fe1703b')
VIDEO = dict(url='https://ai2-public-datasets.s3-us-west-2.amazonaws.com/charades/Charades_v1.zip',
             bytes=58807341227, etag='fa450a0dd79ec4e5453a6d0f9dd9bd34-7011')
ORDER_PREFIX = 'charades-boundary-v1:'


def require(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def safe_name(name):
    path = PurePosixPath(name)
    require(name and '\\' not in name and not path.is_absolute() and
            all(p not in ('', '.', '..') for p in path.parts), 'unsafe archive member name')
    require(':' not in path.parts[0], 'drive-qualified archive member')
    return path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Unexpected redirect; diagnose instead of changing origin')


class MetadataHTTP:
    def __init__(self, out, budget):
        self.out, self.budget, self.requested, self.received = out, budget, 0, 0
        self.opener = urllib.request.build_opener(NoRedirect())

    def fetch(self, spec, start, length, name):
        require(type(start) is int and type(length) is int and 0 <= start < start+length <= spec['bytes'],
                'range outside frozen object')
        require(self.requested+length <= self.budget, 'registered metadata byte budget exceeded')
        target = self.out/name
        require(not target.exists() and not target.with_suffix(target.suffix+'.partial').exists(),
                'range already attempted; no implicit repeat')
        self.requested += length
        item = dict(url=spec['url'], start=start, length=length, total=spec['bytes'], name=name,
                    if_match=spec['etag'], event='REQUEST', utc=dt.datetime.now(dt.timezone.utc).isoformat())
        append(self.out/'http.jsonl', item)
        req = urllib.request.Request(spec['url'], headers={
            'Range': f'bytes={start}-{start+length-1}', 'If-Match': '"'+spec['etag']+'"',
            'Accept-Encoding': 'identity', 'User-Agent': 'AIC-Charades-metadata-evaluation/1.0'})
        pending = target.with_suffix(target.suffix+'.partial')
        with self.opener.open(req, timeout=45) as response:
            header_path = self.out/(name+'.http_headers.json')
            save(header_path, dict(status=response.status, headers=dict(response.headers.items()),
                 url=spec['url'], start=start, length=length))
            require(response.status == 206, 'expected206; never consume200 whole archive')
            require(response.headers.get('Content-Range') == f'bytes {start}-{start+length-1}/{spec["bytes"]}',
                    'Content-Range differs from frozen exact request')
            require(response.headers.get('Content-Length') == str(length), 'range length header differs')
            require(response.headers.get('ETag') == '"'+spec['etag']+'"', 'object ETag changed')
            require(response.headers.get('Content-Encoding', 'identity') == 'identity', 'encoded HTTP payload')
            count = 0
            with pending.open('xb') as stream:
                while count < length:
                    chunk = response.read(min(1 << 20, length-count))
                    require(chunk, 'truncated metadata range; retain partial and failure')
                    stream.write(chunk)
                    count += len(chunk)
                    self.received += len(chunk)
                require(not response.read(1), 'metadata range exceeds declared exact length')
                stream.flush()
                os.fsync(stream.fileno())
        require(pending.stat().st_size == length, 'actual metadata file length differs')
        pending.rename(target)
        append(self.out/'http.jsonl', dict(**{k:v for k,v in item.items() if k != 'event'},
               event='ACCEPTED', bytes=length, sha256=sha(target), status=206,
               headers_sha256=sha(header_path)))
        return target.read_bytes()


def end_records(tail, total, fetch_record):
    """Parse EOCD and optional ZIP64 EOCD without any member-body read."""
    tail_start = total-len(tail)
    positions = [i for i in range(len(tail)-21) if tail[i:i+4] == b'PK\x05\x06']
    valid = []
    for pos in positions:
        if pos+22 <= len(tail):
            values = struct.unpack_from('<4s4H2IH', tail, pos)
            if pos+22+values[7] == len(tail):
                valid.append((pos, values))
    require(len(valid) == 1, 'ambiguous/missing exact EOCD at object end')
    pos, values = valid[0]
    _, disk, disk_cd, count_disk, count, cd_size, cd_offset, comment = values
    require(disk == disk_cd == 0, 'multidisk ZIP unsupported')
    absolute_eocd = tail_start+pos
    locator_pos = pos-20
    has_locator = locator_pos >= 0 and tail[locator_pos:locator_pos+4] == b'PK\x06\x07'
    sentinel = count_disk == 65535 or count == 65535 or cd_size == 0xffffffff or cd_offset == 0xffffffff
    require(not sentinel or has_locator, 'ZIP64 marker without locator')
    zip64 = None
    directory_limit = absolute_eocd
    if has_locator:
        _, record_disk, record_offset, disks = struct.unpack_from('<4sIQI', tail, locator_pos)
        require(record_disk == 0 and disks == 1 and 0 <= record_offset < absolute_eocd-20,
                'invalid ZIP64 locator')
        record = fetch_record(record_offset, 56)
        fields = struct.unpack('<4sQ2H2I4Q', record)
        require(fields[0] == b'PK\x06\x06' and fields[1] >= 44 and fields[4] == fields[5] == 0,
                'invalid ZIP64 end record')
        require(record_offset+12+fields[1] <= absolute_eocd-20, 'ZIP64 end record overlaps locator')
        require(fields[6] == fields[7], 'ZIP64 split directory unsupported')
        if count != 65535:
            require(count == fields[7], 'classic/ZIP64 total entry disagreement')
        if count_disk != 65535:
            require(count_disk == fields[6], 'classic/ZIP64 disk entry disagreement')
        if cd_size != 0xffffffff:
            require(cd_size == fields[8], 'classic/ZIP64 directory size disagreement')
        if cd_offset != 0xffffffff:
            require(cd_offset == fields[9], 'classic/ZIP64 directory offset disagreement')
        count, cd_size, cd_offset = fields[7], fields[8], fields[9]
        directory_limit = record_offset
        zip64 = dict(record_offset=record_offset, record_size=12+fields[1],
                     entries=count, directory_bytes=cd_size, directory_offset=cd_offset)
    else:
        require(count == count_disk, 'split central directory unsupported')
    require(count > 0 and cd_size >= count*46 and 0 <= cd_offset < cd_offset+cd_size <= directory_limit,
            'central directory domain invalid')
    return dict(entries=count, directory_bytes=cd_size, directory_offset=cd_offset,
                eocd_offset=absolute_eocd, comment_bytes=comment, zip64=zip64)


def zip64_extra(extra, unpacked, packed, offset, disk):
    cursor, record = 0, None
    while cursor < len(extra):
        require(cursor+4 <= len(extra), 'truncated extra header')
        tag, length = struct.unpack_from('<HH', extra, cursor)
        cursor += 4
        require(cursor+length <= len(extra), 'truncated extra field')
        if tag == 1:
            require(record is None, 'duplicate ZIP64 extra field')
            record = extra[cursor:cursor+length]
        cursor += length
    needed = (unpacked == 0xffffffff, packed == 0xffffffff, offset == 0xffffffff, disk == 65535)
    require(not any(needed) or record is not None, 'member ZIP64 marker without extra')
    cursor, result = 0, [unpacked, packed, offset, disk]
    for index, present in enumerate(needed):
        if present:
            size, fmt = (4, '<I') if index == 3 else (8, '<Q')
            require(cursor+size <= len(record), 'short member ZIP64 payload')
            result[index] = struct.unpack_from(fmt, record, cursor)[0]
            cursor += size
    return result


def parse_directory(raw, expected_count, directory_offset):
    cursor, rows, names = 0, [], set()
    for _ in range(expected_count):
        require(cursor+46 <= len(raw), 'truncated central-directory header')
        v = struct.unpack_from('<4s6H3I5H2I', raw, cursor)
        require(v[0] == b'PK\x01\x02', 'invalid central-directory signature')
        length = 46+v[10]+v[11]+v[12]
        require(cursor+length <= len(raw), 'truncated central-directory variable fields')
        name_bytes = raw[cursor+46:cursor+46+v[10]]
        name = name_bytes.decode('utf-8' if v[3]&0x800 else 'cp437')
        safe_name(name)
        require(name not in names, 'duplicate archive member identity')
        names.add(name)
        require(not stat.S_ISLNK(v[15] >> 16), 'symbolic-link member unsupported')
        extra = raw[cursor+46+v[10]:cursor+46+v[10]+v[11]]
        unpacked, packed, offset, disk = zip64_extra(extra, v[9], v[8], v[16], v[13])
        require(disk == 0 and 0 <= offset < directory_offset and packed >= 0 and unpacked >= 0,
                'member header domain or disk invalid')
        rows.append(dict(name=name, bytes=unpacked, compressed_bytes=packed, header_offset=offset,
                         crc32=f'{v[7]:08x}', compression=v[4], flags=v[3],
                         encrypted=bool(v[3]&1), directory=name.endswith('/')))
        cursor += length
    require(cursor == len(raw), 'unexpected bytes after complete central directory')
    return rows


def annotation_ids(path, out, max_expanded):
    members, train_name, license_name = [], None, None
    with zipfile.ZipFile(path) as archive:
        require(sum(z.file_size for z in archive.infolist()) <= max_expanded, 'metadata expansion exceeds protocol')
        names = archive.namelist()
        require(len(names) == len(set(names)), 'duplicate annotation member')
        for z in archive.infolist():
            safe_name(z.filename)
            require(not z.flag_bits&1 and not stat.S_ISLNK(z.external_attr >> 16), 'encrypted/symlink metadata')
            h = hashlib.sha256()
            count = 0
            with archive.open(z) as stream:
                for chunk in iter(lambda: stream.read(1 << 20), b''):
                    h.update(chunk)
                    count += len(chunk)
            require(count == z.file_size, 'annotation member size mismatch')  # ZipFile also checks CRC.
            members.append(dict(name=z.filename, bytes=count, crc32=f'{z.CRC:08x}', sha256=h.hexdigest()))
            basename = PurePosixPath(z.filename).name
            if basename == 'Charades_v1_train.csv':
                require(train_name is None, 'ambiguous author train CSV')
                train_name = z.filename
            if basename.lower() == 'license.txt':
                require(license_name is None, 'ambiguous author data license')
                license_name = z.filename
        require(train_name and license_name, 'author train CSV and license required')
        license_text = archive.read(license_name).decode('utf-8-sig')
        require('License for Non-Commercial Use' in license_text and
                'It may also be used for evaluation purposes elsewhere.' in license_text, 'author data license differs')
        with (out/'author_license.txt').open('x', encoding='utf-8') as stream:
            stream.write(license_text)
        reader = csv.DictReader(io.StringIO(archive.read(train_name).decode('utf-8-sig'), newline=''))
        require(reader.fieldnames and 'id' in reader.fieldnames, 'author train id column missing')
        ids = [row['id'] for row in reader]  # Never use actions, quality, script, or GT to select sources.
        require(len(ids) >= 60 and len(ids) == len(set(ids)) and all(x.isascii() and x.isalnum() for x in ids),
                'invalid or duplicate author training IDs')
    save(out/'annotation_members_01.json', dict(status='PASS_AUTHOR_METADATA_MEMBERS_SIZE_CRC_SHA', members=members,
         author_train_member=train_name, train_sources=len(ids), license_member=license_name,
         source_selection_read_fields=['id'], no_media_members=True))
    return sorted(ids, key=lambda x: (hashlib.sha256((ORDER_PREFIX+x).encode('utf-8')).hexdigest(), x))


def main(root):
    require(socket.gethostname() == 'inspur-NP5570M5' and str(root) == str(REMOTE_ROOT),
            'fixed Linux host/root identity')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'metadata CPU-only environment required')
    protocol_path, receipt_path = root/'metadata_protocol_01.json', root/'charades_http_01.json'
    protocol, receipt = read(protocol_path), read(receipt_path)
    require(protocol['approved'] is True and protocol['scope'] == 'CHARADES_METADATA_AND_ARCHIVE_DIRECTORY_ONLY',
            'registered metadata-only authority required')
    require(protocol['root'] == str(root) and protocol['annotation'] == ANNOTATION and protocol['video'] == VIDEO,
            'registered objects/root differ from original current HTTP evidence')
    require(protocol['primary_sources'] == 20 and protocol['dev_sources'] == protocol['confirm_sources'] == 10
            and protocol['engineering_replacements'] == 40, 'fixed source cohort sizes')
    require(sha(receipt_path) == protocol['http_receipt_sha256'] and sha(__file__) == protocol['script_sha256'],
            'registered source/script SHA changed')
    for spec in (ANNOTATION, VIDEO):
        item = next(x for x in receipt['objects'] if x['url'] == spec['url'])
        require(item['bytes'] == spec['bytes'] and item['etag'] == spec['etag'] and item['range_status'] == 206,
                'prior successful author range evidence differs')
    deadline = dt.datetime.fromisoformat(protocol['deadline'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'new metadata action after deadline')
    require(ORDER_PREFIX in protocol['sample_order'] and protocol['media_bodies_authorized_in_this_stage'] is False
            and protocol['new_GPU_authorized_in_this_stage'] is False, 'frozen source order/metadata-only scope')
    budget, expanded = protocol['max_metadata_payload_bytes'], protocol.get('max_annotation_expanded_bytes', 256 << 20)
    require(type(budget) is int and ANNOTATION['bytes']+65557 < budget <= 32 << 20,
            'bounded metadata payload protocol required')
    require(type(expanded) is int and 0 < expanded <= 256 << 20, 'bounded annotation expansion protocol required')
    # Dynamic capacity relates to this action, not a fixed disk GiB admission line.
    free = shutil.disk_usage(root).free
    require(free > budget+expanded, 'insufficient capacity for registered metadata/expansion')
    out = root/'metadata_01'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(protocol_sha256=sha(protocol_path), script_sha256=sha(__file__),
         prior_http_receipt_sha256=sha(receipt_path), pid=os.getpid(),
         host=socket.gethostname(), disk_free_bytes=free, load_average=os.getloadavg(),
         scope=protocol['scope'], new_media_downloads=0, new_model_calls=0, optimizer_updates=0,
         utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    http = MetadataHTTP(out, budget)
    try:
        http.fetch(ANNOTATION, 0, ANNOTATION['bytes'], 'Charades.zip')
        ids = annotation_ids(out/'Charades.zip', out, expanded)
        # This is the first real directory-index read, not a repeat HEAD/22B probe.
        tail_size = min(65557, VIDEO['bytes'])
        tail = http.fetch(VIDEO, VIDEO['bytes']-tail_size, tail_size, 'video_end_directory_metadata.bin')
        layout = end_records(tail, VIDEO['bytes'],
            lambda offset,length: http.fetch(VIDEO, offset, length, 'video_zip64_end_record.bin'))
        require(layout['directory_bytes'] <= budget-http.requested, 'central directory exceeds frozen metadata budget')
        raw = http.fetch(VIDEO, layout['directory_offset'], layout['directory_bytes'], 'video_central_directory.bin')
        members = parse_directory(raw, layout['entries'], layout['directory_offset'])
        save(out/'video_archive_index_01.json', dict(layout=layout, members=members,
             archive=VIDEO, central_directory_sha256=sha(out/'video_central_directory.bin'),
             media_headers_requested=0, media_payload_bytes=0))
        mapped = {}
        for item in members:
            name = PurePosixPath(item['name']).name
            if not item['directory'] and name.lower().endswith('.mp4'):
                source = name[:-4]
                require(source not in mapped, 'ambiguous source ID to video member mapping')
                mapped[source] = item
        rows = []
        for index, source in enumerate(ids[:60]):
            item = mapped.get(source)
            usable = item is not None and not item['encrypted'] and item['compression'] in (0, 8)
            rows.append(dict(source_id=source, source_order_sha256=hashlib.sha256((ORDER_PREFIX+source).encode()).hexdigest(),
                 rank=index+1, role='dev' if index < 10 else ('confirm' if index < 20 else 'engineering_reserve'),
                 member=item, metadata_member_usable=usable,
                 media_identity_nativeclock_reference_domain='NOT_PERFORMED'))
        manifest = dict(schema='CHARADES_AUTHOR_TRAIN_SHA_ORDERED_20_PLUS40_METADATA_01',
            status='PASS_METADATA_AND_DIRECTORY_ONLY_NOT_MEDIA_ADMISSION', rows=rows,
            primary_sources=20, dev_sources=10, confirm_sources=10, engineering_replacements=40,
            sort='sha256(UTF8 charades-boundary-v1: + raw author train id), id tie-break; no actions/quality/GT fields used',
            author_train_sources=len(ids), archive=VIDEO,
            primary_metadata_usable=sum(x['metadata_member_usable'] for x in rows[:20]),
            reserve_metadata_usable=sum(x['metadata_member_usable'] for x in rows[20:]),
            primary_compressed_media_bytes=sum(x['member']['compressed_bytes'] for x in rows[:20] if x['member']),
            primary_uncompressed_media_bytes=sum(x['member']['bytes'] for x in rows[:20] if x['member']),
            all60_compressed_media_bytes=sum(x['member']['compressed_bytes'] for x in rows if x['member']),
            annotation_zip_sha256=sha(out/'Charades.zip'), archive_index_sha256=sha(out/'video_archive_index_01.json'),
            known_train_test_identity_isolation='PENDING', boundary_precision='NOT_ESTABLISHED',
            media_downloads=0, media_headers_requested=0, new_model_calls=0, optimizer_updates=0)
        save(out/'source_manifest_01.json', manifest)
        result = dict(status=manifest['status'], source_manifest_path=str(out/'source_manifest_01.json'),
            source_manifest_bytes=(out/'source_manifest_01.json').stat().st_size,
            source_manifest_sha256=sha(out/'source_manifest_01.json'),
            annotation_zip_bytes=ANNOTATION['bytes'], annotation_zip_sha256=sha(out/'Charades.zip'),
            archive_index_bytes=(out/'video_archive_index_01.json').stat().st_size,
            archive_index_sha256=sha(out/'video_archive_index_01.json'),
            metadata_payload_requested=http.requested, metadata_payload_received=http.received,
            primary_metadata_usable=manifest['primary_metadata_usable'],
            primary_compressed_media_bytes=manifest['primary_compressed_media_bytes'],
            primary_uncompressed_media_bytes=manifest['primary_uncompressed_media_bytes'],
            all60_compressed_media_bytes=manifest['all60_compressed_media_bytes'],
            unique_claim_sha256=sha(out/'claim.json'), protocol_sha256=sha(protocol_path),
            media_downloads=0, new_model_calls=0, optimizer_updates=0)
        require(http.requested == http.received, 'metadata payload accounting differs')
        save(out/'completion.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
             requested_bytes=http.requested, received_bytes=http.received,
             successful_files_not_repeated=True, media_downloads=0, new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=REMOTE_ROOT)
    args = parser.parse_args()
    main(args.root)
