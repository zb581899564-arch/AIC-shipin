"""Merge only the verified prefix length; preserve the late-flushed old prefix."""
import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'QWEN8B_TRAINING_PREP_V2_20261009.zip'
SIZE=1269695818
OFFSET=56295424
EXPECTED='45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
PREFIX_SHA='6dd84f800c3bad5a06faa2bc69a6992802af6501a67954d1824f14bfd7a67bd4'
def hash_range(start,length):
    h=hashlib.sha256()
    with SOURCE.open('rb') as f:
        f.seek(start)
        while length:
            b=f.read(min(1<<20,length));assert b
            h.update(b);length-=len(b)
    return h.hexdigest()
assert SOURCE.stat().st_size==SIZE and hash_range(0,SIZE)==EXPECTED
assert hash_range(0,OFFSET)==PREFIX_SHA
width=(SIZE-OFFSET+7)//8
parts=[{'part':i,'bytes':min(width,SIZE-OFFSET-i*width),
        'sha256':hash_range(OFFSET+i*width,min(width,SIZE-OFFSET-i*width)),
        'path':f'/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2.transfer_parts/part_{i:02d}.bin'}
       for i in range(8)]
code=f'''import hashlib,json,os
from pathlib import Path
p=Path('/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2.incoming.zip')
old=p.with_name('qwen8b_annotation_20261009_v2.scp_raw_prefix.zip')
assert p.resolve(strict=True)==p and p.stat().st_size>={OFFSET}
assert not old.exists() and not old.is_symlink()
original_bytes=p.stat().st_size
def read_exact(f,length):
 while length:
  b=f.read(min(1<<20,length));assert b
  yield b;length-=len(b)
h=hashlib.sha256()
with p.open('rb') as f:
 for b in read_exact(f,{OFFSET}):h.update(b)
assert h.hexdigest()=={PREFIX_SHA!r}
parts={parts!r}
for part in parts:
 q=Path(part['path']);assert q.resolve(strict=True)==q and q.stat().st_size==part['bytes']
 h=hashlib.sha256()
 with q.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 assert h.hexdigest()==part['sha256']
p.rename(old)
h=hashlib.sha256()
with p.open('xb') as out:
 with old.open('rb') as f:
  for b in read_exact(f,{OFFSET}):out.write(b);h.update(b)
 for part in parts:
  with Path(part['path']).open('rb') as f:
   for b in iter(lambda:f.read(1<<20),b''):out.write(b);h.update(b)
 out.flush();os.fsync(out.fileno())
assert p.stat().st_size=={SIZE} and h.hexdigest()=={EXPECTED!r}
print(json.dumps({{'status':'PASS_REMOTE_ZIP_SIZE_SHA','bytes':p.stat().st_size,'sha256':h.hexdigest(),
 'path':str(p),'verified_prefix_bytes':{OFFSET},'preserved_prefix_actual_bytes':original_bytes,
 'late_buffered_bytes_omitted':original_bytes-{OFFSET},'all_parts_sha_verified':True,'new_data_transferred':0}}))
'''
encoded=base64.b64encode(code.encode()).decode()
cmd=['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
     '-o','ConnectTimeout=20','aic-inspur-home',
     'python3 -B -c "import base64;exec(base64.b64decode(\''+encoded+'\'))"']
receipt=json.loads(subprocess.check_output(cmd,text=True))
receipt.update({'utc':datetime.now(timezone.utc).isoformat(),'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX',
                'training_started':False,'parts':parts,'preserved_initial_merge_failure':True,
                'initial_merge_failure_reason':'Early receiver flushed another 542720 bytes after its parent was stopped; exact-size guard refused merge before mutating files',
                'repair':'Recheck all part hashes and read only the exact already-verified prefix length'})
with (HERE/'transfer_completion.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
