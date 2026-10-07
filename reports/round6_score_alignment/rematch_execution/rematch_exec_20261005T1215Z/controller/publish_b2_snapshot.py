"""Publish exact B2 core and aggregate receipts; no media, labels or per-frame data."""
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import shutil

RUN=Path(__file__).resolve().parent.parent
WORKSPACE=RUN.parents[3]
PUB=WORKSPACE/'.github-publication/AIC-shipin'
REL=RUN.relative_to(WORKSPACE).as_posix()


def edit(path, transform):
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n')
    new=transform(text).replace('\n',ending).splitlines(keepends=True)
    old=raw.decode('utf-8').splitlines(keepends=True)
    matcher=difflib.SequenceMatcher(None,[line.rstrip('\r\n') for line in old],[line.rstrip('\r\n') for line in new],autojunk=False)
    for a,b,count in matcher.get_matching_blocks():new[b:b+count]=old[a:a+count]
    path.write_bytes(''.join(new).encode('utf-8'))


def aggregate_processor(value):
    return {key:value[key] for key in ('status','actual_source_videos','HD_defaults_tensor_equal',
        'same_encode_function_as_production','synthetic_cases','actual_CUDA_started','optimizer_updates',
        'confirm_read','rematch_pixels_read','wall_seconds') if key in value}


