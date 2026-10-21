"""Deploy only small source/protocol through the currently observed direct SSH."""
import ast
import base64
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/video_text_grounding_20261021_v1'
REMOTE = '/home/inspur/aic_video_work/video_text_grounding_20261021_v1'
PROTOCOL = dict(
    mechanism='Official frozen K400 X-CLIP-B32 pretrained cross-frame and temporal integration',
    hypothesis='Learned video/text representation improves event separation and uses within-cell temporal order',
    comparison='New frozen encoder versus completed static CLIP meanframe; not a pure causal isolation of pretraining, architecture or parameter count',
    sources='Same historical VideoXum8 V00..V07,512native64cells,26 raw human ActivityNet event queries',
    target='Broad event timestamps only, NOT shortened highlight truth or unconditional highlights',
    inputs='Adopt all existing uint8 8sample224center pixels, native counts and CLIP token identities; zero new decode',
    model='Microsoft VideoX X-CLIP, Kinetics400 supervised, B32 8frames; all tensors frozen and strict-loaded',
    author_commit='1744b2159c3d11694f94dab4fcde8660c685e79a',
    weight_url='https://github.com/nbl97/X-CLIP_Model_Zoo/releases/download/v1.0/k400_32_8.pth',
    weight_bytes=786503179, publisher_digest=None,
    scope='MIT source; research on already admitted public external data; K400/pretraining overlap UNKNOWN',
    parameter_rule='Actual full protected baseline plus XCLIP<=9B; replaces staticCLIP encoder, does not ensemble both; baseline ZIP unchanged',
    runtime_port='Original forward methods unchanged; replace initializer import with torch trunc_normal_, remove unused einops/path side effects; every checkpoint tensor strictly replaces initialization',
    direct_only=True, automatic_proxy_or_model_fallback=False,
    controls=['same-pixel8frame reversal','circular next-caption same-video','next-source query','half-cell sequence shift','constant prevalence'],
    metric='Native-frame tie-grouped AP, event-average then source-macro; same previous26queries andtargets',
    gate=dict(within_gain=.03,cross_gain=.05,shift_gain=.03,constant_gain=.05,sources=6,static_gain=.02,reverse_gain=.005),
    interpretation='Passing permits only a separately registered automatic-query pilot, never direct426 production. Failure preserves STOP, no prompt/threshold/checkpoint sweep.',
    gpu_max_seconds=1200,planned_output_bytes=90000000,real_cells=512,reverse_cells=512,
    video_batch_cells=8,text_forward_batches=1,new_training_steps=0,new_qwen_calls=0,
    baseline_score=40.47,protected_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    no_goal_timer_author_crosschat_or_auto_submission=True,
)


def main():
    names = ['common.py','assets.py','model_io.py','prepare.py','contracts.py','infer.py','review.py','audit.py','controller.py']
    files = {}
    for name in names:
        data = (HERE / name).read_bytes()
        ast.parse(data, filename=name)
        files[name] = base64.b64encode(data).decode()
    payload = json.dumps(dict(files=files, protocol=PROTOCOL))
    script = r'''
import ast,pathlib,json,base64,subprocess,os,hashlib
r=pathlib.Path(REMOTE)
data=json.loads(PAYLOAD)
r.mkdir();(r/'code').mkdir()
for name,value in data['files'].items():
 raw=base64.b64decode(value);ast.parse(raw,filename=name)
 with (r/'code'/name).open('xb') as f:f.write(raw)
with (r/'protocol.json').open('x') as f:json.dump(data['protocol'],f,ensure_ascii=False,indent=2)
identity={'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'code').glob('*.py')},'code_bytes':sum(len(base64.b64decode(s)) for s in data['files'].values())}
with (r/'code_acceptance.json').open('x') as f:json.dump(identity,f,indent=2)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (r/'controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(r/'code/controller.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out={'pid':p.pid,'start_ticks':pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],'root':str(r),'code_bytes':identity['code_bytes'],'automatic_production':False}
with (r/'launch.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
'''.replace('REMOTE', repr(REMOTE)).replace('PAYLOAD', repr(payload))
    command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
               'aic-inspur-home','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -']
    result = subprocess.run(command, input=script.encode(), capture_output=True, timeout=50)
    receipt = dict(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode())
    REPORT.mkdir()
    for name, value in [('launch.json', receipt), ('protocol.json', PROTOCOL)]:
        with (REPORT / name).open('x',encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))
    assert result.returncode == 0


if __name__ == '__main__':
    main()
