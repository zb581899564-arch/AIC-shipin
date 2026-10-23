"""Acquire only twelve frozen members directly, then first native compatibility QA."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import json
from pathlib import Path
import sys
import traceback

from mturk_native16 import native_profile, possible_duplicate_pairs
from t_io import ROOT, WORK, check, identity, read, save
from tar_ranges11 import DirectRanges

OUT = ROOT / 'media_native16'
sys.path.insert(0, str(WORK / 'highlight_source_control_20261021_v1'))
from native_audit12 import known_isolation


def adopt_metadata(reader):
    rows = []
    for stage in ['archive_index11', 'archive_scoped14']:
        journal = ROOT / stage / 'ranges/ranges.jsonl'
        accepted = [json.loads(line) for line in journal.read_text().splitlines()]
        rows.extend(accepted)
        for row in accepted:
            path = check(row['body'])
            reader.cache.append((row['start'], row['start'] + row['count'], path))
    etags = {row['object_etag'] for row in rows}
    if len(etags) != 1:
        raise ValueError('Previously acquired ranges refer to different objects')
    reader.etag = next(iter(etags))
    reader.network_bytes = sum(row['count'] for row in rows)
    return reader.network_bytes


def acquire_member(reader, row):
    folder = OUT / row['source_id']
    folder.mkdir()
    member = row['archive_member']
    if reader.etag != member['object_etag']:
        raise ValueError('Registered member/object identity differs')
    reader.seek(member['data_offset'])
    path = folder / (row['source_id'] + '.mp4')
    # The range reader reuses accepted single-byte boundary probes as well.
    with path.with_suffix('.partial').open('xb') as stream:
        remaining = member['bytes']
        while remaining:
            count = min(4 << 20, remaining)
            data = reader.read(count)
            if len(data) != count:
                raise ValueError('Incomplete selected member; preserve partial')
            stream.write(data)
            remaining -= count
    path.with_suffix('.partial').rename(path)
    result = identity(path)
    save(folder / 'media_acceptance.json', dict(media=result, registered_member=member,
        byte_size_exact=result['bytes'] == member['bytes'], object_etag=reader.etag,
        direct_route=reader.route, no_full_archive_fallback=True,
        whole_archive_checksum_not_verified=True))
    return folder, result


def admit_native(row, folder, media):
    isolation = known_isolation(media)
    profile = native_profile(Path(media['path']), row['mirror']['media'])
    save(folder / 'clock.json', profile)
    if max(s['end_frame'] for s in row['mirror']['segments']) != profile['native_frames']:
        raise ValueError('Registered author frame extent and actual native decode differ')
    record = dict(source_id=row['source_id'], role=row['role'], known_group=row['known_group'],
                  media=media, clock=identity(folder / 'clock.json'), isolation=isolation,
                  original_labels=identity(ROOT / 'source_manifest15' / row['source_id'] / 'acceptance.json'),
                  native_frames=profile['native_frames'], sketches=profile['duplicate_sketches'],
                  mirror_and_original_vote_coordinates_exact=True,
                  endpoint_convention='PENDING_ORIGINAL_EXTRACTION_CODE',
                  scope='Native extent compatibility; not original-content identity proof or training admission',
                  no_padding_stretch_truncation=True, no_quality_metrics=True)
    save(folder / 'native_acceptance.json', record)
    print('NATIVE16_ACCEPTED', row['source_id'], row['role'], profile['native_frames'], flush=True)
    return record


def main():
    manifest = read(ROOT / 'source_manifest15/registration.json')
    terminal = read(ROOT / 'source_manifest15/completion.json')
    if terminal['failed'] or len(terminal['accepted']) != 12:
        raise ValueError('All twelve original author files must be accepted before media')
    OUT.mkdir()
    metadata = read(ROOT / 'code/mirror_metadata11.json')
    prior = read(ROOT / 'archive_scoped14/completion.json')['cumulative_range_body_bytes']
    maximum = manifest['media_payload_bytes']
    reader = DirectRanges(metadata['signed_CDN_url'], metadata['archive_bytes'], OUT / 'ranges',
                          byte_cap=prior + maximum, seconds=900)
    accepted, failed = [], []
    try:
        adopted = adopt_metadata(reader)
        if adopted != prior:
            raise ValueError('Adopted journal and prior terminal byte counts differ')
        save(OUT / 'registration.json', dict(source_selection=identity(ROOT / 'source_manifest15/registration.json'),
            author_terminal=identity(ROOT / 'source_manifest15/completion.json'),
            selected_member_bytes=maximum, maximum_new_direct_network_bytes=maximum,
            adopted_metadata_body_bytes=adopted, maximum_seconds=900,
            no_accepted_network_range_or_media_repeated=True,
            new_downloads_only_on_verified_public_TLS_peer_and_physical_route=True,
            native_decode_first_and_exact_original_labels=True, model_or_training_admitted=False))
        for row in manifest['sources']:
            try:
                folder, media = acquire_member(reader, row)
                accepted.append(admit_native(row, folder, media))
            except Exception:
                failure = dict(source=row['source_id'], traceback=traceback.format_exc())
                save(OUT / (row['source_id'] + '_failure.json'), failure)
                failed.append(failure)
                # A transport failure must not silently retry or move to a new route.
                break
        save(OUT / 'completion.json', dict(state='SELECTED_MEDIA_NATIVE_COMPATIBILITY_COMPLETE',
            accepted=[identity(OUT / row['source_id'] / 'native_acceptance.json') for row in accepted],
            failed=failed, actual_new_direct_bytes=reader.network_bytes - adopted,
            native_frames=sum(row['native_frames'] for row in accepted),
            possible_duplicates=possible_duplicate_pairs(accepted),
            training_admission=False, endpoint_and_duplicate_scope_review_still_required=True,
            new_model_calls=0, protected_baseline_unchanged=True))
    except Exception:
        save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
            accepted_network_bytes=reader.network_bytes, no_automatic_retry=True))
        raise
    finally:
        reader.close()


if __name__ == '__main__':
    main()
