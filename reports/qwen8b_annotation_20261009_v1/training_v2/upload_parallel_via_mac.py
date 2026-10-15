"""Transfer disjoint ZIP ranges through Mac; preserve and verify existing prefix."""
import base64
import concurrent.futures
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'QWEN8B_TRAINING_PREP_V2_20261009.zip'
SIZE = 1269695818
EXPECTED = '45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
STAGE = '/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2.incoming.zip'
PARTS = '/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2.transfer_parts'
SSH = ['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
       '-o','ConnectTimeout=20','-o','ServerAliveInterval=30','-o','ServerAliveCountMax=3','aic-inspur-home']
def command(code):
    encoded = base64.b64encode(code.encode()).decode()
    return SSH + ['python3 -c "import base64;exec(base64.b64decode(\'' + encoded + '\'))"']
def digest(start, length):
    h=hashlib.sha256()
    with SOURCE.open('rb') as f:
        f.seek(start)
        while length:
            b=f.read(min(1<<20,length))
            assert b
            h.update(b);length-=len(b)
    return h.hexdigest()
assert SOURCE.stat().st_size==SIZE and digest(0,SIZE)==EXPECTED
setup=f'''import hashlib,json
from pathlib import Path
p=Path({STAGE!r});d=Path({PARTS!r})
assert p.resolve(strict=True)==p and not p.is_symlink()
assert d.parent.resolve(strict=True)==d.parent and not d.exists() and not d.is_symlink()
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''):h.update(b)
d.mkdir()
print(json.dumps({{'size':p.stat().st_size,'sha256':h.hexdigest()}}))
'''
prefix=json.loads(subprocess.check_output(command(setup),text=True))
offset=prefix['size']
assert 0<=offset<SIZE and digest(0,offset)==prefix['sha256']
workers=8
width=(SIZE-offset+workers-1)//workers
ranges=[(i,offset+i*width,min(width,SIZE-offset-i*width)) for i in range(workers) if offset+i*width<SIZE]
progress={i:0 for i,_,_ in ranges}
def upload(item):
    i,start,length=item
    expected=digest(start,length)
    target=f'{PARTS}/part_{i:02d}.bin'
    code=f'''import hashlib,json,os,sys
from pathlib import Path
p=Path({target!r})
assert p.parent.resolve(strict=True)==p.parent and not p.exists() and not p.is_symlink()
h=hashlib.sha256();remaining={length}
with p.open('xb') as f:
 while remaining:
  b=sys.stdin.buffer.read(min(1<<20,remaining))
  if not b:raise ValueError('Incomplete transfer; partial retained')
  f.write(b);h.update(b);remaining-=len(b)
 f.flush();os.fsync(f.fileno())
assert p.stat().st_size=={length} and h.hexdigest()=={expected!r}
print(json.dumps({{'part':{i},'start':{start},'bytes':{length},'sha256':h.hexdigest(),'path':str(p)}}))
'''
    with (HERE/f'upload_part_{i:02d}.stderr.log').open('xb') as err:
        p=subprocess.Popen(command(code),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err)
        try:
            with SOURCE.open('rb') as f:
                f.seek(start);remaining=length
                while remaining:
                    b=f.read(min(1<<20,remaining));assert b
                    p.stdin.write(b);remaining-=len(b);progress[i]+=len(b)
            p.stdin.close()
            result=p.stdout.read().decode()
            assert p.wait()==0,result
        finally:
            if not p.stdin.closed:p.stdin.close()
        return json.loads(result)
started=time.monotonic()
print(json.dumps({'stage':'VERIFIED_PREFIX_PARALLEL_MAC_TRANSFER','prefix':prefix,'connections':workers}),flush=True)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
    pending={pool.submit(upload,r) for r in ranges}
    while pending:
        done,pending=concurrent.futures.wait(pending,timeout=20,return_when=concurrent.futures.FIRST_COMPLETED)
        for future in done:results.append(future.result())
        elapsed=time.monotonic()-started
        sent=offset+sum(progress.values())
        print(json.dumps({'stage':'DISJOINT_UPLOAD_VIA_MAC','sent_bytes':sent,'total_bytes':SIZE,
                          'percent':round(sent/SIZE*100,2),'verified_parts':len(results),
                          'elapsed_seconds':round(elapsed,1),'average_bytes_per_second':round((sent-offset)/elapsed)}),flush=True)
merge=f'''import hashlib,json,os
from pathlib import Path
p=Path({STAGE!r});old=p.with_name('qwen8b_annotation_20261009_v2.scp_raw_prefix.zip')
assert p.stat().st_size=={offset} and not old.exists() and not old.is_symlink()
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''):h.update(b)
assert h.hexdigest()=={prefix['sha256']!r}
p.rename(old)
sources=[old]+[Path(x['path']) for x in sorted({results!r},key=lambda x:x['part'])]
h=hashlib.sha256()
with p.open('xb') as out:
 for source in sources:
  with source.open('rb') as f:
   for b in iter(lambda:f.read(1<<20),b''):out.write(b);h.update(b)
 out.flush();os.fsync(out.fileno())
assert p.stat().st_size=={SIZE} and h.hexdigest()=={EXPECTED!r}
print(json.dumps({{'status':'PASS_REMOTE_ZIP_SIZE_SHA','bytes':p.stat().st_size,'sha256':h.hexdigest(),'path':str(p)}}))
'''
receipt=json.loads(subprocess.check_output(command(merge),text=True))
receipt.update({'utc':datetime.now(timezone.utc).isoformat(),'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX',
                'verified_prefix_bytes':offset,'prefix_preserved':True,'parts':sorted(results,key=lambda x:x['part']),
                'elapsed_seconds':time.monotonic()-started,'training_started':False})
with (HERE/'transfer_completion.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
