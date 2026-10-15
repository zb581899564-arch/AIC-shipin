"""Separately registered relative-deletion first fresh media/native stage.

Never invokes the old media launcher or registration. Download is a single
registered GET without retries; current routes are supplied by the main agent.
This file is only prepared locally until the main agent deploys and invokes it.
"""
import argparse
from bisect import bisect_left
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import traceback
from urllib.parse import urlparse

from reference_common import HOME, checked, read, ref, require, save, validate_gates

ROOT = HOME/'midnight_pair_applicability_20261015_v1'
PASS = 'PASS_MIDNIGHT_PAIR_SHORT_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'


def registration(root):
    reg = read(root/'media_registration.json')
    require(reg['schema'] == 'MIDNIGHT_PAIR_SHORT_MEDIA_REGISTRATION_V1'
        and reg['status'] == 'REGISTERED_MIDNIGHT_PAIR_SHORT_MEDIA_NATIVE'
        and reg['group'] == 'confirm' and reg['expected_accepted_sources'] == 4
        and reg['production_admitted'] is False and reg['windows_video_body_bytes'] == 0,
        'New relative-deletion four-source media registration required')
    for name, digest in reg['required_files'].items():
        checked(dict(path=name, sha256=digest))
    require(reg['required_files'].get(str(Path(__file__).resolve())) == ref(__file__)['sha256'], 'Freeze the new wrapper before media')
    checked(reg['authorization_ref']); protocol = read(checked(reg['protocol_ref'])); validate_gates(protocol)
    selection = read(checked(reg['development_selection_ref'])); result = read(checked(selection['result_ref']))
    require(selection['schema'] == 'MIDNIGHT_DELETE_DEV_SELECTION_V1' and selection['selected_policies'] == ['PAIR_ONLY']
        and selection['confirm_metrics_examined_scope'] == 'THIS_NEW_SHORT_COHORT_ONLY'
        and selection['prior_confirm_metrics_examined'] is True and selection['old_confirm_result_unchanged'] is True and selection['protocol_ref'] == reg['protocol_ref']
        and selection['confirm_metrics_examined'] is False and any(selection['passed_arms'].values())
        and result['group'] == 'dev' and result['passed_arms'] == selection['passed_arms']
        and result['bindings']['protocol_ref'] == reg['protocol_ref'], 'Only actual new relative development PASS permits source acquisition')
    candidates = read(checked(reg['source_candidates_ref'])); rows = candidates['selection']+candidates['ordered_engineering_reserves']
    require(candidates['schema'] == 'MIDNIGHT_FIRST_FRESH_SOURCE_CANDIDATES_V1' and len(rows) == 6
        and len(candidates['selection']) == 4 and candidates['protocol_ref'] == reg['protocol_ref']
        and candidates['development_selection_ref'] == reg['development_selection_ref']
        and len({row['video_id'] for row in rows}) == 6
        and [row['selection_hash'] for row in rows] == sorted(row['selection_hash'] for row in rows)
        and reg['maximum_media_pool_bytes'] == candidates['maximum_pool_bytes'] ==
            sum(row['provider']['size_bytes'] for row in rows), 'Exact new six-pool identity/order/registered budget required')
    require(all(0 < F(row['author_duration_raw']) <= 30 for row in rows), 'All six sources must belong to the author-declared short stratum')
    protected = set(candidates['protected_source_ids']); prohibited = set(candidates['prohibited_media_sha256'])
    require(not protected & {row['video_id'] for row in rows}, 'New sources intersect old/known identity')
    known = read(checked(candidates['known_exclusions_ref']))
    require(set(known['known_media_sha256']) <= prohibited and
        {name if name.startswith('v_') else 'v_'+name for name in known['youtube_ids']} <= protected,
        'Complete known training/test IDs and file bytes remain excluded')
    prior = [read(checked(value)) for value in candidates['prior26_media_receipts']]
    require(len(prior) == len({row['video_id'] for row in prior}) == 26
        and all(row['video_id'] in protected and row['sha256'] in prohibited for row in prior), 'Complete recent26 byte/identity exclusion required')
    for scope in candidates['source_scope_refs']:
        checked(scope)
    helper_path = checked(reg['media_helper_ref'])
    spec = importlib.util.spec_from_file_location('_midnight_frozen_native_media_helpers', helper_path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    require(candidates['annotation_file_ref']['sha256'] == helper.ANNOTATION_SHA
        and candidates['known_exclusions_ref']['sha256'] == helper.KNOWN_SHA, 'Original annotation/known bytes changed')
    routes_doc = read(checked(reg['public_routes_ref'])); routes = {row['video_id']: row for row in routes_doc['routes']}
    require(routes_doc['windows_video_body_bytes'] == 0 and len(routes) == 6
        and set(routes) == {row['video_id'] for row in rows}, 'Exactly six current metadata-only registered routes required')
    for row in rows:
        route = routes[row['video_id']]; provider = row['provider']
        require(row['video_id'] == 'v_'+row['youtube_id'] and provider['video_id'] == row['youtube_id']
            and provider['video_url'] == helper.public_url(row['youtube_id'])
            and route['initial_public_url'] == provider['video_url'] and route['bytes'] == provider['size_bytes']
            and route['metadata_only'] is True and route['status'] in ('PINNED_NORMAL_PUBLIC_REDIRECT', 'PUBLIC_OBJECT_404'),
            'Exact provider URL, byte count and current source route required')
        if route['status'] == 'PINNED_NORMAL_PUBLIC_REDIRECT':
            url = urlparse(route['publisher_redirect_url'])
            require(url.scheme == 'https' and url.hostname and url.hostname.endswith('.cdn.hf.co')
                and url.username is None and url.password is None and url.port in (None, 443) and route['etag'],
                'Normal public HTTPS publisher CDN and exact ETag required')
    return reg, candidates, rows, routes, prohibited, helper


def download_once(folder, row, route, prohibited, transfer, pool):
    """New registered budget; never widen or invoke old positive pool_budget."""
    save(folder/'route.json', route)
    if route['status'] == 'PUBLIC_OBJECT_404':
        return None, 'REGISTERED_PUBLIC_OBJECT_404'
    import requests
    class NoCredentials(requests.auth.AuthBase):
        def __call__(self, request):
            return request
    expected, url, etag = row['provider']['size_bytes'], route['publisher_redirect_url'], route['etag']
    require(shutil.disk_usage(folder).free > expected, 'Insufficient actual capacity for this registered payload')
    digest, size = hashlib.sha256(), 0; partial = folder/'media.mp4.partial'
    with requests.get(url, stream=True, allow_redirects=False, timeout=(10, 45), auth=NoCredentials(),
            headers={'Accept-Encoding': 'identity', 'If-Match': etag}) as response:
        if response.status_code == 404:
            save(folder/'public_404.json', dict(status=404, response_body_read=False))
            return None, 'ACTUAL_PUBLIC_OBJECT_404'
        actual = urlparse(response.url); target = urlparse(url)
        require(response.status_code == 200 and response.headers.get('ETag') == etag
            and int(response.headers['Content-Length']) == expected
            and response.headers.get('Content-Encoding') in (None, 'identity')
            and (actual.scheme, actual.hostname, actual.path) == (target.scheme, target.hostname, target.path),
            'Current public version/network failure: stop without source replacement')
        with partial.open('xb') as stream:
            for block in response.iter_content(1 << 20):
                size += len(block); transfer['actual_new_media_payload_bytes'] += len(block)
                require(size <= expected and transfer['actual_new_media_payload_bytes'] <= pool, 'Registered payload budget exceeded')
                stream.write(block); digest.update(block)
            stream.flush(); os.fsync(stream.fileno())
    require(size == expected and digest.hexdigest() not in prohibited, 'Incomplete or known/old/new byte-overlapping media; retain partial and stop')
    final = folder/'media.mp4'; partial.rename(final)
    receipt = dict(video_id=row['video_id'], path=str(final), bytes=size, sha256=digest.hexdigest(),
        public_url=row['provider']['video_url'], group='confirm', original_author_byte_identity_verified=False,
        known_ID_and_byte_separation=True, hidden_alias_or_semantic_overlap='UNKNOWN')
    save(folder/'media_receipt.json', receipt)
    return receipt, None


def validate_domain(clock, reference, rejection_type):
    points = list(map(F, clock['original_exact_pts'])); end = F(clock['physical_end_exact'])
    if not (points and points[0] == 0 and len(points) == clock['native_frames']
        and points == sorted(set(points)) and F(clock['first_original_pts_exact']) == 0
        and clock['original_zero_origin_verified'] is True and clock['timeline_shift_applied'] is False
        and F(clock['last_frame_duration_exact']) > 0 and end == points[-1]+F(clock['last_frame_duration_exact'])):
        raise rejection_type('ORIGINAL_NATIVE_ORIGIN_OR_PHYSICAL_END_INVALID')
    if not all(0 <= F(a) < F(b) <= end for spans in reference['annotator_intervals_exact_seconds'] for a, b in spans):
        raise rejection_type('UNMODIFIED_REFERENCE_OUTSIDE_NATIVE_DOMAIN')
    if not (0 < end <= 30):
        raise rejection_type('ORIGINAL_PHYSICAL_END_OUTSIDE_PREDECLARED_SHORT_STRATUM')
    count = (end.numerator+30*end.denominator-1)//(30*end.denominator)
    if any(bisect_left(points, end*(i+1)/count)-bisect_left(points, end*i/count) < 64 for i in range(count)):
        raise rejection_type('FEWER_THAN64_NATIVE_FRAMES_IN_REGISTERED_BASELINE_VIEW')


def main(root):
    root = root.resolve()
    require(root == ROOT and Path(__file__).resolve().is_relative_to(root) and sys.platform == 'linux'
        and socket.gethostname() == 'inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'Exact independent Linux relative-confirm root and CPU process required')
    reg, candidates, rows, routes, prohibited, helper = registration(root)
    annotation_path = checked(candidates['annotation_file_ref'])
    wanted = {row['video_id'] for row in rows}
    raw_all = json.loads(annotation_path.read_text(encoding='utf-8-sig'), parse_float=Decimal, object_pairs_hook=helper.unique_object)
    raw = {row['video_id']: row for row in raw_all if row['video_id'] in wanted}; del raw_all
    require(set(raw) == wanted, 'All original registered author reference rows required')
    output = root/'reference_01'; output.mkdir(exist_ok=False)
    save(output/'launch_claim.json', dict(pid=os.getpid(), media_registration_ref=ref(root/'media_registration.json'),
        maximum_media_pool_bytes=reg['maximum_media_pool_bytes'], CPU_only=True, actual_new_model_calls=0))
    accepted, rejected, current, reserved, reserve_index, measured = [], [], None, 0, 4, 0
    transfer = dict(actual_new_media_payload_bytes=0)
    try:
        native04, native01 = helper.native_helpers(); import av
        for slot, initial in enumerate(rows[:4]):
            row = initial
            while True:
                current = row['video_id']; folder = output/current; folder.mkdir(exist_ok=False)
                reserved += row['provider']['size_bytes']
                require(reserved <= reg['maximum_media_pool_bytes'], 'Frozen six-pool cannot expand')
                receipt, reason = download_once(folder, row, routes[current], prohibited, transfer, reg['maximum_media_pool_bytes'])
                rejection = None
                if receipt is None:
                    rejection = dict(video_id=current, reason=reason, downloaded=False, no_model_or_quality_observed=True)
                else:
                    prohibited.add(receipt['sha256']); measured += 1
                    try:
                        clock = native04.measure_original_video(receipt['path'], av)
                    except ValueError as error:
                        if str(error) not in helper.NATIVE_MEASUREMENT_REJECTIONS:
                            raise
                        rejection = dict(video_id=current, reason='EXPLICIT_ORIGINAL_NATIVE_DOMAIN_REJECTED', error=str(error), no_model_or_quality_observed=True)
                    if rejection is None:
                        save(folder/'clock.json', clock); reference = helper.original_reference(raw[current]); save(folder/'reference.json', reference)
                        try:
                            validate_domain(clock, reference, helper.NativeDomainRejected)
                        except helper.NativeDomainRejected as error:
                            rejection = dict(video_id=current, reason='EXPLICIT_ORIGINAL_REFERENCE_NATIVE_DOMAIN_REJECTED',
                                error=str(error), no_model_or_quality_observed=True, original_endpoints_changed=False)
                        if rejection is None:
                            native04.validate_original_origin(clock); native01.native64_windows(clock)
                if rejection is not None:
                    rejected.append(rejection); save(folder/'rejected.json', rejection)
                    require(reserve_index < len(rows), 'No preregistered engineering reserve remains')
                    row = rows[reserve_index]; reserve_index += 1; continue
                accepted.append(dict(video_id=current, slot=slot, group='confirm', media=receipt,
                    clock_path=str(folder/'clock.json'), clock_sha256=ref(folder/'clock.json')['sha256'],
                    reference_path=str(folder/'reference.json'), reference_sha256=ref(folder/'reference.json')['sha256']))
                save(output/('accepted_slot_%02d.json'%slot), accepted[-1]); print('ACCEPTED_MEDIA_NATIVE', current, flush=True); break
        require(len(accepted) == len({row['video_id'] for row in accepted}) == 4, 'Complete new four-source native admission required')
        save(output/'completion.json', dict(status=PASS, group='confirm', accepted=accepted, rejected=rejected,
            source_registration_ref=ref(root/'media_registration.json'), source_candidates_ref=reg['source_candidates_ref'],
            dev_selection_ref=reg['development_selection_ref'], protocol_ref=reg['protocol_ref'],
            reserved_bytes_counted=reserved, actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],
            maximum_media_pool_bytes=reg['maximum_media_pool_bytes'], prior_actual_media_count=26,
            native_clock_measurements_started=measured, original_labels_unmodified=True,
            reference_scope=helper.SCOPE, windows_video_body_bytes=0, successful_media_and_clocks_repeated=0,
            actual_new_model_calls=0, new_RGB_or_processor_calls=0, CPU_only=True, GPU_admitted=False, production_admitted=False))
        save(root/'reference_completion_confirm.json', ref(output/'completion.json'))
    except BaseException as error:
        message, trace = repr(error), traceback.format_exc()
        for route in routes.values():
            if route.get('publisher_redirect_url'):
                message = message.replace(route['publisher_redirect_url'], '<PUBLISHER_CDN>')
                trace = trace.replace(route['publisher_redirect_url'], '<PUBLISHER_CDN>')
        save(output/'failure.json', dict(current=current, accepted=accepted, rejected=rejected, error=message,
            traceback=trace, actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],
            implicit_resume=False, successful_media_and_clocks_must_not_repeat=True, actual_new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
