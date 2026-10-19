"""Verify exported bytes and submission archive identities without datasets or GPUs."""
from pathlib import Path, PurePosixPath
import ast
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def manifest_row_path(root, row):
    require(isinstance(row, dict), 'manifest row must be an object')
    name = row.get('path')
    require(isinstance(name, str) and name and '\\' not in name, 'invalid manifest path')
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and '..' not in relative.parts and
            str(relative) == name and name != '.', 'noncanonical manifest path '+name)
    path = root/name
    require(path.resolve().is_relative_to(root), 'manifest path escaped root '+name)
    require(type(row.get('bytes')) is int and row['bytes'] >= 0 and
            isinstance(row.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', row['sha256']),
            'invalid bytes/SHA256 '+name)
    return path

def verify_manifest_files(root, updates_path=None):
    """Verify current files without changing the frozen publication manifest.

    Optional AIC_PUBLICATION_UPDATES_V1 files bind the original manifest bytes.
    previous_sha256 refers to that manifest's entry, and is explicitly null for
    a newly tracked path (which may already have existed outside the manifest).
    This function reads only the specified root and returns verification counts;
    it does not run the archive, syntax, excluded-asset or secret scans in main.
    """
    root = Path(root).resolve()
    base_path = root/'docs/publication_manifest.json'
    manifest = json.loads(base_path.read_text(encoding='utf-8'))
    require(isinstance(manifest, dict) and isinstance(manifest.get('files'), list), 'invalid base manifest')
    effective = {}
    for row in manifest['files']:
        manifest_row_path(root, row)
        require(row['path'] not in effective, 'duplicate base path '+row['path'])
        effective[row['path']] = row
    base_sha = sha(base_path)
    explicit_updates = updates_path is not None
    updates_path = Path(updates_path) if explicit_updates else root/'docs/publication_updates.json'
    if not updates_path.is_absolute():
        updates_path = root/updates_path
    require(updates_path.resolve().is_relative_to(root), 'updates path escaped root')
    update_count = 0
    if explicit_updates or updates_path.exists():
        updates = json.loads(updates_path.read_text(encoding='utf-8'))
        require(isinstance(updates, dict) and updates.get('schema') == 'AIC_PUBLICATION_UPDATES_V1', 'invalid updates schema')
        require(updates.get('base_manifest_sha256') == base_sha, 'updates base manifest SHA256 differs')
        changes = updates.get('files')
        require(isinstance(changes, list), 'updates files must be a list')
        seen = set()
        for row in changes:
            path = manifest_row_path(root, row)
            name = row['path']
            require(path.resolve() not in (base_path.resolve(), updates_path.resolve()), 'updates cannot replace their own manifest '+name)
            require(name not in seen, 'duplicate update path '+name)
            seen.add(name)
            previous = effective.get(name)
            require('previous_sha256' in row and row['previous_sha256'] ==
                    (previous['sha256'] if previous is not None else None), 'updates previous SHA256 differs '+name)
            effective[name] = row
        update_count = len(changes)
    for name, row in effective.items():
        path = root/name
        require(path.is_file(), 'missing '+name)
        require(path.stat().st_size == row['bytes'], 'size '+name)
        require(sha(path) == row['sha256'], 'hash '+name)
    return dict(manifest_files=len(effective), base_manifest_files=len(manifest['files']),
                publication_updates=update_count, base_manifest_sha256=base_sha)

def main():
    manifest_counts = verify_manifest_files(ROOT)
    packages = json.loads((ROOT/'docs/submission_packages.json').read_text(encoding='utf-8'))
    for row in packages:
        path = ROOT/row['package']
        assert sha(path) == row['zip_sha256'], 'package hash '+row['id']
        assert path.stat().st_size == row['zip_bytes'], 'package size '+row['id']
        assert (ROOT/row['evidence']).is_file(), 'score evidence '+row['id']
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, 'CRC '+row['id']
            assert archive.namelist() == ['predictions.jsonl'], 'members '+row['id']
            rows = [json.loads(line) for line in archive.read('predictions.jsonl').decode('utf-8-sig').splitlines() if line.strip()]
            if row['stage'] == '复赛':
                assert len(rows) == 426, '426 records '+row['id']
    code_count = 0
    for path in ROOT.rglob('*.py'):
        if '.git' in path.parts:
            continue
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        code_count += 1
    blocked = re.compile(r'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----|(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})|\bsk-[A-Za-z0-9_-]{25,}|(?:X-Amz-Signature|X-Goog-Signature|[?&]access_token)=[A-Za-z0-9%._-]{12,}')
    forbidden = {'.safetensors','.gguf','.whl','.incomplete','.pt','.pth','.onnx','.mp4','.mkv','.mov','.avi','.pem','.key'}
    for path in ROOT.rglob('*'):
        if not path.is_file() or '.git' in path.parts:
            continue
        assert path.suffix.lower() not in forbidden, 'excluded asset '+str(path)
        assert path.stat().st_size < 50*1024**2, 'large file '+str(path)
        if path.suffix.lower() in {'.py','.sh','.ps1','.md','.json','.txt','.yaml','.yml','.html','.js','.jsonl'}:
            assert not blocked.search(path.read_text(encoding='utf-8-sig',errors='replace')), 'secret '+str(path)
    print(json.dumps(dict(status='PASS_PUBLICATION',**manifest_counts,python_syntax_files=code_count,submission_archives=len(packages),source_hashes='PASS',zip_crc='PASS',excluded_asset_scan='PASS',secret_pattern_scan='PASS'),ensure_ascii=False))

if __name__ == '__main__':
    main()
