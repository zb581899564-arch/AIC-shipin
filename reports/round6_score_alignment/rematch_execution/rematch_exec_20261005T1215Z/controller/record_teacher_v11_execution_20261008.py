"""Record actual receipts and refresh unbound handoffs; never mutate a frozen run."""
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
from register_b2_package_v1 import remote, REMOTE, RUN

ENTRY = 'teacher_student_autopilot_v11'
MARKER = '<!-- END_CURRENT_TEACHER_V10 -->'


def main():
    actual = json.loads(remote('''import base64,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
p=Path(%r)/%r
print(json.dumps({n:base64.b64encode((p/n).read_bytes()).decode() for n in
    ('source_lock.json','start_receipt.json','registration.json','progress.json','completion.json') if (p/n).is_file()}))
''' % (REMOTE, ENTRY), echo=False))
    for name, encoded in actual.items():
        data = base64.b64decode(encoded)
        path = RUN/ENTRY/name
        if path.exists() and name in ('source_lock.json','start_receipt.json','registration.json'):
            assert path.read_bytes() == data, 'immutable local receipt differs: '+name
        else:
            path.write_bytes(data)
    start = json.loads((RUN/ENTRY/'start_receipt.json').read_bytes())
    lock = json.loads((RUN/ENTRY/'source_lock.json').read_bytes())
    snap = json.loads((RUN/'controller/monitor_teacher_v11/latest.json').read_bytes())['snapshot']
    digest = hashlib.sha256((RUN/ENTRY/'source_lock.json').read_bytes()).hexdigest()
    assert digest == start['source_lock_sha256'] == snap['source_lock_sha256']
    stage = (snap.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU')
    finished = snap.get('completion') or {}
    if finished:
        stage = finished['status']
    steps = (snap.get('student_progress') or {}).get('optimizer_steps',0)
    visual = (snap.get('v8_stage_receipts') or {}).get('visual_completion') or {}
    probe = (snap.get('v8_stage_receipts') or {}).get('teacher_probe') or {}
    handoff = (snap.get('v8_stage_receipts') or {}).get('legacy_handoff') or {}
    real_format = (snap.get('v8_stage_receipts') or {}).get('new_format_real_probe') or {}
    pilot_progress = snap.get('pilot_progress') or {}
    evidence = json.loads((RUN/ENTRY/'evidence_boundary_cpu_acceptance.json').read_bytes())
    legacy = json.loads((RUN/ENTRY/'legacy_reuse_cpu_acceptance.json').read_bytes())
    cost = json.loads((RUN/ENTRY/'legacy_cost_cpu_acceptance.json').read_bytes())
    cpu_count = evidence['total_contract_tests'] + legacy['tests_run'] + cost['tests_run']
    receipt = dict(status='REGISTERED_AUTONOMOUS_V11_AND_15MIN_SILENT_MONITOR_NOT_QUALITY',
        utc=dt.datetime.now(dt.timezone.utc).isoformat(), entry=ENTRY, automation_id='aic-linux',
        source_lock_sha256=digest, frozen_files=len(lock['files']), cpu_checks=cpu_count,
        launch_historical_pid=start['pid'], launch_utc=start['utc'], snapshot_utc=snap['utc'],
        actual_controller_commands=snap.get('processes',[]), actual_owned_server_count=len(snap.get('owned_servers',[])),
        actual_stage=stage, completion_status=finished.get('status'),
        actual_visual_status=visual.get('status'), actual_probe_status=probe.get('status'),
        actual_legacy_handoff_status=handoff.get('status'),
        actual_new_format_status=real_format.get('status'),
        actual_new_format_fresh_model_calls=real_format.get('fresh_model_calls',0),
        actual_pilot_progress=pilot_progress,
        new_T_optimizer_updates=steps, old_STOP_preserved=True,
        raw_labels_or_per_frame_data_exported=False, large_transfers=0, automatic_return=False, uploaded=False)
    (RUN/'controller/autonomy_v11_registration_20261008.json').write_bytes(
        (json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
    format_state = (f"本次首个原失败窗口于 {real_format['utc']} 已真实新生成通过 `{real_format['status']}`；新调用1、旧成功重调用0，原raw/源帧/原validator独立CPU回放通过，尚不构成语义或训练准入。" if real_format else "首个原失败窗口的新格式真实生成仍以当前实际回执为准，CPU/复用不当新生成。")
    top = f'''## 2026-10-08：V11证据编号与阶段衔接修复，已登记自主接续

当前唯一入口 `{ENTRY}/CONTINUE.md` 与 `PROTOCOL.md`。Linux `{cpu_count}` 项CPU与固定runtime/原validator/真实旧成功SHA验收后冻结 `{len(lock['files'])}` 文件，SHA `{digest}`，一次launcher {start['utc']} 历史PID/PGID `{start['pid']}`。{snap['utc']}实时所属完整命令进程 `{len(snap.get('processes',[]))}`、server `{len(snap.get('owned_servers',[]))}`，实际阶段 `{stage}`。原PID/旧progress/CPU/启动不当存活、标签质量、训练或新ZIP。

V10真实视觉8/8和2条非测试重输入通过，但首个pilot的[15,21)、[42,50)缺少模型所选实际证据帧而STOP；原raw SHA9977638522f91aa2661fd70b5179a7aed557ea816d5f451f6f50b010114f65fa、639锁、所有失败与成功保持。V11仅注册B边界/F物理帧独立编号和每段模型自行所选见证生成约束，所有合法1..5段/证据子集保持，原高光定义与原validator/16024输入字节不改，无后补证据/裁段/造空/UNKNOWN负类。

旧2成功只在完整160内（不在pilot24）通过孤立原validator/全SHA原字节引用，新旧接口由exact manifest分开核；视觉8只在8实际HTTP构造CPU相等及模型/运行时/输入身份相同后引用，不重复成功生成、旧cost保留、引用新调用0。{format_state} 后台继续剩余23窗与盲第二选择。来源/PTS/模型确错工程STOP；语义争议逐条UNKNOWN并保留全分母；不要求小试必须出现空例，不把同教师一致性叫真值。

继续可靠完整窗口监督→完整160/复查→原B LoRA lr1e-5最多3epochs/前缀2–4真实更新保持optimizer/RNG→开发candidate0旧B→NONTEST8→426独立strict ZIP。监督只可靠边界时自主登记B边界精修；教师不可靠自主实现C同8B全源粗览/局部非测试匹配对照。路线B/C当前以协议为准，不假称运行。新T实际更新 `{steps}`，原教师科学STOP保持。

B2用户指认37.32/DONE，317401字节SHA0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3；旧B37.63绑定旧包，两分差-0.31。每15分钟aic-linux静默巡检/自助修复，controller/checkpoint_teacher_v11.py记录CPU/GPU/RAM/disk/真实命令父子PGID、resource/queue与逐窗/semantic/student/strict。CPU SHA、顺序解码与共享等待可能合法；冻结源码不改/launcher不重复/外部任务不抢占。新大流量先许可，控制小量直SSH，Mac退出、100confirm不读、复赛不手看调参；最终ZIP留Linux、不自动官网提交，完整验收后汇报并删除监控，不归档。下面入口/PID为历史。

{MARKER}

'''

    local_targets = [RUN.parents[3]/'AGENTS.md', RUN/'STATUS_AUTOPILOT_20261007.md',
        RUN/'controller/AUTONOMOUS_EXECUTION_20261008.md', RUN/'controller/V8_REPAIR_AND_EXECUTION_20261008.md']
    payload = {}
    for path in local_targets:
        old = path.read_bytes().decode('utf-8')
        assert MARKER in old
        tail = old.split(MARKER,1)[1].lstrip('\r\n')
        path.write_bytes(top.encode()+tail.encode())
        if path.name != 'AGENTS.md':
            payload[path.relative_to(RUN).as_posix()] = base64.b64encode(path.read_bytes()).decode()
    for name in ('autonomy_v11_registration_20261008.json','P0_user_minimal_reproduction_20261008.json','V9_visual_and_overlap_acceptance_20261008.json'):
        path = RUN/'controller'/name
        payload[path.relative_to(RUN).as_posix()] = base64.b64encode(path.read_bytes()).decode()
    remote('''import json,base64,hashlib
from pathlib import Path
r=Path(%r);payload=json.loads(base64.b64decode(%r));bound=set()
for lock in r.glob('*/source_lock.json'):
    value=json.loads(lock.read_bytes())
    entries=value.get('files',value.get('production_files'))
    if isinstance(entries,dict):names=list(entries)
    elif isinstance(entries,list) and all(isinstance(row,dict) and isinstance(row.get('path'),str) for row in entries):
        names=[row['path'] for row in entries]
    else:raise RuntimeError('unknown source-lock schema: '+str(lock))
    bound.update(str((lock.parent/name).resolve()) for name in names)
for name,encoded in payload.items():
    p=r/name;assert p.resolve().is_relative_to(r.resolve()) and str(p) not in bound
    b=base64.b64decode(encoded)
    if p.exists() and p.read_bytes()!=b:
        old=p.read_bytes();h=r/'controller/handoff_history_v11';h.mkdir(exist_ok=True)
        archive=h/(p.name+'.'+hashlib.sha256(old).hexdigest())
        if not archive.exists():archive.write_bytes(old)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print(json.dumps({'status':'PASS_UNBOUND_V11_HANDOFF_ONLY','files':len(payload)}))
''' % (REMOTE,base64.b64encode(json.dumps(payload).encode()).decode()))
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__': main()
