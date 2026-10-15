"""First positive-admission fresh4 media/native references, CPU only.

No HEAD, automatic retry/resume, RGB, processor, model or quality evaluation.
Only preregistered HTTP404 or explicit native-domain rejection may use the
two sequential engineering reserves. Other failures retain material and stop.
"""
import argparse
from bisect import bisect_left
import datetime as dt
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import importlib.util
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
PARENT = HOME/'recall_positive_admission_verify40_46_20261015_v1'
ROOT = PARENT/'fresh_01'
NATIVE_CODE = HOME/'videoxum_reference_iteration_20261013_v1/code'
SCHEMA = 'POSITIVE_FRESH_MEDIA_REGISTRATION_V1'
STATUS = 'REGISTERED_POSITIVE_FIRST_FRESH_MEDIA_NATIVE'
PASS = 'PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'
PROTOCOL_SHA = '8736442639beb692eecfd8f3a83404f9c012575f002653e5bdc3cf7811fc00d2'
DEV_RESULT_SHA = 'c7fdc59b7ffc49772c57fec04a1fd029c8ba612c5983a4cbc3004879d2c3473c'
DEV_REG_SHA = '7a72863ffb832f8583d0ad7eb23212afeeea54d34801b053729e90541b8226dd'
DEV_SELECTION_SHA = '815fc40cb955689f9849a2b31cdcaaa8f05a508d0eae8e69c20786f9795d292a'
ANNOTATION_SHA = '2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556'
KNOWN_SHA = '4ab34ba54cd899a75ddcf1faa573144a8237a88684a7bf690c6a0fbed98bea96'
SELECTED = ('v_NNuIaUFYGCE', 'v_pHZogKGkc9o', 'v_5FM_xJGb-Tk', 'v_YW3mCNKVaa4')
RESERVES = ('v_1VDNFR3vQR4', 'v_SFfB6qvT5FI')
EXPECTED_BYTES = (1673389, 2275440, 18425235, 19389367, 4607018, 3549249)
POOL_BYTES = sum(EXPECTED_BYTES)
DEV_SOURCES = ('v_vfJnUQ9Tax0', 'v_8tlLBffNjf8', 'v__CMIO5R_OGA', 'v_voaGOm-rl9Y')
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain',
              'every_source_loss_within_gate', 'macro_precision_not_lower',
              'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')
SCOPE = 'EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_GENERIC_HIGHLIGHT_OR_ORDINARY_GOLD'
NATIVE_MEASUREMENT_REJECTIONS = frozenset((
    'Ambiguous video stream or unverifiable original seconds origin',
    'Original video stream has a nonzero or invalid presentation origin',
    'Missing original nominal frame rate; never infer the final duration from it',
    'Native frame has no exact presentation timestamp',
    'Native presentation timestamps are not strictly increasing',
    'Native frame geometry changed', 'Actual positive final frame duration required'))


class NativeDomainRejected(ValueError):
    """Only an observed original-source domain failure, never execution failure."""


