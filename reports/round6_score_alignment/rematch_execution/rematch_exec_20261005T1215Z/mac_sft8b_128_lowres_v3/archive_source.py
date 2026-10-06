from pathlib import Path
import json,shutil,hashlib
HERE=Path(__file__).resolve().parent
DST=HERE/'frozen_mac_package';DST.mkdir(exist_ok=False)
names=list(json.loads((HERE/'source_lock.json').read_text())['files'])+['source_lock.json','CONTINUE_MAC.md',
 'controller/sealed_handoff.json','controller/finish_mac_launch.json']
for name in names:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
(DST/'verify_archive.py').write_text('''from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
lock=root/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='fbb48910afe94eb8ab6aa50db1a2eb3174cab2d4c264be65c8aec6205e46dd0a'
entries=json.loads(lock.read_text())['files']
for name,digest in entries.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
receipt=dict(status='PASS_MAC_V3_BOUND_SOURCE_ARCHIVE',bound_files=len(entries),source_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
(root/'archive_verification.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
''')
print(str(DST))
