"""Seal the independent repair using existing read-only verified assets."""
import argparse
import json
import subprocess
from mac_contract import verify_lock,HERE,ASSET_ROOT
from finish_mac import resources,CTRL,write,read,utc
from sft_contract import require,sha256

p=argparse.ArgumentParser();p.add_argument('--expected-lock',required=True);args=p.parse_args()
lock=verify_lock(HERE/'source_lock.json',args.expected_lock)
receipt=read(HERE/'preparation_receipt.json')
require(receipt['status']=='PASS_MAC_REAL_CPU_ACCEPTANCE_AND_PINNED_ENVIRONMENT' and receipt['tests']==8,
        'real CPU/environment acceptance missing')
asset=read(ASSET_ROOT/'controller/asset_http_completion.json')
require(asset['status']=='PASS_MAC_PINNED_MODEL_AND_704_TRAIN_MEDIA_TRANSFER' and
        asset['all_sizes_and_sha256_match'],'read-only asset reuse not verified')
config=read(HERE/'config.json')
planned=config['planned_output_bytes']+15335424*4+48*6144*32+134217728
current=resources(planned,read(HERE/'linux_capacity_snapshot.json'))
require(not current['external_compute'],'Mac external computation conflicts with registered work')
checked=subprocess.run([config['python'],'-B',str(HERE/'test_phase_gate.py')],capture_output=True,text=True)
require(checked.returncode==0,'phase gate acceptance failed')
write(CTRL/'sealed_handoff.json',dict(status='PASS_MAC_SOURCE_ENVIRONMENT_CPU_AND_PROJECTED_CAPACITY_HANDOFF',
    checked_utc=utc(),source_lock_sha256=args.expected_lock,bound_files=len(lock['files']),
    cpu_tests=8,phase_gate_tests=3,asset_root=str(ASSET_ROOT),
    asset_completion_sha256=sha256(ASSET_ROOT/'controller/asset_http_completion.json'),
    resources=current,training_started=False))
print(json.dumps(read(CTRL/'sealed_handoff.json'),ensure_ascii=False))
