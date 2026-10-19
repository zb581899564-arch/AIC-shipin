"""One-shot fixed-cohort metadata tools; never imports a model or decodes media.

CLI: python cohort4c_tools.py REGISTRATION {download,references,endpoints}
File refs are {path, bytes, sha256}. freeze_model_refs is a nonempty list of
such refs; they must already exist before any author annotation is opened.
No automatic recovery, reserve selection, reference repair, or stage replay.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import datetime as dt
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = Path('/home/inspur/aic_video_work/relative_precision_event_20261018_v1')
COHORT = ROOT/'confirm4c_01'
AUTHOR = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json')
AUTHOR_SHA = '2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556'
SOURCE_CLEAR = Path('/home/inspur/aic_video_work/source_clear_residual_20261018_v1/registration.json')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(value):
    require(isinstance(value, dict), 'An explicit size/SHA file reference is required')
    path = Path(value['path'])
    require(path.is_file() and path.stat().st_size == value['bytes'] and sha(path) == value['sha256'], 'File reference binding failed: '+str(path))
    return path


def read(path, exact=False):
    with Path(path).open(encoding='utf8') as stream:
        return json.load(stream, parse_float=Decimal) if exact else json.load(stream)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def deadline(reg):
    end = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
    require(end.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < end, 'Registered work deadline reached')


def validate_registration(reg):
    require(Path(reg['root']).resolve() == COHORT.resolve(), 'Only the fixed registered confirm4c_01 root is allowed')
    require(Path(reg['pipeline_root']).resolve() == COHORT.resolve(), 'Pipeline must use this fixed cohort root')
    require(Path(reg['native_admission_path']).resolve() == (COHORT/'references/native_admission_for_model.json').resolve(), 'Reference admission must stay in the isolated reference directory')
    selection = reg['selection']
    require(1 <= len(selection) <= 4, 'Only the registered maximum four sources; no automatic reserves')
    names, ids = [], []
    for i, row in enumerate(selection):
        name, youtube_id = row['video_id'], row['youtube_id']
        require(re.fullmatch(r'[A-Za-z0-9_-]+', youtube_id) is not None and name == 'v_'+youtube_id, 'Safe exact original provider identity')
        require(row.get('sid', 'Q%02d'%i) == 'Q%02d'%i, 'Fixed registration order Q00..Q03')
        require(isinstance(row['provider_size_bytes'], int) and not isinstance(row['provider_size_bytes'], bool) and row['provider_size_bytes'] > 0, 'Positive expected media bytes')
        require(0 < F(str(row['author_duration_seconds'])) <= 120, 'Fixed original duration cap120seconds')
        require(row['provider_size_bytes'] <= 25_000_000, 'Fixed maximum25MBper-source')
        parsed = urllib.parse.urlsplit(row['provider_video_url'])
        require(parsed.scheme == 'https' and parsed.hostname == 'huggingface.co' and not parsed.username and not parsed.password and parsed.path.endswith('/'+youtube_id+'.mp4'), 'Registered original public publisher URL')
        names.append(name); ids.append(youtube_id)
    require(len(set(names)) == len(names) and len(set(ids)) == len(ids), 'Distinct fixed source identities')
    require(sum(r['provider_size_bytes'] for r in selection) <= 100_000_000, 'Fixed100MBcohortlimit')
    return selection


def begin(reg_path, reg, mode):
    deadline(reg)
    validate_registration(reg)
    COHORT.mkdir(parents=True, exist_ok=True)
    save(COHORT/(mode+'_recovery02_claim.json'), dict(utc=utc(), pid=os.getpid(), registration_ref=ref(reg_path), code_ref=ref(__file__), stage=mode, automatic_recovery=False))


def cdn_url(url):
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == 'https' and bool(parsed.hostname) and parsed.hostname.endswith('.cdn.hf.co') and not parsed.username and not parsed.password and parsed.port in (None, 443)


class _PublicCDNRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        require(cdn_url(new_url), 'GET redirect left the registered standard public CDN domain')
        return super().redirect_request(request, response, code, message, headers, new_url)


def identity_inventory(reg):
    snapshot = reg['known_identity_snapshot']
    ids, hashes = set(snapshot['youtube_ids']), set(snapshot['known_media_sha256'])
    first_ref = reg['prior_cohort_media_completion_ref']
    first = read(bound(first_ref))
    old_ref = reg.get('source_clear_registration_ref')
    old_path = bound(old_ref) if old_ref else SOURCE_CLEAR
    old = read(old_path)
    require(len(old['sources']) == 33, 'Adopt the existing source-clear 33-source identity inventory')
    for row in first['sources'] + old['sources']:
        if row.get('youtube_id'):
            ids.add(row['youtube_id'])
        if row.get('name', '').startswith('v_'):
            ids.add(row['name'][2:])
        media = row.get('media_ref', row.get('media'))
        require(media and re.fullmatch(r'[0-9a-f]{64}', media['sha256']), 'Existing media SHA inventory required')
        hashes.add(media['sha256'])
    require(not ids.intersection(row['youtube_id'] for row in reg['selection']), 'Known original source identity overlap')
    return ids, hashes, dict(prior_cohort_media_completion_ref=first_ref, source_clear_registration_ref=ref(old_path))


def download(reg):
    out = COHORT/'media'; out.mkdir(exist_ok=False)
    ids, known, inventory_refs = identity_inventory(reg)
    routes = read(bound(reg['public_cdn_routes_ref']))['routes']
    routes_by_id = {row['video_id']:row for row in routes}
    require(len(routes_by_id) == len(routes), 'Unique fixed HEAD routes')
    opener = urllib.request.build_opener(_PublicCDNRedirect())
    sources, failed_requests = [], 0
    for i, source in enumerate(reg['selection']):
        name, expected = source['video_id'], source['provider_size_bytes']
        route = routes_by_id[name]
        require(route['public_url'] == source['provider_video_url'] and route['head_only'] is True and route['status'] == 302 and cdn_url(route['redirect_url']), 'Bound Windows HEAD-only standard public CDN redirect')
        for attempt in range(1, 4):
            deadline(reg)
            partial = out/(name+'.attempt%d.partial'%attempt)
            try:
                request = urllib.request.Request(route['redirect_url'], headers={'User-Agent':'AIC-private-research/1.0'})
                with opener.open(request, timeout=60) as response, partial.open('xb') as stream:
                    require(response.status == 200 and cdn_url(response.geturl()), 'Complete standard public CDN response required')
                    header_length = response.headers.get('Content-Length')
                    require(header_length is None or int(header_length) == expected, 'Response header byte count differs from registration')
                    count, digest = 0, hashlib.sha256()
                    while True:
                        deadline(reg)
                        block = response.read(1024*1024)
                        if not block:
                            break
                        count += len(block)
                        require(count <= expected, 'Body exceeds the fixed expected bytes')
                        stream.write(block); digest.update(block)
                    final_host = urllib.parse.urlsplit(response.geturl()).hostname
                require(count == expected, 'Incomplete media body')
                actual_sha = digest.hexdigest()
                if source.get('provider_sha256') is not None:
                    require(actual_sha == source['provider_sha256'], 'Registered publisher SHA differs')
                require(actual_sha not in known, 'Known media byte overlap')
                final = out/(name+'.mp4')
                # Exclusive hard-link publication never replaces a successful member.
                os.link(partial, final); partial.unlink()
                media_ref = dict(path=str(final), bytes=count, sha256=actual_sha)
                require(sha(final) == actual_sha, 'Committed source media SHA mismatch')
                row = dict(sid='Q%02d'%i, name=name, video_id=name, youtube_id=source['youtube_id'], author_duration_seconds=source['author_duration_seconds'], media_ref=media_ref, public_provider_url=source['provider_video_url'], selection_hash=source['selection_hash'], response_final_host=final_host, attempts=attempt, utc=utc())
                save(COHORT/(row['sid']+'_media_acceptance.json'), row)
                sources.append(row); known.add(actual_sha)
                print(json.dumps(dict(accepted=row['sid'], bytes=count)), flush=True)
                break
            except BaseException as error:
                failed_requests += 1
                save(COHORT/(name+'_attempt%d_failure.json'%attempt), dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(), partial_path=str(partial), partial_bytes=partial.stat().st_size if partial.exists() else 0, failed_requests=failed_requests, prior_successes_preserved=True))
                # Only transient transport failures get another request; at most
                # three unsuccessful requests for the entire registered cohort.
                transient = isinstance(error, (urllib.error.URLError, TimeoutError, ConnectionError))
                if not transient or failed_requests >= 3 or attempt >= 3:
                    raise
                time.sleep(2)
        else:
            raise RuntimeError('Source failed; never convert failure into an empty source')
    completion = dict(status='PASS_FIXED_PUBLIC_MEDIA_SIZE_SHA_IDENTITY_ISOLATION', sources=sources, completion_sources=sources, bytes=sum(s['media_ref']['bytes'] for s in sources), known_ID_count=len(ids), inventory_refs=inventory_refs, public_cdn_routes_ref=reg['public_cdn_routes_ref'], unsuccessful_requests=failed_requests, source_ID_intersection=0, known_byte_intersection=0, model_calls=0, native_decode=0, global_source_and_pretraining_independence='UNKNOWN', utc=utc())
    save(COHORT/'media_completion.json', completion)


def frozen_refs(reg):
    refs = reg['freeze_model_refs']
    require(isinstance(refs, list) and bool(refs), 'Existing frozen model/code refs must be registered before annotation exposure')
    for item in refs:
        bound(item)
    return refs


def original_intervals(raw, selected):
    require(F(str(raw['duration'])) == F(str(selected['author_duration_raw'])), 'Exact rational original duration identity across JSON scalar types')
    labels = [[] for _ in range(10)]
    require(bool(raw['vsum']), 'Original event annotations may not silently become empty')
    for event in raw['vsum']:
        require(len(event) == 10, 'All ten original human reviewers required')
        for k, span in enumerate(event):
            require(len(span) == 2 and 0 <= F(str(span[0])) < F(str(span[1])), 'Original finite positive exact interval')
            labels[k].append([str(span[0]), str(span[1])])
    require(all(labels), 'No reviewer may silently disappear')
    onehot = raw['vsum_onehot']
    require(len(onehot) == 10 and all(len(row) == raw['sampled_frames'] and all(value in (0, 1) for value in row) for row in onehot), 'Original onehot schema only; never resample it as native truth')
    return dict(name=selected['video_id'], author_duration_raw=str(raw['duration']), annotator_intervals_exact_seconds=labels, sampled_frames=raw['sampled_frames'], original_event_count=len(raw['vsum']), onehot_schema_valid=True, onehot_exported=False, texts_exported=False)


def references(reg):
    freeze = frozen_refs(reg)  # Must succeed before opening the author file.
    out = COHORT/'references'; out.mkdir(exist_ok=True)
    require(not any(out.iterdir()), 'Explicit recovery only adopts empty failed-reference directory; no successful export may repeat')
    require(sha(AUTHOR) == AUTHOR_SHA, 'Exact adopted original-author annotation SHA')
    raw_rows = read(AUTHOR, exact=True)
    selected_ids = {row['video_id'] for row in reg['selection']}
    matched = [row for row in raw_rows if row['video_id'] in selected_ids]
    require(len(matched) == len(selected_ids) and len({r['video_id'] for r in matched}) == len(selected_ids), 'Exactly one original row per fixed identity')
    by_id = {row['video_id']:row for row in matched}
    rows = [original_intervals(by_id[s['video_id']], s) for s in reg['selection']]
    save(out/'references.json', rows)
    save(out/'exposure_receipt.json', dict(status='PASS_FIXED_ORIGINAL_ALL10_SCHEMA_AFTER_MODEL_FREEZE', annotation_ref=ref(AUTHOR), freeze_model_refs=freeze, references_ref=ref(out/'references.json'), source_names=[r['name'] for r in rows], labels_provided_to_model=False, native_endpoint_admitted=False, quality_metrics_computed=False, utc=utc()))


def endpoint_row(source, clock, reference):
    points = list(map(F, clock['original_exact_pts']))
    end, duration = F(clock['physical_end_exact']), F(clock['last_frame_duration_exact'])
    require(len(points) == clock['native_frames'] and points and all(a < b for a, b in zip(points, points[1:])), 'Complete strictly increasing measured native PTS')
    require(duration > 0 and end == points[-1]+duration, 'Physical end must use actual final native-frame duration')
    zero = (points[0] == 0 and F(clock['first_original_pts_exact']) == 0 and clock['original_zero_origin_verified'] is True and clock.get('timeline_shift_applied') is False)
    require(clock['source_sha256'] == source['media_ref']['sha256'] and clock['source_bytes'] == source['media_ref']['bytes'], 'Clock must bind the registered actual media')
    labels = reference['annotator_intervals_exact_seconds']
    require(len(labels) == 10 and all(labels), 'Exactly ten unchanged reviewers')
    violations = [(k, i, span) for k, spans in enumerate(labels) for i, span in enumerate(spans) if not F(0) <= F(span[0]) < F(span[1]) <= end]
    return dict(sid=source['sid'], name=source['name'], clock_ref=source['clock_ref'], native_frames=len(points), native_end_exact=str(end), zero_origin=zero, violations=violations, pass_native_end=not violations)


def endpoints(reg):
    frozen_refs(reg)
    out = COHORT/'references'
    exposure = read(out/'exposure_receipt.json')
    refs_path = bound(exposure['references_ref'])
    refs = {row['name']:row for row in read(refs_path)}
    native_path = Path(reg['pipeline_root'])/'stages/b0_prepare/completion.json'
    native = read(native_path)
    media_path = COHORT/'media_completion.json'
    media = read(media_path)
    expected = [('Q%02d'%i, s['video_id']) for i, s in enumerate(reg['selection'])]
    require([(s['sid'], s['name']) for s in native['sources']] == expected, 'All and only the fixed native cohort, in registration order')
    require([(s['sid'], s['name']) for s in media['sources']] == expected and set(refs) == {name for _, name in expected}, 'Fixed media/reference/native identity agreement')
    media_by_sid = {s['sid']:s for s in media['sources']}
    rows = []
    for source in native['sources']:
        require(source['media_ref'] == media_by_sid[source['sid']]['media_ref'], 'Native preparation uses the accepted source media')
        rows.append(endpoint_row(source, read(bound(source['clock_ref'])), refs[source['name']]))
    passed = all(row['zero_origin'] and row['pass_native_end'] for row in rows)
    save(out/'native_end_acceptance.json', dict(status='PASS' if passed else 'FAILED_ORIGINAL_NATIVE_ENDPOINT_NO_REPAIR', sources=rows, b0_prepare_completion_ref=ref(native_path), media_completion_ref=ref(media_path), references_ref=exposure['references_ref'], unchanged_original_labels=True, no_stretch_padding_truncation=True, utc=utc()))
    require(passed, 'Original human endpoints/zero origin failed; no label repair, model admission, or automatic reserve')
    save(Path(reg['native_admission_path']), dict(status='PASS', source_ids=[row['sid'] for row in rows], clock_sha256_by_sid={row['sid']:row['clock_ref']['sha256'] for row in rows}, original_endpoints_fit=True, no_label_resizing=True, labels_provided_to_model=False, utc=utc()))


def main():
    require(len(sys.argv) == 3 and sys.argv[2] in ('references', 'endpoints'), 'Usage: cohort4c_tools.py REGISTRATION [download|references|endpoints]')
    require(os.name == 'posix', 'Real stages execute only on the registered Linux host; Windows supplies HEAD metadata separately')
    reg_path, mode = Path(sys.argv[1]), sys.argv[2]
    reg = read(reg_path)
    try:
        begin(reg_path, reg, mode)
        {'download':download, 'references':references, 'endpoints':endpoints}[mode](reg)
        save(COHORT/(mode+'_stage_completion.json'), dict(status='PASS', stage=mode, registration_ref=ref(reg_path), utc=utc()))
    except BaseException as error:
        save(COHORT/(mode+'_failure_'+str(os.getpid())+'_'+uuid.uuid4().hex+'.json'), dict(stage=mode, utc=utc(), error=repr(error), traceback=traceback.format_exc(), successful_artifacts_preserved=True, automatic_recovery=False))
        raise


if __name__ == '__main__':
    main()
