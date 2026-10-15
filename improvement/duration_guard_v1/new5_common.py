"""Independent five-source identity contract; no labels/model execution."""
import hashlib
import json
import os
from pathlib import Path
from origin_range_helpers import identity

BASE = Path('/home/inspur/aic_video_work/duration_guard_iteration_20261013_v1')
MEDIA = BASE/'media_01'
SOURCE_COUNT = 5


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def check_download_admission(registration_path):
    if Path(registration_path).resolve() != BASE/'new5_source_registration_01.json':
        raise ValueError('Independent reserved-five registration path required')
    registration = read(registration_path)
    rows = registration['rows']
    if len(rows) != SOURCE_COUNT or len({r['source_name'] for r in rows}) != SOURCE_COUNT or any(r['role'] != 'new_confirm' for r in rows):
        raise ValueError('Initial reserved-five denominator changed')
    canonical = hashlib.sha256(json.dumps(registration, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    claim = read(MEDIA/'launch_claim.json')
    authorization = claim['authorization']
    if (not authorization['approved'] or authorization['registration_canonical_sha256'] != canonical or
            authorization['registration_sha256'] != sha(registration_path) or claim['registration_sha256'] != sha(registration_path) or
            authorization['route'] != 'ETH_ORIGINAL_ORIGIN_TO_LINUX_DIRECT' or
            authorization['compressed_media_bytes'] != registration['exact_compressed_media_payload_bytes']):
        raise ValueError('Bound continued human route authorization missing')
    completed = read(MEDIA/'completion.json')
    if (completed['status'] != 'PASS_FIVE_AUTHORIZED_ORIGINAL_MEDIA_TRANSFERS_NOT_INPUT_ADMISSION' or
            completed['sources'] != SOURCE_COUNT or len(completed['rows']) != SOURCE_COUNT or
            completed['total_media_file_bytes'] != registration['exact_decoded_file_bytes']):
        raise ValueError('Actual reserved-five media is incomplete')
    downloaded = {r['source_name']:r for r in completed['rows']}
    if set(downloaded) != {r['source_name'] for r in rows}:
        raise ValueError('Actual registered media source identities changed')
    for row in rows:
        proof = downloaded[row['source_name']]
        if (proof['status'] != 'PASS_ORIGINAL_ZIP_MEMBER_CRC_SHA' or proof['source_group'] != row['source_group'] or
                proof['original_member'] != row['member']['name'] or proof['identity']['bytes'] != row['member']['bytes'] or
                proof['identity']['crc32'] != row['member']['crc32'] or Path(proof['path']).resolve() != MEDIA/(row['source_name']+'.webm')):
            raise ValueError('Accepted original reserved member identity/path changed')
    isolation = read(BASE/'source_isolation_acceptance.json')
    if (isolation['status'] != 'PASS_KNOWN_SOURCE_IDENTITY_AND_BYTE_SEPARATION' or
            isolation['registered_sources'] != SOURCE_COUNT or isolation['intersections'] or
            isolation['registration_sha256'] != sha(registration_path) or
            isolation['media_completion_sha256'] != sha(MEDIA/'completion.json') or
            isolation['known_identity_snapshot_sha256'] != sha(BASE/'known_identity_snapshot_01.json') or
            isolation['new_optimizer_updates'] != 0):
        raise ValueError('Reserved-five known identity/byte separation is not accepted')
    for path, digest in isolation['current_training_provenance'].items():
        if sha(path) != digest:
            raise ValueError('Known original-B training provenance changed')
    terminal = read(BASE/'media_stage_completion.json')
    if terminal['media_sha256'] != sha(MEDIA/'completion.json') or terminal['isolation_sha256'] != sha(BASE/'source_isolation_acceptance.json'):
        raise ValueError('Actual media/isolation terminal binding changed')
    return registration, downloaded, claim


def mapping_admission(registration_path):
    registration, downloaded, _ = check_download_admission(registration_path)
    folder = BASE/'mapping_01'
    completed = read(folder/'completion.json')
    if (completed['status'] != 'PASS_FIVE_ORIGINAL_NATIVE_MAPPINGS_NOT_PROCESSOR_OR_SOURCE_ADMISSION' or
            completed['sources'] != SOURCE_COUNT or len(completed['rows']) != SOURCE_COUNT or
            completed['bindings']['registration_sha256'] != sha(registration_path)):
        raise ValueError('Every reserved-five original native mapping must pass')
    mapped = {r['source_name']:r for r in completed['rows']}
    if len(mapped) != SOURCE_COUNT or set(mapped) != {r['source_name'] for r in registration['rows']}:
        raise ValueError('Registered native clock denominator changed')
    return registration, downloaded, mapped, dict(registration_sha256=sha(registration_path),
        mapping_completion_sha256=sha(folder/'completion.json'),
        source_isolation_acceptance_sha256=sha(BASE/'source_isolation_acceptance.json'))
