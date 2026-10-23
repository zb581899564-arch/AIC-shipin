"""Explicit remaining metadata only: adopt 11 ranges, stop after needed domains."""
import json
from pathlib import Path, PurePosixPath
import tarfile
import traceback

from t_io import ROOT, check, identity, read, save
from tar_ranges11 import DirectRanges

OLD = ROOT / 'archive_index11'
TARGET = ROOT / 'archive_scoped14'
WANTED = {'README.md', 'annotation_alignment_warnings.json', 'download_failures.json',
          'dog/annotations_mturk.json', 'parkour/annotations_mturk.json'}


def adopt(reader):
    rows = [json.loads(line) for line in (OLD / 'ranges/ranges.jsonl').read_text().splitlines() if line.strip()]
    for row in rows:
        path = check(row['body'])
        if path.stat().st_size != row['count']:
            raise ValueError('Previously accepted range size differs')
        reader.cache.append((row['start'], row['start'] + row['count'], path))
    etags = {row['object_etag'] for row in rows}
    if len(etags) != 1:
        raise ValueError('Prior accepted ranges refer to inconsistent objects')
    reader.etag = next(iter(etags))
    reader.network_bytes = sum(row['count'] for row in rows)
    if reader.network_bytes != read(OLD / 'failure.json')['accepted_range_bytes']:
        raise ValueError('Prior failure/range journal denominator differs')
    return rows


def main():
    TARGET.mkdir()
    failure = read(OLD / 'failure.json')
    if 'budget exhausted' not in failure['traceback'] or (OLD / 'completion.json').exists():
        raise ValueError('Expected real bounded metadata failure is absent')
    launch = read(ROOT / 'archive_index11_launch.json')
    live = Path('/proc') / str(launch['pid']) / 'stat'
    if live.exists() and live.read_text().rsplit(')', 1)[1].split()[19] == launch['start_ticks']:
        raise RuntimeError('Original metadata parent is still alive; do not duplicate it')
    metadata = read(Path(__file__).parent / 'mirror_metadata11.json')
    reader = DirectRanges(metadata['signed_CDN_url'], metadata['archive_bytes'], TARGET / 'ranges', seconds=900)
    try:
        rows = adopt(reader)
        prior_bytes = reader.network_bytes
        save(TARGET / 'registration.json', dict(
            actual_failure=identity(OLD / 'failure.json'), accepted_range_journal=identity(OLD / 'ranges/ranges.jsonl'),
            adopted_ranges=len(rows), adopted_network_body_bytes=prior_bytes,
            only_missing_metadata_or_header_ranges=True, no_accepted_range_download_repeated=True,
            scope='Dog/parkour original human metadata and their member offsets only; no unrelated remainder scan',
            maximum_cumulative_metadata_bytes=4 << 20, new_seconds_max=900,
            no_whole_archive_or_media_download=True, original_source_and_licensing_still_pending=True))
        members, accepted = [], {}
        with tarfile.open(fileobj=reader, mode='r:') as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Unsafe archive member path')
                relative = str(path.relative_to('youtube_highlights_full'))
                if relative.startswith(('skating/', 'skiing/', 'surfing/')):
                    if set(accepted) != WANTED:
                        raise ValueError('Needed two-domain metadata not found before unrelated remainder')
                    break
                members.append(dict(name=member.name, bytes=member.size, data_offset=member.offset_data,
                                    offset=member.offset, isfile=member.isfile()))
                if relative in WANTED:
                    if not member.isfile() or not 0 < member.size <= 2 << 20:
                        raise ValueError('Requested metadata is not a bounded regular file')
                    data = archive.extractfile(member).read()
                    if len(data) != member.size:
                        raise ValueError('Metadata member read incomplete')
                    destination = TARGET / relative.replace('/', '__')
                    with destination.open('xb') as stream:
                        stream.write(data)
                    if relative.endswith('.json'):
                        json.loads(data)
                    accepted[relative] = identity(destination)
            else:
                if set(accepted) != WANTED:
                    raise ValueError('Archive ended without the required metadata')
        save(TARGET / 'members.json', members)
        save(TARGET / 'completion.json', dict(
            state='SCOPED_DIRECT_METADATA_COMPLETE_NOT_MEDIA_ADMISSION', accepted=accepted,
            partial_member_index=identity(TARGET / 'members.json'), indexed_members=len(members),
            adopted_range_body_bytes=prior_bytes, new_direct_range_body_bytes=reader.network_bytes - prior_bytes,
            cumulative_range_body_bytes=reader.network_bytes, actual_direct_route=reader.route,
            whole_archive_SHA_verified=False, unrelated_archive_remainder_not_scanned=True,
            original_author_and_native_mapping_checks_still_required=True, new_model_calls=0))
        print('ARCHIVE_SCOPED14_COMPLETE', len(members), reader.network_bytes - prior_bytes, flush=True)
    except Exception:
        save(TARGET / 'failure.json', dict(traceback=traceback.format_exc(),
            cumulative_range_body_bytes=reader.network_bytes, no_automatic_retry=True))
        raise
    finally:
        reader.close()


if __name__ == '__main__':
    main()