def require(value, reason):
    if not value:
        raise ValueError(reason)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def unique_object(pairs):
    output = {}
    for key, value in pairs:
        require(key not in output, 'Duplicate JSON key: '+key)
        output[key] = value
    return output


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def bound(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Exact path/SHA reference required')
    path, digest = Path(value['path']).resolve(), value['sha256']
    require(path.is_relative_to(HOME) and path.is_file() and isinstance(digest, str) and
            re.fullmatch('[0-9a-f]{64}', digest) and sha(path) == digest,
            'Missing or changed frozen resident evidence: '+str(path))
    return path


def validate_development(protocol, result, selection, registration, refs):
    require(refs['protocol_ref']['sha256'] == PROTOCOL_SHA and
            refs['development_result_ref']['sha256'] == DEV_RESULT_SHA and
            refs['development_selection_ref']['sha256'] == DEV_SELECTION_SHA and
            refs['development_registration_ref']['sha256'] == DEV_REG_SHA,
            'Use the exact naturally completed positive dev, not an old recipe')
    require(protocol['schema'] == 'POSITIVE_ADMISSION_RECALL_PILOT_V2_NOVEL_NATIVE_PARTS' and
            protocol['candidate'] == 'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION' and
            tuple(protocol['development']['source_names']) == DEV_SOURCES and
            protocol['production_before_required_passes'] is False,
            'Immutable new positive dev protocol required')
    gates = protocol['quality_gates']
    require(gates['full_group_denominator'] == 4 and
            F(gates['macro_paired_all_rater_duration_F1_delta_min']) == 0 and
            F(gates['per_source_F1_delta_min']) == F('-0.01') and
            F(gates['macro_all_rater_recall_delta_min']) == F('0.01') and
            F(gates['macro_all_rater_precision_delta_min']) == 0 and
            gates['minimum_sources_with_real_new_native_frames'] == 2 and
            gates['per_rater_baseline_recall_and_frame_retention'] == 'no loss' and
            gates['engineering_failure_is_not_EMPTY_or_UNKNOWN'] is True,
            'Original positive dev/confirm gates cannot be changed')
    require(result['status'] == 'PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION' and
            result['group'] == 'dev' and tuple(result['conditions']) == CONDITIONS and
            all(value is True for value in result['conditions'].values()) and
            tuple(row['video_id'] for row in result['cases']) == DEV_SOURCES and
            result['source_metrics_exposed_first_time'] is False and result['old_failed_gates_changed'] is False and
            result['production_admitted'] is False and
            result['bindings']['protocol_ref'] == refs['protocol_ref'] and
            result['bindings']['registration_ref'] == refs['development_registration_ref'],
            'Complete original four-source eight-gate dev PASS required')
    require(selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and
            selection['protocol_sha256'] == PROTOCOL_SHA and selection['result_ref'] == refs['development_result_ref'] and
            selection['confirm_metrics_examined'] is False and selection['candidate'] == protocol['candidate'] and
            selection['production_admitted'] is False,
            'Frozen passing dev selection must precede first fresh source acquisition')
    require(registration['status'] == 'REGISTERED_POSITIVE_ADMISSION_V1' and
            registration['stage_group'] == 'dev' and registration['protocol_ref'] == refs['protocol_ref'] and
            registration['reference_available_to_inference'] is False and registration['production_admitted'] is False,
            'Actual completed dev registration binding required')


def canonical_candidates(document):
    selected, reserves = document['selection'], document['ordered_engineering_reserves']
    rows = selected+reserves
    require(tuple(row['video_id'] for row in rows) == SELECTED+RESERVES and
            tuple(row['provider']['size_bytes'] for row in rows) == EXPECTED_BYTES and
            document['source_order']['selection_salt'] == 'RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1' and
            document['budget']['historical_maximum_pool_bytes'] == POOL_BYTES,
            'Keep the original unexposed source hash order and fixed six-pool budget')
    hashes = []
    for row in rows:
        vid, youtube = row['video_id'], row['youtube_id']
        require(vid == 'v_'+youtube and row['provider']['video_id'] == youtube and row['group'] == 'confirm' and
                row['provider']['video_url'] == public_url(youtube) and type(row['provider']['size_bytes']) is int and
                F(30) <= F(row['author_duration_raw']) <= 60 and re.fullmatch('[0-9a-f]{64}', row['selection_hash']),
                'Original candidate metadata/identity differs')
        hashes.append(row['selection_hash'])
    require(hashes == sorted(hashes) and len(set(hashes)) == 6, 'Pre-exposure hash order changed')
    return selected, reserves


def public_url(youtube):
    return 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+youtube+'.mp4'


def prior_media(reg, candidates):
    """Use fourteen SHA-bound original receipts; never rehash old media bodies."""
    exclusions = candidates['exclusions']
    expected = {row['video_id']: dict(path=row['media_path'], bytes=row['bytes'], sha256=row['media_sha256'])
                for row in exclusions['prior10_actual_media_receipts']}
    expected.update({row['video_id']: dict(path=row['source_ref']['path'], bytes=row['historical_bytes'],
                                         sha256=row['source_ref']['sha256'])
                     for row in exclusions['fresh4_actual_media_metadata']})
    require(len(expected) == 14 and set(expected) == set(exclusions['all14_acquired_IDs']) and
            len(reg['prior_media_receipts']) == 14, 'All fourteen previously acquired media identities required')
    ids, hashes, output = set(), set(), []
    for value in reg['prior_media_receipts']:
        path = bound(value); receipt = read(path); vid = receipt['video_id']
        require(vid in expected and vid not in ids and path.name == 'media_receipt.json' and
                path.parent.name == vid and Path(receipt['path']) == path.parent/'media.mp4' and
                receipt['path'] == expected[vid]['path'] and receipt['bytes'] == expected[vid]['bytes'] and
                receipt['sha256'] == expected[vid]['sha256'] and receipt['known_ID_and_byte_separation'] is True and
                receipt['public_url'] == public_url(vid[2:]) and
                re.fullmatch('[0-9a-f]{64}', receipt['sha256']) and receipt['sha256'] not in hashes,
                'Wrong or duplicate old-media receipt/recorded bytes/SHA')
        require(reg['required_files'].get(str(path)) == value['sha256'], 'Old receipt absent from frozen closure')
        ids.add(vid); hashes.add(receipt['sha256'])
        output.append(dict(video_id=vid, receipt_ref=value, bytes=receipt['bytes'], media_sha256=receipt['sha256']))
    require(ids == set(expected), 'Missing previously acquired media identity')
    return dict(actual_media_count=14, actual_media_bytes=sum(row['bytes'] for row in output), media=output), ids, hashes


def validate_routes(document, rows):
    require(document['windows_video_body_bytes'] == 0 and len(document['routes']) == 6,
            'Exactly six HEAD-only route entries required')
    routes = {row['video_id']: row for row in document['routes']}
    require(len(routes) == 6 and set(routes) == set(SELECTED+RESERVES), 'Missing/duplicate/out-of-pool route')
    for row in rows:
        route = routes[row['video_id']]
        require(route['initial_public_url'] == row['provider']['video_url'] and
                route['bytes'] == row['provider']['size_bytes'] and route['metadata_only'] is True and
                route['status'] in ('PINNED_NORMAL_PUBLIC_REDIRECT', 'PUBLIC_OBJECT_404'),
                'Current route/version/bytes changed; network failure is not a replacement reason')
        if route['status'] == 'PINNED_NORMAL_PUBLIC_REDIRECT':
            url = urlparse(route['publisher_redirect_url'])
            require(url.scheme == 'https' and url.hostname and url.hostname.endswith('.cdn.hf.co') and
                    url.username is None and url.password is None and url.port in (None, 443) and
                    isinstance(route['etag'], str) and bool(route['etag']), 'Normal pinned public CDN/ETag required')
    return routes


def registration(root):
    path = root/'media_registration.json'; reg = read(path)
    require(reg['schema'] == SCHEMA and reg['status'] == STATUS and reg['group'] == 'confirm' and
            reg['expected_accepted_sources'] == 4 and reg['maximum_media_pool_bytes'] == POOL_BYTES and
            reg['route_acquisition_method'] == 'HEAD' and reg['windows_video_body_bytes'] == 0,
            'Independent positive first-fresh media registration required')
    canonical = dict(protocol_ref=PARENT/'protocol_v2.json', development_result_ref=PARENT/'dev/comparison_01/result.json',
        development_selection_ref=PARENT/'dev/selection_before_confirmation.json', development_registration_ref=PARENT/'registration.json',
        source_candidates_ref=PARENT/'reference_candidates.json', authorization_ref=PARENT/'USER_AUTHORIZATION.json',
        public_routes_ref=root/'public_routes.json')
    for key, expected in canonical.items():
        actual = bound(reg[key])
        require(actual == expected and reg['required_files'].get(str(actual)) == reg[key]['sha256'],
                'Wrong/unlocked current-stage binding: '+key)
    required_code = {str(Path(__file__).resolve()), str(NATIVE_CODE/'native_profile_01.py'), str(NATIVE_CODE/'native_profile_04.py')}
    require(required_code <= set(reg['required_code_files']) and
            all(reg['required_files'].get(name) == digest for name, digest in reg['required_code_files'].items()),
            'Actual new/native implementation closure required')
    for name, digest in reg['required_files'].items():
        bound(dict(path=name, sha256=digest))
    validate_development(read(bound(reg['protocol_ref'])), read(bound(reg['development_result_ref'])),
        read(bound(reg['development_selection_ref'])), read(bound(reg['development_registration_ref'])), reg)
    require(isinstance(read(bound(reg['authorization_ref'])), dict), 'Bound project authorization required')
    document = read(bound(reg['source_candidates_ref'])); selected, reserves = canonical_candidates(document)
    dev_registration = read(bound(reg['development_registration_ref']))
    require(dev_registration['required_files'].get(str(bound(reg['source_candidates_ref']))) == reg['source_candidates_ref']['sha256'],
            'Fresh candidate metadata must be the same document frozen before completed dev')
    require(reg['selection'] == selected and reg['ordered_engineering_reserves'] == reserves,
            'Do not alter any original candidate/reserve metadata')
    require(set(reg['old_exposed_and_reserved_ids']) == set(document['exclusions']['all_old_conservative_plus_acquired_IDs']),
            'The complete historical identity exclusion union must remain frozen')
    expected_annotation = Path(document['remote_refs_from_existing_local_receipts_only']['annotation_file_path'])
    require(bound(reg['annotation_file_ref']) == expected_annotation and reg['annotation_file_ref']['sha256'] == ANNOTATION_SHA and
            reg['known_exclusions_ref']['sha256'] == KNOWN_SHA, 'Original annotation/known-exclusion byte identity changed')
    for key in ('annotation_file_ref', 'known_exclusions_ref'):
        actual = bound(reg[key]); require(reg['required_files'].get(str(actual)) == reg[key]['sha256'], 'Original metadata missing closure')
    require(bound(reg['known_exclusions_ref']) == HOME/'sparse_context_iteration_20261013_v1/known_source_exclusions_01.json',
            'Wrong known identity exclusion source')
    scope_paths = {HOME/'videoxum_reference_iteration_20261013_v1/direct_source_scope_05.json',
                   HOME/'sparse_context_iteration_20261013_v1/source_scope_02.json'}
    require(len(reg['source_scope_refs']) == 2 and {bound(value) for value in reg['source_scope_refs']} == scope_paths,
            'Existing private-research media/annotation scope references required')
    for value in reg['source_scope_refs']:
        require(reg['required_files'].get(str(bound(value))) == value['sha256'], 'Source scope absent from closure')
    known = read(bound(reg['known_exclusions_ref']))
    prior, prior_ids, prior_hashes = prior_media(reg, document)
    excluded = {vid if vid.startswith('v_') else 'v_'+vid for vid in known['youtube_ids']} | set(
        document['exclusions']['all_old_conservative_plus_acquired_IDs']) | prior_ids
    require(not (set(SELECTED+RESERVES) & excluded), 'Fresh source intersects known/test/old/exposed identities')
    prohibited = set(known['known_media_sha256']) | prior_hashes
    require(all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) for value in prohibited),
            'Known old/test media byte exclusions malformed')
    routes = validate_routes(read(bound(reg['public_routes_ref'])), selected+reserves)
    return reg, selected, reserves, routes, prior, prohibited, path


