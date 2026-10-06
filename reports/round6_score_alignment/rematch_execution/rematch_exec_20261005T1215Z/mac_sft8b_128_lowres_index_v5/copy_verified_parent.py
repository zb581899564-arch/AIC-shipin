from pathlib import Path
import json,hashlib,shutil
root=Path('/Users/choubk/codex-workspace/projects/aic-video')
src=root/'mac_sft8b_128_lowres_20261006T0720Z';dst=root/'mac_sft8b_128_lowres_index_20261006T0728Z'
assert src.is_dir() and not src.is_symlink() and dst.is_dir() and not dst.is_symlink()
lock=src/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='fbb48910afe94eb8ab6aa50db1a2eb3174cab2d4c264be65c8aec6205e46dd0a'
for name,digest in json.loads(lock.read_text())['files'].items():
    source=src/name;assert not source.is_symlink() and hashlib.sha256(source.read_bytes()).hexdigest()==digest
    target=dst/name;assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
print('PASS_MAC_LOCAL_VERIFIED_ASSET_FREE_SOURCE_FORK')
