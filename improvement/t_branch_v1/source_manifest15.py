"""Freeze a small author-bound MTurk cohort from already indexed TAR headers."""
from collections import Counter
import hashlib
from pathlib import PurePosixPath
import tarfile
import traceback

from t_io import ROOT, WORK, check, fetch, identity, read, save

OUT = ROOT / 'source_manifest15'
PIN = '29083d2dc8ee951986f6fb436f1be8f92c8937fd'


def cached_video_headers():
    """Parse only durable accepted header blocks; no new archive walk or request."""
    headers = {}
    journal = ROOT / 'archive_index11/ranges/ranges.jsonl'
    import json
    for line in journal.read_text().splitlines():
        row = json.loads(line)
        if row['count'] != 512 or row['start'] % 512:
            continue
        path = check(row['body'])
        try:
            member = tarfile.TarInfo.frombuf(path.read_bytes(), 'utf-8', 'surrogateescape')
        except tarfile.HeaderError:
            continue
        if member and member.isfile() and member.name.endswith('.mp4'):
            p = PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or len(p.parts) != 4:
                raise ValueError('Unexpected cached video member path')
            headers[(p.parts[1], p.stem)] = dict(
                name=member.name, bytes=member.size, data_offset=row['start'] + 512,
                accepted_header=row['body'], object_etag=row['object_etag'])
    return headers


def source_group(row):
    title = row['mirror']['title'].lower()
    if 'diego' in title:
        return 'dog-recurring-Diego'
    if 'dock dogs scarborough' in title:
        return 'dog-scarborough-2012'
    if 'novice a timonium' in title:
        return 'dog-novice-timonium-2013'
    if title.startswith('gopr'):
        return 'parkour-GOPR-unknown-uploader'
    return row['domain'] + ':' + row['source_id']


def eligible_sources():
    headers = cached_video_headers()
    warnings = {x['video_id'] for x in read(ROOT / 'archive_scoped14/annotation_alignment_warnings.json')}
    author = read(WORK / 'i3d_umt_cross_domain_20261021_v1/source_inventory01.json')
    if author['commit'] != PIN:
        raise ValueError('Author inventory commit differs')
    original = {(x['domain'], x['source_id']): x for x in author['sources']}
    candidates = []
    for domain in ['dog', 'parkour']:
        for video in read(ROOT / ('archive_scoped14/' + domain + '__annotations_mturk.json'))['videos']:
            key = (domain, video['video_id'])
            media = video['media']
            if key not in headers or key not in original or video['video_id'] in warnings:
                continue
            # A conservative compatibility filter, not proof of original frame indexing.
            if not 8 <= media['duration_sec'] <= 120 or headers[key]['bytes'] > 32 << 20:
                continue
            if max(x['end_frame'] for x in video['segments']) != media['num_frames']:
                continue
            if video['supervision_type'] != 'human_mturk':
                raise ValueError('Unexpected supervision task')
            candidates.append(dict(domain=domain, source_id=video['video_id'],
                                   mirror=video, original=original[key], archive_member=headers[key]))
    return candidates


def choose():
    candidates = eligible_sources()
    order = lambda r: hashlib.sha256(('T-MTurk15-source-v1/' + r['source_id']).encode()).hexdigest()
    dog_train = sorted([r for r in candidates if r['domain'] == 'dog' and r['mirror']['split'] == 'train'], key=order)
    dog_test = sorted([r for r in candidates if r['domain'] == 'dog' and r['mirror']['split'] == 'test'], key=order)
    parkour_test = sorted([r for r in candidates if r['domain'] == 'parkour' and r['mirror']['split'] == 'test'], key=order)
    if len(dog_train) < 6 or len(dog_test) < 2 or len(parkour_test) < 4:
        raise ValueError('Conservative author/media compatibility cohort too small')
    selected = dog_train[:6] + dog_test[:2] + parkour_test[:4]
    groups = sorted({source_group(r) for r in dog_train[:6]},
                    key=lambda g: hashlib.sha256(('T-MTurk15-group/' + g).encode()).hexdigest())
    if len(groups) < 3:
        raise ValueError('Too few known title families for fit/development separation')
    development = groups[-1]
    for row in selected:
        row['known_group'] = source_group(row)
        row['role'] = ('confirmation' if row['mirror']['split'] == 'test' else
                       'development' if row['known_group'] == development else 'fit')
        row['historical_quality_exposure'] = False
        row['global_publisher_or_reupload_independence'] = 'UNKNOWN'
    train_groups = {r['known_group'] for r in selected if r['role'] != 'confirmation'}
    if train_groups & {r['known_group'] for r in selected if r['role'] == 'confirmation'}:
        raise ValueError('Known recording/title family crosses confirmation boundary')
    return selected


