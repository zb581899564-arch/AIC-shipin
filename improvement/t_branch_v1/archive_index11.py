"""Only TAR headers and two-domain human metadata; never whole-download the TAR."""
import json
from pathlib import Path, PurePosixPath
import tarfile
import traceback

from t_io import ROOT, identity, read, save
from tar_ranges11 import DirectRanges

TARGET = ROOT / 'archive_index11'
WANTED = {'README.md', 'annotation_alignment_warnings.json', 'download_failures.json',
          'dog/annotations_mturk.json', 'parkour/annotations_mturk.json'}


def main():
    TARGET.mkdir()
    meta_path = Path(__file__).parent / 'mirror_metadata11.json'
    meta = read(meta_path)
    if (meta['archive_bytes'] != 9904404480 or meta['archive_full_sha256'] !=
            'af5c025a03071b1a3e064da3bb96546fc2ae5de76050973bb3153d354870efa2'):
        raise ValueError('Pinned mirror manifest/object identity differs')
    save(TARGET / 'registration.json', dict(
        source_metadata=identity(meta_path), repo=meta['repository'], revision=meta['revision'],
        archive_bytes=meta['archive_bytes'], maximum_direct_metadata_bytes=4 << 20,
        metadata_time_seconds=600, selected_metadata=sorted(WANTED),
        scope='TAR headers/boundary bytes plus metadata only; no extracted media',
        Windows_metadata_exception_used_only_for6773bytes=True,
        Linux_media_or_metadata_body_requires_actual_direct_public_TLS_route=True,
        no_training_or_model=True, no_whole_archive_SHA_validation_claim=True))
    reader = DirectRanges(meta['signed_CDN_url'], meta['archive_bytes'], TARGET / 'ranges')
    try:
        with tarfile.open(fileobj=reader, mode='r:') as archive:
            members = []
            for member in archive:
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts:
                    raise ValueError('Unsafe archive path; no extraction allowed')
                members.append(dict(name=member.name, bytes=member.size, offset=member.offset,
                                    data_offset=member.offset_data, isfile=member.isfile(),
                                    type=member.type.decode('ascii', errors='replace')))
                if len(members) % 50 == 0:
                    print('TAR11_HEADERS', len(members), reader.network_bytes, flush=True)
            save(TARGET / 'members.json', members)
            accepted = []
            for relative in sorted(WANTED):
                full = 'youtube_highlights_full/' + relative
                member = archive.getmember(full)
                if not member.isfile() or member.size > 2 << 20:
                    raise ValueError('Metadata member is not a bounded regular file')
                stream = archive.extractfile(member)
                data = stream.read()
                if len(data) != member.size:
                    raise ValueError('Metadata member truncated')
                path = TARGET / relative.replace('/', '__')
                with path.open('xb') as output:
                    output.write(data)
                if relative.endswith('.json'):
                    json.loads(data)
                accepted.append(dict(member=full, file=identity(path)))
            save(TARGET / 'completion.json', dict(
                state='DIRECT_PARTIAL_TAR_METADATA_COMPLETE_NOT_MEDIA_ADMISSION',
                archive_members=len(members), MP4_members=sum(m['name'].endswith('.mp4') for m in members),
                accepted=accepted, direct_network_body_bytes=reader.network_bytes,
                route=reader.route, whole_archive_SHA_verified=False,
                original_author_blob_and_native_media_binding_still_required=True,
                model_calls=0, training=0))
            print('TAR11_METADATA_COMPLETE', len(members), reader.network_bytes, flush=True)
    except Exception:
        save(TARGET / 'failure.json', dict(traceback=traceback.format_exc(),
            accepted_range_bytes=reader.network_bytes, actual_route=reader.route,
            no_automatic_retry=True, no_whole_archive_fallback=True))
        raise
    finally:
        reader.close()


if __name__ == '__main__':
    main()
