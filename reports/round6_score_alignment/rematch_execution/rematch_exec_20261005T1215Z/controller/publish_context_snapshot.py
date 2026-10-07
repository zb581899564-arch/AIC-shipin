"""Curate source and aggregate evidence; never export labels/media/weights."""
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil

RUN = Path(__file__).resolve().parent.parent
WORKSPACE = RUN.parents[3]
PUB = WORKSPACE / '.github-publication/AIC-shipin'
REL = RUN.relative_to(WORKSPACE).as_posix()


def edit(path, transform):
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n')
    new=transform(text).replace('\n',ending).splitlines(keepends=True)
    old=raw.decode('utf-8').splitlines(keepends=True)
    matcher=difflib.SequenceMatcher(None,[line.rstrip('\r\n')for line in old],[line.rstrip('\r\n')for line in new],autojunk=False)
    for a,b,size in matcher.get_matching_blocks():new[b:b+size]=old[a:a+size]
    path.write_bytes(''.join(new).encode('utf-8'))


snapshot=json.loads((RUN/'controller/monitor_aic_linux/latest.json').read_text())
entry=snapshot['entry']
assert entry=='teacher_context_diagnostic_v3'
cpu=json.loads((RUN/entry/'cpu_acceptance.json').read_text())
phase=(snapshot.get('progress') or {}).get('stage') or (snapshot.get('progress') or {}).get('status') or '全SHA/注册中'
when=dt.datetime.fromisoformat(snapshot['utc']).astimezone(dt.timezone(dt.timedelta(hours=8)))
evidence=len(snapshot.get('context_diagnostic_requests',[]))
common=(f"2026-10-08 {when:%H:%M} UTC+8：用户已授权完全自主裁决、修复和接续至最终 ZIP，已有监控改为每15分钟静默检查。"
        "v7于10月7日23:49:31科学STOP：12/12均正、真实空0，第二真实弱复查12/12为10支持/2拒绝，工程失败0；旧失败与标签保持，T更新0，无新T ZIP。\n\n"
        f"当前独立 [相对全源摘要必要性诊断v3]({REL}/{entry}/CONTINUE.md)：v2完整4次有/无背景配对均正、状态未变，因此v3改为先说明整段可见主内容、与窗外比较再判断目标保留价值。"
        "剩余校准来源只按split内window_id SHA各选2条，不按旧标签或内容筛选；4次判断后全部4次真实弱复查，无配额。校准不是未触碰验证，诊断回答不成为训练标签或人工真值。"
        f"{cpu['checks']}项Linux CPU（{cpu['actual_pinned_grammar_examples']}实际固定runtime grammar、256真实native时间）和原记录逐SHA/validator回放通过；"
        f"312文件锁 `{snapshot['source_lock_sha256']}`，单次launcher历史PID `{(snapshot.get('launch_receipt') or {}).get('pid')}`。"
        f"该次实查阶段 `{phase}`，判断 `{evidence}/4`、复查 `{len(snapshot.get('context_diagnostic_reviews',[]))}/4`、实际命令进程 `{len(snapshot['processes'])}`、所属server `{len(snapshot['owned_servers'])}`。\n\n"
        "诊断v1首请求错配frame ordinal与另一帧的秒数，差0.5005秒，被独立validator正确拒绝。v2以每帧完整ordinal/time对象anyOf固定配对，"
        "时间用源数据的完整十进制字符串与Decimal验证；固定C++ JSON/runtime numeric常量变位已复现，原失败不改写/复用。"
        f"见[独立修复]({REL}/teacher_context_diagnostic_v2/REPAIR.md)、[科学决策]({REL}/controller/RELATIVE_SUMMARY_DECISION_20261008.md)和[自主接续]({REL}/controller/AUTONOMOUS_EXECUTION_20261008.md)。\n\n"
        "完整八请求后按证据独立登记下一监督或可交付8B方案。T仍经原完整质量门推进B LoRA lr1e-5/最多3epochs、第20更新实际重载、开发、NONTEST8、426独立strict ZIP。"
        "不重复已证伪配方、不造空或弱化科学门。最终只交付一个Linux ZIP，不自动回传/官网上传；新大流量先许可，Mac不参与。"
        "Linux后台计算独立运行；本地定时诊断/修复需要Windows开机且Codex运行。旧预测失效，官网新分未知。\n\n"
        "v7的94项CPU、10302实际端点、12原目标无损及两条真实native解码验收仍有效；工程通过不代表标签分布或CUDA训练通过。"
        f"[全链审计]({REL}/controller/COMPREHENSIVE_AUDIT_20261007.md)保留全部问题与限制。\n\n")
