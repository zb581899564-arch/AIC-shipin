"""Original-author QV train/val only; bounded complete members, no whole-archive fallback."""
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile
import traceback

from common import ROOT, fetch, read, ref, save
from fresh_videoxum30 import EXCLUDE, exposures
from qv_stream45 import AuthorRanges, PrefixLimit

TARGET = ROOT / 'author_qv45'
ORIGIN = ROOT / 'author_qv43'
CAP = 512 << 20


def annotations():
    commit = read(ORIGIN / 'commit.json')['sha']
    result = {}
    identities = []
    for split in ['train', 'val']:
        name = f'highlight_{split}_release.jsonl'
        api = TARGET / (name + '.api.json')
        fetch('https://api.github.com/repos/jayleicn/moment_detr/contents/data/' +
              name + '?ref=' + commit, api, 15 << 20)
        document = read(api)
        if document.get('encoding') == 'none' and document.get('sha'):
            blob = TARGET / (name + '.blob.json')
            fetch('https://api.github.com/repos/jayleicn/moment_detr/git/blobs/' +
                  document['sha'], blob, 15 << 20)
            document = read(blob)
        if document.get('encoding') != 'base64':
            raise ValueError('Original annotation GitHub content encoding differs')
        payload = base64.b64decode(document['content'])
        if len(payload) != document['size']:
            raise ValueError('Original annotation declared length differs')
        path = TARGET / name
        with path.open('xb') as out:
            out.write(payload)
        identities.append(ref(path))
        for line in payload.splitlines():
            item = json.loads(line)
            item['original_split'] = split
            result.setdefault(item['vid'], []).append(item)
    return result, identities


def validate_queries(rows):
    for row in rows:
        duration = float(row['duration'])
        ids, scores = row['relevant_clip_ids'], row['saliency_scores']
        if (not duration > 0 or len(ids) != len(scores) or len(set(ids)) != len(ids)
                or not ids or any(type(i) is not int or i < 0 or i*2 >= duration for i in ids)):
            raise ValueError('Invalid original 2-second annotation domain')
        if any(len(votes) != 3 or any(type(s) is not int or not 0 <= s <= 4 for s in votes)
               for votes in scores):
            raise ValueError('Original all-three-reviewer saliency differs')
        if any(not 0 <= first < stop <= duration for first, stop in row['relevant_windows']):
            raise ValueError('Original temporal intervals outside declared domain')


def collect(stream, index, known):
    selected, examined, seen = [], [], set()
    with tarfile.open(fileobj=stream, mode='r|gz') as archive:
        for member in archive:
            if len(examined) >= 100:
                break
            if member.isdir():
                continue
            name = Path(member.name).name
            match = re.fullmatch(r'([A-Za-z0-9_-]{11})_([0-9.]+)_([0-9.]+)\.mp4', name)
            if not member.isfile() or not match or member.name != 'videos/' + name:
                raise ValueError('Unexpected original author archive member path/type')
            youtube = match.group(1)
            vid = name[:-4]
            rows = index.get(vid)
            eligible = bool(rows and youtube not in known and youtube not in seen and
                            not EXCLUDE.search(' '.join(row['query'] for row in rows)))
            examined.append(dict(vid=vid, bytes=member.size, eligible=eligible,
                                 reason='metadata/domain/known-ID/group rule only'))
            if not eligible:
                continue
            validate_queries(rows)
            if not 0 < member.size <= 40 << 20:
                continue
            path = TARGET / 'media' / name
            partial = path.with_suffix('.partial')
            source = archive.extractfile(member)
            with partial.open('xb') as out:
                shutil.copyfileobj(source, out, length=1 << 18)
            if partial.stat().st_size != member.size:
                raise ValueError('Complete original tar member size differs')
            partial.rename(path)
            labels = TARGET / 'media' / (vid + '.annotations.json')
            save(labels, rows)
            accepted = dict(vid=vid, youtube_id=youtube, media=ref(path),
                annotations=ref(labels), human_queries=len(rows),
                source_hash=hashlib.sha256(('QV-AUTHOR45/' + youtube).encode()).hexdigest(),
                original_archive_member=member.name, original_tar_member_bytes=member.size)
            save(TARGET / 'media' / (vid + '.acceptance.json'), accepted)
            selected.append(accepted)
            seen.add(youtube)
            print('QV_COMPLETE_SOURCE', len(selected), vid, member.size, flush=True)
            if len(selected) == 24 or len(examined) >= 100:
                break
    return selected, examined


def main():
    TARGET.mkdir()
    (TARGET / 'media').mkdir()
    origin = read(ORIGIN / 'completion44.json')
    if origin['state'] != 'DIRECT_ORIGINAL_AUTHOR_ARCHIVE_PREFIX_ADMITTED':
        raise ValueError('Exact original author direct prefix not admitted')
    known, exclusions = exposures()
    save(TARGET / 'registration.json', dict(
        origin=ref(ORIGIN / 'completion44.json'), license=ref(ORIGIN / 'annotation_LICENSE44'),
        author_commit=read(ORIGIN / 'commit.json')['sha'], compressed_prefix_cap=CAP,
        target_unique_original_sources=24, max_archive_members=100,
        explicit_no_whole_archive=True, prefix44_adopted_without_redownload=True,
        known_exclusions=exclusions, excluded_ids=len(known),
        splits=['train', 'val'], test_labels_or_official_data_access=False,
        source_selection='First original complete eligible members, independent of saliency values or model quality',
        semantics='Query-conditional 3-reviewer saliency 0..4 on original 2-second clips; outside annotated clips UNKNOWN',
        rights='Private student noncommercial research under author data CC-BY-NC-SA4; no raw redistribution; uploader ownership not relicensed',
        training_or_GPU_here=False, full_archive_gzip_CRC='UNAVAILABLE_FOR_PARTIAL_PREFIX'))
    index, identities = annotations()
    save(TARGET / 'annotation_index.json', dict(original_annotations=identities,
        unique_video_clips=len(index), original_queries=sum(map(len,index.values()))))
    stream = AuthorRanges(TARGET, origin['head'], ORIGIN / 'original_prefix_00044.bin', CAP)
    limit = False
    try:
        selected, examined = collect(stream, index, known)
    except PrefixLimit:
        limit = True
        selected = [read(p) for p in sorted((TARGET/'media').glob('*.acceptance.json'))]
        examined = []
    selected.sort(key=lambda item:item['source_hash'])
    held_count = max(2, len(selected)//5)
    for i, source in enumerate(selected):
        source['role'] = 'held_recording' if i < held_count else 'development'
    save(TARGET / 'completion.json', dict(state='BOUNDED_ORIGINAL_AUTHOR_MEMBERS_COMPLETE',
        compressed_bytes_received=stream.offset, registered_cap=CAP, reached_cap=limit,
        accepted=selected, examined=examined, new_media_members=len(selected),
        full_archive_gzip_CRC='UNAVAILABLE_FOR_PARTIAL_PREFIX',
        all_member_checksums='Tar headers checked by Python tar parser; full native decode still required',
        no_GPU=True))
    print('QV45_COMPLETE', len(selected), stream.offset, flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        if TARGET.exists():
            save(TARGET / 'failure.json', dict(traceback=traceback.format_exc(),
                explicit_remaining_required=True, accepted_ranges_and_members_preserved=True))
        raise
