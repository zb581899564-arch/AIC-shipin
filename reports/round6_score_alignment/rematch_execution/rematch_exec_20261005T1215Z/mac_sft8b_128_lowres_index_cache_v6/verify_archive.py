from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
lock=root/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='d936c5a76e89f0360010ce3fd29ada8c7e353e4aec360cc145a298605fe21cba'
entries=json.loads(lock.read_text())['files']
for name,digest in entries.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
receipt=dict(status='PASS_MAC_INDEX_CACHE_V6_BOUND_SOURCE_ARCHIVE',bound_files=len(entries),source_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
(root/'archive_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