def original_reference(raw):
    events = raw['vsum']
    require(isinstance(events, list) and events and isinstance(events[0], list), 'Original all-rater summary schema missing')
    count = len(events[0])
    require(count >= 2 and all(isinstance(event, list) and len(event) == count for event in events),
            'Inconsistent original reviewer axis; schema failure is not a replacement reason')
    references = [[] for _ in range(count)]
    for event in events:
        for index, span in enumerate(event):
            require(isinstance(span, list) and len(span) == 2 and F(str(span[0])) < F(str(span[1])),
                    'Invalid original summary schema; never repair labels or replace by quality')
            references[index].append([str(span[0]), str(span[1])])
    return dict(video_id=raw['video_id'], annotator_count=count, annotator_intervals_exact_seconds=references,
                text_available_to_model=False, original_labels_unmodified=True,
                label_semantics='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY')


def validate_reference_domain(clock, reference):
    points = list(map(F, clock['original_exact_pts'])); end = F(clock['physical_end_exact'])
    if not (points and points[0] == 0 and len(points) == clock['native_frames'] and
            all(a < b for a, b in zip(points, points[1:])) and F(clock['first_original_pts_exact']) == 0 and
            clock['original_zero_origin_verified'] is True and clock['timeline_shift_applied'] is False and
            F(clock['last_frame_duration_exact']) > 0 and end == points[-1]+F(clock['last_frame_duration_exact'])):
        raise NativeDomainRejected('ORIGINAL_NATIVE_ORIGIN_OR_PHYSICAL_END_INVALID')
    if not all(0 <= F(a) < F(b) <= end for spans in reference['annotator_intervals_exact_seconds'] for a, b in spans):
        raise NativeDomainRejected('UNMODIFIED_REFERENCE_OUTSIDE_NATIVE_DOMAIN')
    windows, start = set(), F(0)
    if end <= 15:
        windows.add((F(0), end))
    else:
        while start+15 <= end:
            windows.add((start, start+15)); start += F(15, 2)
        windows.add((end-15, end))
    count = (end.numerator+30*end.denominator-1)//(30*end.denominator)
    windows.update((end*index/count, end*(index+1)/count) for index in range(count))
    if any(bisect_left(points, b)-bisect_left(points, a) < 64 for a, b in windows):
        raise NativeDomainRejected('FEWER_THAN64_NATIVE_FRAMES_IN_REGISTERED_VIEW')


