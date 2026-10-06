from pathlib import Path
import json,hashlib,datetime as dt,ast
HERE=Path(__file__).resolve().parent
old=json.loads((HERE.parent/'mac_sft8b_128_lowres_v2/source_lock.json').read_text())
names=list(old['files'])+['test_process_ownership.py']
for name in names:
    if name.endswith('.py'):ast.parse((HERE/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b128_lowres_source_lock_v3',scope=old['scope'],
 created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 parent_v2_source_lock_sha256=hashlib.sha256((HERE.parent/'mac_sft8b_128_lowres_v2/source_lock.json').read_bytes()).hexdigest(),
 files={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names})
with (HERE/'source_lock.json').open('x',encoding='utf-8') as f:f.write(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
print(hashlib.sha256((HERE/'source_lock.json').read_bytes()).hexdigest())
