"""One bounded, train-only provenance/identity audit. No media or model work."""
import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/diagnostic_score_goal_20261018_v1/qvh_original_human_145')
REGISTRY = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/inputs_01/r7_train_registry.json')
REGISTRY_SHA = '71552f64ccdb125ca11a451baf5b8a22491d51d73db1a42e0ce1a545262d1cd4'
COMMIT = 'b7e553ac3b0c898ee6b85e03ee507c064eab89ca'
FILES = {
    'README.md': (2443, 'b6660f0ce3cc65be6f85b43996be6dedb7331bdc'),
    'LICENSE': (20848, 'bfef380bf7d9cb74ec9ba533b37c3fbeef3bdc09'),
    'highlight_train_release.jsonl': (3956580, '0dda92dfdbc50598d9a5eade5972d5736ed2a728'),
}


def dump(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(data, spec):
    size, blob = spec
    if len(data) != size:
        raise ValueError('upstream size mismatch')
    actual = hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + data).hexdigest()
    if actual != blob:
        raise ValueError('immutable upstream Git blob mismatch')


def main():
    if os.uname().nodename != 'inspur-NP5570M5':
        raise RuntimeError('wrong host')
    ROOT.mkdir(exist_ok=True)
    dump(ROOT / 'claim.json', {'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                              'purpose': 'original external QVHighlights train annotation availability and identity only',
                              'commit': COMMIT, 'max_payload_bytes': sum(x[0] for x in FILES.values()),
                              'media_downloads': 0, 'model_calls': 0, 'new_training_admission': False})
    try:
        registry_bytes = REGISTRY.read_bytes()
        if sha(registry_bytes) != REGISTRY_SHA:
            raise ValueError('frozen TIME registry identity mismatch')
        parents = json.loads(registry_bytes)['records']
        if len(parents) != 704:
            raise ValueError('wrong parent set')
        receipts = []
        new_bytes = 0
        for name, spec in FILES.items():
            target = ROOT / name
            adopted = target.exists()
            if adopted:
                data = target.read_bytes()
            else:
                url = f'https://raw.githubusercontent.com/jayleicn/moment_detr/{COMMIT}/data/{name}'
                req = urllib.request.Request(url, headers={'User-Agent': 'AIC-student-research-metadata-audit/145'})
                with urllib.request.urlopen(req, timeout=25) as response:
                    data = response.read(spec[0] + 1)
                (ROOT / (name + '.received')).write_bytes(data)
                verify(data, spec)
                target.write_bytes(data)
                new_bytes += len(data)
            verify(data, spec)
            receipts.append({'name': name, 'bytes': len(data), 'sha256': sha(data),
                             'upstream_git_blob': spec[1], 'adopted': adopted})
        rows = [json.loads(x) for x in (ROOT / 'highlight_train_release.jsonl').read_text().splitlines() if x.strip()]
        by_vid = {}
        qids = set()
        human_schema_invalid = []
        all_raters = set()
        for row in rows:
            vid = row['vid']
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}_[0-9.]+_[0-9.]+', vid):
                raise ValueError('unknown author vid schema')
            if row['qid'] in qids:
                raise ValueError('duplicate qid')
            qids.add(row['qid'])
            ids, scores = row['relevant_clip_ids'], row['saliency_scores']
            if len(ids) != len(scores) or len(set(ids)) != len(ids):
                human_schema_invalid.append(row['qid'])
            for clipid, votes in zip(ids, scores):
                all_raters.add(len(votes))
                if (not isinstance(clipid, int) or clipid < 0 or clipid * 2 >= row['duration']
                        or len(votes) != 3 or any(not isinstance(x, int) or not 0 <= x <= 4 for x in votes)):
                    human_schema_invalid.append(row['qid'])
            if not isinstance(row['query'], str) or not row['query'].strip():
                human_schema_invalid.append(row['qid'])
            by_vid.setdefault(vid, []).append(row)
        train_yt = {r['youtube_id'] for r in parents}
        human_yt = {v.rsplit('_', 2)[0] for v in by_vid}
        joined = []
        for parent in parents:
            stem = Path(parent['source_path']).stem
            matches = by_vid.get(stem, [])
            joined.append({'parent_sample_id': parent['parent_sample_id'], 'youtube_id': parent['youtube_id'],
                           'source_sha256': parent['source_sha256'], 'source_file_stem': stem,
                           'exact_author_vid_match': bool(matches), 'human_train_queries': len(matches),
                           'human_qids': [r['qid'] for r in matches]})
        summary = {
            'status': 'COMPLETE_QVH145_ORIGINAL_TRAIN_METADATA_ONLY_NO_NEW_SUPERVISION_ADMISSION',
            'commit': COMMIT, 'registry_sha256': REGISTRY_SHA,
            'files': receipts, 'new_payload_bytes': new_bytes,
            'human_train_query_rows': len(rows), 'human_train_unique_vids': len(by_vid),
            'human_train_unique_original_youtube_ids': len(human_yt),
            'TIME_parent_count': len(parents), 'TIME_original_youtube_ids': len(train_yt),
            'TIME_youtube_ids_in_original_human_train': len(train_yt & human_yt),
            'TIME_parent_exact_author_vid_matches': sum(x['exact_author_vid_match'] for x in joined),
            'TIME_parents_without_author_train_vid': sum(not x['exact_author_vid_match'] for x in joined),
            'annotation_schema_invalid_qids': sorted(set(human_schema_invalid)),
            'original_rater_counts': sorted(all_raters),
            'annotation_task': 'query-conditioned 2-second clip saliency, 3 raters, ordinal 0..4',
            'unconditional_highlight_truth': False,
            'unannotated_regions_are_explicit_ordinary': False,
            'native_media_identity_and_pts_alignment_verified_this_audit': False,
            'annotation_license': 'CC BY-NC-SA 4.0; data/LICENSE, distinct from MIT code',
            'media_usage_license': 'UNKNOWN; annotation license does not automatically establish video rights',
            'original_official_test_source_overlap': 'UNKNOWN; no original source IDs in current official metadata',
            'exposure': 'All downloaded external train annotations are research development material, never a new blind confirmation set',
            'media_downloads': 0, 'new_processor_calls': 0, 'model_calls': 0,
            'training_updates': 0, 'new_supervision_admission': False, 'production_admitted': False,
            'completed_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        dump(ROOT / 'parent_id_join.json', joined)
        dump(ROOT / 'result.json', summary)
        print(json.dumps(summary, ensure_ascii=False))
    except Exception as exc:
        dump(ROOT / 'failure.json', {'type': type(exc).__name__, 'message': str(exc),
                                    'partial_and_successful_fetches_preserved': True})
        raise


if __name__ == '__main__':
    main()
