"""Read-only SSH inspector code via stdin, private small summary and delta."""
import datetime as dt
import json
from register_b2_package_v1 import RUN,remote

def main():
    code=(RUN/'controller/inspect_spatial_gap8_slot4_v2.py').read_text(encoding='utf-8')
    raw=remote(code+'\nprint(json.dumps(capture(),ensure_ascii=False))\n',echo=False)
    snapshot=json.loads(raw);out=RUN/'controller/monitor_spatial_gap8_slot4_v2';out.mkdir(exist_ok=True)
    old=json.loads((out/'latest.json').read_bytes()) if (out/'latest.json').exists() else {}
    current=snapshot['artifacts'];before=old.get('artifacts',{})
    delta=dict(utc=snapshot['utc'],previous_utc=old.get('utc'),added=len(set(current)-set(before)),
        changed=sum(v!=before.get(k) for k,v in current.items()),
        net_bytes=sum(x['bytes'] for x in current.values())-sum(x['bytes'] for x in before.values()),
        stage=snapshot.get('actual_execution_stage') or (snapshot['stages'].get('progress.json') or {}).get('stage'),done_count=snapshot['done_count'],
        raw_count=snapshot['raw_count'],cpu_replay_count=snapshot['cpu_replay_count'],reused_probe_count=snapshot['reused_probe_count'],
        owned_process_count=len(snapshot['processes']),all_done_bound_SHA_pass=snapshot['all_done_bound_SHA_pass'],
        source_lock_sha256=snapshot['source_lock_sha256'],frozen_files=snapshot['frozen_files'],
        completion=snapshot['stages'].get('completion.json'),resource=snapshot['resource'],non_atomic_component_reads=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for name,value in [(stamp+'.json',snapshot),('latest.json',snapshot),('latest_delta.json',delta)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(delta,ensure_ascii=False))

if __name__=='__main__':main()
