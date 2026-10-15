"""First confirm media/clock preparation after the frozen actual dev PASS.

No HEAD, Windows media body, implicit recovery, model, RGB/processor input or
quality selection is performed here. Original author seconds remain unchanged.
The registration schema is described by REGISTRATION_FIELDS below.
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

from stage_io import HOME, checked, read, require, save, sha, utc

REG_STATUS = 'REGISTERED_FIRST_CONFIRM_REFERENCE_MEDIA_V3'
REFERENCE_STATUS = 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU'
MAXIMUM_MEDIA_POOL_BYTES = 104730788
NATIVE_CODE = HOME/'videoxum_reference_iteration_20261013_v1/code'
REGISTRATION_FIELDS = {
    'status': REG_STATUS, 'group': 'confirm', 'route_acquisition_method': 'HEAD',
    'windows_video_body_bytes': 0, 'maximum_media_pool_bytes': MAXIMUM_MEDIA_POOL_BYTES,
    'expected_existing_dev_media_count': 6, 'existing_dev_media_bytes': 'actual six receipt total',
    'source_registration_ref': 'root/new8_source_registration_01.json path+sha256',
    'protocol_ref': 'root/protocol.json path+sha256',
    'development_selection_ref': 'root/dev/selection_before_confirmation.json path+sha256',
    'development_result_ref': 'root/dev/comparison_01/result.json path+sha256',
    'dev_reference_pointer_ref': 'root/reference_completion_dev.json path+sha256',
    'dev_reference_completion_ref': 'root/dev/reference_02/completion.json path+sha256',
    'public_routes_ref': 'root/confirm_public_routes_03.json path+sha256',
    'selected_confirm_ids': 'exact four original registered IDs, in order',
    'ordered_confirm_engineering_reserve_ids': 'exact four same-group reserves, in order',
    'required_code_files': 'absolute implementation path -> sha256; this file, stage_io, native_profile_01+04',
}


def fixed_candidates(registry):
    selected = [row for row in registry['selection'] if row['group'] == 'confirm']
    reserves = [row for row in registry['ordered_engineering_reserves'] if row['group'] == 'confirm']
    ids = [row['video_id'] for row in selected+reserves]
    require(len(selected) == len(reserves) == 4 and len(set(ids)) == 8, 'Exact four confirm sources and four ordered same-group reserves required')
    for row in selected+reserves:
        require(row['video_id'] == 'v_'+row['youtube_id'] and row['provider']['video_id'] == row['youtube_id'] and
            type(row['provider']['size_bytes']) is int and row['provider']['size_bytes'] > 0,
            'Original registered media identity/size changed')
    return selected, reserves


def validate_dev_pass(selection, result, protocol_sha, result_sha):
    require(selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and
        selection['protocol_sha256'] == protocol_sha and selection['result_sha256'] == result_sha and
        selection['candidate'] == 'OVERLAP15_STRIDE7_5_EXPLICIT_KEEP_ONLY' and selection['confirm_metrics_examined'] is False,
        'Frozen actual dev selection/protocol/result binding required before first confirmation')
    expected = {'full_group', 'macro_F1_not_lower', 'macro_recall_gain', 'every_source_loss_within_gate',
                'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources'}
    require(result['status'] == 'PASS_REGISTERED_PROXY_GROUP_PENDING_FIXED_FACT_GATE' and result['group'] == 'dev' and
        result['bindings']['protocol_sha256'] == protocol_sha and set(result['conditions']) == expected and
        all(value is True for value in result['conditions'].values()) and len(result['cases']) == 4 and
        len({row['video_id'] for row in result['cases']}) == 4 and result['old_failed_gates_changed'] is False,
        'The actual stored complete dev comparison must pass every original condition')


def validate_routes(document, candidates):
    require(document['windows_video_body_bytes'] == 0 and len(document['routes']) == len(candidates), 'HEAD-only complete confirm metadata required')
    routes = {row['video_id']: row for row in document['routes']}
    require(len(routes) == len(candidates) and set(routes) == {row['video_id'] for row in candidates}, 'No duplicate, missing or cross-group public route')
    for row in candidates:
        route = routes[row['video_id']]
        url = 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+row['youtube_id']+'.mp4'
        require(row['provider']['video_url'] == route['initial_public_url'] == url and
            route['bytes'] == row['provider']['size_bytes'] and route['metadata_only'] is True,
            'Original publisher URL/registered byte count/metadata-only scope changed')
        require(route['status'] in ('PINNED_NORMAL_PUBLIC_REDIRECT', 'PUBLIC_OBJECT_404'), 'Network/metadata failure cannot replace a source')
        if route['status'] == 'PINNED_NORMAL_PUBLIC_REDIRECT':
            target = urlparse(route['publisher_redirect_url'])
            require(target.scheme == 'https' and target.hostname and target.hostname.endswith('.cdn.hf.co') and
                target.username is None and target.password is None and target.port in (None, 443) and
                isinstance(route['etag'], str) and bool(route['etag']), 'Pinned original public CDN domain/ETag required')
    return routes


def pool_budget(existing_bytes, new_reserved_bytes, maximum=MAXIMUM_MEDIA_POOL_BYTES):
    require(type(existing_bytes) is int and type(new_reserved_bytes) is int and existing_bytes >= 0 and new_reserved_bytes >= 0 and
        maximum == MAXIMUM_MEDIA_POOL_BYTES and existing_bytes+new_reserved_bytes <= maximum,
        'Frozen global media pool budget includes all prior actual dev bytes')
    return existing_bytes+new_reserved_bytes


def registration(root):
    path = root/'confirm_media_registration_03.json'
    reg = read(path)
    require(reg['status'] == REG_STATUS and reg['group'] == 'confirm' and reg['route_acquisition_method'] == 'HEAD' and
        reg['windows_video_body_bytes'] == 0 and reg['maximum_media_pool_bytes'] == MAXIMUM_MEDIA_POOL_BYTES and
        reg['expected_existing_dev_media_count'] == 6, 'Explicit first-confirm metadata/media registration required')
    expected = dict(source_registration_ref=root/'new8_source_registration_01.json', protocol_ref=root/'protocol.json',
        development_selection_ref=root/'dev/selection_before_confirmation.json', development_result_ref=root/'dev/comparison_01/result.json',
        dev_reference_pointer_ref=root/'reference_completion_dev.json', dev_reference_completion_ref=root/'dev/reference_02/completion.json',
        public_routes_ref=root/'confirm_public_routes_03.json')
    refs = {}
    for name, canonical in expected.items():
        ref = reg[name]
        refs[name] = checked(ref['path'], ref['sha256'])
        require(refs[name] == canonical, 'Confirm registration points at another stage: '+name)
    required = {str(Path(__file__).resolve()), str(Path(__file__).parent/'stage_io.py'),
                str(NATIVE_CODE/'native_profile_01.py'), str(NATIVE_CODE/'native_profile_04.py')}
    require(required <= set(reg['required_code_files']), 'New implementation and original clock helpers must be frozen')
    for filename, digest in reg['required_code_files'].items():
        checked(filename, digest)
    registry, protocol = read(refs['source_registration_ref']), read(refs['protocol_ref'])
    require(registry['status'] == 'FROZEN_EXTERNAL_PROXY_IDENTITIES_BEFORE_MEDIA_MODEL_OR_METRIC_NOT_CPU_ADMISSION' and
        registry['maximum_pool_bytes'] == protocol['maximum_media_pool_bytes'] == MAXIMUM_MEDIA_POOL_BYTES and
        protocol['sources_per_group'] == 4 and protocol['reference_scope'] == 'EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NO_QUERY_TO_MODEL' and
        protocol['confirmation_before_dev_pass'] is False and protocol['labels_available_to_model'] is False,
        'Frozen original source/proxy/budget protocol changed')
    result = read(refs['development_result_ref'])
    validate_dev_pass(read(refs['development_selection_ref']), result,
                      reg['protocol_ref']['sha256'], reg['development_result_ref']['sha256'])
    checked(root/'cpu_acceptance_dev.json', result['bindings']['cpu_acceptance_sha256'])
    checked(root/'dev/VERIFY/verification_export.json', result['bindings']['verification_export_sha256'])
    selected, reserves = fixed_candidates(registry)
    require(reg['selected_confirm_ids'] == [row['video_id'] for row in selected] and
        reg['ordered_confirm_engineering_reserve_ids'] == [row['video_id'] for row in reserves], 'Original source/reserve order changed')
    routes = validate_routes(read(refs['public_routes_ref']), selected+reserves)
    return reg, registry, protocol, selected, reserves, routes, refs, path


def prior_dev_usage(root, reg, registry, refs):
    pointer, complete = read(refs['dev_reference_pointer_ref']), read(refs['dev_reference_completion_ref'])
    dev = root/'dev/reference_02'
    require(pointer['path'] == str(refs['dev_reference_completion_ref']) and pointer['sha256'] == reg['dev_reference_completion_ref']['sha256'] and
        complete['status'] == REFERENCE_STATUS and complete['group'] == 'dev' and len(complete['accepted']) == 4 and
        complete['registration_sha256'] == reg['source_registration_ref']['sha256'], 'Existing actual dev media completion/pointer required')
    accepted = {row['video_id']: row for row in complete['accepted']}
    rejected = {row['video_id']: row for row in complete['rejected']}
    require(len(accepted) == 4 and len(rejected) == len(complete['rejected']) and not (set(accepted) & set(rejected)), 'Duplicate prior media terminal source')
    require({row['video_id'] for row in read(refs['development_result_ref'])['cases']} == set(accepted),
            'Stored development PASS must use the exact accepted original dev source denominator')
    candidates = {row['video_id']: row for row in registry['selection']+registry['ordered_engineering_reserves'] if row['group'] == 'dev'}
    receipts, total, hashes = [], 0, set()
    for receipt_path in sorted(dev.glob('*/media_receipt.json')):
        receipt = read(receipt_path)
        vid = receipt['video_id']
        require(vid in candidates and receipt_path.parent == dev/vid and receipt['group'] == 'dev' and
            vid in set(accepted) | set(rejected) and receipt['bytes'] == candidates[vid]['provider']['size_bytes'] and
            receipt['public_url'] == candidates[vid]['provider']['video_url'] and receipt['known_ID_and_byte_separation'] is True,
            'Existing media must be an exact original completed dev-stage artifact')
        media_path = checked(receipt['path'], receipt['sha256'])
        require(media_path == dev/vid/'media.mp4' and media_path.stat().st_size == receipt['bytes'] and receipt['sha256'] not in hashes,
            'Actual prior media size/hash/path differs or duplicates another source')
        clock_path = dev/vid/'clock.json'
        if vid in accepted:
            row = accepted[vid]
            require(row['media'] == receipt and row['clock_path'] == str(clock_path), 'Prior accepted receipt/clock changed')
            checked(clock_path, row['clock_sha256'])
        else:
            rejection = rejected[vid]
            require(rejection['media_receipt_sha256'] == sha(receipt_path), 'Prior rejected successful media receipt changed')
            checked(clock_path, rejection['clock_sha256'])
        total += receipt['bytes']; hashes.add(receipt['sha256'])
        receipts.append(dict(video_id=vid, receipt_path=str(receipt_path), receipt_sha256=sha(receipt_path),
                             bytes=receipt['bytes'], media_sha256=receipt['sha256']))
    expected_media = set(accepted) | {vid for vid, row in rejected.items() if 'media_receipt_sha256' in row}
    require(len(receipts) == reg['expected_existing_dev_media_count'] == 6 and
        {row['video_id'] for row in receipts} == expected_media and total == reg['existing_dev_media_bytes'],
        'Global budget must bind the six actual prior dev media, including native-domain rejections')
    pool_budget(total, 0)
    return dict(actual_media_count=len(receipts), actual_media_bytes=total, media=receipts), hashes


def original_reference(raw):
    events = raw['vsum']
    require(bool(events) and isinstance(events[0], list), 'Original human summaries missing')
    count = len(events[0])
    require(count >= 2 and all(len(event) == count for event in events), 'Inconsistent original all-rater denominator')
    references = [[] for _ in range(count)]
    for event in events:
        for index, span in enumerate(event):
            require(len(span) == 2 and F(str(span[0])) < F(str(span[1])), 'Invalid original human span')
            references[index].append([str(span[0]), str(span[1])])
    return dict(video_id=raw['video_id'], annotator_count=count, annotator_intervals_exact_seconds=references,
        text_available_to_model=False, original_labels_unmodified=True, label_semantics='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY')


def validate_reference_domain(clock, reference):
    end = F(clock['physical_end_exact'])
    require(all(0 <= F(first) < F(last) <= end for spans in reference['annotator_intervals_exact_seconds'] for first, last in spans),
            'UNMODIFIED_REFERENCE_OUTSIDE_NATIVE_DOMAIN')


def download(folder, row, route, prohibited_hashes, transfer, existing_bytes):
    import requests
    expected = row['provider']['size_bytes']
    if route['status'] == 'PUBLIC_OBJECT_404':
        return None
    url, etag = route['publisher_redirect_url'], route['etag']
    save(folder/'route.json', dict(video_id=row['video_id'], initial_public_url=route['initial_public_url'],
        publisher_redirect_url=url, bytes=expected, etag=etag, metadata_only=True, metadata_method='HEAD', utc=utc()))
    require(shutil.disk_usage(folder).free > 2*expected, 'Actual media/partial capacity insufficient; no source replacement')
    partial = folder/'media.mp4.partial'; digest, size = hashlib.sha256(), 0
    # No HEAD/retry/automatic redirect. A stale signed CDN route stops with all
    # successful media/clock artifacts retained for explicit future handling.
    with requests.get(url, stream=True, allow_redirects=False, timeout=(10, 45),
        headers={'Accept-Encoding': 'identity', 'If-Match': etag}) as body:
        require(body.status_code == 200 and body.headers.get('ETag') == etag and
            int(body.headers['Content-Length']) == expected and body.headers.get('Content-Encoding') in (None, 'identity') and
            urlparse(body.url).hostname == urlparse(url).hostname, 'Actual public CDN object/version differs; no source replacement')
        with partial.open('xb') as stream:
            for chunk in body.iter_content(1 << 20):
                size += len(chunk); transfer['actual_new_media_payload_bytes'] += len(chunk)
                require(size <= expected, 'New media payload exceeds pinned object size')
                pool_budget(existing_bytes, transfer['actual_new_media_payload_bytes'])
                stream.write(chunk); digest.update(chunk)
            stream.flush(); os.fsync(stream.fileno())
    require(size == expected and digest.hexdigest() not in prohibited_hashes, 'Incomplete media or known/dev/new byte overlap; no replacement')
    final = folder/'media.mp4'; partial.rename(final)
    receipt = dict(video_id=row['video_id'], path=str(final), bytes=size, sha256=digest.hexdigest(),
        public_url=row['provider']['video_url'], group='confirm', utc=utc(), original_author_byte_identity_verified=False,
        known_ID_and_byte_separation=True, hidden_alias_or_semantic_overlap='UNKNOWN')
    save(folder/'media_receipt.json', receipt)
    return receipt


def main(root, group='confirm'):
    require(group == 'confirm' and sys.platform == 'linux' and socket.gethostname() == 'inspur-NP5570M5' and
        os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only first confirm preparation on existing CPU-only Linux host is admitted')
    root = Path(root).resolve()
    require(root.is_relative_to(HOME) and root != HOME, 'Independent project root required')
    require(not (root/'reference_completion_confirm.json').exists() and not list((root/'confirm').glob('reference_*')),
        'Confirm media/clock stages must never implicitly resume or repeat successful artifacts')
    reg, registry, protocol, selected, reserves, routes, refs, reg_path = registration(root)
    prior, dev_hashes = prior_dev_usage(root, reg, registry, refs)
    pool_budget(prior['actual_media_bytes'], sum(row['provider']['size_bytes'] for row in selected+reserves))
    annotation_path = checked(registry['annotation_file_path'], registry['annotation_file_sha256'])
    known = read(checked(registry['known_exclusions_path'], registry['known_exclusions_sha256']))
    excluded = {('v_'+name if not name.startswith('v_') else name) for name in known['youtube_ids']}
    excluded.update(registry['old_exposed_and_reserved_ids']); excluded.update(row['video_id'] for row in prior['media'])
    require(not ({row['video_id'] for row in selected+reserves} & excluded), 'Confirm source intersects known/dev identity exclusions')
    # Reuse the already-resident original author file. Only attempted fixed
    # confirm sources' vsum is extracted below; text is never output to inference.
    raw_rows = json.loads(annotation_path.read_text(encoding='utf-8'), parse_float=Decimal)
    wanted = {row['video_id'] for row in selected+reserves}
    raw = {row['video_id']: dict(video_id=row['video_id'], vsum=row['vsum']) for row in raw_rows if row['video_id'] in wanted}
    require(set(raw) == wanted, 'Exact registered confirm author rows missing')
    del raw_rows
    output = root/'confirm/reference_03'; output.mkdir(parents=True, exist_ok=False)
    save(output/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), group=group,
        source_registration_sha256=sha(refs['source_registration_ref']), confirm_media_registration_sha256=sha(reg_path),
        development_selection_sha256=sha(refs['development_selection_ref']), development_result_sha256=sha(refs['development_result_ref']),
        prior_actual_dev_media_bytes=prior['actual_media_bytes'], windows_video_body_bytes=0, actual_new_model_calls=0))
    save(output/'prior_dev_media_budget.json', prior)
    accepted, rejected, current, reserved = [], [], None, 0
    transfer = dict(actual_new_media_payload_bytes=0)
    prohibited_hashes = set(known['known_media_sha256']) | dev_hashes
    reserve_position = 0
    try:
        sys.path.insert(0, str(NATIVE_CODE))
        from native_profile_04 import measure_original_video, validate_original_origin
        import av
        for slot, initial in enumerate(selected):
            row = initial
            while True:
                current = row['video_id']; folder = output/current; folder.mkdir(exist_ok=False)
                reserved += row['provider']['size_bytes']; pool_budget(prior['actual_media_bytes'], reserved)
                receipt = download(folder, row, routes[current], prohibited_hashes, transfer, prior['actual_media_bytes'])
                rejection = None
                if receipt is None:
                    rejection = dict(video_id=current, reason='REGISTERED_PUBLIC_OBJECT_404', downloaded=False,
                        no_model_or_quality_observed=True)
                else:
                    prohibited_hashes.add(receipt['sha256'])
                    try:
                        clock = measure_original_video(receipt['path'], av)
                    except (ValueError, av.error.InvalidDataError) as error:
                        rejection = dict(video_id=current, reason='ACTUAL_ORIGINAL_NATIVE_MEASUREMENT_REJECTED',
                            error=repr(error), media_receipt_sha256=sha(folder/'media_receipt.json'), no_model_or_quality_observed=True)
                    if rejection is None:
                        save(folder/'clock.json', clock)
                        reference = original_reference(raw[current]); save(folder/'reference.json', reference)
                        try:
                            validate_original_origin(clock); validate_reference_domain(clock, reference)
                        except ValueError as error:
                            rejection = dict(video_id=current, reason=str(error), media_receipt_sha256=sha(folder/'media_receipt.json'),
                                clock_sha256=sha(folder/'clock.json'), reference_sha256=sha(folder/'reference.json'),
                                no_model_or_quality_observed=True, original_endpoints_changed=False)
                if rejection is not None:
                    rejected.append(rejection); save(folder/'source_rejection.json', rejection)
                    require(reserve_position < len(reserves), 'Fixed confirm engineering reserve order exhausted; do not broaden the source pool')
                    row = reserves[reserve_position]; reserve_position += 1
                    continue
                accepted.append(dict(video_id=current, slot=slot, group=group, media=receipt,
                    clock_path=str(folder/'clock.json'), clock_sha256=sha(folder/'clock.json'),
                    reference_path=str(folder/'reference.json'), reference_sha256=sha(folder/'reference.json')))
                save(output/('accepted_slot_%02d.json'%slot), accepted[-1])
                print('Accepted first confirm media/native reference '+current, flush=True)
                break
        require(len(accepted) == 4 and len({row['video_id'] for row in accepted}) == 4, 'Complete fixed confirmation denominator required')
        save(output/'completion.json', dict(status=REFERENCE_STATUS, group=group, accepted=accepted, rejected=rejected,
            reserved_bytes_counted=reserved, actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],
            prior_actual_dev_media_bytes=prior['actual_media_bytes'], global_actual_media_payload_bytes=prior['actual_media_bytes']+transfer['actual_new_media_payload_bytes'],
            global_reserved_media_bytes=pool_budget(prior['actual_media_bytes'], reserved), utc=utc(),
            registration_sha256=sha(refs['source_registration_ref']), confirm_media_registration_sha256=sha(reg_path),
            development_selection_sha256=sha(refs['development_selection_ref']), development_result_sha256=sha(refs['development_result_ref']),
            original_labels_unmodified=True, windows_video_body_bytes=0, original_annotation_downloads_repeated=0,
            successful_media_and_clocks_repeated=0, actual_new_model_calls=0))
        save(root/'reference_completion_confirm.json', dict(path=str(output/'completion.json'), sha256=sha(output/'completion.json')))
    except BaseException:
        save(output/'failure.json', dict(current=current, accepted=accepted, rejected=rejected, traceback=traceback.format_exc(),
            reserved_bytes_counted=reserved, prior_actual_dev_media_bytes=prior['actual_media_bytes'],
            actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'], successful_media_and_clocks_must_not_repeat=True,
            implicit_resume=False, source_pool_or_original_endpoints_must_not_change=True, actual_new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=('confirm',), default='confirm')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main(args.root, args.group)
