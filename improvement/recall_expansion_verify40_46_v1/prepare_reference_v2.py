"""First media/clock preparation for the frozen external proxy, CPU only.

Successful downloads and clocks are separate immutable artifacts. No retry,
label-based replacement, RGB encode, model call or implicit production admission.
"""
import argparse
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import traceback
from urllib.parse import urlparse
from stage_io import checked, read, require, save, sha, utc


def original_reference(raw):
    events = raw['vsum']
    require(bool(events) and isinstance(events[0], list), 'Original human summaries missing')
    count = len(events[0])
    require(count >= 2 and all(len(event) == count for event in events), 'Inconsistent all-rater denominator')
    references = [[] for _ in range(count)]
    for event in events:
        for index, span in enumerate(event):
            require(len(span) == 2 and F(str(span[0])) < F(str(span[1])), 'Invalid original span')
            references[index].append([str(span[0]), str(span[1])])
    # Author labels remain seconds. The one-second visualization is not native GT.
    return dict(video_id=raw['video_id'], annotator_count=count,
                annotator_intervals_exact_seconds=references, text_available_to_model=False,
                original_labels_unmodified=True, label_semantics='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY')


def download(root, row, known, registered_routes):
    import requests
    vid = row['video_id']
    expected = row['provider']['size_bytes']
    url = row['provider']['video_url']
    require(url == 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+row['youtube_id']+'.mp4',
            'Unregistered public media route')
    registered = registered_routes[vid]
    require(registered['initial_public_url'] == url and registered['bytes'] == expected, 'Source route/bytes changed')
    if registered['status'] == 'PUBLIC_OBJECT_404':
        return None
    require(registered['status'] == 'PINNED_NORMAL_PUBLIC_REDIRECT', 'Failed metadata route')
    redirect_url = registered['publisher_redirect_url']; final = urlparse(redirect_url)
    require(final.scheme == 'https' and final.hostname.endswith('.cdn.hf.co'), 'Unexpected public CDN route')
    etag = registered['etag']
    route = dict(video_id=vid, initial_public_url=url, bytes=expected, etag=etag, utc=utc())
    save(root/'route.json', route)
    require(shutil.disk_usage(root).free > 2*expected, 'Actual media/partial capacity insufficient')
    partial = root/'media.mp4.partial'; digest = hashlib.sha256(); size = 0
    with requests.get(redirect_url, stream=True, timeout=(10, 45),
                      headers={'Accept-Encoding': 'identity', 'If-Match': etag}) as body:
        require(body.status_code == 200 and body.headers.get('ETag') == etag and
                int(body.headers['Content-Length']) == expected, 'Actual public object version differs')
        with partial.open('xb') as stream:
            for chunk in body.iter_content(1 << 20):
                size += len(chunk); require(size <= expected, 'Media payload exceeds fixed size')
                stream.write(chunk); digest.update(chunk)
            stream.flush(); os.fsync(stream.fileno())
    require(size == expected and digest.hexdigest() not in set(known['known_media_sha256']),
            'Incomplete media or known byte overlap')
    final_path = root/'media.mp4'; partial.rename(final_path)
    receipt = dict(video_id=vid, path=str(final_path), bytes=size, sha256=digest.hexdigest(),
                   public_url=url, group=row['group'], utc=utc(), original_author_byte_identity_verified=False,
                   known_ID_and_byte_separation=True, hidden_alias_or_semantic_overlap='UNKNOWN')
    save(root/'media_receipt.json', receipt)
    return receipt


