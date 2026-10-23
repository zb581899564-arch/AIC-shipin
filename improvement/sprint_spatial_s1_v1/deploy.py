"""Deploy necessary small control code; sources/model/outputs remain on Linux."""
import ast
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/sprint_spatial_s1_20261021_v1'
REMOTE = '/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1'
PROTOCOL = dict(schema='S1_SPATIAL_DISTRIBUTION_DEPLOYMENT_GEOMETRY_20261021_V1',
    authoritative_plan='PROJECT_PRIMARY_PLAN_20261021.md; PR5@72533ece44cb490c48cea88fab41463bdf14eb3c',
    baseline_score=40.47, protected_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    scope='Noncommercial student research on author-native16 GNMC; no original media or annotations distributed',
    source_group='Publisher train/validation/test filename,bytes,dHash isolation; original photo provenance/global independence UNKNOWN',
    old200='Historical regression anchor only, prior trained adapter not reused as initialization; old scientific STOP unchanged',
    train_count=602, maximum_pool_per_role=200, evaluation_per_role=80,
    evaluation_selection='SHA256(S1_20261021:author_split:filename), exclude prior8+40 filenames/hashes and dHash<=6 to602train/all prior40/current eval',
    original_eval_splits=dict(dev='author validation', confirm='author test'),
    origin_url='https://zenodo.org/api/records/6228834/files/GNMC.zip/content', archive_bytes=363946070,
    model='Existing exact original frozen BASE for centers; fresh language-qkvo LoRA per arm, no vision/TIME changes',
    retired_input_recovery='602originalJPEG retained; retired RGB must first be recovered, RGB_SHA checked against accepted602. New shared pixels needed for center-conditioned profile, old files/locks never overwritten',
    processor_pixels=131072, max_sequence_tokens=2048, new_base_centers_max=762,
    center_prompt='Exact unchanged deployed Qwen.predict_focus(image,[16,9]); only raw picture, not human center or box',
    target=dict(W10='file_equal, original human relative width', W01='three human-width bins approximately equal, deployed-center maximum-reference-IoU width',
                W11='file_equal, deployed-center maximum-reference-IoU width'),
    input='Same pixel input/normalized frozen deployed center/sourceW,H/ratio/maxlegalwidth for all3arms; assistant targets only differ by declared objective',
    geometry='Max width min(W,H*16//9); integer width floor(max*relative/1000), minimum1; floatheightw*9/16 and original deployed round/clamp',
    condition_target='Enumerate relative1..1000 at frozen original center; exact ties prefer larger width then relative; only external train labels create targets',
    training=dict(rank=8,alpha=16,dropout=.05,lr=1e-4,optimizer='AdamW',weight_decay=0,grad_accum=8,
        proposed_steps=50,exact_steps_frozen_after_first8_cost_profile=True,seed=20261021,gradient_clip=1.0,
        initialize='Fresh same seed standard LoRA zeroB from original BASE for all3arms',final_checkpoint_only=True),
    sampling='W10/W11 same deterministic shuffled-file sequence; W01 cycle3 human-width bins shuffled within-bin. No source labels available; file-equal not global source-equal claim',
    risk=dict(mean_delta_gt=0,median_delta_ge=0,worst_decile_mean_ge=-.10,severe_loss_gt025_fraction_le=.05,invalid=0),
    development='Evaluate all3same80; freeze selected eligible arm by macro IoU, tie priorityW11,W10,W01, before one80confirm; no confirm tuning',
    checkpoint_selection='No intermediate checkpoint/epoch/lr/grid scan;50steps if actual cost fits total, else explicit record before training',
    GPU_total_seconds=7200, research_wall_seconds=14400, center_GPU_seconds_max=2400,
    remaining_output_budget_bytes=4*1024**3, bounded_small_code_transfer=True,
    automatic_production=False,new_goal_or_automation=False,new_author_or_crosschat_message=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control-recovery-tailscale', action='store_true')
    args = parser.parse_args()
    files = {}
    for p in sorted(HERE.glob('*.py')):
        if p.name == 'deploy.py':
            continue
        data = p.read_bytes()
        ast.parse(data, filename=p.name)
        files[p.name] = dict(base64=base64.b64encode(data).decode(), sha256=hashlib.sha256(data).hexdigest())
    payload = dict(files=files, protocol=PROTOCOL)
    script = '''
import ast,base64,json,hashlib,os,pathlib,subprocess,datetime
r=pathlib.Path(REMOTE);data=json.loads(PAYLOAD)
assert r.exists() and not (r/'prepare_claim.json').exists() and not (r/'code').exists()
(r/'code').mkdir()
for name,record in data['files'].items():
 raw=base64.b64decode(record['base64']);assert hashlib.sha256(raw).hexdigest()==record['sha256'];ast.parse(raw,filename=name)
 with (r/'code'/name).open('xb') as f:f.write(raw)
with (r/'protocol.json').open('x') as f:json.dump(data['protocol'],f,ensure_ascii=False,indent=2)
identity=dict(code_bytes=sum(len(base64.b64decode(x['base64'])) for x in data['files'].values()),code_sha256={k:v['sha256'] for k,v in data['files'].items()})
with (r/'code_acceptance.json').open('x') as f:json.dump(identity,f,indent=2)
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (r/'prepare_controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(r/'code/prepare_controller.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],root=str(r),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),**identity)
with (r/'prepare_launch.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
'''.replace('REMOTE', repr(REMOTE)).replace('PAYLOAD', repr(json.dumps(payload)))
    alias = 'aic-inspur-tailscale' if args.control_recovery_tailscale else 'aic-inspur-home'
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
        alias, '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
        input=script.encode(), capture_output=True, timeout=45)
    REPORT.mkdir(exist_ok=args.control_recovery_tailscale)
    receipt = dict(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
                   control_alias=alias, no_media_or_model_transfer=True)
    outputs = [('launch_remaining02.json', receipt)] if args.control_recovery_tailscale else [('launch.json', receipt), ('protocol.json', PROTOCOL)]
    for name, content in outputs:
        if (REPORT / name).exists():
            raise FileExistsError('Do not overwrite deploy result')
        (REPORT / name).write_bytes((json.dumps(content, ensure_ascii=False, indent=2)+'\n').encode())
    print(json.dumps(receipt, ensure_ascii=False))
    if result.returncode:
        raise RuntimeError('Small-code deploy failed; inspect actual state before any recovery')


if __name__ == '__main__':
    main()
