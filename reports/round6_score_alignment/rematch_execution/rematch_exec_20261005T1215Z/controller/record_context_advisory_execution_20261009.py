"""Refresh only unbound private handoffs; preserve all historical sections."""
import json
from collections import Counter
from pathlib import Path
from register_b2_package_v1 import RUN, REMOTE


def main():
    snap=json.loads((RUN/'controller/monitor_context_advisory_v1/latest.json').read_bytes())
    marker='<!-- END_CURRENT_CONTEXT_ADVISORY -->'
    phase=(snap['stages'].get('progress.json') or {}).get('stage','SOURCE_IDENTITY_CPU_PENDING_STAGE')
    start=snap['stages'].get('start.json') or {}
    scopes={}
    for scope in ('nontest_01','developer_01','rematch_01'):
        rows=[x for x in snap['done'] if f'/{scope}/' in x['path']]
        if rows:
            scopes[scope]={'done':dict(Counter(x['kind'] for x in rows)),
                'local_arms':dict(Counter(x['arm'] for x in rows if x['kind']=='local')),
                'overview_event_counts':dict(Counter(x['events_count'] for x in rows if x['kind']=='overview'))}
    body=(f'## 20261009：自主C-advisory新路线（实际快照{snap["utc"]}）\n\n'
        '用户要求继续探索更好包并睡觉期间主控负责。ai-yiguodun已修改Pro必须Chrome网页研究项目内先对话；'
        'Tibo/Sol/Grok各两轮实际完整讨论与最终metadata同步。连续Pro3次已用/新0、Gemini无有效回复，主控独立兜底不冒充共识。'
        '最佳旧B37.63保持，V14用户少.03仅推算37.60非独立官网核验。\n\n'
        f'唯一context_advisory_v1/CONTINUE.md及PROTOCOL.md，冻结{snap["frozen_files"]}文件SHA{snap["source_lock_sha256"]}；'
        f'单次start UTC{start.get("utc")}历史PID{start.get("pid")}，本次实际所属完整命令{len(snap["processes"])}。'
        f'阶段{phase}，粗览/局部已done {snap.get("done_by_kind",{})}、各臂局部{snap.get("local_done_by_arm",{})}、新failure{len(snap["failures"])}，所有已done绑定SHA {snap["all_done_bound_SHA_pass"]}。'
        f'分scope盘上实际集合{scopes}；存量/复用不当当前阶段新调用，进度各自UTC按snapshot保留，组件顺序读取非原子。'
        f'逐scope已写出模型receipt实际字节SHA{ {n:v["sha256"] for n,v in snap.get("model_receipts",{}).items()} }，全部done模型身份与回执相等{snap.get("all_done_model_identity_matches_actual_receipts","NOT_CAPTURED_HISTORICAL_SNAPSHOT")}；阶段实际读取UTC另见snapshot.stage_read_utc。'
        'CPU2145合同/实际82111token候选与8源processor已PASS，CPU/启动不当新模型生成或最终包。新训练更新0。\n\n'
        '同8B全源粗览adapter OFF、原B局部ON，全部原nativePTS/floor64自然窗继续，参数8782459120。'
        '104不同许可文件/96组分别粗览，原112开发窗、固定24组/剩72组供体；32旧teacher交叠如实记录。'
        '后台8五臂/11strict→24五臂→104四臂→固定投入门→合格单R426/521+426粗览/exact空间复用/11strict/独立ZIP账本。'
        '弱参考覆盖UNKNOWN，闭世界一致性只投入排序，幻觉/真实质量UNKNOWN。不事后改提示/阈值/样本，原97白名单和唯一小数尾端精确登记不扩大。\n\n'
        '工程STOP独立复现修复新版本/exact成功复用不重跑；C STOP具体S CPU inventory与固定16事件B平移hand-off后监控实现真实matched边界诊断，稳定不当真值，无方向不训练，D/65CE不重开。'
        'aic-linux实际ACTIVE每15分钟failed_runs_only静默入口controller/checkpoint_context_advisory_v1.py，实际snapshot/latest_delta有各组件UTC。'
        'GPU闲/CPU SHA/grammar/顺解/队列不当卡死；共享任务/锁/7200账本/连接保留。Mac实际在线、仅项目既有小量控制直SSH授权，无新模型/数据/ZIP大流量。'
        '最终真实8/426各11strict、ZIP大小SHA/CRC/唯一JSONL/身份原字节/全部终态费用与筛选GitHub发布齐后一次通知/删除监控，不归档；新官网分未知，不自动回传或上传。\n\n'+marker+'\n\n')
    proof_path=RUN/'controller/C_ADVISORY_first_real_acceptance_20261009.json'
    if proof_path.exists():
        import hashlib
        proof=json.loads(proof_path.read_bytes())
        proof_text=(f'独立首个真实GPU结果CPU回放{proof["utc"]} PASS，完整冻结SHA/原nativeRGB/processor/输出token/原validator与首个五臂一致；'
            f'验收新模型/优化器调用0，私有proof SHA{hashlib.sha256(proof_path.read_bytes()).hexdigest()}。实际NONTEST_GPU charge{proof["actual_NONTEST_GPU_charge_seconds"]}秒终态唯一账本匹配。'
            '原NONTEST8粗览均合法空事件表，不当视频无高光或教师真值，原NONTEST的R/X未携带不同事件内容，局部N/R差异不能冒称真实上下文语义提升。其他scope的实际事件数另见上方，不翻改原验收。\n\n')
        body=body.replace(marker,proof_text+marker)
    pilot_proof_path=RUN/'controller/C_ADVISORY_pilot_acceptance_20261009.json'
    if pilot_proof_path.exists():
        import hashlib
        pilot=json.loads(pilot_proof_path.read_bytes())
        assert pilot['status']=='PASS_INDEPENDENT_COMPLETE_PILOT_CPU_NATIVE_PROCESSOR_REPLAY'
        assert pilot['source_lock_sha256']==snap['source_lock_sha256']
        assert pilot['new_acceptance_model_calls']==pilot['new_acceptance_optimizer_updates']==0
        text=(f'完整pilot独立CPU回放{pilot["utc"]} PASS：24源/24组/26原自然窗、24粗览及130五臂局部的原request/raw/输出token/真实nativeRGB/processor/原validator逐一相等；'
            f'原GPU charge{pilot["actual_GPU_charge_seconds"]}秒终态唯一账本匹配，验收新模型/优化器调用0，私有proof SHA{hashlib.sha256(pilot_proof_path.read_bytes()).hexdigest()}。'
            f'原label-blind R/N集合变化{pilot["R_N_changed_native_sets"]}/24、R/X变化{pilot["R_X_changed_native_sets"]}/24，粗览事件数{pilot["overview_event_counts"]}；'
            '合法空表及模板差异不当真实事件语义改善，未读弱方向，完整104/剩72组固定投入门仍须完成。\n\n')
        body=body.replace(marker,text+marker)
    for path in (RUN.parents[3]/'AGENTS.md', RUN/'STATUS_AUTOPILOT_20261007.md'):
        for lp in RUN.glob('*/source_lock.json'):
            value=json.loads(lp.read_bytes());entries=value.get('files',value.get('production_files',{}))
            names=list(entries) if isinstance(entries,dict) else [x['path'] for x in entries]
            assert not any(n.endswith('/'+path.name) for n in names), 'handoff filename frozen'
        old=path.read_text(encoding='utf-8')
        if marker in old:old=old.split(marker,1)[1].lstrip('\n')
        path.write_text(body+old,encoding='utf-8')
    (RUN/'controller/context_advisory_handoff_latest.md').write_text(body,encoding='utf-8')
    print(phase, snap['done_count'], 'PRIVATE_UNBOUND_HANDOFF_UPDATED')


if __name__=='__main__':main()
