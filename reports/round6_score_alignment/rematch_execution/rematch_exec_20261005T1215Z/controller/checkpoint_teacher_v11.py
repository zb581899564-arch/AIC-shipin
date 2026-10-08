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
for lock in root.glob('*/source_lock.json'):
    value=json.loads(lock.read_text())
    entries=value.get('files',value.get('production_files'))
    if isinstance(entries,dict):names=list(entries)
    elif isinstance(entries,list) and all(isinstance(row,dict) and isinstance(row.get('path'),str) for row in entries):
        names=[row['path'] for row in entries]
    else:raise RuntimeError('unknown source-lock schema: '+str(lock))
    bound={str((lock.parent/name).resolve()) for name in names}
    assert str(path) not in bound,'inspector is frozen'
if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
spec=importlib.util.spec_from_file_location('live_v8_inspector',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
target,snapshot=module.capture('v11','teacher_student_autopilot_v11')
print(json.dumps({'snapshot_path':str(target),'snapshot':snapshot},ensure_ascii=False))
'''%(REMOTE,base64.b64encode(data).decode(),digest),echo=False)
    value=json.loads(raw)
    output=RUN/'controller/monitor_teacher_v11';output.mkdir(exist_ok=True)
    path=output/Path(value['snapshot_path']).name
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'latest.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    snap=value['snapshot']
    stages=snap.get('v8_stage_receipts',{})
    visual=stages.get('visual_completion') or {}
    print(json.dumps({'snapshot':str(path),'owned_process_count':len(snap.get('processes',[])),
        'owned_server_count':len(snap.get('owned_servers',[])), 'gpu':snap.get('gpu'),
        'completion':snap.get('completion'),'progress':snap.get('progress'),
        'visual_status':visual.get('status'),'visual_case_count':len(visual.get('cases',[])),
        'teacher_probe':stages.get('teacher_probe'),'teacher_progress':snap.get('teacher_progress'),
        'pilot_progress':snap.get('pilot_progress'),'student_progress':snap.get('student_progress')},ensure_ascii=False))


if __name__=='__main__': main()
