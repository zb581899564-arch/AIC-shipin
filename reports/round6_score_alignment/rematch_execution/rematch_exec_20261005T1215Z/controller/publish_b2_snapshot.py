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
    completion=snapshot.get('completion') or {}
    strict=[snapshot.get(key) or {} for key in ('nontest8_strict','rematch_strict')]
    final_ready=(completion.get('stage')=='PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX' and
        completion.get('crc_pass') is True and completion.get('videos')==426 and
        completion.get('archive_names')==['predictions.jsonl'] and
        all(row.get('status')=='PASS_INDEPENDENT_STRICT_VALIDATION' and len(row.get('checks',{}))==11 and
            all(value is True for value in row['checks'].values()) for row in strict))
    if final_ready and entry == 'b_score_aligned_package_v4':
        final_acceptance=json.loads((RUN/'controller/B2_v4_final_acceptance_20261008.json').read_text())
        assert final_acceptance['status']=='PASS_INDEPENDENT_B2_FINAL_ZIP_ACCEPTANCE'
        assert final_acceptance['source_lock_sha256']==snapshot['source_lock_sha256']
        assert final_acceptance['scopes']['rematch']['zip_sha256']==completion['zip_sha256']
        assert final_acceptance['scopes']['rematch']['zip_bytes']==completion['zip_bytes']
    package_state=('Linux最终ZIP终态与NONTEST8/426全部独立strict登记已PASS。'
        f'包 `{completion["candidate"]}`，实际 `{completion["zip_bytes"]}` 字节，SHA256 `{completion["zip_sha256"]}`。'
        '包仍留Linux，尚无新官网分。' if final_ready else
        '完整NONTEST8/426严格包分别看实际回执，尚未宣称最终ZIP完成。')
    probe=snapshot.get('b2_probe') or {}
    cuda=('实际B LoRA长输入CUDA已PASS：12048token、288 adapter张量与保存值相等、全基座SHA与原训练相等，选择token分数有限；0优化器更新。'
          if probe.get('status')=='PASS_B2_ACTUAL_TRAINED_ADAPTER_LONG_CUDA_INFERENCE' else '实际长输入CUDA尚待真实回执。')
    when=dt.datetime.fromisoformat(snapshot['utc']).astimezone(dt.timezone(dt.timedelta(hours=8)))
    monitor_state=('最终ZIP已完整验收，本轮巡检在交付时结束。' if final_ready else
                   '已有监控每15分钟静默核查、自主修复并更新证据，最后汇报一次。')
    common=(f'2026-10-08 {when:%H:%M} UTC+8：当前路线为[B2已微调8B生产对齐]({REL}/{entry}/CONTINUE.md)。'
        '保留已评分37.63的B最终LoRA，不增加训练更新；时间使用B adapter、空间同8B原生基座，总逻辑参数8,782,459,120。'
        'B2采用所有分支实际native PTS/floor64帧/顺序PyAV/16384长输入、精确端点与全源空间场，仍用B原1–5段提示与greedy。旧37.63仍绑定旧B包，新B2官网分未知。\n\n'
        '32B context v3已经完整8/8真实请求、0工程失败，三正被弱审核支持，唯一NO被拒绝；没有受支持真实空例，T更新0。'
        '审核声称overview仅到119.0189秒，实际完整源回执末PTS149.98316666666668、13帧>=120；事实性错误和语义争议同时保留，不能将拒绝改PASS或空标签当真值。'
        '旧raw/失败/科学STOP保存；不再盲试同配方，不造空或弱化原监督门。B2是保留已经训练B的可交付路线，不冒充新教师T训练。\n\n'
        f'{cpu["tests"]}项CPU、434来源/529真实自然窗/33447样本端点、12原目标无损回放与实际processor/HD/8非测试源重开pixel SHA通过。'
        f'{len(lock["files"])}文件锁 `{snapshot["source_lock_sha256"]}`，单次launcher历史PID `{(snapshot.get("launch_receipt") or {}).get("pid")}`；'
        f'本次快照阶段 `{phase}`、实际命令进程 `{len(snapshot["processes"])}`。'+cuda+package_state+'\n\n'
        '旧Z时间实际adapter=False，521旧时间不能复用B2。非测试全源CPU/同基座空间只在输入/算法/关键SHA与完整回执一致后原样复用；'
        '复赛旧CPU域与新native源域不同，不准入复用，真实重算全源CPU/空间。后台真实B长输入CUDA→NONTEST8→426/521时间/全源空间→独立strict ZIP。'
        '最终只有真实B2 completion PASS、8/426独立strict全部true、大小/SHA/CRC/唯一JSONL/426身份验收才可提交。\n\n'
        f'{monitor_state}Linux后台独立运行，本地巡检需要Windows开机且Codex运行。'
        '最终只有一个选定ZIP留Linux，不自动回传或AIC上传；新大流量先许可、Mac退出，实际容量与共享GPU锁/账本/7200保持。'
        f'见[B2决策]({REL}/controller/NEXT_ACTION_B2_20261008.md)、[协议]({REL}/{entry}/PROTOCOL.md)、[实时接续]({REL}/STATUS_AUTOPILOT_20261007.md)。\n\n')
    if final_ready and entry == 'b_score_aligned_package_v4':
        common+=f'最终实物ZIP、8/426身份与全部strict、31,295个真实锚点及GPU追加账本已独立复核，见[最终验收]({REL}/controller/B2_v4_final_acceptance_20261008.json)。\n\n'
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
            temporal=(snapshot.get('production_stage_receipts') or {}).get('rematch_01',{}).get('temporal.stage.json') or {}
            if temporal.get('status')=='PASS_TEMPORAL_EXECUTION':
                common+=(f'完整426/521时间已PASS、无效{temporal["invalid_windows"]}；'
                    f'原{temporal["original_record_raw_lines_exact"]}成功记录整行字节/{temporal["original_successful_windows_reused"]}成功窗口相等，'
                    f'仅为已登记送模型前失败实际新生成{temporal["new_generation_calls"]}窗MODEL_OK，原失败和STOP保留。'
                    '原raw与接受窗、全部分母及NONTEST8/11 strict均经独立验收；实际GPU费用单独按wrapper账本核。'
                    f'见[真实恢复验收]({REL}/controller/B2_v4_recovery_acceptance_20261008.json)。\n\n')
    def readme(text):
        before,rest=text.split('旧已评分包不变。',1)
        _,tail=rest.split('## 资源策略已取消人为额度',1)
        package_label='`candidate_B2_8B.zip` 已在Linux严格验收' if final_ready else 'ZIP验收中'
        row='| 复赛 | B2：保留Linux B最终LoRA、native输入与全源空间场 | 未评分 | [代码与生成状态]('+REL+'/'+entry+'/CONTINUE.md)；'+package_label+' |\n'
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
        'register_b2_package_v1.py','build_b2_control.py','publish_b2_snapshot.py','verify_b2_final_20261008.py',
        'build_b2_duration_repair.py','B2_DURATION_REPAIR_20261008.md','build_b2_color_repair.py',
        'B2_COLOR_RECOVERY_20261008.md','test_b2_handoff_cpu.py')]
    selected += [p for pattern in ('B2_v3_*_cpu_20261008.json','B2_v4_*_cpu_20261008.json')
                 for p in (RUN/'controller').glob(pattern) if p.is_file()]
    selected += [p for p in [RUN/'controller/B2_v4_recovery_acceptance_20261008.json',
                            RUN/'controller/B2_v4_final_acceptance_20261008.json'] if p.is_file()]
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



