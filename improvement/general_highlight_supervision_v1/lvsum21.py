"""Explicit remaining metadata: adopt four successes; omit absent optional notice."""
from common import ROOT, fetch, read, ref, save
from lvsum20 import REPO, TARGET, inventory


def main():
    if '404' not in read(TARGET / 'failure.json')['traceback']:
        raise ValueError('Expected optional-file failure boundary differs')
    adopted = [ref(TARGET / name) for name in ['commit.json', 'README.md', 'LICENSE', 'LICENSE_DATA']]
    sha = read(TARGET / 'commit.json')['sha']
    save(TARGET / 'remaining21_registration.json', dict(adopted=adopted, commit=sha,
        omitted='ACKNOWLEDGEMENTS referenced by LICENSE but absent at exact commit; not essential code executed',
        original_failure_preserved=True, new_model_or_media=0))
    remaining = []
    for name in ['utils/eval_utils.py', 'annotations/lvsum_72_dataset.json']:
        remaining.append(fetch(f'https://raw.githubusercontent.com/{REPO}/{sha}/{name}',
                               TARGET / name.replace('/', '__'), 12000000))
    result = inventory(TARGET / 'annotations__lvsum_72_dataset.json')
    save(TARGET / 'inventory.json', result)
    save(TARGET / 'completion_remaining21.json', dict(state='AUTHOR_METADATA_AND_UNSCORED_INVENTORY_COMPLETE',
        adopted=adopted, remaining=remaining, inventory=ref(TARGET / 'inventory.json'),
        original_media_not_automatically_relicensed=True, no_GPU_or_media_download=True))
    print('INVENTORY', result['unique_videos'], result['media_hosts'], flush=True)
    for row in result['sources']:
        print(row['source_hash'][:8], row['host'], row['annotators'], row['max_original_endpoint_ms'],
              row['url'], row['description_diagnostic'][:120], flush=True)


if __name__ == '__main__':
    main()
