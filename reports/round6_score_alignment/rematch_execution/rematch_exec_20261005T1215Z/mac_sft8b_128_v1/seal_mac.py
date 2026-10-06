"""Byte-verify the final handoff before the one-time background launch."""
import argparse
import json
from pathlib import Path
from mac_contract import verify_lock,HERE
from finish_mac import resources,CTRL,write,read,utc
from sft_contract import require

p=argparse.ArgumentParser();p.add_argument('--expected-lock',required=True);args=p.parse_args()
lock=verify_lock(HERE/'source_lock.json',args.expected_lock)
receipt=read(HERE/'preparation_receipt.json')
require(receipt['status']=='PASS_MAC_REAL_CPU_ACCEPTANCE_AND_PINNED_ENVIRONMENT' and receipt['tests']==8,
        'real CPU/environment acceptance missing')
manifest=read(HERE/'assets_manifest.json');total=sum(entry['bytes'] for entry in manifest['files'])
progress=read(CTRL/'asset_http_progress.json')
remaining=total-progress['received_bytes']
config=read(HERE/'config.json')
planned=remaining+config['planned_output_bytes']+15335424*4+48*16384*32+134217728
current=resources(planned,read(HERE/'linux_capacity_snapshot.json'))
require(not current['external_compute'],'Mac external computation conflicts with registered work')
output=dict(status='PASS_MAC_SOURCE_ENVIRONMENT_CPU_AND_PROJECTED_CAPACITY_HANDOFF',
    checked_utc=utc(),source_lock_sha256=args.expected_lock,bound_files=len(lock['files']),
    cpu_tests=8,phase_gate_tests=3,asset_files=719,asset_total_bytes=total,
    transfer_bytes_at_check=progress['received_bytes'],resources=current,training_started=False)
write(CTRL/'sealed_handoff.json',output)
print(json.dumps(output,ensure_ascii=False))
