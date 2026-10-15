"""Resume an exact verified ZIP prefix over the required SSH Mac jump."""
import base64
import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'QWEN8B_TRAINING_PREP_V2_20261009.zip'
EXPECTED = '45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
SIZE = 1269695818
STAGE = '/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2.incoming.zip'
SSH = ['ssh', '-o', 'ProxyJump=macmini', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
       'aic-inspur-home']

def command(code):
    encoded = base64.b64encode(code.encode()).decode()
    return SSH + ['python3 -c "import base64;exec(base64.b64decode(\'' + encoded + '\'))"']

def digest(path, limit=None):
    h = hashlib.sha256()
    with path.open('rb') as f:
        remaining = path.stat().st_size if limit is None else limit
        while remaining:
            chunk = f.read(min(1 << 20, remaining))
            if not chunk:
                raise ValueError('Unexpected EOF')
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()

assert SOURCE.stat().st_size == SIZE and digest(SOURCE) == EXPECTED
probe = f'''import hashlib,json
from pathlib import Path
p=Path({STAGE!r})
assert p.resolve()==p and p.is_file() and not p.is_symlink()
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''): h.update(b)
print(json.dumps({{'size':p.stat().st_size,'sha256':h.hexdigest()}}))
'''
prefix = json.loads(subprocess.check_output(command(probe), text=True))
offset = prefix['size']
assert 0 <= offset < SIZE and digest(SOURCE, offset) == prefix['sha256'], 'Remote prefix differs'
receiver = f'''import hashlib,json,os,sys
from pathlib import Path
p=Path({STAGE!r})
assert p.resolve()==p and not p.is_symlink() and p.stat().st_size=={offset}
remaining={SIZE-offset}
with p.open('ab') as f:
 while remaining:
  b=sys.stdin.buffer.read(min(1<<20,remaining))
  if not b: raise ValueError('Transfer ended early; verified prefix preserved')
  f.write(b);remaining-=len(b)
 f.flush();os.fsync(f.fileno())
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''): h.update(b)
assert p.stat().st_size=={SIZE} and h.hexdigest()=={EXPECTED!r}
print(json.dumps({{'status':'PASS_REMOTE_ZIP_SIZE_SHA','bytes':p.stat().st_size,'sha256':h.hexdigest(),'path':str(p)}}),flush=True)
'''
print(json.dumps({'stage':'PREFIX_VERIFIED_RAW_SSH_RESUME','offset':offset,'size':SIZE}), flush=True)
process = subprocess.Popen(command(receiver), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=(HERE/'upload_raw_ssh.stderr.log').open('xb'))
progress = {'sent':offset, 'error':None}
def writer():
    try:
        with SOURCE.open('rb') as f:
            f.seek(offset)
            for block in iter(lambda:f.read(1 << 20), b''):
                process.stdin.write(block)
                progress['sent'] += len(block)
        process.stdin.close()
    except Exception as e:
        progress['error'] = repr(e)
        process.stdin.close()
t = threading.Thread(target=writer)
t.start()
started=time.monotonic()
while t.is_alive():
    t.join(20)
    elapsed=time.monotonic()-started
    print(json.dumps({'stage':'UPLOAD_VIA_MAC','sent_bytes':progress['sent'],'total_bytes':SIZE,
                      'percent':round(progress['sent']/SIZE*100,2),'elapsed_seconds':round(elapsed,1),
                      'average_bytes_per_second':round((progress['sent']-offset)/elapsed)}),flush=True)
result=process.stdout.read().decode()
code=process.wait()
if code or progress['error']:
    raise RuntimeError({'exit_code':code,'writer_error':progress['error'],'remote_output':result})
receipt=json.loads(result)
receipt.update({'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX','prefix_verified_bytes':offset,
                'training_started':False,'elapsed_seconds':time.monotonic()-started})
with (HERE/'transfer_completion.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