def author_labels(row):
    folder = OUT / row['source_id']
    folder.mkdir()
    refs = {}
    for key in ['human_label_ref', 'clip_ref']:
        original = row['original'][key]
        path = folder / (key + '.json')
        fetch('https://raw.githubusercontent.com/aliensunmin/DomainSpecificHighlight/' + PIN + '/' + original['path'],
              path, original['bytes'])
        data = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if len(data) != original['bytes'] or blob != original['git_blob']:
            raise ValueError('Original author file differs from pinned Git blob')
        refs[key] = identity(path)
    labels, clips = read(refs['human_label_ref']['path']), read(refs['clip_ref']['path'])
    segments = row['mirror']['segments']
    if labels[0] != clips or len(segments) != len(clips):
        raise ValueError('Original clip and vote domains differ')
    if [[s['start_frame'], s['end_frame']] for s in segments] != clips:
        raise ValueError('Mirror frame coordinates differ from original author')
    if [s['mturk_score'] for s in segments] != labels[1]:
        raise ValueError('Mirror human votes differ from original author')
    save(folder / 'acceptance.json', dict(source=row['source_id'], refs=refs,
        original_blob_and_mirror_labels_exact=True, original_votes_not_binary=True,
        zero_votes_not_generic_ordinary=True, annotator_count='UNKNOWN',
        native_media_and_endpoint_convention_still_pending=True))
    print('AUTHOR15_ACCEPTED', row['source_id'], row['role'], flush=True)
    return identity(folder / 'acceptance.json')


def main():
    OUT.mkdir()
    rows = choose()
    save(OUT / 'registration.json', dict(
        state='SOURCE_SELECTION_FROZEN_BEFORE_MEDIA_OR_QUALITY', sources=rows,
        role_counts=dict(Counter(r['role'] for r in rows)),
        media_payload_bytes=sum(r['archive_member']['bytes'] for r in rows),
        original_author_commit=PIN,
        mirror_commit=read(ROOT / 'code/mirror_metadata11.json')['revision'],
        scope='Human domain-specific clip preference votes; dogs and parkour, not general dense HL/NHL',
        fit_test_assignment='Original split; title-family grouped hash development; no outcome selection',
        exclusions='All19 mismatch warnings, weak_match, nonmatching final frame extent, >120s, >32MiB',
        native_ordinal_semantics_not_inferred_from_fps_or_duration=True,
        research_only_no_original_media_redistribution=True, no_training_or_model_admission=True))
    accepted, failed = [], []
    for row in rows:
        try:
            accepted.append(author_labels(row))
        except Exception:
            failure = dict(source=row['source_id'], traceback=traceback.format_exc())
            save(OUT / (row['source_id'] + '_failure.json'), failure)
            failed.append(failure)
    save(OUT / 'completion.json', dict(state='AUTHOR_IDENTITY_LABEL_ADMISSION_COMPLETE',
        accepted=accepted, failed=failed, sources=len(rows), new_model_calls=0,
        native_media_admitted=False, media_payload_bytes=sum(r['archive_member']['bytes'] for r in rows)))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
