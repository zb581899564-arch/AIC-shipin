"""Independent reserved-five origin transfer and known-identity isolation; no model."""
import datetime
import hashlib
import json
import os
import socket
import struct
import traceback
import zlib
from pathlib import Path

from origin_range_helpers import identity, range_response, save

BASE = Path('/home/inspur/aic_video_work/duration_guard_iteration_20261013_v1')
OLD = Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1')
OUT = BASE/'media_01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isolation(registration, accepted):
    snapshot_path = BASE/'known_identity_snapshot_01.json'
    snapshot = read(snapshot_path)
    if snapshot['status'] != 'COMPLETE_KNOWN_B_TRAINING_AND_FROZEN_426_IDENTITIES_NOT_NEW_MEDIA_SEPARATION':
        raise ValueError('Incomplete known source snapshot')
    training, testing = snapshot['training']['sources'], snapshot['testing']['records']
    if len(training) != 704 or len(testing) != 426 or {int(r['video_id']) for r in testing} != set(range(426)):
        raise ValueError('Known training/testing denominator changed')
    provenance = {}
    for name, digest in snapshot['provenance_bindings'].items():
        pieces = name.replace('\\', '/').split('/')
        if pieces[:2] != ['reports', 'round6_score_alignment']:
            raise ValueError('Unexpected original training provenance path')
        path = Path('/home/inspur/aic_video_work').joinpath(*pieces[1:])
        if sha(path) != digest:
            raise ValueError('Original B training provenance changed')
        provenance[str(path)] = digest
    known = training+testing
    known_bytes = {r['source_sha256'] for r in known}
    aliases = set()
    for row in known:
        names = [str(row.get(k, '')) for k in ('source_name', 'source_group', 'video_id', 'youtube_id', 'parent_sample_id')]
        names.append(Path(row['source_path']).stem)
        aliases.update(name.casefold().replace(' ', '_') for name in names if name)
    matches, checked = [], []
    for row, proof in zip(registration['rows'], accepted):
        actual = identity(OUT/(row['source_name']+'.webm'))
        if actual != proof['identity'] or proof['source_name'] != row['source_name']:
            raise ValueError('New media transfer/identity binding changed')
        if actual['sha256'] in known_bytes or any(name.casefold().replace(' ', '_') in aliases for name in (row['source_name'], row['source_group'])):
            matches.append(row['source_name'])
        checked.append(dict(source_name=row['source_name'], **actual))
    if len(checked) != 5 or len({r['sha256'] for r in checked}) != 5:
        raise ValueError('Reserved five denominator/byte uniqueness changed')
    result = dict(status='FAILED_KNOWN_SOURCE_INTERSECTION' if matches else 'PASS_KNOWN_SOURCE_IDENTITY_AND_BYTE_SEPARATION',
        registered_sources=5, registration_sha256=sha(BASE/'new5_source_registration_01.json'),
        media_completion_sha256=sha(OUT/'completion.json'), known_identity_snapshot_sha256=sha(snapshot_path),
        current_training_provenance=provenance, intersections=matches, actual_original_media=checked,
        scope_limitations=snapshot['identity_limitations'], semantic_separation_proven=False,
        new_model_calls=0, new_optimizer_updates=0, audit_code_sha256=sha(Path(__file__)))
    target = BASE/('source_isolation_failure_01.json' if matches else 'source_isolation_acceptance.json')
    if target.exists():
        raise ValueError('Existing isolation result must not be overwritten')
    save(target, result)
    if matches:
        raise ValueError('Known source intersection; no CPU/model admission')


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Unexpected host')
    reg_path = BASE/'new5_source_registration_01.json'
    registration = read(reg_path)
    auth = read(BASE/'new5_route_authorization_01.json')
    canonical = hashlib.sha256(json.dumps(registration, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    if (auth['approved'] is not True or auth['registration_sha256'] != sha(reg_path) or
            auth['registration_canonical_sha256'] != canonical or auth['route'] != 'ETH_ORIGINAL_ORIGIN_TO_LINUX_DIRECT' or
            auth['compressed_media_bytes'] != registration['exact_compressed_media_payload_bytes'] or
            auth['media_file_bytes'] != registration['exact_decoded_file_bytes'] or len(registration['rows']) != 5):
        raise ValueError('Five-source registration/continued route authorization rejected')
    original = read(OLD/'human_source_registration_01.json')
    if (sha(OLD/'human_source_registration_01.json') != registration['original_reserved_list_sha256'] or
            [r['source_name'] for r in registration['rows']] != original['reserve_sources']):
        raise ValueError('Initial reserved list changed')
    selection_path = BASE/'screen_selection_before_new5_confirm.json'
    selection = read(selection_path)
    if (sha(selection_path) != registration['frozen_screen_selection_sha256'] or
            selection['chosen'] != ['D2', 'D4', 'D8'] or not selection['frozen_before_new5_media_and_prediction'] or
            selection['candidate_package_admitted'] or sha(BASE/'PROTOCOL.md') != registration['protocol_sha256']):
        raise ValueError('Development selection was not frozen before new confirmation media')
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json', dict(pid=os.getpid(), registration_sha256=sha(reg_path), authorization=auth,
        code_sha256=sha(Path(__file__)), range_helper_sha256=sha(Path(__file__).with_name('origin_range_helpers.py')), new_model_calls=0))
    accepted = []
    stage = 'DOWNLOAD'
    try:
        for row in registration['rows']:
            name, info = row['source_name'], row['member']
            if any(c in name for c in ('/', '\\')) or '..' in name or row['role'] != 'new_confirm':
                raise ValueError('Unsafe/unregistered reserved source name')
            with range_response(registration['original_source_url'], info['header_offset'], 30, registration['archive_bytes']) as response:
                header = response.read(31)
            if len(header) != 30:
                raise ValueError('Original ZIP header length mismatch')
            (OUT/(name+'.local_header.bin')).write_bytes(header)
            values = struct.unpack('<4s5H3I2H', header)
            if values[0] != b'PK\x03\x04' or values[3] != info['compression'] or info['compression'] not in (0, 8):
                raise ValueError('Original ZIP header/member mismatch')
            with range_response(registration['original_source_url'], info['header_offset']+30, values[-2], registration['archive_bytes']) as response:
                member_name = response.read(values[-2]+1)
            if member_name.decode('utf-8') != info['name']:
                raise ValueError('Original ZIP member name changed')
            offset = info['header_offset']+30+values[-2]+values[-1]
            packed = OUT/(name+'.packed.partial')
            with range_response(registration['original_source_url'], offset, info['compressed_bytes'], registration['archive_bytes']) as response, packed.open('xb') as stream:
                count = 0
                while count < info['compressed_bytes']:
                    chunk = response.read(min(1 << 20, info['compressed_bytes']-count))
                    if not chunk:
                        raise ValueError('Truncated original range; preserve partial for explicit recovery')
                    stream.write(chunk)
                    count += len(chunk)
                    stream.flush()
                os.fsync(stream.fileno())
                if response.read(1):
                    raise ValueError('Original range exceeded registration')
            pending = OUT/(name+'.webm.pending')
            decompress = zlib.decompressobj(-15) if info['compression'] == 8 else None
            with packed.open('rb') as source, pending.open('xb') as target:
                for chunk in iter(lambda: source.read(1 << 20), b''):
                    target.write(decompress.decompress(chunk) if decompress else chunk)
                if decompress:
                    target.write(decompress.flush())
                    if not decompress.eof or decompress.unused_data:
                        raise ValueError('Original raw-DEFLATE boundary mismatch')
                target.flush()
                os.fsync(target.fileno())
            actual = identity(pending)
            if actual['bytes'] != info['bytes'] or actual['crc32'] != info['crc32']:
                raise ValueError('Original ZIP member size/CRC mismatch')
            target = OUT/(name+'.webm')
            pending.rename(target)
            proof = dict(status='PASS_ORIGINAL_ZIP_MEMBER_CRC_SHA', source_name=name, source_group=row['source_group'],
                path=str(target), identity=actual, original_member=info['name'], range_compressed_bytes=info['compressed_bytes'],
                original_archive_url=registration['original_source_url'])
            save(OUT/(name+'.download.json'), proof)
            accepted.append(proof)
            save(OUT/'progress.json', dict(completed_sources=len(accepted), expected_sources=5, last_source=name, new_model_calls=0))
            print(json.dumps(dict(source=name, accepted=len(accepted), bytes=actual['bytes'])), flush=True)
        if len(accepted) != 5 or sum(r['identity']['bytes'] for r in accepted) != registration['exact_decoded_file_bytes']:
            raise ValueError('Reserved five actual media denominator/bytes changed')
        save(OUT/'completion.json', dict(status='PASS_FIVE_AUTHORIZED_ORIGINAL_MEDIA_TRANSFERS_NOT_INPUT_ADMISSION',
            rows=accepted, sources=5, native_mapping='UNVERIFIED', new_model_calls=0,
            total_media_file_bytes=sum(r['identity']['bytes'] for r in accepted)))
        stage = 'SOURCE_ISOLATION'
        isolation(registration, accepted)
        save(BASE/'media_stage_completion.json', dict(status='PASS_NEW5_MEDIA_AND_KNOWN_IDENTITY_ISOLATION_NOT_CPU_INPUT_ADMISSION',
            completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), media_sha256=sha(OUT/'completion.json'),
            isolation_sha256=sha(BASE/'source_isolation_acceptance.json'), new_model_calls=0, new_optimizer_updates=0))
        print('PASS_NEW5_MEDIA_AND_KNOWN_IDENTITY_ISOLATION_NOT_CPU_INPUT_ADMISSION', flush=True)
    except BaseException as error:
        save(OUT/'failure.json', dict(status='FAILED_NEW5_STAGE_PRESERVE_ALL_SUCCESS_AND_PARTIAL',stage=stage,
            completed_sources=len(accepted), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            exception=repr(error), traceback=traceback.format_exc(), new_model_calls=0))
        raise


if __name__ == '__main__':
    main()
