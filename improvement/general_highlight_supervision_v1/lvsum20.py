"""First new LVSum author metadata acquisition and unscored media inventory."""
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import traceback
from urllib.parse import urlparse

from common import ROOT, fetch, read, ref, save

REPO = 'apple-aiml-research/ml-lvsum-video-summarization'
TARGET = ROOT / 'lvsum20'


def inventory(path):
    rows = read(path)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['video_path']].append(row)
    records = []
    for url, annotations in grouped.items():
        intervals = [segment for a in annotations for segment in a['summary_timestamps']]
        if any(not 0 <= s['start_time'] < s['end_time'] for s in intervals):
            raise ValueError('Original millisecond interval is invalid')
        records.append(dict(url=url, host=urlparse(url).hostname,
            source_ids=sorted({a['video_id'] for a in annotations}),
            annotators=len({a['annotator_id'] for a in annotations}),
            annotation_rows=len(annotations), intervals=len(intervals),
            max_original_endpoint_ms=max(s['end_time'] for s in intervals),
            source_hash=hashlib.sha256(('LVSum-nonsport-v1/' + url).encode()).hexdigest(),
            description_diagnostic=annotations[0]['summary_timestamps'][0].get('description', ''),
            human_metrics_computed=False))
    records.sort(key=lambda x: x['source_hash'])
    return dict(rows=len(rows), unique_videos=len(records),
        media_hosts=dict(Counter(r['host'] for r in records)), sources=records,
        all_reviewers_preserved=True, time_unit='original milliseconds, author eval divides by1000',
        labels_not_modified=True, model_calls=0, media_downloads=0)


def main():
    TARGET.mkdir()
    commit = fetch(f'https://api.github.com/repos/{REPO}/commits/main', TARGET / 'commit.json', 250000)
    sha = read(TARGET / 'commit.json')['sha']
    files = ['README.md', 'LICENSE', 'LICENSE_DATA', 'ACKNOWLEDGEMENTS',
             'utils/eval_utils.py', 'annotations/lvsum_72_dataset.json']
    accepted = []
    for name in files:
        destination = TARGET / name.replace('/', '__')
        receipt = fetch(f'https://raw.githubusercontent.com/{REPO}/{sha}/{name}', destination, 12000000)
        accepted.append(receipt)
        print('METADATA_ACCEPTED', name, receipt['accepted']['bytes'], flush=True)
    result = inventory(TARGET / 'annotations__lvsum_72_dataset.json')
    save(TARGET / 'inventory.json', result)
    save(TARGET / 'completion.json', dict(state='AUTHOR_METADATA_AND_UNSCORED_SOURCE_INVENTORY_COMPLETE',
        commit=sha, commit_response=commit, files=accepted, inventory=ref(TARGET / 'inventory.json'),
        original_media_rights_not_automatically_relicensed=True, no_automatic_GPU=True))
    print('INVENTORY', result['unique_videos'], result['media_hosts'], flush=True)
    for row in result['sources']:
        print(row['source_hash'][:8], row['host'], row['annotators'], row['max_original_endpoint_ms'],
              row['url'], row['description_diagnostic'][:100], flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        if TARGET.exists():
            save(TARGET / 'failure.json', dict(traceback=traceback.format_exc(), no_silent_retry=True))
        raise
