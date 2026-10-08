"""Private continuation, outside every historical frozen source schema."""
import json
from register_b2_package_v1 import RUN

def main():
    s=json.loads((RUN/'controller/monitor_native_round_alignment_v1/latest.json').read_bytes())
    stage=s.get('actual_execution_stage') or (s['stages'].get('progress.json') or {}).get('stage') or 'PREFREEZE_ADMISSION_PENDING'
    cpu=s['stages'].get('cpu_acceptance.json') or {};up=s['upstream_density'];r=up['report']
    first=s['stages'].get('first_real_acceptance.json') or {}
    replays={k:{field:v.get(field) for field in ('status','actual_proof_count','fresh_replay_count','exact_original_success_reused','first_proof_sha256','full_private_receipt_sha256')}
        for k,v in s['stages'].items() if k.endswith('/replay_acceptance.json') and v}
    nontest=s['stages'].get('nontest_01/independent_validation.json') or {}
    nontest_checks=nontest.get('checks',{})
    archives=s.get('actual_archives',{})
    round_report=s['stages'].get('developer_01/report.json') or {}
    disposition=RUN/'controller/NRA_monitor_disposition_20261009.json'
    monitor_deleted=disposition.exists() and json.loads(disposition.read_bytes()).get('status')=='DELETED_OBSOLETE_AIC_LINUX_AFTER_FINITE_SCIENTIFIC_STOP'
    monitor_text=('aic-linux已删除：本次有限已登记输入机制全部结束且未通过投入门，无剩余作业可巡检；目标更好426包尚未取得，不称完成。'
        if monitor_deleted else 'aic-linux每15分钟failed_runs_only静默，入口controller/checkpoint_native_round_alignment_v1.py，record只更新未绑定AGENTS/STATUS/handoff；')
    resources={}
    for n,pair in s['resources'].items():
        v=pair.get('resource')
        if v:
            resources[n]={k:v.get(k) for k in ('status','finished_utc','exit_code','stop_reason','charged_seconds')}
            resources[n]['unique_terminal_ledger_match']=sum(row==v for row in s['GPU_ledger']['owned_rows'])==1
    marker='<!-- END_CURRENT_NATIVE_ROUND_ALIGNMENT -->'
    text=(f'## 20261009单次 native nearest64 服务输入对齐（实际快照{s["utc"]}）\n\n'
        f'原密度完整112开发/120总成功及全CPU通过、工程失败0，固定all104差{r["all104_D_minus_B0"]["mean"]}、'
        f'扩展72差{r["expanded72_D_minus_B0"]["mean"]}，科学拒绝原样保留；原所属完整命令{len(up["actual_owned_commands"])}。'
        '原开发已被观察，弱参考覆盖/人工真值/官网质量UNKNOWN，负结果不回写，不重复成功和已完成验收。\n\n'
        '只读机制审计已完成，原112历史raw全部canonical且当前grammar均接受，空白单独误拒绝0；训练nearest与当前native floor64算术在102/112开发窗改变3054个观察ordinal。'
        '唯一native_round_alignment_v1/CONTINUE.md和PROTOCOL.md：仅单次nearest64内部观察ordinal对齐，同数量/first-last/实际grid/原B8B/原B0 prompt/0..5 grammar/greedy/nativePTS/自然窗。'
        '不舍入PTS，不恢复CFR/Decord，不称原64子集或tensor相等、纯因果、旧37.63包逐字节复现。原交集RGB须精确相等；变化开发102新生成、原10成功exact引用，NONTEST8另计。'
        '120 CPU消费者移交、单次冻结preflight后单次launcher，8真实变化生成/独立CPU回放/11strict→开发全112消费者与102新回放→固定all104>=0/扩展72>0/输出集合改变门→仅GO完整426/521。'
        '门失败有限已登记输入机制证据耗尽保留B，不再扫prompt/pixel/floor/nearest/密度或重开旧65CE/160。\n\n'
        f'当前stage={stage}，冻结文件{s["frozen_files"]}、锁SHA={s["source_lock_sha256"]}；当前完整所属命令{len(s["processes"])}、'
        f'本路线实际新Q done{s["done_count"]}，逐窗failure{len(s["failures"])}，boundSHA{s["all_done_bound_SHA_pass"]}、'
        f'原120B0及密度120SHA{s.get("all_original_resume_bindings_SHA_pass")}；各scope新done{s.get("done_by_scope")}，登记变化窗{s.get("registered_changed_windows")}。'
        f'实际CPU摘要status={cpu.get("status")}、count={cpu.get("actual_proof_count")}、maxinput={cpu.get("max_input_tokens")}、receiptSHA={cpu.get("full_private_receipt_sha256")}。'
        f'首真实Q独立CPUstatus={first.get("status")}、UTC={first.get("utc")}、inputtokens={first.get("input_tokens")}、receiptSHA={first.get("private_receipt_sha256")}；已写出各scope CPU回放{replays}。已完成验收只引用不重复，阶段progress与新回执的顺序读取时差分别保留。'
        f'NONTEST独立status={nontest.get("status")}、strict项数={len(nontest_checks)}、全部strict true={bool(nontest_checks) and all(v is True for v in nontest_checks.values())}、源数={nontest.get("video_records")}、预测帧={nontest.get("prediction_frames")}；实际ZIP核验{archives}。NONTEST包仅8源，不能当426提交包；空间exact复用新模型0且原成本保持。'
        f'完整开发report status={round_report.get("status")}、all104 Q-B0={round_report.get("all104_Q_minus_B0")}、扩展72 Q-B0={round_report.get("expanded72_Q_minus_B0")}、集合改变={round_report.get("changed_native_sets")}、下降组={round_report.get("groups_down")}；仅弱一致性投入证据，非官网或质量真值。'
        f'各GPU真实回执{resources}；ledger{s["GPU_ledger"]["lines"]}/历史offset7200保持，活跃作业费用待真实终态，不写0成本。'
        '新optimizer/32B/overview/spatial0，CPU/冻结/启动/复用不是新生成或最终ZIP。非原子组件各UTC与实际父子PGID/-B/IO/fds以monitor为准；GPU闲/CPU SHA/顺解/排队可合法。\n\n'
        +monitor_text+
        '全部旧锁/成功raw/STOP/UNKNOWN/外部任务/共享锁/7200账本与连接服务保持。工程故障先真实复现，新版本/CPU/必要非测试验收/新锁单次接续，成功只全exact复用。'
        'Mac在线不参与，小量项目控制直接SSH例外保持，新model/data/批量产物/ZIP大流量先许可。'
        '只有新的真实426根completion和独立final PASS、8和426各11strict、实际ZIP大小SHA CRC唯一JSONL身份原字节/全部GPU终态账本及筛选GitHub齐后一次通知并删除监控，不归档；'
        '实际生产原B/新训练0/官网新分UNKNOWN、未保证超过37.63，包留Linux不自动回传或官网提交。\n\n'+marker+'\n\n')
    for p in (RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md'):
        for lp in RUN.glob('*/source_lock.json'):
            lock=json.loads(lp.read_bytes());rows=lock.get('files',lock.get('production_files',{}))
            names=list(rows) if isinstance(rows,dict) else [r['path'] for r in rows]
            assert not any(x.endswith('/'+p.name) for x in names),'handoff frozen'
        before=p.read_text(encoding='utf-8')
        if marker in before:before=before.split(marker,1)[1].lstrip('\n')
        p.write_text(text+before,encoding='utf-8')
    (RUN/'controller/native_round_alignment_handoff_latest.md').write_text(text,encoding='utf-8')
    print('PASS_PRIVATE_NATIVE_ROUND_ALIGNMENT_HANDOFF',s['utc'],stage)

if __name__=='__main__':main()
