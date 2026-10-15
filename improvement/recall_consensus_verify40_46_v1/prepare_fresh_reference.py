"""First fresh4 confirmation media/native reference; no implicit recovery.

Import is stdlib-only. Network and the original native-clock decoder are used
only by the explicitly launched Linux CPU main(), never by registration or
pure checks. No HEAD, RGB/processor/model work or quality selection occurs.
"""
import argparse
from bisect import bisect_left
import datetime as dt
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import traceback
from urllib.parse import urlparse

sys.dont_write_bytecode = True
HOME = Path('/home/inspur/aic_video_work')
ROOT = HOME/'recall_consensus_verify40_46_20261015_v1'
OLD = HOME/'recall_expansion_verify40_46_20261014_v1'
NATIVE_CODE = HOME/'videoxum_reference_iteration_20261013_v1/code'
REG_SCHEMA = 'RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1'
REG_STATUS = 'REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE'
REFERENCE_STATUS = 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU'
PROTOCOL_SHA = 'd71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236'
PRIOR_REGISTRY_SHA = '2521b9901e9e432d5bdd27f0ef57fae3fec6ccc66f659bed06416f0ff838b1ad'
POOL_BYTES = 24392052
SELECTED = ('v_rrNJt73BG_8', 'v_17nr8u_ze0o', 'v_isUCIXYjOXE', 'v_IGamNJ5yIh4')
RESERVES = ('v_NNuIaUFYGCE', 'v_pHZogKGkc9o')
SCOPE = 'EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_GENERIC_HIGHLIGHT_OR_ORDINARY_GOLD'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def checked(path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME) and path.is_file() and
            isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) and sha(path) == digest,
            'Missing/changed frozen resident file: '+str(path))
    return path


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'Explicit path/SHA reference required')
    return checked(ref['path'], ref['sha256'])


def expected_candidate_rows(registry, prior_ids):
    """Original global reserve order, after excluding the ten actual old IDs."""
    original = registry['selection']+registry['ordered_engineering_reserves']
    require(len({row['video_id'] for row in original}) == len(original), 'Duplicate original registered identity')
    require(len(set(prior_ids)) == 10 and set(prior_ids) <= {row['video_id'] for row in original}, 'Exact ten prior actual IDs required')
    remaining = [row for row in registry['ordered_engineering_reserves'] if row['video_id'] not in set(prior_ids)]
    require(tuple(row['video_id'] for row in remaining) == SELECTED+RESERVES, 'Do not alter the original remaining reserve order')
    result = []
    for row in remaining:
        require(row['video_id'] == 'v_'+row['youtube_id'] and row['provider']['video_id'] == row['youtube_id'] and
                type(row['provider']['size_bytes']) is int and row['provider']['size_bytes'] > 0 and
                F(30) <= F(row['author_duration_raw']) <= 60, 'Original source identity/byte count/duration eligibility differs')
        result.append(dict(row, prior_registration_group=row['group'], group='confirm'))
    require(sum(row['provider']['size_bytes'] for row in result) == POOL_BYTES, 'New six-source pool byte count changed')
    return result[:4], result[4:]


