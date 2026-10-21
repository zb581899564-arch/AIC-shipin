"""Receive only a final accepted ZIP and a compact receipt over authorized SSH."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

H=Path(__file__).resolve().parent
WORK=H.parents[1]
CANDIDATE=sys.argv[1]
assert CANDIDATE in ('critic','contrast')
RECOVERY19 = len(sys.argv) == 3 and sys.argv[2] == '--recovery19'
assert len(sys.argv) == 2 or RECOVERY19
assert not RECOVERY19 or CANDIDATE == 'contrast'
R='/home/inspur/aic_video_work/content_choice_20261019_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
ALIAS='aic-inspur-tailscale'
BASELINE=WORK/'deliveries/CONTEXT_SEMANTIC_RESIDUAL_8B_20261016/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
BASE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'

def sha(blob):return hashlib.sha256(blob).hexdigest()
def save_new(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def canonical(rows):
    data=[{k:r[k] for k in ['video_id','targetRatioWH','predictions']} for r in rows]
    data.sort(key=lambda x:x['video_id'])
    return sha(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def read_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
        payload=z.read('predictions.jsonl')
    rows=[json.loads(s) for s in payload.splitlines() if s.strip()]
    assert len(rows)==426 and len({r['video_id'] for r in rows})==426
    return payload,rows

source=r'''
from pathlib import Path
import hashlib,json,zipfile
R=Path(RUN_ROOT);candidate=CANDIDATE
parent_name=('package_contrast_remaining_controller_completion19.json' if RECOVERY19 else 'package_'+candidate+'_controller_completion09.json')
package_name='package_contrast_remaining19' if RECOVERY19 else 'package_'+candidate
parent=json.loads((R/parent_name).read_text())
assert parent['status']=='PACKAGE_AND_INDEPENDENT_QA_NATURALLY_COMPLETED_WINDOWS_DELIVERY_PENDING'
result=json.loads((R/package_name/'completion.json').read_text())
receipt=result['receipt'];assert receipt['status']=='NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN'
if RECOVERY19:
 assert receipt['execution_recovery']=='REMAINING_CPU_CLOCK_BRIDGE19'
 assert result['original_failure_preserved'] is True and result['no_models_or_replay_repeated'] is True
 compatibility=json.loads(Path(receipt['exact_frame_clock_compatibility_ref']['path']).read_text())
 assert compatibility['status']=='PASS_ALL426_EXACT_POINTS_AND_SELECTED_FRAME_DOMAINS'
 assert compatibility['selected_ordinals_unchanged'] is True
ref=receipt['zip_ref'];p=Path(ref['path']).resolve(strict=True)
assert p.is_relative_to(R) and p.name.endswith('.zip')
b=p.read_bytes();assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']
with zipfile.ZipFile(p) as z:
 assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
 payload=z.read('predictions.jsonl');member=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
v=json.loads(Path(receipt['independent_validation_ref']['path']).read_text());assert len(v['checks'])==11 and all(v['checks'].values()) and not v['strict_loader_issues']
print(json.dumps(dict(zip_ref=ref,member=member,records=receipt['records'],frames=receipt['frames'],added_frames=receipt['added_frames'],removed_frames=receipt['removed_frames'],empty_source_ids=receipt['empty_source_ids'],actual_pipeline_parameters=receipt['actual_pipeline_parameters'],canonical_sha256=receipt['canonical_sha256'],strict_checks_passed=11,protected_baseline_ref=receipt['protected_baseline_ref'],official_score='UNKNOWN',website_submitted=False)))
'''
source='RUN_ROOT='+repr(R)+'\nCANDIDATE='+repr(CANDIDATE)+'\nRECOVERY19='+repr(RECOVERY19)+'\n'+source
r=subprocess.run(['ssh','-o','ConnectTimeout=15',ALIAS,PY+' -B -'],input=source,text=True,capture_output=True,timeout=60)
print(r.stderr,file=sys.stderr);r.check_returncode();remote=json.loads(r.stdout)
target=WORK/('deliveries/CONTENT_CHOICE_'+CANDIDATE.upper()+'_8B_20261020')
target.mkdir(exist_ok=True)
final=target/Path(remote['zip_ref']['path']).name
partial=target/(final.name+'.partial01')
claim=H/('windows_delivery_'+CANDIDATE+'_started10.json')
save_new(claim,dict(utc=datetime.now(timezone.utc).isoformat(),remote=remote,partial=str(partial),final=str(final),route=ALIAS))
if final.exists():
    assert final.stat().st_size==remote['zip_ref']['bytes'] and sha(final.read_bytes())==remote['zip_ref']['sha256']
    received=final
else:
    assert not partial.exists(), 'Preserve prior partial, require explicit remaining recovery'
    subprocess.run(['scp','-o','ConnectTimeout=15',ALIAS+':'+remote['zip_ref']['path'],str(partial)],check=True,timeout=180)
    received=partial
blob=received.read_bytes()
assert len(blob)==remote['zip_ref']['bytes'] and sha(blob)==remote['zip_ref']['sha256']
payload,rows=read_zip(received)
assert len(payload)==remote['member']['bytes'] and sha(payload)==remote['member']['sha256']
assert BASELINE.stat().st_size==384630 and sha(BASELINE.read_bytes())==BASE_SHA
_,original=read_zip(BASELINE)
assert {(r['video_id'],tuple(r['targetRatioWH'])) for r in rows}=={(r['video_id'],tuple(r['targetRatioWH'])) for r in original}
assert all(abs(r['model_params_b']-remote['actual_pipeline_parameters']/1e9)<1e-12 for r in rows)
current=canonical(rows);assert current==remote['canonical_sha256'];assert current!=canonical(original)
frame_count=sum(len(r['predictions']) for r in rows)
checked=0
for history in (WORK/'deliveries').glob('*/*.zip'):
    if history.resolve() in {final.resolve(),received.resolve()}:continue
    try:
        _,historical=read_zip(history)
    except (AssertionError,KeyError,zipfile.BadZipFile,json.JSONDecodeError):continue
    if frame_count==sum(len(r['predictions']) for r in historical):
        assert current!=canonical(historical), 'Same predictions as historical package: '+str(history)
    checked+=1
if received!=final:received.rename(final)
receipt=dict(status='FINAL_ZIP_WINDOWS_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN',utc=datetime.now(timezone.utc).isoformat(),
    candidate=CANDIDATE,local_zip=str(final),bytes=len(blob),sha256=sha(blob),member_sha256=sha(payload),
    records=426,history_packages_distinct=checked,canonical_sha256=current,remote=remote,
    protected_baseline_unchanged=True,automatic_website_submission=False,explicit_remaining_clock_recovery19=RECOVERY19)
save_new(target/'WINDOWS_DELIVERY_RECEIPT.json',receipt)
save_new(H/('windows_delivery_'+CANDIDATE+'_completion10.json'),receipt)
# Only the compact receipt goes back; no intermediate evidence is moved.
ack='from pathlib import Path\nimport json\np=Path('+repr(R)+')/'+repr('windows_delivery_'+CANDIDATE+'_completion10.json')+'\nwith p.open("x") as f:json.dump('+repr(receipt)+',f,ensure_ascii=False,indent=2)\nprint("WINDOWS_FINAL_DELIVERY_RECEIPT_SAVED")\n'
ack_result=subprocess.run(['ssh','-o','ConnectTimeout=15',ALIAS,PY+' -B -'],input=ack,text=True,encoding='utf-8',capture_output=True,timeout=45)
save_new(H/('windows_delivery_'+CANDIDATE+'_ack10.json'),dict(exit_code=ack_result.returncode,stdout=ack_result.stdout,stderr=ack_result.stderr))
print(json.dumps(receipt,ensure_ascii=False));print(ack_result.stdout);print(ack_result.stderr,file=sys.stderr)
ack_result.check_returncode()
