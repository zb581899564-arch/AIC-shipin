**“可本地诊断”“可作为某种有限参考”“可用于训练或比赛决策”必须分别登记，不能合并成一个`eligible=true`。**

这也纠正了两个相反的过度推断：

- 原inventory为0，只说明**没有已登记的独立构图authority**，不能推论全盘不存在其他参考。
- 其他资产尚未扫描，也不能推论那里一定有可用新监督。

只读核验已明确记录`UNKNOWN_NOT_SCANNED`；p1b默认未标注、987条豆包来源和未获许可的LIVE_YT_VC也不能重新算作现成独立标签。context-p01-part06

---

## 四、可直接派发的工作单

### 工作边界

执行主机仍为Linux，使用既有授权和既有连接；**本回答是工作单，不是已启动回执**。

只允许读取规定范围内的现存协议、清单、标注schema、来源登记、曝光记录和已保存的native时钟表。允许在独立新目录写入本次CPU工具、清单及报告。**不读取媒体像素、不调用decoder或processor、不加载8B/32B、不下载、不联系作者、不打开100confirm、不读取复赛预测来选配方。**

本次程序不应提供`train`、`infer`、`rematch`或`package`执行子命令，避免出现“G0通过后旧控制器自动接续”的隐含路径。

### 工作A：固定入口的参考资格核验

先由以下**已点名入口的明确本地引用**构造清单，不全盘搜索，不递归追逐外链：

| 入口 | 本次只补什么 | 已有结论如何处理 |
|---|---|---|
| `context_advisory_v1/fallback.py`及其绑定的NONTEST/developer计划、authority登记 | 是否明确指向尚未审计的本地参考资产 | 已登记authority为0直接引用，不重复跑旧inventory |
| p1b的`pilot_manifest`及其标注状态登记 | 是否有此前未核的、实际完成标注的现存文件 | 默认`UNANNOTATED`不当成标签 |
| `existing_16x9_reference_audit`及其明确引用的本地许可、映射文件 | 只补此前UNKNOWN且确有新文件支持的字段 | 原四源有效语义0、人工复核0等旧结果保留 |
| `round3 label_origin_audit`及来源登记 | 是否存在明确不同来源、未审计的新条目 | 987条`api_doubao`保持弱参考身份 |
| p2r9候选矩阵 | 是否指向已经本地存在、已有读取许可且未审计的资产 | `PERMISSION_REQUIRED`、未下载、仅外链条目直接记阻塞 |
| 新GNMC参考协议 | 精确记录用途限制及其覆盖的资产范围 | 不升级为训练、比赛测试、打包或提交许可 |

这些入口和“只补未知、不重复已知失败”的范围有卷宗依据。实际路径必须从现有登记解析，不能靠文件名猜绝对路径。context-p01-part06

**清单第一次冻结后，不因发现参考质量差而继续扩目录。**只有明确指向、当前许可允许读取、且确实尚未完成相同资格检查的条目，才进入本次增量审计。

每条资产至少逐项记录：

| 字段组 | 必须回答的问题 |
|---|---|
| 存在与身份 | 文件是否实际存在；版本、文件SHA及所引用旧回执是什么 |
| 生成来源 | 人工、模型、混合还是未知；是否完成标注；采用什么协议 |
| 任务适配 | 时间选择还是空间构图；有无query；原生目标比例是什么 |
| 映射与覆盖 | 源文件、来源组、坐标或时间基准是否可追溯；哪些范围有判断，未选含义是什么 |
| 使用范围 | 元数据读取、本地诊断、训练、比赛用途及对外共享各自有何依据 |
| 本任务曝光 | 是否参与过训练、选点、选方案或既往查看；是否由当前候选输出派生 |
| 当前结论 | 每项`PASS / FAIL / UNKNOWN`及证据位置，不只给一个总通过标志 |

其中，`PASS`只能表示对应资格字段得到证据支持，**不表示已经独立看过画面、验证语义正确**。来源隔离也不等于模型预训练绝未见过该视频。

缺少隔离依据时，不能通过打开100confirm来“补证”；只引用此前可用的保护登记，无法核清就记UNKNOWN。模型预测缓存不转为人工参考，只有正例的时间标签不把补集补成负例。

### 工作B：全部适用双窗记录的纯CPU精确计划

这部分使用开放开发manifest、原窗口计划及**已经存在的native PTS表**，不读取新旧预测答案或弱标签来挑记录。

必须先实核：

**104条记录中实际哪些旧计划恰有两窗、对应多少真实来源组、许可范围是什么。**现有证据支持8条双窗记录和8个相邻接缝，但尚不能把它写成8个独立来源组。NT8没有接缝，不移植其来源组验收作为这8条开发记录的证明。context-p01-part06

本次只规划以下规则，不扩大成任意多窗均分：

\[
W_{\rm new}=
\begin{cases}
\{[a,m),[m,b)\},&\text{旧计划恰两窗且 }30<b-a<60,\\
W_{\rm old},&\text{其他正常情况},
\end{cases}
\qquad m=\frac{a+b}{2}.
\]

时长恰60秒时，须核新旧边界及计划确实一致，才记录恒等。旧计划异常、有缺口或身份冲突则标阻塞，不能归入正常恒等分支。

**精确实现要求：**

1. 从原登记数值的规范表示构造有理数，不用报告里四舍五入的“约30.3秒”重建边界；不假设源起点为0。
2. 中点**不必落在某个物理帧PTS上**。禁止为此吸附到帧或加入epsilon。
3. 对已有PTS表 \(P_j\)，分别建立
   \[
   I(a,m)=\{j:a\le P_j<m\},\quad
   I(m,b)=\{j:m\le P_j<b\}.
   \]
   两者必须不相交，并完整覆盖原许可域中的物理帧。
4. 对一窗中连续的 \(N\) 个物理ordinal，\(N\le64\)时全部取用；否则按原floor64合同取
   \[
   j_k=j_{\rm first}+\left\lfloor\frac{k(N-1)}{63}\right\rfloor,\quad k=0,\ldots,63.
   \]
   不换为nearest64，不补插值帧。
5. 检查中点、局部时长及源时间转换能否由现有消费者保持同一语义。发现序列化或浮点接口改变半开归属时，记录具体反例并阻塞；**不为了让计划通过，静默舍入或修改旧端点。**

每条适用记录输出旧新窗口、实际来源组、旧尾长度、物理帧数、floor64计划索引，以及**新增与丢失的采样ordinal**。同时分别报告旧主窗区域和旧短尾区域中的采样间隔变化，而不是只报整体平均密度。

原30秒接缝两侧是否有计划样本、新中点两侧间隔多大，可以由现存时钟计算；**“这些样本是否含有更有效的语义信息”仍是UNKNOWN。**

原理上，生成前均分并完整投影模型段不属于输出裁段；但此工作单尚未运行模型。可以用合成区间测试消费者不裁、不延长、不混用旧新答案，不能据此声称真实模型原段已验收。

### 工作C：独立检查并关闭工作包

建议只实现四个职责明确的小模块：

| 模块 | 职责 |
|---|---|
| `qualify_references.py` | 固定入口、用途资格及曝光证据 |
| `plan_two_windows.py` | 纯元数据精确分区、native PTS归属和采样增删 |
| `verify_g0.py` | 独立重算计划与资格结论，检查禁止项和报告一致性 |
| `run_g0.py` | 一次运行、总时限、阶段结果与终态；无GPU或426分支 |

**不要导入会触发模型加载、解码或旧自动接续的通用controller。**纯计划器只接收已解析的元数据。

新CPU测试至少覆盖：非零源起点、单窗、恰60秒恒等、三窗以上保持、二分点恰有或没有物理帧、半开边界唯一归属、空物理窗口拒绝、非法数值、不同文件同来源组、禁止路径访问，以及**GNMC本地诊断资格不能使训练/比赛准入变成True**。

这些测试是本单要实施的要求，**不是本次已完成的验收结果**。旧SG8的53次CPU回放、原strict、旧完整空间场以及18104项冻结文件，不重新跑一遍来填工作量。

---

## 五、前瞻成功门与停止门

本轮不设置任何“涨分门”。设置的是**工作完整性、资格和计划门**：

| 结果 | 精确含义 | 后续动作 |
|---|---|---|
| `NO_NEW_AUDITABLE_ENTRY` | 固定入口没有指向新的可审本地资产 | 结束参考支项，完成双窗计划后NO426 |
| `NO_REFERENCE_ESTABLISHED` | 有资产，但用途、来源、监督含义、映射或曝光史仍缺证 | 列明缺项，不用UNKNOWN填充通过；NO426 |
| `REFERENCE_QUALIFIED_FOR_DECLARED_PURPOSE` | 某资产的特定用途资格成立 | 封存其适用域与证据；**本轮仍不评分、训练或426** |
| `PASS_TWO_WINDOW_PLAN_ONLY` | 既有元数据足以证明精确分区及采样计划成立 | 保存计划，不能改写为真实输入或模型验收 |
| `STOP_PLAN_CONTRACT` | 时钟、来源、许可域或消费者映射存在具体阻塞 | 保存最小反例，不修改端点救过门 |
| `STOP_G0_SCOPE_OR_BUDGET` | 越出白名单、触及禁止数据或达到总时限 | 保存已完成范围及未完成项，停止扩展 |

**本工作单所有正常和阻塞出口，最终都汇总为`NO426`。**不存在“未找到参考→风险推理”“资格PASS→自动加载模型”这两条控制流。

如果发现任务匹配、来源可追溯、用途适当的新参考，下一次可行动的信息应是**具体哪份资产、支持哪个目标、允许什么用途、还缺哪个证据**，而不是再写一句“建议找高质量标签”。是否据此开展新的有限实验，必须针对那份真实新信息重新冻结；不必为了知会消耗一次Pro，也不能把本次NO426回写成GO。

### 真实GPU和训练条件

**本单没有准入真实GPU的分支，新增优化器更新固定为0。**原因是目前没有成立的新训练目标与监督依据，而不是“模型再也不能提高”。

纯CPU计划也不能提供以下验收：

- 实际解码RGB或像素SHA一致；
- 实际processor grid、token长度、显存峰值；
- 新模型原raw及完整区间投影；
- 新NONTEST8或426的11项strict；
- 新官方成绩。

这些字段应记`NOT_RUN`或`UNKNOWN`，不填PASS，更不把0次调用写成“零失败实验成功”。

---

## 六、我为什么否决当前行为门，而不是再替它挑一个数字

### 最强反例仍然穿过原跨缝GO

考虑一个**构造例，不是本题实测标签**：

许可范围为\([0,30.3)\)，均分点为15.15秒。新右窗输出完整合法原段\([15.2,30.2)\)。它不是整窗，跨过旧30秒接缝，两侧有真实帧，也可以改变最终选择集合。

然而，这个长段可能大部分无关；新中点附近原来完整的事件可能被拆散，旧0.3秒尾窗曾密集看到的短瞬态也可能因新采样变稀而遗漏。**非整窗、跨旧缝、集合变化可以全部成立，选择质量仍然更差。**卷内Tibo已给出这一反例。context-p01-part06

Gemini后加的“至少3个新99%全选或全空才阻断”也没有补上这个缺口：刚才的误报可以低于99%，遗漏也不必表现为整窗变空。它是一个拟议的行为限制，不是已有数据支持的质量判据。

全104均值还会被96条恒等记录稀释。卷内构造例中，8条受影响记录假设分属8组，5条弱F1各降0.8，其他记录不变，全104均值仅下降约0.03846；下降组占受影响组62.5%。这足以说明原0.05／75%粗门可能放过严重的局部损失，**不是证明这些弱F1就是真实质量**。context-p01-part06

我的处理不是再换一个全选比例、组数或分母来“修好放行门”，而是**本次不让这些行为指标承担质量准入职责**。新增99%／3窗条件及“几十次调用”的成本表述，卷末主控也已明确指出缺乏依据或与190窗上界不一致。context-p01-part06

### 对本裁决最强的反对意见

**可能所有已许可资产都没有新参考，G0最终没有新包；均衡二分即使没有方向证据，仍可能实际提高官方分。**

我接受这个机会成本，不声称NO426在未知真实分数上必然最优。选择G0的理由是：它用一个短、可提前结束的工作包，补齐目前确实未完成的资格字段和真实采样交换；而不是继续购买一批无法用当前条件判断方向的新答案。

因此本轮结束后，不应自动开始“第二次寻找参考”，也不应因GPU空闲而启动均衡二分。**没有新证据就是这份工作单的终点，不是无限等待人工的起点。**

---

## 七、最终产物与费用验收

工作包应留下以下可审查产物，实际路径在新目录建立时登记：

| 产物 | 内容 |
|---|---|
| `input_scope.json` | 本次白名单、真实路径、版本／SHA、允许用途和引用来源 |
| `reference_qualification.jsonl` | 全部审计条目、逐字段结论、排除或未知原因 |
| `source_exposure.json` | 来源派生、组关系及本任务训练／选法曝光证据 |
| `two_window_plan.json` | 全部适用记录的精确边界、PTS归属、floor64及采样增删 |
| `cpu_acceptance.json` | 本次新CPU合同、独立计划重算结果及失败反例 |
| `closure.json`、简短结论 | 实际读取范围、未完成项、费用、禁止项计数及最终NO426 |

**不生成`predictions.jsonl`或候选ZIP，不重复封装旧包伪装成新候选。**

费用记录为本次实际CPU时间、文件读取量、峰值占用和产物大小；新增模型、decoder、processor及优化器调用均应为0。没有GPU作业，就不伪造一次`completed`的GPU回执。其他合法作业若追加了共享账本，应核实是正常追加，不要求整份共享账本始终不变；**旧记录、7200偏移和历史空间成本必须保留。**

旧B37.63仍保护原ZIP：

```text
86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54
```

本轮不比较旧B与V14逐例测试预测来决定方向。Grok已撤回该提议；只读或聚合并不会把“据测试输出选择／取消配方”变成单纯完整性检查。context-p01-part06

对席位来源另作一处明确说明：卷内`sol-r01.md`正文仍保留均衡风险与跨缝门的旧表述，**Sol最终撤回由本次用户说明及卷末`host-pre-pro.md`登记提供**；不能声称所附Sol正文已经逐字同步撤回。我的裁决不以三比一或所谓全文共识为依据。context-p01-part06 context-p01-part06

## 最终执行结论

**现在安排：一次有界的增量参考资格G0＋全部适用双窗记录的精确CPU计划。只补未知，不重验旧成功；不启动新GPU，不训练，不产新426。**

**GNMC保持本地诊断用途，SG8保持原NO426，均衡二分保持“工程上可讨论、质量方向未成立”的状态。**完成工作单后，交付具体资产资格、计划收益与损失、阻塞证据及NO426终态；没有新证据就结束本轮，不靠剩余额度、换阈值或另起同类实验延长流水线。
```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/official_rematch_snapshot.txt
字节=4125；SHA256=c5e218ca636c4a8c102e51b8a8d223dd12b612c35e2755e9da2fa07b29db3e04

```txt
Title: 全球校园人工智能算法精英大赛 智青春·算未来

URL Source: https://www.aicomp.cn/notice/notice-3/5307.html

Markdown Content:
关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知

各参赛团队：

2026年第八届全球校园人工智能算法精英大赛产业命题赛道“基于视频大模型的通用视频高光剪辑”赛题报名将于9月30日11:00截止，初赛赛题结果文档提交截止时间为9月30日11:30。结合赛事整体组织安排，经大赛组委会研究决定，现将复赛有关事项通知如下：

###### 一、赛程安排

1.复赛数据集开放时间：9月30日18:00；

2.复赛赛题结果文档提交开始时间：10月1日09:00；

3.复赛赛题结果文档提交截止时间：10月23日20:00；

4.复赛作品文档提交截止时间：10月25日23:59。

###### 二、评审原则

1.初赛晋级。参赛团队须于9月30日11:30前提交初赛赛题结果文档，且在初赛排行榜上成绩得分＞0分的团队，方可进入复赛。

2.复赛数据集下载。复赛数据集开放后，各参赛团队登录大赛平台，查看“我的参赛信息—详情”，即可下载复赛数据集。

3.复赛成绩。复赛阶段，参赛团队每日可提交5次赛题结果文档，最终以复赛阶段排行榜最高得分为最终成绩（因排行榜存在算分延迟，最终成绩以组委会公示结果为准）。

4.复赛评测。复赛阶段实际推理所使用的主模型及辅助模型总参数量不得超过 9B。参赛团队须在技术报告中如实填写模型总参数量。参数统计口径及违规处理方式详见《基于视频大模型的通用视频高光剪辑算法赛题规则》（附件 1）。

5.复赛作品提交。参赛团队需在规定时间内提交参赛作品文档。作品提交截止日期后，不再接受任何形式的修改和补充。评审团队对复赛参赛作品文档进行结果复现与审核，如有疑问，将要求参赛者进行解释说明。

6.复赛评奖规则。以复赛排行榜得分为依据评选复赛一、二、三等奖，获奖作品数量分别按照不超过15%、25%、30%的比例取整计算。复赛一、二等奖获奖作品将推荐参加半决赛。

###### 三、作品提交注意事项

参赛队伍需将复赛提交内容（预测结果JSONL文件、算法代码、模型文件与运行环境、技术报告）提交至大赛平台。提交前，需按指定入口和文档命名规则仔细检查作品文档，确保内容准确且无格式错误。作品提交要求详见《基于视频大模型的通用视频高光剪辑复赛作品提交要求》（附件2）。

###### 四、联系方式

赛题QQ群：389921008

国赛组委会联系电话：025-85778806

国赛组委会仲裁邮箱：office@aicomp.cn

