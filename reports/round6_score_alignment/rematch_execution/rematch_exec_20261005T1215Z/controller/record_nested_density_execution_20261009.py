"""Private truthful continuation outside all historical frozen source schemas."""
import json
from register_b2_package_v1 import RUN

def main():
    s=json.loads((RUN/'controller/monitor_nested_density_v1/latest.json').read_bytes())
    stage=s.get('actual_execution_stage') or (s['stages'].get('progress.json') or {}).get('stage') or ('PREFREEZE_ACTUAL_CPU_ADMISSION' if s['processes'] else 'PREPARED_PENDING_CPU')
    marker='<!-- END_CURRENT_NESTED_DENSITY -->';up=s['upstream_B1'];report=up['report']
    resource_summary={}
    for name,pair in s.get('resources',{}).items():
        value=pair.get('resource')
        if value:
            resource_summary[name]={k:value.get(k) for k in ('status','finished_utc','exit_code','stop_reason','charged_seconds')}
            if value.get('status')=='completed':
                resource_summary[name]['unique_ledger_match']=sum(row==value for row in s['GPU_ledger']['owned_rows'])==1
    replay_summary={scope:{k:value.get(k) for k in ('status','actual_proof_count','first_proof_sha256','full_private_receipt_sha256')}
        for scope in ('nontest_01','developer_01')
        if (value:=s['stages'].get(scope+'/replay_acceptance.json'))}
    body=(f'## 20261009单次嵌套原生帧密度探索（实际快照{s["utc"]}）\n\n'
        '原C/32B边界/历史B1科学拒绝均保留。B1实际完整86新/26旧/112B0与全部CPU回放工程失败0，'
        f'固定all104差{report["all104_B1_minus_B0"]["mean"]}、扩展72组差{report["expanded72_B1_minus_B0"]["mean"]}，'
        f'自然completed/exit0/null/charge{up["resource"]["charged_seconds"]}秒、原所属命令{len(up["actual_owned_commands"])}。'
        '原弱参考不是质量真值，不重跑成功或翻转负结果。\n\n'
        '唯一nested_density_v1/CONTINUE.md与PROTOCOL.md。原B8B/原B0 prompt与0..5 grammar/greedy保持，'
        '原floor64全部物理帧保留，再为每对非连续相邻序号加入一个向下取整中点，最多127物理帧。'
        '这是独立新输入协议，原窗口/PTS/端点/源RGB不改；固定原总video像素预算会使实际空间grid减小，真实记录，不称视频tensor相等或纯时间因果。'
        '既有104/96/112与24/72分组已被观察，不称新holdout。全部120真实native/processor/token/grid/RGB CPU接口先准入，'
        '再单次冻结与8非测试真实新生成/独立回放/11strict；112开发全部新生成/全CPU回放后才固定弱输出集合投入门，'
        'GO才426/521与空间exact缓存/独立ZIP。无overview/32B/新optimizer，不无限换提示或造提升。\n\n'
        f'当前stage={stage}，冻结文件{s["frozen_files"]}、锁SHA={s["source_lock_sha256"]}；'
        f'完整所属命令{len(s["processes"])}、实际D done{s["done_count"]}、逐窗failure{len(s["failures"])}、'
        f'已done绑定SHA{s["all_done_bound_SHA_pass"]}、原120B0及86B1保留SHA{s.get("all_original_resume_bindings_SHA_pass")}。'
        f'实际scope计数{s.get("done_by_scope")}；CPU与计划/冻结/启动不是生成。'
        f'各实际GPU回执{resource_summary}；ledger{s["GPU_ledger"]["lines"]}/历史offset{s["GPU_ledger"]["historical_offset"]}保持，'
        '尚未终态的活跃GPU作业费用待自然终态追加，已完成费用按真实回执记录，不写0成本。'
        f'实际独立CPU回放聚合{replay_summary}；已完成的回放和成功生成不重复。'
        '组件各自UTC/bytes/mtime与完整命令/-B/父子PGID/IO/fds及资源账本见private monitor，不凭GPU闲或短暂无回执认卡死。\n\n'
        'aic-linux每15分钟failed_runs_only静默，入口controller/checkpoint_nested_density_v1.py。'
        '冻源码/旧raw/STOP/UNKNOWN/成功验收/外部任务/共享锁/7200账本/连接保留；工程异常仅新版本真实复现修复与exact成功复用。'
        'Mac在线不参与，既有小量控制直SSH授权保持，新大模型/数据/批量产物/ZIP流量先许可。'
        '只有新的426完整真实final/8和426各11strict/实际ZIP字节SHA CRC身份/所有GPU终态账本及筛选GitHub齐后一次通知/删除监控，'
        '不归档、不自动回传或官网提交，新官网分UNKNOWN，未保证超过37.63。\n\n'+marker+'\n\n')
    for p in (RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md'):
        for lp in RUN.glob('*/source_lock.json'):
            lock=json.loads(lp.read_bytes());rows=lock.get('files',lock.get('production_files',{}))
            names=list(rows) if isinstance(rows,dict) else [r['path'] for r in rows]
            assert not any(x.endswith('/'+p.name) for x in names),'handoff frozen'
        old=p.read_text(encoding='utf-8')
        if marker in old:old=old.split(marker,1)[1].lstrip('\n')
        p.write_text(body+old,encoding='utf-8')
    (RUN/'controller/nested_density_handoff_latest.md').write_text(body,encoding='utf-8')
    print('PASS_PRIVATE_NESTED_DENSITY_HANDOFF',s['utc'],stage)

if __name__=='__main__':main()
