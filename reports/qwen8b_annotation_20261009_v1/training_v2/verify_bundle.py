"""Verify the selected portable release before preflight, training or prediction."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    root = Path(root).resolve(strict=True)
    path = root / 'training_v2/selected_manifest.json'
    if not path.exists():
        raise ValueError('Selected release manifest missing')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for relative, expected in manifest['files'].items():
        p = (root / relative).resolve(strict=True)
        if not p.is_relative_to(root):
            raise ValueError('Manifest path escapes dataset root')
        if p.stat().st_size != expected['bytes']:
            raise ValueError('Changed file size: ' + relative)
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        if h.hexdigest() != expected['sha256']:
            raise ValueError('Changed file hash: ' + relative)
    return {'status': 'PASS_SELECTED_RELEASE_ALL_FILE_HASHES', 'files': len(manifest['files']),
            'bytes': sum(x['bytes'] for x in manifest['files'].values())}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dataset-root', required=True)
    args = p.parse_args()
    print(json.dumps(verify(args.dataset_root)))