def pool_budget(value):
    require(type(value) is int and 0 <= value <= POOL_BYTES, 'Fixed six-pool byte budget exceeded')
    return value


def download(folder, row, route, prohibited, transfer):
    """One GET; no credentials, hidden redirects, retry, resume or Windows body."""
    save(folder/'route.json', route)
    if route['status'] == 'PUBLIC_OBJECT_404':
        return None, 'REGISTERED_PUBLIC_OBJECT_404'
    import requests
    class NoCredentials(requests.auth.AuthBase):
        def __call__(self, request):
            return request
    expected, url, etag = row['provider']['size_bytes'], route['publisher_redirect_url'], route['etag']
    require(shutil.disk_usage(folder).free > expected, 'Insufficient current capacity for registered source payload; stop')
    digest, size = hashlib.sha256(), 0
    partial = folder/'media.mp4.partial'
    with requests.get(url, stream=True, allow_redirects=False, timeout=(10, 45), auth=NoCredentials(),
                      headers={'Accept-Encoding': 'identity', 'If-Match': etag}) as body:
        if body.status_code == 404:
            save(folder/'public_404.json', dict(status=404, response_body_read=False, utc=utc()))
            return None, 'ACTUAL_PUBLIC_OBJECT_404'
        require(body.status_code == 200 and body.headers.get('ETag') == etag and
                int(body.headers['Content-Length']) == expected and body.headers.get('Content-Encoding') in (None, 'identity') and
                urlparse(body.url).scheme == 'https' and urlparse(body.url).hostname == urlparse(url).hostname and
                urlparse(body.url).path == urlparse(url).path,
                'Public object/version/network failure; stop without replacement')
        with partial.open('xb') as stream:
            for chunk in body.iter_content(1 << 20):
                size += len(chunk); transfer['actual_new_media_payload_bytes'] += len(chunk)
                require(size <= expected, 'Public object exceeded registered bytes')
                pool_budget(transfer['actual_new_media_payload_bytes'])
                stream.write(chunk); digest.update(chunk)
            stream.flush(); os.fsync(stream.fileno())
    require(size == expected and digest.hexdigest() not in prohibited,
            'Incomplete source or known/old/new whole-file overlap; retain partial and stop')
    final = folder/'media.mp4'; partial.rename(final)
    receipt = dict(video_id=row['video_id'], path=str(final), bytes=size, sha256=digest.hexdigest(),
        public_url=row['provider']['video_url'], group='confirm', utc=utc(),
        original_author_byte_identity_verified=False, known_ID_and_byte_separation=True,
        hidden_alias_or_semantic_overlap='UNKNOWN')
    save(folder/'media_receipt.json', receipt)
    return receipt, None