def main():
    snapshot=json.loads((RUN/'controller/monitor_aic_linux/latest.json').read_text())
    entry=snapshot['entry'];assert entry.startswith('b_score_aligned_package_')
    cpu=json.loads((RUN/entry/'cpu_acceptance.json').read_text())
    lock=json.loads((RUN/entry/'source_lock.json').read_text())
    phase=(snapshot.get('progress') or {}).get('stage','CPU/SHA核验')
    probe=snapshot.get('b2_probe') or {}
    cuda=('实际B LoRA长输入CUDA已PASS：12048token、288 adapter张量与保存值相等、全基座SHA与原训练相等，选择token分数有限；0优化器更新。'
          if probe.get('status')=='PASS_B2_ACTUAL_TRAINED_ADAPTER_LONG_CUDA_INFERENCE' else '实际长输入CUDA尚待真实回执。')
    when=dt.datetime.fromisoformat(snapshot['utc']).astimezone(dt.timezone(dt.timedelta(hours=8)))
    common=(f'2026-10-08 {when:%H:%M} UTC+8：当前自主接续为[B2已微调8B生产对齐]({REL}/{entry}/CONTINUE.md)。'
        '保留已评分37.63的B最终LoRA，不增加训练更新；时间使用B adapter、空间同8B原生基座，总逻辑参数8,782,459,120。'
        'B2采用所有分支实际native PTS/floor64帧/顺序PyAV/16384长输入、精确端点与全源空间场，仍用B原1–5段提示与greedy。旧37.63仍绑定旧B包，新B2官网分未知。\n\n'
        '32B context v3已经完整8/8真实请求、0工程失败，三正被弱审核支持，唯一NO被拒绝；没有受支持真实空例，T更新0。'
        '审核声称overview仅到119.0189秒，实际完整源回执末PTS149.98316666666668、13帧>=120；事实性错误和语义争议同时保留，不能将拒绝改PASS或空标签当真值。'
        '旧raw/失败/科学STOP保存；不再盲试同配方，不造空或弱化原监督门。B2是保留已经训练B的可交付路线，不冒充新教师T训练。\n\n'
        f'{cpu["tests"]}项CPU、434来源/529真实自然窗/33447样本端点、12原目标无损回放与实际processor/HD/8非测试源重开pixel SHA通过。'
        f'{len(lock["files"])}文件锁 `{snapshot["source_lock_sha256"]}`，单次launcher历史PID `{(snapshot.get("launch_receipt") or {}).get("pid")}`；'
        f'本次快照阶段 `{phase}`、实际命令进程 `{len(snapshot["processes"])}`。'+cuda+'完整NONTEST8/426严格包分别看实际回执，尚未宣称ZIP完成。\n\n'
        '旧Z时间实际adapter=False，521旧时间不能复用B2。非测试全源CPU/同基座空间只在输入/算法/关键SHA与完整回执一致后原样复用；'
        '复赛旧CPU域与新native源域不同，不准入复用，真实重算全源CPU/空间。后台真实B长输入CUDA→NONTEST8→426/521时间/全源空间→独立strict ZIP。'
        '最终只有真实B2 completion PASS、8/426独立strict全部true、大小/SHA/CRC/唯一JSONL/426身份验收才可提交。\n\n'
        '已有监控每15分钟静默核查、自主修复并更新证据，最后汇报一次。Linux后台独立运行，本地巡检需要Windows开机且Codex运行。'
        '最终只有一个选定ZIP留Linux，不自动回传或AIC上传；新大流量先许可、Mac退出，实际容量与共享GPU锁/账本/7200保持。'
        f'见[B2决策]({REL}/controller/NEXT_ACTION_B2_20261008.md)、[协议]({REL}/{entry}/PROTOCOL.md)、[实时接续]({REL}/STATUS_AUTOPILOT_20261007.md)。\n\n')
    if entry == 'b_score_aligned_package_v2':
        common+=('v2独立修复统一canonical duration：真实529窗56处差异，原29合法全端点误拒绝逐一复现；'
            '新529全端点/529 nextafter上界拒绝、原529输入相等全部通过。原v1有效GPU生成继续到完整426/521；'
            'v2只原字节复用逐SHA/原validator/实际模型与输入身份验收的probe/时间，重新完整NONTEST8/strict，'
            '随后等待原GPU完成记账并受控移交CPU，再全源空间/426严格ZIP。不打断有效生成，不把复用写成新CUDA或新T训练。'
            f'见[端点修复与移交]({REL}/controller/B2_DURATION_REPAIR_20261008.md)。\n\n')
    if entry in ('b_score_aligned_package_v3','b_score_aligned_package_v4'):
        version=entry.rsplit('_',1)[1]
        common+=(f'{version}保持canonical时长修复，新加SHA绑定的97送模型前log316/errno95转换修复：'
            '临时UNSPECIFIED transfer/限定范围ITU601样本映射后恢复frame元数据，原源/YUV/range/尺寸/PTS不变，不声称恢复摄影gamma曲线。'
            '其他源默认转换保持，9转换CPU/64实际帧RGB与空间BGR完全对应、69原CPU/实际processor/8非测试pixel SHA通过；'
            f'11独立所有权mock及6实际失败分类CPU通过。v1有效GPU计算不打断，{version}新NONTEST8后等待完整provider和记账，'
            '所有成功原validator/输入/SHA核验原字节保留，只为登记送模型前错误真正生成一次；旧失败STOP保留，不转空/减426分母。'
            f'见[显式转换与恢复]({REL}/controller/B2_COLOR_RECOVERY_20261008.md)。\n\n')
        if entry == 'b_score_aligned_package_v4':
            common+=('v4另修复恢复失败证据丢失：新返回原文先写独立且不可覆盖raw，再做有效性校验，异常另记failure/traceback；'
                '3项CPU验收无效原文保留/有效原文保留/重复覆盖拒绝通过。v3只停止等待controller，未开始恢复GPU，旧锁与产物保留。'
                '冻结源码不回写，生成/色彩/时间配方保持v3，不重复任何成功推理。\n\n')
    def readme(text):
        before,rest=text.split('旧已评分包不变。',1)
        _,tail=rest.split('## 资源策略已取消人为额度',1)
        row='| 复赛 | B2：保留Linux B最终LoRA、native输入与全源空间场 | 未评分 | [代码与生成状态]('+REL+'/'+entry+'/CONTINUE.md)；ZIP验收中 |\n'
        if '| B2：' not in before:
            start=before.index('| 复赛 | Mac 8B：')
            before=before[:start]+row+before[start:]
        else:
            before='\n'.join(row.rstrip('\n') if line.startswith('| 复赛 | B2：') else line for line in before.split('\n'))
        return before+'旧已评分包不变。\n\n'+common+'## 资源策略已取消人为额度'+tail
    edit(PUB/'README.md',readme)
    core_row='| B2已训练B生产对齐 | ['+entry+']('+REL+'/'+entry+')：`engine.py`、`native_input.py`、`source_color.py`、`temporal_reuse.py`、`recovery.py`、`production.py`、`controller.py` |'
    edit(PUB/'README.md',lambda text:'\n'.join(core_row if line.startswith('| B2已训练B生产对齐 |') else line for line in text.split('\n'))
         if '| B2已训练B生产对齐 |' in text else text.replace('| 新教师/8B全链与审计修复 |',core_row+'\n| 新教师/8B全链与审计修复 |'))
    section=common.replace(']('+REL,'](../'+REL)
    edit(PUB/'docs/SOLUTIONS.md',lambda text:'# 方案、证据与当前状态\n\n## 当前自主B2接续\n\n'+section+'## 复赛 A：'+text.split('## 复赛 A：',1)[1])
    edit(PUB/'docs/REPRODUCTION.md',lambda text:text.split('## 当前自主诊断复现范围',1)[0].split('## 当前B2复现范围',1)[0]+
        '## 当前B2复现范围\n\n'+section+'B2核心代码保持工作项目原字节。聚合processor验收另注明原回执SHA；不导出逐帧原生时间、像素数据、弱标签/原始回答、权重或运行环境。'
        '完整模型/source_lock需要自行恢复已授权私有资产，新机器另建版本和一次性注册，不执行历史launcher。\n')
    selected=[WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
    selected += [RUN/'controller'/name for name in ('NEXT_ACTION_B2_20261008.md','AUTONOMOUS_EXECUTION_20261008.md',
        'RELATIVE_SUMMARY_DECISION_20261008.md','inspect_autopilot_live.py','checkpoint_b2_autonomy_20261008.py',
        'register_b2_package_v1.py','build_b2_control.py','publish_b2_snapshot.py',
        'build_b2_duration_repair.py','B2_DURATION_REPAIR_20261008.md','build_b2_color_repair.py',
        'B2_COLOR_RECOVERY_20261008.md','test_b2_handoff_cpu.py')]
    selected += [p for pattern in ('B2_v3_*_cpu_20261008.json','B2_v4_*_cpu_20261008.json')
                 for p in (RUN/'controller').glob(pattern) if p.is_file()]
    selected += [RUN/'controller/autonomy_registration_20261008.json']
    history=[name for name in ('b_score_aligned_package_v2','b_score_aligned_package_v3') if name!=entry and (RUN/name).is_dir()]
    selected += [path for name in [*history,entry] for path in (RUN/name).iterdir()
                 if path.is_file() and path.suffix in ('.py','.md','.json') and
                 path.name not in ('processor_acceptance.json','source_color_acceptance.json')]
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    processor=json.loads((RUN/entry/'processor_acceptance.json').read_text())
    aggregate=aggregate_processor(processor)
    aggregate.update(original_receipt_sha256=hashlib.sha256((RUN/entry/'processor_acceptance.json').read_bytes()).hexdigest(),
                     per_frame_source_data_exported=False)
    destination=PUB/REL/entry/'processor_acceptance_summary.json'
    destination.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    derived=[destination]
    for name in history:
        path=RUN/name/'processor_acceptance.json'
        if path.is_file():
            summary=aggregate_processor(json.loads(path.read_text()))
            summary.update(original_receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           per_frame_source_data_exported=False)
            destination_history=PUB/REL/name/'processor_acceptance_summary.json'
            destination_history.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            derived.append(destination_history)
        path=RUN/name/'source_color_acceptance.json'
        if path.is_file():
            color=json.loads(path.read_text())
            summary={key:value for key,value in color.items() if key not in ('actual_production_window','actual_native_evidence')}
            summary.update(original_receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           per_frame_source_data_exported=False)
            destination_history=PUB/REL/name/'source_color_acceptance_summary.json'
            destination_history.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            derived.append(destination_history)
    color_path=RUN/entry/'source_color_acceptance.json'
    if color_path.is_file():
        color=json.loads(color_path.read_text())
        color_summary={key:value for key,value in color.items() if key not in ('actual_production_window','actual_native_evidence')}
        color_summary.update(original_receipt_sha256=hashlib.sha256(color_path.read_bytes()).hexdigest(),
                             per_frame_source_data_exported=False)
        destination_color=PUB/REL/entry/'source_color_acceptance_summary.json'
        destination_color.write_text(json.dumps(color_summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        derived.append(destination_color)
    if probe:
        probe_summary={key:probe[key] for key in ('status','model_identity','synthetic_only','contest_media_read',
            'optimizer_updates','peak_allocated_mib','wall_seconds') if key in probe}
        probe_summary.update(original_receipt_sha256=snapshot.get('b2_probe_receipt_sha256'),
            input_tokens=probe['input_identity']['input_tokens'],
            selected_generation_scores_finite=probe['generation']['selected_generation_scores_finite'],
            per_frame_data_exported=False)
        destination_probe=PUB/REL/entry/'probe_acceptance_summary.json'
        destination_probe.write_text(json.dumps(probe_summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        derived.append(destination_probe)
    public_snapshot=dict(snapshot)
    public_snapshot['b2_processor_acceptance']=aggregate_processor(snapshot.get('b2_processor_acceptance') or {})
    if public_snapshot.get('b2_probe'):
        probe=public_snapshot['b2_probe']
        public_snapshot['b2_probe']={key:probe[key] for key in ('status','model_identity','synthetic_only','contest_media_read',
            'optimizer_updates','peak_allocated_mib','wall_seconds') if key in probe}
    monitor=PUB/REL/'controller/monitor_aic_linux/latest.json'
    monitor.write_text(json.dumps(public_snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    manifest_path=PUB/'docs/publication_manifest.json';old=manifest_path.read_bytes();ending='\r\n' if b'\r\n' in old else '\n'
    manifest=json.loads(old);items={row['path']:row for row in manifest['files']}
    additions=[path.relative_to(WORKSPACE).as_posix() for path in selected]+[path.relative_to(PUB).as_posix() for path in derived]+[monitor.relative_to(PUB).as_posix()]
    for relative in additions:
        if relative not in items:
            row=dict(path=relative,source_relative_path=relative,bytes=0,sha256='',category='project_code_or_configuration' if relative.endswith('.py') else 'experiment_protocol_or_acceptance')
            manifest['files'].append(row);items[relative]=row
    for path in derived:
        items[path.relative_to(PUB).as_posix()]['source_relative_path']=None
        items[path.relative_to(PUB).as_posix()]['category']='aggregate_acceptance_no_frame_data'
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    manifest_path.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_B2_CORE_AND_AGGREGATES',manifest_files=len(manifest['files']),
        selected_files=len(selected),per_frame_data_exported=False,raw_labels_or_weights_exported=False)))


if __name__=='__main__':
    main()
