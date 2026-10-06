"""Read-only independent hashes of the archived Mac experiment package."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
archive=HERE/'frozen_mac_package'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
lock_path=archive/'source_lock.json'
assert digest(lock_path)=='5b80284ffdd372725ac02088098f7378d63ab013698d71aa353297a48f327257'
lock=json.loads(lock_path.read_text());results=[]
for name,expected in lock['files'].items():
    path=archive/name
    assert path.is_file() and digest(path)==expected,name
    results.append(dict(name=name,sha256=expected,bytes=path.stat().st_size))
receipt=dict(status='PASS_INDEPENDENT_LINUX_ARCHIVED_MAC_SOURCE_SHA256',files=len(results),
    source_lock_sha256=digest(lock_path),all_sha256_match=True,results=results)
with (HERE/'archive_verification_01.json').open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({key:value for key,value in receipt.items() if key!='results'}))
