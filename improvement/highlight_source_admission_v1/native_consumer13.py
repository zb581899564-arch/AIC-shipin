"""First native admission of complete members already present in accepted ranges."""
import hashlib
import json
from pathlib import Path
import struct
import time
import zlib

from direct import ROOT, ref, save
from native_audit12 import audit_source
from upm_zip08 import SOURCES


def accepted_pieces():
    names = [ROOT/'sportclip10_chunk_000_accepted.json']
    names += sorted(ROOT.glob('sportclip11_fragment_*_accepted.json'))
    original = ROOT/'metadata'/'sportclip10_chunk_001.bin'
    records = []
    for name in names:
        record = json.loads(name.read_text())
        records.append((record['range'][0],record['range'][1]+1,Path(record['path'])))
    partial = json.loads(original.with_suffix('.route.json').read_text())
    records.append((partial['range'][0],partial['range'][0]+partial['bytes'],original))
    records.sort()
    cursor = 0
    for first,stop,path in records:
        if first != cursor or path.stat().st_size != stop-first:
            raise ValueError('Accepted original archive pieces are not contiguous')
        cursor = stop
    return records,cursor


def read_span(pieces, first, stop):
    outputs = []
    for a,b,path in pieces:
        left,right = max(a,first),min(b,stop)
        if left < right:
            with path.open('rb') as stream:
                stream.seek(left-a)
                outputs.append(stream.read(right-left))
    value = b''.join(outputs)
    if len(value) != stop-first:
        raise ValueError('Incomplete accepted span')
    return value


def extract_member(member, pieces, available, folder):
    offset = member['offset']
    if offset+30 > available:
        return False
    header = struct.unpack('<4s5H3I2H',read_span(pieces,offset,offset+30))
    if header[0] != b'PK\x03\x04' or header[2] & 1 or header[3] != 8:
        raise ValueError('Unexpected local original ZIP header')
    start = offset+30+header[9]+header[10]
    end = start+member['compressed_size']
    if end > available:
        return False
    filename = read_span(pieces,offset+30,offset+30+header[9]).decode()
    if filename != member['name']:
        raise ValueError('Original local and central member names differ')
    payload = read_span(pieces,start,end)
    decoded = zlib.decompress(payload,-15)
    if len(decoded) != member['size'] or zlib.crc32(decoded) != member['crc32']:
        raise ValueError('Original member decompression length/CRC failed')
    target = folder/Path(filename).name
    with target.open('xb') as output:
        output.write(decoded)
    save(folder/(target.name+'.acceptance.json'),dict(original_member=member,
        member=ref(target),compressed_span=[start,end],strict_original_CRC_pass=True,
        accepted_piece_refs=[ref(path) for a,b,path in pieces if a<end and b>offset]))
    return True


def main():
    source = SOURCES['sportclip']
    sources = ['diving','long_jump','pole_vault','tumbling']
    ordered = sorted(sources,key=lambda name:hashlib.sha256(('UPM-SportCLIP-v1/'+name).encode()).hexdigest())
    save(ROOT/'native13_registration.json',dict(source=source,
        author_index=ref(ROOT/'sportclip08_index.json'),source_hash_order=ordered,
        roles={name:('held_sport' if name==ordered[-1] else 'development') for name in sources},
        original_index='zero-based inclusive, author extractor start0 / CSV last+1',
        scope='Only first complete source/member CRC and original frame alignment; no GPU/training',
        UNKNOWN_mask_required=True,no_summary_unselected_as_negative=True,
        no_repeat_successful_download_or_native_decode=True,max_wall_seconds=1800,
        no_production_admission=True,source_count=4,not_80_independent_sources=True))
    folder=ROOT/'media'/'sportclip_members13';folder.mkdir(parents=True)
    (ROOT/'native12').mkdir()
    members=[row for row in json.loads((ROOT/'sportclip08_index.json').read_text())['members'] if row['size']]
    accepted,started,rows=set(),time.monotonic(),[]
    while time.monotonic()-started < 1800:
        pieces,available=accepted_pieces()
        for member in members:
            if member['name'] not in accepted and extract_member(member,pieces,available,folder):
                accepted.add(member['name'])
                print('CRC_ACCEPTED',member['name'],flush=True)
        for stem in sources:
            ready=all(f'SportCLIP dataset/{stem}{suffix}' in accepted for suffix in ['.csv','.mp4'])
            if ready and not (ROOT/'native12'/stem/'acceptance.json').exists():
                rows.append(audit_source(stem,folder))
        if len(rows)==4:
            save(ROOT/'native13_completion.json',dict(state='PASS4_ORIGINAL_SOURCE_MANUAL_FRAME_ALIGNMENT',
                sources=rows,source_count=4,new_GPU=0,new_training=0,no_automatic_production=True))
            return
        if (ROOT/'sportclip_remaining11_failure.json').exists():
            save(ROOT/'native13_partial.json',dict(state='WAITING_FOR_REMAINING_MEDIA_AFTER_ACTUAL_NETWORK_FAILURE',
                sources=rows,accepted_members=sorted(accepted),accepted_prefix_bytes=available))
            return
        time.sleep(2)
    raise TimeoutError('Bounded original-member consumer elapsed')


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        save(ROOT/'native13_failure.json',dict(error=repr(error),time=time.time()))
        raise
