"""Immutable direct public-publisher video objects, independent of failed TAR route."""
import argparse
import hashlib
import os
import socket
import traceback
from pathlib import Path
from urllib.parse import urlparse

from stage_common_04 import BASE, check_file, read, save, sha, utc


def main(registration_path):
    if socket.gethostname() != 'inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Registered CPU-only Linux public download required')
    reg_path = Path(registration_path)
    reg = read(reg_path)
    for relative, digest in reg['required_files'].items():
        check_file(BASE/relative, digest)
    routes = read(check_file(BASE/reg['routes_path'], reg['routes_sha256']))
    exclusions = read(BASE/'known_source_exclusions_01.json')
    selected = {row['video_id']: row for row in read(BASE/reg['selection_path'])['selection']}
    out = BASE/reg['output_directory']
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=sha(reg_path)))
    accepted, current = [], None
    try:
        import requests
        session = requests.Session()
        for route in routes:
            vid = current = route['video_id']
            row = selected[vid]
            if row['youtube_id'] in exclusions['youtube_ids']:
                raise ValueError('Known source identity overlap')
            url = urlparse(route['publisher_redirect_url'])
            if url.scheme != 'https' or not url.hostname.endswith('.cdn.hf.co'):
                raise ValueError('Unexpected normal publisher CDN route')
            partial = out/(vid+'.mp4.partial')
            digest, received = hashlib.sha256(), 0
            with session.get(route['publisher_redirect_url'], stream=True, timeout=(10, 45),
                             headers={'Accept-Encoding':'identity', 'If-Match':route['etag']}) as response:
                if response.status_code != 200 or response.headers.get('ETag') != route['etag']:
                    raise ValueError('Pinned direct object unavailable or changed')
                if int(response.headers['Content-Length']) != route['bytes']:
                    raise ValueError('Publisher object size changed')
                with partial.open('xb') as destination:
                    for chunk in response.iter_content(1024 * 1024):
                        if received+len(chunk) > route['bytes']:
                            raise ValueError('Direct object exceeds its registered size')
                        destination.write(chunk)
                        digest.update(chunk)
                        received += len(chunk)
                    destination.flush()
                    os.fsync(destination.fileno())
            if received != route['bytes'] or digest.hexdigest() in exclusions['known_media_sha256']:
                raise ValueError('Incomplete file or known training/test byte overlap')
            final = out/(vid+'.mp4')
            partial.rename(final)
            proof = dict(status='PASS_SELECTED_MEMBER_BYTES_AND_KNOWN_IDENTITY_NOT_NATIVE_ADMISSION',
                video_id=vid, group=row['group'], path=str(final), bytes=received, sha256=digest.hexdigest(),
                publisher_ETag=route['etag'], public_source_url=route['initial_public_url'],
                registration_sha256=sha(reg_path), known_identity_and_whole_file_byte_separation=True,
                original_source_quality_is_publisher_claim_pending_native_measurement=True,
                exact_author_original_byte_identity_verified=False,
                hidden_test_ID_or_subclip_semantic_disjointness_verified=False,
                new_model_calls=0, new_optimizer_updates=0)
            save(out/(vid+'.receipt.json'), proof)
            accepted.append(proof)
            print('Accepted direct source '+vid, flush=True)
        save(out/'completion.json', dict(status='PASS_REGISTERED_LOCATED_MEDIA_BATCH_NOT_ALL20_OR_NATIVE_ADMISSION',
             utc=utc(), registration_sha256=sha(reg_path), sources=len(accepted),
             total_bytes=sum(row['bytes'] for row in accepted), members=accepted, new_model_calls=0))
    except BaseException:
        save(out/'failure.json', dict(status='FAILED_DIRECT_BATCH_KEEP_PARTIAL_AND_SUCCESSFUL_FILES', utc=utc(),
            video_id=current, accepted_members=accepted, traceback=traceback.format_exc(), new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registration')
    main(parser.parse_args().registration)
