"""Update only unbound handoffs from actual V14 receipts and live snapshot."""
import base64
import datetime as dt
import hashlib
import json
from register_b2_package_v1 import remote, REMOTE, RUN

ENTRY = 'teacher_student_autopilot_v14'
MARKER = '<!-- END_CURRENT_TEACHER_V14 -->'


def main():
    snap = json.loads((RUN / 'controller/monitor_teacher_v14/latest.json').read_bytes())['snapshot']
    raw = json.loads(remote("""from pathlib import Path
import base64,json
h=Path(%r)/%r
names=('start_receipt.json','registration.json','cpu_acceptance.json','full_resume_cpu_acceptance.json','full_resume_handoff.json')
print(json.dumps({n:base64.b64encode((h/n).read_bytes()).decode() for n in names if (h/n).exists()}))
""" % (REMOTE, ENTRY), echo=False))
    for name, encoded in raw.items():
        p = RUN / ENTRY / name
        data = base64.b64decode(encoded)
        if p.exists():
            assert p.read_bytes() == data
        else:
            p.write_bytes(data)
    start = json.loads((RUN / ENTRY / 'start_receipt.json').read_bytes())
    assert start['source_lock_sha256'] == snap['source_lock_sha256']
    stage = (snap.get('completion') or {}).get('status') or (snap.get('progress') or {}).get('stage')
    if stage is None and snap.get('processes') and not snap.get('registration'):
        stage = 'SOURCE_PREFLIGHT_CPU_PENDING_REGISTRATION'
    steps = (snap.get('student_progress') or {}).get('optimizer_steps', 0)
    full = snap.get('complete_teacher_manifest_summary') or {}
    proof = RUN / 'controller/V13_real_full_review_acceptance_20261008.json'
    proof_sha = hashlib.sha256(proof.read_bytes()).hexdigest()
    receipt = dict(status='ACTUAL_V14_COMPLETE_TEACHER_HANDOFF_AND_STUDENT_CONTINUATION_NOT_FINAL_ZIP',
        utc=dt.datetime.now(dt.timezone.utc).isoformat(), snapshot_utc=snap['utc'], entry=ENTRY,
        source_lock_sha256=snap['source_lock_sha256'], frozen_files=snap['source_lock_file_count'],
        launch_utc=start['utc'], launch_historical_pid=start['pid'], actual_stage=stage,
        complete_teacher_manifest=full, all_original_SHA_pass=snap.get('all_original_resume_file_sha_pass'),
        all_complete_review_SHA_pass=snap.get('all_complete_teacher_review_file_SHA_pass'),
        independent_full_teacher_acceptance_sha256=proof_sha, original_labels=160, original_reviews=160,
        supported_by_split={'train': 65, 'dev': 14}, unknown_count=81,
        original_pilot_diagnostic_flags_preserved=24, original_V13_STOP_preserved=True,
        new_teacher_calls=0, actual_new_T_optimizer_updates=steps,
        final_ZIP_complete=False, per_frame_or_raw_exported=False, large_transfer_bytes=0)
    registration = RUN / 'controller/autonomy_v14_registration_20261008.json'
    registration.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    top = f"""## 2026-10-08：V14完整教师回执与学生diagnostic阶段移交修复

当前唯一入口 `{ENTRY}/CONTINUE.md`、`PROTOCOL.md`。V13原160标签与160盲第二选择已完整自然成功：原28复查逐SHA保留、新132真实复查、工程失败0；completed/exit0/stop_reason null，真实GPU charge5493.750158078037秒已追加账本，原V11失败charge6748.806357712485秒仍保持。独立全量CPU验收SHA `{proof_sha}` 核160原validator、HTTP构造/实际processor/应用GBNF/raw、10181物理PNG/RGB和全部绑定SHA，CPU新调用0，同教师一致性只是弱证据。支持正65(train55/dev10)、空14(train10/dev4)、UNKNOWN81；支持准入实际65train/14dev，原128/32及160全分母不减。

V13学生于2026-10-08T12:11:31.394857UTC在GPU前CPU准入STOP：完整教师复用的pilot24仍有diagnostic_only=True，学生旧consumer却只接受False。原标记/raw/支持/UNKNOWN/STOP不回写。V14仅允许完整exact160 manifest批准的原pilot24精确成功回执跨阶段作为弱监督，修改/外部/非pilot diagnostic仍STOP，不把UNKNOWN转空/负、不重复任何教师成功生成。旧consumer原症状/新完整160 consumer及11拒绝合同实际CPU通过；原训练、输入、prompt、validator与生产配方保持。完整教师manifest SHA `{full.get('manifest_sha256')}` 仅Linux原地，逐帧/教师raw不导出。

V14冻结 `{snap['source_lock_file_count']}` 文件，锁 `{snap['source_lock_sha256']}`；单次launcher `{start['utc']}`、历史PID/PGID `{start['pid']}`。实际快照 `{snap['utc']}` 阶段 `{stage}`，完整路径进程{len(snap.get('processes', []))}/server{len(snap.get('owned_servers', []))}。新教师调用0、新T实际optimizer更新 `{steps}`，无新最终ZIP。CPU SHA/原validator重开/资源排队可能合法，历史PID和GPU闲不作存活/卡死证据；冻结源码不改，launcher/成功生成不重开。

自动接续：完整教师CPU移交→学生准入→2–4真实更新同optimizer/RNG/288adapter重载→旧B candidate0开发→NONTEST8→426全部11独立strict ZIP。原B胜出如实保留；科学不足按已授权独立B/C实现，不等待用户、不盲换prompt。B2用户37.32/DONE（317401字节SHA0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3）；旧B37.63仍绑定86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54。新分未知。

每15分钟aic-linux静默入口controller/checkpoint_teacher_v14.py，逐次核真实完整命令/父子PGID/IO、原终态、学生/dev/strict、共享锁/账本7200与实际容量，比artifact字节/mtime。Mac退出、小量控制直SSH授权；新大流量先许可，100confirm不读、不手看复赛调参、不改外部任务/连接/服务。只有最终ZIP真实全验收后一次通知、删除监控、不归档，包留Linux。

{MARKER}

"""
    targets = [RUN.parents[3] / 'AGENTS.md', RUN / 'STATUS_AUTOPILOT_20261007.md',
               RUN / 'controller/AUTONOMOUS_EXECUTION_20261008.md', RUN / 'controller/V8_REPAIR_AND_EXECUTION_20261008.md']
    payload = {}
    for p in targets:
        text = p.read_text(encoding='utf-8')
        if MARKER in text:
            head, tail = text.split(MARKER, 1)
            prefix = head.split('## 2026-10-08：V14', 1)[0] if p.name == 'AGENTS.md' else ''
            text = prefix + top + tail.lstrip('\n')
        else:
            anchor = '## 2026-10-08：V13'
            index = text.index(anchor)
            prefix = text[:index] if p.name == 'AGENTS.md' else ''
            text = prefix + top + text[index:]
        p.write_text(text, encoding='utf-8', newline='\n')
        if p.name != 'AGENTS.md':
            payload[p.relative_to(RUN).as_posix()] = base64.b64encode(p.read_bytes()).decode()
    payload[registration.relative_to(RUN).as_posix()] = base64.b64encode(registration.read_bytes()).decode()
    remote("""import base64,json,hashlib
from pathlib import Path
r=Path(%r);items=json.loads(base64.b64decode(%r));bound=set()
for lock in r.glob('*/source_lock.json'):
 v=json.loads(lock.read_bytes());entries=v.get('files',v.get('production_files'))
 if isinstance(entries,dict):names=list(entries)
 elif isinstance(entries,list) and all(isinstance(x,dict) and isinstance(x.get('path'),str) for x in entries):names=[x['path'] for x in entries]
 else:raise RuntimeError('unknown source lock schema')
 bound.update(str((lock.parent/n).resolve()) for n in names)
for name,encoded in items.items():
 p=r/name;assert p.resolve().is_relative_to(r.resolve()) and str(p) not in bound
 new=base64.b64decode(encoded)
 if p.exists() and p.read_bytes()!=new:
  old=p.read_bytes();a=r/'controller/handoff_history_v14';a.mkdir(exist_ok=True);q=a/(p.name+'.'+hashlib.sha256(old).hexdigest())
  if not q.exists():q.write_bytes(old)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
print(json.dumps({'status':'PASS_UNBOUND_V14_HANDOFF_ONLY','files':len(items)}))
""" % (REMOTE, base64.b64encode(json.dumps(payload).encode()).decode()))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
