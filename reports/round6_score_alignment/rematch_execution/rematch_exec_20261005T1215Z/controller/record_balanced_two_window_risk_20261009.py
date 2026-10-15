"""Write current private handoff only outside every historical source lock."""
import json
from register_b2_package_v1 import RUN,REMOTE,remote

MARKER='<!-- END_CURRENT_BALANCED_TWO_WINDOW_RISK -->'
def main():
    s=json.loads((RUN/'controller/monitor_balanced_two_window_risk_v1/latest.json').read_bytes())
    stage=(s['stages'].get('progress.json') or {}).get('stage') or 'CPU_PREPARATION'
    text=(f'## 20261009 用户明确接受风险后的双窗均衡实验（实际{s["utc"]}）\n\n'
        '用户最新明确要求按照讨论方案执行并打包ZIP，“本来我们就是在试的”。'
        '因此独立执行balanced_two_window_risk_v1，保留上一轮Pro/主控G0止步意见与所有历史STOP，'
        '不把用户接受风险说成独立质量证据或旧科学门通过。讨论已完成，本次不为知会再耗Pro，余3次。\n\n'
        '仅原恰好两窗且30<总域<60秒改为精确Fraction中点的等长两窗。原B8B/288adapter、B0 prompt、'
        '0..5 grammar/greedy/floor64/nativePTS/source97色彩白名单/16384input/256output/原像素预算保持。'
        '原B已训练，此路线新optimizer0、新32B/overview/空间模型0；不编造微调。'
        '新窗口、采样、时间选择独立实现，失败不转空、不补证据/裁段/并集或epsilon。\n\n'
        f'当前stage={stage}；完整实际owned命令{s["processes"]}。身份仅本UTC快照，下次必须实核完整命令/-B/PPID/PGID/IO/fds。'
        f'新计划prepared={s["stages"].get("prepared.json")}。'
        'NONTEST8原8窗全部exact引用；非测试104/96组/112窗中16变化真实新调用；完整426/521中116变化真实新调用、405原V14成功exact引用。'
        '这些是计划分母，完成数以各scope实际回执为准。'
        f'当前scope={s["scopes"]}。首真实CPU回放={s["stages"].get("first_real_acceptance.json")}。'
        '已成功生成/已完成CPU回放只引用，不重跑；旧PCHIP/C/B边界/B1/D/Q/65CE/160及全部raw/UNKNOWN/旧成本不回写。\n\n'
        f'锁SHA={s["source_lock_sha256"]}，冻结文件{s["frozen_files"]}，冻结全SHA={s["all_frozen_sha_pass"]}，'
        f'新done全部绑定SHA={s["all_new_done_bound_sha"]}。'
        f'真实GPU={s["GPU"]}，disk剩{s["disk_free_bytes"]}bytes，共享active={s["shared_active"]}，ledger={s["ledger"]}，费用回执={s["resources"]}。'
        '活跃作业费用待自然终态追加，不能记0；旧7200offset/原空间18723.876秒/V14全部真实训练推理费用保留。'
        'CPU SHA/顺序解码/模型加载/独立回放或队列可能合法，不据GPU闲/旧PID判卡死。\n\n'
        f'根completion={s["stages"].get("completion.json")}；工程failure={s["stages"].get("execution_failure.json")}。'
        '后台NT8完整11strict→开发16真实生成及独立CPU→426的116真实生成/405exact及全112?以521完整分母核验→全部新请求独立CPU→完整原空间源场exact→426全11strict/ZIP/独立final/全部GPU唯一终态账本。'
        '无独立质量参考，弱方向不作为本次用户接受风险的阻止条件，不据结果改配方；新官网分UNKNOWN，可能低于旧最佳37.63。'
        '仅最终完整真实验收和GitHub筛选同步后交付。包留Linux，不自动回传或官网提交。\n\n'
        '每15分钟静默接续，只写项目；工程异常保存原trace/raw/成功后独立新版本修复，不改冻结文件或重复launcher。'
        '共享任务/锁/连接/代理/服务保持，Mac在线不参与，既有小量项目控制直SSH授权保持；新model/data/批量产物/ZIP大流量仍须方向字节链路机场消耗说明和许可。'
        '不读100confirm、不手看复赛调参、不本地复刻官网分。仅允许GitHub core/协议/聚合/真实包路径大小SHA，不导出raw/逐帧/完整讨论/弱标签/整source_lock/resume/model/ZIP。\n\n'+MARKER+'\n\n')
    text=text.replace('及全112?以521完整分母核验','并以521完整分母核验')
    targets=[RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md',RUN/'balanced_two_window_risk_v1/CONTINUE.md',
        RUN/'controller/BALANCED_TWO_WINDOW_RISK_EXECUTION_20261009.md']
    for lp in RUN.glob('*/source_lock.json'):
        lock=json.loads(lp.read_bytes())
        for k in ('files','production_files'):
            values=lock.get(k,{})
            for path in (values if isinstance(values,dict) else [r['path'] for r in values]):
                normal=str(path).replace('\\','/')
                for p in targets:
                    suffix='/'+p.name if p.name in ('AGENTS.md','STATUS_AUTOPILOT_20261007.md') else '/'+str(p.relative_to(RUN)).replace('\\','/')
                    assert not normal.endswith(suffix),'protected historical handoff: '+str(p)
    payload='# 唯一入口：balanced_two_window_risk_v1\n\n'+text
    remote('''from pathlib import Path
import json,socket
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);p=r/'balanced_two_window_risk_v1/CONTINUE.md'
for lp in r.glob('*/source_lock.json'):
 v=json.loads(lp.read_bytes())
 for key in ('files','production_files'):
  x=v.get(key,{})
  paths=x if isinstance(x,dict) else [row['path'] for row in x]
  assert str(p) not in paths,'remote continuation frozen'
p.write_text(%r,encoding='utf-8')
print('PASS_UNBOUND_BALANCED_HANDOFF')
'''%(REMOTE,payload),echo=False)
    for p in targets:
        before=p.read_text(encoding='utf-8') if p.exists() else ''
        if p.name in ('AGENTS.md','STATUS_AUTOPILOT_20261007.md'):
            if MARKER in before:before=before.split(MARKER,1)[1].lstrip('\n')
            value=text+before
        else:value=payload
        p.write_text(value,encoding='utf-8')
    print('PASS_CURRENT_USER_ACCEPTED_RISK_HANDOFF',s['utc'],stage)
if __name__=='__main__':main()
