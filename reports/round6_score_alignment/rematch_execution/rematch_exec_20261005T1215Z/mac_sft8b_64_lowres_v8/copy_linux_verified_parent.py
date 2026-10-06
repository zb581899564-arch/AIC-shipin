from pathlib import Path
import json,hashlib,shutil
ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
SRC=ROOT/'mac_sft8b_128_lowres_v3/frozen_mac_package'
DST=ROOT/'mac_sft8b_64_lowres_v8/frozen_mac_package'
assert not SRC.is_symlink() and ROOT in SRC.resolve().parents
lock=SRC/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='fbb48910afe94eb8ab6aa50db1a2eb3174cab2d4c264be65c8aec6205e46dd0a'
DST.mkdir(exist_ok=False)
for name,digest in json.loads(lock.read_text())['files'].items():
    source=SRC/name;assert not source.is_symlink() and hashlib.sha256(source.read_bytes()).hexdigest()==digest
    target=DST/name;assert ROOT in target.resolve().parents
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
print('PASS_LINUX_LOCAL_VERIFIED_MAC_SOURCE_FORK')
