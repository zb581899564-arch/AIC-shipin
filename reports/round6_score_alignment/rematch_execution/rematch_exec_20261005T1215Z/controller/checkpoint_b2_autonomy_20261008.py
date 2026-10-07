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
        for path in (RUN/'STATUS_AUTOPILOT_20261007.md',handoff,decision,RUN/'controller/NEXT_ACTION_B2_20261008.md')}
    remote("""import base64,hashlib,json
from pathlib import Path
root=Path(%r)
for name,row in json.loads(base64.b64decode(%r)).items():
    assert name in ('STATUS_AUTOPILOT_20261007.md','controller/AUTONOMOUS_EXECUTION_20261008.md',
        'controller/RELATIVE_SUMMARY_DECISION_20261008.md','controller/NEXT_ACTION_B2_20261008.md')
    data=base64.b64decode(row['data']);assert hashlib.sha256(data).hexdigest()==row['sha256']
    (root/name).write_bytes(data)
print(json.dumps({'status':'PASS_LIVE_B2_AUTONOMOUS_HANDOFF','entry':%r}))
"""%(REMOTE,base64.b64encode(json.dumps(payload).encode()).decode(),entry))
    print(json.dumps(dict(entry=entry,stage=stage,completion=completion,processes=len(snapshot['processes']),utc=snapshot['utc'])))


if __name__=='__main__':
    main()
