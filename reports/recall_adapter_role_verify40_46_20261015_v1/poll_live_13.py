"""Single short read-only SSH observation; no watcher or launcher."""
import json
from pathlib import Path
import subprocess

REPORT=Path(__file__).resolve().parent
code=(REPORT/'short_fresh_status_10.py').read_text(encoding='utf8')
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
    '-o','ConnectTimeout=8','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2',
    'aic-inspur-home','python3 -'],input=code,encoding='utf8',text=True,capture_output=True,timeout=30)
if result.returncode:
    raise RuntimeError('Read-only observation failed, not evidence of model failure: '+result.stderr[-2000:])
value=json.loads(result.stdout)
(REPORT/'last_live_snapshot_13.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
launch=json.loads((REPORT/'fresh_chain_launch_09.json').read_text(encoding='utf8'))
parent=[row for row in value['processes'] if row['pid']==launch['pid'] and row['start_ticks']==launch['start_ticks']]
state_path=REPORT/'current_state.json'
state=json.loads(state_path.read_text(encoding='utf8'))
gpu_stages={name:value['stages'].get(prefix+'/gpu_01',{}) for name,prefix in
    [('B0','confirm/B0'),('VERIFY','confirm/VERIFY'),('POSITIVE','MAIN/confirm/POSITIVE')]}
accepted=sum(row.get('ACCEPTED',0) for row in gpu_stages.values())
begun=sum(row.get('BEGIN',0) for row in gpu_stages.values())
chain=value['stages'].get('confirm/chain_01',{})
state.update(stage=chain.get('completion.json',{}).get('status',
    'ENGINEERING_FAILURE' if 'failure.json' in chain else 'RUNNING_FROZEN_FIRST_FRESH_CONFIRM'),
    actual_model_calls=10+accepted,actual_model_calls_counter_scope='COMPLETED_ACCEPTED_DEV10_PLUS_FRESH',
    fresh_actual_model_calls_begun_at_snapshot=begun,fresh_actual_GPU_model_calls_at_snapshot=accepted,
    fresh_per_stage_accepted_at_snapshot={name:row.get('ACCEPTED',0) for name,row in gpu_stages.items()},
    fresh_unique_terminals_at_snapshot=value['unique_terminals'],
    status_checked_utc=value['utc'],exact_original_parent_alive_at_snapshot=bool(parent),
    production_admitted=False,actual_zips=0)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(utc=value['utc'],exact_parent_alive=bool(parent),
    processes=[dict(pid=row['pid'],ppid=row['ppid'],state=row['state'],start_ticks=row['start_ticks'],
        script=next((part for part in row['argv'].split() if part.endswith('.py')),row['argv']),
        io=row['io']) for row in value['processes']],
    stages=value['stages'],unique_terminals=value['unique_terminals'],gpu=value['gpu']),ensure_ascii=False))
