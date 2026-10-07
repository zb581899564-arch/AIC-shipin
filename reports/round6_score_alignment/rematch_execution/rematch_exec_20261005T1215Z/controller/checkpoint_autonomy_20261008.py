"""Inspect live identity, save bounded evidence and current human-neutral handoff."""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

from register_context_diagnostic_v1 import remote, RUN, REMOTE

parser=argparse.ArgumentParser();parser.add_argument('--entry',default='teacher_context_diagnostic_v3')
entry=parser.parse_args().entry
assert re.fullmatch(r'teacher_context_diagnostic_v[1-9][0-9]*',entry)
inspector=(RUN/'controller/inspect_autopilot_live.py').read_bytes()
script="""import base64,hashlib,json,sys
from pathlib import Path
root=Path(%r)
entry=%r
path=root/'controller/inspect_autopilot_live.py'
for lock in (root/entry/'source_lock.json',root/'teacher_student_autopilot_v7/source_lock.json'):
    assert str(path) not in json.loads(lock.read_text())['files'],'frozen inspector must not change'
data=base64.b64decode(%r)
assert hashlib.sha256(data).hexdigest()==%r
path.write_bytes(data)
sys.path.insert(0,str(path.parent))
import inspect_autopilot_live as monitor
snapshot_path,snapshot=monitor.capture(entry.rsplit('_',1)[1],entry)
files={}
for name in ('start_receipt.json','registration.json','progress.json','completion.json'):
    p=root/entry/name
    if p.is_file():files[name]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps({'snapshot':snapshot,'remote_snapshot_path':str(snapshot_path),'files':files}))
""" % (REMOTE,entry,base64.b64encode(inspector).decode(),hashlib.sha256(inspector).hexdigest())
data=json.loads(remote(script,echo=False))
snapshot=data['snapshot']
directory=RUN/'controller/monitor_aic_linux'
directory.mkdir(exist_ok=True)
raw=(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n').encode()
(directory/'latest.json').write_bytes(raw)
(directory/Path(data['remote_snapshot_path']).name).write_bytes(raw)
for name,content in data['files'].items(): (RUN/entry/name).write_bytes(base64.b64decode(content))

launch=snapshot.get('launch_receipt') or {}
cpu=json.loads((RUN/entry/'cpu_acceptance.json').read_text())
manifest=json.loads((RUN/entry/'manifest.json').read_text())
control_bytes=sum((RUN/entry/name).stat().st_size for name in
                  ('PROTOCOL.md','prompt.txt','review_prompt.txt','diagnostic.py','cpu_tests.py','prepare.py','launch.py','CONTINUE.md','REPAIR.md')
                  if (RUN/entry/name).is_file())
requests=snapshot.get('context_diagnostic_requests',[])
stage=(snapshot.get('progress') or {}).get('stage') or (snapshot.get('progress') or {}).get('status') or 'waiting for registration'
completion=snapshot.get('completion')
utc=dt.datetime.fromisoformat(snapshot['utc']);local=utc.astimezone(dt.timezone(dt.timedelta(hours=8)))
intro=(f"## 2026-10-08 {local:%H:%M} UTC+8：自主裁决与15分钟静默监控已登记\n\n"
       "用户完全放权到最终ZIP；工程修复、科学路线、独立新版本和接续均自主完成，阶段证据写项目，最后验收报告一次。新大流量仍先许可，Mac不参与，最终包留Linux、不自动回传或官网上传。\n\n"
       "v7已于10月7日23:49:31科学STOP：12/12正、空0、工程失败0，第二真实弱复查10支持/2拒绝；原标签与234冻结文件保持。没有T更新或T ZIP，不重开旧配方。\n\n"
       f"当前入口{entry}/CONTINUE.md，{len(json.loads((RUN/entry/'source_lock.json').read_text())['files'])}文件锁SHA{snapshot['source_lock_sha256']}。"
       f"{cpu['checks']}项Linux CPU合同（含{cpu['actual_pinned_grammar_examples']}实际runtime grammar）和原记录逐SHA/validator回放通过，{control_bytes:,}字节小量控制代码直接SSH部署。"
       f"一次launcher历史PID{launch.get('pid')}，{local:%H:%M}实际完整路径捕获进程{len(snapshot['processes'])}、所属server{len(snapshot['owned_servers'])}，"
       f"阶段{stage}，真实判断{len(requests)}/{len(manifest['window_ids'])}、复查{len(snapshot.get('context_diagnostic_reviews',[]))}/{manifest.get('review_requests',0)}，"
       f"全源背景回执{len(snapshot.get('context_overview_receipts',[]))}/{len(manifest['window_ids'])}。"
       f"完成回执{(completion or {}).get('status','尚未写出')}。诊断输出不是训练标签，不宣称上下文已解决科学阻塞。\n\n"
       f"v1首请求将ordinal1723错配另一帧时间，差0.5005秒，独立诊断validator正确拒绝；独立v2/v3绑定每帧ordinal/time完整anyOf，使用原始十进制字符串和Decimal验证。固定C++ converter数字常量变位已CPU复现；当前{cpu.get('actual_native_endpoints_checked',0)}真实native时间无损通过，全部旧失败保持。\n\n"
       "v2实际4/4判断完成，两个有/无整段overview配对均正、状态未变，0工程失败；不能声称添加背景已解决分布。独立v3改变科学任务为先说明整段可见主内容与窗外对比，再判断摘要必要性。原校准剩余来源按split/window_id SHA各取两条，共4判断+全部4真实弱复查；不按旧标签或拒绝筛选，无类别/时长配额。旧校准不冒充未触碰验证。\n\n"
       "完整诊断后按证据自主登记下一监督或可交付方案，并继续原完整质量门→B LoRA lr1e-5最多3epochs→开发→NONTEST8→426独立strict ZIP。诊断若不支持则不重复盲试，不造空或弱化门。详细接续controller/AUTONOMOUS_EXECUTION_20261008.md，实际快照controller/monitor_aic_linux/latest.json。\n\n"
       "aic-linux每15分钟静默检查；完成前不发阶段通知，异常立即自主处理。Windows开机且Codex运行才能唤醒本地检查，Linux后台计算独立继续。旧时间预测和下方快照均历史。\n\n")

workspace=RUN.parents[3]
assert (workspace/'AGENTS.md').is_file(),workspace
for path,anchor in ((workspace/'AGENTS.md','# AIC 高光剪辑项目执行约定'),
                    (RUN/'STATUS_AUTOPILOT_20261007.md','# Linux 后台接续登记')):
    content=path.read_bytes().decode('utf-8-sig')
    ending='\r\n' if '\r\n' in content else '\n'
    before,after=content.split(anchor,1)
    if after.lstrip().startswith('## 2026-10-08'):
        after='## 2026-10-07'+after.split('## 2026-10-07',1)[1]
    updated=before+anchor+ending*2+intro.replace('\n',ending)+after.lstrip('\r\n')
    path.write_bytes(updated.encode('utf-8'))

handoff=RUN/'controller/AUTONOMOUS_EXECUTION_20261008.md'
content=handoff.read_text(encoding='utf-8')
before,tail=content.split('## 当前入口与真实状态',1)
_,rest=tail.split('## 必须继续到最终ZIP的工作',1)
content=before+'## 当前入口与真实状态\n\n'+intro+'## 必须继续到最终ZIP的工作'+rest
handoff.write_text(content,encoding='utf-8',newline='\n')

payload={path.relative_to(RUN).as_posix():{'data':base64.b64encode(path.read_bytes()).decode(),
                                  'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
         for path in (RUN/'STATUS_AUTOPILOT_20261007.md',handoff,RUN/'controller/RELATIVE_SUMMARY_DECISION_20261008.md')}
remote("""import base64,hashlib,json
from pathlib import Path
root=Path(%r)
rows=json.loads(base64.b64decode(%r))
for name,row in rows.items():
    assert name in ('STATUS_AUTOPILOT_20261007.md','controller/AUTONOMOUS_EXECUTION_20261008.md','controller/RELATIVE_SUMMARY_DECISION_20261008.md')
    data=base64.b64decode(row['data']);assert hashlib.sha256(data).hexdigest()==row['sha256']
    (root/name).write_bytes(data)
print(json.dumps({'status':'PASS_CURRENT_AUTONOMOUS_HANDOFF_SAVED','files':len(rows)}))
""" % (REMOTE,base64.b64encode(json.dumps(payload).encode()).decode()))
print(json.dumps({'status':'PASS_LIVE_CONTEXT_DIAGNOSTIC_CHECKPOINT','entry':entry,'phase':stage,
                  'requests':len(requests),'processes':len(snapshot['processes']),
                  'owned_servers':len(snapshot['owned_servers']),'utc':snapshot['utc']}))