def validate_development(protocol, selection, result, protocol_sha, result_sha):
    require(protocol_sha == PROTOCOL_SHA and protocol['schema'] == 'RECALL_CONSENSUS_TWO_VIEW_SMALL_PILOT_V1' and
            protocol['candidate'] == 'TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION' and
            protocol['baseline'] == 'TEMPORAL_VERIFY_USER40.46' and protocol['support_count'] == 2 and
            protocol['view_seconds'] == '15' and protocol['stride_seconds'] == '15/2' and
            protocol['development_source_count'] == 8 and protocol['fresh_confirmation_source_count'] == 4 and
            protocol['old_confirmation_is_exposed_development'] is True and protocol['reference_scope'] == SCOPE and
            protocol['production_before_fresh_confirmation_and_fixed_facts_pass'] is False,
            'Frozen new two-view development protocol required, never the old single-KEEP gate')
    expected = {'full_group', 'macro_F1_not_lower', 'macro_recall_gain', 'every_source_loss_within_gate',
                'macro_precision_not_lower', 'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources'}
    require(selection['status'] == 'FROZEN_CONSENSUS2_AFTER_DEV_PASS' and selection['protocol_sha256'] == protocol_sha and
            selection['result_sha256'] == result_sha and selection['candidate'] == protocol['candidate'] and
            selection['fresh_confirm_metrics_examined'] is False and
            result['status'] == 'PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM' and result['protocol_sha256'] == protocol_sha and
            result['candidate'] == protocol['candidate'] and set(result['conditions']) == expected and
            all(value is True for value in result['conditions'].values()) and len(result['cases']) == 8 and
            len({row['video_id'] for row in result['cases']}) == 8 and result['production_admitted'] is False and
            result['old_confirmation_used_as_blind'] is False and result['prior_failure_and_gates_unchanged'] is True,
            'Complete frozen exposed-eight development PASS required before fresh confirmation')


