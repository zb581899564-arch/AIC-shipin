"""Save a live B2 checkpoint and the current autonomous handoff, outside frozen code."""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from register_b2_package_v1 import remote, RUN, REMOTE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--entry',default='b_score_aligned_package_v1')
    entry=parser.parse_args().entry
    assert re.fullmatch(r'b_score_aligned_package_v[1-9][0-9]*',entry)
    inspector=(RUN/'controller/inspect_autopilot_live.py').read_bytes()
    result=remote("""import base64,hashlib,json,sys
from pathlib import Path
root=Path(%r);entry=%r;path=root/'controller/inspect_autopilot_live.py'
for lock in (root/entry/'source_lock.json',root/'teacher_context_diagnostic_v3/source_lock.json',root/'teacher_student_autopilot_v7/source_lock.json'):
    if lock.is_file():assert str(path) not in json.loads(lock.read_text())['files'],'inspector is frozen'
data=base64.b64decode(%r);assert hashlib.sha256(data).hexdigest()==%r
path.write_bytes(data);sys.path.insert(0,str(path.parent))
import inspect_autopilot_live as monitor
snapshot_path,snapshot=monitor.capture(entry.rsplit('_',1)[1],entry)
files={}
for name in ('source_lock.json','cpu_acceptance.json','processor_acceptance.json','cache_bindings.json',
             'launch.json','registration.json','progress.json','completion.json'):
    p=root/entry/name
    if p.is_file():files[name]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps({'snapshot':snapshot,'remote_snapshot_path':str(snapshot_path),'files':files}))
"""%(REMOTE,entry,base64.b64encode(inspector).decode(),hashlib.sha256(inspector).hexdigest()),echo=False)
    data=json.loads(result);snapshot=data['snapshot'];directory=RUN/'controller/monitor_aic_linux';directory.mkdir(exist_ok=True)
    raw=(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode()
    (directory/'latest.json').write_bytes(raw);(directory/Path(data['remote_snapshot_path']).name).write_bytes(raw)
    for name,content in data['files'].items():(RUN/entry/name).write_bytes(base64.b64decode(content))
    lock=json.loads((RUN/entry/'source_lock.json').read_text()) if (RUN/entry/'source_lock.json').is_file() else {'files':{}}
    cpu=snapshot.get('b2_cpu_acceptance') or {};processor=snapshot.get('b2_processor_acceptance') or {}
    stage=(snapshot.get('progress') or {}).get('stage','CPU_ACCEPTANCE_AND_SOURCE_SHA')
    completion=(snapshot.get('completion') or {}).get('stage','尚未写出')
    launch=snapshot.get('launch_receipt') or {}
    now=dt.datetime.fromisoformat(snapshot['utc']).astimezone(dt.timezone(dt.timedelta(hours=8)))
    intro=(f'## 2026-10-08 {now:%H:%M} UTC+8：自主B2接续与15分钟静默巡检\n\n'
        '用户完全放权科学/工程裁决、立即修复并接续到一个最终ZIP；中途不参与/不发阶段通知。新大流量仍须许可，Mac不参与，最终包留Linux、不自动回传或AIC提交。\n\n'
        '32B context v3已01:02:48完整8/8请求、0工程失败，3正均弱复查支持、唯一NO被拒绝，真实受支持空例0；原raw/审核/科学STOP均保留，T更新0。审核声称背景只到119.0189秒，但实际overview末PTS149.98316666666668、13帧>=120；该事实性错误与其他语义争议同时保留，不能翻转拒绝。\n\n'
        '自主选择B2：保留已评分37.63的B最终8B LoRA，以修复的原生PTS/合法坐标/全源空间场完成新候选。不是新的教师微调，不延长旧LoRA。旧37.63仍绑定旧B ZIP，新B2官方分未知；旧Z时间无B LoRA，不能复用B2。源CPU/同基座空间只在身份/算法/所有SHA及完整回执一致后原样复用。\n\n'
        f'当前入口{entry}/CONTINUE.md，{len(lock["files"])}文件锁SHA{snapshot.get("source_lock_sha256")}。'
        f'{cpu.get("tests",0)}项CPU合同、434来源/{cpu.get("actual_natural_windows",0)}真实元数据窗、原{cpu.get("original_target_values_replayed",0)}目标无损回放；'
        f'实际processor/HD默认张量相等/{processor.get("actual_source_videos",0)}非测试源重开pixel SHA验收状态{processor.get("status","待完成")}。'
        f'一次launcher历史PID{launch.get("pid","尚未启动")}，{now:%H:%M}实核完整路径进程{len(snapshot["processes"])}，阶段{stage}，completion={completion}。'
        'CUDA长输入/完整NONTEST8/426封包分别以真实回执为准，CPU或启动不当最终验收。\n\n'
        '后台控制器完整接续真实B LoRA长输入CUDA→NONTEST8→426/521时间/全源空间→独立strict ZIP；真实容量、共享GPU锁/追加账本/7200保持。无100confirm/本地复刻官网分/手看复赛调参。异常立即独立版本修复，运行冻结源码不改/launcher不重复，CPU SHA、顺序解码和共享队列可能合法。\n\n'
        '只有PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX加NONTEST8/426独立strict全部true、实际ZIP大小/SHA/CRC/唯一JSONL/426身份通过，才最后报告一次并删除aic-linux。不伪写T完成。详细决策controller/NEXT_ACTION_B2_20261008.md，快照controller/monitor_aic_linux/latest.json。Windows开机且Codex运行才能唤醒巡检，Linux后台独立计算；旧预测/下方历史快照均按历史理解。\n\n')
    if entry == 'b_score_aligned_package_v2':
        provider=snapshot.get('b2_generation_provider') or {}
        count=(provider.get('temporal_progress') or {}).get('windows',0)
        failure_count=(provider.get('temporal_progress') or {}).get('failures',0)
        intro+=('v2统一生成与物理选帧的canonical duration：529真实窗56处差异/29原合法全端点误拒绝已复现修复；'
            '529全端点物理帧范围与529 nextafter越界仍拒绝、原529输入完全相等。没有epsilon/裁值/改输出。'
            '原v1真实B LoRA CUDA与完整NONTEST8已PASS，probe/8条时间经逐SHA/原validator/模型输入身份原样复用，不能称v2重新CUDA生成。'
            f'原v1 GPU时间provider此快照{count}/521、失败{failure_count}；不打断有效GPU生成。'
            'v2重新NONTEST8/strict后，合法等待原426时间PASS及wrapper完整记账，temporal_reuse.py按实时命令/父子PGID受控CPU移交，再全源CPU/空间/426 ZIP；'
            '运行冻结564文件不改。详细controller/B2_DURATION_REPAIR_20261008.md，provider与reuse/handoff同时见实时快照。\n\n')
    if entry in ('b_score_aligned_package_v3','b_score_aligned_package_v4'):
        provider=snapshot.get('b2_generation_provider') or {}
        count=(provider.get('temporal_progress') or {}).get('windows',0)
        failures=(provider.get('temporal_progress') or {}).get('failures',0)
        version=entry.rsplit('_',1)[1]
        intro+=(f'{version}保留v2统一canonical duration：529窗56差异/29误拒绝已复现，529端点/529越界仍拒绝、529计划原生序号/PTS/参数相同；'
            '没有epsilon/裁值。额外修复一条送模型前errno95：97源log316在PyAV17/libswscale9无法转RGB，模型回答0。'
            '仅绑定该SHA/profile登记临时UNSPECIFIED transfer/限定范围ITU601样本映射，恢复frame元数据；源YUV/range/尺寸/PTS不变，不声称摄影gamma真值，其他源默认转换保持。'
            '9转换CPU/实际64RGB与空间BGR一致、真实processor/8非测试pixel SHA，11独立所有权mock/6真实失败分类均PASS。'
            'v2仅停止等待controller，独立owned_stop回执；不打断v1有效GPU生成。'
            f'此快照原provider时间{count}/521、失败{failures}；{version}完整NONTEST8/strict后等待provider终态/追加账本，'
            '严格核所有成功原validator/输入/SHA，仅登记97送模型前失败在新目录实际生成一次，原成功行字节和旧失败STOP不改。'
            '新完整时间PASS才全源CPU/同转换空间/426严格ZIP；额外错误STOP立即独立诊断，不能放宽color白名单。'
            f'详细controller/B2_COLOR_RECOVERY_20261008.md；{len(lock["files"])}冻结文件不改，不重复launcher。\n\n')
        if entry == 'b_score_aligned_package_v4':
            intro+=('v4另修复真实恢复回答的失败证据保存：原始返回在有效性校验前以独立且不可覆盖raw回执落盘，异常另记failure/traceback。'
                '3项CPU真实症状测试通过：无效响应拒绝后原文仍在、有效响应保留、重复写入拒绝。'
                'v3仅按完整命令/唯一PGID停止等待controller，未开始恢复GPU；旧568文件与STOP/成功物保持。'
                'v4色彩配方/生成算法/时长修复与v3相同，只生成已登记失败窗，不重复成功生成。\n\n')
    workspace=RUN.parents[3]
    for path,anchor in ((workspace/'AGENTS.md','# AIC 高光剪辑项目执行约定'),(RUN/'STATUS_AUTOPILOT_20261007.md','# Linux 后台接续登记')):
        content=path.read_bytes().decode('utf-8-sig');ending='\r\n' if '\r\n' in content else '\n'
        before,after=content.split(anchor,1)
        if after.lstrip().startswith('## 2026-10-08'):
            after='## 2026-10-07'+after.split('## 2026-10-07',1)[1]
        path.write_bytes((before+anchor+ending*2+intro.replace('\n',ending)+after.lstrip('\r\n')).encode('utf-8'))
    handoff=RUN/'controller/AUTONOMOUS_EXECUTION_20261008.md'
    original=handoff.read_text(encoding='utf-8')
    first=original.split('## 当前入口与真实状态',1)[0]
    trailing=original.split('## 流量、资源与最终交付',1)[1]
    steps=('## 必须继续到最终ZIP的工作\n\n'
        '当前路线已裁决为B2，按controller/NEXT_ACTION_B2_20261008.md与冻结入口CONTINUE/PROTOCOL执行。'
        '真实B LoRA生产时间不复用旧Z，完整NONTEST8再进426/521，全源空间/独立strict全部门保持；'
        '不重复旧教师拒绝或等待用户。若工程失败，核真实命令/父子PGID和原错误，复现修复，独立版本CPU/适当真实非测试验收、锁/单次启动，保持成功物原SHA，更新本监控入口。'
        '所有T监督科学STOP保持，不能翻转弱审核、失败转空、造标签或把B2当新训练。\n\n')
    handoff.write_text(first+'## 当前入口与真实状态\n\n'+intro+steps+'## 流量、资源与最终交付'+trailing,encoding='utf-8',newline='\n')
    decision=RUN/'controller/RELATIVE_SUMMARY_DECISION_20261008.md'
    text=decision.read_text(encoding='utf-8')
    marker='## 当前已裁决：优先保留已训练B的B2'
    if marker not in text:
        decision.write_text(text+'\n'+marker+'\n\n'+
            'v3已完整3正支持/1NO拒绝，T监督不准入。先前Z恢复为候选提案，现以NEXT_ACTION_B2_20261008.md为准：'
            '旧Z时间实际adapter=False，不是37.63已训练B；B2必须启用原B LoRA重新实际时间推理，合格全源CPU/同基座空间可逐SHA复用。'
            '此裁决保留已训练B而避免伪造T，并保持全部工程门和单个最终ZIP交付。\n',encoding='utf-8',newline='\n')
    payload={path.relative_to(RUN).as_posix():dict(data=base64.b64encode(path.read_bytes()).decode(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for path in (RUN/'STATUS_AUTOPILOT_20261007.md',handoff,decision,RUN/'controller/NEXT_ACTION_B2_20261008.md',
                     RUN/'controller/B2_DURATION_REPAIR_20261008.md')}
    color_report=RUN/'controller/B2_COLOR_RECOVERY_20261008.md'
    if color_report.exists():
        payload['controller/B2_COLOR_RECOVERY_20261008.md']=dict(data=base64.b64encode(color_report.read_bytes()).decode(),
            sha256=hashlib.sha256(color_report.read_bytes()).hexdigest())
    registration_path=RUN/'controller/autonomy_registration_20261008.json'
    if registration_path.is_file():
        old=registration_path.read_bytes()
        history=registration_path.with_name(registration_path.stem+'.history.'+hashlib.sha256(old).hexdigest()+'.json')
        if not history.exists():history.write_bytes(old)
        metadata=json.loads(old)
        metadata.update(entry=entry,source_lock_sha256=snapshot.get('source_lock_sha256'),snapshot_utc=snapshot['utc'],
            progress=snapshot.get('progress'),completion=snapshot.get('completion'),
            actual_process_count=len(snapshot['processes']),launch=snapshot.get('launch_receipt'),
            provider_actual_progress=(snapshot.get('b2_generation_provider') or {}).get('temporal_progress'),
            nontest8_status=(snapshot.get('nontest8_package') or {}).get('status'),
            nontest8_strict_checks=(snapshot.get('nontest8_strict') or {}).get('checks'),
            B2ZIP_completed=(snapshot.get('completion') or {}).get('stage')=='PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX',
            raw_receipt_cpu_status=(snapshot.get('b2_recovery_receipts_cpu') or {}).get('status'),
            utc=dt.datetime.now(dt.timezone.utc).isoformat())
        registration_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        payload['controller/autonomy_registration_20261008.json']=dict(
            data=base64.b64encode(registration_path.read_bytes()).decode(),
            sha256=hashlib.sha256(registration_path.read_bytes()).hexdigest())
    remote("""import base64,hashlib,json
from pathlib import Path
root=Path(%r)
for name,row in json.loads(base64.b64decode(%r)).items():
    assert name in ('STATUS_AUTOPILOT_20261007.md','controller/AUTONOMOUS_EXECUTION_20261008.md',
        'controller/RELATIVE_SUMMARY_DECISION_20261008.md','controller/NEXT_ACTION_B2_20261008.md',
        'controller/B2_DURATION_REPAIR_20261008.md','controller/B2_COLOR_RECOVERY_20261008.md',
        'controller/autonomy_registration_20261008.json')
    data=base64.b64decode(row['data']);assert hashlib.sha256(data).hexdigest()==row['sha256']
    (root/name).write_bytes(data)
print(json.dumps({'status':'PASS_LIVE_B2_AUTONOMOUS_HANDOFF','entry':%r}))
"""%(REMOTE,base64.b64encode(json.dumps(payload).encode()).decode(),entry))
    print(json.dumps(dict(entry=entry,stage=stage,completion=completion,processes=len(snapshot['processes']),utc=snapshot['utc'])))


if __name__=='__main__':
    main()
