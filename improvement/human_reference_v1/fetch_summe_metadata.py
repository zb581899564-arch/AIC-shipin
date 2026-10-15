"""Read only small original annotation/document members via bounded HTTP ranges."""
import hashlib
import io
import json
import struct
import urllib.request
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/human_reference_iteration_20261013_v1/summe_original_metadata_01'
URL = 'https://data.vision.ee.ethz.ch/cvl/SumMe/SumMe.zip'
SIZE = 2396688224
BUDGET = 5_000_000
received = 0


def get_range(start, length):
    global received
    assert 0 <= start < start + length <= SIZE and received + length <= BUDGET
    req = urllib.request.Request(URL, headers={'Range': f'bytes={start}-{start + length - 1}',
                                              'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(req, timeout=40) as response:
        assert response.status == 206, f'Range ignored; no full archive read: {response.status}'
        assert response.headers['Content-Range'] == f'bytes {start}-{start + length - 1}/{SIZE}'
        data = response.read(length + 1)
    assert len(data) == length
    received += length
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    tail = get_range(SIZE - 65558, 65558)
    pos = tail.rfind(b'PK\x05\x06')
    assert pos >= 0
    end = tail[pos:]
    values = list(struct.unpack('<4s4H2IH', end[:22]))
    assert values[1] == values[2] == 0 and values[3] == values[4]
    cd_size, cd_offset = values[5:7]
    assert cd_size < 1_000_000
    central = get_range(cd_offset, cd_size)
    values[6] = 0
    index = zipfile.ZipFile(io.BytesIO(central + struct.pack('<4s4H2IH', *values) + end[22:]))
    inventory = []
    members = []
    for info in index.infolist():
        inventory.append(dict(name=info.filename, bytes=info.file_size,
                              compressed_bytes=info.compress_size, header_offset=info.header_offset,
                              crc32=f'{info.CRC:08x}', compression=info.compress_type))
        name = info.filename.lower()
        if info.is_dir() or not (name.endswith('.mat') or name.endswith('.txt') or name.endswith('.m')):
            continue
        assert info.file_size <= 1_000_000 and info.compress_size <= 1_000_000
        header = get_range(info.header_offset, 30)
        vals = struct.unpack('<4s5H3I2H', header)
        assert vals[0] == b'PK\x03\x04' and vals[3] == info.compress_type
        offset = info.header_offset + 30 + vals[-2] + vals[-1]
        packed = get_range(offset, info.compress_size)
        if info.compress_type == zipfile.ZIP_DEFLATED:
            raw = zlib.decompress(packed, -15)
        else:
            assert info.compress_type == zipfile.ZIP_STORED
            raw = packed
        assert len(raw) == info.file_size and zlib.crc32(raw) & 0xffffffff == info.CRC
        relative = Path(info.filename)
        assert not relative.is_absolute() and '..' not in relative.parts
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        members.append(dict(name=info.filename, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                            crc32=f'{info.CRC:08x}'))
    receipt = dict(status='PASS_BOUNDED_ORIGINAL_DOCUMENT_AND_ANNOTATION_RANGES', source_url=URL,
                   full_archive_bytes=SIZE, actual_range_payload_bytes=received, payload_budget=BUDGET,
                   videos_downloaded=0, inventory=inventory, extracted_members=members,
                   archive_sha256='UNKNOWN_FULL_ARCHIVE_NOT_DOWNLOADED')
    (OUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('inventory', 'extracted_members')}))
    print('members', len(members), 'videos', sum(x['name'].lower().endswith(('.avi', '.mp4')) for x in inventory))


if __name__ == '__main__':
    main()
