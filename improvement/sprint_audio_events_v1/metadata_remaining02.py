"""Recover only missing author files using their exact Git blobs, not a mirror."""
import base64
import hashlib
import json
from common import ROOT, read, write, reference, direct_get


def main():
    write(ROOT/'metadata_failure01.json', dict(stage='FIRST_RAW_README_HEADER',
        error='TimeoutError: read operation timed out', accepted_body_bytes=0,
        root_inventory_commit_and_tree_preserved=True))
    commit = read(ROOT/'author/commit.json')['sha']
    paths = {row['path']: row for row in read(ROOT/'author/tree.json')['tree']}
    write(ROOT/'metadata_remaining02_registration.json', dict(commit=commit,
        purpose='Only missing Git blob bodies after raw host failed; official GitHub API same tree',
        no_weight_or_model=True))
    accepted = {}
    for name in ['README.md', 'LICENSE.MIT', 'pytorch/models.py',
                 'pytorch/pytorch_utils.py', 'metadata/class_labels_indices.csv']:
        entry = paths[name]
        response = read(direct_get('https://api.github.com/repos/qiuqiangkong/audioset_tagging_cnn/git/blobs/'+entry['sha'],
            name.replace('/', '__')+'.api.json'))
        raw = base64.b64decode(response['content'])
        if len(raw) != entry['size'] or hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest() != entry['sha']:
            raise ValueError('Git blob mismatch')
        path = ROOT/'author'/name.replace('/', '__')
        with path.open('xb') as stream:
            stream.write(raw)
        accepted[name] = reference(path)
        print('ACCEPTED', name, len(raw), flush=True)
    write(ROOT/'author_source_acceptance.json', dict(commit=commit,
        repo='qiuqiangkong/audioset_tagging_cnn', files=accepted))
    for line in (ROOT/'author/README.md').read_text().splitlines():
        if any(k in line.lower() for k in ['decisionlevelatt', 'zenodo', 'license']):
            print('README', line, flush=True)


if __name__ == '__main__':
    main()
