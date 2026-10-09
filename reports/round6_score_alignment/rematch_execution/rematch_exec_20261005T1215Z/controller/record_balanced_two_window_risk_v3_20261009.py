"""Write current private handoff only outside every historical source lock."""
import json,hashlib
from register_b2_package_v1 import RUN,REMOTE,remote

MARKER='<!-- END_CURRENT_BALANCED_TWO_WINDOW_RISK_V3 -->'
def main():
    snapshot=RUN/'controller/monitor_balanced_two_window_risk_v3/latest.json'
    s=json.loads(snapshot.read_bytes())
    later_path=snapshot.with_name('latest_runtime.json')
    later=json.loads(later_path.read_bytes()) if later_path.exists() else None
    if later and later.get('full_frozen_verification_reference',{}).get('sha256')!=hashlib.sha256(snapshot.read_bytes()).hexdigest():later=None
    live=(later.get('progress.json',{}).get('value') or {}) if later else (s['stages'].get('progress.json') or {})
    stage=live.get('stage') or 'CPU_PREPARATION'
    owned=later['processes'] if later else s['processes']
    component_time=later['utc'] if later else s['utc']
    later_text=(f'实际较晚运行组件={later}。此组件与完整冻结核验分开读取，原UTC和集合保持；不把较早CPU阶段覆盖较晚GPU阶段，不把晚读组件冒称重新冻结验收。' if later else '')
    text=(f'## 20261009 用户明确接受风险后的双窗均衡实验（实际{s["utc"]}）\n\n'
        '用户最新明确要求按照讨论方案执行并打包ZIP，“本来我们就是在试的”。'
        '因此独立执行balanced_two_window_risk_v3，保留上一轮Pro/主控G0止步意见与所有历史STOP，'
        '不把用户接受风险说成独立质量证据或旧科学门通过。讨论已完成，本次不为知会再耗Pro，余3次。\n\n'
        '工程v1在模型启动前因可变freeze.cpu.log被绑定而拒绝，原锁/失败trace保留，原始首轮stdout随后被失败核验输出覆盖，此事实保留；v1新模型0。'
        'v2仅排除日志冻结及独立作业身份，132个实际native decoder/processor/精确域CPU成功与科学代码原字节移交，cpu_acceptance SHA cc6117d720ad8c472ed60c48f79ff22640dbf54395242f6c737a38bf5b342fdf。'
        '不重复132CPU准备。v2首真实回答因list/tuple表示比较误拒绝，实际整数范围相等，raw SHA2c64ed0bbbb56271b15f41ca55a4e95309326ff8d084a4a077bfd348b4a07541保留；v2自然failed/exit1/null/144.4350819280371秒唯一账本保留。v3修表示及独立exact恢复，原有效raw仅一次独立native/processor/token/原parser CPU回放后移交，不重复模型；原NT8完整11strict与ZIP原字节移交，不重复成功NT assemble/finish。v3计划15开发新+1原真实恢复+96旧exact，116复赛新+405exact；科学全路线新132、本版新131、optimizer0。新静默15分钟监控automation id=aic，旧aic-linux已删除，不复活旧launcher。\n\n'
        '仅原恰好两窗且30<总域<60秒改为精确Fraction中点的等长两窗。原B8B/288adapter、B0 prompt、'
        '0..5 grammar/greedy/floor64/nativePTS/source97色彩白名单/16384input/256output/原像素预算保持。'
        '原B已训练，此路线新optimizer0、新32B/overview/空间模型0；不编造微调。'
        '新窗口、采样、时间选择独立实现，失败不转空、不补证据/裁段/并集或epsilon。\n\n'
        f'当前stage={stage}；命令组件UTC={component_time}；完整实际owned命令{owned}。身份仅本UTC快照，下次必须实核完整命令/-B/PPID/PGID/IO/fds。'
        f'新计划prepared={s["stages"].get("prepared.json")}。'
        'NONTEST8原8窗全部exact引用；非测试104/96组/112窗中16变化回答（15本版新+1原真实恢复）；完整426/521中116本版新回答、405原V14成功exact引用。'
        '这些是计划分母，完成数以各scope实际回执为准。'
        f'完整快照各scope读取集合={s["scopes"]}。首真实CPU回放={s["stages"].get("first_real_acceptance.json")}。'
        f'{later_text}'
        '已成功生成/已完成CPU回放只引用，不重跑；旧PCHIP/C/B边界/B1/D/Q/65CE/160及全部raw/UNKNOWN/旧成本不回写。\n\n'
        f'锁SHA={s["source_lock_sha256"]}，冻结文件{s["frozen_files"]}，冻结全SHA={s["all_frozen_sha_pass"]}，'
        f'新done全部绑定SHA={s["all_new_done_bound_sha"]}。'
        f'真实GPU={s["GPU"]}，disk剩{s["disk_free_bytes"]}bytes，共享active={s["shared_active"]}，ledger={s["ledger"]}，费用回执={s["resources"]}。'
        '活跃作业费用待自然终态追加，不能记0；旧7200offset/原空间18723.876秒/V14全部真实训练推理费用保留。'
        'CPU SHA/顺序解码/模型加载/独立回放或队列可能合法，不据GPU闲/旧PID判卡死。\n\n'
        f'根completion={s["stages"].get("completion.json")}；工程failure={s["stages"].get("execution_failure.json")}。'
        '后台原NT8完整11strict exact移交→开发15新+1原真实恢复及全部16独立CPU→426的116真实生成/405exact并以521完整分母核验→全部新请求独立CPU→完整原空间源场exact→426全11strict/ZIP/独立final/全部GPU唯一终态账本。'
        '无独立质量参考，弱方向不作为本次用户接受风险的阻止条件，不据结果改配方；新官网分UNKNOWN，可能低于旧最佳37.63。'
        '仅最终完整真实验收和GitHub筛选同步后交付。包留Linux，不自动回传或官网提交。\n\n'
        '每15分钟静默接续，只写项目；工程异常保存原trace/raw/成功后独立新版本修复，不改冻结文件或重复launcher。'
        '共享任务/锁/连接/代理/服务保持，Mac在线不参与，既有小量项目控制直SSH授权保持；新model/data/批量产物/ZIP大流量仍须方向字节链路机场消耗说明和许可。'
        '不读100confirm、不手看复赛调参、不本地复刻官网分。仅允许GitHub core/协议/聚合/真实包路径大小SHA，不导出raw/逐帧/完整讨论/弱标签/整source_lock/resume/model/ZIP。\n\n'+MARKER+'\n\n')
    targets=[RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md',RUN/'balanced_two_window_risk_v3/CONTINUE.md',
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
    payload='# 唯一入口：balanced_two_window_risk_v3\n\n'+text
    remote('''from pathlib import Path
import json,socket
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);p=r/'balanced_two_window_risk_v3/CONTINUE.md'
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
