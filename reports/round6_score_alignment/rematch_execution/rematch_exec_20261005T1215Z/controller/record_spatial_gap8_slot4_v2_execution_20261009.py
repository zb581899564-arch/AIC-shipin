"""Update only unfrozen private continuation, protecting both historical schemas."""
import json
from pathlib import Path
from register_b2_package_v1 import RUN,REMOTE,remote

MARKER='<!-- END_CURRENT_SPATIAL_GAP8_SLOT4_REPLAN -->'

def main():
    s=json.loads((RUN/'controller/monitor_spatial_gap8_slot4_v2/latest.json').read_bytes())
    assert not s['protected_handoff_paths'],'remote handoff path belongs to frozen source'
    stage=s.get('actual_execution_stage') or (s['stages'].get('progress.json') or {}).get('stage') or 'G0_IMPLEMENTATION'
    admission=s['stages'].get('g0_admission.json') or {};start=s['stages'].get('start.json')
    report=s['stages'].get('diagnostic_01/report.json')
    model=s['stages'].get('diagnostic_01/model.json')
    first=s['stages'].get('diagnostic_01/first_real_acceptance.json')
    receipt_summary={k:dict(status=v.get('status'),utc=v.get('utc'),sha256=s['component_sha256'][k])
        for k,v in s['stages'].items() if v and k.startswith('g0_')}
    text=(f'## 20261009空间gap8 PCHIP单次有限接续（实际快照{s["utc"]}）\n\n'
        '重新一锅炖与GPT-6 sol网页席位、Chrome研究项目Pro本轮1/5（累计slot4/8）已真实完成，余4次不为知会耗用。'
        '唯一入口spatial_gap8_pchip_slot4_v2/CONTINUE.md与PROTOCOL.md，最终final-decision-v2.md原样保持。'
        '不是多数共识或官网提分保证，旧最佳37.63保护。\n\n'
        f'当前stage={stage}；冻结文件{s["frozen_files"]}、source_lockSHA={s["source_lock_sha256"]}。'
        f'完整实时所属命令{len(s["processes"])}；历史start={start}，PID仅该快照，下次必须核完整命令/-B/PPID/PGID/IO/fds。'
        f'实际新空间done={s["done_count"]}、raw={s["raw_count"]}、独立CPU回放={s["cpu_replay_count"]}、旧探针精确引用={s["reused_probe_count"]}；'
        f'全部done绑定SHA={s["all_done_bound_SHA_pass"]}。新32B/optimizer/time/overview均0。'
        '88是32原支持+56隔离探针的输入上限，预计53缺失真实新调用/3原8B缓存不是已完成调用；原32支持不重复生成，探针永不入生产支持集。'
        f'实时模型回执={model}；首个真实新空间探针独立CPU回放={first}。首CPU和全部已成功回放只引用、不重复；原CPU准备不是新生成。\n\n'
        'v1实际GPU装载后在任何生成前因默认requires_grad=True被原canonical validator拒绝，原17807锁/STOP/trace与103.09017407242209秒唯一failed账本保留，新raw0。v2只显式冻结base参数grad标志，实际CPU复现旧拒绝并核冻结前后参数字节相同；独立工程锁/单次launcher，原样本/预测seal/全88 native输入与G0成功原字节移交，不重复decoder或旧CPU验收。科学算法v1名称保持。实际Linux G0全量原资产17012绑定文件/28,510,589,351字节和固定模型文件SHA已验，'
        'V14原521时间回答/102470键与原31295空间锚点、NONTEST8原447键移交，'
        '原pinned线性正常回退41632整数框逐一恒等，新四支持provenance独立多项式与原11strict语义合成合同/6拒绝通过。'
        '元数据专用8来源组固定哈希选择已完成，前2工程后6确认；所有56个L/P预测在任何探针揭示前封存，'
        '本轮讨论全文不含入选videoID/sourceSHA，当前公式/门/样本无探针答案参与；历史缓存存在与既往被观察的限制明确保留。'
        '全部88实际nativeBGR/RGB/PNG与原空间processor前缀/tensor/input已CPU通过，'
        '新实际consumer再加载88份tensor与精确ratio指标/门/旧终态账本合同也通过。'
        'CPU不是新模型或质量；旧G0组件中pending字段按各自历史UTC解释，后续实际组件独立解除。'
        f'G0当前回执聚合={receipt_summary}。\n\n'
        f'GPU={s["GPU"]}，盘剩{s["disk_free_bytes"]}bytes，shared_active={s["shared_active"]}，'
        f'真实resource={s["resource"]}，ledger={s["GPU_ledger"]}。'
        '活跃费用待自然终态追加不能写0；原空间18723.876秒与7200offset保留。'
        'CPU SHA/顺解/加载/独立回放/共享队列/GPU闲可能合法，不能凭旧PID或缺回执认卡死。'
        f'当前G2报告={report}。根completion={s["stages"].get("completion.json")}。\n\n'
        '后续固定53缺失真实8B空间探针/逐请求独立CPU一次回放→全8组56相位精确有理数G2→'
        '仅G2通过NONTEST全源新场/固定447键/11strict/选中整数框改变→仅G0-G3通过唯一426全源CPU场/固定102470键/11strict/ZIP/独立final/全部真实GPU唯一账本。'
        '任何科学门失败本版NO_426/NO_EFFECT，保留所有分母与成本，不换组/降门/自动再换公式或重开C/B1/D/Q/65CE。'
        '同模型逐帧重建一致性不是构图真值、独立幻觉率或官网分，新官网分UNKNOWN。\n\n'
        'aic-linux ACTIVE每15分钟failed_runs_only静默；入口controller/checkpoint_spatial_gap8_slot4_v2.py，'
        '只读Linux、非原子组件各自UTC/集合保留，record保护全部历史files与production_files；'
        '当前运行冻结源码/成功raw/已通过CPU不改不重复，单次launcher不可重开。'
        '工程STOP保存raw/trace后独立新工程版本与exact成功引用，不能修改本锁。'
        '共享任务/锁/账本/SSH/Tailscale/代理/服务保持，不抢占外部、不读100confirm或手看复赛调参。'
        'Mac在线不参与，小量项目控制直SSH例外保持；新model/data/批量产物/ZIP大流量仍先说明方向字节链路机场消耗等许可。'
        '仅最终真实426全验收且GitHub小量筛选发布后，或本版有限证据耗尽形成真实结论，才一次通知并删除本监控、不归档。'
        '禁止逐帧/raw/探针答案/完整讨论/source_lock/resume/model/新ZIP发布，不自动回传或官网提交。\n\n'+MARKER+'\n\n')
    closed=RUN/'controller/SG8_scientific_stop_acceptance_20261009_summary.json'
    if closed.exists():
        a=json.loads(closed.read_bytes())
        assert a['status']=='PASS_INDEPENDENT_SG8_FINITE_NO_426_RAW_GATE_AND_ACCOUNTING'
        assert a['source_lock_sha256']==s['source_lock_sha256'] and not s['processes']
        assert s['done_count']==s['cpu_replay_count']==53 and s['reused_probe_count']==3
        publication=RUN/'controller/SG8_github_publication_receipt_20261009.json'
        monitor=RUN/'controller/SG8_monitor_closure_20261009.json'
        pub=json.loads(publication.read_bytes()) if publication.exists() else None
        mon=json.loads(monitor.read_bytes()) if monitor.exists() else None
        text=(f'## 20261009空间gap8 PCHIP本版有限证据闭环（实核{s["utc"]}，独立终态{a["utc"]}）\n\n'
            '当前NO_426_FINITE_SG8_EVIDENCE_COMPLETE，53次真实新8B空间生成、53份独立CPU回放、3条旧exact探针引用，'
            '完整8来源组/56相位/原32支持保持、探针不入生产支持，工程失败0。'
            f'确认仅{a["confirmation_positive_groups"]}/6组为正，至少4/6门未通过；'
            f'确认均值{a["confirmation_mean"]["display_float"]}，全8均值{a["all8_mean"]["display_float"]}，'
            '确认留一门也失败。独立原raw/原parser/有理数多项式、全部18104冻结SHA、全量分母和账本验收一致。'
            f'私有独立验收controller/SG8_scientific_stop_acceptance_20261009.json SHA{a["private_receipt_sha256"]}，'
            f'原reportSHA{a["report_sha256"]}。\n\n'
            '真实GPU v2自然completed/exit0/stop_reason null、charge495.22363770753145秒，唯一ledger165/原7200offset保持。'
            'v1生成前requires_grad准入故障保留原STOP/锁/raw0及failed/exit1/null/103.09017407242209秒费用；'
            'v2仅冻结grad标志、参数字节不变，真实8B基座SHA及8767123696参数/adapterOFF已验。'
            '原空间18723.876秒成本保持。新32B/optimizer/time/overview均0，本次验收无新decoder/processor/model调用，'
            '全部成功及CPU回放不重跑，所属完整命令0/共享active null是自然终态。\n\n'
            '本版NO_426：未进入真实NONTEST全源新场或426，也没有新最终ZIP；G0合成11strict不当真实NT/426终态。'
            '更好包目标尚未实现。停止本配方，不换组/降门/改公式补考，不自动接均衡窗或旧C/B1/D/Q/65CE。'
            '原最佳B37.63及旧包SHA86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54保持；'
            'V14用户低.03仅推算约37.60，不是新官方核验。同模型一致性不是构图真值或官网分。'
            '下一次质量路线需要合法可用、来源隔离的原生目标比例独立构图参考；现有参考不足，不盲训练或下载。\n\n'
            '重新一锅炖与GPT-6 sol网页席位已完成，Pro研究项目本轮1/5（累计slot4/8），余4次保留，不为知会耗用。'
            '最终讨论final-decision-v2.md及全部历史讨论、原source_lock files/production_files/raw/UNKNOWN/成功和费用保持。'
            f'筛选GitHub实际发布回执={pub}。监控关闭回执={mon}。'
            '仅本任务core/协议/工程聚合发布，未导出逐帧/探针raw/完整讨论/source_lock/resume/model/ZIP；'
            '无自动回传或官网提交。本版结束后删除aic-linux，不归档。\n\n'+MARKER+'\n\n')
    targets=[RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md',RUN/'spatial_gap8_pchip_slot4_v2/CONTINUE.md',
        RUN/'controller/spatial_gap8_slot4_handoff_latest.md',RUN/'controller/SPATIAL_GAP8_SLOT4_EXECUTION_20261009.md']
    for lp in RUN.glob('*/source_lock.json'):
        lock=json.loads(lp.read_bytes())
        for key in ('files','production_files'):
            values=lock.get(key,{})
            paths=values if isinstance(values,dict) else [r['path'] for r in values]
            for path in paths:
                normal=str(path).replace('\\','/')
                for p in targets:
                    suffix=('/'+p.name if p.name in ('AGENTS.md','STATUS_AUTOPILOT_20261007.md')
                        else '/'+str(p.relative_to(RUN)).replace('\\','/'))
                    assert not normal.endswith(suffix),'local handoff protected'
    for p in targets:
        before=p.read_text(encoding='utf-8') if p.exists() else ''
        if p.name in ('AGENTS.md','STATUS_AUTOPILOT_20261007.md'):
            if MARKER in before:before=before.split(MARKER,1)[1].lstrip('\n')
            value=text+before
        else:value='# 唯一新路线接续：spatial_gap8_pchip_slot4_v2\n\n'+text
        p.write_text(value,encoding='utf-8')
    payload=(RUN/'spatial_gap8_pchip_slot4_v2/CONTINUE.md').read_text(encoding='utf-8')
    remote('''import json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);p=r/'spatial_gap8_pchip_slot4_v2/CONTINUE.md'
for lp in r.glob('*/source_lock.json'):
 v=json.loads(lp.read_text())
 for k in ('files','production_files'):
  x=v.get(k,{})
  names=x if isinstance(x,dict) else [i['path'] for i in x]
  assert str(p) not in {str((lp.parent/n).resolve()) for n in names},'CONTINUE frozen'
p.write_text(%r,encoding='utf-8')
print('PASS_UNBOUND_CURRENT_CONTINUE_UPDATE')
'''%(REMOTE,payload),echo=False)
    print('PASS_PRIVATE_SG8_RECORD',s['utc'],stage)

if __name__=='__main__':main()
