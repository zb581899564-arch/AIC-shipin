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
    runtime_handoff = snap.get('full_resume_handoff')
    handoff_proof = RUN / 'controller/V14_real_handoff_acceptance_20261008.json'
    handoff_proof_sha = hashlib.sha256(handoff_proof.read_bytes()).hexdigest() if handoff_proof.exists() else None
    student_admission_log = snap.get('cpu_stage_logs', {}).get('student_admission.cpu.log')
    student_progress = snap.get('student_progress') or {}
    student_runtime = snap.get('student_stage_receipts') or {}
    student_completion = snap.get('student_report') or {}
    selection = {key:student_completion.get(key) for key in ('selected_epoch', 'selected_candidate_original_B',
        'trained_candidate_selected', 'selected_adapter_sha256', 'selected_video_macro_f1',
        'selection_rule', 'selected_new_T_improvement_claim', 'official_score')}
    prefix_gate = snap.get('v8_stage_receipts', {}).get('prefix')
    final_path = RUN / 'controller/V14_final_acceptance_20261008.json'
    final = json.loads(final_path.read_bytes()) if final_path.exists() else None
    final_sha = hashlib.sha256(final_path.read_bytes()).hexdigest() if final else None
    if final:
        assert final['status'] == 'PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING'
        assert final['source_lock_sha256'] == snap['source_lock_sha256']
        assert stage == final['completion_status']
        assert steps == final['actual_T_optimizer_updates'] == 15
        assert selection['selected_candidate_original_B'] is final['selected_original_B']
        assert selection['selected_adapter_sha256'] == final['selected_adapter_sha256']
        assert all(all(scope['strict_checks'].values()) for scope in final['scopes'].values())
    student_stage = dict(status=student_progress.get('status'), optimizer_steps=steps,
        backward_examples_in_progress=student_progress.get('backward_examples'),
        actual_flushed_backward_examples=(student_runtime.get('backward_evidence') or {}).get('actual_flushed_examples'),
        prefix_required_updates=student_progress.get('prefix_required_updates'),
        prefix_gate=prefix_gate,
        real_assistant_CE={key:{field:item.get(field) for field in ('status','loss','optimizer_updates')}
            for key,item in student_progress.get('real_assistant_ce_acceptance', {}).items()},
        dev_metrics={name:{key:item.get(key) for key in ('windows','parse_failures','inference_failures','seconds','local_metric_role')}
            for name,item in student_runtime.get('dev_metrics', {}).items()},
        runtime_artifact_read_utc=student_runtime.get('read_utc'),
        sequential_snapshot_not_atomic=True)
    receipt = dict(status=('ACTUAL_V14_FINAL_ZIP_INDEPENDENTLY_ACCEPTED_ORIGINAL_B_SELECTED' if final else
        'ACTUAL_V14_COMPLETE_TEACHER_HANDOFF_AND_STUDENT_CONTINUATION_NOT_FINAL_ZIP'),
        utc=dt.datetime.now(dt.timezone.utc).isoformat(), snapshot_utc=snap['utc'], entry=ENTRY,
        source_lock_sha256=snap['source_lock_sha256'], frozen_files=snap['source_lock_file_count'],
        launch_utc=start['utc'], launch_historical_pid=start['pid'], actual_stage=stage,
        complete_teacher_manifest=full, all_original_SHA_pass=snap.get('all_original_resume_file_sha_pass'),
        all_complete_review_SHA_pass=snap.get('all_complete_teacher_review_file_SHA_pass'),
        independent_full_teacher_acceptance_sha256=proof_sha, original_labels=160, original_reviews=160,
        runtime_complete_teacher_handoff=runtime_handoff,
        independent_runtime_handoff_acceptance_sha256=handoff_proof_sha,
        actual_student_CPU_admission_log=student_admission_log,
        actual_student_runtime_stage=student_stage,
        supported_by_split={'train': 65, 'dev': 14}, unknown_count=81,
        original_pilot_diagnostic_flags_preserved=24, original_V13_STOP_preserved=True,
        new_teacher_calls=0, actual_new_T_optimizer_updates=steps,
        actual_student_selection=selection,
        final_ZIP_complete=bool(final), independent_final_acceptance_sha256=final_sha,
        final_candidate=final['scopes']['rematch'] if final else None,
        official_score=None, per_frame_or_raw_exported=False, large_transfer_bytes=0)
    registration = RUN / 'controller/autonomy_v14_registration_20261008.json'
    registration.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    top = f"""## 2026-10-08：V14完整教师回执与学生diagnostic阶段移交修复

当前唯一入口 `{ENTRY}/CONTINUE.md`、`PROTOCOL.md`。V13原160标签与160盲第二选择已完整自然成功：原28复查逐SHA保留、新132真实复查、工程失败0；completed/exit0/stop_reason null，真实GPU charge5493.750158078037秒已追加账本，原V11失败charge6748.806357712485秒仍保持。独立全量CPU验收SHA `{proof_sha}` 核160原validator、HTTP构造/实际processor/应用GBNF/raw、10181物理PNG/RGB和全部绑定SHA，CPU新调用0，同教师一致性只是弱证据。支持正65(train55/dev10)、空14(train10/dev4)、UNKNOWN81；支持准入实际65train/14dev，原128/32及160全分母不减。

V13学生于2026-10-08T12:11:31.394857UTC在GPU前CPU准入STOP：完整教师复用的pilot24仍有diagnostic_only=True，学生旧consumer却只接受False。原标记/raw/支持/UNKNOWN/STOP不回写。V14仅允许完整exact160 manifest批准的原pilot24精确成功回执跨阶段作为弱监督，修改/外部/非pilot diagnostic仍STOP，不把UNKNOWN转空/负、不重复任何教师成功生成。旧consumer原症状/新完整160 consumer及11拒绝合同实际CPU通过；原训练、输入、prompt、validator与生产配方保持。完整教师manifest SHA `{full.get('manifest_sha256')}` 仅Linux原地，逐帧/教师raw不导出。

V14冻结 `{snap['source_lock_file_count']}` 文件，锁 `{snap['source_lock_sha256']}`；单次launcher `{start['utc']}`、历史PID/PGID `{start['pid']}`。实际快照 `{snap['utc']}` 阶段 `{stage}`，完整路径进程{len(snap.get('processes', []))}/server{len(snap.get('owned_servers', []))}。新教师调用0、新T实际optimizer更新 `{steps}`，无新最终ZIP。CPU SHA/原validator重开/资源排队可能合法，历史PID和GPU闲不作存活/卡死证据；冻结源码不改，launcher/成功生成不重开。

本次完整教师运行时移交实际状态 `{(runtime_handoff or {}).get('status', 'PENDING')}`、UTC `{(runtime_handoff or {}).get('utc')}`；独立原9个聚合/准入文件逐字节、原24诊断标记及全部原authority与新core SHA验收SHA `{handoff_proof_sha}`，CPU新模型调用0，移交不是GPU训练或新ZIP。

学生CPU准入原日志SHA `{(student_admission_log or {}).get('sha256')}`，完整日志/规划更新与prefix读monitor_teacher_v14/latest.json的cpu_stage_logs；PASS的65train/14dev与计划15更新、prefix4不能当实际更新。新GPU作业若尚有CPU模型/原validator检查，active费用仍待真实wrapper终态追加，不虚写0成本。

学生实际运行回执 `{student_stage['status']}`；本快照完成optimizer更新 `{steps}`，原始反向证据已落盘 `{student_stage['actual_flushed_backward_examples']}` 例（逐例backward不等于已完成optimizer更新）。真实正/空assistant CE状态 `{student_stage['real_assistant_CE']}`；同production开发回执 `{student_stage['dev_metrics']}`。前缀独立CPU重载门 `{(prefix_gate or {}).get('status', 'PENDING')}`，未通过该门及完整训练/开发不能宣称训练验收完成。组件顺序读取UTC `{student_stage['runtime_artifact_read_utc']}`，与progress读取有合法时差。

实际开发选点 `{selection}`。若selected_candidate_original_B=True，生产采用原B权重；新T训练实际发生，但新权重没有在该弱开发集胜出，不能声称新T提高。该开发集为同教师盲一致性弱证据，非人工真值或官网成绩。

自动接续：完整教师CPU移交→学生准入→2–4真实更新同optimizer/RNG/288adapter重载→旧B candidate0开发→NONTEST8→426全部11独立strict ZIP。原B胜出如实保留；科学不足按已授权独立B/C实现，不等待用户、不盲换prompt。B2用户37.32/DONE（317401字节SHA0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3）；旧B37.63仍绑定86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54。新分未知。

每15分钟aic-linux静默入口controller/checkpoint_teacher_v14.py，逐次核真实完整命令/父子PGID/IO、原终态、学生/dev/strict、共享锁/账本7200与实际容量，比artifact字节/mtime。Mac退出、小量控制直SSH授权；新大流量先许可，100confirm不读、不手看复赛调参、不改外部任务/连接/服务。只有最终ZIP真实全验收后一次通知、删除监控、不归档，包留Linux。

{MARKER}

"""
    if final:
        candidate = final['scopes']['rematch']
        top = f"""## 2026-10-08：V14最终Linux ZIP已独立完整验收，生产选原B

生产控制器于2026-10-08T15:16:10.653385+00:00自然完成，completion=`{final['completion_status']}`。独立终态验收UTC `{final['utc']}`、状态 `{final['status']}`，证据controller/V14_final_acceptance_20261008.json SHA `{final_sha}`。独立核全部16502冻结文件、当前模型/训练/选点/8与426分母/产物字节/ZIP/资源账本，验收新模型调用0、优化器更新0；当前所属进程0。名称中的T表示此执行路线，不代表新微调权重被选用。

最终包留Linux：`{candidate['candidate']}`。实际 `{candidate['zip_bytes']}` 字节，SHA256 `{candidate['zip_sha256']}`。NONTEST8与426复赛各11项独立strict全true；426源/521时间窗/时间无效0、102470预测帧、ZIP CRC通过、仅一个predictions.jsonl、426身份及原字节完全相等。未自动回传或提交官网；新官网分未知。

32B教师是推理弱监督，未微调32B：完整160标签/160盲第二选择工程失败0，支持65train/14dev，UNKNOWN81及160全分母保留，同教师一致性不是人工真值。8B学生确已完成3epochs/15次真实optimizer更新/195次样本反向；有限loss/梯度、288adapter逐更新变化、冻结基座保持、4更新前缀同optimizer/RNG继续及原独立CPU288adapter重载均通过。开发含原B candidate0并与production输入一致，弱14dev的原B/epoch1同为0.3786251362162477，epoch2/3为0.3596785770535768/0.36453995670744305；按登记同分取较早epoch的规则选epoch0原B，adapter SHA `{final['selected_adapter_sha256']}`，trained_candidate_selected=false，不声称新T提升或新官方成绩。

NONTEST时间8/8与复赛时间426/521为本次真实生成。空间完整源场/31295真实原锚点仅在算法、请求、模型、源身份及全部SHA一致后原样复用，空间本候选新模型调用0，原GPU/CPU成本保持；先全源插值再按时间筛选，禁止把缓存复用当新生成。实际GPU终态训练/非测试时间/复赛时间charge分别2231.7791278334334/164.55463389214128/5430.027779461816秒，均completed/exit0/stop_reason null并与追加账本唯一记录一致，7200历史offset保留。

教师B/F证据与边界编号、生成约束、probe/all/review阶段衔接、canonical键顺序、原validator metadata部署与pilot diagnostic精确跨阶段准入已修复。V14仅在完整exact160 manifest下许可原pilot24精确成功回执；原诊断标记、raw、各旧STOP、UNKNOWN和成功记录不改，不重复成功调用。冻结锁 `{final['source_lock_sha256']}` 与12:37:29单次launcher保持。教师完整验收SHA `{proof_sha}`、运行时移交SHA `{handoff_proof_sha}`保持。网络修复仅既有用户授权本地精确范围，当前SSH已恢复，仍为DERP中继。

历史线上分数分开绑定：原B37.63为旧包SHA86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54；B2用户37.32/DONE为317401字节旧包SHA0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3。当前新包官网分未知。最终发布仅筛选核心代码、协议、聚合验收和包路径/大小/SHA，不导出ZIP、模型、逐帧数据、教师raw或弱标签。完成发布与交付后删除aic-linux，不归档聊天。

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
