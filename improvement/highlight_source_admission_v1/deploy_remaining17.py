"""Adopt passed CPU contracts; repair explicit location of the existing RGB helper."""
import base64
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).parent
REPORT=HERE.parents[1]/'reports/highlight_source_admission_20261021_v1'
ROOT='/home/inspur/aic_video_work/highlight_source_admission_20261021_v1/matched_hl_pilot16'
PREP='''import sys
from pathlib import Path
ROOT=Path(ROOT_VALUE)
sys.path.insert(0,str(ROOT/'code'))
sys.path.append('/home/inspur/aic_video_work/i3d_umt_cross_domain_20261021_v1/crossdata12/code')
from pilot15_common import read,checked,ref,save
from pilot15_prepare import render
registration=read(ROOT/'registration.json')
checked(registration['protected_baseline']);checked(registration['control_checkpoint'])
if list((ROOT/'inputs').rglob('acceptance.json')):raise ValueError('No successful RGB may be re-rendered')
rows=[render(source) for source in registration['sources']]
save(ROOT/'input_acceptance.json',dict(state='PASS4_FIRST_REAL_I3D_INPUTS',sources=rows,
    CPU_contracts_adopted=ref(ROOT/'new_CPU_contracts.json'),no_previous_RGB_success=True,
    original_native_mapping_adopted=True,held_labels_not_in_loss=True))
'''.replace('ROOT_VALUE',repr(ROOT))
CONTROLLER='''import sys,os,subprocess,traceback
from pathlib import Path
ROOT=Path(ROOT_VALUE);sys.path.insert(0,str(ROOT/'code'))
from pilot15_common import ENGINEERING,read,checked,ref,save
from pilot15_controller import PY,WRAPPER,stage
CONTROL=Path(__file__).parent
try:
    save(CONTROL/'claim.json',dict(scope='Remaining first RGB/GPU/review only;3CPU checks adopted'))
    if read(ROOT/'new_CPU_contracts.json')['status']!='PASS':raise ValueError('Original passed CPU checks absent')
    if (ROOT/'gpu_launch.json').exists() or (ROOT/'input_acceptance.json').exists():raise ValueError('No successful stage may repeat')
    with (CONTROL/'prepare.log').open('x') as log:
        p=subprocess.Popen([str(PY),'-B','-u',str(CONTROL/'prepare.py')],cwd=ROOT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
        save(CONTROL/'prepare_launch.json',dict(pid=p.pid,command=p.args,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=p.wait()
    save(CONTROL/'prepare_terminal.json',dict(exit_code=code))
    if code:raise RuntimeError('First remaining RGB preparation failed')
    files={p.name:ref(p) for p in (ROOT/'code').glob('*.py')}
    files.update({'remaining17_'+p.name:ref(p) for p in CONTROL.glob('*.py')})
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),code=files,
        adopted_old_code={'runtime':ref(ENGINEERING/'runtime.py'),'profile_gpu':ref(ENGINEERING/'profile_gpu.py'),
            'existing_RGB_helper':ref(ENGINEERING/'crossdata12/code/prepare_raw.py')},
        inputs=ref(ROOT/'input_acceptance.json'),registration=ref(ROOT/'registration.json'),
        adopted_CPU_contracts=ref(ROOT/'new_CPU_contracts.json'),wrapper=ref(WRAPPER)))
    stage('gpu',True);stage('review')
    checked(read(ROOT/'registration.json')['protected_baseline'])
    save(ROOT/'completion_remaining17.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        old15_and16_failures_preserved=True,new_ZIP=0,baseline40_47_unchanged=True,no_automatic_production=True))
except BaseException:
    save(CONTROL/'failure.json',dict(traceback=traceback.format_exc(),no_automatic_retry=True))
    raise
'''.replace('ROOT_VALUE',repr(ROOT))


def main():
    payload=json.dumps({name:base64.b64encode(text.encode()).decode() for name,text in
        [('prepare.py',PREP),('controller.py',CONTROLLER)]})
    script=r'''
import base64,json,pathlib,os,subprocess,time,hashlib
root=pathlib.Path(ROOT_VALUE);failure=json.loads((root/'failure.json').read_text())
if 'prepare' not in failure['traceback'] or (root/'gpu_launch.json').exists():raise ValueError('Recovery boundary differs')
helper=root.parent.parent/'i3d_umt_cross_domain_20261021_v1/crossdata12/code/prepare_raw.py'
if not helper.is_file():raise ValueError('Exact original RGB helper absent')
payload=json.loads(PAYLOAD);target=root/'remaining17';target.mkdir()
for name,data in payload.items():
 with (target/name).open('xb') as stream:stream.write(base64.b64decode(data))
with (target/'registration.json').open('x') as stream:json.dump(dict(
 previous_failure=str(root/'failure.json'),adopted_CPU_contracts=str(root/'new_CPU_contracts.json'),
 original_helper_path=str(helper),original_helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
 no_successful_new_RGB_or_GPU=True,scientific_protocol_unchanged=True),stream,indent=2)
with (target/'controller.log').open('x') as log:
 p=subprocess.Popen(['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-u',str(target/'controller.py')],cwd=root,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 a=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=p.args,time=time.time())
 with (target/'launch.json').open('x') as stream:json.dump(a,stream,indent=2)
 print(json.dumps(a))
'''.replace('ROOT_VALUE',repr(ROOT)).replace('PAYLOAD',repr(payload))
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','aic-inspur-tailscale',
        '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
        input=script.encode(),capture_output=True,timeout=60)
    receipt=dict(returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode())
    with (REPORT/'remaining17_launch.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    print(json.dumps(receipt))
    if result.returncode:raise RuntimeError('Actual remaining17 deployment failed')


if __name__=='__main__':main()