def prior_media(reg, registry):
    """Reuse byte-bound original receipts; no old media rehash, decode or glob."""
    refs = reg['prior_media_receipts']
    require(reg['expected_prior_media_count'] == 10 and len(refs) == 10, 'All ten original successful media receipts required')
    candidates = {row['video_id']: row for row in registry['selection']+registry['ordered_engineering_reserves']}
    result, ids, hashes = [], set(), set()
    for ref in refs:
        require({'path', 'sha256'} <= set(ref) <= {'path', 'sha256', 'video_id', 'bytes', 'media_path', 'media_sha256'},
                'Only explicit receipt path/SHA and matching recorded media metadata are allowed')
        receipt_ref = dict(path=ref['path'], sha256=ref['sha256'])
        path = bound(receipt_ref); receipt = read(path); vid = receipt['video_id']
        require(vid in candidates and vid not in ids and path.name == 'media_receipt.json' and path.parent.name == vid and
                path.parent.parent in (OLD/'dev/reference_02', OLD/'confirm/reference_03'), 'Wrong/duplicate original media receipt')
        row = candidates[vid]
        require(receipt['group'] == row['group'] and receipt['bytes'] == row['provider']['size_bytes'] and
                receipt['public_url'] == row['provider']['video_url'] and receipt['known_ID_and_byte_separation'] is True and
                isinstance(receipt['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', receipt['sha256']) and
                receipt['sha256'] not in hashes and Path(receipt['path']) == path.parent/'media.mp4',
                'Original actual media identity/bytes/recorded SHA differs')
        require(all(ref[key] == receipt[receipt_key] for key, receipt_key in (
                    ('video_id', 'video_id'), ('bytes', 'bytes'), ('media_path', 'path'), ('media_sha256', 'sha256')) if key in ref),
                'Optional prior receipt summary metadata differs from its byte-bound original')
        media = Path(receipt['path'])
        require(media.is_file() and media.stat().st_size == receipt['bytes'], 'Previously resident media missing/size changed; no implicit recovery')
        require(reg['required_files'].get(str(path)) == ref['sha256'], 'Prior receipt absent from new frozen metadata closure')
        ids.add(vid); hashes.add(receipt['sha256'])
        result.append(dict(video_id=vid, receipt_ref=receipt_ref, bytes=receipt['bytes'], media_sha256=receipt['sha256']))
    require(len(ids) == 10 and len(hashes) == 10 and
            {row['video_id'] for row in registry['selection']} <= ids and
            {row['video_id'] for row in read(bound(reg['development_result_ref']))['cases']} <= ids,
            'All old original selections/exposed eight must be among the ten actual receipts')
    return dict(actual_media_count=10, actual_media_bytes=sum(row['bytes'] for row in result), media=result), ids, hashes


def validate_routes(document, candidates):
    require(document['windows_video_body_bytes'] == 0 and len(document['routes']) == 6, 'Six HEAD-only public route metadata entries required')
    routes = {row['video_id']: row for row in document['routes']}
    require(len(routes) == 6 and set(routes) == {row['video_id'] for row in candidates}, 'Missing/duplicate/out-of-pool public route')
    for row in candidates:
        route = routes[row['video_id']]
        url = 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+row['youtube_id']+'.mp4'
        require(route['initial_public_url'] == row['provider']['video_url'] == url and
                route['bytes'] == row['provider']['size_bytes'] and route['metadata_only'] is True and
                route['status'] in ('PINNED_NORMAL_PUBLIC_REDIRECT', 'PUBLIC_OBJECT_404'),
                'Original publisher metadata identity/size changed; network failure is not a replacement reason')
        if route['status'] == 'PINNED_NORMAL_PUBLIC_REDIRECT':
            target = urlparse(route['publisher_redirect_url'])
            require(target.scheme == 'https' and target.hostname and target.hostname.endswith('.cdn.hf.co') and
                    target.username is None and target.password is None and target.port in (None, 443) and
                    isinstance(route['etag'], str) and bool(route['etag']), 'Pinned original public CDN/ETag required')
    return routes


def registration(root):
    path = root/'fresh_confirm_registration.json'; reg = read(path)
    require(reg['schema'] == REG_SCHEMA and reg['status'] == REG_STATUS and reg['group'] == 'confirm' and
            reg['expected_accepted_sources'] == 4 and reg['maximum_media_pool_bytes'] == POOL_BYTES and
            reg['route_acquisition_method'] == 'HEAD' and reg['windows_video_body_bytes'] == 0,
            'New fresh4 reference registration is required; extra frozen runtime fields are allowed')
    canonical = dict(protocol_ref=root/'protocol.json', development_selection_ref=root/'selection_before_fresh_confirmation.json',
                     development_result_ref=root/'development_01/result.json', public_routes_ref=root/'public_routes.json',
                     prior_source_registration_ref=OLD/'new8_source_registration_01.json')
    refs = {}
    for name in tuple(canonical)+('authorization_ref',):
        refs[name] = bound(reg[name])
        require((name not in canonical or refs[name] == canonical[name]) and
                reg['required_files'].get(str(refs[name])) == reg[name]['sha256'], 'Wrong or unlocked reference: '+name)
    require(refs['authorization_ref'].is_relative_to(root) and isinstance(read(refs['authorization_ref']), dict) and
            bool(read(refs['authorization_ref'])), 'Bound current authorization receipt required')
    required = {str(Path(__file__).resolve()), str(NATIVE_CODE/'native_profile_01.py'), str(NATIVE_CODE/'native_profile_04.py')}
    require(required <= set(reg['required_code_files']) and
            all(reg['required_files'].get(name) == digest for name, digest in reg['required_code_files'].items()), 'Original helpers/new actual code closure incomplete')
    for name, digest in reg['required_files'].items():
        checked(name, digest)
    require(reg['protocol_ref']['sha256'] == PROTOCOL_SHA and reg['prior_source_registration_ref']['sha256'] == PRIOR_REGISTRY_SHA,
            'Frozen new protocol or original preselection registry changed')
    registry, protocol = read(refs['prior_source_registration_ref']), read(refs['protocol_ref'])
    validate_development(protocol, read(refs['development_selection_ref']), read(refs['development_result_ref']),
                         reg['protocol_ref']['sha256'], reg['development_result_ref']['sha256'])
    require(all(reg['required_files'].get(str(root/'code'/name)) == digest
                for name, digest in protocol['code_sha256'].items()), 'Actual selected development implementation changed')
    prior, prior_ids, prior_hashes = prior_media(reg, registry)
    selected, reserves = expected_candidate_rows(registry, prior_ids)
    require(reg['selection'] == selected and reg['ordered_engineering_reserves'] == reserves and
            tuple(reg['selected_confirm_ids']) == SELECTED and tuple(reg['ordered_confirm_engineering_reserve_ids']) == RESERVES,
            'Fresh source/reserve identities or order changed')
    for name in ('annotation_file', 'known_exclusions'):
        require(reg[name+'_path'] == registry[name+'_path'] and reg[name+'_sha256'] == registry[name+'_sha256'] and
                reg['required_files'].get(reg[name+'_path']) == reg[name+'_sha256'], 'Original resident annotation/exclusion reference changed')
        checked(reg[name+'_path'], reg[name+'_sha256'])
    require(set(reg['old_exposed_and_reserved_ids']) == set(registry['old_exposed_and_reserved_ids']) | prior_ids,
            'All original historical exclusions and actual ten prior IDs must remain excluded')
    known = read(reg['known_exclusions_path'])
    excluded = {name if name.startswith('v_') else 'v_'+name for name in known['youtube_ids']} | set(reg['old_exposed_and_reserved_ids'])
    require(not (set(SELECTED+RESERVES) & excluded), 'Fresh identity intersects a known/test/exposed exclusion')
    prohibited = set(known['known_media_sha256']) | prior_hashes
    require(all(re.fullmatch(r'[0-9a-f]{64}', digest) for digest in prohibited), 'Known media byte exclusions malformed')
    routes = validate_routes(read(refs['public_routes_ref']), selected+reserves)
    return reg, selected, reserves, routes, prior, prohibited, path


def original_reference(raw):
    events = raw['vsum']
    require(isinstance(events, list) and events and isinstance(events[0], list), 'Original all-rater summaries missing')
    count = len(events[0])
    require(count >= 2 and all(isinstance(event, list) and len(event) == count for event in events), 'Inconsistent original reviewer count')
    references = [[] for _ in range(count)]
    for event in events:
        for index, span in enumerate(event):
            require(isinstance(span, list) and len(span) == 2 and F(str(span[0])) < F(str(span[1])), 'Invalid original summary interval')
            references[index].append([str(span[0]), str(span[1])])
    return dict(video_id=raw['video_id'], annotator_count=count, annotator_intervals_exact_seconds=references,
                text_available_to_model=False, original_labels_unmodified=True,
                label_semantics='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY')


def validate_reference_domain(clock, reference):
    points = list(map(F, clock['original_exact_pts'])); end = F(clock['physical_end_exact'])
    require(points and points[0] == 0 and len(points) == clock['native_frames'] and
            all(a < b for a, b in zip(points, points[1:])) and F(clock['first_original_pts_exact']) == 0 and
            clock['original_zero_origin_verified'] is True and clock['timeline_shift_applied'] is False and
            F(clock['last_frame_duration_exact']) > 0 and end == points[-1]+F(clock['last_frame_duration_exact']),
            'ORIGINAL_NATIVE_ORIGIN_OR_PHYSICAL_END_INVALID')
    require(reference['annotator_count'] >= 2 and len(reference['annotator_intervals_exact_seconds']) == reference['annotator_count'] and
            all(0 <= F(first) < F(last) <= end for spans in reference['annotator_intervals_exact_seconds'] for first, last in spans),
            'UNMODIFIED_REFERENCE_OUTSIDE_NATIVE_DOMAIN')
    windows, start = set(), F(0)
    if end <= 15:
        windows.add((F(0), end))
    else:
        while start+15 <= end:
            windows.add((start, start+15)); start += F(15, 2)
        windows.add((end-15, end))
    require(all(bisect_left(points, last)-bisect_left(points, first) >= 64 for first, last in windows),
            'FEWER_THAN64_NATIVE_FRAMES_IN_REGISTERED_OVERLAP_VIEW')


def pool_budget(value):
    require(type(value) is int and 0 <= value <= POOL_BYTES, 'New six-source payload/reservation budget exceeded')
    return value


def download(folder, row, route, prohibited, transfer):
    """One Linux GET of an already pinned public object; never HEAD/retry."""
    save(folder/'route.json', route)
    if route['status'] == 'PUBLIC_OBJECT_404':
        return None, 'REGISTERED_PUBLIC_OBJECT_404'
    import requests
    expected, url, etag = row['provider']['size_bytes'], route['publisher_redirect_url'], route['etag']
    require(shutil.disk_usage(folder).free > 2*expected, 'Current disk cannot hold this original source/partial; no source replacement')
    digest, size = hashlib.sha256(), 0
    partial = folder/'media.mp4.partial'
    with requests.get(url, stream=True, allow_redirects=False, timeout=(10, 45),
                      headers={'Accept-Encoding': 'identity', 'If-Match': etag}) as body:
        if body.status_code == 404:
            save(folder/'public_404.json', dict(status=404, response_body_read=False, utc=utc()))
            return None, 'ACTUAL_PUBLIC_OBJECT_404'
        require(body.status_code == 200 and body.headers.get('ETag') == etag and
                int(body.headers['Content-Length']) == expected and body.headers.get('Content-Encoding') in (None, 'identity') and
                urlparse(body.url).hostname == urlparse(url).hostname, 'Public object/version/network failure; retain and stop, never replace')
        with partial.open('xb') as stream:
            for chunk in body.iter_content(1 << 20):
                size += len(chunk); transfer['actual_new_media_payload_bytes'] += len(chunk)
                require(size <= expected, 'Public object exceeded pinned bytes')
                pool_budget(transfer['actual_new_media_payload_bytes'])
                stream.write(chunk); digest.update(chunk)
            stream.flush(); os.fsync(stream.fileno())
    require(size == expected and digest.hexdigest() not in prohibited, 'Incomplete media or known/old/new byte overlap; retain and stop')
    final = folder/'media.mp4'; partial.rename(final)
    receipt = dict(video_id=row['video_id'], path=str(final), bytes=size, sha256=digest.hexdigest(),
                   public_url=row['provider']['video_url'], group='confirm', utc=utc(),
                   original_author_byte_identity_verified=False, known_ID_and_byte_separation=True,
                   hidden_alias_or_semantic_overlap='UNKNOWN')
    save(folder/'media_receipt.json', receipt)
    return receipt, None


def main(root):
    require(sys.platform == 'linux' and socket.gethostname() == 'inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
            'First fresh reference preparation requires the existing explicitly CPU-only Linux host')
    root = Path(root).resolve()
    require(root == ROOT and not (root/'reference_completion_confirm.json').exists() and
            not (root/'confirm/reference_01').exists(), 'Wrong root or existing successful/failed reference stage; no implicit resume')
    reg, selected, reserves, routes, prior, prohibited, reg_path = registration(root)
    raw_rows = json.loads(Path(reg['annotation_file_path']).read_text(encoding='utf-8'), parse_float=Decimal,
                          object_pairs_hook=unique_object)
    wanted = set(SELECTED+RESERVES)
    raw = {row['video_id']: row for row in raw_rows if row['video_id'] in wanted}
    require(set(raw) == wanted and sum(row['video_id'] in wanted for row in raw_rows) == 6, 'Original author IDs missing/duplicated')
    del raw_rows
    output = root/'confirm/reference_01'; output.mkdir(parents=True, exist_ok=False)
    save(output/'launch_claim.json', dict(utc=utc(), pid=os.getpid(), group='confirm', registration_sha256=sha(reg_path),
        protocol_sha256=reg['protocol_ref']['sha256'], development_selection_sha256=reg['development_selection_ref']['sha256'],
        development_result_sha256=reg['development_result_ref']['sha256'], windows_video_body_bytes=0,
        maximum_new_six_pool_bytes=POOL_BYTES, actual_new_model_calls=0, CPU_only=True))
    save(output/'prior_media_budget.json', prior)
    accepted, rejected, current, reserved, reserve_position, measured = [], [], None, 0, 0, 0
    transfer = dict(actual_new_media_payload_bytes=0)
    try:
        for name in ('native_profile_01', 'native_profile_04'):
            existing = sys.modules.get(name)
            require(existing is None or Path(existing.__file__).resolve() == NATIVE_CODE/(name+'.py'), 'Native helper import identity collision')
        sys.path.insert(0, str(NATIVE_CODE))
        from native_profile_04 import measure_original_video, validate_original_origin
        from native_profile_01 import native64_windows
        import av
        for slot, initial in enumerate(selected):
            row = initial
            while True:
                current = row['video_id']; folder = output/current; folder.mkdir(exist_ok=False)
                reserved += row['provider']['size_bytes']; pool_budget(reserved)
                receipt, reason = download(folder, row, routes[current], prohibited, transfer)
                rejection = None
                if receipt is None:
                    rejection = dict(video_id=current, reason=reason, downloaded=False, no_model_or_quality_observed=True)
                else:
                    prohibited.add(receipt['sha256'])
                    try:
                        measured += 1
                        clock = measure_original_video(receipt['path'], av)
                    except (ValueError, av.error.InvalidDataError) as error:
                        rejection = dict(video_id=current, reason='ACTUAL_ORIGINAL_NATIVE_MEASUREMENT_REJECTED', error=repr(error),
                            media_receipt_sha256=sha(folder/'media_receipt.json'), no_model_or_quality_observed=True)
                    if rejection is None:
                        save(folder/'clock.json', clock)
                        try:
                            reference = original_reference(raw[current]); save(folder/'reference.json', reference)
                            validate_original_origin(clock); validate_reference_domain(clock, reference); native64_windows(clock)
                        except ValueError as error:
                            rejection = dict(video_id=current, reason='ORIGINAL_REFERENCE_OR_NATIVE_DOMAIN_REJECTED', error=repr(error),
                                media_receipt_sha256=sha(folder/'media_receipt.json'), clock_sha256=sha(folder/'clock.json'),
                                no_model_or_quality_observed=True, original_endpoints_changed=False)
                if rejection is not None:
                    rejected.append(rejection); save(folder/'source_rejection.json', rejection)
                    require(reserve_position < len(reserves), 'Fixed two engineering reserves exhausted; do not broaden the source pool')
                    row = reserves[reserve_position]; reserve_position += 1
                    continue
                accepted.append(dict(video_id=current, slot=slot, group='confirm', media=receipt,
                    clock_path=str(folder/'clock.json'), clock_sha256=sha(folder/'clock.json'),
                    reference_path=str(folder/'reference.json'), reference_sha256=sha(folder/'reference.json')))
                save(output/('accepted_slot_%02d.json'%slot), accepted[-1])
                print('Accepted fresh confirm native reference '+current, flush=True)
                break
        require(len(accepted) == len({row['video_id'] for row in accepted}) == 4, 'Full fresh4 confirmation denominator required')
        save(output/'completion.json', dict(status=REFERENCE_STATUS, group='confirm', accepted=accepted, rejected=rejected,
            registration_sha256=sha(reg_path), source_registration_sha256=sha(reg_path),
            prior_source_registration_sha256=reg['prior_source_registration_ref']['sha256'],
            protocol_sha256=reg['protocol_ref']['sha256'], development_selection_sha256=reg['development_selection_ref']['sha256'],
            development_result_sha256=reg['development_result_ref']['sha256'], reserved_bytes_counted=reserved,
            actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'], maximum_media_pool_bytes=POOL_BYTES,
            prior_actual_media_count=10, prior_actual_media_bytes=prior['actual_media_bytes'], native_clock_measurements_started=measured,
            original_labels_unmodified=True, reference_scope=SCOPE, annotator_count_not_hardcoded=True,
            annotation_votes_exported_only_for_attempted_ids=True, windows_video_body_bytes=0,
            original_annotation_downloads_repeated=0, successful_media_and_clocks_repeated=0,
            actual_new_model_calls=0, new_RGB_or_processor_calls=0, CPU_only=True, GPU_admitted=False, production_admitted=False, utc=utc()))
        save(root/'reference_completion_confirm.json', dict(path=str(output/'completion.json'), sha256=sha(output/'completion.json')))
    except BaseException as error:
        save(output/'failure.json', dict(current=current, accepted=accepted, rejected=rejected, error=repr(error),
            traceback=traceback.format_exc(), reserved_bytes_counted=reserved,
            actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'], successful_media_and_clocks_must_not_repeat=True,
            implicit_resume=False, source_order_and_original_endpoints_must_not_change=True,
            actual_new_model_calls=0, GPU_admitted=False, production_admitted=False, utc=utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    main(args.root)