def readme(text):
    prefix,after=text.split('旧已评分包不变。',1)
    _,tail=after.split('Z已完成',1)
    prefix=prefix.replace('## 下一轮代码修复与执行（2026-10-07）','## 下一轮代码修复与自主执行（2026-10-08）')
    return prefix+'旧已评分包不变。\n\n'+common+'Z已完成'+tail
edit(PUB/'README.md',readme)
for name in ('SOLUTIONS.md','REPRODUCTION.md'):
    # Markdown paths in docs are one directory deeper than README.
    section=common.replace(']('+REL,'](../'+REL)
    if name=='SOLUTIONS.md':
        edit(PUB/'docs'/name,lambda text:'# 方案、证据与当前状态\n\n## 当前自主接续与真实诊断\n\n'+section+'## 复赛 A：'+text.split('## 复赛 A：',1)[1])
    else:
        edit(PUB/'docs'/name,lambda text:re.split(r'## 当前(?:v7工程修复|自主诊断)复现范围',text,maxsplit=1)[0]+'## 当前自主诊断复现范围\n\n'+section+
             "v6/v7和context v1/v2核心源码、CPU检查、source_lock与聚合停止/验收回执随仓库发布。媒体、逐样本标签/回答、权重不分发。新机器需自行恢复授权资产并另建版本和锁，不执行历史一次性launcher。\n")

selected=[WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md',
          RUN/'controller/AUTONOMOUS_EXECUTION_20261008.md',RUN/'controller/inspect_autopilot_live.py',
          RUN/'controller/register_context_diagnostic_v1.py',RUN/'controller/checkpoint_autonomy_20261008.py',
          RUN/'controller/publish_context_snapshot.py',RUN/'controller/RELATIVE_SUMMARY_DECISION_20261008.md',
          RUN/'controller/monitor_aic_linux/latest.json']
for version in ('teacher_context_diagnostic_v1','teacher_context_diagnostic_v2','teacher_context_diagnostic_v3'):
    selected += [path for path in (RUN/version).iterdir() if path.is_file() and
                 (path.suffix in ('.py','.md','.json') or path.name in ('prompt.txt','review_prompt.txt','cpu_tests.stdout.txt','cpu_tests.stderr.txt',
                     'prepare.stdout.txt','prepare.stderr.txt','diagnostic.stdout.txt','diagnostic.stderr.txt'))]
for relative in ('teacher_student_autopilot_v7/completion.json','teacher_student_autopilot_v7/pilot_01/completion.json',
                 'teacher_student_autopilot_v7/pilot_01/distribution.json'):
    if (RUN/relative).is_file():selected.append(RUN/relative)
for path in selected:
    destination=PUB/path.relative_to(WORKSPACE)
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,destination)

manifest_path=PUB/'docs/publication_manifest.json'
old=manifest_path.read_bytes();ending='\r\n' if b'\r\n' in old else '\n'
manifest=json.loads(old)
rows={r['path']:r for r in manifest['files']}
for path in selected:
    relative=path.relative_to(WORKSPACE).as_posix()
    if relative not in rows:
        row={'path':relative,'source_relative_path':relative,'bytes':0,'sha256':'',
             'category':'project_code_or_configuration' if path.suffix=='.py' else 'experiment_protocol_or_acceptance'}
        manifest['files'].append(row);rows[relative]=row
for row in manifest['files']:
    path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
manifest_path.write_bytes((json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').replace('\n',ending).encode('utf-8'))
print(json.dumps({'status':'PASS_CURATED_CONTEXT_CODE_AND_AGGREGATES','files_selected':len(selected),
                  'manifest_files':len(manifest['files']),'raw_model_answers_exported':False,'new_labels_exported':False}))
