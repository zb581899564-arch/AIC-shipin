"""Small unbound inspector deployment and actual non-atomic snapshot/delta."""
import base64
import datetime as dt
import hashlib
import json
from register_b2_package_v1 import remote,REMOTE,RUN


def main():
    script=(RUN/'controller/inspect_b_prompt_recovery_v1.py').read_bytes()
    digest=hashlib.sha256(script).hexdigest()
    raw=remote('''import base64,hashlib,importlib.util,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r);p=root/'controller/inspect_b_prompt_recovery_v1.py'
for lp in root.glob('*/source_lock.json'):
 lock=json.loads(lp.read_text());rows=lock.get('files',lock.get('production_files',{}))
 names=list(rows) if isinstance(rows,dict) else [x['path'] for x in rows]
 assert str(p) not in {str((lp.parent/x).resolve()) for x in names}, 'inspector frozen'
data=base64.b64decode(%r);assert hashlib.sha256(data).hexdigest()==%r
if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
spec=importlib.util.spec_from_file_location('live_boundary',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
print(json.dumps(mod.capture(),ensure_ascii=False))
'''%(REMOTE,base64.b64encode(script).decode(),digest),echo=False)
    snapshot=json.loads(raw);out=RUN/'controller/monitor_b_prompt_recovery_v1';out.mkdir(exist_ok=True)
    old=json.loads((out/'latest.json').read_text()) if (out/'latest.json').exists() else {}
    current=snapshot['artifacts'];before=old.get('artifacts',{})
    delta={'utc':snapshot['utc'],'previous_utc':old.get('utc'),'added':len(set(current)-set(before)),
        'changed':sum(v!=before.get(k) for k,v in current.items()),
        'net_bytes':sum(x['bytes'] for x in current.values())-sum(x['bytes'] for x in before.values()),
        'done_count':snapshot['done_count'],'previous_done_count':old.get('done_count'),
        'owned_process_count':len(snapshot['processes']),'current_stage':(snapshot['stages'].get('progress.json') or {}).get('stage'),
        'failure_count':len(snapshot['failures']),'all_done_bound_SHA_pass':snapshot['all_done_bound_SHA_pass'],
        'source_lock_sha256':snapshot['source_lock_sha256'],'completion':snapshot['stages'].get('completion.json'),
        'non_atomic_component_reads':True}
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for name,value in ((stamp+'.json',snapshot),('latest.json',snapshot),('latest_delta.json',delta)):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(delta,ensure_ascii=False))


if __name__=='__main__':main()