def publish_teacher_v8(entry="teacher_student_autopilot_v8"):
    """Explicit small code/config allowlist and aggregate metadata only."""
    assert entry in ('teacher_student_autopilot_v8','teacher_student_autopilot_v9','teacher_student_autopilot_v10','teacher_student_autopilot_v11')
    here=RUN/entry;version=entry.rsplit('_',1)[1]
    lock=json.loads((here/'source_lock.json').read_text());cpu=json.loads((here/'cpu_acceptance.json').read_text())
    registration=json.loads((here/'start_receipt.json').read_text())
    snapshot=json.loads((RUN/('controller/monitor_teacher_'+version+'/latest.json')).read_text())['snapshot']
    assert cpu['status']=='PASS_V8_CPU_STAGE_AND_CONTRACT_TESTS'
    assert snapshot['source_lock_sha256']==registration['source_lock_sha256']
    approved_json={'config.json','authorization.json','accepted_resume_manifest.json',
                   'teacher_metadata_20261007.json','teacher_response.schema.json'}
    if version=='v11':approved_json.remove('accepted_resume_manifest.json')
    selected=[p for p in here.rglob('*') if p.is_file()
        and not any(x in p.relative_to(here).parts for x in ('__pycache__','prelock_repairs','selection_01','pilot_selection'))
        and (p.suffix in ('.py','.cpp','.md') or p.name in approved_json
             or p.name in ('teacher_prompt.txt','review_prompt.txt'))]
    selected += [WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
    selected += [RUN/'controller'/n for n in ('V8_REPAIR_AND_EXECUTION_20261008.md',
        'V8_original_probe_handoff_reproduction_20261008.json','official_score_B2_LINUX_37_32_20261008.json',
        'register_autopilot_v8.py','checkpoint_teacher_v8.py','register_autopilot_v9.py','checkpoint_teacher_v9.py','inspect_autopilot_live.py',
        'publish_b2_snapshot.py','AUTONOMOUS_EXECUTION_20261008.md','autonomy_v9_registration_20261008.json','V9_visual_and_overlap_acceptance_20261008.json')]
    if version in ('v10','v11'):
        selected += [RUN/'controller'/n for n in ('register_autopilot_v10.py','checkpoint_teacher_v10.py',
            'record_teacher_v10_execution_20261008.py','V10_monitor_guard_repair_20261008.json',
            'autonomy_v10_registration_20261008.json','V10_ordered_boundary_independent_review_20261008.json',
            'P0_user_minimal_reproduction_20261008.json',
            'verify_teacher_v10_probe_20261008.py','V10_real_interface_probe_acceptance_20261008.json')]
    if version=='v11':
        selected += [RUN/'controller'/n for n in ('register_autopilot_v11.py','checkpoint_teacher_v11.py',
            'record_teacher_v11_execution_20261008.py','autonomy_v11_registration_20261008.json',
            'V11_cpu_repair_acceptance_20261008.json','V11_frozen_preflight_acceptance_20261008.json')]
        first_proof=RUN/'controller/V11_real_first_generation_acceptance_20261008.json'
        if first_proof.is_file():
            selected += [first_proof,RUN/'controller/verify_teacher_v11_first_generation_20261008.py']
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    aggregate={'status':'PASS_CPU_REPAIR_AND_ONCE_LINUX_LAUNCH_NOT_TEACHER_QUALITY',
        'snapshot_utc':snapshot['utc'],'entry':entry,'source_lock_sha256':snapshot['source_lock_sha256'],
        'bound_file_count':len(lock['files']),'cpu_tests':cpu['tests'],'cpu_test_count':json.loads((here/'ordered_boundary_cpu_acceptance.json').read_text())['total_contract_tests'] if version in ('v10','v11') else (64 if version=='v9' else 55),
        'new_selection_counts':{'train':128,'dev':32},'untouched_pilot_counts':{'train':16,'dev':8},
        'all_new_groups_exclude_old160_and_context':True,
        'stage':(snapshot.get('completion') or {}).get('status') or (snapshot.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU'),
        'owned_process_count':len(snapshot['processes']),'completion_status':(snapshot.get('completion') or {}).get('status'),'launch_utc':registration['utc'],
        'launch_historical_pid':registration['pid'],
        'new_T_optimizer_updates':(snapshot.get('student_progress') or {}).get('optimizer_steps',0),
        'teacher_visual_status':(snapshot['v8_stage_receipts'].get('visual_completion') or {}).get('status'),
        'synthetic_not_highlight_supervision':True,'same_teacher_review_not_human_truth':True,
        'B2_user_official_score':37.32,'B2_zip_sha256':'0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3',
        'prior_B_user_official_score':37.63,'new_candidate_official_score':None,
        'raw_labels_or_per_frame_data_exported':False,'models_videos_environment_or_new_zip_exported':False}
    if version in ('v9','v10','v11'):
        identity=json.loads((here/'v9_cache_identity_cpu_acceptance.json').read_text())
        assert identity['status']=='PASS_V9_ACTUAL_CACHE_IDENTITY_AND_BRIDGE_CPU'
        aggregate['additional_cache_identity_tests']=identity['new_contract_tests']
        bridge=json.loads((here/'real_cache_bridge_cpu_acceptance.json').read_text())
        assert bridge['status']=='PASS_ACTUAL_B2_COMPLETE_CACHE_BRIDGE_CPU'
        assert bridge['production_controller_sha256']==hashlib.sha256((here/'controller.py').read_bytes()).hexdigest()
        stopped=json.loads((RUN/'teacher_student_autopilot_v8/completion.json').read_text())
        assert stopped['status']=='STOP_AUTOPILOT_PRESERVED'
        aggregate['actual_B2_cache_bridge_CPU']={key:bridge[key] for key in (
            'status','original_actual_failure_reproduced','same_actual_B2_final_JSON_stage_key_used',
            'actual_cache_models_input_and_all_artifact_SHA_verified','GPU_started','old_data_changed')}
        aggregate['actual_B2_cache_bridge_CPU']['receipt_sha256']=hashlib.sha256((here/'real_cache_bridge_cpu_acceptance.json').read_bytes()).hexdigest()
        aggregate['v8_original_pre_GPU_STOP_preserved']=True
        aggregate['same_v8_unlabelled_selection_recipe_and_bytes']=True
    if version in ('v10','v11'):
        aggregate['preregistered_pilot_counts']=aggregate.pop('untouched_pilot_counts')
        ordered=json.loads((here/'ordered_boundary_cpu_acceptance.json').read_text())
        assert ordered['status']=='PASS_FIXED_RUNTIME_ORDERED_BOUNDARY_CPU' and ordered['old_raw_rejected'] is True
        aggregate['ordered_boundary_CPU']={key:ordered[key] for key in ('status','old_raw_rejected','GPU_started','total_contract_tests')}
        aggregate['ordered_boundary_CPU']['receipt_sha256']=hashlib.sha256((here/'ordered_boundary_cpu_acceptance.json').read_bytes()).hexdigest()
        aggregate['original_V9_invalid_probe_preserved']=True
        aggregate['same_preregistered_inputs_not_new_unseen_24']=True
    if version=='v10':
        proof=json.loads((RUN/'controller/V10_real_interface_probe_acceptance_20261008.json').read_text())
        aggregate['real_visual_and_heavy_acceptance']={key:proof[key] for key in (
            'status','real_visual_calls','real_fresh_non_test_probe_calls','max_real_prompt_tokens',
            'probe_original_validator_and_all_done_file_SHA_revalidated','raw_and_successful_records_unchanged',
            'semantic_quality_or_training_admitted_by_this_check','new_T_optimizer_updates')}
        if aggregate['completion_status']=='STOP_AUTOPILOT_PRESERVED':
            aggregate['status']='STOP_REAL_PILOT_EVIDENCE_ID_RELATION_PRESERVED'
            aggregate['actual_invalid_pilot_decisions']=1
            aggregate['original_failed_raw_not_salvaged']=True
    if version=='v11':
        evidence=json.loads((here/'evidence_boundary_cpu_acceptance.json').read_text())
        legacy=json.loads((here/'legacy_reuse_cpu_acceptance.json').read_text())
        assert evidence['status']=='PASS_FIXED_RUNTIME_BF_PER_SEGMENT_EVIDENCE_CPU'
        assert legacy['status']=='PASS_EXACT_V10_SUCCESS_REUSE_CPU'
        cost=json.loads((here/'legacy_cost_cpu_acceptance.json').read_text())
        assert cost['status']=='PASS_EXPLICIT_ORIGINAL_PROBE_COST_CPU' and cost['GPU_started'] is False
        aggregate['cpu_test_count']=evidence['total_contract_tests']+legacy['tests_run']+cost['tests_run']
        aggregate['original_probe_cost_handoff_CPU']={key:cost[key] for key in (
            'status','tests_run','GPU_started','old_bytes_changed')}
        aggregate['original_probe_cost_handoff_CPU']['receipt_sha256']=hashlib.sha256((here/'legacy_cost_cpu_acceptance.json').read_bytes()).hexdigest()
        aggregate['BF_witness_interface_CPU']={key:evidence[key] for key in (
            'status','GPU_started','old_raw_rejected','legacy_visual_requests_equal_actual_count')}
        aggregate['legacy_reuse_CPU']={'status':legacy['status'],'GPU_started':False,
            'exact_original_success_count':2,'accepted_manifest_sha256':hashlib.sha256((here/'accepted_resume_manifest.json').read_bytes()).hexdigest(),
            'full160_only_not_pilot24':True,'original_success_calls_not_repeated':True}
        aggregate['legacy_handoff']={key:value for key,value in (snapshot['v8_stage_receipts'].get('legacy_handoff') or {}).items()
            if key in ('status','fresh_model_calls','original_visual_calls','original_probe_calls','pilot_old_success_reuse_count','new_T_optimizer_updates')}
        actual=snapshot['v8_stage_receipts'].get('new_format_real_probe') or {}
        aggregate['actual_new_format_probe']={key:value for key,value in actual.items()
            if key in ('status','fresh_model_calls','old_success_model_calls','optimizer_steps','utc')}
        if first_proof.is_file():
            proof=json.loads(first_proof.read_bytes())
            assert proof['source_lock_sha256']==snapshot['source_lock_sha256'] and proof['independent_revalidation_model_calls']==0
            aggregate['actual_new_format_independent_CPU_replay']={key:proof[key] for key in (
                'status','actual_new_model_calls','original_success_new_calls','original_validator_and_canonical_record_byte_identity_pass',
                'complete_source_and_input_SHA_pass','physical_frame_SHA_pass','actual_label_status','actual_prompt_tokens',
                'actual_generation_wall_sec','new_T_optimizer_updates','semantic_quality_or_training_admitted')}
            aggregate['actual_new_format_independent_CPU_replay']['receipt_sha256']=hashlib.sha256(first_proof.read_bytes()).hexdigest()
        aggregate['original_V10_failed_evidence_raw_and_STOP_preserved']=True
    derived=PUB/REL/entry/'aggregate_repair_launch_acceptance.json'
    derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    derived_items=[derived]
    if version=='v9':
        history=PUB/REL/'teacher_student_autopilot_v8/aggregate_repair_launch_acceptance.json'
        assert history.is_file(), 'publish reviewed V8 code history before V9 snapshot'
        value=json.loads(history.read_text())
        value.update(status='STOP_PRE_GPU_B2_STAGE_KEY_HANDOFF_PRESERVED',stage='STOP_AUTOPILOT_PRESERVED',
            completion_status=stopped['status'],stop_utc=stopped['utc'],stop_error_type=stopped['error_type'],
            stop_reason=stopped['reason'],owned_process_count=0,new_T_optimizer_updates=0,
            actual_teacher_GPU_calls=0,actual_new_labels=0,stale_launch_snapshot_superseded=True,
            historical_STOP_kept_original_bytes=True)
        history.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        derived_items.append(history)
    if version=='v10':
        history=PUB/REL/'teacher_student_autopilot_v9/aggregate_repair_launch_acceptance.json'
        assert history.is_file()
        current=json.loads((RUN/'controller/monitor_teacher_v9/latest.json').read_text())['snapshot']
        value=json.loads(history.read_text())
        value.update(status='STOP_REAL_PROBE_OVERLAPPING_BOUNDARY_OUTPUT_PRESERVED', stage='STOP_AUTOPILOT_PRESERVED',
            completion_status=current['completion']['status'], stop_utc=current['completion']['utc'],
            stop_error_type=current['completion']['error_type'], stop_reason='unordered or overlapping native boundary segments',
            owned_process_count=0,new_T_optimizer_updates=0,teacher_visual_status='PASS_REAL_SYNTHETIC_VISUAL_INTERFACE',
            real_visual_cases=8,actual_invalid_probe_decisions=1,stale_launch_snapshot_superseded=True)
        history.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');derived_items.append(history)
    paragraph=('2026-10-08：用户截图指认已交付B2复赛成绩 **37.32 / DONE**，较原Linux B 37.63低0.31；两分各自绑定旧包。'
        '旧科学STOP保留。按用户提供审计另登记独立修复，已修真实probe→all缓存误拒绝、短边界ID与精确PTS映射、'
        '盲二次选择/全分母/UNKNOWN分离、新128/32与固定24、新2–4更新前缀与原B开发candidate0。'
        f'Linux{aggregate["cpu_test_count"]}项CPU验收和{len(lock["files"])}文件绑定通过，锁 `{snapshot["source_lock_sha256"]}`，单次launcher已登记。'
        'v8曾在B2缓存status/stage字段衔接处调用教师前STOP，GPU/标签/T更新均0；旧480文件和STOP保持。v9沿用同配方未标注选择原字节，修复实际回执适配与完整缓存身份绑定，并实际复现旧失败/验证两个scopeCPU桥接。' +
        ('v9真实视觉8/8通过，但首条非测试探针返回重叠区间，被原validator拒绝且保持STOP/T0。v10登记有限状态GBNF生成合法1..5非重叠原生边界，原prompt/validator/高光标准/16024输入不改，不合并裁段修补旧原答。' if version=='v10' else '') +
        ('V11修B/F独立编号与每段模型所选物理证据的生成约束；原V10真实8接口/2成功重输入回执仅核SHA与原validator引用，不当新调用；同24首个原失败窗真实验证新格式再继续，全部原失败与成功原字节保留。' if version=='v11' else '') +
        f'当前{version}接续逐条24标注/盲选择→科学分路A/B/C；启动/CPU不是32B质量或新训练通过。新T实际更新数 `{aggregate["new_T_optimizer_updates"]}`。'
        f'当前实际阶段 `{aggregate["stage"]}`。每15分钟静默巡检自动修复；最终真实完整验收后交付，官网新分未知。'
        f'见[修复与范围]({REL}/controller/V8_REPAIR_AND_EXECUTION_20261008.md)、[新协议]({REL}/{entry}/PROTOCOL.md)、'
        f'[聚合验收]({REL}/{entry}/aggregate_repair_launch_acceptance.json)。\n\n')
    def front(text,title,body):
        if '<!-- END_CURRENT_V8 -->' in text:
            _,rest=text.split('\n',1);rest=rest.split('<!-- END_CURRENT_V8 -->',1)[1]
            text=text.split('\n',1)[0]+'\n'+rest.lstrip('\n')
        first,rest=text.split('\n',1)
        return first+'\n\n'+title+'\n\n'+body+'<!-- END_CURRENT_V8 -->\n'+rest.lstrip('\n')
    edit(PUB/'README.md',lambda text:front(text,'## 当前教师修复与B2官网结果',paragraph))
    edit(PUB/'README.md',lambda text:'\n'.join(line.replace('| 未评分 |','| 37.32 |') if line.startswith('| 复赛 | B2：') else line for line in text.split('\n')))
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):
        edit(PUB/'docs'/name,lambda text:front(text,'## 当前教师独立修复',paragraph.replace(']('+REL,'](../'+REL)))
    for path in (PUB/'README.md',PUB/'docs/SOLUTIONS.md',PUB/'docs/REPRODUCTION.md'):
        edit(path,lambda text:text.replace('新B2官网分未知','B2用户回报官网37.32/DONE').replace('包仍留Linux，尚无新官网分。','B2已交付，用户回报37.32/DONE。'))
    manifest_path=PUB/'docs/publication_manifest.json';old_manifest=manifest_path.read_bytes();ending='\r\n' if b'\r\n' in old_manifest else '\n';manifest=json.loads(old_manifest)
    items={row['path']:row for row in manifest['files']}
    additions=[(path.relative_to(WORKSPACE).as_posix(),path.relative_to(WORKSPACE).as_posix()) for path in selected]
    additions.extend((path.relative_to(PUB).as_posix(),None) for path in derived_items)
    for relative,source in additions:
        if relative not in items:
            row=dict(path=relative,source_relative_path=source,bytes=0,sha256='',category='project_code_or_configuration' if relative.endswith('.py') else 'experiment_protocol_or_acceptance')
            manifest['files'].append(row);items[relative]=row
        if source is None:items[relative]['category']='aggregate_acceptance_no_frame_data'
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    manifest_path.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps({'status':'PASS_CURATED_TEACHER_CORE_AND_AGGREGATES','entry':entry,'selected_files':len(selected),
        'raw_labels_or_per_frame_data_exported':False,'models_videos_environment_or_new_zip_exported':False}))


