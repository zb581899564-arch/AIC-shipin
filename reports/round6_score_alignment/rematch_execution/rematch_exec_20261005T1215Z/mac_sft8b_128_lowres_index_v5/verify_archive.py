from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
lock=root/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='25f7b9df1a0a452c9187043bbc7d9fe2bf4658d232afcfb9f1d7dd4c8cb30fc5'
entries=json.loads(lock.read_text())['files']
for name,digest in entries.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
receipt=dict(status='PASS_MAC_INDEX_V5_BOUND_SOURCE_ARCHIVE',bound_files=len(entries),source_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
(root/'archive_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
