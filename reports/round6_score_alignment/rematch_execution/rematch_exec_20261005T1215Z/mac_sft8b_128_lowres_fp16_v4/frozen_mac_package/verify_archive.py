from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
lock=root/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='4424de75341b5249fe5be2f42b428d1e0cfea9b86fc9e75e3fffa06b32454a7c'
entries=json.loads(lock.read_text())['files']
for name,digest in entries.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
receipt=dict(status='PASS_MAC_FP16_V4_BOUND_SOURCE_ARCHIVE',bound_files=len(entries),source_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
(root/'archive_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
