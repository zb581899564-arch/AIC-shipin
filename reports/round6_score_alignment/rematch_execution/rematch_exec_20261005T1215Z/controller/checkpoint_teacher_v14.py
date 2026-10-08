"""Small read-only Linux inspector deployment and bounded local monitoring snapshot."""
import base64
import hashlib
import json
from pathlib import Path
from register_b2_package_v1 import remote,REMOTE,RUN,PY


def delta_summary(previous, value):
    before=(previous or {}).get('snapshot',{})
    current=value['snapshot']
    flatten=lambda snap:{scope+'/'+name:state for scope,files in snap.get('artifact_activity',{}).items()
        for name,state in files.items()}
    old,new=flatten(before),flatten(current)
    changed=[name for name in sorted(new) if old.get(name)!=new[name]]
    io={pid:{key:state.get('counters',{}).get(key,0)-before.get('process_io',{}).get(pid,{}).get('counters',{}).get(key,0)
        for key in ('rchar','wchar','read_bytes','write_bytes')}
        for pid,state in current.get('process_io',{}).items() if pid in before.get('process_io',{})}
    stages=current.get('v8_stage_receipts',{})
    return dict(status='READ_ONLY_ACTUAL_PROGRESS_DELTA_NOT_QUALITY_OR_TRAINING',
        previous_utc=before.get('utc'),utc=current['utc'],source_lock_sha256=current['source_lock_sha256'],
        progress=current.get('progress'),completion=current.get('completion'),
        owned_processes=len(current.get('processes',[])),owned_servers=len(current.get('owned_servers',[])),
        review_progress=stages.get('review_progress'),
        fresh_completed_reviews=current.get('fresh_review_done_count',0),
        fresh_review_failures=current.get('fresh_review_failure_count',0),
        all_original_receipt_SHA_pass=current.get('all_original_resume_file_sha_pass'),
        all_fresh_completed_review_SHA_pass=current.get('all_fresh_completed_review_SHA_pass'),
        complete_teacher_manifest=current.get('complete_teacher_manifest_summary'),
        all_complete_teacher_review_SHA_pass=current.get('all_complete_teacher_review_file_SHA_pass'),
        complete_teacher_handoff=current.get('full_resume_handoff'),
        original_V13_terminal=current.get('original_V13_terminal'),
        changed_artifact_count=len(changed),added_artifact_count=len(set(new)-set(old)),
        net_artifact_byte_delta=sum(v['bytes'] for v in new.values())-sum(v['bytes'] for v in old.values()),
        first_changed_artifacts=[dict(path=name,before=old.get(name),after=new[name]) for name in changed[:12]],
        process_IO_counter_delta=io,gpu=current.get('gpu'),disk=current.get('disk'),
        shared_active_gpu_job=current.get('active_gpu_job'),GPU_ledger=current.get('gpu_ledger_summary'),
        new_T_optimizer_updates=(current.get('student_progress') or {}).get('optimizer_steps',0),
        final_ZIP_complete=False)


def main():
    output=RUN/'controller/monitor_teacher_v14';output.mkdir(exist_ok=True)
    previous=json.loads((output/'latest.json').read_bytes()) if (output/'latest.json').exists() else None
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
target,snapshot=module.capture('v14','teacher_student_autopilot_v14')
print(json.dumps({'snapshot_path':str(target),'snapshot':snapshot},ensure_ascii=False))
'''%(REMOTE,base64.b64encode(data).decode(),digest),echo=False)
    value=json.loads(raw)
    path=output/Path(value['snapshot_path']).name
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'latest.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary=delta_summary(previous,value)
    (output/(path.stem+'.delta.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'latest_delta.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    snap=value['snapshot']
    stages=snap.get('v8_stage_receipts',{})
    visual=stages.get('visual_completion') or {}
    print(json.dumps({'snapshot':str(path),'owned_process_count':len(snap.get('processes',[])),
        'owned_server_count':len(snap.get('owned_servers',[])), 'gpu':snap.get('gpu'),
        'completion':snap.get('completion'),'progress':snap.get('progress'),
        'visual_status':visual.get('status'),'visual_case_count':len(visual.get('cases',[])),
        'teacher_probe':stages.get('teacher_probe'),'teacher_progress':snap.get('teacher_progress'),
        'pilot_progress':snap.get('pilot_progress'),'review_progress':stages.get('review_progress'),'first_review_generation':stages.get('first_review_generation'),'student_progress':snap.get('student_progress')},ensure_ascii=False))


if __name__=='__main__': main()
