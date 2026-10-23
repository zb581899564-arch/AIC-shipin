"""One named small-code stage with exclusive launch claim and content identity."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).parent
REPORT = HERE.parents[1] / 'reports/general_highlight_supervision_20261021_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
ROOT = '/home/inspur/aic_video_work/general_highlight_supervision_20261021_v1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage')
    parser.add_argument('--files', nargs='+', required=True)
    args = parser.parse_args()
    if not args.stage.isidentifier() or any(Path(name).name != name for name in args.files):
        raise ValueError('Only explicit code basenames and a named stage allowed')
    files = {name: base64.b64encode((HERE / name).read_bytes()).decode() for name in args.files}
    script = '''import base64,json,pathlib,subprocess,os,hashlib
root=pathlib.Path(ROOT_VALUE);code=root/'code';stage=STAGE_VALUE
claim=root/(stage+'_claim.json')
with claim.open('x') as out:json.dump(dict(stage=stage,scope='Only new explicit remaining work; no old successes repeated'),out)
files=json.loads(FILES_VALUE)
for name,encoded in files.items():
 data=base64.b64decode(encoded)
 with (code/name).open('xb') as stream:stream.write(data)
 assert hashlib.sha256(data).hexdigest()==hashlib.sha256((code/name).read_bytes()).hexdigest()
with (root/(stage+'.log')).open('x') as log:
 p=subprocess.Popen([PY_VALUE,'-B','-u',str(code/(stage+'.py'))],cwd=root,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 launch=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=p.args,
   code_sha256={n:hashlib.sha256((code/n).read_bytes()).hexdigest() for n in files})
 with (root/(stage+'_launch.json')).open('x') as out:json.dump(launch,out,indent=2)
 print(json.dumps(launch))
'''.replace('ROOT_VALUE', repr(ROOT)).replace('FILES_VALUE', repr(json.dumps(files))).replace('PY_VALUE', repr(PY)).replace('STAGE_VALUE', repr(args.stage))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-home', PY + ' -'], input=script.encode(), capture_output=True, timeout=50)
    receipt = dict(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
                   deployed_bytes=sum((HERE / name).stat().st_size for name in files), alias='aic-inspur-home')
    with (REPORT / (args.stage + '_launch.json')).open('x', encoding='utf-8') as out:
        json.dump(receipt, out, ensure_ascii=False, indent=2)
    print(json.dumps(receipt))
    if result.returncode:
        raise RuntimeError('Actual deployment failed; inspect claim and files before recovery')


if __name__ == '__main__':
    main()
