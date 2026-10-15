"""Local, reviewable full discussion packets; no model or browser calls."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
RUN = PROJECT / 'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
OLD = HERE.parent / 'aic_video_rematch_20261005T1044Z'
TASK = 'AIC-VIDEO-REMATCH-NEXT-20261005'

def digest(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def section(title, path, language=''):
    return '\n\n## ' + title + '\n\n来源与字节身份：' + json.dumps(digest(path), ensure_ascii=False) + '\n\n```' + language + '\n' + path.read_text(encoding='utf-8-sig') + '\n```\n'

base = '''# AIC 视频高光剪辑：37.63之后的下一轮决策（完整允许共享卷宗）

连续任务ID：AIC-VIDEO-REMATCH-NEXT-20261005。接续版本：20261009-r00。
主控：当前Codex执行Agent，也是正式参与者。
Pro预算：本连续议题已在Chrome“研究”项目实际得到3次完整回答，旧簿只登记1次，另2次用户手动请求现按网页原文补记；剩余0。本轮不向Pro新增发问，按技能额度用尽条款由主控兜底裁决，不伪称新Pro认可。
共享边界：本文件是用户明确调用ai-yiguodun所授权的任务上下文、核心代码、协议、聚合结果与外部AI历史可见论据。未共享视频、权重、逐帧预测、教师raw或弱标签、凭据、网络配置、100confirm；这些缺失意味着外部参与者不能独立重新审视频语义，不能声称拥有人工真值。

## 1. 当前用户原始诉求与授权

用户：刚才那个包我上传了，比我们最佳少了0.03分，所以还是要探索一个更好的包。现在修改一锅炖skill，Pro必须在网页“研究”项目进行对话；调用skill讨论后续路线，制定方案之后主控去执行，全程主控负责棘手难题，自主持续工作，用户去睡觉。
已有最高分37.63，最新差值-0.03是用户本轮回报，所以37.60为据此计算值；本轮尚未读取官网这条新记录，不能假称独立官网核验。该差值只绑定V14 ZIP 95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2，308278字节。37.63仍绑定旧B ZIP 86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54。B2 37.32绑定旧包0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3、317401字节。4B33.81/Mac33.46分别属于旧包。禁止移花接木。
目标：探索真正不同且有科学依据的完整候选，之后由用户获得新的官方排序结果；不承诺一定超过37.63，更不保证50分。用户已授权执行新的科学/工程方案，无需逐步确认。任何新大流量模型/数据/批量产物传输仍要说明方向、实际字节、链路、可能机场消耗并等许可。现有32B/8B均Linux原地，小量控制SSH已授权，Mac退出不参与关键路径。
硬边界：不读100confirm，不手看复赛视频或个别测试预测来调参，不本地复刻官方总分。允许必要的开放104视频/96源开发诊断，但必须同production，并如实标注旧弱标签的局限；不拿弱F1/CI>0作工程硬门。全量测试只执行冻结的、非测试先验证的算法，不给网页模型测试内容。共享机器动态实际容量/峰值/冲突判断，无人为固定利用率/显存/磁盘门；保留GPU锁、追加账本7200历史offset和外部任务，不抢占/终止外部任务，不改连接代理服务。
旧运行冻结源码、成功回答、错误raw/STOP和已验收成果保持。新配方用独立目录/协议/锁，单次启动并真实监控父子PGID、费用终态。CPU/启动/复用/计划不能冒充新模型生成、训练或最终ZIP。

## 2. 已真实完成的结果与限制

V14已完整验收：NONTEST8和426复赛各11独立strict全true；426源/521时间窗，时间无效0；102470预测帧；ZIP CRC通过、单一predictions.jsonl、426身份和原字节匹配。最终独立验收状态PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING，证据SHA f8f17dcad75dd96ff0ddcc89caf9f6531ebdcb9e0965fae81a7d4236c2ecc027。Linux包也已经授权回传Windows并逐SHA/CRC/426身份再核；用户现在报告线上少0.03。工程验收证明格式和执行真实，不证明高光语义或官网提升。
32B是Qwen3-VL-32B-Instruct Q4_K_M加F16视觉projector，用于推理弱监督；没有微调32B。160标签/160盲第二选择工程失败0。弱支持正65(train55/dev10)、空14(train10/dev4)、UNKNOWN81，全160原128train/32dev分母保留。实际训练65、开发14；同教师两次一致只是弱证据，不是人工真值；UNKNOWN不作负，正区间补集不当负。
8B确已从最佳B LoRA续训3epochs、15次optimizer更新、195样本反向；有限loss/grad、144A+144B共288张量逐更新改变；基座视觉冻结，prefix4同optimizer/RNG/scheduler继续及独立CPU288adapter重载通过。lr1e-5/r16/alpha32/dropout.05/有效batch16。弱14dev macro时间F1：B epoch0=0.3786251362162477；epoch1完全相同；epoch2=0.3596785770535768；epoch3=0.36453995670744305。按预登记同分取更早规则，实际选epoch0原B，trained_candidate_selected=false。新训练确实发生，但新权重没胜出；这不是T提升。旧B本来完成过5epochs/227更新，此次15更新单独记录。
被选adapter SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23；时间启用B LoRA，空间同8B基座无adapter，合计逻辑参数8782459120（8767123696基座+15335424 adapter），共享基座只计一次。V14新时间8+521窗实际生成；空间31295原锚点/全源234158帧的完整场，仅全算法/源/模型/请求/clock/全部SHA一致后复用，空间新调用0，保留原约18723.876秒成本。先全源插值再时间过滤。V14实际GPU charge训练2231.7791278334334、NONTEST时间164.55463389214128、426时间5430.027779461816秒；都真实completed/exit0/null及唯一追加账本，不能用单段生成wall代替费用。
输入：所有分支native PTS/floor64/顺序PyAV真实RGB、max16384、不截断；教师/学生局部自然30秒，V14提示NEXT_ROUND_0_TO_5、greedy约束JSON；原最佳B/B2提示历史1..5强制至少一段，包输出/提示/clock等配方差异不得由权重相同推定包同。空间0..1000整数框/完整源场/失败与合法空分离/全部分母保持。
CPU修复已完成：教师B边界与F物理证据独立编号；有限状态GBNF保留全部合法1..5顺序不重叠半开段及每段模型自选非空证据；program只映射真实PTS，不补证据/裁段/合并/排序修补/造空。probe/all/review阶段移交、canonical键排序、validator metadata部署、原pilot24 diagnostic_only=True完整160精确manifest跨阶段准入均已修；旧flag/raw/STOP保持，成功调用不重复。端点canonical float duration修复无epsilon/裁值。单一97源log316转换仅精确SHA/profile白名单，YUV/PTS不变、临时transfer UNSPECIFIED恢复原metadata，不换任意decoder。
历史科学失败也保留：v7 12/12全正、0空、弱复查10支持2拒；context3 8/8工程有效、3正支持/唯一NO拒，受支持空0，且教师声称粗览仅至119秒的可证实错误（实际overview尾约149.98秒、13帧>=120）与其他语义异议同时存在，不翻整个拒绝。后来V11新局部BF接口24标注/24盲选择0工程失败，弱正8/空4/UNKNOWN12、9近整窗，完整160才得到79受支持。不是靠无限换prompt凑空样本。

## 3. 下一步候选及主控初始独立立场（尚未读本轮他人意见）

主控倾向：不要再延长同65弱样本CE训练或强行选择较晚epoch；把新的实验集中到一个有机制变化的非测试matched对照。优先考虑原Pro路线C同8B全源粗览事件表→局部精确定位，原B负责局部；另保留原Pro路线B候选边界精修的竞争意见。空间可能更影响总分，但仅0.03总差无法辨别；应先做空间链可解释诊断，不能从总分推导测试真值。保护37.63旧包，并在比较时保留同输入本次B控制，避免用不同历史clock/prompt成本当因果结论。
候选C：同基座全源64帧粗览产出少量可见事件/粗位置，局部30秒再用原B精确定位；不新下载、不微调，新增上下文改变需独立协议。风险粗览漏掉短事件、幻觉把局部带偏、长源丢失上下文、token预算；须用非测试matched对照明确增量。如何测幻觉/遗漏/边界且不靠同教师自证，如何锁完整24或8非测试先验门，需讨论。
候选B：原B提区间，32B只确认局部事件和边界，独立小adapter学习边界，不教完整拒绝器、候选外未知不负。风险同教师不可靠、机会成本、两个adapter要计总参数（基座一次、两个LoRA每个15335424依然小于9B但实测核）。应先真实非测试边界matched证据，再决定训练。
候选D：后置时间查询二元网格头，第一Pro偏好但负格与coverage语义一直未可靠；现79整窗弱支持是否足够不能武断，需要帧格可证实监督域、真实grad流和同production评估。风险小数据过拟合和语义域误标，不能无覆盖把UNKNOWN当负。此轮是否继续推D值得反对。
候选S：同8B空间基座/目标比例感知crop重新设计或空间LoRA。不假定全场复用质量等于最优；但暂缺可信ROI真值及纯空间控制。先用非测试明确可见主体/目标比例/锚点和插值稳定性，保留模型成本、全部空间分母和合法空。禁止靠删难例、统一放大框、名义合法而错误ROI来冲分。
候选E：保持同最佳B，调空输出/采样/边界后处理。禁止盲阈值扫与测试内容调参；可提出有机制理由的少量事前候选，工程规则对比须和原生产同输入。重复生成原成功配方无科学收益；仅修证实工程错才用独立版本。不能为了不同ZIP随意换seed。
主控最强反例：C的64全源帧可能比原局部更稀，所添事件文本有误且训练时未见，会恶化选择；14弱dev很小且同教师源，不能作为C整体优越的真值。B也可能把候选缺失永久固化。需要各席提出最小可证伪对照，而非从37分到50分愿望倒推承诺。

## 4. 资源和科学验收

最新只读2026-10-08T16:19:25UTC hostname核inspur-NP5570M5，RTX6000Ada46GB、GPU0%/182MiB，RAM可用126211743744字节，盘剩191055884288字节。这只是瞬时容量，进实验前还须完整核共享锁/实际命令/外部任务。模型原地有8B和32B；环境冻结不升级。此前全426时间约1.5h GPU费用，空间复用合法才0新空间调用，原5.2h仍引用。全源额外粗览相当于每源再一模型调用，实际token/CPU顺解成本小试测量后外推，无写死人为配额。
最终候选须NONTEST8/426各11项独立strict、所有521时间窗及426身份、ZIP实际大小/SHA/CRC/仅一predictions.jsonl/原字节/资源账本完整才能叫可交付。质量诊断和工程strict分离。未官方提交前新分未知，只用户回传官网总分作整包排序信息；不自动官网上传，不通过多数票证明优越。

## 5. 本轮请各普通席独立回答

请首部确认连续任务ID、接续版本、context-r00.md与实际可读范围，至少复述：37.60为用户差值推算/最佳37.63保留、已真实15更新但选原B、81UNKNOWN不负、9B/原地模型/无测试内容调参/Pro3次已尽。缺失文件阅读请直说，别用本地路径假称阅读。
给一个优先主案、一个后备，并指出最强反例。不要迎合主控；明确事实/推断/未知/建议。比较C/B/D/S成本和可归因证据；提出今晚Linux可具体实现的非测试matched对照，允许试出不提高但不无意义再训练。给可测字段、样本来源与固定选择、工程门与科学go/no-go、完整包如何形成、费用真实记账及停止条件。不同意Pro旧结论可指出证据变化，原完整意见在下附录。不得要求外传测试视频/标签、换无限prompt、强制正/空配额或暗示官网分等于teacher弱F1。

## 6. 累计历史原文和必要代码

下方保留三个历史Pro可见请求/回答全部论据，并明确旧授权/预算/建议的时间边界：原10月5只讨论/80GiB额度已被用户后续授权执行与动态容量规则取代；旧“新T0/B2未知”已被真实终态及用户37.32/最新差值取代。其他硬边界未自动解除。旧普通轮意见不另附整个244KB旧卷宗，因为此轮已完整包含三次Pro裁决和其保留反对意见；如该缺失影响某判断，须明示不能独立审其原始证据而不假称覆盖。
'''

sources = [
    ('历史三次Pro完整可见会话', HERE / 'pro-history-visible.md', ''),
    ('V14完整独立聚合验收原文', RUN / 'controller/V14_final_acceptance_20261008.json', 'json'),
    ('V14继承科学与接续协议完整原文', RUN / 'teacher_student_autopilot_v14/PROTOCOL.md', ''),
    ('当前时间/空间生产函数完整原文', RUN / 'teacher_student_autopilot_v14/production_t.py', 'python'),
    ('匹配工程诊断与模型/生成函数完整原文', RUN / 'teacher_student_autopilot_v14/precision_helpers/engine.py', 'python'),
    ('学生输入/训练/选点完整核心代码原文（无实际弱标签）', RUN / 'teacher_student_autopilot_v14/train_student.py', 'python'),
]

packet = base + ''.join(section(*s) for s in sources)
out = HERE / 'context-r00.md'
with out.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(packet)
score = {'utc': datetime.now(timezone.utc).isoformat(), 'source': 'direct_user_report_current_turn',
         'reported_difference_from_best': -0.03, 'best_previous_score': 37.63,
         'inferred_score_not_independently_read': 37.60, 'zip_sha256': '95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2',
         'zip_bytes': 308278, 'selected_weight': 'original_B', 'official_page_independently_read': False}
with (HERE / 'score_receipt.json').open('x', encoding='utf-8') as stream:
    json.dump(score, stream, ensure_ascii=False, indent=2)
ledger = {'task_id': TASK, 'continuation': '20261009', 'created_utc': score['utc'],
          'pro_budget_root': str(OLD / 'pro-budget'), 'pro_effective_used': 3, 'pro_remaining': 0,
          'pro_current_new_calls': 0, 'pro_history_source': str(HERE/'pro-history-visible.md'),
          'pro_project': '研究', 'pro_project_ui_verified': True,
          'packets': {'r00': digest(out)}, 'rounds': [],
          'status': 'ORDINARY_ROUNDS_PREPARED_NOT_COMPLETE', 'execution_authorized': True,
          'sources': [digest(s[1]) for s in sources]}
with (HERE / 'ledger.json').open('x', encoding='utf-8') as stream:
    json.dump(ledger, stream, ensure_ascii=False, indent=2)
print(json.dumps(digest(out), ensure_ascii=False))
