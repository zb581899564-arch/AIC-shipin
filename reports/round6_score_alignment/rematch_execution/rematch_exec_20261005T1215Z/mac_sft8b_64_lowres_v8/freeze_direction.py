from pathlib import Path
import json,hashlib,datetime as dt,ast
HERE=Path(__file__).resolve().parent
old=json.loads((HERE.parent/'mac_sft8b_128_lowres_mps_v7/source_lock.json').read_text())
names=[name.replace('controller/cpu_acceptance_03.log','controller/cpu_acceptance_64_01.log') for name in old['files']]
for name in names:
    if name.endswith('.py'):ast.parse((HERE/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b64_lowres_source_lock_v8',scope='MAC_8B_64_LOWRES_INTERVAL_SFT_NONTEST',
 created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 files={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names})
with (HERE/'source_lock.json').open('x',encoding='utf-8') as f:f.write(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
print(hashlib.sha256((HERE/'source_lock.json').read_bytes()).hexdigest())
