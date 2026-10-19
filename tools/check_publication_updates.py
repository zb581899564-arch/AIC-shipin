"""Synthetic temporary-root checks; never verifies or rewrites the real export."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

from verify_publication import verify_manifest_files


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def fixture(root, changed=True):
    (root/'docs').mkdir()
    original = b'original\n'
    stable = b'stable\n'
    (root/'source.txt').write_bytes(original)
    (root/'stable.txt').write_bytes(stable)
    manifest = dict(files=[dict(path='source.txt', bytes=len(original), sha256=digest(original)),
                          dict(path='stable.txt', bytes=len(stable), sha256=digest(stable))])
    base_path = root/'docs/publication_manifest.json'
    save(base_path, manifest)
    if not changed:
        return None
    edited, added = b'edited\n', b'new\n'
    (root/'source.txt').write_bytes(edited)
    (root/'new.txt').write_bytes(added)
    updates = dict(schema='AIC_PUBLICATION_UPDATES_V1', base_manifest_sha256=digest(base_path.read_bytes()),
                   base_commit='1' * 40, files=[
        dict(path='source.txt', previous_sha256=digest(original), bytes=len(edited), sha256=digest(edited)),
        dict(path='new.txt', previous_sha256=None, bytes=len(added), sha256=digest(added))])
    save(root/'docs/publication_updates.json', updates)
    return updates


def rejected(change, expected_message):
    with tempfile.TemporaryDirectory(prefix='aic_publication_updates_') as directory:
        root = Path(directory)
        updates = fixture(root)
        change(root, updates)
        save(root/'docs/publication_updates.json', updates)
        try:
            verify_manifest_files(root)
        except ValueError as error:
            assert expected_message in str(error), str(error)
        else:
            raise AssertionError('Expected rejection: ' + expected_message)


def main():
    with tempfile.TemporaryDirectory(prefix='aic_publication_updates_') as directory:
        root = Path(directory)
        fixture(root, changed=False)
        before = (root/'docs/publication_manifest.json').read_bytes()
        result = verify_manifest_files(root)
        assert result['manifest_files'] == result['base_manifest_files'] == 2
        assert result['publication_updates'] == 0
        assert (root/'docs/publication_manifest.json').read_bytes() == before
    with tempfile.TemporaryDirectory(prefix='aic_publication_updates_') as directory:
        root = Path(directory)
        fixture(root)
        before = (root/'docs/publication_manifest.json').read_bytes()
        result = verify_manifest_files(root, updates_path='docs/publication_updates.json')
        assert result['manifest_files'] == 3 and result['base_manifest_files'] == 2
        assert result['publication_updates'] == 2
        assert (root/'docs/publication_manifest.json').read_bytes() == before
    rejected(lambda root, value: value.update(base_manifest_sha256='0' * 64), 'base manifest SHA256')
    rejected(lambda root, value: value['files'][0].update(previous_sha256='0' * 64), 'previous SHA256')
    rejected(lambda root, value: value['files'][0].update(previous_sha256=None), 'previous SHA256')
    rejected(lambda root, value: value['files'][1].update(previous_sha256='0' * 64), 'previous SHA256')
    rejected(lambda root, value: value['files'][1].pop('previous_sha256'), 'previous SHA256')
    rejected(lambda root, value: value['files'].append(deepcopy(value['files'][0])), 'duplicate update path')
    rejected(lambda root, value: (root/'source.txt').write_bytes(b'tamper\n'), 'hash source.txt')
    rejected(lambda root, value: value['files'][1].update(bytes=999), 'size new.txt')
    rejected(lambda root, value: value['files'][1].update(path='../outside.txt'), 'noncanonical manifest path')
    rejected(lambda root, value: value['files'][1].update(path='docs/publication_manifest.json'), 'own manifest')
    rejected(lambda root, value: value['files'][1].update(path='docs/publication_updates.json'), 'own manifest')
    print('PASS_SYNTHETIC_PUBLICATION_BASE_COMPATIBILITY_UPDATES_BINDING_DUPLICATES_AND_ACTUAL_BYTES')


if __name__ == '__main__':
    main()
