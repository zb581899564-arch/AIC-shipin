"""Record actual receipts and refresh unbound handoffs; never mutate a frozen run."""
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
from register_b2_package_v1 import remote, REMOTE, RUN

ENTRY = 'teacher_student_autopilot_v10'
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
    snap = json.loads((RUN/'controller/monitor_teacher_v10/latest.json').read_bytes())['snapshot']
    digest = hashlib.sha256((RUN/ENTRY/'source_lock.json').read_bytes()).hexdigest()
    assert digest == start['source_lock_sha256'] == snap['source_lock_sha256']
    stage = (snap.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU')
    finished = snap.get('completion') or {}
    if finished:
        stage = finished['status']
    steps = (snap.get('student_progress') or {}).get('optimizer_steps',0)
    visual = (snap.get('v8_stage_receipts') or {}).get('visual_completion') or {}
    probe = (snap.get('v8_stage_receipts') or {}).get('teacher_probe') or {}
    receipt = dict(status='REGISTERED_AUTONOMOUS_V10_AND_15MIN_SILENT_MONITOR_NOT_QUALITY',
        utc=dt.datetime.now(dt.timezone.utc).isoformat(), entry=ENTRY, automation_id='aic-linux',
        source_lock_sha256=digest, frozen_files=len(lock['files']), cpu_checks=72,
        launch_historical_pid=start['pid'], launch_utc=start['utc'], snapshot_utc=snap['utc'],
        actual_controller_commands=snap.get('processes',[]), actual_owned_server_count=len(snap.get('owned_servers',[])),
        actual_stage=stage, completion_status=finished.get('status'),
        actual_visual_status=visual.get('status'), actual_probe_status=probe.get('status'),
        new_T_optimizer_updates=steps, old_STOP_preserved=True,
        raw_labels_or_per_frame_data_exported=False, large_transfers=0, automatic_return=False, uploaded=False)
    (RUN/'controller/autonomy_v10_registration_20261008.json').write_bytes(
        (json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
    top = f'''## 2026-10-08：V10工程修复已冻结并单次接续；以真实阶段为准

当前唯一入口 `{ENTRY}/CONTINUE.md` 与 `PROTOCOL.md`。Linux72项CPU合同通过，639文件锁SHA `{digest}`；冻结后preflight通过，一次launcher于{start['utc']}登记历史PID/PGID {start['pid']}。{snap['utc']}实时完整命令核对：所属进程{len(snap.get('processes',[]))}、教师server {len(snap.get('owned_servers',[]))}；实际阶段 `{stage}`，视觉回执 `{visual.get('status')}`、真实探针 `{probe.get('status')}`。历史PID、旧progress、CPU或启动均不是持续存活、标签质量、训练或新ZIP验收。

用户提供最小复现4项通过；生产函数probe→pilot→all→review的CPU串联（mock推理）与实际缓存身份验收已通过，不当作真实32B生成。probe必须新生成，all仅原validator/完整输入模型prompt/SHA核过后原样复用，review不重复标注。短KEEP/NO_HIGHLIGHT/UNKNOWN、原生边界ID与程序精确PTS、同局部输入、盲第二选择/逐条UNKNOWN/全分母、新来源隔离128/32与固定24、早期2–4真实更新且同optimizer/RNG、原B开发candidate0均已登记。

v9真实视觉8/8通过后首条非测试探针返回重叠区间，原validator正确拒绝；原HTTP/raw/STOP与556冻结文件不改、不重开。V10保留原prompt/schema/高光标准/validator及160/24输入原字节，仅增加有限状态GBNF关系约束，全部合法1–5段保留；4356边界对、143小域合法序列和独立20实例均由固定C++运行时核验。旧无效回答不裁段/排序/合并/转空。原登记24中一条工程探针已见，不冒充全新未见批次。

真实接续8合成接口→2非测试重输入探针→24标注/盲复查→可靠完整窗口监督时全160与B LoRA lr1e-5最多3epochs→原B/新检查点开发→NONTEST8→426独立strict ZIP。完整监督不足，按证据登记B边界精修可行性或C同8B全源粗览→局部匹配对照；监控Agent自主继续，不无限换提示或等用户。新T实际更新{steps}；旧科学STOP保持，同教师一致性不是真值。

已交付B2用户截图37.32/DONE，旧B37.63仍绑定旧包，B2低0.31且不是T。每15分钟aic-linux静默巡检与自助修复，当前检查脚本controller/checkpoint_teacher_v10.py。运行冻结源码不改/launcher不重复，CPU核SHA、顺序解码与共享队列可能合法；按实时容量保护外部任务与GPU追加账本。只小量控制直SSH、Mac不参与、100confirm不读，不手看复赛调参。新大流量仍事先许可，最终ZIP留Linux，不自动官网提交；实际完整验收后才交付并删除监控，不归档。下方其他入口/PID为历史。

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
    for name in ('autonomy_v10_registration_20261008.json','V10_ordered_boundary_independent_review_20261008.json',
                 'P0_user_minimal_reproduction_20261008.json','V9_visual_and_overlap_acceptance_20261008.json'):
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
        old=p.read_bytes();h=r/'controller/handoff_history_v10';h.mkdir(exist_ok=True)
        archive=h/(p.name+'.'+hashlib.sha256(old).hexdigest())
        if not archive.exists():archive.write_bytes(old)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print(json.dumps({'status':'PASS_UNBOUND_V10_HANDOFF_ONLY','files':len(payload)}))
''' % (REMOTE,base64.b64encode(json.dumps(payload).encode()).decode()))
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__': main()