def publish_teacher_v12():
    """Use the same curated core/aggregate publication workflow for exact resume."""
    entry='teacher_student_autopilot_v12';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_teacher_v12/latest.json').read_bytes())['snapshot']
    registration=json.loads((here/'start_receipt.json').read_bytes())
    cpu=json.loads((here/'resume_cpu_acceptance.json').read_bytes())
    assert cpu['status']=='PASS_V12_ACTUAL_SORTED_LEGACY_PROJECTION_AND_EXACT_RESUME_CPU'
    assert snapshot['source_lock_sha256']==registration['source_lock_sha256']
    selected=[p for p in here.rglob('*') if p.is_file()
        and not any(x in p.relative_to(here).parts for x in ('__pycache__','prelock_repairs','selection_01','pilot_selection'))
        and (p.suffix in ('.py','.cpp','.md') or p.name in ('config.json','authorization.json','teacher_prompt.txt','review_prompt.txt',
            'teacher_metadata_20261007.json','teacher_response.schema.json'))]
    selected += [RUN/'controller'/n for n in ('register_autopilot_v12.py','checkpoint_teacher_v12.py',
        'record_teacher_v12_execution_20261008.py','inspect_autopilot_live.py','publish_b2_snapshot.py',
        'V12_CANONICAL_HANDOFF_REPRODUCTION_20261008.json','V8_REPAIR_AND_EXECUTION_20261008.md','AUTONOMOUS_EXECUTION_20261008.md')]
    selected += [WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    stage=(snapshot.get('completion') or {}).get('status') or (snapshot.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU')
    parts=snapshot.get('v8_stage_receipts') or {};first=parts.get('first_review_generation') or {}
    aggregate=dict(status='PASS_EXACT_CPU_REPAIR_AND_SINGLE_LINUX_REVIEW_CONTINUATION_NOT_FINAL_QUALITY',
        snapshot_utc=snapshot['utc'],entry=entry,source_lock_sha256=snapshot['source_lock_sha256'],
        frozen_file_count=snapshot.get('source_lock_file_count'),launch_utc=registration['utc'],
        launch_historical_pid=registration['pid'],stage=stage,owned_process_count=len(snapshot['processes']),
        original_complete_labels=160,original_completed_reviews=28,remaining_registered_reviews=132,new_label_calls=0,
        actual_new_review_progress=parts.get('review_progress'),
        first_actual_review={k:first[k] for k in ('status','utc','fresh_review_model_calls','new_label_calls','old_success_repeated','new_T_optimizer_updates') if k in first},
        actual_original_records_CPU_checked=cpu['actual_original_records_checked'],actual_original_reviews_CPU_checked=cpu['completed_reviews_replayed'],
        actual_sorted_legacy_regressions=cpu['legacy_JSONL_regressions'],rejection_contracts=cpu['rejection_tests'],
        original_CPU_receipt_sha256=hashlib.sha256((here/'resume_cpu_acceptance.json').read_bytes()).hexdigest(),
        exact_resume_manifest_sha256=(snapshot.get('resume_manifest_summary') or {}).get('manifest_sha256'),
        all_original_receipt_SHA_pass=snapshot.get('all_original_resume_file_sha_pass'),original_V11_STOP_kept=True,
        original_V11_full_GPU_charged_seconds=6748.806357712485,original_full_label_fresh_calls=134,original_full_label_reused=26,
        new_T_optimizer_updates=(snapshot.get('student_progress') or {}).get('optimizer_steps',0),
        same_teacher_consistency_not_human_truth=True,new_official_score=None,
        B2_user_score=37.32,B2_zip_bytes=317401,B2_zip_sha256='0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3',
        prior_B_user_score=37.63,prior_B_zip_sha256='86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        raw_labels_or_per_frame_data_exported=False,models_videos_environment_or_new_zip_exported=False)
    derived=PUB/REL/entry/'aggregate_resume_acceptance.json';derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'V11已真实完整标注160/160（全量阶段新134、原SHA复用26），盲第二选择28条完成。'
        '全量复查在旧成功JSONL对象键排序导致canonical字符串SHA误拒绝处工程停止，原raw/标签/成功回执/STOP保持。'
        'V12独立修复投影的原始对象序列顺序，原160/28经过原validator及全部输入/物理帧SHA验收后引用；'
        '剩132独立盲选择，新label调用0，不重复成功生成，原GPU成本6748.806357712485秒保留。'
        f'当前实际阶段 `{stage}`，新T实际更新{aggregate["new_T_optimizer_updates"]}，没有新最终ZIP/新官网分。'
        'B2用户37.32/DONE与原B37.63各绑定各自包。CPU/启动/同教师一致性不是人工真值或新模型训练。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)与[聚合验收]({REL}/{entry}/aggregate_resume_acceptance.json)。\n\n')
    def front(text):
        if '<!-- END_CURRENT_V8 -->' in text:
            first,rest=text.split('\n',1);rest=rest.split('<!-- END_CURRENT_V8 -->',1)[1].lstrip('\n')
        else:first,rest=text.split('\n',1)
        return first+'\n\n## 当前教师工程修复与真实接续\n\n'+body+'<!-- END_CURRENT_V8 -->\n'+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):
        edit(PUB/'docs'/name,lambda text:front(text).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';original=mp.read_bytes();ending='\r\n' if b'\r\n' in original else '\n';manifest=json.loads(original)
    items={v['path']:v for v in manifest['files']}
    additions=[(p.relative_to(WORKSPACE).as_posix(),p.relative_to(WORKSPACE).as_posix()) for p in selected]
    additions.append((derived.relative_to(PUB).as_posix(),None))
    for relative,source in additions:
        if relative not in items:
            row=dict(path=relative,source_relative_path=source,bytes=0,sha256='',category='project_code_or_configuration' if relative.endswith('.py') else 'experiment_protocol_or_acceptance')
            manifest['files'].append(row);items[relative]=row
        if source is None:items[relative]['category']='aggregate_acceptance_no_frame_data'
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_V12_CORE_AND_AGGREGATE_ONLY',selected_files=len(selected),new_ZIP_or_labels_or_frames_exported=False)))


def publish_teacher_v13():
    """Use the same curated core/aggregate publication workflow for exact resume."""
    entry='teacher_student_autopilot_v13';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_teacher_v13/latest.json').read_bytes())['snapshot']
    registration=json.loads((here/'start_receipt.json').read_bytes())
    cpu=json.loads((here/'resume_cpu_acceptance.json').read_bytes())
    assert cpu['status']=='PASS_V13_ACTUAL_SORTED_LEGACY_PROJECTION_AND_EXACT_RESUME_CPU'
    assert snapshot['source_lock_sha256']==registration['source_lock_sha256']
    selected=[p for p in here.rglob('*') if p.is_file()
        and not any(x in p.relative_to(here).parts for x in ('__pycache__','prelock_repairs','selection_01','pilot_selection'))
        and (p.suffix in ('.py','.cpp','.md') or p.name in ('config.json','authorization.json','teacher_prompt.txt','review_prompt.txt',
            'teacher_metadata_20261007.json','teacher_response.schema.json'))]
    selected += [RUN/'controller'/n for n in ('register_autopilot_v13.py','checkpoint_teacher_v13.py',
        'record_teacher_v13_execution_20261008.py','inspect_autopilot_live.py','publish_b2_snapshot.py',
        'V12_CANONICAL_HANDOFF_REPRODUCTION_20261008.json','V13_MISSING_VALIDATOR_DEPENDENCY_REPRODUCTION_20261008.json','V13_frozen_preflight_acceptance_20261008.json','V8_REPAIR_AND_EXECUTION_20261008.md','AUTONOMOUS_EXECUTION_20261008.md')]
    first_proof=RUN/'controller/V13_real_first_review_acceptance_20261008.json'
    if first_proof.exists():selected += [RUN/'controller/verify_teacher_v13_first_review_20261008.py']
    selected += [WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    stage=(snapshot.get('completion') or {}).get('status') or (snapshot.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU')
    parts=snapshot.get('v8_stage_receipts') or {};first=parts.get('first_review_generation') or {}
    aggregate=dict(status='PASS_EXACT_CPU_REPAIR_AND_SINGLE_LINUX_REVIEW_CONTINUATION_NOT_FINAL_QUALITY',
        snapshot_utc=snapshot['utc'],entry=entry,source_lock_sha256=snapshot['source_lock_sha256'],
        frozen_file_count=snapshot.get('source_lock_file_count'),launch_utc=registration['utc'],
        launch_historical_pid=registration['pid'],stage=stage,owned_process_count=len(snapshot['processes']),
        original_complete_labels=160,original_completed_reviews=28,remaining_registered_reviews=132,new_label_calls=0,
        actual_new_review_progress=parts.get('review_progress'),
        first_actual_review={k:first[k] for k in ('status','utc','fresh_review_model_calls','new_label_calls','old_success_repeated','new_T_optimizer_updates') if k in first},
        actual_original_records_CPU_checked=cpu['actual_original_records_checked'],actual_original_reviews_CPU_checked=cpu['completed_reviews_replayed'],
        actual_current_full_blind_validator_CPU_replayed=cpu['actual_current_blind_validator_replayed'],
        exact_original_dependencies=cpu['exact_original_dependency_files'],original_V12_pre_GPU_STOP_kept=True,
        actual_sorted_legacy_regressions=cpu['legacy_JSONL_regressions'],rejection_contracts=cpu['rejection_tests'],
        original_CPU_receipt_sha256=hashlib.sha256((here/'resume_cpu_acceptance.json').read_bytes()).hexdigest(),
        exact_resume_manifest_sha256=(snapshot.get('resume_manifest_summary') or {}).get('manifest_sha256'),
        all_original_receipt_SHA_pass=snapshot.get('all_original_resume_file_sha_pass'),original_V11_STOP_kept=True,
        original_V11_full_GPU_charged_seconds=6748.806357712485,original_full_label_fresh_calls=134,original_full_label_reused=26,
        new_T_optimizer_updates=(snapshot.get('student_progress') or {}).get('optimizer_steps',0),
        same_teacher_consistency_not_human_truth=True,new_official_score=None,
        B2_user_score=37.32,B2_zip_bytes=317401,B2_zip_sha256='0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3',
        prior_B_user_score=37.63,prior_B_zip_sha256='86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        raw_labels_or_per_frame_data_exported=False,models_videos_environment_or_new_zip_exported=False)
    if first_proof.exists():
        actual=json.loads(first_proof.read_bytes())
        public_keys=('status','utc','source_lock_sha256','actual_new_review_model_calls','new_label_model_calls',
            'old_success_generation_repeated','independent_CPU_revalidation_model_calls',
            'original_validator_and_input_and_raw_SHA_pass','physical_frame_and_native_clock_SHA_pass',
            'actual_HTTP_request_processor_applied_grammar_and_response_SHA_pass',
            'actual_review_HTTP_wall_seconds','actual_teacher_weight_and_runtime_identity_pass',
            'original_label_record_unchanged','actual_prompt_tokens','new_T_optimizer_updates',
            'semantic_training_admitted','same_teacher_comparison_not_human_truth')
        aggregate['independent_first_real_review_acceptance']={k:actual[k] for k in public_keys}
        aggregate['independent_first_real_review_acceptance']['private_receipt_sha256']=hashlib.sha256(first_proof.read_bytes()).hexdigest()
    derived=PUB/REL/entry/'aggregate_resume_acceptance.json';derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'V11已真实完整标注160/160（全量阶段新134、原SHA复用26），盲第二选择28条完成。'
        '全量复查在旧成功JSONL对象键排序导致canonical字符串SHA误拒绝处工程停止，原raw/标签/成功回执/STOP保持。'
        'V12修复投影的原始对象序列顺序，随后因部署漏原validator metadata在GPU前自然STOP，所有原失败保持。V13补齐原metadata/schema字节并CPU执行完整28条当前blind validator，原160/28经过原validator及全部输入/物理帧SHA验收后引用；'
        '剩132独立盲选择，新label调用0，不重复成功生成，原GPU成本6748.806357712485秒保留。'
        f'当前实际阶段 `{stage}`，新T实际更新{aggregate["new_T_optimizer_updates"]}，没有新最终ZIP/新官网分。'
        'B2用户37.32/DONE与原B37.63各绑定各自包。CPU/启动/同教师一致性不是人工真值或新模型训练。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)与[聚合验收]({REL}/{entry}/aggregate_resume_acceptance.json)。\n\n')
    def front(text):
        if '<!-- END_CURRENT_V8 -->' in text:
            first,rest=text.split('\n',1);rest=rest.split('<!-- END_CURRENT_V8 -->',1)[1].lstrip('\n')
        else:first,rest=text.split('\n',1)
        return first+'\n\n## 当前教师工程修复与真实接续\n\n'+body+'<!-- END_CURRENT_V8 -->\n'+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):
        edit(PUB/'docs'/name,lambda text:front(text).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';original=mp.read_bytes();ending='\r\n' if b'\r\n' in original else '\n';manifest=json.loads(original)
    items={v['path']:v for v in manifest['files']}
    additions=[(p.relative_to(WORKSPACE).as_posix(),p.relative_to(WORKSPACE).as_posix()) for p in selected]
    additions.append((derived.relative_to(PUB).as_posix(),None))
    for relative,source in additions:
        if relative not in items:
            row=dict(path=relative,source_relative_path=source,bytes=0,sha256='',category='project_code_or_configuration' if relative.endswith('.py') else 'experiment_protocol_or_acceptance')
            manifest['files'].append(row);items[relative]=row
        if source is None:items[relative]['category']='aggregate_acceptance_no_frame_data'
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_V13_CORE_AND_AGGREGATE_ONLY',selected_files=len(selected),new_ZIP_or_labels_or_frames_exported=False)))


def publish_teacher_v14():
    entry='teacher_student_autopilot_v14';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_teacher_v14/latest.json').read_bytes())['snapshot']
    finalpath=RUN/'controller/V14_final_acceptance_20261008.json'
    final=json.loads(finalpath.read_bytes()) if finalpath.exists() else None
    if final:
        assert final['status']=='PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING'
        assert final['source_lock_sha256']==snapshot['source_lock_sha256']
        assert (snapshot.get('completion') or {}).get('status')==final['completion_status']
        assert all(all(scope['strict_checks'].values()) for scope in final['scopes'].values())
        assert hashlib.sha256((RUN/'controller/verify_v14_final_20261008.py').read_bytes()).hexdigest()==final['verifier_source_sha256']
    cpu=json.loads((here/'full_resume_cpu_acceptance.json').read_bytes())
    assert cpu['status']=='PASS_V14_EXACT_PILOT_DIAGNOSTIC_STAGE_HANDOFF_CPU' and cpu['rejection_tests']>=11
    allowed=lambda p:p.suffix=='.py' or p.name in ('config.json','authorization.json','PROTOCOL.md','CONTINUE.md','teacher_prompt.txt','review_prompt.txt','runtime_schema_check.cpp')
    selected=[p for p in here.iterdir() if p.is_file() and allowed(p)]
    selected += [p for p in (here/'precision_helpers').glob('*.py')]
    selected += [here/'supervision'/n for n in ('select_windows.py','validate_teacher.py','teacher_metadata_20261007.json','teacher_response.schema.json')]
    selected += [RUN/'controller'/n for n in ('register_autopilot_v14.py','checkpoint_teacher_v14.py',
        'record_teacher_v14_execution_20261008.py','verify_teacher_v13_full_review_20261008.py',
        'inspect_autopilot_live.py','publish_b2_snapshot.py','V14_DIAGNOSTIC_STAGE_REPRODUCTION_20261008.json',
        'V8_REPAIR_AND_EXECUTION_20261008.md','AUTONOMOUS_EXECUTION_20261008.md')]
    selected += [WORKSPACE/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
    if final:selected += [RUN/'controller/verify_v14_final_20261008.py']
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    fullproof=RUN/'controller/V13_real_full_review_acceptance_20261008.json'
    actual=json.loads(fullproof.read_bytes())
    stage=(snapshot.get('completion') or {}).get('status') or (snapshot.get('progress') or {}).get('stage')
    if stage is None and snapshot.get('processes') and not snapshot.get('registration'):
        stage='SOURCE_PREFLIGHT_CPU_PENDING_REGISTRATION'
    aggregate=dict(status=('ACTUAL_V14_FINAL_ZIP_INDEPENDENTLY_ACCEPTED_ORIGINAL_B_SELECTED' if final else
        'ACTUAL_V14_EXACT_STAGE_HANDOFF_AND_STUDENT_CONTINUATION_NOT_FINAL_ZIP'),
        snapshot_utc=snapshot['utc'],entry=entry,stage=stage,source_lock_sha256=snapshot['source_lock_sha256'],
        frozen_file_count=snapshot['source_lock_file_count'],original_labels=160,original_reviews=160,
        original_pilot_diagnostic_flags_preserved=24,actual_new_teacher_calls=0,
        supported_by_split=cpu['supported_by_split'],supported_positive_by_split=cpu['supported_positive_by_split'],
        supported_empty_by_split=cpu['supported_empty_by_split'],unknown_count=81,UNKNOWN_never_negative=True,
        old_consumer_actual_failure_reproduced=True,exact_foreign_or_changed_rejection_contracts=cpu['rejection_tests'],
        same_teacher_consistency_is_weak_not_truth=True,
        independent_full_teacher_receipt_sha256=hashlib.sha256(fullproof.read_bytes()).hexdigest(),
        independent_full_teacher_engineering={k:actual[k] for k in ('full_selected_denominator',
            'actual_fresh_review_model_calls','engineering_failure_count','all_actual_HTTP_processor_grammar_raw_pass',
            'original_validator_and_exact_native_projection_pass','physical_PNG_and_RGB_SHA_pass',
            'physical_frames_checked','actual_GPU_charged_seconds','actual_wrapper_status','exit_code','stop_reason','independent_CPU_model_calls')},
        complete_teacher_manifest=(snapshot.get('complete_teacher_manifest_summary') or {}),
        all_original_receipt_SHA_pass=snapshot.get('all_original_resume_file_sha_pass'),
        all_complete_teacher_review_file_SHA_pass=snapshot.get('all_complete_teacher_review_file_SHA_pass'),
        actual_runtime_complete_teacher_handoff=snapshot.get('full_resume_handoff'),
        independent_runtime_handoff_receipt_sha256=hashlib.sha256((RUN/'controller/V14_real_handoff_acceptance_20261008.json').read_bytes()).hexdigest()
            if (RUN/'controller/V14_real_handoff_acceptance_20261008.json').exists() else None,
        actual_new_T_optimizer_updates=(snapshot.get('student_progress') or {}).get('optimizer_steps',0),
        final_ZIP_complete=bool(final),new_official_score=None,B2_user_official_score=37.32,original_B_official_score=37.63,
        B2_ZIP_sha256='0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3',
        original_B_ZIP_sha256='86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        new_ZIP_raw_labels_and_per_frame_data_exported=False)
    finalderived=None
    if final:
        aggregate.update(independent_final_acceptance_sha256=hashlib.sha256(finalpath.read_bytes()).hexdigest(),
            final_candidate=final['scopes']['rematch'],
            actual_training={'epochs':final['epochs_completed'],'optimizer_updates':final['actual_T_optimizer_updates'],
                'backward_examples':final['actual_backward_examples'],'prefix_updates':final['prefix_updates'],
                'original_independent_CPU_288_adapter_reload_pass':final['independent_CPU_reload_was_288_adapter_PASS']},
            selected_epoch=final['selected_epoch'],selected_original_B=final['selected_original_B'],
            trained_candidate_selected=final['trained_candidate_selected'],selected_adapter_sha256=final['selected_adapter_sha256'],
            weak_dev_candidates=final['weak_dev_candidates'],new_T_improvement_claim=False,
            resources=final['resources'])
        finalderived=PUB/REL/entry/'aggregate_final_acceptance.json'
        finalderived.write_bytes(finalpath.read_bytes())
    derived=PUB/REL/entry/'aggregate_stage_handoff_acceptance.json'
    derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=('32B教师完整160标签与160盲第二选择已真实完成，132新复查、28原成功精确复用，工程失败0。'
        '弱支持正65、空14、UNKNOWN81；实际支持65train/14dev，全部160分母与原raw保持，同教师一致性不是人工真值。'
        'V13学生CPU准入错误拒绝原pilot24的diagnostic标记。V14在独立exact manifest下仅允许原pilot24精确成功回执跨阶段，原标记/STOP/成本不改；'
        '旧consumer失败、新完整160 consumer与11拒绝合同已真实CPU验收，不重复教师生成。'
        f'实际快照{snapshot["utc"]}阶段 `{stage}`，新8B T实际更新{aggregate["actual_new_T_optimizer_updates"]}，没有新最终ZIP，新官网分未知。'
        '原B37.63与B2用户37.32/DONE继续绑定各自旧ZIP。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)与[聚合验收]({REL}/{entry}/aggregate_stage_handoff_acceptance.json)。\n\n')
    if final:
        candidate=final['scopes']['rematch']
        body=('32B教师推理完整160标签与160盲第二选择、真实8B微调及最终Linux ZIP均已完成独立验收。'
            '教师未微调32B；同教师一致性为弱监督，支持65train/14dev，UNKNOWN81与原160分母保留。'
            '修复了证据/边界编号、生成约束及probe/all/review、canonical键顺序、validator metadata、pilot diagnostic精确阶段移交。'
            '8B学生完成3epochs、15次真实optimizer更新、195次样本反向；4更新前缀、288adapter独立CPU重载与冻结基座通过。'
            '弱14dev的原B与epoch1同分，epoch2/3较低，按登记规则选择epoch0原B；新权重未胜出，不宣称新T提高。'
            'NONTEST8与426复赛各11项独立strict全true，完整426源/521时间窗/无效0、102470预测帧，ZIP CRC/唯一JSONL/身份/原字节通过。'
            '时间为本次真实生成，空间精确复用原B2完整源场，本候选新空间模型调用0、原成本保留。'
            f'最终Linux包：`{candidate["candidate"]}`，实际{candidate["zip_bytes"]}字节，SHA256 `{candidate["zip_sha256"]}`。'
            '包未自动回传或提交官网，新官网分未知。原B37.63绑定旧包SHA `86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`；'
            'B2用户37.32/DONE绑定317401字节旧包SHA `0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3`。'
            f'见[协议]({REL}/{entry}/PROTOCOL.md)与[最终聚合验收]({REL}/{entry}/aggregate_final_acceptance.json)。\n\n')
    def front(text):
        first,rest=text.split('\n',1)
        if '<!-- END_CURRENT_V8 -->' in rest:rest=rest.split('<!-- END_CURRENT_V8 -->',1)[1].lstrip('\n')
        if final:
            rest=rest.replace('## 当前自主B2接续','## 已交付B2历史')
            rest=rest.replace('## 当前B2复现范围','## 已交付B2历史复现范围')
            rest=rest.replace('## 下一轮代码修复与自主执行（2026-10-08）','## B2与前期教师诊断历史（2026-10-08上午）')
            rest=rest.replace('## 下一轮Z/T/S（2026-10-07）','## Z/T/S计划历史（2026-10-07）')
            rest=rest.replace('2026-10-08 09:45 UTC+8：当前路线','2026-10-08 09:45 UTC+8历史：当时路线')
            note='以下B2、context v3与Z/T/S段落保留对应日期的历史状态；当前V14训练和最终ZIP以上方终态验收为准。\n\n'
            if not rest.startswith(note):rest=note+rest
        return first+'\n\n## '+('当前最终交付与真实选点' if final else '当前教师工程修复与真实接续')+'\n\n'+body+'<!-- END_CURRENT_V8 -->\n'+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):
        edit(PUB/'docs'/name,lambda text:front(text).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';original=mp.read_bytes();ending='\r\n' if b'\r\n' in original else '\n';manifest=json.loads(original)
    items={v['path']:v for v in manifest['files']}
    additions=[(p.relative_to(WORKSPACE).as_posix(),p.relative_to(WORKSPACE).as_posix()) for p in selected]
    additions.append((derived.relative_to(PUB).as_posix(),None))
    if finalderived:additions.append((finalderived.relative_to(PUB).as_posix(),None))
    for relative,source in additions:
        if relative not in items:
            row=dict(path=relative,source_relative_path=source,bytes=0,sha256='',category='project_code_or_configuration' if relative.endswith('.py') else 'experiment_protocol_or_acceptance')
            manifest['files'].append(row);items[relative]=row
        if source is None:items[relative]['category']='aggregate_acceptance_no_frame_data'
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_V14_CORE_AND_AGGREGATE_ONLY',selected_files=len(selected),new_ZIP_or_labels_or_frames_exported=False)))


def publish_context_advisory_v1():
    entry='context_advisory_v1'; here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_context_advisory_v1/latest.json').read_bytes())
    lock=json.loads((here/'source_lock.json').read_bytes())
    assert hashlib.sha256((here/'source_lock.json').read_bytes()).hexdigest()==snapshot['source_lock_sha256']
    selected=[p for p in here.iterdir() if p.is_file() and (p.suffix=='.py' or p.name in ('PROTOCOL.md','CONTINUE.md','DEVELOPMENT_EVIDENCE.md'))]
    selected += [RUN/'controller'/n for n in ('register_context_advisory_v1.py','checkpoint_context_advisory_v1.py',
        'inspect_context_advisory_v1.py','record_context_advisory_execution_20261009.py','accept_context_advisory_first_real.py',
        'accept_context_advisory_pilot.py',
        'CONTEXT_ADVISORY_EXECUTION_20261009.md','publish_b2_snapshot.py')]
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    cpu=json.loads((here/'draft_preflight.json').read_bytes())
    assert cpu['status']=='PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS' and len(cpu['non_test_proofs'])==8
    completion=snapshot['stages'].get('completion.json')
    aggregate={'status':'CURATED_CONTEXT_ADVISORY_ACTUAL_ENGINEERING_AND_PROGRESS_NOT_QUALITY',
        'snapshot_utc':snapshot['utc'],'entry':entry,'source_lock_sha256':snapshot['source_lock_sha256'], 'frozen_files':len(lock['files']),
        'actual_CPU':{k:cpu[k] for k in ('status','valid_boundary_pairs','explicit_invalid_cases','tokenizer_candidate_count','tokenizer_ascii_contexts')},
        'actual_CPU_nontest_sources':8,'processor_tensor_equal_all_five_arms':True,'B0_all_tensors_equal_actual_V14':True,
        'done_count':snapshot['done_count'],'failure_count':len(snapshot['failures']),'done_bound_SHA_pass':snapshot['all_done_bound_SHA_pass'],
        'current_stage':(snapshot['stages'].get('progress.json') or {}).get('stage','SOURCE_IDENTITY_CPU_PENDING_STAGE'),
        'actual_new_training_updates':0,'actual_new_32B_calls':0,'models':'EXISTING_8B_BASE_OVERVIEW_ORIGINAL_B_LOCAL_ADAPTER',
        'logical_parameters':8782459120,'developer_files':104,'source_groups':96,'developer_local_windows':112,
        'Pro_persistent_used':3,'new_Pro_calls':0,'Gemini_effective_responses':0,'actual_ordinary_rounds':2,
        'final_metadata_MD_sha256':'586d95e6a92c4b17008d9c60c6d30aeff0fe69f51ecb5eb082af3f8221875765',
        'decision_source':'MAIN_CONTROLLER_BUDGET_EXHAUSTED_FALLBACK_NOT_PRO_OR_MAJORITY_TRUTH',
        'new_final_ZIP_complete':bool(completion),'completion':completion,'new_official_score':None,
        'original_B_official_score':37.63,'original_B_ZIP_sha256':'86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        'V14_user_delta':-.03,'V14_score_inferred_not_independently_read':37.60,'V14_ZIP_sha256':'95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2',
        'B2_user_official_score':37.32,'B2_ZIP_sha256':'0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3',
        'teacher_reference_coverage_complete':'UNKNOWN','semantic_quality_or_hallucination_rate':'UNKNOWN',
        'raw_frames_labels_weights_new_ZIP_exported':False}
    aggregate['done_by_kind']=snapshot.get('done_by_kind',{})
    aggregate['local_done_by_arm']=snapshot.get('local_done_by_arm',{})
    proof_path=RUN/'controller/C_ADVISORY_first_real_acceptance_20261009.json'
    if proof_path.exists():
        proof=json.loads(proof_path.read_bytes())
        assert proof['status']=='PASS_INDEPENDENT_FIRST_REAL_C_ADVISORY_CPU_REPLAY' and proof['source_lock_sha256']==snapshot['source_lock_sha256']
        assert proof['new_acceptance_model_calls']==proof['new_acceptance_optimizer_updates']==0
        aggregate['first_real_CPU_replay']={k:proof[k] for k in ('status','utc','all_frozen_files_SHA','new_acceptance_model_calls',
            'new_acceptance_optimizer_updates','actual_NONTEST_GPU_charge_seconds','ledger_unique_terminal_match','not_semantic_truth_or_official_score')}
        aggregate['first_real_CPU_replay']['private_receipt_sha256']=hashlib.sha256(proof_path.read_bytes()).hexdigest()
    pilot_proof_path=RUN/'controller/C_ADVISORY_pilot_acceptance_20261009.json'
    if pilot_proof_path.exists():
        pilot_proof=json.loads(pilot_proof_path.read_bytes())
        assert pilot_proof['status']=='PASS_INDEPENDENT_COMPLETE_PILOT_CPU_NATIVE_PROCESSOR_REPLAY'
        assert pilot_proof['source_lock_sha256']==snapshot['source_lock_sha256']
        assert pilot_proof['new_acceptance_model_calls']==pilot_proof['new_acceptance_optimizer_updates']==0
        aggregate['complete_pilot_CPU_replay']={k:pilot_proof[k] for k in ('status','utc','all_frozen_files_SHA',
            'pilot_videos','pilot_source_groups','native_local_windows','original_new_overview_calls','original_new_local_calls',
            'overview_event_counts','all_original_requests_raw_output_tokens_native_RGB_processor_validator_equal',
            'R_N_changed_native_sets','R_X_changed_native_sets','actual_GPU_charge_seconds','ledger_unique_terminal_match',
            'new_acceptance_model_calls','new_acceptance_optimizer_updates','not_semantic_truth_or_official_score',
            'full104_investment_rule_still_required')}
        aggregate['complete_pilot_CPU_replay']['private_receipt_sha256']=hashlib.sha256(pilot_proof_path.read_bytes()).hexdigest()
    aggregate['resources']={name:{k:r['resource'][k] for k in ('status','exit_code','stop_reason','charged_seconds','started_utc','finished_utc') if k in r['resource']}
        for name,r in snapshot['resources'].items() if r.get('resource')}
    for name in ('nontest_01/independent_validation.json','nontest_01/nontest.report.json','developer_01/pilot.report.json','developer_01/full.report.json'):
        value=snapshot['stages'].get(name)
        if value:aggregate[name]={k:value[k] for k in ('status','records','source_groups','checks','issues',
            'R_N_changed_native_sets','R_X_changed_native_sets','weak_reference_used','comparisons',
            'R_N_all_native_selected_sets_identical','material_negative_investment_rule','nonnegative_registered_four_direction_rule') if k in value}
    derived=PUB/REL/entry/'aggregate_execution.json'
    derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'\n## 新探索C-advisory（实际快照{snapshot["utc"]}）\n\n'
        '同既有8B全源粗览＋原B局部全部自然窗，先NONTEST8五臂、固定24五臂，再完整104/96四臂对照；只有固定投入规则准入才一个探索ZIP。'
        '旧最佳B37.63保护。用户V14少0.03，37.60为差值推算，非独立官网读数。新分未知，原V14训练15更新但选原B事实保留。'
        'Tibo/Sol/Grok两轮实际讨论与最终完整卷宗同步；Pro研究项目连续额度3次已用，新0，Gemini无有效答复，主控独立兜底不冒充共识。'
        f'当前阶段`{aggregate["current_stage"]}`、粗览/局部完成{aggregate["done_by_kind"]}、失败{len(snapshot["failures"])}；实际模型回执与独立CPU回放分别计，CPU验收和启动不当新生成。'
        '闭世界教师一致性仅投入排序，真实质量/幻觉率未知，不保证超过最佳。'
        f'见[固定协议]({REL}/{entry}/PROTOCOL.md)和[筛选聚合]({REL}/{entry}/aggregate_execution.json)。\n\n<!-- END_CURRENT_C_ADVISORY -->\n')
    def front(text):
        first,rest=text.split('\n',1)
        if '<!-- END_CURRENT_C_ADVISORY -->' in rest:rest=rest.split('<!-- END_CURRENT_C_ADVISORY -->',1)[1]
        rest=rest.replace('## 当前最终交付与真实选点','## V14历史交付与真实选点')
        return first+'\n'+body+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):edit(PUB/'docs'/name,lambda t:front(t).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';original=mp.read_bytes();ending='\r\n' if b'\r\n' in original else '\n';manifest=json.loads(original)
    rows={x['path']:x for x in manifest['files']}
    for path in selected+[derived]:
        is_derived=path==derived;relative=path.relative_to(PUB if is_derived else WORKSPACE).as_posix()
        if relative not in rows:
            row=dict(path=relative,source_relative_path=None if is_derived else relative,bytes=0,sha256='',
                category='aggregate_acceptance_no_frame_data' if is_derived else ('project_code_or_configuration' if path.suffix=='.py' else 'experiment_protocol_or_acceptance'))
            manifest['files'].append(row);rows[relative]=row
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps({'status':'PASS_CURATED_C_ADVISORY_CORE_AND_AGGREGATE','selected_files':len(selected),'new_ZIP_frames_raw_labels_models_exported':False}))


def publish_boundary_diagnostic_v1():
    """Export code and explicit aggregate fields; never export context/reference rows."""
    publish_context_advisory_v1()
    entry='b_boundary_diagnostic_v1';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_b_boundary_diagnostic_v1/latest.json').read_bytes())
    lock=json.loads((here/'source_lock.json').read_bytes())
    assert snapshot['entry']==entry
    assert hashlib.sha256((here/'source_lock.json').read_bytes()).hexdigest()==snapshot['source_lock_sha256']
    selected=[here/n for n in ('bdiag_common.py','bdiag_engine.py','prepare.py','cpu_checks.py','freeze.py',
        'report.py','controller.py','launch.py','CONTINUE.md','PROTOCOL.md')]
    selected += [RUN/'controller'/n for n in ('register_b_boundary_diagnostic_v1.py',
        'checkpoint_b_boundary_diagnostic_v1.py','inspect_b_boundary_diagnostic_v1.py',
        'record_b_boundary_execution_20261009.py','B_BOUNDARY_EXECUTION_20261009.md','publish_b2_snapshot.py')]
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    cpu=json.loads((here/'cpu_acceptance.json').read_bytes())
    assert cpu['status']=='PASS_EXACT_C_STOP_AND_B_MATCHED_NATIVE_CPU_INTERFACES'
    aggregate={'status':'CURATED_MATCHED_BOUNDARY_ENGINEERING_NOT_TRUTH_TRAINING_OR_FINAL_ZIP',
        'snapshot_utc':snapshot['utc'],'entry':entry,'source_lock_sha256':snapshot['source_lock_sha256'],
        'frozen_files':len(lock['files']),'current_stage':(snapshot['stages'].get('progress.json') or {}).get('stage'),
        'actual_successful_32B_context_calls':snapshot['done_count'],'failure_count':len(snapshot['failures']),
        'all_done_bound_SHA_pass':snapshot['all_done_bound_SHA_pass'],
        'all_done_teacher_recipe_SHA_match':snapshot['all_done_teacher_recipe_SHA_match'],
        'teacher_recipe_sha256':snapshot['actual_teacher_recipe_sha256'],
        'model':'EXISTING_QWEN3_VL_32B_Q4_K_M_WITH_F16_PROJECTOR_INFERENCE',
        'teacher_context_length':65536,'actual_new_8B_calls':0,'actual_new_optimizer_updates':0,
        'teacher_finetuned':False,'training_admitted':False,'new_final_426_ZIP_complete':False,
        'new_official_score':None,'same_event_semantic_identity':'UNKNOWN',
        'independent_human_boundary_truth':'UNKNOWN','external_reference_coverage':'UNKNOWN',
        'endpoint_stability_is_truth':False,'context_reference_raw_frames_labels_weights_exported':False,
        'actual_CPU':{k:cpu[k] for k in ('status','utc','C_full_original_frozen_files','C_full_source_files',
            'C_full_groups','C_original_local_windows','C_full_actual_GPU_charge_seconds',
            'C_all_raw_validator_native_rows_and_frozen_rule_equal','C_report_sha256','C_original_STOP_preserved',
            'fixed_B_events','fixed_context_variants','actual_pinned_runtime_grammar_cases',
            'new_32B_calls','new_8B_calls','optimizer_updates','training_admitted')},
        'private_CPU_receipt_sha256':hashlib.sha256((here/'cpu_acceptance.json').read_bytes()).hexdigest()}
    first=snapshot['stages'].get('first_real_acceptance.json')
    if first:
        first_path=here/'first_real_acceptance.json'
        assert json.loads(first_path.read_bytes())==first
        assert first['status']=='PASS_REAL_FIRST_MATCHED_CONTEXTS_AND_INDEPENDENT_CPU_REPLAY'
        assert all(row['source_native_PNG_RGB_HTTP_prompt_raw_validator_equal'] is True for row in first['proofs'])
        aggregate['first_real_acceptance']={k:first[k] for k in ('status','utc','event_denominator','context_denominator',
            'actual_new_32B_calls','CPU_replay_new_model_calls','optimizer_updates','semantic_identity_and_boundary_truth')}
        aggregate['first_real_acceptance']['private_receipt_sha256']=hashlib.sha256(first_path.read_bytes()).hexdigest()
        aggregate['first_real_acceptance']['all_physical_request_raw_validator_replays_equal']=True
    aggregate['resources']={name:{k:value['resource'][k] for k in ('status','exit_code','stop_reason',
        'charged_seconds','started_utc','finished_utc') if k in value['resource']}
        for name,value in snapshot['resources'].items() if value.get('resource')}
    upstream=snapshot['upstream_C']
    aggregate['original_C_terminal']={k:upstream['report'][k] for k in ('status','records','source_groups',
        'comparisons','R_N_all_native_selected_sets_identical','material_negative_investment_rule',
        'nonnegative_registered_four_direction_rule') if k in upstream['report']}
    aggregate['original_C_STOP_preserved']=True
    terminal=snapshot['stages'].get('diagnostic_completion.json')
    if terminal:
        actual=json.loads((here/'diagnostic_completion.json').read_bytes())
        assert actual==terminal and actual['status']=='PASS_REAL_MATCHED_32B_BOUNDARY_DIAGNOSTIC_AND_CPU_ACCOUNTING'
        keys=('status','utc','events','context_attempts','engineering_failures',
            'all_contexts_unique_temporal_overlap_events','spread_within_original_sample_gap_events',
            'independent_weak_direction_events','external_weak_event_macro_delta',
            'reference_coverage_and_semantic_truth','stability_is_not_boundary_truth','training_admitted',
            'new_optimizer_updates','new_8B_calls','actual_new_32B_calls','actual_GPU_charge_seconds',
            'new_CPU_acceptance_model_calls','ledger_unique_terminal_match','ledger_historical_offset','no_final_426_ZIP')
        aggregate['complete_diagnostic']={k:actual[k] for k in keys}
        aggregate['complete_diagnostic']['private_receipt_sha256']=hashlib.sha256((here/'diagnostic_completion.json').read_bytes()).hexdigest()
    derived=PUB/REL/entry/'aggregate_execution.json'
    derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'\n## 当前边界诊断（实际快照{snapshot["utc"]}）\n\n'
        'C-advisory完整104/96组已自然完成，新增72组R−N为−0.000582455299541034，固定投入门拒绝C生产；原STOP与成功回答保持，无C426包。'
        '主控已实现独立32B候选边界匹配诊断，固定16事件/42原及平移上下文，现有权重原地推理。'
        f'当前`{aggregate["current_stage"]}`，实际成功32B上下文{snapshot["done_count"]}/42，工程失败{len(snapshot["failures"])}。'
        'CPU核验、首个真实生成、独立回放和终态成本分别登记；时间重叠与稳定不证明同事件或正确边界，弱外部参考覆盖未知。'
        '本诊断无8B更新、无新426提交包，不宣称提升；下一路线由实际证据另行登记。旧B最佳37.63、V14用户差值推算37.60及B2用户37.32各原包绑定保持。'
        f'见[边界协议]({REL}/{entry}/PROTOCOL.md)及[筛选聚合]({REL}/{entry}/aggregate_execution.json)。\n\n<!-- END_CURRENT_B_BOUNDARY -->\n')
    def front(text):
        first,rest=text.split('\n',1)
        if '<!-- END_CURRENT_B_BOUNDARY -->' in rest:rest=rest.split('<!-- END_CURRENT_B_BOUNDARY -->',1)[1]
        return first+'\n'+body+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):edit(PUB/'docs'/name,lambda t:front(t).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';original=mp.read_bytes();ending='\r\n' if b'\r\n' in original else '\n'
    manifest=json.loads(original);rows={x['path']:x for x in manifest['files']}
    for path in selected+[derived]:
        is_derived=path==derived;relative=path.relative_to(PUB if is_derived else WORKSPACE).as_posix()
        if relative not in rows:
            manifest['files'].append(dict(path=relative,source_relative_path=None if is_derived else relative,
                bytes=0,sha256='',category='aggregate_acceptance_no_frame_data' if is_derived else
                ('project_code_or_configuration' if path.suffix=='.py' else 'experiment_protocol_or_acceptance')))
    for row in manifest['files']:
        path=PUB/row['path'];row['bytes']=path.stat().st_size;row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps({'status':'PASS_CURATED_B_BOUNDARY_CORE_AND_AGGREGATE','selected_files':len(selected),
        'context_reference_raw_frames_labels_weights_ZIP_exported':False}))


def publish_b_prompt_recovery_v1():
    """Explicit source/aggregate whitelist; original per-frame manifests stay private."""
    publish_boundary_diagnostic_v1()
    entry='b_prompt_recovery_v1';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_b_prompt_recovery_v1/latest.json').read_bytes())
    assert snapshot['entry']==entry
    assert hashlib.sha256((here/'source_lock.json').read_bytes()).hexdigest()==snapshot['source_lock_sha256']
    selected=[p for p in here.iterdir() if p.is_file() and p.suffix in ('.py','.md')]
    selected += [RUN/'controller'/n for n in ('register_b_prompt_recovery_v1.py','checkpoint_b_prompt_recovery_v1.py',
        'inspect_b_prompt_recovery_v1.py','record_b_prompt_recovery_execution_20261009.py',
        'B_PROMPT_RECOVERY_EXECUTION_20261009.md','publish_b2_snapshot.py')]
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    cpu=json.loads((here/'cpu_acceptance.json').read_bytes())
    prepared=json.loads((here/'prepared.json').read_bytes())
    assert cpu['status']=='PASS_ACTUAL_NEW_B1_NATIVE_PROCESSOR_AND_EXACT_RESUME'
    stage=(snapshot['stages'].get('progress.json') or {}).get('stage')
    if stage is None:stage='SOURCE_PREFLIGHT_CPU' if snapshot['processes'] else 'FROZEN_PENDING_SINGLE_LAUNCH'
    aggregate={'status':'CURATED_HISTORICAL_B1_PROMPT_AND_GRAMMAR_EXPLORATION_NOT_QUALITY_TRUTH',
        'snapshot_utc':snapshot['utc'],'entry':entry,'source_lock_sha256':snapshot['source_lock_sha256'],
        'frozen_files':snapshot['frozen_files'],'stage':stage,'actual_new_B1_done':snapshot['done_count'],
        'new_failure_count':len(snapshot['failures']),'all_new_done_bound_SHA_pass':snapshot['all_done_bound_SHA_pass'],
        'all_exact_original_resume_SHA_pass':snapshot['all_original_resume_bindings_SHA_pass'],
        'original_resume_counts':snapshot['resume_counts'],'private_resume_manifest_sha256':snapshot['original_resume_manifest_sha256'],
        'records':prepared['records'],'source_groups':prepared['groups'],'natural_windows':prepared['windows'],
        'planned_missing_B1_calls':prepared['missing_B1'],'new_optimizer_updates':0,'new_32B_calls':0,
        'new_overview_calls':0,'production_weight':'ORIGINAL_B_8B','coupled_prompt_and_grammar_not_cardinality_only':True,
        'old_37_63_ZIP_byte_identity_claimed':False,'weak_reference_coverage':'UNKNOWN','official_score':None,
        'forced_nonempty_contract_risk_retained':True,'old_teacher_or_C_or_65_CE_repeated':False,
        'actual_CPU':{k:cpu[k] for k in ('status','utc','original_NONTEST8_five_arm_proof_reused',
            'original_proof_sha256','input_tokens','B1_B0_actual_video_tensor_equal','original_native_pixel_SHA_equal',
            'actual_B1_empty_rejected','original_parser_cases','changed_cache_contract_rejections','new_model_calls','new_optimizer_updates')},
        'private_CPU_receipt_sha256':hashlib.sha256((here/'cpu_acceptance.json').read_bytes()).hexdigest(),
        'raw_frames_reference_rows_weak_labels_models_ZIP_exported':False}
    report=snapshot['stages'].get('developer_01/report.json')
    if report:aggregate['full_developer_investment_report']=report
    first=snapshot['stages'].get('first_real_acceptance.json')
    if first:
        aggregate['first_real_CPU_acceptance']={k:first[k] for k in ('status','utc','input_tokens',
            'native_decoder_processor_actual_prefix_raw_validator_equal','new_model_calls','new_optimizer_updates')}
        aggregate['first_real_CPU_acceptance']['private_receipt_sha256']=hashlib.sha256((here/'first_real_acceptance.json').read_bytes()).hexdigest()
    final=snapshot['stages'].get('final_acceptance.json')
    aggregate['new_final_426_ZIP_complete']=bool(final)
    if final:
        assert final['status']=='PASS_INDEPENDENT_HISTORICAL_B1_FINAL'
        aggregate['final_package']={k:final[k] for k in ('status','utc','candidate','zip_bytes','zip_sha256','new_optimizer_updates','official_score')}
        aggregate['final_package']['all_8_and_426_strict']=all(all(v['all_11_checks'].values()) for v in final['reports'].values())
    aggregate['resources']={n:{k:v['resource'][k] for k in ('status','exit_code','stop_reason','charged_seconds',
        'started_utc','finished_utc') if k in v['resource']} for n,v in snapshot['resources'].items() if v.get('resource')}
    derived=PUB/REL/entry/'aggregate_execution.json';derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'\n## 当前历史B提示恢复探索（实际快照{snapshot["utc"]}）\n\n'
        'C固定门已拒绝生产；32B边界16事件/42上下文完整工程通过，但仅3事件在所有上下文唯一重叠，2固定弱方向均负，宏差−0.11320021399718093，未准入边界训练。'
        '主控独立恢复已有完整B1历史提示及1..5语法，以原B8B权重和当前native输入对照B0；这是耦合合同替代，不声称旧37.63包逐字节复现或cardinality单因果。'
        '固定104/96/112及原24/72来源组，精确复用26已完成B1与112 B0，仅生成86缺失B1，NONTEST各8也原字节引用。无粗览、32B新调用或训练。'
        f'当前`{stage}`、本阶段实际新done{snapshot["done_count"]}、工程失败{len(snapshot["failures"])}；CPU与启动不冒充生成。'
        '完整104及新增72的事前弱输出集合投入门通过后才NONTEST11strict和426/521完整候选；覆盖及真值未知，不保证高于37.63，新官网分未知。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)和[筛选聚合]({REL}/{entry}/aggregate_execution.json)。\n\n<!-- END_CURRENT_B_PROMPT_RECOVERY -->\n')
    def front(t):
        first,rest=t.split('\n',1)
        if '<!-- END_CURRENT_B_PROMPT_RECOVERY -->' in rest:rest=rest.split('<!-- END_CURRENT_B_PROMPT_RECOVERY -->',1)[1]
        return first+'\n'+body+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):edit(PUB/'docs'/name,lambda t:front(t).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';raw=mp.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n';manifest=json.loads(raw)
    present={x['path'] for x in manifest['files']}
    for path in selected+[derived]:
        is_derived=path==derived;rel=path.relative_to(PUB if is_derived else WORKSPACE).as_posix()
        if rel not in present:
            manifest['files'].append(dict(path=rel,source_relative_path=None if is_derived else rel,bytes=0,sha256='',
                category='aggregate_acceptance_no_frame_data' if is_derived else ('project_code_or_configuration' if path.suffix=='.py' else 'experiment_protocol_or_acceptance')))
    for row in manifest['files']:
        data=(PUB/row['path']).read_bytes();row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps({'status':'PASS_CURATED_B_PROMPT_RECOVERY_CORE_AND_AGGREGATE','selected_files':len(selected),
        'raw_frames_reference_rows_models_new_ZIP_exported':False}))


