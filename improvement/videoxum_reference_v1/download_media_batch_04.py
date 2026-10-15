"""Fetch only preregistered located members, never entire parts or archive headers."""
import argparse
import hashlib
import os
import socket
import traceback
from pathlib import Path

from stage_common_04 import BASE, check_file, read, save, sha, utc


def member_ranges(member, regular, parts):
    cursor, remaining = member['body_global_offset'], member['member_bytes']
    if remaining <= 0:
        raise ValueError('Invalid preregistered member length')
    result = []
    while remaining:
        index, start = divmod(cursor, regular)
        if not 0 <= index < len(parts) or start >= parts[index]['bytes']:
            raise ValueError('Selected member escaped the pinned archive')
        count = min(remaining, parts[index]['bytes'] - start)
        result.append((index, start, count))
        cursor += count
        remaining -= count
    return result


def main(registration_path):
    if socket.gethostname() != 'inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Registered CPU-only Linux media stage required')
    reg_path = Path(registration_path)
    reg = read(reg_path)
    check_file(BASE/'metadata_02/source_registration_01.json', reg['source_registration_sha256'])
    check_file(BASE/'media_use_scope_04.json', reg['media_use_scope_sha256'])
    scope = read(BASE/'media_use_scope_04.json')
    if scope['purpose'] != 'PRIVATE_EXTERNAL_REFERENCE_VALIDATION_NO_TRAINING_OR_MEDIA_REDISTRIBUTION':
        raise ValueError('Media scope is not the registered external evaluation use')
    routes = read(check_file(reg['routes_path'], reg['routes_sha256']))
    exclusions = read(check_file(BASE/'known_source_exclusions_01.json', reg['exclusions_sha256']))
    selection = {row['video_id']: row for row in read(BASE/'metadata_02/source_registration_01.json')['selection']}
    out = BASE/reg['output_directory']
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=sha(reg_path)))
    accepted, current = [], None
    try:
        import requests
        session = requests.Session()
        for row in reg['members']:
            vid, member = row['video_id'], row['member']
            current = vid
            if vid not in selection or member['member_name'] != 'Activity_Videos/'+vid+'.mp4':
                raise ValueError('Archive member does not match a frozen reference source')
            if selection[vid]['youtube_id'] in exclusions['youtube_ids']:
                raise ValueError('Known training or historical external identity overlap')
            partial = out/(vid+'.mp4.partial')
            digest, received = hashlib.sha256(), 0
            part_evidence = []
            with partial.open('xb') as destination:
                for index, start, count in member_ranges(member, reg['regular_part_bytes'], routes):
                    part = routes[index]
                    expected = f"bytes {start}-{start+count-1}/{part['bytes']}"
                    headers = {'Range': f'bytes={start}-{start+count-1}', 'Accept-Encoding': 'identity'}
                    pinned_etag = reg['part_etags'].get(str(index))
                    if pinned_etag:
                        headers['If-Range'] = pinned_etag
                    with session.get(part['publisher_redirect_url'], headers=headers, stream=True,
                                     timeout=(10, 45)) as response:
                        if response.status_code != 206 or response.headers.get('Content-Range') != expected:
                            raise ValueError('Strict member range rejected; no full-part fallback')
                        etag = response.headers.get('ETag')
                        if not etag or (pinned_etag and etag != pinned_etag):
                            raise ValueError('Pinned publisher part changed')
                        n = 0
                        for chunk in response.iter_content(1024 * 1024):
                            if n + len(chunk) > count:
                                raise ValueError('Publisher sent more than the registered range')
                            destination.write(chunk)
                            digest.update(chunk)
                            n += len(chunk)
                        if n != count:
                            raise ValueError('Incomplete exact member range')
                        received += n
                        part_evidence.append(dict(part=index, start=start, bytes=n, etag=etag))
                destination.flush()
                os.fsync(destination.fileno())
            if received != member['member_bytes']:
                raise ValueError('Selected full member length differs from its TAR header')
            actual_sha = digest.hexdigest()
            if actual_sha in exclusions['known_media_sha256']:
                raise ValueError('Known training/test whole-file byte overlap')
            final = out/(vid+'.mp4')
            partial.rename(final)
            receipt = dict(status='PASS_SELECTED_MEMBER_BYTES_AND_KNOWN_IDENTITY_NOT_NATIVE_ADMISSION',
                video_id=vid, group=selection[vid]['group'], path=str(final), bytes=received,
                sha256=actual_sha, ranges=part_evidence, member=member,
                registration_sha256=sha(reg_path), media_use_scope_sha256=reg['media_use_scope_sha256'],
                known_identity_and_whole_file_byte_separation=True,
                exact_author_original_byte_identity_verified=False,
                hidden_test_ID_or_subclip_semantic_disjointness_verified=False,
                full_archive_part_SHA_verified=False, new_model_calls=0)
            save(out/(vid+'.receipt.json'), receipt)
            accepted.append(receipt)
            print('Accepted member '+vid, flush=True)
        save(out/'completion.json', dict(status='PASS_REGISTERED_LOCATED_MEDIA_BATCH_NOT_ALL20_OR_NATIVE_ADMISSION',
             utc=utc(), registration_sha256=sha(reg_path), sources=len(accepted),
             total_bytes=sum(row['bytes'] for row in accepted), members=accepted, new_model_calls=0))
    except BaseException:
        save(out/'failure.json', dict(status='FAILED_MEDIA_BATCH_PRESERVE_PARTIAL_AND_SUCCESSFUL_MEMBERS',
            utc=utc(), video_id=current, accepted_members=accepted, traceback=traceback.format_exc(),
            new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registration')
    main(parser.parse_args().registration)
