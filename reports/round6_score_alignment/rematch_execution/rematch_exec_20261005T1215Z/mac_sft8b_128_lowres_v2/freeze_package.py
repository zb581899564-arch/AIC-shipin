"""Local explicit-file repair registration and hash lock; run once before launch."""
from pathlib import Path
import datetime as dt
import hashlib
import json
HERE=Path(__file__).resolve().parent
config=json.loads((HERE/'config.json').read_text())
config['scientific_change']='Explicit Qwen3VL VIDEO size total budget n_sampled*32768 (old image max_pixels did not constrain videos); fresh nested kwargs preserve metadata/no-resampling; seq<=6144; same128 ordinals, data and SFT optimization'
(HERE/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
names=['authorization.json','config.json','environment_final_freeze.txt','preparation_receipt.json',
 'linux_capacity_snapshot.json','model_receipt.json','original_train.jsonl','r7_train_registry.json',
 'full_train.jsonl','smoke_train.jsonl','probe_train.jsonl','source_map.json','sft_contract.py','row_contract.py',
 'train_sft.py','temporal_common.py','hash_helpers.py','mac_inputs.py','mac_contract.py','train_mac.py',
 'test_mac_cpu.py','phase_gate.py','test_phase_gate.py','finish_mac.py','seal_mac.py','status_mac.py',
 'record_preflight.py','launch_owned_mac.py','PROTOCOL.md','controller/cpu_acceptance_03.log']
lock=dict(schema='aic_mac_8b128_lowres_source_lock_v2',created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 scope='MAC_8B_128_LOWRES_INTERVAL_SFT_NONTEST',files={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names})
with (HERE/'source_lock.json').open('x',encoding='utf-8') as f:f.write(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
print(hashlib.sha256((HERE/'source_lock.json').read_bytes()).hexdigest())
