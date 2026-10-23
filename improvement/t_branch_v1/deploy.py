"""Deploy exactly named small control files once to the new independent T root."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).parent
ROOT = '/home/inspur/aic_video_work/t_branch_execution_20261022_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
REPORT = HERE.parents[1] / 'reports/t_branch_execution_20261022_v1'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('stage'); parser.add_argument('--files', nargs='+', required=True)
    parser.add_argument('--alias', choices=['aic-inspur-home', 'aic-inspur-tailscale'], default='aic-inspur-home',
                        help='Explicit already-authorized small control route; never an automatic fallback')
    args = parser.parse_args()
    if not args.stage.isidentifier() or any(Path(name).name != name for name in args.files):
        raise ValueError('Explicit stage/code names only')
    payload = {}
    for name in args.files:
        content = (HERE / name).read_bytes()
        if name.endswith('.py'):
            ast.parse(content.decode('utf-8-sig'), filename=name)
        payload[name] = base64.b64encode(content).decode()
    script = '''import base64,hashlib,json,os,pathlib,subprocess,socket
root=pathlib.Path(ROOT_VALUE);root.mkdir(exist_ok=True);code=root/'code';code.mkdir(exist_ok=True)
if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Host identity differs')
stage=STAGE_VALUE
with (root/(stage+'_claim.json')).open('x') as f:json.dump(dict(stage=stage,only_explicit_new_stage=True),f)
files=json.loads(FILES_VALUE)
for name,encoded in files.items():
 data=base64.b64decode(encoded)
 with (code/name).open('xb') as f:f.write(data)
 if hashlib.sha256((code/name).read_bytes()).hexdigest()!=hashlib.sha256(data).hexdigest():raise ValueError('Code transfer identity differs')
with (root/(stage+'.log')).open('x') as log:
 p=subprocess.Popen([PY_VALUE,'-B','-u',str(code/(stage+'.py'))],cwd=root,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 record=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=p.args,code_sha256={n:hashlib.sha256((code/n).read_bytes()).hexdigest() for n in files})
 with (root/(stage+'_launch.json')).open('x') as f:json.dump(record,f,indent=2)
 print(json.dumps(record))
'''.replace('ROOT_VALUE', repr(ROOT)).replace('STAGE_VALUE', repr(args.stage)).replace('FILES_VALUE', repr(json.dumps(payload))).replace('PY_VALUE', repr(PY))
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
            args.alias, PY + ' -'], input=script.encode(), capture_output=True, timeout=45)
    except subprocess.TimeoutExpired as error:
        receipt = dict(state='OBSERVATION_TIMEOUT_REMOTE_OUTCOME_UNKNOWN', stage=args.stage,
            timeout_seconds=45, alias=args.alias, no_automatic_retry=True,
            stdout=(error.stdout or b'').decode(errors='replace'),
            stderr=(error.stderr or b'').decode(errors='replace'),
            expected_code_sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in args.files})
        with (REPORT / (args.stage + '_launch_timeout.json')).open('x', encoding='utf8') as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
        raise RuntimeError('Deployment outcome unknown; inspect exact remote claim/files/handles before any recovery') from error
    receipt = dict(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
        bytes=sum((HERE / name).stat().st_size for name in args.files), alias=args.alias)
    with (REPORT / (args.stage + '_launch.json')).open('x', encoding='utf8') as f: json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(json.dumps(receipt))
    if result.returncode: raise RuntimeError('Deployment not accepted; inspect claim/files before recovery')


if __name__ == '__main__': main()
