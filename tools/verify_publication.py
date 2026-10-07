"""Verify exported bytes and submission archive identities without datasets or GPUs."""
from pathlib import Path
import ast
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((ROOT/'docs/publication_manifest.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        path = ROOT/row['path']
        assert path.is_file(), 'missing '+row['path']
        assert path.stat().st_size == row['bytes'], 'size '+row['path']
        assert sha(path) == row['sha256'], 'hash '+row['path']
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
    print(json.dumps(dict(status='PASS_PUBLICATION',manifest_files=len(manifest['files']),python_syntax_files=code_count,submission_archives=len(packages),source_hashes='PASS',zip_crc='PASS',excluded_asset_scan='PASS',secret_pattern_scan='PASS'),ensure_ascii=False))

if __name__ == '__main__':
    main()
