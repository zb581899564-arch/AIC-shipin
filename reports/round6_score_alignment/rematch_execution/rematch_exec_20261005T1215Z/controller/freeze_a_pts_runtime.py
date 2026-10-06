"""Archive exactly the production files referenced by the four runtime locks."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
CODE = HERE.parent/'baseline_a_pts_v1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', type=int, required=True)
    parser.add_argument('--expected-lock', required=True)
    args = parser.parse_args()
    if sha(CODE/'source_lock.json') != args.expected_lock:
        raise RuntimeError('source lock differs from the intended frozen snapshot')
    names = set()
    for lock in ('source_lock.json','snapshot_lock.json','vendor_lock.json','additional_frozen_dependencies.json'):
        names.add(lock)
        for record in json.loads((CODE/lock).read_text())['files']:
            name = record['path']
            path = (CODE/name).resolve()
            if CODE.resolve() not in path.parents or sha(path) != record['sha256']:
                raise RuntimeError('invalid locked file: '+name)
            names.add(name)
    archive = HERE/f'a_pts_runtime_{args.revision:02d}.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as output:
        for name in sorted(names):
            output.write(CODE/name,name)
    receipt = dict(revision=args.revision, source_lock_sha256=args.expected_lock,
        archive_sha256=sha(archive), files={name:sha(CODE/name) for name in sorted(names)},
        only_locked_production_sources=True, media_or_weights_included=False)
    with (HERE/f'a_pts_runtime_{args.revision:02d}.archive.json').open('x') as stream:
        json.dump(receipt,stream,indent=2)
        stream.write('\n')
    print(json.dumps(dict(archive=archive.name,sha256=receipt['archive_sha256'],files=len(names))))