def publish_nested_density_v1():
    """Only explicitly selected core, protocols and aggregate engineering evidence."""
    publish_b_prompt_recovery_v1()
    entry='nested_density_v1';here=RUN/entry
    snapshot=json.loads((RUN/'controller/monitor_nested_density_v1/latest.json').read_bytes())
    assert snapshot['entry']==entry and snapshot['source_lock_sha256']
    lock=json.loads((here/'source_lock_summary.json').read_bytes())
    assert lock['actual_core_SHA_pass'] and lock['source_lock_sha256']==snapshot['source_lock_sha256']
    names=('nd_common.py','nd_native.py','nd_video.py','nd_prepare.py','nd_cpu.py','nd_engine.py','nd_report.py',
        'freeze.py','packager.py','final_acceptance.py','controller.py','launch.py','CONTINUE.md','PROTOCOL.md')
    selected=[here/n for n in names]+[RUN/'controller'/n for n in ('register_nested_density_v1.py',
        'checkpoint_nested_density_v1.py','inspect_nested_density_v1.py','record_nested_density_execution_20261009.py',
        'NESTED_DENSITY_EXECUTION_20261009.md','publish_b2_snapshot.py')]
    for name in names:
        remote='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/'+entry+'/'+name
        assert hashlib.sha256((here/name).read_bytes()).hexdigest()==lock['new_core_locked_sha'][remote]
    for path in selected:
        target=PUB/path.relative_to(WORKSPACE);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);assert target.read_bytes()==path.read_bytes()
    cpu=snapshot['stages']['cpu_acceptance.json']
    assert cpu['status']=='PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY' and cpu['actual_proof_count']==120
    stage=snapshot.get('actual_execution_stage') or (snapshot['stages'].get('progress.json') or {}).get('stage')
    aggregate=dict(status='CURATED_NESTED_NATIVE_DENSITY_ENGINEERING_NOT_QUALITY_TRUTH',
        snapshot_utc=snapshot['utc'],entry=entry,source_lock_sha256=snapshot['source_lock_sha256'],frozen_files=snapshot['frozen_files'],
        current_stage=stage,actual_new_density_done=snapshot['done_count'],done_by_scope=snapshot['done_by_scope'],
        new_failure_count=len(snapshot['failures']),all_new_done_bound_SHA_pass=snapshot['all_done_bound_SHA_pass'],
        all_new_model_receipts_match=snapshot['all_done_model_identity_matches_actual_receipts'],
        original120_baseline_and86_B1_bindings_SHA_pass=snapshot['all_original_resume_bindings_SHA_pass'],
        physical_floor64_subset_retained=True,nested_physical_frames_max=127,total_video_pixel_budget_unchanged=True,
        temporal_density_spatial_resolution_tradeoff_explicit=True,identical_video_tensors_claimed=False,
        observed_development_not_fresh_holdout=True,reference_coverage='UNKNOWN',quality_truth='UNKNOWN',
        production_weight='ORIGINAL_B_8B',new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0,new_spatial_calls=0,
        official_score=None,not_guaranteed_to_exceed37_63=True,
        actual_CPU={k:cpu[k] for k in ('status','utc','physical_sampling_contract_cases','registered_gate_cases','max_input_tokens',
            'actual_all120_inputs_not_estimated','new_model_calls','new_optimizer_updates','new_32B_calls')},
        actual_CPU_input_count=cpu['actual_proof_count'],actual_spatial_grid_changed_windows=cpu['spatial_grid_changed_windows'],
        private_CPU_receipt_sha256=cpu['full_private_receipt_sha256'],
        source_lock_resume_frames_raw_reference_rows_labels_weights_ZIP_exported=False)
    first=snapshot['stages'].get('first_real_acceptance.json')
    if first:
        aggregate['first_real_independent_CPU']={k:first[k] for k in ('status','utc','input_tokens',
            'actual_native_processor_raw_validator_equal','new_model_calls','new_optimizer_updates')}
        aggregate['first_real_independent_CPU']['private_receipt_sha256']=hashlib.sha256((here/'first_real_acceptance.json').read_bytes()).hexdigest()
    report=snapshot['stages'].get('developer_01/report.json')
    if report:aggregate['full_developer_aggregate']=report
    final=snapshot['stages'].get('final_acceptance.json')
    aggregate['new_final426_complete']=bool(final)
    if final:
        assert final['status']=='PASS_INDEPENDENT_NESTED_NATIVE_DENSITY_FINAL'
        aggregate['final_package']={k:final[k] for k in ('status','utc','candidate','zip_bytes','zip_sha256','new_optimizer_updates','official_score')}
        aggregate['final_package']['all8_and426_11strict']=all(all(r['all_11_checks'].values()) for r in final['reports'].values())
        aggregate['final_package']['private_final_receipt_sha256']=hashlib.sha256((here/'final_acceptance.json').read_bytes()).hexdigest()
    aggregate['resources']={n:{k:v['resource'][k] for k in ('status','exit_code','stop_reason','charged_seconds','started_utc','finished_utc') if k in v['resource']}
        for n,v in snapshot['resources'].items() if v.get('resource')}
    derived=PUB/REL/entry/'aggregate_execution.json';derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=(f'\n## 当前嵌套原生帧密度探索（实际快照{snapshot["utc"]}）\n\n'
        '原C/32B边界/历史B1固定科学拒绝保持；B1完整86新回答和CPU回放工程通过，但all104差−0.009816273304981254、扩展72差−0.01620639512922189，未生产426包。'
        '本独立实验保留原floor64物理观察，再加入每对非连续相邻序号的一个原生中点，最多127物理帧；原B8B/B0提示/0..5语法及全部原自然窗保持。'
        '固定总video像素预算带来时间密度与空间grid的取舍，真实记录，不称视频tensor相同。120实际CPU接口已核，CPU与启动不是生成。'
        f'当前`{stage}`，实际新密度done{snapshot["done_count"]}，失败{len(snapshot["failures"])}；训练/32B/粗览新调用0。'
        '原开发集合已被观察，弱输出集合门仅投入证据，覆盖与真值UNKNOWN，不保证超过37.63，新官网分未知。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)和[筛选聚合]({REL}/{entry}/aggregate_execution.json)。\n\n<!-- END_CURRENT_NESTED_DENSITY -->\n')
    if final:body=body.replace('新官网分未知。',f'最终426包已独立验收，实际{final["zip_bytes"]}字节、SHA256`{final["zip_sha256"]}`，Linux路径`{final["candidate"]}`；新官网分未知。')
    def front(t):
        first,rest=t.split('\n',1)
        if '<!-- END_CURRENT_NESTED_DENSITY -->' in rest:rest=rest.split('<!-- END_CURRENT_NESTED_DENSITY -->',1)[1]
        return first+'\n'+body+rest
    edit(PUB/'README.md',front)
    for name in ('SOLUTIONS.md','REPRODUCTION.md'):edit(PUB/'docs'/name,lambda t:front(t).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';raw=mp.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n';manifest=json.loads(raw)
    present={x['path'] for x in manifest['files']}
    for path in selected+[derived]:
        is_derived=path==derived;rel=path.relative_to(PUB if is_derived else WORKSPACE).as_posix()
        if rel not in present:manifest['files'].append(dict(path=rel,source_relative_path=None if is_derived else rel,bytes=0,sha256='',
            category='aggregate_acceptance_no_frame_data' if is_derived else ('project_code_or_configuration' if path.suffix=='.py' else 'experiment_protocol_or_acceptance')))
    for row in manifest['files']:
        data=(PUB/row['path']).read_bytes();row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_NESTED_DENSITY_CORE_AND_AGGREGATE',selected_files=len(selected),raw_frames_reference_rows_models_new_ZIP_exported=False)))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for v in ('v8','v9','v10','v11','v12','v13','v14'):parser.add_argument('--teacher-'+v,action='store_true')
    parser.add_argument('--context-advisory',action='store_true')
    parser.add_argument('--boundary-diagnostic',action='store_true')
    parser.add_argument('--b-prompt-recovery',action='store_true')
    parser.add_argument('--nested-density',action='store_true')
    args=parser.parse_args()
    if args.nested_density:publish_nested_density_v1()
    elif args.b_prompt_recovery:publish_b_prompt_recovery_v1()
    elif args.boundary_diagnostic:publish_boundary_diagnostic_v1()
    elif args.context_advisory:publish_context_advisory_v1()
    elif args.teacher_v14:publish_teacher_v14()
    elif args.teacher_v13:publish_teacher_v13()
    elif args.teacher_v12:publish_teacher_v12()
    elif args.teacher_v8 or args.teacher_v9 or args.teacher_v10 or args.teacher_v11:
        publish_teacher_v8('teacher_student_autopilot_v11' if args.teacher_v11 else ('teacher_student_autopilot_v10' if args.teacher_v10 else ('teacher_student_autopilot_v9' if args.teacher_v9 else 'teacher_student_autopilot_v8')))
    else:main()
