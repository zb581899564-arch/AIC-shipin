"""Deploy necessary small controls; no data or model crosses to Windows."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).parent
REPORT=HERE.parents[1]/'reports/highlight_source_admission_20261021_v1'
ROOT='/home/inspur/aic_video_work/highlight_source_admission_20261021_v1/matched_hl_pilot15'
PROTOCOL=dict(name='UPM4_MATCHED_HL_SUPERVISION_PILOT15',seed=7315,updates=200,
    learning_rate=1e-4,train_sources=3,held_sport_sources=1,held_sport='diving',
    split='Frozen native13 SHA256 UPM-SportCLIP-v1/name; last source held, other3 development',
    purpose='New dense-performance HL/NHL supervision feasibility, NOT broad T main training or automatic production',
    model='Adopt old final400-update UMT summary checkpoint, continue exactly200 new updates; frozen Meta I3D and BASE/TIME unchanged',
    feature_profile='Adopt previous RGB I3D:8 samples per64native frames; short256 center224 mean.45 std.225; L2 norm',
    loss='Native known-frame weighted BCE per source, sources equal; UN weight0; final checkpoint only',
    held_AP_gain=.03,held_shift_AP_gain=.03,equal_training_coverage_F1_gain_required='strictly positive',
    coverage='Training3-source known positive fraction only; matched-ranking diagnostic, no held threshold scan',
    controls=['Old saved summary UMT on same NEW4 sources','Fixed half-sequence content shift through same new final model'],
    old_successful_features_or_models_not_rerun_on_old_sources=True,
    no_8B_calls_or_updates=True,no_new_model_download=True,new_GPU_budget_seconds=600,
    independent_review='All known native frames, tied-score AP independently recomputed, UN neverNHL',
    source_scope='4 static-camera athletic-performance recordings; one held sport, NOT general highlight truth or80sources',
    labels_previously_read_for_native_admission=True,blind_test_claim=False,
    even_positive_result_requires_broader_evidence_and_exact_TIME_bridge_before426=True,
    protected_baseline_score=40.47,protected_baseline_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    no_automatic426_or_ZIP_or_site_submission=True,no_Goal_or_automation=True)


def main():
    files={path.name:base64.b64encode(path.read_bytes()).decode()
        for path in HERE.glob('pilot15_*.py')}
    envelope=dict(files=files,sha256={name:hashlib.sha256(base64.b64decode(value)).hexdigest()
        for name,value in files.items()},protocol=PROTOCOL)
    remote=r'''
import base64,hashlib,json,os,pathlib,subprocess,time
payload=json.loads(PAYLOAD)
root=pathlib.Path(ROOT_VALUE);root.mkdir()
code=root.parent.parent/'highlight_source_control_20261021_v1'
for name,encoded in payload['files'].items():
 data=base64.b64decode(encoded)
 if hashlib.sha256(data).hexdigest()!=payload['sha256'][name]:raise ValueError('Small code SHA differs')
 with (code/name).open('xb') as stream:stream.write(data)
with (root/'protocol.json').open('x') as stream:json.dump(payload['protocol'],stream,indent=2)
with (root/'deployment.json').open('x') as stream:json.dump(dict(code_sha256=payload['sha256'],small_control_bytes=sum(len(base64.b64decode(v)) for v in payload['files'].values())),stream,indent=2)
with (root/'controller.log').open('x') as log:
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
 process=subprocess.Popen(['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-u',str(code/'pilot15_controller.py')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 result=dict(pid=process.pid,start_ticks=pathlib.Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=process.args,root=str(root),code_sha256=payload['sha256'],time=time.time())
 with (root/'controller_launch.json').open('x') as stream:json.dump(result,stream,indent=2)
 print(json.dumps(result))
'''.replace('PAYLOAD',repr(json.dumps(envelope))).replace('ROOT_VALUE',repr(ROOT))
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
        'aic-inspur-tailscale','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
        input=remote.encode(),capture_output=True,timeout=60)
    REPORT.mkdir(parents=True,exist_ok=True)
    receipt=dict(returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode())
    with (REPORT/'pilot15_launch.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    with (REPORT/'pilot15_protocol.json').open('x',encoding='utf-8') as stream:json.dump(PROTOCOL,stream,indent=2)
    print(json.dumps(receipt))
    if result.returncode:raise RuntimeError('Actual deployment failed; inspect receipt before any retry')


if __name__=='__main__':main()
