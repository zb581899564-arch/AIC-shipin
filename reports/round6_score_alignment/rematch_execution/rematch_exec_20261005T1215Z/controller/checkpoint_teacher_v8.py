"""Small read-only Linux inspector deployment and bounded local monitoring snapshot."""
import base64
import hashlib
import json
from pathlib import Path
from register_b2_package_v1 import remote,REMOTE,RUN,PY


def main():
    path=RUN/'controller/inspect_autopilot_live.py'
    data=path.read_bytes(); digest=hashlib.sha256(data).hexdigest()
    raw=remote('''import base64,hashlib,importlib.util,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r);path=root/'controller/inspect_autopilot_live.py'
data=base64.b64decode(%r);assert hashlib.sha256(data).hexdigest()==%r
for entry in ('teacher_student_autopilot_v7','b_score_aligned_package_v4','teacher_student_autopilot_v8'):
    lock=root/entry/'source_lock.json'
    if lock.is_file():assert str(path) not in json.loads(lock.read_text())['files'],'inspector is frozen'
if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
spec=importlib.util.spec_from_file_location('live_v8_inspector',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
target,snapshot=module.capture('v8','teacher_student_autopilot_v8')
print(json.dumps({'snapshot_path':str(target),'snapshot':snapshot},ensure_ascii=False))
'''%(REMOTE,base64.b64encode(data).decode(),digest),echo=False)
    value=json.loads(raw)
    output=RUN/'controller/monitor_teacher_v8';output.mkdir(exist_ok=True)
    path=output/Path(value['snapshot_path']).name
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'latest.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    snap=value['snapshot']
    print(json.dumps({'snapshot':str(path),'owned_processes':snap.get('processes'),
        'completion':snap.get('completion'),'progress':snap.get('progress'),'v8_stages':snap.get('v8_stage_receipts')},ensure_ascii=False))


if __name__=='__main__': main()