def main(root, group):
    require(socket.gethostname() == 'inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only native preparation')
    registry = read(root/'new8_source_registration_01.json')
    protocol = read(root/'protocol.json')
    route_ref = read(root/'dev_media_recovery_02.json')
    require(group == 'dev' and route_ref['old_stage_failed_without_successful_media'] is True, 'Only registered dev network recovery')
    registered_routes = {x['video_id']:x for x in read(checked(root/route_ref['routes_path'], route_ref['routes_sha256']))['routes']}
    require(protocol['reference_scope'] == 'EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NO_QUERY_TO_MODEL', 'Reference scope changed')
    if group == 'confirm':
        selection = read(root/'dev/selection_before_confirmation.json')
        require(selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION', 'No development selection')
    raw_path = checked(registry['annotation_file_path'], registry['annotation_file_sha256'])
    raw = {row['video_id']: row for row in json.loads(raw_path.read_text(), parse_float=Decimal)}
    known = read(checked(registry['known_exclusions_path'], registry['known_exclusions_sha256']))
    excluded = {('v_'+name if not name.startswith('v_') else name) for name in known['youtube_ids']}
    excluded.update(registry['old_exposed_and_reserved_ids'])
    output = root/group/'reference_02'; output.mkdir(parents=True, exist_ok=False)
    save(output/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), source_registration_sha256=sha(root/'new8_source_registration_01.json')))
    sys.path.insert(0, '/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/code')
    from native_profile_04 import measure_original_video, validate_original_origin
    import av
    selected = [row for row in registry['selection'] if row['group'] == group]
    reserves = iter(row for row in registry['ordered_engineering_reserves'] if row['group'] == group)
    accepted, rejected, current, payload = [], [], None, 0
    try:
        for slot, initial in enumerate(selected):
            row = initial
            while True:
                current = row['video_id']; require(current not in excluded, 'Known identity/exposure overlap')
                folder = output/current; folder.mkdir(exist_ok=False)
                payload += row['provider']['size_bytes']
                require(payload <= protocol['maximum_media_pool_bytes'], 'Registered media budget exceeded')
                receipt = download(folder, row, known, registered_routes)
                if receipt is None:
                    rejected.append(dict(video_id=current, reason='REGISTERED_PUBLIC_OBJECT_404', downloaded=False))
                    save(folder/'source_rejection.json', rejected[-1]); row = next(reserves); continue
                clock = measure_original_video(receipt['path'], av)
                save(folder/'clock.json', clock)
                reference = original_reference(raw[current]); save(folder/'reference.json', reference)
                try:
                    validate_original_origin(clock)
                    end = F(clock['physical_end_exact'])
                    require(all(0 <= F(a) < F(b) <= end for spans in reference['annotator_intervals_exact_seconds'] for a,b in spans),
                            'UNMODIFIED_REFERENCE_OUTSIDE_NATIVE_DOMAIN')
                except ValueError as error:
                    rejected.append(dict(video_id=current, reason=str(error), media_receipt_sha256=sha(folder/'media_receipt.json'),
                                         clock_sha256=sha(folder/'clock.json'), no_model_or_quality_observed=True))
                    save(folder/'source_rejection.json', rejected[-1]); row = next(reserves); continue
                accepted.append(dict(video_id=current, slot=slot, group=group, media=receipt,
                    clock_path=str(folder/'clock.json'), clock_sha256=sha(folder/'clock.json'),
                    reference_path=str(folder/'reference.json'), reference_sha256=sha(folder/'reference.json')))
                save(output/('accepted_slot_%02d.json'%slot), accepted[-1]); print('Accepted media/native reference '+current, flush=True)
                break
        require(len(accepted) == protocol['sources_per_group'] and len({x['video_id'] for x in accepted}) == len(accepted), 'Complete fixed group required')
        save(output/'completion.json', dict(status='PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU',
            group=group, accepted=accepted, rejected=rejected, reserved_bytes_counted=payload, utc=utc(),
            registration_sha256=sha(root/'new8_source_registration_01.json'), actual_new_model_calls=0))
        save(root/('reference_completion_'+group+'.json'), dict(path=str(output/'completion.json'),sha256=sha(output/'completion.json')))
    except BaseException:
        save(output/'failure.json', dict(current=current, accepted=accepted, rejected=rejected, traceback=traceback.format_exc(),
             successful_media_and_clocks_must_not_repeat=True, actual_new_model_calls=0))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True); parser.add_argument('--group', choices=['dev','confirm'], required=True)
    args=parser.parse_args(); main(args.root, args.group)
