from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'rematch_execution'/'rematch_exec_20261005T1215Z'
OLD=HERE.parent/'aic_video_continue_20261009'/'context-final-metadata.md'
def sh(data):return hashlib.sha256(data).hexdigest()
intro='''# AIC 更好可提交包：重新完整讨论 r00
连续任务ID：AIC-VIDEO-REMATCH-NEXT-20261005；新讨论：20261009-replan-r00。
用户原话：“重新按照一锅炖技能去讨论，然后网页版你换成gpt6sol，这个技能你改一下，然后pro这次我给你五次额度，务必出一个很好的方案能提交好包，去讨论吧”。
历史Pro已用3次，现明确新增最多5次、累计上限8；原预算簿保留。本卷旧文中“Pro额度0”仅指历史，本轮不再适用。Sol当前指定GPT-6 sol，高模式；Pro只能Chrome网页既有研究项目内。Tibo/Grok仍按技能固定席位；Gemini指定3.8 Flash扩展，若UI不可用如实记录，不能冒称参与。

## 当前目标与事实优先级
请先读本节和最后新增证据，再读中间全部历史卷宗。历史建议只是历史；本轮目标是形成有新信息价值、能实际实施并产一个合规完整426视频ZIP的最好有限路线，不能许诺未知官网分。用户已授权主控后续自主接手，但不得用讨论意见绕过流量、共享资源、数据许可或平台规则。
最佳旧B37.63只绑定旧ZIP 86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54。V14用户反馈比最佳少0.03，37.60仅推算；V14使用原B权重，实际15次新训练更新发生但弱开发选回epoch0原B。教师32B是推理弱监督，不是32B微调。
本轮前所有已登记有限探索均自然完成、工程0失败、科学拒绝。没有新426包，没有仍在跑的作业，旧监控已真实删除不归档。不能将旧失败改名通过或重新跑已成功生成/CPU验收。
只共享已许可项目协议、必要代码、历史AI可见意见、聚合工程/科学证据；不附视频、逐帧manifest/hash表、教师raw/弱标签逐行、账号凭据、私人浏览内容。媒体级独立真值未提供，语义幻觉率UNKNOWN。
原模型在Linux原地，8B生产逻辑参数8782459120/288adapter，总推理参数<=9B。共享GPU资源动态核验，不固定机器额度，不抢占外部任务/改连接服务/账本7200offset。100confirm不读、不手看复赛/测试调参、不本地复刻官网总分。任何新模型/数据/批量产物/ZIP大传输先说明方向字节链路与可能机场消耗并等许可。

## 全部旧路线实际终态（不是新增实验建议）
|路线|完整真实结果|弱参考方向/科学结论|
|V14弱监督学生|160标注+160盲选，65train/14dev，UNKNOWN81；15optimizer/195backward/4prefix/288独立CPU重载|原B与epoch1弱dev同分.3786251362162477，epoch2/3更低，按登记选epoch0原B；426旧新包已交付，用户-0.03|
|C-advisory|104文件/96组/112窗，104粗览全部合法空表，R/X集合全同；626成功包括NT48/pilot154|all104 R-B0 +.01259764737522522/R-N +.0013798519386831974；expanded72 R-B0 +.010946200100208966/R-N -.000582455299541034；原四方向门拒绝，没有C426|
|32B边界matched诊断|固定16事件42contexts全成功，完整CPU回放，自然server停止|仅3/16全部context唯一弱时间重叠，same-event语义UNKNOWN；固定外部方向2条都负，macro-.11320021399718093；拒绝边界训练，不挑3条|
|历史B1耦合prompt+1..5grammar|原26成功精确复用+新86成功，完整104/96/112及CPU|all104 -.009816273304981254，expanded72 -.01620639512922189；49集合改变/21组下降；原门拒绝，不是旧37.63包精确复现|
|D嵌套密度|原floor64+相邻间隔中点<=127帧，同总像素预算、空间grid有取舍；NT8+112开发全成功/CPU|all104 -.0011019550696133747，expanded72 -.008962509660797473；82集合改变/37组下降；原门拒绝|
|Q内部nearest64|NT8+102变化开发新调用/原10输入完全相同引用，samecount/firstlast/grid，原nativePTS端点不变；全部CPU|all104 +.0028675084249248947，CI[-.03560765390434146,.038973738491221696]；expanded72 -.011370797431947438，CI[-.05964563371762155,.03140317901040649]；40集合改变/16组下降，原门拒绝|
原所有STOP、raw、冻结锁、已成功调用/验收及GPU成本永久保持。C/B1/D/Q相对豆包104的闭世界集合一致性只曾作行政投入排序，覆盖/人工真值/真实质量UNKNOWN；不能由差值称官网改善或证明整条机制无效。
合格独立portrait构图参考inventory0，不拿旧16:9crop/模型框当构图真值。当前生产空间是B2同8B基座全源场31295锚点，时间筛选后复用，旧成本保留。新空间算法变化就不能冒称exact缓存复用。

## 主控初始独立意见（在读本轮其他席位新答复前写入）
我的首要诊断是决策证据不足：同教师盲一致不是真值，豆包覆盖未知，开放104/96已反复被观察。继续换prompt、采样细节、密度并看同一弱指标有多重比较和自我过滤风险。应保留所有旧门结果，独立登记新的选择程序，而不是事后放行旧C/Q。
优先考虑两个尚需裁决的方向：A）重建可审计的独立非测试评价/任务对齐（若已有许可训练/开发标注可核身份，或盲审固定非测试分歧，避免未知区域当负），再选择一个有方向依据的机制；B）生产机制审计，尤其时间/空间分离、目标比例、镜头边界插值和尺度的真实上限，先找具体可复现损失，不能凭几何示例硬设阈值。若没有任何新增可靠质量信号，宁可明确有限风险的一次新候选、保护37.63，也不要承诺涨分或无限开模型/阈值扫。
我不预先指定训练：65弱样本CE和旧160不重开；若有新的独立监督，应先证明数据/任务/输入同一和真正新信息，单独冻结。32B/GPU工程可用不能代表监督可信。也不把反复复用空间场自动当作正确空间。
最强反例：新评价仍只是另一模型的偏好，被误叫独立真值；方案弱指标更好却丢掉真实短高光。另一反例：只因微小扩展组差值为负停止全部方案，会让决策永远无法交付；但解除历史门又是结果驱动。需要Pro裁决新的前瞻有限投入规则，清楚区分可交付工程门与质量证据/风险，不能改旧合同。

## 本轮各席必须回答
1. 依据新增完整终态，哪些旧建议被真正证伪，哪些只是缺信息？不要再推荐已完成C/B1/D/Q或42边界重跑。
2. 当前最可能限制质量的是数据/定义/评价、时间决策、空间构图、生产混杂还是其他？请列强反例，区分事实/推断/未知，不靠模型投票。
3. 重新设计一条最有新信息价值且主控能自主完成的有限路线；给精确数据来源许可/输入/监督与未知掩码/产物/独立控制/CPU与真实非测试验证/训练必要性/实际成本预测方法/停止门/完整426交付门。不能只给“大量高质量标注”“换更大模型”等不可执行口号。
4. 审查原闭世界弱参考零方向投入门的适用性。可建议新前瞻程序，但旧STOP和结果不可回写。如何避免既永远拒绝又盲产包？若风险包值得做，清楚说明新增机制和先验证什么，不保证分数。
5. 提出你最反对主控/历史Pro/其他席位的具体一项，说明可证伪检查。首轮独立，下一轮读取所有原文交叉批判，再向Pro做关键裁决。本轮Pro新增五次仅上限，不为耗尽额度闲聊。
完整信息包很长；请工具完整分段读取，若工具截断补读，不把显示截断说成文件缺失。回复首部确认任务ID、r00/文件、实际读取范围及关键约束。不要索要私有思维链，只提交可分享论据与结论。

---
# 前次完整卷宗原文（322401字节，原始内容保持）
'''
sources=[ROOT/'controller'/x for x in ['CONTEXT_ADVISORY_EXECUTION_20261009.md','B_BOUNDARY_EXECUTION_20261009.md','B_PROMPT_RECOVERY_EXECUTION_20261009.md','NESTED_DENSITY_EXECUTION_20261009.md','NATIVE_ROUND_ALIGNMENT_EXECUTION_20261009.md','NRA_scientific_stop_acceptance_20261009_summary.json']]
sources += [ROOT/'native_round_alignment_v1'/x for x in ['PROTOCOL.md','nr_native.py','nr_report.py','packager.py']]
parts=[intro,OLD.read_text(encoding='utf-8-sig'),'\n# 新增完整已许可证据与必要代码\n']
inventory=[]
for p in sources:
    data=p.read_bytes();inventory.append(dict(path=str(p),bytes=len(data),sha256=sh(data)))
    parts += ['\n## 来源 '+str(p.relative_to(ROOT))+'\nSHA256 '+sh(data)+'\n\n````'+('python' if p.suffix=='.py' else '')+'\n',data.decode('utf-8-sig'),'\n````\n']
parts+=['\n# END_REPLAN_R00\n本轮原始用户目标、主控独立立场、全部历史讨论及新终态已合并。没有本轮其他席位答案；首轮必须独立。\n']
packet=HERE/'context-r00.md';data=''.join(parts).encode('utf-8');packet.write_bytes(data)
(HERE/'packet-r00-receipt.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),path=str(packet),bytes=len(data),sha256=sh(data),lines=data.count(b'\n'),prior_full_packet_sha256=sh(OLD.read_bytes()),sources=inventory),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(path=str(packet),bytes=len(data),sha256=sh(data),lines=data.count(b'\n')),ensure_ascii=False))