def native_helpers():
    for name in ('native_profile_01', 'native_profile_04'):
        path = NATIVE_CODE/(name+'.py'); existing = sys.modules.get(name)
        require(existing is None or Path(existing.__file__).resolve() == path, 'Native helper import identity collision')
        if existing is None:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return sys.modules['native_profile_04'], sys.modules['native_profile_01']


def main(root):
    require(sys.platform == 'linux' and socket.gethostname() == 'inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
            'Existing strictly identified Linux CPU-only host required')
    root = Path(root).resolve()
    require(root == ROOT and Path(__file__).resolve() == root/'media_code/positive_media.py' and
            not (root/'reference_01').exists() and not (root/'reference_completion_confirm.json').exists(),
            'New exact media root/code only; existing successful or failed stage cannot implicitly resume')
    reg, selected, reserves, routes, prior, prohibited, reg_path = registration(root)
    raw_rows = json.loads(bound(reg['annotation_file_ref']).read_text(encoding='utf-8-sig'),
        parse_float=Decimal, object_pairs_hook=unique_object)
    wanted = set(SELECTED+RESERVES)
    raw = {row['video_id']: row for row in raw_rows if row['video_id'] in wanted}
    require(set(raw) == wanted and sum(row['video_id'] in wanted for row in raw_rows) == 6, 'Author six fixed IDs missing/duplicate')
    del raw_rows
    output = root/'reference_01'; output.mkdir(parents=True, exist_ok=False)
    save(output/'launch_claim.json', dict(utc=utc(), pid=os.getpid(), group='confirm', registration_sha256=sha(reg_path),
        protocol_sha256=PROTOCOL_SHA, development_result_sha256=DEV_RESULT_SHA,
        development_selection_sha256=reg['development_selection_ref']['sha256'],
        windows_video_body_bytes=0, maximum_media_pool_bytes=POOL_BYTES, CPU_only=True, actual_new_model_calls=0))
    save(output/'prior_media_budget.json', prior)
    accepted, rejected, current, reserved, reserve_position, measured = [], [], None, 0, 0, 0
    transfer = dict(actual_new_media_payload_bytes=0)
    try:
        native04, native01 = native_helpers()
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
                    measured += 1
                    try:
                        clock = native04.measure_original_video(receipt['path'], av)
                    except ValueError as error:
                        if str(error) not in NATIVE_MEASUREMENT_REJECTIONS:
                            raise
                        rejection = dict(video_id=current, reason='EXPLICIT_ORIGINAL_NATIVE_DOMAIN_REJECTED',
                            error=str(error), media_receipt_sha256=sha(folder/'media_receipt.json'), no_model_or_quality_observed=True)
                    if rejection is None:
                        save(folder/'clock.json', clock)
                        # Schema errors stop. Only exact source-domain failures may substitute.
                        reference = original_reference(raw[current]); save(folder/'reference.json', reference)
                        try:
                            validate_reference_domain(clock, reference)
                        except NativeDomainRejected as error:
                            rejection = dict(video_id=current, reason='EXPLICIT_ORIGINAL_REFERENCE_NATIVE_DOMAIN_REJECTED',
                                error=str(error), media_receipt_sha256=sha(folder/'media_receipt.json'),
                                clock_sha256=sha(folder/'clock.json'), no_model_or_quality_observed=True,
                                original_endpoints_changed=False)
                        if rejection is None:
                            native04.validate_original_origin(clock)
                            native01.native64_windows(clock)
                if rejection is not None:
                    rejected.append(rejection); save(folder/'source_rejection.json', rejection)
                    require(reserve_position < len(reserves), 'Two fixed engineering reserves exhausted; do not expand')
                    row = reserves[reserve_position]; reserve_position += 1
                    continue
                accepted.append(dict(video_id=current, slot=slot, group='confirm', media=receipt,
                    clock_path=str(folder/'clock.json'), clock_sha256=sha(folder/'clock.json'),
                    reference_path=str(folder/'reference.json'), reference_sha256=sha(folder/'reference.json')))
                save(output/('accepted_slot_%02d.json'%slot), accepted[-1])
                print('Accepted positive fresh source native reference '+current, flush=True)
                break
        require(len(accepted) == len({row['video_id'] for row in accepted}) == 4, 'Full four fresh sources required')
        save(output/'completion.json', dict(status=PASS, group='confirm', accepted=accepted, rejected=rejected,
            registration_sha256=sha(reg_path), source_registration_sha256=sha(reg_path),
            source_registration_ref=dict(path=str(reg_path), sha256=sha(reg_path)),
            dev_selection_ref=reg['development_selection_ref'], dev_result_ref=reg['development_result_ref'],
            source_candidates_ref=reg['source_candidates_ref'], protocol_sha256=PROTOCOL_SHA,
            development_result_sha256=DEV_RESULT_SHA, development_registration_sha256=DEV_REG_SHA,
            development_selection_sha256=reg['development_selection_ref']['sha256'],
            reserved_bytes_counted=reserved, actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],
            maximum_media_pool_bytes=POOL_BYTES, prior_actual_media_count=14, prior_actual_media_bytes=prior['actual_media_bytes'],
            native_clock_measurements_started=measured, original_labels_unmodified=True, reference_scope=SCOPE,
            annotator_count_not_hardcoded=True, annotation_votes_exported_only_for_attempted_ids=True,
            windows_video_body_bytes=0, original_annotation_downloads_repeated=0, successful_media_and_clocks_repeated=0,
            actual_new_model_calls=0, new_RGB_or_processor_calls=0, CPU_only=True, GPU_admitted=False,
            production_admitted=False, utc=utc()))
        save(root/'reference_completion_confirm.json', dict(path=str(output/'completion.json'), sha256=sha(output/'completion.json')))
    except BaseException as error:
        error_text, trace = repr(error), traceback.format_exc()
        for route in routes.values():
            url = route.get('publisher_redirect_url')
            if url:
                error_text, trace = error_text.replace(url, '<PINNED_PUBLIC_CDN>'), trace.replace(url, '<PINNED_PUBLIC_CDN>')
        save(output/'failure.json', dict(current=current, accepted=accepted, rejected=rejected, error=error_text,
            traceback=trace, reserved_bytes_counted=reserved,
            actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'], successful_media_and_clocks_must_not_repeat=True,
            implicit_resume=False, source_order_and_original_endpoints_must_not_change=True,
            actual_new_model_calls=0, GPU_admitted=False, production_admitted=False, utc=utc()))
        raise RuntimeError('Positive media stage stopped; inspect retained reference_01/failure.json without repeating successes') from None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    main(parser.parse_args().root)
