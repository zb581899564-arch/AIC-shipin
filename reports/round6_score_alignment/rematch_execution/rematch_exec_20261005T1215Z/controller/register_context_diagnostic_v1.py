"""Deploy small control files and run sequential CPU registration over existing SSH."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

RUN = Path(__file__).resolve().parent.parent
REMOTE = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
ENTRY = 'teacher_context_diagnostic_v1'
NAMES = ('PROTOCOL.md', 'prompt.txt', 'diagnostic.py', 'cpu_tests.py', 'prepare.py', 'launch.py', 'CONTINUE.md')


def remote(script, *, echo=True):
    command = PY + ' -B -'
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'aic-inspur-home', command],
                            input=script.encode('utf-8'), capture_output=True, timeout=600)
    if echo and result.stdout: print(result.stdout.decode('utf-8', errors='replace'), end='', flush=True)
    if result.stderr: print(result.stderr.decode('utf-8', errors='replace'), end='', flush=True)
    if result.returncode: raise RuntimeError('remote control failed: ' + str(result.returncode))
    return result.stdout


def deploy():
    payload = {name: {'sha256': hashlib.sha256((RUN / ENTRY / name).read_bytes()).hexdigest(),
                      'bytes': base64.b64encode((RUN / ENTRY / name).read_bytes()).decode()} for name in NAMES}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    remote("""import base64,hashlib,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r)/%r
payload=json.loads(base64.b64decode(%r))
root.mkdir(exist_ok=True)
for name,row in payload.items():
    assert name in %r
    path=root/name; data=base64.b64decode(row['bytes'])
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    if path.exists() and path.read_bytes()!=data:
        assert not (root/'source_lock.json').exists() and not (root/'registration.json').exists() and not (root/'start_receipt.json').exists(),'preserve frozen diagnostic file: '+name
        old=path.read_bytes(); archive=root/'prelock_repairs'; archive.mkdir(exist_ok=True)
        (archive/(name+'.'+hashlib.sha256(old).hexdigest())).write_bytes(old)
        for p in root.glob('*.stderr.txt'):
            if p.stat().st_size: (archive/(p.name+'.'+hashlib.sha256(p.read_bytes()).hexdigest())).write_bytes(p.read_bytes())
        path.write_bytes(data)
    elif path.exists(): assert path.read_bytes()==data
    else:
        assert not (root/'source_lock.json').exists() and not (root/'registration.json').exists()
        path.write_bytes(data)
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==row['sha256'] for name,row in payload.items())
print(json.dumps({'status':'PASS_SMALL_CONTEXT_CONTROL_DEPLOYMENT','files':len(payload),
 'bytes':sum(len(base64.b64decode(row['bytes'])) for row in payload.values()),'host':socket.gethostname()}))
""" % (REMOTE, ENTRY, encoded, NAMES))


def accept():
    remote("""import subprocess,json
from pathlib import Path
root=Path(%r)/%r
for name,args in [('cpu_tests.py',[]),('prepare.py',[]),('diagnostic.py',['--preflight'])]:
    result=subprocess.run([%r,'-B',str(root/name),*args],cwd=root,capture_output=True)
    (root/(name.replace('.py','')+'.stdout.txt')).write_bytes(result.stdout)
    (root/(name.replace('.py','')+'.stderr.txt')).write_bytes(result.stderr)
    print(result.stdout.decode(errors='replace'),flush=True)
    if result.returncode:
        print(result.stderr.decode(errors='replace'),flush=True)
        raise RuntimeError(name+' failed CPU registration')
""" % (REMOTE, ENTRY, PY))
    remote_files = ('manifest.json', 'source_lock.json', 'cpu_acceptance.json',
                    'cpu_tests.stdout.txt', 'cpu_tests.stderr.txt', 'prepare.stdout.txt', 'prepare.stderr.txt',
                    'diagnostic.stdout.txt', 'diagnostic.stderr.txt')
    raw = remote("""import base64,json
from pathlib import Path
root=Path(%r)/%r
print(json.dumps({name:base64.b64encode((root/name).read_bytes()).decode() for name in %r}))
""" % (REMOTE, ENTRY, remote_files), echo=False)
    for name, data in json.loads(raw).items():
        (RUN / ENTRY / name).write_bytes(base64.b64decode(data))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('deploy','accept','launch'))
    parser.add_argument('--entry',default=ENTRY);args=parser.parse_args()
    assert re.fullmatch(r'teacher_context_diagnostic_v[1-9][0-9]*',args.entry)
    ENTRY=args.entry
    if (RUN/ENTRY/'REPAIR.md').is_file(): NAMES=(*NAMES,'REPAIR.md')
    if (RUN/ENTRY/'review_prompt.txt').is_file(): NAMES=(*NAMES,'review_prompt.txt')
    if args.stage=='deploy': deploy()
    elif args.stage=='accept': accept()
    else: remote('import subprocess\nsubprocess.run([%r,"-B",%r],check=True)' % (PY, REMOTE+'/'+ENTRY+'/launch.py'))
