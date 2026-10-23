"""Deploy only necessary control code; run one new bounded author metadata stage."""
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
    REPORT.mkdir(exist_ok=True)
    files = {name: base64.b64encode((HERE / name).read_bytes()).decode()
             for name in ['common.py', 'lvsum20.py']}
    script = '''import base64,json,pathlib,subprocess,os,hashlib
root=pathlib.Path(ROOT_VALUE);root.mkdir();code=root/'code';code.mkdir()
files=json.loads(FILES_VALUE)
for name,encoded in files.items():
 data=base64.b64decode(encoded)
 with (code/name).open('xb') as stream:stream.write(data)
 assert hashlib.sha256(data).hexdigest()==hashlib.sha256((code/name).read_bytes()).hexdigest()
with (root/'metadata20.log').open('x') as log:
 p=subprocess.Popen([PY_VALUE,'-B','-u',str(code/'lvsum20.py')],cwd=root,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 launch=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=p.args)
 with (root/'metadata20_launch.json').open('x') as out:json.dump(launch,out,indent=2)
 print(json.dumps(launch))
'''.replace('ROOT_VALUE', repr(ROOT)).replace('FILES_VALUE', repr(json.dumps(files))).replace('PY_VALUE', repr(PY))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-home', PY + ' -'], input=script.encode(), capture_output=True, timeout=50)
    receipt = dict(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
                   deployed_bytes=sum((HERE / name).stat().st_size for name in files), alias='aic-inspur-home')
    with (REPORT / 'metadata20_launch.json').open('x', encoding='utf-8') as out:
        json.dump(receipt, out, ensure_ascii=False, indent=2)
    print(json.dumps(receipt))
    if result.returncode:
        raise RuntimeError('Bounded metadata deployment failed; inspect before any retry')


if __name__ == '__main__':
    main()
