"""Current private handoff outside all historical frozen schemas."""
import json
from register_b2_package_v1 import RUN

def main():
    s=json.loads((RUN/'controller/monitor_b_prompt_recovery_v1/latest.json').read_bytes())
    stage=(s['stages'].get('progress.json') or {}).get('stage') or ('SOURCE_PREFLIGHT_CPU' if s['processes'] else 'FROZEN_PENDING_SINGLE_LAUNCH')
    marker='<!-- END_CURRENT_B_PROMPT_RECOVERY -->'
    body=(f'## 20261009自主历史B提示恢复（实际快照{s["utc"]}）\n\n'
        '原C固定104门STOP保持；原32B边界诊断16/42工程完整PASS/0失败，只有3事件所有context唯一重叠，'
        '2固定弱方向均负、宏差−0.11320021399718093，语义身份/边界真值UNKNOWN，未准入边界训练。'
        '原42实际调用与1998.8051604395732秒真实GPU费用/唯一账本、旧raw/STOP保留，不重复验收或调用。\n\n'
        f'唯一b_prompt_recovery_v1/CONTINUE.md与PROTOCOL.md，锁SHA{s["source_lock_sha256"]}、冻结{s["frozen_files"]}文件；'
        f'实际阶段{stage}、完整所属命令{len(s["processes"])}、本阶段新B1 done{s["done_count"]}、failure{len(s["failures"])}、'
        f'绑定SHA{s["all_done_bound_SHA_pass"]}、旧精确resume SHA{s.get("all_original_resume_bindings_SHA_pass")}。\n\n'
        '独立恢复已有完整B1历史prompt及1..5 grammar，原B8B权重与native输入保持；这是耦合历史合同对照，不称cardinality单因果或旧37.63包逐字节复现。'
        '完整104/96/112及原24/72组固定，旧B1已完成26和B0全部112/NT各8按原request/model/raw/validator逐SHA引用，仅86缺失B1新生成；无overview/32B/新训练。'
        '实际CPU新首缺失窗口B1/B0视频tensor与B0原像素相等/真实5292及5329tokens，旧8源五臂CPU proof引用而非重复。'
        '新86实际生成/CPU独立回放后，原登记all104弱输出集合差>=0且新72>0及选帧变化门，才NT8完整11strict/426全部521窗/空间exact复用/独立ZIP。'
        '弱覆盖UNKNOWN，非质量真值/官网分，不删难窗/改提示/放宽门或拿空比例造监督。新模型调用以实际done为准，启动和CPU不是生成。\n\n'
        'aic-linux每15分钟failed_runs_only静默，入口controller/checkpoint_b_prompt_recovery_v1.py；保护全部历史冻结/旧raw/外部任务/共享锁/7200账本/连接。'
        '按完整命令/-B/父子PGID/IO/CPU/GPU/RAM/disk及产物逐UTC核验，不据GPU闲或短暂无回执认卡死。'
        '工程故障复现后新版本/exact成功复用，科学STOP主控继续具体机制审计、不等待用户、不强造提升。'
        '项目已有小量控制直SSH授权、Mac在线不参与；新大流量先许可。只有真实新426最终包全部独立通过且筛选发布后一次通知/删除监控，不归档、不自动回传或官网提交。\n\n'+marker+'\n\n')
    for p in (RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md'):
        for lp in RUN.glob('*/source_lock.json'):
            lock=json.loads(lp.read_bytes());rows=lock.get('files',lock.get('production_files',{}))
            names=list(rows) if isinstance(rows,dict) else [r['path'] for r in rows]
            assert not any(x.endswith('/'+p.name) for x in names),'handoff frozen'
        old=p.read_text(encoding='utf-8')
        if marker in old:old=old.split(marker,1)[1].lstrip('\n')
        p.write_text(body+old,encoding='utf-8')
    (RUN/'controller/b_prompt_recovery_handoff_latest.md').write_text(body,encoding='utf-8')
    print('PASS_PRIVATE_RECOVERY_HANDOFF',s['utc'],stage)

if __name__=='__main__':main()
