"""Windows small-code deployment; all data/compute remain on Linux."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[2] / 'reports/i3d_umt_cross_domain_20261021_v1'
REMOTE = '/home/inspur/aic_video_work/i3d_umt_cross_domain_20261021_v1/crossdata12'
PROTOCOL = dict(
    name='I3D_UMT_SUMME_TO_VIDEOXUM12', seed=7312, learning_rate=1e-4, updates=400,
    train=20, dev=5, held_dataset=8, train_dataset='SumMe', held_dataset_name='VideoXum',
    split='Five SumMe dev by SHA256 I3D_UMT_SUMME_DEV12:name; rest20 train; all8 VideoXum held',
    target='All original human summary columns: mean(user_score>0), native64 disjoint cells',
    loss='Full-source native-frame-weighted soft BCE, source equal, final checkpoint only',
    feature_profile='Frozen Meta RGB I3D-R50, eight samples/64 native frames, short256 center224 mean.45 std.225; L2 feature norm',
    auxiliary_parameters=34252497, total_parameters=8816809946,
    gpu_seconds=dict(features=1200,train=1200), output_policy='No automatic426 or ZIP',
    history='All33 sources historically exposed; held dataset means no labels from this dataset in this new UMT fit, not globally unseen',
    controls=['Existing external TIME/B masks at their original coverage (not claimed exact40.47 reconstruction)',
              'Source-balanced ridge lambda1 on identical features and labels',
              'Fixed half-sequence circular content shift through same final UMT'],
    selection='Exactly match per-source inherited external-control selected-frame count; stable native-order ties; no held-threshold tuning',
    review_gate=dict(held_macro_F1_gain_over_existing_control=.005,
                     held_macro_F1_gain_over_ridge=.005,
                     held_macro_F1_gain_over_content_shift=.005,
                     held_sources_improved_over_existing=5,max_per_source_F1_loss=.05),
    scope='Noncommercial student research, no original-data redistribution; temporal summary proxy, no crop IoU or official-score claims',
    no_new_dataset_or_model_downloads=True, protected_baseline_score=40.47,
    protected_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    former_skating_protocol='Superseded BEFORE any training by explicit user instruction to change dataset; old registrations/failures unchanged',
    forbidden=['Official test labels/training','Closed service official video upload','Network/service changes','CONTROL5 signals','Automatic site submission'],
)


def main():
    names = ['common.py','prepare.py','features.py','train.py','checks.py']
    files = {n:base64.b64encode((HERE/n).read_bytes()).decode() for n in names}
    envelope = dict(files=files,protocol=PROTOCOL)
    raw = json.dumps(envelope)
    script = r'''
import json,sys,base64,pathlib,os,subprocess,hashlib
root=pathlib.Path(REMOTE_PATH)
payload=json.loads(PAYLOAD)
root.mkdir()
(root/'code').mkdir()
for name,encoded in payload['files'].items():
 data=base64.b64decode(encoded)
 (root/'code'/name).write_bytes(data)
with (root/'protocol.json').open('x') as f:json.dump(payload['protocol'],f,ensure_ascii=False,indent=2)
bundle={n:hashlib.sha256((root/'code'/n).read_bytes()).hexdigest() for n in payload['files']}
with (root/'code_deployment.json').open('x') as f:json.dump({'sha256':bundle,'via':'PREVIOUSLY_AUTHORIZED_TAILSCALE_SMALL_CONTROL_ONLY'},f,indent=2)
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
log=(root/'prepare.log').open('x')
p=subprocess.Popen([py,'-u','-B',str(root/'code/prepare.py')],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=pathlib.Path('/proc')/str(p.pid)/'stat'
result={'pid':p.pid,'start_ticks':stat.read_text().rsplit(')',1)[1].split()[19],'argv':[py,'-u','-B',str(root/'code/prepare.py')],'root':str(root),'control_bytes':sum(len(base64.b64decode(s)) for s in payload['files'].values()),'code_sha256':bundle}
with (root/'prepare_launch.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
'''.replace('REMOTE_PATH',repr(REMOTE)).replace('PAYLOAD',repr(raw))
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
             'aic-inspur-tailscale','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -']
    result=subprocess.run(command,input=script.encode(),capture_output=True,timeout=60)
    receipt=dict(returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode(),
                 remote_root=REMOTE,source_control='authorized small SSH code, not media download')
    REPORT.mkdir(exist_ok=True,parents=True)
    with (REPORT/'crossdata12_prepare_launch.json').open('x',encoding='utf-8') as f:
        json.dump(receipt,f,ensure_ascii=False,indent=2)
    if result.returncode:
        raise RuntimeError(receipt)
    print(receipt['stdout'])
    with (REPORT/'crossdata12_protocol.json').open('x',encoding='utf-8') as f:
        json.dump(PROTOCOL,f,ensure_ascii=False,indent=2)


if __name__ == '__main__':
    main()