大赛官网：[www.aicomp.cn](https://www.aicomp.cn/)

**附件:1.**[基于视频大模型的通用视频高光剪辑算法赛题](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B61-%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E7%AE%97%E6%B3%95%E8%B5%9B%E9%A2%98-0930.pdf)

**[2.基于视频大模型的通用视频高光剪辑复赛作品提交要求](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B62%EF%BC%9A%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E4%BD%9C%E5%93%81%E6%8F%90%E4%BA%A4%E8%A6%81%E6%B1%82-1.pdf)**

[关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知](https://www.aicomp.cn/wp-content/uploads/2026/09/%E5%85%B3%E4%BA%8E%E4%B8%BE%E5%8A%9E%E4%BA%A7%E4%B8%9A%E5%91%BD%E9%A2%98%E8%B5%9B%E9%81%93%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E7%9A%84%E9%80%9A%E7%9F%A5-1.pdf)

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/baseline_a_pts_v1/vendor/temporal_common.py
字节=8859；SHA256=bb8f47896e20e069e9ddf992d94488132ccbee46dc850a2658851f4aa52946b4

```py
#!/usr/bin/env python3
"""temporal_round5 — shared query-free temporal I/O.

Virtual clip:
  The clip is taken ON THE FLY from the source video at
  [clip_start_sec, clip_end_sec]. No clip files are rendered in batch.
  `qwen_vl_utils`' own video_start/video_end slicing records ABSOLUTE frame
  indices, so the processor would label the clip with absolute source times.
  To make the model see time starting at 0 we decode the clip's frames
  ourselves and hand the processor 0-BASED `frames_indices` plus the source fps,
  which makes `_calculate_timestamps` produce clip-local seconds.

Prompt: one query-free prompt, identical for every arm and for training.
  It never receives a QVHighlights query, a teacher summary, cropRois or any
  test-set information.
"""
from __future__ import annotations

import json
import math
import re

MAX_FRAMES = 64
MAX_PIXELS = 128 * 32 * 32           # same per-frame budget as the frozen baseline

PROMPT = (
    "You are shown a short video clip. Identify every time interval in the clip that is "
    "worth keeping in a short highlight edit.\n"
    "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
    'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
    "clip-local seconds.\n"
    "Rules:\n"
    "- every interval must satisfy 0 <= start_sec < end_sec <= clip duration\n"
    "- return between 1 and 5 intervals\n"
    "- sort them by start time and do not let them overlap\n"
    "- output nothing except the JSON"
)

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"


def build_virtual_clip(source_path, clip_start_sec, clip_end_sec, max_frames=MAX_FRAMES):
    """Decode the clip's frames and build 0-based video metadata.

    Returns (frames_uint8_THWC, metadata, info).
    """
    import numpy as np
    import decord

    vr = decord.VideoReader(str(source_path))
    total = len(vr)
    fps = float(vr.get_avg_fps())
    if fps <= 0 or total <= 0:
        raise RuntimeError(f"unreadable video {source_path}: total={total} fps={fps}")
    sf = int(math.ceil(max(0.0, clip_start_sec) * fps))
    ef = int(math.floor(clip_end_sec * fps))
    sf = max(0, min(sf, total - 1))
    ef = max(sf + 1, min(ef, total - 1))
    n_clip = ef - sf + 1
    nframes = int(max(1, min(max_frames, n_clip)))
    if nframes == 1:
        local_idx = [0]
    else:
        local_idx = [int(round(x)) for x in np.linspace(0, n_clip - 1, nframes)]
    abs_idx = [sf + i for i in local_idx]
    arr = vr.get_batch(abs_idx).asnumpy()          # (T, H, W, C) uint8
    md = {"fps": fps, "frames_indices": local_idx,
          "total_num_frames": n_clip, "video_backend": "decord"}
    info = {"source_total_frames": total, "source_fps": fps,
            "clip_start_frame_abs": sf, "clip_end_frame_abs": ef,
            "n_frames_in_clip": n_clip, "n_sampled": nframes,
            "clip_local_indices": local_idx, "absolute_indices": abs_idx,
            "clip_local_times_sec": [round(i / fps, 4) for i in local_idx],
            "clip_duration_sec": round(clip_end_sec - clip_start_sec, 6),
            "sampled_span_sec": [round(local_idx[0] / fps, 4),
                                 round(local_idx[-1] / fps, 4)]}
    return arr, md, info


# ---------------------------------------------------------------- parsing
def parse_segments(raw, clip_duration, max_segments=5):
    """Strict parse -> (segments|None, errors, warnings).

    Accepts only a single JSON object with a "segments" list of [a, b] pairs.
    Ranges must be numeric, finite, 0 <= a < b <= clip_duration.
    Overlaps are reported; the returned list is sorted and merged-free (the
    evaluator uses the UNION, so overlaps do not inflate the score).
    """
    errors, warnings = [], []
    if not isinstance(raw, str) or not raw.strip():
        return None, ["empty model output"], warnings
    objs = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", raw, re.S)
    found = None
    for o in objs:
        try:
            d = json.loads(o)
        except Exception:
            continue
        if isinstance(d, dict) and "segments" in d:
            if found is not None:
                return None, [f"ambiguous: more than one JSON object with 'segments'"], warnings
            found = d
    if found is None:
        return None, ["no JSON object containing 'segments'"], warnings
    segs = found["segments"]
    if not isinstance(segs, list):
        return None, [f"'segments' is not a list: {type(segs).__name__}"], warnings
    if len(segs) == 0:
        return None, ["'segments' is empty"], warnings
    if len(segs) > max_segments:
        return None, [f"{len(segs)} segments exceeds the requested maximum {max_segments}"], warnings
    out = []
    for i, s in enumerate(segs):
        if not (isinstance(s, (list, tuple)) and len(s) == 2):
            errors.append(f"segment {i} is not a 2-element list: {s!r}")
            continue
        a, b = s
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b)):
            errors.append(f"segment {i} has non-numeric bounds: {s!r}")
            continue
        a, b = float(a), float(b)
        if not (math.isfinite(a) and math.isfinite(b)):
            errors.append(f"segment {i} has non-finite bounds: {s!r}")
            continue
        if not (0 <= a < b):
            errors.append(f"segment {i} violates 0 <= start < end: [{a},{b}]")
            continue
        if b > clip_duration + 1e-3:
            errors.append(f"segment {i} exceeds clip duration {clip_duration}: [{a},{b}]")
            continue
        out.append([round(a, 4), round(min(b, clip_duration), 4)])
    if not out:
        return None, errors or ["no usable segment"], warnings
    out.sort()
    for (a1, b1), (a2, b2) in zip(out, out[1:]):
        if a2 < b1 - 1e-9:
            warnings.append(f"overlapping segments [[{a1},{b1}],[{a2},{b2}]]")
    if errors:
        return None, errors, warnings
    return out, errors, warnings


def union_length(segs):
    if not segs:
        return 0.0
    s = sorted(segs)
    tot, a, b = 0.0, s[0][0], s[0][1]
    for x, y in s[1:]:
        if x <= b + 1e-9:
            b = max(b, y)
        else:
            tot += b - a
            a, b = x, y
    return tot + (b - a)


def interval_metrics(pred_segs, gt_segs, clip_duration):
    """Union-based precision / recall / F1 in the clip's time span."""
    if clip_duration <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    pl = union_length(pred_segs or [])
    gl = union_length(gt_segs or [])
    if pl <= 0 or gl <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
                "inter_sec": 0.0}
    # intersection length of two union-of-intervals
    def to_segments(segs):
        s = sorted(segs)
        m, a, b = [], s[0][0], s[0][1]
        for x, y in s[1:]:
            if x <= b + 1e-9:
                b = max(b, y)
            else:
                m.append([a, b]); a, b = x, y
        m.append([a, b])
        return m
    A, B = to_segments(pred_segs), to_segments(gt_segs)
    inter, i, j = 0.0, 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if hi > lo:
            inter += hi - lo
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    p = inter / pl
    r = inter / gl
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    return {"precision": round(p, 6), "recall": round(r, 6), "f1": round(f1, 6),
            "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
            "inter_sec": round(inter, 4)}


def materialize_clip_file(source_path, clip_start_sec, clip_end_sec, out_path):
    """Write ONE temporary clip file for the virtual window.

    Needed for the Qwen3.5 (Video-ORA-4B) video path, whose processor rejects a
    directly supplied frame tensor. The file is cut with -ss/-t so its timeline
    starts at 0, i.e. the clip is still "virtual" (one file at a time, deleted
    after use; nothing is batch-rendered onto disk).
    """
    import subprocess
    from pathlib import Path
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(0.04, clip_end_sec - clip_start_sec)
    subprocess.run(["/usr/local/bin/ffmpeg", "-nostdin", "-y", "-v", "error",
                    "-ss", f"{clip_start_sec:.6f}", "-i", str(source_path),
                    "-t", f"{dur:.6f}", "-c:v", "mpeg4", "-q:v", "3",
                    "-pix_fmt", "yuv420p", "-an", str(out)],
                   check=True, stdin=subprocess.DEVNULL)
    return str(out)


def load_split(name, r5root):
    from pathlib import Path
    p = Path(r5root) / "data" / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

```

END_EMPTY407_R00B


## 第一轮原始完整公开回答：tibo-r00.md
SHA256=5470e02ee3f86f8de522e954db6c72bd7bbbf9203b05077ac8eb1fc426fb98d6

12:36收到。我先完整读取这份新卷宗，核清407/426空输出的实际证据，再区分校准、语义、时序和训练目标的问题，给出唯一有界路线。本轮只讨论，不联网或执行实验，也不会把声明SHA当作已独立验签。12:36

已完整分段读取 context-r00(3).md 第1–37132行，读至 END_EMPTY407_R00；展示截断处已补读。quality_result.json 的4臂×9源、共5404个评分四元组也已完整核对。841249字节及 d41e…fea0 是主控声明；本次读取的是工具提供的文本，没有独立验证原文件字节SHA。我的唯一主案：先做“可审计事件标签小试”，通过后从37.66对应原B续训一次；未通过就保留原B、NO426。停止扩训当前图片评分配方。校准检查用于辨别病因，不另开一条降阈值冲包路线。407空的病因：目前可以确定什么校准问题有实证，但不是唯一原因。阈值49来自训练集人工分数的80分位，没有证明它可直接用作模型输出的决策界。已有9源开发结果中，新模型1351点预测范围24–53，80分位38、95分位48；≥49仅48点，占3.55%。对应人工≥49有293点，占21.69%。新模型已有4/9开发源为空，这四源都有人工作为高重要性的评分点。但不能据此把阈值改成38。新模型≥49那部分平均预测50.69、平均人工50.65，尾部均值并非普遍低估；尺度压缩与具体排序错误同时存在。语义错误不能靠标量校准修好。最直接的非测试反例来自同一源 sTEELN-vY30：grid5/ordinal329，人工87、预测48，被丢；grid32/ordinal1949，人工27、预测50，被选。任何保序一维校准都不能纠正这对逆序。这里的人工分数仍只是TVSum重要性，不是AIC高光真值。时序问题是另一层：单个中点的重要性不能推出整个2秒都应保留。已有扇舞28/29秒与29.96秒行人切镜，足以推翻整格无条件扩展。反过来，短动作若根本没进入学生输入，降低阈值也无法补回信息。目标函数问题尚未排除。237步、非零梯度和权重改变证明真实训练，不能证明任务目标正确。附件的 observed_train.py 是外部训练器包装；没有展示实际collator的label mask和完整loss实现，不能独立确认prompt、padding是否正确排除。整数文本CE本身也不直接优化事件召回和边界。grammar没有强制空输出：它约束每图20–100整数，再由≥49选择；有效低分形成合法空。11项strict和回放PASS主要证明工程合同。407空是严重风险信号，但没有测试真值，不能宣称真实召回就是零。我对主控的关键批评旧投入门比较的是新评分器与base在新图片任务上的点估计，native代理F的差值区间还跨零；production_B也被放进图片评分prompt，并未与37.66原生视频系统公平比较。这个门能放行“相对很弱基线略好、绝对质量仍差”的候选。新立场仍有一个容易重犯的漏洞：“UNKNOWN不转负例”不够。若完整窗口含UNKNOWN，却把目标写成只列KEEP的完整segments列表，闭括号和停止生成仍在教学生遗漏未知区域。必须整窗排除这种样本，不能只在记录里写一句unknown_never_negative。此外，“强闭源能产高质量标签”应当是待检验假设，不能当开工前提。最小非测试判别与G0先复用已有成功raw，不重跑四臂生成：冻结上述分布、逆序例、4个开发空源及随机对照，逐项检查事件是否进入实际学生采样。分清“看见但低估”“看见却认错”“根本没看见”“单点正确但扩段错误”。已见9源和NT8只作诊断，不改名盲确认。取一条实际训练batch核input/labels、视觉占位及padding的mask、答案token数量、损失归一化；补齐外部训练器的真实合同。candidate0锁定37.66那套完整balanced_two_window_v3 native系统：原B adapter、实际展开prompt、grammar、processor、floor64、精确PTS、双窗、解码和空间场。不能拿旧CFR入口或图片评分版production_B替代。特别核实版本缝隙：最新协议写0..5，旧附录prompt写1..5。材料不足以断言当前生产冲突，必须核实际运行锁的字节；不能借核验偷偷修改candidate0。若实际prompt不支持明确空窗，须先解决新训练合同与原基线的兼容问题，本轮不得直接喂入冲突的空目标。建来源关系表：原视频、转载、裁剪、近重复及历史训练曝光归组。9已见dev、旧标注和104/96开发经历如实登记；不读100confirm，不假设库存里天然有未暴露金标。这些检查若已表明没有可审计观察路径、来源无法隔离或训练合同无法绑定，就STOP，不花训练费。标签必须怎样才可入训优先终端agy，但native MP4调用成功和“1fps/30images”自报不等于实际观察证明。现在6片90格的teacher入训仍为0，处理正确。每条事件记录至少包含：来源组、源SHA、窗口、原生ordinal/PTS、学生实际输入清单、标注规则版本。程序生成的证据帧ID与像素哈希；实际供给回执、教师声称看过的ID、独立审查确认的事实分别存储。KEEP/明确NO/UNKNOWN，可见动作事实与高光理由分开写。起止边界的内外证据ID、不确定区间、切镜关系、上下文不足或音频缺失等限制。审查者、盲审原始结论、争议及准入理由。教师引用已存在的证据ID，不自由编精确秒数。关键动作与边界补供显式连续原生帧；仍看不清就UNKNOWN。确切坐标不代表确切语义。切镜触发检查，不机械充当高光边界：跨镜事件可以成立，但两侧都须有证据；单镜头也可能早已结束事件。禁止把一侧KEEP自动扩到另一侧，禁止事后裁剪教师端点来伪造通过。独立审查先看媒体和冻结规则、后看教师答案；所有NO也审，不只审高置信KEEP。同教师复查或多个教师一致只算弱证据。闭源标签称“可审计银标”，没有人工独立裁决就不升级为金标。完整segments SFT只收全窗可监督样本：整个声明范围均有经审查KEEP或明确NO，未列区域不自动算NO。含未解决UNKNOWN整窗排除。明确全窗NO才可输出[]。边界仍只有模糊包围范围时，不取中点冒充精确标签。教师看见而学生输入不可辨认的关键事件，也不能强塞为精确监督。唯一有界工作包以下数字是我建议新冻结的投入上限，不是统计保证，也不改写旧STOP。标注阶段：先复用原六片及原raw检查新证据合同；新增请求只为新观察或独立盲审，不重复成功调用。扩展上限24个现有许可source_group，每组事前固定2个≤30秒窗口，共48窗。12组训练、6组流程开发、6组锁定确认，按来源关系和真实曝光史先冻结；不能根据模型结果选窗、换组。总计最多108次闭源请求，含48次提案、48次盲审和12次证据补查；原六片若产生新调用也计入此总额。供给视频累计上限30分钟，实际usage及费用逐项追加。至少取得8个训练组、16个完整可监督窗口才训练；明确正事件和明确NO均须跨多个来源。开发、确认集合若无法提供可评价的正事件及NO范围，就NO426，不能反复换样本凑门。缺乏足够来源、上下文或观测能力，在上限内无法解决就停止。无需无限等人工，也不拿弱参考冒充真值。训练阶段：从原B全部288个adapter张量精确加载；保持原r16/alpha32、语言q/k/v/o，基座及视觉冻结。新建优化器明确记账，不宣称恢复原优化器轨迹。一次固定lr=1e-5、3遍已接纳数据，有效batch4、最多18次更新；不扫学习率、轮数或checkpoint。采用源均衡及逐样本答案长度归一的assistant-only CE，具体公式与mask在开跑前冻结。前2步做真实梯度、冻结参数和保存重载验收，随后沿同一优化器/RNG继续，不能重启重复曝光。只评估固定终点与candidate0。新训练计费上限1200秒，非测试推理1200秒，获准的唯一426出口另限2400秒；任一阶段到限未完成即停，不拿半成品充当通过。沿用现有算力，不新增租卡。闭源费用还须按实际终端计费方式登记，次数上限不等于免费。前瞻质量门与出口先完成参考、冻结标签和规则，再揭示候选预测。开发用于一次淘汰，不用于改配方；确认只使用一次。旧曝光无法排除时如实降为锁定开发审查，不能宣称独立泛化验证。主指标是逐source等权的经审查区间F1，辅助必须同时报：事件召回、明确NO误选时长、含正事件却全空的窗口数、边界外溢及不确定范围。完整分母、拒收和UNKNOWN都报告，不能丢掉难例再报好看均值。TVSum排序、教师一致率和格式合法率单列。建议放行条件：开发均值ΔF1>0；确认6组至少4组ΔF1>0、均值>0、留一组后均值均≥0；确认宏precision、recall均不退化，正事件漏空数及明确NO误选比例均不增加。证据、来源、采样或切镜合同出现未解决违规直接STOP。以上只是小预算风险筛选，六组不能证明统计显著或官方涨分。全部通过且参考具备可审查事实依据，才允许制作一个质量UNKNOWN的426风险包：沿用冻结native管线和完整空间场后过滤，核实际总参数≤9B、全部426记录、时钟/边界/JSON严格验收和唯一成本终态。不在426结果上调整阈值、TopK或重选权重；制包不等于官网提交或替换生产授权。任何门失败则NO426，继续保留原B37.66。对我自己主案的最强反例强闭源审查也可能把“显著、热闹、有运动”系统性偏好成高光；学生在银标F1上胜原B，官方却下降。两张都正确的1fps画面还可能共同漏掉中间动作，教师一致只会强化同一个错误。上述门只能压低这种风险，不能消除共同偏差。另一种反例是：目标一致的非测试审查最终发现排序已足够好，主要只是尺度问题，那么续训不是最省钱的办法。故小试必须允许否定续训必要性；此时本轮STOP并提交新证据讨论，不能为了兑现“要训练”硬跑。最终裁决：有可靠的TVSum重要性监督，不等于已有可靠的AIC事件边界监督。当前最值得买的新信息，是可复查的事件与完整窗口监督，以及相对原B native的真实配对证据。先验证这两件事，再决定是否花那一次续训和426预算。12:44

## 第一轮原始完整公开回答：sol-r00.md
SHA256=3d2f0a034019c68bb369555108b887a645049eda68c4c8b8de0a51e5af15cb57

说：
EMPTY407-20261010｜第一轮独立会诊

任务ID： AIC-VIDEO-REMATCH-NEXT-20261005
子议题： EMPTY407-20261010
版本： r00
实际附件： context-r00(3).md

一、附件核验与读取范围

已在本地直接读取附件，并独立完成文件完整性核验：

核验项

	

结果




文件字节数

	

841,249，吻合




文件行数

	

37,132，吻合




SHA-256

	

与主控声明完全一致




文件末尾

	

END_EMPTY407_R00，存在




本轮边界

	

仅文字会诊，不执行实验、不联网

独立计算的 SHA-256：

d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0

后续判断以附件中的真实结果、代码、协议及历史裁决为基础，不把报告自述的成功等同于独立实验复现。

二、独立技术判断：为什么出现407个空视频
1. 现有证据

以下数值来自附件记录及保存的代码，不是本轮重新执行的模型实验。

指标

	

历史最佳B

	

新237步评分器




复赛视频数

	

426

	

426




选中帧数

	

102,112

	

3,189




空视频数

	

未给出精确数量

	

407




非测试8源

	

旧生产链已有验收

	

8/8为空




已知官网分

	

用户反馈37.66

	

未知

新评分器空视频比例为 95.54%。它不是一个有可靠AIC质量证据支持的替代方案。
context-r00.md

我另外检查了 quality_result.json 保存的9个开发源预测分布，发现一个比总体Spearman更值得重视的现象：

新模型9源预测分数的最高值分别为：50、47、50、52、42、48、46、53、50。

9源中有4源，最高预测分仍低于冻结阈值49，所以这些源在该规则下必然全空。

新模型的排序相关系数明显提高，但它给出的绝对分数集中在较低范围，且最高分普遍只比阈值略高。

阈值49来自人工训练标签的80%分位数，并不是模型预测分数的已验证校准分位数。

这构成了当前最具体的校准失配证据。

还要注意：新模型在已见9源上的TVSum Spearman为0.522329，相对基座0.043629，确实有排序学习；但native代理F改善的配对95%区间为[-0.001096, 0.210326]，包含0。
context-r00.md

因此不能简单说模型完全没学会，也不能据此认定其具有AIC高光选择能力。

2. 四类根因必须分开

根因

	

当前证据强度

	

我的判断




分数校准失配

	

较强

	

很可能直接导致大量阈值下全空




语义任务错配

	

较强的机制证据

	

TVSum重要性与AIC可剪辑高光并非相同标签目标




时序信息与边界缺失

	

已有具体失败案例

	

单个2秒中点不能代表整格内的动作及切镜




目标函数与任务不一致

	

代码可以确认

	

训练优化评分文本的交叉熵，未直接优化高光事件召回与时间边界

我检查了 selector_contract.py、score_grammar.py 和 contest_engine.py。

新系统的实际决策结构为：

2秒格中点采样 → 每批最多16张有序静态图

预测 scores_x20，语法限制为20–100

score >= 49 保留，否则丢弃

整个2秒格选入或排除 → 复用完整空间场

这个管线具有明确的结构性限制：

即使评分器正确发现某一帧很重要，它也不能直接确定真实事件的开始、结束、动作是否完成，以及2秒范围内是否出现切镜。

407空则是另一种失败表现：绝对分数偏低时，严格阈值把弱但有价值的候选也全部过滤掉。

不能在这两种错误之间直接选择“降低阈值”。降低阈值可能增加召回，也可能仅仅增加无意义帧。

3. 校准和语义哪个是主因？

我会区分两个问题：

问题A：为什么新系统几乎不输出？
现有证据首先指向校准失配与阈值化机制。

问题B：就算让新系统多输出，能否提高AIC成绩？
现有证据不足，而且语义与边界监督不匹配仍可能造成重大损失。

因此，修复407空的输出分布，不等于修复高光质量。

我反对继续扩大相同TVSum评分配方，也反对仅通过改变分数阈值产出另一个426包。

三、唯一推荐路线：原B Native事件监督续训
推荐主案：B-NATIVE-EVENT-SFT-v1

保留37.66原B作为candidate0，以原B原生视频窗口为训练单位，利用agy产生事件候选，再通过独立视觉与边界审查获得小规模高可信监督。只有监督完整且公平对照通过，才允许一次有界LoRA续训和后续候选验收。

不继续训练TVSum图片评分器，不引入新架构，不并行探索其他模型。

这条路线的核心不是寻找更强的教师，而是把训练目标从“帧重要性打分”重新对准“可实际剪辑的高光事件区间”。

阶段A：最小根因判别，先不训练

严格限定在已有非测试资源。

检查

	

最小操作

	

判别结果




校准

	

读取冻结的train/9dev评分，统计分位数、分数范围、阈值49以上比例

	

排序尚可但分数普遍低，支持校准失配




语义

	

对少量独立审查的非测试事件，比较TVSum高分与实际可剪辑事件

	

高重要性不等于高光，支持目标错配




时序

	

比较原B64帧原生采样、新模型2秒中点与事件真实可见帧

	

有事件但采样不可见，支持时序瓶颈




输出目标

	

检查完整事件标签、缺失区间、模型格式及可表达范围

	

判断是否可用现有B协议做完整窗口监督

这里最重要的是可观察性检查。

如果独立参考确认某个关键动作发生，但原B的实际输入采样根本没有捕获该动作的可识别证据，那么增加微调步数不可能稳定解决这个特定问题。

如果原B能够观察到动作，却没有选择，才具有进一步研究语义监督的价值。

所有检查必须在训练配方冻结前完成，不读取复赛单视频输出。

阶段B：agy标注，最多24个原生窗口

建议一次前瞻试验上限：

项目

	

冻结上限




数据

	

现有且用途许可明确的非测试视频




来源组

	

最多12个彼此隔离的来源组




每组

	

2个不重叠的原B原生窗口




总视频窗口

	

24个，每窗不超过30秒




agy首次调用

	

最多24次




定点边界补查

	

最多8次




新大数据下载

	

0

预先按照来源组划分6组训练、3组校准、3组确认。相同视频、同源派生裁剪、重复素材不能跨组；还需核对历史B训练和开发曝光记录。如果找不到满足条件的来源，就缩小可用集合并明确降低证据等级，不把已见开发集冒充全新盲测。

历史已有6段90格标注保留为流程失效案例，不直接升级训练样本。
context-r00.md

新标注不再以2秒KEEP列表作为最终训练目标，而是要求agy针对原B实际窗口输出可追溯的事件及其起止证据。

阶段C：标注格式与真实观测要求

建议使用如下核心字段；具体枚举和路径应在首次模型调用前冻结。

JSON
{
  "source_id": "source-id",
  "source_group": "group-id",
  "source_sha256": "...",
  "window_id": "...",
  "clip_sha256": "...",
  "time_basis": "native_pts",
  "observation": {
    "tool": "agy/view_file",
    "actual_observed_ordinals": [],
    "coverage": "SPARSE",
    "full_observation_proven": false
  },
  "events": [
    {
      "state": "KEEP",
      "event_type": "action_or_result",
      "start_native_ordinal": 1200,
      "end_native_ordinal_exclusive": 1240,
      "positive_evidence_ordinals": [],
      "boundary_evidence_ordinals": [],
      "boundary_status": "UNVERIFIED",
      "confidence": "MEDIUM"
    }
  ],
  "unresolved_ranges": [],
  "full_window_supervision_eligible": false
}

这些是格式示意，不代表已存在对应帧或审核结果。

需要保留原模型答复、原生媒体SHA、实际输入、模型声明的观察时刻、独立核验的物理帧以及规范映射结果。教师声称看见的内容与审查人员实际验证过的内容必须分字段存储。

建议用双层观察方式：

第一层通过agy读取原生短MP4并描述候选事件。第二层基于真实native PTS提供可索引的视觉证据，尤其是事件起止和切镜附近的较密集帧序列。即使视频工具报告1fps，也不能推断模型连续观察了完整视频。

对正例区间，必须至少能够核验事件内部的正向证据，并用起止附近的前后帧支持边界。只有内部证据而没有边界证据的片段，不应取得精确时间监督资格。

切镜是硬边界问题，而不是标注格式问题。

以附件中28–30秒扇舞案例为例，28/29秒确有扇舞，29.96秒已经出现行人。不能因为28/29秒正确，就把整个28–30秒赋为KEEP。
context-r00.md

接受条件应是：

区间端点映射到合法原生ordinal，半开范围精确，无来源漂移。

每个KEEP都有真实可观察的事件依据，且原B实际采样至少具有足以识别该事件的证据。

已确认的切镜必须分段或截断；切镜位置不确定则边界保持UNKNOWN。

REJECT必须有已观察到的明确过渡或冗余证据，UNKNOWN不能当负例。

未能覆盖完整窗口时，禁止把部分KEEP列表转换为完整窗口的segments监督。

最后一条尤其重要。完整窗口交叉熵训练隐含模型应该输出全部目标事件。如果只标出了其中两个正例，另外未观察的时段就可能在训练时被错误地当成“不应输出”。

这正是弱标签污染原B的重要风险。

阶段D：标注质量门

建议对候选KEEP和所有切镜相关端点实施独立人工复核，对REJECT按事前随机规则抽查，确认组的完整事件参考应在查看candidate0及新模型预测之前完成。

我建议采用以下前瞻性工程准入线，而非统计置信保证：

指标

	

建议接受条件




来源及native映射

	

100%合法




已确认跨镜误标

	

0




KEEP独立复核精确率

	

≥85%




经复核的边界区间IoU

	

平均≥0.75




可作为完整窗口监督的训练样本

	

≥8窗，覆盖≥4来源组




UNKNOWN处理

	

全部分离；不得自动变负例




样本数不足

	

到24窗上限直接STOP，不循环补采

85%、0.75及最小样本数是控制投入和噪声的工程选择，并没有来自附件的统计保证。少量样本达标不等于教师已成为金标。

同一教师重复判断所得的一致率只能评估稳定性，不能代替独立语义审查。

四、训练：只允许一次从原B续训

有一个必须正视的协议问题：

原B的native视频提示词要求返回1–5个segments，也就是它不能在每个窗口内直接表达零段。这个限制在历史原始提示词代码中是明确的。
context-r00.md

因此本轮不能一边声称沿用原B语法，一边把NO_HIGHLIGHT当作合法的空段输出进行完整窗口SFT。

我的处理是：**本轮只用完整审查、存在1–5个真实可见高光区间的窗口进行B原协议续训。**确认没有高光的窗口保留作负例诊断及误报评估，不假装本轮已经解决原B不能输出空窗口的表达问题。

被冻结的训练条件：

项目

	

条件




初始化

	

37.66候选对应的原B8B时间LoRA




基座

	

原Qwen3-VL-8B，冻结




LoRA

	

继承r16、alpha32、q/k/v/o




学习率

	

1e-5




有效batch

	

4




训练

	

最多2 epoch、最多8次真实optimizer更新




数据

	

仅合格train来源的完整窗口




目标

	

原B native视频到完整segments，不使用TVSum分数




checkpoint

	

预先指定最终checkpoint，不用确认组挑权重




新架构/新参数头

	

0

继续加载原B适配器是必须的，不能像237步实验那样重新训练独立任务LoRA。若不能恢复旧optimizer状态，应明确登记新优化器初始化，不能声称优化器无缝接续。

这个规模是可证伪的低成本续训试验，不是预计能够直接显著涨分的大规模训练。

训练前应保存原B全部权重和参数身份；训练后验实际参数变化、冻结情况、有限梯度、加载身份与输出合法性。

如果有效样本太少，实际更新可以少于8，禁止重复曝光样本以凑足步数。

五、原B native公平candidate0

这是我认为必须补足的最关键科学对照。

Candidate0

历史37.66原B

原LoRA、原native视频输入、原双窗配置、原processor与grammar。

Candidate1

B + 合格事件监督

仅替换训练得到的时间LoRA，其余原生推理协议完全相同。

必须锁定以下不变量：视频源、窗口划分、sampled ordinals、native PTS、processor、输入像素预算、B0 prompt、生成语法、greedy设置、空间模型、源场、compose与输出严格验证器。

候选0不能使用新image-score prompt，因为那是另一个任务和输入分布。此前production_B评分诊断不能替代这一对照。

对3组确认来源，按来源组等权计算：

指标

	

用途




事件时间区间Precision/Recall/F1

	

主要质量指标




区间起止误差及跨镜误选率

	

判断剪辑边界




非高光窗口误报率

	

评估B强制输出的代价




选中时长占比与整窗占比

	

排查长段过选




每来源组F1差值和最差退化

	

防止均值掩盖失败




工程合法率与完整帧身份

	

独立硬约束

已见TVSum Spearman只保留为辅助研究指标，不能给candidate1授予AIC质量资格。

最终STOP/GO

建议一次确认通过需要同时满足：

确认组macro时间F1相对candidate0至少提高0.05绝对值。

无确认来源组F1下降超过0.05。

时间Precision下降不超过0.02，且没有已确认跨镜错误。

非高光窗口误报不明显恶化，完整协议及参数上限通过。

后续非测试8的原生输入、空间合成、严格验证通过；质量风险不能只凭输出合法或非空消除。

数值仍是前瞻投入规则，不是AIC成绩涨幅预测。3个确认来源组的证据力有限，即使全通过，也只能支持“值得一次后续验证”，不能称可靠泛化。

**任何科学门失败，直接STOP并保留原37.66候选。**不换阈值、不回头挑checkpoint、不改teacher提示反复扩标、不启动第二种模型。若后续所有门通过，才考虑一次新的完整426生成；这一步不在本轮执行。

六、对主控的关键批评

主控已经正确撤回全空包推荐，并认识到TVSum不是AIC金标。但我认为还有一个流程问题没有被充分解决：

第二阶段准入仍然过分依赖已见TVSum代理F的点估计，而且允许非测试8全空后继续进入426。

从代码上看，stage2_pass主要要求已有研究门通过且9源macro代理F点估计优于基座。它没有要求可靠的独立事件质量参考，也没有要求新选择器在目标语义下达到最低可用性。

即便不依据复赛反馈调阈值，也可以事前登记独立非测试质量风险门。

全空不应自动判错误，因为真实无高光的窗口可以合理为空；但是连续8个非测试视频全空，也不应在没有任务语义核验的情况下仅以11strict工程通过继续放行。

这不是事后拿407修改门槛，而是指出原放行门本来就没有充分覆盖“合规但无用”的输出模式。

另一个弱点是现有agy的任务定义仍过宽。“重要动作、结果、叙事核心”允许不同标注者采用不同的取舍标准，且没有把事件能否被学生实际看到列为必要条件。扩大这种标签集合可能只会提高教师风格拟合程度，而不是提高真实高光质量。

七、对我这条主案的最强反例

假设某段30秒视频只有0.4秒真正值得保留的关键动作。

原B的64帧抽样恰好没有看到动作。agy通过更密集的观察找到了事件，独立审查也确认标注正确。

这时，用它微调原B会产生一个危险监督关系：

模型没有看到动作，却被要求输出该动作发生的准确位置。

训练损失可能下降，但模型学到的可能是依据上下文猜测事件时间，而不是可靠观察。

再考虑另一个窗口确实完全没有精彩内容。原B被约束至少输出一个区间，而更合适的模型应当输出空。这样一来，即使新LoRA在有高光的确认窗口上提高了F1，整体应用仍可能因为非高光窗口的强制输出而变差。

这个反例足以否决“只要高质量闭源标注更多数据，继续微调原B就一定有效”的论证。

所以我的训练准入同时要求事件可观察、标签覆盖完整和独立负例评价。若失败，应该承认本轮B-native微调路线不成立，而非继续堆标签。

对主案最强的机会成本质疑是：现有TVSum新模型可能只差一次正确的训练域校准，就能把较好的排序转化成可用的选择结果，而且成本比重新标注和续训B更低。

我承认这种可能性。但它依旧无法直接修复2秒整格语义和切镜边界问题，并且缺少AIC质量参考。鉴于已有37.66的原B，当前优先购买可检验的事件监督，比继续修补TVSum评分器更有决策价值。

八、最终裁决

决策项

	

意见




新237步评分器及全空ZIP

	

撤回质量候选，保留失败证据




37.66原B

	

保留为不可覆盖的candidate0




TVSum继续训练

	

NO




agy标注

	

YES，但必须事件级、原生可观察、边界审查




原B继续微调

	

有条件YES，仅一次有界SFT




强制TopK/按复赛调阈值

	

NO




100confirm或复赛逐例调参

	

NO




本轮启动实验、GPU、提交

	

NO

下一轮最值得交叉审查的两个问题是：

问题1： 在当前可合法使用的非测试来源中，能否取得足够多的、与原B实际观察一致的完整窗口监督？如果教师能看见而学生不能看见，是否应该直接判本轮监督不可训练？

问题2： 原B要求1–5个区间，意味着不能表达真正的空窗口。若确认组显示这才是主要质量瓶颈，是否应结束本轮续训路线，另立带有合法空输出的独立协议实验，而不是偷偷修改candidate1的grammar？

我的最终意见：先建立可验证的原生事件监督，再进行一次原B的小规模续训；不能证明监督完整和可观察，就不启动训练。没有独立确认质量提升，就不产新的426竞争包。

本轮只完成附件核验、历史代码及结果静态审查、独立方案裁决；没有读取100confirm、调用agy、训练模型、重新生成视频或联网。Pro余额仍按原连续账本5/8、剩3处理，不因本次会诊发生消耗。

ChatGPT 可能会出错。请核查重要信息。
最新一条回复




高

## 第一轮原始完整公开回答：grok-r00.md
SHA256=dfe12f43219e03e10c1c25fb9922d19ab771a94f6c506ecb9c26d03be209562d

工作了 34s

读取确认

任务 AIC-VIDEO-REMATCH-NEXT-20261005 / 子议题 EMPTY407-20261010 / r00。

实际读取范围：附件 context-r00.md 全文 37132 行，至末标 END_EMPTY407_R00。本地计算 SHA256 = d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0（与声明一致，但此为本次读取核对，不代表对原始 Linux 文件的独立主机验签）。未调用外部实验或联网。

事实 / 推断 / 未知

事实：原 B 双窗 37.66 / 102112 选中帧已由用户反馈；新 237 步独立 TVSum 图片评分 LoRA 在 426 上仅 3189 帧、407 空；非测试 8 全空；dev 上 Spearman 0.522 vs base 0.044，native proxy F 点估计改善但 95% CI 跨 0；agy 6 段 90 格 KEEP37/REJECT34/UNKNOWN19，1fps 声明无法独立证明完整观测，末格切镜导致整格过宽；阈值 49 仅 train 人工 80 分位冻结；新包已撤回质量推荐。
推断：407 空高度可能来自任务/域不匹配（TVSum 相对重要性 ≠ AIC 高光边界）+ 绝对分数校准偏移 + 2 秒整格扩展假设，而非单纯工程失败。
未知：真实 AIC 高光召回、官网分、闭源标注与任务定义的实际对齐程度、原 B native 在相同非测试域上的选帧分布。

唯一推荐主路线（有界、可执行）

以原 B native 视频 prompt / grammar / processor / 时钟作为 candidate0 保底。

有界工作包：在已有非测试来源（优先非测试 8 或开放非测试短片）上，用 Gemini 3.8 Flash（agy 终端，最高档）做小批事件级标注（先 3–5 个完整短域或等效 30–60 秒切片，覆盖不同内容类型）。

标注产出后，在同一非测试域上同时回放：

原 B native 预测；
新图片评分选择器的原始分数分布（不改阈值、不强制 TopK）。
用标注作为弱代理，量化两者与闭源事件边界的重合程度、空视频是否对应标注中的真实低光/无高光，以及分数是否系统偏低。此检查可区分校准偏移 vs 语义不匹配 vs 时序输入差异，且不扩大同配方 TVSum、不碰复赛输出、不生成新 426。

最强反例

TVSum 高 Spearman 仍可导致 AIC 崩塌：相对重要性高的“叙事中段/人物特写”在 AIC 短剪辑中可能是冗余过渡；2 秒整格 KEEP 会吞掉切镜后的非高光帧（agy 已实证末格扇舞→行人切换）；分数整体下移后 49 阈值把几乎所有视频判空，即使排序局部正确。CI 跨 0 的 proxy F 已提示该风险，却仍进入 426。

根因最小非测试判别检查

非测试 8（已全空）上：导出新选择器每格 scores_x20 原始分布 + 原 B native 实际选帧区间；同时用上述小批闭源事件标注计算区间 IoU / 覆盖率 / 空视频一致性。若分数中位数显著低于 TVSum train 分布且与标注高光区间错位，则优先校准/任务重定义；若原 B 与标注更重合，则新选择器路线可证伪。不读 100confirm、不按复赛输出调阈值。

标注格式 / 观测方法 / 质量接受条件

格式：事件级（非固定 2 秒格）。每条：KEEP / NO_HIGHLIGHT / UNKNOWN；精确 start/end（原生 PTS 或有理秒）；至少 1 个可见证据帧 ordinal；visible_evidence 文本；observation_scope 与 limitations 必填。
观测：原生 MP4 直接 view_file；对潜在切镜/快速动作提高密度（关键点多帧或短窗密集），不声称逐帧全覆盖；UNKNOWN 保留且不转负例。
接受条件：独立第二观察（不同模型或人工抽查）对边界与切镜一致性 ≥ 预定义比例；证据帧实际对应描述对象；整格过宽导致切镜覆盖的案例显式拒绝或拆分。同教师一致率不视为金标。

原 B 续训 vs 新选择器 + 公平对照

优先原 B native 作为 candidate0。仅当上述非测试判别显示原 B 与闭源事件明显更优，且标签质量验收通过后，才考虑从原 B adapter 续训（明确加载原 adapter SHA、保留 optimizer 状态、train-only 不足标签不凑负例）。新选择器仅作诊断对照，不直接晋升；公平对照必须同 native 输入域、同 grammar、非测试隔离。

数据源与隔离

仅用现有非测试 / 开放非测试来源；train/calibration/confirmation 源级隔离；9 个已见 TVSum dev 不得冒充盲测；新标注不混入旧人工评分训练目标；空间场继续精确复用原 8B 源场（本轮新空间调用 0）。

预算 / 停止条件

本轮仅小批标注 + 非测试回放诊断，无新 GPU 训练、无 426 生成。
停止：UNKNOWN 比例过高或边界验收失败；判别检查显示两者均与标注严重错位；达到预定义小批上限仍无清晰根因方向。
数值（如验收一致率）仅为前瞻工程投入规则，无统计保证。连续 Pro 已用 5/8，剩 3，本讨论不消耗。

对主控的批评（关键弱点）

研究门与 stage2_pass 以点估计 native proxy F > base 放行，同时明确记录配对 95% CI 跨 0，仍推进完整 426。这把“弱代理排序改善”直接当成可投入生产的信号，未能在非测试域提前拦截系统性空视频风险。工程 11strict 通过与质量证据被过度分离。

排序提升 ≠ AIC 高光质量；同教师一致率 ≠ 真值。禁止复赛调阈值、强制 TopK、读 100confirm、重复成功生成。本轮仅文字讨论，等待下一轮交叉审查后由研究项目 Pro 裁决。

## 第一轮原始完整公开回答：gemini-r00-partial-input-visible.md
SHA256=95a31c871627cefbdbb680bf2c1c465ca7f3ceaffef2f8ad7774c4e6401890e0

Gemini 说

本次输入已完整读取主控提供的附件材料及所声明的上下文信息。主控声明文件大小为 841249 字节 / 37132 行，主控声明 SHA256 为 d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0；在此明确：该散列值仅为主控环境的单方声明值，我未在本地沙箱独立验签。当前输入流在 quality_result.json 尾部数据行处自然截断，但前序完整的故障事实、全部 8 个开发/训练/评估/标注脚本源码、前置指标表格及决策链路已完全读取，足以支撑排查与技术路线界定。   
MD
+ 3

根因诊断与事实/推断/未知边界
事实、推断与未知的边界划分

确定事实：新训练 237 步 LoRA 采用 TVSum 图像打分协议（16 图拼接，20..100 整数），冻结阈值 49 来自 39 个训练源的真值 80 分位数。在 9 个已见开发源上，new 模型在 5 个源上的选中帧率为完全全空的 0.000000（-esJrBWj2d8 为 11.2%，Yi4Ij2NM7U4 为 4.4%，cjibtmSLxQ4 为 1.5%，sTEELN-vY30 为 14.8%，EYqVtI9YWJA 为 10.1%）。非测试 8 个视频全部为空，426 个复赛视频中 407 个为空。历史原 B（双窗均衡）曾获用户反馈 37.66 分。   
MD
+ 3

工程推断：407 空并非推理硬件挂起或解码崩塌，而是“预测值收缩”与“真值绝对阈值”错位叠加“固定 2 秒整格脉冲扩展”造成的全域截断。AIC 视频画面分布与 TVSum 存在分布偏移，模型输出向均值（25~45 分）聚拢，几乎无法越过硬编码的 49 分界线。   
MD
+ 1

客观未知：AIC 官方评测真实判分脚本对“空视频”的惩罚机制（是按 F1 判 0 分，还是导致提交格式校验失败）；真实复赛视频中真实正例时长的全局先验分布；以及闭源教师模型在完整视频时序下的真实动作召回率。   
MD

四大技术维度的根因隔离

目标函数与语义任务根因（Semantic & Objective Mismatch）：
TVSum 是视频摘要（Video Summarization）任务，其人工打分反映的是镜头在整个视频中的“信息代表性与冗余度”，均值主要分布在 2~3 分区间。而 AIC 是高光检测与剪辑（Highlight Moment Detection），关注强动作爆发、核心事件与叙事高潮。用摘要代表性替代高光动作性，监督信号从源头即发生语义偏移。   
MD
+ 1

校准根因（Calibration Collapse）：
这是导致 407 空的最直接导火索。主控将训练集人工真值的第 80 百分位数（49）直接作为模型预测输出的二值化硬阈值。深度模型经过回归微调后存在方差收缩（Variance Shrinkage）和均值回归效应，预测分数的经验分布根本不等于标签分布。未经过任何保序回归（Isotonic Regression）或温度校准，直接把真值分位数套用在预测值上，导致在 9 个 dev 源中已有 5 个源全空（模型最大输出从未达到 49）。   
MD
+ 1

时序与采样根因（Temporal & Grid Extrapolation）：
将每 2 秒抽取 1 帧的中点预测分数，无条件广播覆盖这 2 秒内的所有原生帧（50~60 帧）。这种阶跃矩形扩展放大了校准失误：只要采样子帧低了 1 分，整段 2 秒瞬间归零；且 2 秒固定网格完全割裂了镜头时序连续性，破坏了动作的天然起止点。   
MD
+ 1

工程与评估根因（Evaluation Metric Blindness）：
Stage 2 放行规则仅要求 native_macro_proxy_f['new'] > base。在 9 个源中，由于模型在 Yi4Ij2NM7U4 上异常拟合打出了 0.7058 的 F 值（base 仅 0.2175），单点拉高了宏平均，掩盖了超过半数源完全全空的系统性崩溃，使伪优化通过了放行闸口。   
MD
+ 1

主控致命弱点批评与最强反例
弱点批评：形式主义伪严格与指标结构性失明（Verification Theater）

主控耗费大量算力与代码，在 SHA256 账本追踪、Fraction 纳秒对齐、BGR 转 RGB 二进制哈希校验、11 项严格格式回放上构筑了看似无懈可击的防线。然而，主控在最核心的业务质量监控上存在严重的逻辑倒错：
在 PROSPECTIVE_STAGE2.md 中预先写明“empty allowed”，从而在思想上合理化了空输出；当看到 9 个开发源中 5 个全空、非测试 8 个视频全部选出 0 帧时，主控没有将其识别为灾难性异常，反而以“独立 CPU 回放通过、11 项 strict 全部 PASS、允许空是原协议行为”为由，强行推进了 426 个全量复赛推理，最终产出 407 个空视频的废弃包。主控用完美的“流程合规”掩盖了“业务死亡”。   
MD
+ 2

最强反例（The Strongest Counterexample）

构造一个退化退火模型 M
degen
	​

：
对任意输入的 16 图序列，该模型全部预测常数 30 分（低于阈值 49），但在遇到特定背景色彩的视频（例如特定亮度的一段采访）时，对其中连续两格恒定预测 50 分。
在包含 9 个开发源的集合中，M
degen
	​

 在 8 个源上的选中帧数均为 0，对应的局部指标全为 0；唯独在第 9 个源上，这两格恰好撞上了人工高光，取得局部 F=0.8。
此时计算宏平均代理指标：
   
MD

Macro Proxy F=
9
0×8+0.8
	​

≈0.0889

对照基座的宏平均指标：

Base Macro Proxy F=0.0415[cite: 1]


因为 0.0889>0.0415，该退化模型完美通过主控现行的 Stage 2 放行门槛（stage2_pass = True）！然而该模型在全域场景下的全空率高达 88.9%。这确证了：当前主控依赖的宏平均代理 F 值，极易被单一源的极端高分绑架，对大面积全空的系统性溃败毫无防御能力。   
MD
+ 1

唯一推荐执行路线：基于原 B 骨架的高光闭源蒸馏（有界闭环）

必须坚守底线原则：

排序提升不等于 AIC 高光质量，同教师一致率不等于真值。   
MD

严禁复赛调阈值、严禁强制 TopK 兜底、严禁读取 100confirm、严禁对复赛数据做输出分布逆推。   
MD

空间场沿用原 8B 冻结源场（31295 锚点），不追加空间模型调用。   
MD

路线唯一选择：彻底废弃独立的 16 图 TVSum 图像评分选择器，回归原 B native 视频时序协议作为 Candidate 0；通过终端 agy 对非测试视频执行基于切镜与动作边界的闭环标注，在原 B adapter 权重上进行小学习率时序边界微调。   
MD

[现有非测试视频 (Train/Dev/Holdout)]
                 │
                 ▼
[Shot 切镜预分段 (PySceneDetect / I-frame 强边界)]
                 │
                 ▼
[终端 agy (Gemini 3.8 Flash high) 结构化三态标注] ──> (拒绝跨镜整格/保留 UNKNOWN 隔离)
                 │
                 ▼
[严格语义与观测验收 (通过率门禁)]
                 │
                 ▼
[以原 B Adapter 为起点，加载权重续训 (Native 视频时序微调)]
                 │
                 ▼
[非测试 8 视频最小判别门禁] ──(未超越 Candidate 0 / 出现全空)──> 触发 STOP，直接回退 37.66 保底
                 │ (严格胜出)
                 ▼
[单次 426 复赛生成与打包]

1. 非测试最小判别检查（Sanity Check Gate）

在对 426 视频启动任何推理之前，必须且仅在现有的 8 个非测试视频（nontest）上执行最小判别，不通过则严禁进入复赛：

全空一票否决（Zero-Empty Veto）：8 个非测试视频中，空视频数量必须严格为 0。

帧预算合理性区间：整体选中帧占总视频帧数比例必须处于 [12%,28%] 之间，且单视频选中率标准差不得超过 10%（严禁饥饿或泛滥）。

切镜交叠惩罚：选中的高光区间与场景切换点的重合度必须小于 5%（高光不可跨越突兀切镜）。

2. 标注格式、切镜边界与真实观测接受条件

终端 agy 标注必须从“粗暴 2 秒网格打标签”升级为“Shot 约束下的事件级三态标注”：   
MD

输入预切分：禁止送入跨切镜片段。利用基础切镜工具对长视频切分为单镜头单元（Shot），候选边界严格对齐 Shot 边界。

输出格式约束：

JSON
{
  "shot_id": 12,
  "start_pts": 145000,
  "end_pts": 235000,
  "state": "KEEP | REJECT | UNKNOWN",
  "action_description": "明确的动作核心与视觉主体",
  "observed_keyframes_pts": [150000, 180000, 220000],
  "boundary_confidence": "HIGH | MEDIUM | LOW"
}


真实观测证明与接受条件：

模型必须列出其判断所依据的具体关键帧时间戳（observed_keyframes_pts），禁止仅给结果不给观测依据。   
MD

三态逻辑隔离：KEEP 必须具备明确主体动作；REJECT 必须是观察完整且明确为静态/过渡的内容；UNKNOWN 包含视野模糊、镜头快速晃动、动作未完成等一切不确定情况。   
MD

负例规则：UNKNOWN 严格作为中性掩码剔除，绝不作为负例（not_semantic_highlight_gold = true）；仅将高置信度的 REJECT 作为时序对比负例。   
MD

单段废弃规则：若一个 Shot 内存在未观察到的切镜（如 91IHQYk1IQM 尾帧行人突变案例），该 Shot 必须直接废弃或将边界截断至切镜前，严禁整格强行赋 KEEP。单视频 UNKNOWN 比例超过 35% 则整视频隔离。   
MD

3. 数据来源隔离与多维质量指标

源级强隔离：数据切分必须以原始视频 Source ID 为单位严格隔离，禁止将同源视频的不同片段混入 Train 和 Calibration/Dev 集。   
MD

替代脆弱 Proxy F 的多维指标：

事件级加权 IoU-mAP：以交并比 IoU ≥0.5 为门槛，计算高光区间的召回与精确度。

有效非空覆盖率（Non-Empty Video Coverage）：开发集视频非空率必须为 100%。

排序与边界联合增益：对有标注区间的排序相关系数改善，必须伴随帧分布方差在合理边界内。

4. 原 B Native 公平 Candidate 0

基准身份冻结：Candidate 0 明确为原始原 B adapter（权重 SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23），配合其原生视频双窗均衡 prompt 与时钟协议。   
MD

同场对照原则：所有新训练成果，必须在相同的非测试 8 视频上，与 Candidate 0 进行逐帧交并比、有效选中率及边界置信度的一对一严格对比。只有在整体边界更紧凑且覆盖合理的前提下，才构成候选升级资格。

5. 训练配方与 STOP 中止条件

训练机制：

明确继承原 B：必须显式从原 B adapter safetensors 加载权重续训，严禁从基座从头盲训。   
MD

微调参数：LoRA rank 保持原规格，冻结视觉编码器，仅微调语言注意力和时序投影层；学习率压缩至 1.5×10
−5
（采用余弦衰减），训练严格限制在 120 优化步以内，batch 保持梯度累积，防止破坏原 B 已建立的视觉语义空间。

硬性 STOP 条件（立即终止并交付 37.66 保底）：

训练过程出现 Loss 震荡不收敛或非有限值（Nonfinite Gradients）。

在非测试 8 视频执行推理后，出现任何 1 个视频全空，或选中帧比例超出 [10%,35%] 边界。

非测试集上的事件级指标未能严格胜出 Candidate 0。

算力预算消耗达到 2000 计费秒，或剩余 3 次 Pro 原簿额度面临无意义耗费时。   
MD

一旦触发任何一条 STOP 条件，严禁对 426 复赛集执行试探性推理，立刻以原字节引用历史 37.66 稳定包（SHA 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496）作为唯一交付物，终止本轮试探。   
MD




Flash
高点

Gemini 是一款 AI 工具，其回答未必正确无误。

## 第一轮原始完整公开回答：gemini-r00b.md
SHA256=2afe601ac079301ac3023dfd762c49c5657e7928442c54a5fcda827133b89dd8


读取范围确认与认知边界界定
1. 附件读取范围确认

完整读取本次上传的索引文件 context-r00b-index.md 及 4 卷分卷正文至终末标记 END_EMPTY407_R00B：   
MD
+ 1

context-r00b-index.md：2,361 字节，索引声明全文完整。   
MD

context-r00b-part01.md：104,985 字节，读取范围包含用户要求、关键事实、主控初始立场，以及自 PLAN.md 至 agy_short_clips_v2.py 前半段的所有报告与核心代码。   
MD

context-r00b-part02.md：2,487 字节，完整承接 agy_short_clips_v2.py 的执行函数及终态，平滑衔接进入 quality_result.json 的起始定义。   
MD

context-r00b-part03.md：123,573 字节，完整读取格式压缩后的 quality_result.json，无字段或数值截断。   
MD

context-r00b-part04.md：84,598 字节，完整读取 contest_results/completion.json、历史 b_sft8b_package_v3、b_score_aligned_package_v4、balanced_two_window_risk_v3、teacher_student_autopilot_v14、pro-p01.md 裁决、官方复赛通知快照及 temporal_common.py，读至 END_EMPTY407_R00B。   
MD

四卷拼接累计声明字节数为 315,643 字节，主控声明完整 SHA256 为 e436c71211d70252d24c6b5b3b1a458e959e3b26284e61b1bbeb7c9cd2cca479。必须客观声明：该散列值为主控单方声明，我在本交互会话中已逐行读毕全部文本流并核对末标，但未在本地操作系统环境对其进行底层独立验签。   
MD
+ 1

2. 客观事实、机制推断与未知边界划分
客观事实（已有日志与代码直接证明）

开发源真实分布更正：在 9 个 TVSum 已见开发源上，new 模型（237 步 LoRA，阈值 49）的实际结果为 4 个源全空、5 个源非空：   
MD
+ 1

全空源（选中帧数 = 0，占比 0.00%）：4wU_LUjG5Ic、J0nA4VgnoCo、JKpqYvAdIsw、i3wAGJaaktw。   
MD

非空源（选中帧数 > 0）：-esJrBWj2d8（11.28%）、EYqVtI9YWJA（10.07%）、Yi4Ij2NM7U4（4.44%）、cjibtmSLxQ4（1.54%）、sTEELN-vY30（14.77%）。   
MD

注：cjibtmSLxQ4 虽选出 299 帧，但选出帧的人类评分均低于 3（selected_human_below3_fraction = 1.0），导致其代理 F 值为 0.00。   
MD

全流程全空事实：非测试 8 个视频全部输出为空（8/8 空，选中 0 帧）；复赛 426 个视频输出中 407 个为空、19 个非空（仅选出 3,189 帧）。   
MD
+ 1

阈值来源：阈值 49 严格来自于 39 个训练源人工真值分数的第 80 百分位数（nearest-rank 80th percentile），并未对模型在该 prompt 下的预测分数分布做任何拟合或重校准。   
MD
+ 1

基线状态：原 B8B + 双窗均衡历史最佳成绩为用户反馈的 37.66，产生 102,112 个选中帧，ZIP SHA 为 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496。   
MD

代理指标特性：开发集上 new 模型 Macro Spearman 达到 0.5223（base 为 0.0436），但配对 native macro proxy F 改善量的 95% Bootstrap 置信区间为 [−0.001096,0.210326]，区间下界跨 0。   
MD
+ 1

机制推断（基于代码与统计特性的合理解释，非确证唯一真因）

分布收缩与硬截断错位：深度回归模型微调容易产生方差收缩与均值回归现象（预测值集中在 25~45 之间）。将人工打分的 80 分位数硬编码为预测截断线，是导致模型输出大面积跌破阈值而全空的最直接技术诱因。   
MD
+ 2

任务定义偏移：TVSum 监督的是 20 人平均的视频摘要代表性（相对重要性），而 AIC 是无 query 的短视频高光事件抽取。排序能力（Spearman）在摘要领域的提升，无法等价于 AIC 高光召回能力的成立。   
MD
+ 1

采样扩展的方差放大：将 2 秒中点采样的离散打分强行广播赋给同格全部 50~60 个原生帧，属于无边界支撑的阶跃扩展。若该采样帧的分数恰好低于 49，整段 2 秒瞬间跌落归零，放大了阈值偏置的敏感度。   
MD
+ 3

客观未知（当前材料无法证实的事项）

AIC 官方评测系统对“空视频”的真实判定惩罚逻辑（是直接判 0 分、按极低召回惩罚 F1，还是影响解包有效性）。   
MD

复赛 426 数据集中客观上“真正无高光”的真实样本比例。   
MD

闭源大模型在长时序上下文下对 AIC 真正高光事件边界的准确召回率与误报率。   
MD

根因维度的结构化排查
                        407/426 全空故障多维溯源
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   【校准根因】               【目标与语义根因】        【时序与网格根因】
真值80分位数(49)硬套       TVSum摘要代表性均值       2秒中点离散采样向
模型收缩预测值，无分       ≠ AIC强动作高光提取，     整格强行广播，丢失
布重对齐与温度校准         排序提升不等于高光质量     连续动作与镜头切分


校准根因（Calibration Mismatch）：
这是最直接的数值诱因。主控脚本将训练集标签的经验 80 分位点（49）直接作为推理时的二值化判断条件。模型预测值受正则化与损失约束，其预测分布动态范围通常窄于真值分布。缺乏保序回归、Platt 缩放或在验证集上的独立经验分位数映射，直接套用硬阈值导致绝大部分视频的预测最大值无法突破 49。   
MD
+ 3

语义与目标函数根因（Semantic & Objective Divergence）：
TVSum 的监督本质是全局代表性冗余消除（Summarization）。高相关系数（Spearman 0.52）仅证明模型在辨别“哪个画面相对更具代表性”上有所学习，但不提供“某个画面是否达到 AIC 高光剪辑准入标准”的绝对度量。   
MD
+ 2

时序与采样根因（Temporal Discretization & Bin Assumption）：
每 2 秒仅取 1 个中点原生帧送入 16 图序列。在实际视频中，快速发生的突发高光动作容易被跳过；反之，若中点落在背景过渡帧，整段 2 秒即被判定剔除。这种粗粒度时间离散化与 AIC 原生高光的毫秒级/多镜头叙事要求存在粒度失配。   
MD
+ 4

评估门禁盲区（Gate Vulnerability）：
Stage 2 放行条件仅依赖 native_macro_proxy_f['new'] > base。在 9 个源中，仅因 Yi4Ij2NM7U4 单源的 F 值由 0.2176 冲高至 0.7059（净增 0.488），便将整体宏平均拉升，掩盖了 4 个源全空、1 个源有效选帧全错（cjibtmSLxQ4）的严重系统性溃缩，导致伪进展通过了放行闸口。   
MD
+ 2

主控关键弱点批评与最强反例
弱点批评：防御性工程合规替代了业务可用性底线（Verification Theater）

主控在工程底层（哈希绑定、纳秒级有理数网格、单次 BGR 到 RGB 转换核验、CPU 预测重放及 11 项 strict 检查）展现了严密的防御性设计。然而，主控在最核心的业务质量门禁上陷入了形式主义：
在 PROSPECTIVE_STAGE2.md 中写下 empty allowed，本意是尊重“合法无高光视频可以为空”的业务规律；但主控将其扭曲成了对系统性瘫痪的免责条款——在非测试 8 视频执行结果为 empty_videos = 8（100% 全空）、426 执行结果为 empty_videos = 407（95.5% 全空）时，主控依然以“符合预定协议、11-strict PASS、允许空是原协议行为”完成了全量流水线并生成最终候选包。主控预先设立了非测试验收环节，却未赋予其阻断能力，任由明显失效的策略推演至复赛全量生产。   
MD
+ 4

最强反例（The Strongest Counterexample）

构造一个极度退化的伪模型 M
spike
	​

：
该模型对所有输入的图像格无差别输出预测分 30（均低于阈值 49），仅在极少数具有特定背景（如纯色背景）的画面中恒定输出 52。

在 9 个已见开发源中，M
spike
	​

 在 8 个源上从未出现该特征，帧预测全部低于 49，8 个源的选中帧数全部为 0，对应的局部 Proxy F 均为 0。   
MD

在第 9 个源上，该背景恰好与某处高分重合，选出了部分重合帧，取得局部 Proxy F = 0.60。

计算宏平均指标：

Macro Proxy F=
9
0×8+0.60
	​

≈0.0667


基座模型 Base 的宏平均指标为 0.0415。   
MD

依据主控预先冻结的 Stage 2 规则 native_macro_f['new'] > base（0.0667>0.0415），该退化模型将完全合规地通过门禁，被推入全量 426 推理，产出近乎全域全空的废弃结果。   
MD
+ 1

结论：现行等权宏平均代理 F 指标极易被单一源的离群收益绑架，对系统性空选崩溃完全缺乏辨识力。   
MD
+ 1

唯一可执行有界路线：回归原 B 视频时序协议（Candidate 0），探索有界闭环增量

坚决恪守前提原则：

排序提升不等于 AIC 高光质量，同教师一致率不等于真值。   
MD

严禁复赛调阈值、严禁强制 TopK 兜底、严禁读取 100confirm、严禁根据复赛输出反推参数。   
MD

空间场严密复用原 8B 冻结源场（31,295 锚点），不新增空间模型调用。   
MD
+ 1

合法无高光视频可以为空；跨镜叙事可以是完整高光事件；编码 I 帧绝不等于语义切镜。   
MD
+ 1

路线唯一选择：彻底废弃独立的 16 图 TVSum 图像评分选择器架构，以原 B（双窗均衡，37.66）原生视频时序协议作为 Candidate 0，基于终端 agy 结构化标注建立有界闭环验证。   
MD
+ 1

                  ┌──────────────────────────────────────────────┐
                  │ Candidate 0: 原B8B+双窗均衡 (37.66 冻结底线)  │
                  └──────────────────────┬───────────────────────┘
                                         │ 对照基准
                                         ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  非测试来源视频集    │ ───> │ 终端 agy (Gemini)    │ ───> │ 严格语义与观测验收   │
│ (严格按Source ID隔离)│      │ 连续时序三态结构标注 │      │ (UNKNOWN中性隔离)    │
└──────────────────────┘      └──────────────────────┘      └──────────┬───────────┘
                                                                       │ 达标放行
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ 显式继承原B Adapter  │
                                                            │ 微步续训 (极低学习率)│
                                                            └──────────┬───────────┘
                                                                       │
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ 非测试最小判别检查   │
                                                            │ (相对 Candidate 0)   │
                                                            └──────────┬───────────┘
                                                                       │ 未超越或病态偏离
                                          ┌────────────────────────────┴──────────────────────────┐
                                          ▼ 超越基准                                              ▼ 触发 STOP
                               ┌──────────────────────┐                                ┌──────────────────────┐
                               │ 单次 426 推理与打包  │                                │ 回退 37.66 历史保底  │
                               │ (严禁线上调参/补TopK)│                                │ (NO426 封存本轮工作) │
                               └──────────────────────┘                                └──────────────────────┘

1. 非测试最小判别检查（Sanity Check Gate）

在对 426 复赛集执行任何推理前，必须且仅在现有的非测试视频（nontest）上执行防御性判别，明确以下规则为前瞻工程管理规则，非统计保证事实：   
MD
+ 1

相对基准离群检验（Relative Anomaly Check）：新模型在非测试样本上的输出行为不得与 Candidate 0 发生病态偏离。若 Candidate 0 在某视频中给出了有效的高光召回，而新模型在相同输入下产生断崖式萎缩（如全空）或数量级暴增，直接判定模型进入病态区间，一票否决。   
MD
+ 3

语法与结构有效性：输出区间必须严格遵循 0 <= start < end <= clip_duration，解析失败及语法截断率必须为 0。   
MD

允许合法全空，拒绝系统性极值：允许单个无高光视频为空，但若模型在非测试集全部样本上均输出为空或均输出饱和全选，判定为分布坍塌。   
MD
+ 1

2. 标注格式、切镜边界与真实观测接受条件

终端 agy 标注必须从机械的 2 秒网格打标升级为具备事件边界意识的结构化标注：   
MD

切镜与叙事边界原则：

切镜识别工具：应使用基于像素内容连续性或直方图差异的算法（如 PySceneDetect），严禁将视频编码的 I 帧（Keyframe）直接等同于语义切镜。   
MD

跨镜叙事接纳：明确跨镜头的动作衔接、正反打对话或镜头组接可以是完整的高光事件。如果高光区间跨越了切镜，要求标注中提供该动作连续性的描述依据；对于单镜头内的独立高光，区间应紧贴动作起止，不应机械跨越无关镜头。   
MD
+ 1

标注输出格式约束：

JSON
{
  "segment_id": 0,
  "start_sec": 4.50,
  "end_sec": 12.20,
  "state": "KEEP | REJECT | UNKNOWN",
  "action_summary": "明确的主体、核心动作与叙事高潮说明",
  "observed_keyframes_seconds": [5.0, 8.5, 11.0],
  "spans_multiple_shots": false,
  "boundary_clarity": "HIGH | MEDIUM | LOW"
}


真实观测证明与接受条件：

强制可见依据：标注必须列出其实际观察到的采样时间点（observed_keyframes_seconds），禁止无支撑的区间推测。   
MD

三态逻辑隔离：KEEP 仅用于视觉特征明确的高光核心；REJECT 仅用于充分观察且确认冗余/平淡的片段；UNKNOWN 包含镜头模糊、动作起止模糊、快速晃动等一切不确定情形。   
MD

严格负例隔离：UNKNOWN 仅作为掩码排除，绝对不得当作负例监督；仅有充分观察的高置信度 REJECT 方可作为对比负例。   
MD

单段废弃规则：若某段高光区间在尾部被证实切入完全无关的静态路人（如 91IHQYk1IQM 案例），该区间必须被截断至切镜前，或标记为 UNKNOWN 隔离，严禁将整段全赋 KEEP。   
MD

3. 数据来源隔离与多维质量指标

来源级强隔离（Source-Level Isolation）：切分必须以原始视频 Source ID 为最小原子单位，彻底物理隔离 Train、Dev、Holdout，严禁同源视频的不同片段跨 split 渗透。   
MD
+ 1

多维评价体系（取代脆弱的单点 Proxy F）：

事件级 IoU 加权 F1：在有标注的非测试集合上，以时间交并比（IoU ≥0.5）为准绳评估边界质量。   
MD

逐源胜率（Source-Level Win Rate）：在验证集上，新模型相对 Candidate 0 表现改善的源必须占多数，且最差单源退化幅度必须受限。   
MD
+ 1

选帧分布散度监测：监控新模型与 Candidate 0 在选帧比例上的分布差异，防止阈值偏移导致整体漂移。   
MD
+ 1

4. 原 B Native 公平 Candidate 0

基线身份锁定：Candidate 0 严格为已获 37.66 的原 B adapter（权重 SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23），配合其双窗均衡提示词、原生 video 标签与时钟配置。   
MD
+ 1

公平比对原则：任何新训练或新配置，必须在同一组非测试视频、同等解码配置与完全一致的空间场下，与 Candidate 0 展开端到端的选帧重合度及事件边界一对一比对，未全面优于 Candidate 0 前不得晋升。   
MD
+ 1

5. 训练机制与硬性 STOP 终止条件

微调机制：

显式续训：严禁从原始基座从头盲训，必须显式加载原 B adapter 权重作为初始化。   
MD
+ 1

训练超参数管理建议：冻结视觉编码器与主干权重，仅微调语言 LoRA；学习率建议收敛在极小范围（如 1×10
−5
），优化步建议控制在 50 步以内或采用早停策略，防止破坏原 B 已建立的时序感知空间。   
MD
+ 1

硬性 STOP 条件（立即终止并回退 37.66 保底）：

训练初期 Loss 发生发散、震荡或出现非有限数值（NaN/Inf）。   
MD
+ 1

在非测试样本推理中，出现与 Candidate 0 的系统性偏离（如 Candidate 0 有正常选帧，而新模型出现全空，或选帧总量发生量级萎缩）。   
MD
+ 1

验证集上的事件级评测与逐源胜率未能严格击败 Candidate 0。   
MD
+ 1

连续 Pro 预算原簿累计已达 5/8（剩余 3 次），禁止为无质量突破的中间过程耗费 Pro 裁决。   
MD

一旦触发上述任何一项 STOP 条件，立即停止向复赛 426 集推演，以历史 37.66 保底包（SHA 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496）作为本轮唯一交付产物，封存所有实验产物与账本。   
MD




Flash
高点

Gemini 是一款 AI 工具，其回答未必正确无误。

## 补充原文件全文：reports/qwen8b_annotation_20261009_v1/training_v2/train_lora.py
字节=5297 SHA256=46b3ef67cbed55b29db77d29b010b16b49474d831b918dc8fb60664260169614

```py
"""Explicit preflight/train entry. Default preflight never loads model weights or CUDA."""
import argparse
import hashlib
import json
from pathlib import Path

from sft_contract import ImageSFTCollator, load_rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    p.add_argument('--dataset-root', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--train', action='store_true', help='Explicitly authorize this invocation to load weights and optimize')
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    root = Path(args.dataset_root).resolve(strict=True)
    from verify_bundle import verify
    verify(root)
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory; no overwrite or implicit resume')
    rows = {s: load_rows(root / config[f'{s}_file'], root) for s in ('train', 'validation')}
    if {r['source_group'] for r in rows['train']} & {r['source_group'] for r in rows['validation']}:
        raise ValueError('Train/validation source leakage')
    if any(r['task'] != config['task'] for s in rows.values() for r in s):
        raise ValueError('Do not silently mix tasks')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True,
                                             min_pixels=config['min_pixels'], max_pixels=config['max_pixels'])
    model_config = Path(args.model) / 'config.json'
    expected = config.get('model_config_sha256')
    actual = hashlib.sha256(model_config.read_bytes()).hexdigest()
    if expected is None or actual != expected:
        raise ValueError('Model config identity is missing or changed')
    collator = ImageSFTCollator(processor, root, max_tokens=config['max_input_tokens'])
    # Every real row is processed before any model/optimizer operation. Refuse silent truncation.
    stats = {}
    for split, records in rows.items():
        counts, supervised = [], []
        for row_index, row in enumerate(records):
            encoded = collator.encode(row)
            counts.append(encoded['input_ids'].shape[1])
            supervised.append(int((encoded['labels'] != -100).sum()))
            if row_index % 20 == 0:
                print(json.dumps({'stage': 'PROCESSOR_PREFLIGHT', 'split': split,
                                  'done_rows': row_index + 1, 'expected_rows': len(records)}), flush=True)
        stats[split] = {'rows': len(records), 'max_tokens': max(counts), 'min_assistant_tokens': min(supervised)}
    output.mkdir(parents=True)
    receipt = {'status': 'PASS_ALL_REAL_IMAGE_ROWS_PROCESSOR_AND_MASK_PREFLIGHT', 'stats': stats,
               'model_config_sha256': actual, 'model_weights_loaded': False, 'optimizer_started': False}
    (output / 'preflight.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if not args.train:
        print(json.dumps(receipt))
        return
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen3VLForConditionalGeneration, Trainer, TrainingArguments
    if not torch.cuda.is_available():
        raise ValueError('Requested training has no CUDA device; no silent CPU fallback')
    model = Qwen3VLForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
                torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    targets = [name for name, module in model.named_modules()
               if name.endswith(tuple('.' + n for n in ('q_proj', 'k_proj', 'v_proj', 'o_proj')))
               and 'visual' not in name and 'vision' not in name and 'language_model' in name]
    if not targets:
        raise ValueError('Language-only LoRA targets not found')
    model = get_peft_model(model, LoraConfig(r=config['lora_rank'], lora_alpha=config['lora_alpha'],
                lora_dropout=config['lora_dropout'], target_modules=targets, bias='none', task_type='CAUSAL_LM'))
    model.config.use_cache = False
    training_args = TrainingArguments(output_dir=str(output / 'trainer'),
                per_device_train_batch_size=1, per_device_eval_batch_size=1,
                gradient_accumulation_steps=config['gradient_accumulation_steps'],
                learning_rate=config['learning_rate'], num_train_epochs=config['epochs'],
                warmup_ratio=0.05, weight_decay=0.01, bf16=True, gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant': False},
                remove_unused_columns=False, dataloader_num_workers=0, report_to=[],
                eval_strategy='epoch', save_strategy='epoch', save_total_limit=2,
                logging_steps=1, seed=20261009, data_seed=20261009)
    trainer = Trainer(model=model, args=training_args, train_dataset=rows['train'],
                      eval_dataset=rows['validation'], data_collator=collator)
    result = trainer.train()
    trainer.save_model(str(output / 'adapter'))
    processor.save_pretrained(output / 'adapter')
    trainer.save_state()
    (output / 'train_metrics.json').write_text(json.dumps(result.metrics, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

```


## 补充原文件全文：reports/qwen8b_annotation_20261009_v1/training_v2/sft_contract.py
字节=7250 SHA256=1656abf79b8ff266851c6d4b03bbda2840ed6bed8a2dfba280800489863186a2

```py
"""Portable Qwen3-VL image SFT contract; assistant-only loss and exact source pixels."""
import json
from pathlib import Path

import torch
from PIL import Image


def load_rows(path, root):
    root = Path(root).resolve(strict=True)
    rows = [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty dataset or duplicate row ID')
    for row in rows:
        if [m['role'] for m in row['messages']] != ['user', 'assistant']:
            raise ValueError('Expected one user message and one assistant answer')
        if row['messages'][0]['content'].count('<image>') != len(row['images']):
            raise ValueError('Image placeholders and real images must match exactly')
        answer = json.loads(row['messages'][1]['content'])
        if row['task'] == 'spatial_pixel_crop':
            if set(answer) != {'box_xyw'} or len(answer['box_xyw']) != 3:
                raise ValueError('Wrong crop target')
            if not all(type(v) is int for v in answer['box_xyw']):
                raise ValueError('Crop coordinates must be integer pixels')
        elif row['task'] in ('temporal_tvsum_frame_importance', 'temporal_tvsum_importance_x20'):
            key = 'scores_x20' if row['task'].endswith('_x20') else 'scores'
            low, high = (20, 100) if key == 'scores_x20' else (1, 5)
            if set(answer) != {key} or len(answer[key]) != len(row['images']):
                raise ValueError('Wrong temporal target length')
            if not all(type(v) is int and low <= v <= high for v in answer[key]):
                raise ValueError('TVSum scores outside declared scale')
        else:
            raise ValueError('Unrecognized task')
        for image in row['images']:
            relative = Path(image)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Only contained portable image paths are allowed')
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError('Image escapes dataset root')
    return rows


def typed_messages(row, images):
    text = row['messages'][0]['content']
    parts = text.split('<image>')
    if len(parts) - 1 != len(images):
        raise ValueError('Image count mismatch')
    content = []
    for i, part in enumerate(parts):
        if part:
            content.append({'type': 'text', 'text': part})
        if i < len(images):
            content.append({'type': 'image', 'image': images[i]})
    return [{'role': 'user', 'content': content},
            {'role': 'assistant', 'content': [{'type': 'text', 'text': row['messages'][1]['content']}]}]


class ImageSFTCollator:
    def __init__(self, processor, dataset_root, max_tokens=16384, image_loader=None):
        self.processor = processor
        self.root = Path(dataset_root)
        self.max_tokens = max_tokens
        self.image_loader = image_loader

    def _images(self, row):
        if self.image_loader is not None:
            return self.image_loader(row)
        images = []
        for path in row['images']:
            with Image.open(self.root / path) as im:
                rgb = im.convert('RGB')
                rgb.load()
                images.append(rgb)
        return images

    def encode(self, row):
        images = self._images(row)
        messages = typed_messages(row, images)
        full = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prefix = self.processor.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=True)
        encoded = self.processor(text=[full], images=images, return_tensors='pt', padding=False)
        prompt = self.processor(text=[prefix], images=images, return_tensors='pt', padding=False)
        ids = encoded['input_ids']
        n = prompt['input_ids'].shape[1]
        if ids.shape[1] > self.max_tokens:
            raise ValueError(f'No silent truncation: {ids.shape[1]} > {self.max_tokens}')
        if n >= ids.shape[1] or not torch.equal(ids[:, :n], prompt['input_ids']):
            raise ValueError('Full token sequence must have an exact user/generation prefix')
        labels = ids.clone()
        labels[:, :n] = -100
        labels[encoded['attention_mask'] == 0] = -100
        if not bool((labels != -100).any()):
            raise ValueError('No assistant target tokens')
        if 'pixel_values' not in encoded or 'image_grid_thw' not in encoded:
            raise ValueError('Real image vision tensors missing')
        if encoded['image_grid_thw'].shape[0] != len(images):
            raise ValueError('Vision grids and images disagree')
        encoded['labels'] = labels
        return encoded

    def __call__(self, rows):
        values = [self.encode(r) for r in rows]
        longest = max(v['input_ids'].shape[1] for v in values)
        pad = self.processor.tokenizer.pad_token_id
        if pad is None:
            raise ValueError('Tokenizer must define a padding token')
        batch = {}
        for key, fill in [('input_ids', pad), ('attention_mask', 0), ('labels', -100)]:
            target = values[0][key].new_full((len(values), longest), fill)
            for i, value in enumerate(values):
                n = value[key].shape[1]
                target[i, :n] = value[key][0]
            batch[key] = target
        expected = {'input_ids', 'attention_mask', 'labels', 'pixel_values', 'image_grid_thw'}
        for value in values:
            if set(value) != expected:
                raise ValueError(f'Unexpected processor tensors require explicit handling: {set(value) - expected}')
        for key in ('pixel_values', 'image_grid_thw'):
            batch[key] = torch.cat([v[key] for v in values], dim=0)
        return batch


def decode_output(text, task, image_count=None, source_size=None, ratio=None):
    """Strict JSON parsing. Never clamp, silently fall back, or infer empty as negative."""
    obj = json.loads(text)
    if task in ('temporal_tvsum_frame_importance', 'temporal_tvsum_importance_x20'):
        key = 'scores_x20' if task.endswith('_x20') else 'scores'
        low, high = (20, 100) if key == 'scores_x20' else (1, 5)
        if set(obj) != {key} or len(obj[key]) != image_count:
            raise ValueError('Temporal output count mismatch')
        if not all(type(v) is int and low <= v <= high for v in obj[key]):
            raise ValueError('Temporal output outside TVSum scale')
        return obj
    if task == 'spatial_pixel_crop':
        if set(obj) != {'box_xyw'} or len(obj['box_xyw']) != 3:
            raise ValueError('Wrong crop output')
        x, y, w = obj['box_xyw']
        if not all(type(v) is int for v in (x, y, w)):
            raise ValueError('Non-integer crop output')
        rw, rh = ratio
        if w <= 0 or w * rh % rw:
            raise ValueError('Crop height must be positive and exact integer')
        h = w * rh // rw
        iw, ih = source_size
        if x < 0 or y < 0 or x + w > iw or y + h > ih:
            raise ValueError('Crop outside source')
        return {'box_xywh': [x, y, w, h]}
    raise ValueError('Unrecognized task')

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/bw_common.py
字节=11048 SHA256=a70d2b2fd9a009291fe6c17556e5875d9918fc7a1e29170f7baa486721b6c79e

```py
"""Independent balanced-two-window input and exact unchanged-success authority."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
CAD=RUN/'context_advisory_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def utc():return datetime.now(timezone.utc).isoformat()

def save(path,value,fresh=True):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if fresh:
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    else:
        tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(p)

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def helpers():
    sys.path.insert(0,str(CAD))
    rt=load(CAD/'runtime.py','bw_original_cad_runtime')
    student,old,frames,production=rt.bind_helpers()
    ex=load(CAD/'experiment.py','bw_original_cad_experiment')
    import context_contract as cc
    return rt,ex,cc,student,old,frames,production

def verify():
    lock=read(HERE/'source_lock.json')
    for p,s in lock['files'].items():require(sha(p)==s,'frozen balanced-two-window-alignment dependency changed: '+p)
    return lock

def state(stage,**kw):
    value=dict(stage=stage,utc=utc(),pid=__import__('os').getpid(),new_optimizer_updates=0,
        new_32B_calls=0,official_score=None,uploaded=False,**kw)
    save(HERE/'progress.json',value,fresh=False);print(json.dumps(value),flush=True)

def base_job(job):
    import copy
    value=copy.deepcopy(job)
    for part in value['windows']:
        part['window']=part['base_window'];part.pop('base_window',None)
    return value

def base_path(scope,job,ix,cc):
    return CAD/('developer_01' if scope=='developer' else scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'B0/done.json'

def checked_base(scope,job,ix):
    upstream=load(RUN/'b_prompt_recovery_v1/brec_common.py','bw_preserved_base_authority')
    rt,ex,cc,student,old,frames,production=helpers()
    return upstream.checked(base_path(scope,job,ix,cc),base_job(job),ix,'B0',ex)

def local_request(job,ix,arm,identity,ex):
    require(arm=='BW','only one balanced-two-window-alignment arm')
    return dict(kind='local',window=job['windows'][ix]['window'],arm='BW',
        prompt=ex.base_texts(None)['B0'],model=identity,max_input=16384,max_output=256,
        allow_empty=True,context_audit={},sampling_recipe='EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64',
        video_size={'shortest_edge':4096,'longest_edge':25165824},
        spatial_resolution_tradeoff='ORIGINAL_TOTAL_PIXEL_BUDGET_ACTUAL_GRID_RECORDED')

def done_path(scope,job,ix,arm,cc):
    require(arm=='BW','wrong new arm')
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope!='rematch':
        return base_path(scope,job,ix,cc)
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope=='rematch':
        return HERE/'rematch_01/aliases'/cc.digest(job['video_id'])/(str(ix)+'.json')
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'BW/done.json'

def checked(path,job,ix,arm,ex):
    if '/rematch_01/aliases/' in str(path):return checked_v14_alias(path,job,ix,ex)
    if '/context_advisory_v1/' in str(path):
        scope='nontest' if '/nontest_01/' in str(path) else 'developer'
        require(str(path)==str(base_path(scope,job,ix,ex.cc)) and
            job['windows'][ix]['window']==job['windows'][ix]['base_window'],'reuse requires original exact window')
        return checked_base(scope,job,ix)
    value=read(path);ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']=='BW' and value['window']==w and value['context_audit']=={},'wrong round_alignment window/arm/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==value['parsed_segments'],'original unchanged validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'original native selection differs')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'new round_alignment raw identity')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'invalid actual token scores')
    return value

def checked_v14_alias(path,job,ix,ex):
    """Exact old success projection; no new raw response or model call."""
    alias=read(path);source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    require(alias['source']==str(source) and sha(source)==alias['source_sha256'] and
        alias['window']==job['windows'][ix]['window']==job['windows'][ix]['base_window'] and
        alias['video_id']==job['video_id'] and alias['index']==ix,'V14 alias exact authority differs')
    row=next(x for x in (read_line(s) for s in source.read_text().splitlines() if s.strip()) if x['video_id']==job['video_id'])
    original=row['windows'][ix];require(ex.cc.digest(original)==alias['original_window_digest'],'old original response changed')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=alias['window'];parsed,errors,_=parse_segments(original['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
        original['video_identity']==alias['actual_processor_identity'],'accepted V14 raw/input identity differs')
    ranges=native_segment_ranges(parsed,original['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old native selection differs')
    return dict(original,window=w,model_identity=read(HERE/'input_01/resume_manifest.json')['model_identity'],
        original_success_alias=str(path),new_model_calls=0,reused_original_T_temporal_window=True)

def read_line(s):return json.loads(s)

def v14_authority(student,model_identity):
    """Original full accepted bytes and model, before any projection is allowed."""
    source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    stage=read(source.parent/'temporal.stage.json');complete=read(RUN/'teacher_student_autopilot_v14/student_01/student_completion.json')
    require(stage['status']=='PASS_TEMPORAL_EXECUTION' and stage['invalid_windows']==0 and stage['videos']==426 and
        stage['windows']==521 and stage['output_sha256']==sha(source) and stage['input_contract']==student.INPUT_CONTRACT and
        stage['selected_adapter_sha256']==complete['selected_adapter_sha256']==model_identity['adapter_sha256'],
        'V14 exact terminal/model/inputs differ')
    rows=[read_line(s) for s in source.read_text().splitlines() if s.strip()]
    require(len(rows)==426 and len({r['video_id'] for r in rows})==426 and sum(len(r['windows']) for r in rows)==521,'V14 full denominator')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    for row in rows:
        for original in row['windows']:
            duration=original['end_sec']-original['start_sec'];e=original['video_identity']
            parsed,errors,_=parse_segments(original['raw_output'],duration,allow_empty=True)
            require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
                0<e['input_tokens']<=16384 and not e['truncation'],'old V14 original validator/input bound')
            ranges=native_segment_ranges(parsed,e['window_source_pts_sec'],e['native_processor_identity']['window_start'],duration)
            require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old V14 native selection')
    return source,stage,{r['video_id']:r for r in rows}

def is_changed(part):return part['window']!=part['base_window']

def jobs_for(scope):
    plan=read(HERE/'input_01'/(scope+'_plan.json'))
    return plan,plan['developer_jobs'] if scope=='developer' else plan['jobs']

def proof_aliases(jobs,ex,student):
    source,stage,oldrows=v14_authority(student,read(HERE/'input_01/resume_manifest.json')['model_identity'])
    aliases=[]
    for job in jobs:
        require(len(oldrows[job['video_id']]['windows'])==len(job['windows']),'old V14 window denominator')
        for ix,part in enumerate(job['windows']):
            if is_changed(part):continue
            original=oldrows[job['video_id']]['windows'][ix];w=part['window']
            require(original['start_sec']==part['start_sec'] and original['end_sec']==part['end_sec'] and
                original['video_identity']['source_frame_ids']==w['planned_source_frame_ordinals'] and
                original['video_identity']['actual_pts_sec']==w['planned_actual_pts_sec'] and
                original['video_identity']['native_processor_identity']['window_start']==w['window_pts_start_sec'],
                'unchanged exact V14 request/source/PTS/prompt differs')
            path=done_path('rematch',job,ix,'BW',ex.cc)
            save(path,dict(status='PASS_EXACT_V14_UNCHANGED_REQUEST_AUTHORITY_HANDOFF',source=str(source),source_sha256=sha(source),
                video_id=job['video_id'],index=ix,window=w,original_window_digest=ex.cc.digest(original),
                actual_processor_identity=original['video_identity'],new_model_calls=0,new_optimizer_updates=0,
                original_cost_preserved=True,not_new_raw_or_generation=True))
            checked_v14_alias(path,job,ix,ex);aliases.append(dict(path=str(path),sha256=sha(path)))
    save(HERE/'rematch_01/alias_handoff.json',dict(status='PASS_EXACT_UNCHANGED_V14_REQUESTS',aliases=aliases,
        old_validator_and_processor_receipts_referenced=True,new_decoder_calls=0,new_model_calls=0,
        original_temporal_sha256=sha(source),original_costs_preserved=True))

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/bw_engine.py
字节=6223 SHA256=3c0174fa86d25c19385b3a1a7a87e4bc1a75c260a1c1faa1f23a772e682c3b15

```py
"""One native-nearest-alignment input, original B0 prompt/greedy/validator/model."""
import argparse,time
import bw_common as c
from bw_native import decode_balanced_window,exact_ranges

def encode_balanced(processor,window,rt,student,ex):
    import torch
    from exact_pts import exact_native_pts,verify_native_encoding
    from bw_video import encode,identity
    decoded=decode_balanced_window(window);arr,metadata,plan,evidence=decoded
    with exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded=encode(processor,text=[rt.prompt(processor,ex.base_texts(None)['B0'])],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=student.VIDEO_SIZE,max_input=16384)
        verify_native_encoding(processor,encoded,native)
    return encoded,dict(**evidence,native_processor_identity=native,**identity(processor,encoded,len(arr)),
        registered_prompt_sha256=ex.cc.digest(ex.base_texts(None)['B0']))

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'BW',ex);w=job['windows'][ix]['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
    c.require(exact_ranges(v['parsed_segments'],w)==v['native_frame_realizability']['ranges'],'exact rational replay differs')
    c.require(ex.video_signature(encoded)==v['vision_tensor_signature'] and evidence==v['video_identity'],'new independent native/processor identity')
    raw=c.read(v['raw_receipt']);tok=processor.tokenizer
    c.require(tok.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],'actual output token decoding')
    from constrained_json import make_prefix_constraint,ascii_token_candidates
    import torch
    make_prefix_constraint(tok,0,__import__('fractions').Fraction(w['exact_raw_end'])-__import__('fractions').Fraction(w['exact_raw_start']),candidate_token_ids=ascii_token_candidates(tok),eos_token_ids=tok.eos_token_id,allow_empty=True).assert_complete(torch.tensor(raw['output_token_ids']))
    c.require(int(encoded['input_ids'].shape[1])==v['input_tokens'],'actual CPU token count')
    return dict(path=str(path),done_sha256=c.sha(path),input_tokens=v['input_tokens'],actual_native_processor_raw_validator_equal=True,new_model_calls=0,new_optimizer_updates=0)

def run(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
    student,old,model,processor,candidates,unused,identity=ex.loaded_model()
    c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'actual original B model differs')
    admitted={(p['scope'],p['video_id'],p['index']):p for p in c.read(c.HERE/'cpu_acceptance.json')['proofs']}
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity);fresh=reused=recovered=0;recovery={r['path']:r for r in c.read(c.HERE/'engineering_handoff.json')['recovered_successes']};began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'BW',cc)
            if part['window']==part['base_window']:
                c.checked(path,job,ix,'BW',ex);reused+=1;continue
            if str(path) in recovery:
                c.require(path.exists() and c.sha(path)==recovery[str(path)]['sha256'],'recovered exact success changed')
                c.checked(path,job,ix,'BW',ex);recovered+=1;continue
            c.require(not path.exists(),'success must not be generated twice')
            w=part['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
            proof=admitted[(scope,job['video_id'],ix)]
            c.require(proof['window']==w and proof['video_identity']==evidence and proof['vision_signature']==ex.video_signature(encoded),'actual GPU request differs from accepted native CPU input')
            from bw_attempt import attempt
            value=attempt(model,processor,encoded,evidence,w,path.parent/'raw.json',allow_empty=True,local_candidates=candidates)
            c.require(exact_ranges(value['parsed_segments'],w)==value['native_frame_realizability']['ranges'],'exact vs pinned float realizability differs')
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'BW',identity,ex)),bound_files={value['raw_receipt']:c.sha(value['raw_receipt'])},
                arm='BW',window=w,model_identity=identity,context_audit={},vision_tensor_signature=ex.video_signature(encoded))
            c.save(path,value);fresh+=1;del encoded
            if not (c.HERE/'first_real_acceptance.json').exists():
                import subprocess,os
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
                with (c.HERE/'first_replay.cpu.log').open('x') as log:
                    result=subprocess.run([c.PY,'-B',str(c.HERE/'bw_first_replay.py'),scope,job['video_id'],str(ix)],
                        cwd=c.RUN,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                c.require(result.returncode==0 and c.read(c.HERE/'first_real_acceptance.json')['separate_CPU_process'],'independent first CPU replay failed')
        c.state('RUNNING_'+scope.upper()+'_BALANCED_TWO_WINDOW',records_completed=num,total_records=len(jobs),fresh_model_calls=fresh,
            reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,new_overview_calls=0,wall_seconds=time.monotonic()-began)
    total={'nontest':8,'developer':112,'rematch':521}[scope]
    c.require(fresh+reused+recovered==total and fresh+recovered==sum(p['window']!=p['base_window'] for j in jobs for p in j['windows']),'actual fresh+exact reused denominator')
    c.save(out/(scope+'.completion.json'),dict(status='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS',utc=c.utc(),records=len(jobs),fresh_model_calls=fresh,
        model_identity=identity,reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,total_windows=total,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))


if __name__=='__main__':
    import sys
    run(sys.argv[1])

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/experiment.py
字节=18147 SHA256=da4cb613eded66626f271577e255d3b6767fc6a091d3b968d5f7343f986bfc1e

```py
"""One frozen advisory recipe: exact native CPU preflight and owned GPU jobs.

No grading data is used by selection or inference. Reference-set agreement is
computed separately after the four complete developer arms are committed.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import context_contract as cc
import runtime as rt

HERE, RUN = rt.HERE, rt.RUN


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def progress(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(json.dumps(value), flush=True)


def verify():
    lock = read(HERE / "source_lock.json")
    for path, wanted in lock["files"].items():
        cc.require(sha(path) == wanted, "registered dependency changed: " + path)
    return lock


def scope_plan(scope):
    student, old, frames, production = rt.bind_helpers()
    ref, manifest, clocks = old.inputs(scope)
    jobs, sources = [], {}
    source_clock = rt.load(HERE / "prepare.py", "cad_prepare").source_clock
    for item in manifest["records"]:
        clock = clocks[item["video_id"]]
        a = clock["arrays"]
        tick = Fraction(a["raw_time_base"])
        points = [float(x * tick) for x in a["native_pts_ticks"]]
        key = item["source_sha256"]
        # Independently scan the actual terminal packet. Do not infer an
        # overview endpoint from nominal CFR FPS or frame count.
        physical = source_clock(item, manifest["allowed_source_roots"])
        cc.require(physical["pts"] == points, "current scope registry differs from native full-source PTS")
        sources[key] = physical
        windows = []
        for j, (start, end) in enumerate(frames.window_schedule(item, manifest["kind"], clock)):
            raw_start, raw_end = production.raw_window_bounds(a, start, end)
            w = student.window_from_pts(item["source_path"], key, points, raw_start, raw_end,
                item["video_id"] + ":CAD:" + str(j), width=item["width"], height=item["height"])
            w["window_duration_sec"] = end - start
            windows.append({"start_sec": start, "end_sec": end, "window": w,
                "clock_record_sha256": clock["clock_record_sha256"], "clock_branch": clock["branch"],
                "raw_source_pts_origin_sec": float(a["raw_first_pts_ticks"] * tick)})
        jobs.append(dict(video_id=item["video_id"], source_key=key, source_group=item["source_sha256"],
            metadata=item, windows=windows))
        print(json.dumps({"stage": "SCOPE_NATIVE_CPU_SCAN", "scope": scope, "sources": len(sources)}), flush=True)
    mapping = cc.deterministic_derangement(list(sources), {k: c["duration_sec"] for k, c in sources.items()}) if scope == "nontest" else {}
    value = dict(scope=scope, jobs=jobs, sources=sources, shuffle_source_mapping=mapping, input_ref=ref,
        overview_source_files=len(sources), records=len(jobs), windows=sum(len(x["windows"]) for x in jobs),
        no_model_calls=True)
    rt.raw_write(HERE / "input_01" / (scope + "_plan.json"), value)
    return value


def overview_window(source, key):
    return cc.overview_plan(source["source_path"], key, source["pts"], source["raw_end_exclusive_sec"],
        key + ":SOURCE_OVERVIEW", width=source["width"], height=source["height"],
        observation_authority="EXACT_PERMITTED_SOURCE_FILE_NO_CROSS_FILE_UNION")


def source_tables(plan):
    return {k: read(p) for k, p in plan["source_clocks"].items()} if "source_clocks" in plan else plan["sources"]


def base_texts(old):
    from contracts import EMPTY_PROMPT
    tc = rt.load(RUN / "baseline_a_pts_v1/vendor/temporal_common.py", "cad_prompt_only")
    return {"B1": tc.PROMPT, "B0": EMPTY_PROMPT}


def arm_text(arm, window, table, donor_table, texts):
    if arm in texts:
        return texts[arm], {}
    if arm == "N":
        context = json.dumps({"source_context_provided": False,
            "missing_context_does_not_mean_no_events": True}, separators=(",", ":"))
        audit = {"context_not_provided": True}
    else:
        selected = table if arm == "R" else donor_table
        count = len(selected["overview_window"]["planned_actual_pts_sec"])
        own_pts = table["overview_window"]["planned_actual_pts_sec"]
        value = selected["events"]
        if count != len(own_pts):
            # Same normalized rank map for all legal short-source denominators.
            mapped = {"events": [dict(e, first=(e["first"] * (len(own_pts) - 1) // max(count - 1, 1)),
                last=(e["last"] * (len(own_pts) - 1) // max(count - 1, 1))) for e in value["events"]]}
        else:
            mapped = value
        context = cc.render_event_table(mapped, own_pts, window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"])
        audit = {"context_source_sha256": selected["overview_window"]["source_sha256"],
            "recipient_source_sha256": window["source_sha256"], "donor_raw_receipt": selected["raw_receipt"],
            "deliberately_wrong_context_diagnostic_only": arm == "X", "not_recipient_evidence": arm == "X"}
    return texts["B0"] + rt.ADVISORY_TEXT + context, audit


def tensor_sha(value):
    return hashlib.sha256(value.detach().cpu().contiguous().view(__import__('torch').uint8).numpy().tobytes()).hexdigest()


def video_signature(encoded):
    return {k: {"shape": list(v.shape), "dtype": str(v.dtype), "sha256": tensor_sha(v)}
        for k, v in encoded.items() if k in ("pixel_values_videos", "video_grid_thw")}


def cpu_preflight(draft=False):
    if not draft:
        verify()
    student, old, frames, production = rt.bind_helpers()
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates
    checks = rt.load(HERE / "tests.py", "cad_tests").test_contracts()
    cfg = old.read(RUN / "b_score_aligned_package_v4/config.json")
    processor = AutoProcessor.from_pretrained(cfg["model_dir"], local_files_only=True, min_pixels=131072, max_pixels=131072)
    candidates = rt.overview_candidates(processor.tokenizer)
    # Check the actual fixed tokenizer's whole-context ASCII additivity on all
    # candidates in several syntax/description contexts, not synthetic mocks.
    tok = processor.tokenizer
    for prefix in ('', '{"events":[{"first":', '{"events":[{"first":0,"last":0,"description":"'):
        ids = tok.encode(prefix, add_special_tokens=False)
        actual = tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        for token, piece in candidates:
            cc.require(tok.decode(ids + [token], skip_special_tokens=False, clean_up_tokenization_spaces=False) == actual + piece,
                "actual ASCII candidate is context-dependent")
    plan = read(HERE / "input_01/nontest_plan.json")
    texts, proofs = base_texts(old), []
    import torch
    for job in plan["jobs"]:
        window = job["windows"][0]["window"]
        decoded = student.decode_window(window)
        ov = overview_window(plan["sources"][job["source_key"]], job["source_key"])
        # Test real overview decode and processor without any GPU model call.
        over_decoded = student.decode_window(ov)
        overview_encoded, ov_evidence = rt.encode_decoded(processor, over_decoded, rt.OVERVIEW_TEXT)
        dummy = {"events": {"events": [{"first": 0, "last": 0, "description": "visible activity"}]},
            "overview_window": ov, "raw_receipt": "CPU_CONTRACT_ONLY"}
        common = None
        for arm in ("B1", "B0", "N", "R", "X"):
            text, audit = arm_text(arm, window, dummy, dummy, texts)
            encoded, identity = rt.encode_decoded(processor, decoded, text)
            signature = video_signature(encoded)
            if common is None:
                common = signature
            cc.require(signature == common, "advisory changed local video tensor/grid")
            if arm == "B0":
                original, original_identity = student.production_encode(processor, window)
                cc.require(set(original) == set(encoded) and all(torch.equal(original[k], encoded[k]) for k in encoded),
                    "new B0 encoding differs from actual V14 production function")
                cc.require(original_identity["frame_pixel_sha256"] == identity["frame_pixel_sha256"], "B0 pixel identity")
                del original
            del encoded
        proofs.append({"video_id": job["video_id"], "all_five_vision_tensors_equal": True,
            "B0_all_encoded_tensors_equal_actual_V14": True, "pixel_sha256": decoded[3]["frame_pixel_sha256"],
            "overview_pixels": ov_evidence["frame_pixel_sha256"], "overview_input_tokens": int(overview_encoded["input_ids"].shape[1])})
        del overview_encoded, over_decoded, decoded
        print(json.dumps({"stage": "CPU_REAL_PROCESSOR_NONTEST", "videos": len(proofs), "total": 8}), flush=True)
    cc.require(len(proofs) == 8, "NONTEST8 CPU denominator")
    rt.raw_write(HERE / ("draft_preflight.json" if draft else "preflight.json"), dict(checks, status="PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS",
        tokenizer_candidate_count=len(candidates), tokenizer_ascii_contexts=3, non_test_proofs=proofs,
        source_lock_sha256=None if draft else sha(HERE / "source_lock.json")))


def loaded_model():
    student, old, _, production = rt.bind_helpers()
    from sft_contract import verify_live_gpu_reservation
    from engine import load_model
    from verify_saved_smoke import canonical_frozen_hash
    from constrained_json import ascii_token_candidates
    import torch
    verify_live_gpu_reservation()
    cfg = read(RUN / "b_score_aligned_package_v4/config.json")
    cc.require(sha(Path(cfg["b_adapter"]) / "adapter_model.safetensors") == cfg["b_adapter_sha256"], "B adapter file changed")
    model, processor, count = load_model(cfg, adapter=True)
    base_hash = canonical_frozen_hash(model, torch)
    production.check_base_hash(base_hash, cfg)
    from safetensors.torch import load_file
    saved = load_file(str(Path(cfg["b_adapter"]) / "adapter_model.safetensors"), device="cpu")
    actual = {name.replace("base_model.model.", "", 1).replace(".default", ""): p.detach().cpu() for name, p in model.named_parameters() if "lora_" in name}
    # Peft save keys retain the base_model.model prefix. Match only its declared
    # canonical key transformation, not fuzzy suffixes.
    expected = {name.replace("base_model.model.", "", 1): p for name, p in saved.items()}
    cc.require(len(actual) == len(expected) == 288 and set(actual) == set(expected) and
        all(torch.equal(actual[name], expected[name]) for name in actual), "loaded 288 adapter tensors differ from B saved bytes")
    cc.require(not model.training and not any(p.requires_grad for p in model.parameters()), "inference model not frozen/eval")
    identity = dict(base_hash=base_hash, logical_parameters=count, adapter_sha256=cfg["b_adapter_sha256"],
        adapter_saved_tensor_equality=288, new_optimizer_updates=0)
    return student, old, model, processor, ascii_token_candidates(processor.tokenizer), rt.overview_candidates(processor.tokenizer), identity


def checked_done(path, request):
    value = read(path)
    cc.require(value["request_sha256"] == cc.digest(request), "attempt cache request differs")
    for p, wanted in value["bound_files"].items():
        cc.require(sha(p) == wanted, "completed attempt byte identity changed")
    cc.require(value.get("output_valid") is True, "attempt cache was invalid")
    return value


def run(stage):
    verify()
    cc.require(read(HERE / "preflight.json")["status"] == "PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS", "preflight missing")
    if stage in ("nontest", "rematch"):
        plan = read(HERE / "input_01" / (stage + "_plan.json"))
        jobs = plan["jobs"]
        out = HERE / (stage + "_01")
        arms = ("B1", "B0", "N", "R", "X") if stage == "nontest" else ("R",)
    else:
        plan = read(HERE / "input_01/developer_plan.json")
        jobs = plan["developer_jobs"]
        if stage == "pilot":
            jobs = [x for x in jobs if x["video_id"] in plan["pilot_video_ids"]]
        out = HERE / "developer_01"
        arms = ("B1", "B0", "N", "R", "X") if stage == "pilot" else ("B0", "N", "R", "X")
    out.mkdir(exist_ok=True)
    started = time.monotonic()
    student, old, model, processor, local_candidates, event_candidates, model_identity = loaded_model()
    rt.raw_write(out / (stage + ".model.json"), model_identity)
    sources = source_tables(plan)
    needed = {j["source_key"] for j in jobs}
    if "X" in arms:
        needed |= {plan["shuffle_source_mapping"][j["source_key"]] for j in jobs}
    tables, fresh_overview, reused_overview = {}, 0, 0
    for key in sorted(needed):
        w = overview_window(sources[key], key)
        request = {"kind": "overview", "window": w, "prompt": rt.OVERVIEW_TEXT, "model": model_identity,
            "max_input": 16384, "max_output": 1280, "adapter_disabled": True}
        folder = out / "overview" / key
        done = folder / "done.json"
        if done.exists():
            table = checked_done(done, request); reused_overview += 1
        else:
            encoded, evidence = rt.encode_decoded(processor, student.decode_window(w), rt.OVERVIEW_TEXT)
            raw = folder / "raw.json"
            table = rt.attempt(model, processor, encoded, evidence, w, raw, overview=True, event_candidates=event_candidates)
            table.update(overview_window=w, request_sha256=cc.digest(request), model_identity=model_identity,
                bound_files={str(raw): sha(raw)}, overview_input_tokens=int(encoded["input_ids"].shape[1]))
            rt.raw_write(done, table); fresh_overview += 1
            del encoded
        cc.validate_overview(table["raw_output"], w["planned_actual_pts_sec"])
        tables[key] = table
        progress(out / "progress.json", {"stage": stage + "_OVERVIEW", "completed": len(tables), "total": len(needed),
            "fresh_model_calls": fresh_overview, "reused_calls": reused_overview, "wall_seconds": time.monotonic() - started})
    texts = base_texts(old)
    fresh, reused = 0, 0
    for num, job in enumerate(jobs, 1):
        table = tables[job["source_key"]]
        donor = tables[plan["shuffle_source_mapping"][job["source_key"]]] if "X" in arms else table
        for ix, part in enumerate(job["windows"]):
            w = part["window"]
            decoded = student.decode_window(w)
            vision_signature = None
            for arm in arms:
                text, audit = arm_text(arm, w, table, donor, texts)
                request = {"kind": "local", "window": w, "arm": arm, "prompt": text, "model": model_identity,
                    "max_input": 16384, "max_output": 256, "allow_empty": arm != "B1", "context_audit": audit}
                folder = out / "local" / cc.digest(job["video_id"]) / str(ix) / arm
                done = folder / "done.json"
                if done.exists():
                    value = checked_done(done, request); reused += 1
                else:
                    encoded, evidence = rt.encode_decoded(processor, decoded, text)
                    sig = video_signature(encoded)
                    if vision_signature is None:
                        vision_signature = sig
                    cc.require(sig == vision_signature, "arm changed local vision tensor")
                    raw = folder / "raw.json"
                    value = rt.attempt(model, processor, encoded, evidence, w, raw, allow_empty=arm != "B1", local_candidates=local_candidates)
                    value.update(request_sha256=cc.digest(request), bound_files={str(raw): sha(raw)}, arm=arm,
                        window=w, model_identity=model_identity, context_audit=audit, vision_tensor_signature=sig)
                    rt.raw_write(done, value); fresh += 1
                    del encoded
                # Validate even exactly reused attempts against current original validator.
                from contracts import parse_segments
                parsed, errors, _ = parse_segments(value["raw_output"], w["window_duration_sec"], allow_empty=arm != "B1")
                cc.require(not errors and parsed == value["parsed_segments"], "reused original validator differs")
                if vision_signature is None:
                    vision_signature = value["vision_tensor_signature"]
                cc.require(value["vision_tensor_signature"] == vision_signature, "reused arm video identity differs")
            del decoded
        progress(out / "progress.json", {"stage": stage + "_LOCAL", "videos": num, "total": len(jobs),
            "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overviews": fresh_overview,
            "reused_overviews": reused_overview, "wall_seconds": time.monotonic() - started})
    rt.raw_write(out / (stage + ".completion.json"), {"status": "PASS_ALL_REGISTERED_ADVISORY_ATTEMPTS",
        "stage": stage, "records": len(jobs), "source_files": len(needed), "arms": list(arms),
        "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overview_calls": fresh_overview,
        "reused_overview_calls": reused_overview, "model_identity": model_identity, "wall_seconds": time.monotonic() - started})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare-nontest", "prepare-rematch", "draft-preflight", "preflight", "nontest", "pilot", "full", "rematch"))
    args = parser.parse_args()
    if args.stage.startswith("prepare-"):
        scope_plan(args.stage.split("-", 1)[1])
    elif args.stage in ("preflight", "draft-preflight"):
        cpu_preflight(draft=args.stage == "draft-preflight")
    else:
        run(args.stage)

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/runtime.py
字节=10161 SHA256=73f014e20034e0c61e9d57fe927ec7c69392f2d5f5e7a2f3f9f06ca6efa614b9

```py
"""C-advisory inference, binding frozen V14 native decoder and B adapter.

All output attempts first receive an exclusive raw receipt. Validation never
overwrites an attempt, fills an event, repairs a boundary or converts failure
to empty. Overview inference disables B's adapter; local inference enables it.
"""
import contextlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
sys.path.insert(0, str(HERE))
import context_contract as cc

OVERVIEW_TEXT = (
    "Describe visible activities in this sparse overview of one source video. "
    "This is factual context, not a highlight selection. Number the actual supplied "
    "video frames from 0 in their displayed order. Return ONLY canonical JSON "
    '{"events":[{"first":0,"last":1,"description":"brief visible activity"}]}. '
    "Use 0 to 8 events. Each first and last is an actual supplied frame number, "
    "0 <= first <= last < the supplied frame count. Use concise English descriptions "
    "of at most 80 characters. Include only activities directly visible in those "
    'frames; do not infer unseen actions or label highlights. If none can be described, '
    'return {"events":[]}. Sparse frames can miss short events.'
)
ADVISORY_TEXT = (
    "\nAdditional sparse source-video context follows. It describes sampled visible "
    "activities, not highlight labels. It can be incomplete or irrelevant. Judge "
    "the current local video visually; a missing event is not a negative example. "
    "Do not let this context exclude any visible local event. Source times in the "
    "table are not clip-local output boundaries. Output boundaries still follow "
    "the original clip-local rules above.\nSOURCE_CONTEXT_JSON:\n"
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind_helpers():
    student = load(RUN / "teacher_student_autopilot_v14/train_student.py", "cad_v14_student")
    student.helper_paths(RUN)
    # production_t imports train_student by its public name.
    sys.modules["train_student"] = student
    production = load(RUN / "teacher_student_autopilot_v14/production_t.py", "cad_v14_production")
    student, common, frame_contract, source = production.helpers()
    return student, common, frame_contract, production


def raw_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def prompt(processor, text):
    value = processor.apply_chat_template([{"role": "user", "content": [{"type": "text", "text": text}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return value.replace("<|im_start|>user\n", "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)


def encode_decoded(processor, decoded, text):
    import torch
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    student = sys.modules["train_student"]
    arr, metadata, plan, evidence = decoded
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt(processor, text)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=student.VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**evidence, native_processor_identity=native,
        **identity(processor, encoded, len(arr)), registered_prompt_sha256=cc.digest(text))


def overview_candidates(tokenizer):
    alphabet = cc.DESCRIPTION_CHARS | frozenset('{}[]"0123456789,')
    # The same documented ASCII advisory prefilter used by the local grammar.
    result = []
    for token in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= alphabet:
            result.append((token, piece))
    return tuple(result)


class OverviewPrefix:
    def __init__(self, tokenizer, prompt_length, frames, candidates, eos):
        self.tokenizer, self.prompt_length = tokenizer, prompt_length
        self.grammar = cc.OverviewGrammar(frames)
        self.eos = [eos] if isinstance(eos, int) else list(eos)
        self.candidates = [(i, p) for i, p in candidates if i not in self.eos]
        self.cache = {}
        self.pieces = dict(self.candidates)
        self.stats = {"calls": 0, "candidate_count": len(self.candidates), "full_context_decodes": 0}

    def decode(self, ids):
        self.stats["full_context_decodes"] += 1
        return self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)

    def __call__(self, batch, input_ids):
        ids = tuple(input_ids.tolist()[self.prompt_length:])
        self.stats["calls"] += 1
        if ids in self.cache:
            return self.cache[ids]
        text = self.decode(list(ids))
        cc.require(text == "".join(self.pieces[i] for i in ids),
            "actual full-context ASCII token decoding not additive; STOP")
        if self.grammar.complete(text):
            allowed = self.eos
        else:
            cc.require(self.grammar.valid_prefix(text), "invalid overview prefix; no recovery")
            self.grammar.prepare(text)
            allowed = []
            for token, piece in self.candidates:
                # Incremental ASCII automaton; the actual selected HF prefix is
                # whole-context decoded and checked for additivity on every call.
                if self.grammar.can_extend(piece):
                    allowed.append(token)
        cc.require(allowed, "overview generation dead end; no output repair")
        self.cache[ids] = allowed
        return allowed


def attempt(model, processor, encoded, evidence, window, raw_path, *, overview=False,
            allow_empty=True, local_candidates=None, event_candidates=None):
    import torch
    from constrained_json import make_prefix_constraint
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    prefix = int(encoded["input_ids"].shape[1])
    eos = model.generation_config.eos_token_id
    constraint = (OverviewPrefix(processor.tokenizer, prefix,
        len(window["planned_actual_pts_sec"]), event_candidates, eos) if overview else
        make_prefix_constraint(processor.tokenizer, prefix, window["window_duration_sec"],
            candidate_token_ids=local_candidates, eos_token_ids=eos, allow_empty=allow_empty))
    started = time.monotonic()
    try:
        with (model.disable_adapter() if overview else contextlib.nullcontext()), torch.inference_mode():
            generated = model.generate(**encoded.to("cuda"), do_sample=False,
                max_new_tokens=1280 if overview else 256, prefix_allowed_tokens_fn=constraint,
                return_dict_in_generate=True, output_scores=True)
        torch.cuda.synchronize()
        ids = generated.sequences[0, prefix:]
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        selected_scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
        # Save the exact model answer before ANY completeness or validity check.
        receipt = {"raw_output": raw, "output_token_ids": ids.tolist(),
            "selected_token_scores": [x if math.isfinite(x) else str(x) for x in selected_scores], "input_tokens": prefix,
            "actual_model_call": True, "overview_adapter_disabled": overview,
            "window": window, "video_identity": evidence,
            "generation_seconds": time.monotonic() - started, "constraint_stats": constraint.stats}
        raw_write(raw_path, receipt)
        cc.require(selected_scores and all(math.isfinite(x) for x in selected_scores), "nonfinite actual selected token scores")
        if overview:
            value = cc.validate_overview(raw, window["planned_actual_pts_sec"])
            result = {"status": "LEGAL_EMPTY_EVENTS" if not value["events"] else "MODEL_OK_EVENTS",
                "output_valid": True, "events": value, "sparse_not_complete_observation": True,
                "descriptions_are_model_claims_not_semantic_truth": True}
        else:
            constraint.assert_complete(ids)
            segments, errors, warnings = parse_segments(raw, window["window_duration_sec"], allow_empty=allow_empty)
            cc.require(segments is not None and not errors, "local parse rejected: " + repr(errors))
            ranges = native_segment_ranges(segments, evidence["window_source_pts_sec"],
                window["window_pts_start_sec"], window["window_duration_sec"])
            result = {"status": "MODEL_OK" if segments else "LEGAL_EMPTY", "output_valid": True,
                "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
                "native_frame_realizability": {"status": "PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges": ranges,
                    "not_limited_to_64_teacher_samples": True}}
        result.update(raw_output=raw, raw_receipt=str(raw_path), video_identity=evidence,
            constraint_stats=constraint.stats, generation_time_constraint=True,
            input_tokens=prefix, output_tokens=len(ids), generation_seconds=time.monotonic() - started)
        return result
    except Exception as error:
        failure = {"status": "STOP_ACTUAL_GENERATION_OR_VALIDATION_FAILURE", "failure_converted_to_empty": False,
            "error": type(error).__name__ + ": " + str(error), "traceback": traceback.format_exc(),
            "raw_receipt_exists": Path(raw_path).exists()}
        raw_write(str(raw_path) + ".failure.json", failure)
        raise

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/train_student.py
字节=78139 SHA256=7b79a6713e3a406d015bc546fc45ce6172b7cf8d3967592779bfdd8c23a6fe09

```py
"""One admitted Route A run: inspect an early prefix, compare B and T on weak dev.

All model imports are deferred until authority/data/semantic admission passes.
This engine never downloads, transfers, opens confirm/test, or starts a GPU job.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import statistics
import subprocess
import sys
import time
import traceback

REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
HERE = Path(__file__).resolve().parent
VERSION = HERE.name
INITIAL_SHA = "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23"
APPROVED_MANIFEST_SHA = {"train": "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf",
                         "dev": "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"}
VIDEO_SIZE = {"shortest_edge": 4096, "longest_edge": 25165824}
INPUT_CONTRACT = {
    "max_frames": 64, "video_size": VIDEO_SIZE, "max_input_tokens": 16384,
    "clock": "REAL_SOURCE_PRESENTATION_PTS_RELATIVE_TO_WINDOW_START",
    "sampling": "SELECTED_WINDOW_INTEGER_FLOOR_ENDPOINTS",
    "decoder": "SEQUENTIAL_PYAV_RGB24_WITH_ACTUAL_PTS_AND_PIXEL_SHA",
    "allow_empty": True, "prompt": "NEXT_ROUND_0_TO_5", "truncation": False,
    "same_contract_train_dev_production": True,
    "endpoint_precision": "EXACT_FINITE_DECIMAL_UP_TO_18_FRACTIONAL_DIGITS_NO_ROUNDING",
    "positive_segment_realizability": "ACTUAL_SOURCE_PTS_HALF_OPEN_NONEMPTY",
}
REQUIRED_HELPERS = (
    "next_round_v1/common.py", f"{VERSION}/precision_helpers/contracts.py", "next_round_v1/video_contract.py",
    f"{VERSION}/precision_helpers/training_target.py", f"{VERSION}/precision_helpers/engine.py",
    f"{VERSION}/supervision/validate_teacher.py", f"{VERSION}/supervision/select_windows.py",
    f"{VERSION}/supervision/teacher_prompt.txt", f"{VERSION}/supervision/teacher_metadata_20261007.json",
    f"{VERSION}/supervision/teacher_response.schema.json", f"{VERSION}/precision_helpers/constrained_json.py",
    f"{VERSION}/native_segment_contract.py",
    f"{VERSION}/source_color.py",
    f"{VERSION}/teacher_label.py", f"{VERSION}/boundary_ids.py",
    f"{VERSION}/teacher_prompt.txt", f"{VERSION}/review_prompt.txt",
    "baseline_a_pts_v1/exact_pts.py", "baseline_a_pts_v1/native_frames.py", "baseline_a_pts_v1/pts_contract.py",
    "baseline_a_pts_v1/a_contract.py", "temporal_sft8b_v1/sft_contract.py",
    "temporal_sft8b_v1/train_sft.py", "temporal_sft8b_v1/verify_saved_smoke.py",
    "baseline_a_pts_v1/vendor/temporal_common.py",
)
_VERIFIED_SOURCE_STATS = {}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def record_sha(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "missing bound file reference")
    path = Path(ref["path"]).resolve(strict=True)
    require(path.is_file() and sha(path) == ref["sha256"], "bound file changed: " + str(path))
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helper_paths(run):
    # Frozen modules import each other by their historical names.
    paths = [run / "next_round_v1", run / "baseline_a_pts_v1", run / "baseline_a_pts_v1/vendor",
             run / "temporal_sft8b_v1", run / VERSION / "supervision"]
    sys.path[:0] = list(map(str, paths))
    # common.py prepends old search paths. Explicit module identities, rather
    # than path priority alone, bind the entire serializer/target/generation
    # bridge to this registered version, even after a legacy import.
    precision = Path(__file__).resolve().parent / "precision_helpers"
    for name in ("contracts", "constrained_json", "engine", "training_target"):
        expected = precision / (name + ".py")
        current = sys.modules.get(name)
        if current is None or Path(current.__file__).resolve() != expected.resolve():
            load(expected, name)
        require(Path(sys.modules[name].__file__).resolve() == expected.resolve(), "precision helper binding differs: " + name)
    owner = str(Path(__file__).resolve().parent)
    if owner not in sys.path:
        sys.path.insert(0, owner)


def schedule(n, epochs=3, batch=16, seed=20261007):
    require(type(n) is int and n > 0 and type(epochs) is int and 1 <= epochs <= 3 and
            type(batch) is int and batch > 0, "invalid training schedule")
    rng = random.Random(seed)
    result = []
    for epoch in range(1, epochs + 1):
        order = list(range(n))
        rng.shuffle(order)
        for offset in range(0, n, batch):
            result.append({"epoch": epoch, "indices": order[offset:offset + batch],
                           "epoch_last": offset + batch >= n})
    require(len(result) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return result


def prefix_update_count(batches, limit=4):
    require(type(limit) is int and 2 <= limit <= 4, "early prefix update limit must be 2..4")
    require(len(batches) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return min(limit, len(batches))


def supervision_classes(targets):
    """Only actual admitted complete-window targets establish class availability."""
    require(targets, "STOP_T_NO_ADMITTED_TRAIN_SUPERVISION")
    counts = {"positive": 0, "explicit_no_highlight": 0}
    for target in targets:
        require(type(target.get("explicit_no_highlight")) is bool, "missing observed target class")
        segments = json.loads(target["target_json"])["segments"]
        require(isinstance(segments, list) and (not segments) == target["explicit_no_highlight"],
                "actual empty target and explicit NO semantics differ")
        counts["explicit_no_highlight" if target["explicit_no_highlight"] else "positive"] += 1
    require(counts["positive"] > 0, "STOP_T_NO_POSITIVE_SUPERVISION_FOR_ROUTE_A")
    return dict(**counts, rejection_supervision_available=counts["explicit_no_highlight"] > 0,
        whole_window_rejection_learning_claim=False,
        supervision_role="ACCEPTED_COMPLETE_WINDOW_WEAK_TEACHER_NOT_HUMAN_TRUTH")


def select_checkpoint(candidates):
    """Candidate zero is retained; a weak-metric tie always preserves original B."""
    require(candidates and any(c["epoch"] == 0 for c in candidates), "original B candidate zero missing")
    require(all(type(c["epoch"]) is int and c["epoch"] >= 0 and
                type(c["video_macro_f1"]) in (int, float) and math.isfinite(c["video_macro_f1"])
                for c in candidates), "invalid candidate development evidence")
    return max(candidates, key=lambda value: (value["video_macro_f1"], -value["epoch"]))


def floor_indices(first, stop, max_frames=64):
    require(type(first) is int and type(stop) is int and 0 <= first < stop and max_frames == 64,
            "invalid T source ordinal window")
    count = stop - first
    if count <= max_frames:
        return list(range(first, stop))
    return [first + i * (count - 1) // (max_frames - 1) for i in range(max_frames)]


def window_from_pts(source_path, source_sha256, points, start, end, window_id, **identity):
    """Public T production planner; points are raw presentation seconds.

    The controller supplies a SHA-bound full source PTS table and natural
    windows, including the packet-duration endpoint. It must preserve raw
    origin in start/end; this function never derives timestamps from FPS.
    """
    from bisect import bisect_left
    require(points and all(math.isfinite(t) for t in points) and all(b > a for a, b in zip(points, points[1:])),
            "full source native PTS required")
    require(math.isfinite(start) and math.isfinite(end) and start < end and end - start <= 30 + 1e-6,
            "invalid T natural time window")
    first, stop = bisect_left(points, start), bisect_left(points, end)
    ids = floor_indices(first, stop)
    return dict(identity, source_path=str(source_path), source_sha256=source_sha256, window_id=window_id,
        window_pts_start_sec=start, window_pts_end_exclusive_sec=end, window_duration_sec=end - start,
        planned_source_frame_ordinals=ids, planned_actual_pts_sec=[points[i] for i in ids],
        eligible_source_frame_count=stop - first, source_total_frames=len(points))


def validate_isolation(train, dev):
    require(train and dev and len(train) <= 512 and len(dev) <= 64, "invalid eligible train/dev denominator")
    all_ids = [r["window"]["window_id"] for r in train + dev]
    require(len(set(all_ids)) == len(all_ids), "duplicate eligible window")
    for split, values in (("train", train), ("dev", dev)):
        for row in values:
            w = row["window"]
            require(w.get("split") == split and w.get("source_group") == w.get("youtube_id"), "wrong split/source unit")
            p = PurePosixPath(w.get("source_path", ""))
            require(p.is_absolute() and ".." not in p.parts and
                    PurePosixPath("/home/inspur/aic_video_data/videos") in p.parents, "confirm/test/outside-media path rejected")
    for key in ("youtube_id", "source_path", "source_sha256"):
        require(not ({r["window"][key] for r in train} & {r["window"][key] for r in dev}), "train/dev leakage: " + key)


def validate_lineage(eligible, approved, split):
    identities = {(r["source_path"], r["youtube_id"]): set() for r in approved}
    for row in approved:
        require(row.get("split") == split, "approved manifest split changed")
        identities[(row["source_path"], row["youtube_id"])].add(row["sample_id"])
    for row in eligible:
        window = row["window"]
        key = (window["source_path"], window["youtube_id"])
        parents = window.get("parent_sample_ids")
        require(key in identities and isinstance(parents, list) and parents and
                set(parents) <= identities[key], "eligible source/parent not in approved original " + split + " registry")


def validate_raw_semantic(item, original):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate raw semantic review JSON key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite raw semantic review JSON: " + value)
    value = json.loads(item["raw_response"], object_pairs_hook=pairs, parse_constant=invalid_constant)
    require(isinstance(value, dict) and set(value) == {"window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"},
            "raw semantic review response schema changed")
    require(value["window_id"] == original["window_id"] and value["semantics_consistent"] is True and
            value["uncertain"] is False and value["issues"] == [] and value["reason"] == item["reason"] and
            isinstance(value["reason"], str) and value["reason"].strip(), "raw semantic review does not support receipt PASS")
    scope = value["observation_scope"]
    require(isinstance(scope, dict) and set(scope) == {"window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"}
            and scope["all_provided_frames_reviewed"] is True, "raw semantic review observation scope changed")
    window = original["window"]; observation = original["actual_observation"]
    for key in ("window_pts_start_sec", "window_pts_end_exclusive_sec"):
        require(type(scope[key]) in (int, float) and math.isfinite(scope[key]) and abs(scope[key] - window[key]) <= 1e-6,
                "raw semantic review window extent differs")
    points = scope["sampled_pts_sec"]
    require(isinstance(points, list) and len(points) == len(observation["actual_pts_sec"]) and
            all(type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= 1e-6 for a, b in zip(points, observation["actual_pts_sec"])),
            "raw semantic review did not observe same actual PTS")
    require(item.get("parsed_response") == value and item.get("source_frame_pixel_sha256") == observation["frame_pixel_sha256"] and
            item.get("source_frame_ordinals") == observation["source_frame_ordinals"] and item.get("actual_pts_sec") == observation["actual_pts_sec"],
            "semantic review raw/frame identity differs from teacher observation")


def verify_semantic(review, validation_sha, file_hashes, eligible, records, verifier, validator):
    """Engineering-complete review admits only individually supported records.

    Every reviewed raw decision is checked, including disagreement/UNKNOWN.
    The full denominator and all original records remain SHA-bound.
    """
    require(review.get("schema") == "aic_automated_weak_semantic_review_v2" and
            review.get("status") == "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW" and
            review.get("mode") == "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH" and
            review.get("manual_ground_truth") is False and review.get("confirm_opened") is False and
            review.get("contest_assets_opened") is False and
            review.get("second_review_same_teacher_not_independent_evidence") is True and
            review.get("review_blind_to_first_answer") is True and
            review.get("no_unknown_or_unobserved_gaps_certified_negative") is True and
            review.get("no_forced_empty_quota") is True, "STOP_T_SEMANTIC_REVIEW_REQUIRED")
    require(review.get("validation_receipt_sha256") == validation_sha and review.get("files") == file_hashes,
            "semantic review does not bind actual supervision files")
    eligible_expected = {r["teacher_record_sha256"] for r in eligible}
    expected = set(records)
    reviewed = review.get("reviewed_teacher_record_sha256", [])
    supported = review.get("supported_teacher_record_sha256", [])
    require(isinstance(reviewed, list) and len(set(reviewed)) == len(reviewed) and set(reviewed) == expected,
            "eligible semantics not exhaustively reviewed")
    require(isinstance(supported, list) and len(set(supported)) == len(supported) and set(supported) <= eligible_expected,
            "unknown/foreign/duplicate supported teacher record")
    raw_path = bound(review["raw_review_receipts"])
    raw = rows(raw_path)
    indexed = {r.get("teacher_record_sha256"): r for r in raw}
    require(len(indexed) == len(raw) and expected == set(indexed), "missing/duplicate/foreign real blind reviews")
    actual_supported = set()
    classification = {}
    actual_table = []
    for digest in expected:
        item = indexed[digest]
        original = records[digest]
        require(item.get("schema") == "aic_blind_local_window_second_selection_v1" and
                item.get("window_id") == original["window_id"] and
                item.get("program_complete_observation") is True and
                item.get("same_teacher_not_independent_truth") is True and item.get("manual_ground_truth") is False and
                (item.get("diagnostic_only") is False or verifier.approved_registered_pilot_review(item, original)) and
                isinstance(item.get("reason"), str) and item["reason"].strip() and
                item.get("reviewer_model_id") == verifier.TEACHER_ID and
                item.get("reviewer_model_revision") == verifier.TEACHER_REVISION and
                item.get("reviewer_runtime_revision") == item.get("second_teacher", {}).get("runtime_revision") and
                isinstance(item.get("raw_response"), str) and item["raw_response"].strip(),
                "STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW")
        require(item.get("raw_response_sha256") == hashlib.sha256(item["raw_response"].encode()).hexdigest() and
                item["raw_response"] == item.get("model_raw_answer"),
                "semantic review raw response not bound")
        comparison = verifier.verify_blind_review_projection(item, original, validator)
        classification[digest] = comparison["support_class"]
        if comparison["supported"]:
            expected_class = ("SUPPORTED_COMPLETE_WINDOW_NO_HIGHLIGHT" if original["explicit_no_highlight"]
                              else "SUPPORTED_COMPLETE_WINDOW_POSITIVE")
            require(comparison["support_class"] == expected_class and
                    item.get("review_status") == "PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW" and
                    item.get("uncertain") is False and item.get("semantics_consistent") is True,
                    "supported review does not agree with actual canonical target class")
            if digest in eligible_expected:
                require(original.get("sft_eligible") is True, "supported target lacks original strict eligibility")
                actual_supported.add(digest)
        else:
            require(comparison["support_class"] == "UNKNOWN" and
                    item.get("review_status") == "UNKNOWN_WEAK_SELECTION_DISAGREEMENT" and
                    item.get("uncertain") is True and item.get("semantics_consistent") is False,
                    "disagreement/UNKNOWN was changed to usable supervision")
        actual_table.append(dict(window_id=original["window_id"], split=original["split"], teacher_record_sha256=digest,
            support_class=comparison["support_class"], boundary_supported=comparison["boundary_supported"],
            reasons=comparison["reasons"]))
    require(actual_supported == set(supported), "semantic supported set differs from actual blind raw decisions")
    support_table = review.get("perrecord_support")
    require(isinstance(support_table, list) and len(support_table) == len(actual_table) and
            sorted(support_table, key=lambda value: value["teacher_record_sha256"]) ==
            sorted(actual_table, key=lambda value: value["teacher_record_sha256"]),
            "perrecord support audit differs from original blind receipts")
    selected_by_split = {split: sum(record["split"] == split for record in records.values()) for split in ("train", "dev")}
    supported_records = [records[digest] for digest in actual_supported]
    supported_count = lambda predicate: {split: sum(record["split"] == split and predicate(record)
        for record in supported_records) for split in ("train", "dev")}
    expected_counts = dict(selected_denominator=len(expected), selected_by_split=selected_by_split,
        support_class_counts=dict(Counter(classification.values())), supported_by_split=supported_count(lambda record: True),
        supported_positive_by_split=supported_count(lambda record: not record["explicit_no_highlight"]),
        supported_explicit_empty_by_split=supported_count(lambda record: record["explicit_no_highlight"]),
        unknown_count=sum(value == "UNKNOWN" for value in classification.values()),
        boundary_supported_count=sum(value["boundary_supported"] for value in actual_table))
    for key, value in expected_counts.items():
        require(review.get(key) == value, "semantic denominator/class count differs: " + key)
    return raw_path, actual_supported, dict(**expected_counts, original_eligible_records=len(eligible_expected),
        supported_records=len(actual_supported), excluded_records=len(expected - actual_supported),
        perrecord_classification=classification,
        all_original_denominators_and_bytes_bound=True,
        teacher_consistency_is_weak_evidence_not_human_truth=True)


def owns(path, run):
    """All student stages must stay under this independent version, not v1."""
    return Path(run).resolve() / Path(__file__).resolve().parent.name in Path(path).resolve().parents


def admit(args):
    run = Path(args.run_dir).resolve(strict=True)
    labels = Path(args.labels_dir).resolve(strict=True)
    out = Path(args.out_dir).resolve()
    require(owns(out, run) and not out.exists(), "fresh owned output directory required")
    config_path = Path(args.config).resolve(strict=True)
    config = read(config_path)
    require(config.get("schema") == "aic_t_student_config_v1" and config.get("authorized") is True and
            config.get("formal_C_BCE_admitted") is False and config.get("official_upload_authorized") is False,
            "student execution authority/scope missing")
    require(config.get("input_contract") == INPUT_CONTRACT, "T train/dev/production input contract differs")
    opt = config["optimization"]
    expected = {"lr": 1e-5, "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8,
                "weight_decay": 0.0, "grad_clip_norm": 1.0, "effective_batch_windows": 16,
                "microbatch_windows": 1, "gradient_accumulation_steps": 16, "max_epochs": 3,
                "prefix_update_limit": opt.get("prefix_update_limit"), "seed": 20261007, "precision": "bf16", "attn_implementation": "sdpa",
                "gradient_checkpointing_use_reentrant": False}
    require(opt == expected, "frozen student optimization recipe changed")
    require(type(opt["prefix_update_limit"]) is int and 2 <= opt["prefix_update_limit"] <= 4,
            "early prefix update limit must be 2..4")
    require(config.get("dev_stop_rule") == {"all_selected_fraction": 0.99, "widespread_degraded_group_fraction": 0.75,
                "widespread_macro_f1_drop": 0.05}, "undeclared developer stop rule")
    lock_path = bound(config["source_lock"])
    lock = read(lock_path)
    files = lock.get("files", {})
    require(files and isinstance(files, dict), "source lock files missing")
    def locked(path):
        absolute = str(Path(path).resolve(strict=True))
        require(absolute in files and sha(absolute) == files[absolute], "source helper outside dynamic source lock: " + absolute)
    for relative in REQUIRED_HELPERS:
        locked(run / relative)
    locked(__file__)
    for path, digest in files.items():
        require(sha(path) == digest, "source lock changed: " + path)
    helper_paths(run)
    import sft_contract as old
    validation_path = bound(config["data"]["validation_receipt"])
    require(validation_path == labels / "validation_receipt.json", "labels directory/validation reference differs")
    validation = read(validation_path)
    require(validation.get("schema") == "aic_complete_window_validation_receipt_v1" and
            validation.get("weak_teacher_only") is True and validation.get("confirm_opened") is False and
            validation.get("contest_assets_opened") is False and validation.get("unlabelled_windows_never_converted_to_empty") is True,
            "non-test weak supervision validation required")
    hashes = {name: sha(labels / name) for name in ("eligible_train.jsonl", "eligible_dev.jsonl", "validated_records.jsonl")}
    require(validation.get("files") == hashes, "eligible/raw validated supervision bytes changed")
    eligible = {split: rows(labels / ("eligible_" + split + ".jsonl")) for split in ("train", "dev")}
    validate_isolation(eligible["train"], eligible["dev"])
    approved_paths = {}
    for split in ("train", "dev"):
        ref = config["data"]["approved_" + split + "_manifest"]
        require(ref["sha256"] == APPROVED_MANIFEST_SHA[split], "original approved split registry changed")
        path = bound(ref); approved_paths[split] = path
        validate_lineage(eligible[split], rows(path), split)
    verifier = load(HERE / "teacher_label.py", "t_registered_teacher_label")
    require(Path(verifier.__file__).resolve() == HERE / "teacher_label.py", "teacher protocol verifier identity differs")
    require(Path(verifier.boundary.__file__).resolve() == HERE / "boundary_ids.py", "native boundary protocol identity differs")
    validator = verifier.validator_for(run)
    actual_records = rows(labels / "validated_records.jsonl")
    records = {record_sha(r): r for r in actual_records}
    require(len(records) == len(actual_records) == validation.get("record_count") and
            len({record["window_id"] for record in actual_records}) == len(actual_records), "duplicate/missing validated record")
    require({split: sum(record["split"] == split for record in actual_records) for split in ("train", "dev")} ==
            {"train": 128, "dev": 32}, "original full-window collection denominator changed")
    original_by_split = {split: [dict(window=record["window"]) for record in actual_records if record["split"] == split]
                         for split in ("train", "dev")}
    validate_isolation(original_by_split["train"], original_by_split["dev"])
    for split, targets in original_by_split.items():
        validate_lineage(targets, rows(approved_paths[split]), split)
    sources = {}
    for original in actual_records:
        require(original.get("status") in ("PASS_WEAK_COMPLETE_WINDOW_TARGET", "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET",
                "EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT") and original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH",
                "original collection contains engineering-invalid or foreign teacher record")
        w, obs = original["window"], original["actual_observation"]
        validator.validate_window(w); validator.validate_observation(w, obs)
        verifier.verify_model_decision_projection(original)
        # Exact legacy first-record identity already passed its original validator.
        if not verifier.approved_legacy_record(original):
