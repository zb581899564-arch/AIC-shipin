"""Private unbound current handoff; preserve all old execution histories."""
import json
from register_b2_package_v1 import RUN


def main():
    snapshot=json.loads((RUN/'controller/monitor_b_boundary_diagnostic_v1/latest.json').read_bytes())
    upstream=snapshot['upstream_C'];report=upstream['report'];stages=snapshot['stages']
    marker='<!-- END_CURRENT_B_BOUNDARY_DIAGNOSTIC -->'
    body=(f'## 20261009自主B边界诊断接续（实际快照{snapshot["utc"]}）\n\n'
        f'C原104/96/112完整自然成功，原固定门STOP_C_PRODUCTION_INVESTMENT保持：新增72组R−N={report["comparisons"]["new72_source_groups"]["R_minus_N"]["mean"]}；'
        f'实际fullGPU charge{upstream["resource"]["charged_seconds"]}秒completed/exit0/null，所有旧成功与冻结原字节保持。S独立构图参考0，EVIDENCE_INSUFFICIENT，不冒充构图真值。\n\n'
        f'唯一b_boundary_diagnostic_v1/CONTINUE.md与PROTOCOL.md；source_lock SHA{snapshot["source_lock_sha256"]}，冻结{snapshot["frozen_files"]}文件，'
        f'实际阶段{(stages.get("progress.json") or {}).get("stage")}，完整所属命令{len(snapshot["processes"])}，'
        f'盘上新32B context done{snapshot["done_count"]}，逐绑定SHA{snapshot["all_done_bound_SHA_pass"]}，新failure{len(snapshot["failures"])}。'
        f'原固定16事件/原窗及已登记合法平移context，首次真实生成/CPU回放{(stages.get("first_real_acceptance.json") or {}).get("status","PENDING")}。'
        '32B原地推理，不是32B微调；本诊断新8B调用/optimizer更新0，无最终426 ZIP。CPU/计划/冻结/启动不叫真实生成。\n\n'
        '原B提议不是标签；原B/F约束与原validator保持，原回答先不可覆盖落盘。唯一时间重叠为弱匹配，语义同事件/边界真值UNKNOWN；NO/UNKNOWN不负，候选外UNKNOWN，稳定不当正确。'
        '外部弱参考在新调用前固定，缺失/歧义不造标签，coverage UNKNOWN；完整16分母及context结果后主控从独立方向证据继续登记实现，不等用户，不自动训练或重开65CE/旧160/C提示。\n\n'
        'aic-linux ACTIVE每15分钟failed_runs_only静默，当前入口controller/checkpoint_b_boundary_diagnostic_v1.py。'
        '实核完整命令/父子PGID/IO/服务器/共享GPU锁/资源终态/追加账本7200/bytes/mtime；非原子component UTC保留。CPU SHA/顺解/grammar/排队可合法，不因GPU闲认卡死。'
        '冻结源码和成功生成不重复；工程问题独立版本、CPU/真实非测试验收/新锁单次启动；外部任务/连接/服务保留。'
        '项目既有小量控制直SSH授权，Mac实际在线但不参与；新大流量仍先许可。最终完整ZIP全部验收与筛选GitHub发布后一次通知并删除监控，不归档、不自动回传或官网提交。\n\n'+marker+'\n\n')
    for path in (RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md'):
        for lp in RUN.glob('*/source_lock.json'):
            lock=json.loads(lp.read_bytes());entries=lock.get('files',lock.get('production_files',{}))
            names=list(entries) if isinstance(entries,dict) else [x['path'] for x in entries]
            assert not any(n.endswith('/'+path.name) for n in names),'handoff frozen'
        old=path.read_text(encoding='utf-8')
        if marker in old:old=old.split(marker,1)[1].lstrip('\n')
        path.write_text(body+old,encoding='utf-8')
    (RUN/'controller/b_boundary_handoff_latest.md').write_text(body,encoding='utf-8')
    print('PASS_PRIVATE_UNBOUND_B_BOUNDARY_HANDOFF',snapshot['utc'],snapshot['done_count'])


if __name__=='__main__':main()
