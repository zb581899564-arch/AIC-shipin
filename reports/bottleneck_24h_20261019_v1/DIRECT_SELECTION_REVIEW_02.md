# 直接B0人工摘要监督：独立只读审查02

审查范围：仅现存代码、协议及已保存训练报告；未执行模型、训练、解码、processor、QA或比较，未读取正式预测或新增人工标签值。2026-10-19新24小时授权优先于历史停止时限；40.47原包及旧失败不变。

结论：没有在本次核到的历史链中发现“SumMe25逐评审人工摘要→单clip原B0区间JSON token SFT”已经实际完成。原TIME确实训练过相同输出形式，不能称首次时间段生成；但它使用WEAK_TEACHER704/724正窗口。PAIR17是三类双clip偏好训练，context29为冻结模型背景干预，BCE/SET为冻结特征小头，均不等价于新提议。仅支持继续新目标合同的准备与只读可表达性统计，**不准入training或GPU pilot**。原B0空输出语义与“摘要未选”不等价；所有逐评审目标能否无损装入原0–5段/256输出token合同尚未证明。后续“整源概览+excerpt→人工摘要区间”属于新输入/目标合同，不能称原B0不变；须重新审查再决定极小工程pilot。

## 1. 旧实验究竟做过什么

| 已有链 | 实际输入/监督/损失 | 与本提议的关系及证据 |
|---|---|---|
| 原TIME区间SFT | 单clip视频；WEAK_TEACHER704父项/602来源、724正窗；assistant区间JSON与终止token CE；base/vision冻结、语言q/k/v/o LoRA | 输出形式和更新位置已有，不可包装成全新架构。原训练报告实际PASS、3620有效backward/227更新/5轮；监督不是SumMe人工摘要，30个无已知正交集窗未训练。见下方TIME代码/协议。 |
| PAIR17 | 每clip8个2Hz观察、两clip；所有评审形成A/B/TIE三类软分布；只对三个digit logits算交叉熵；新PAIR adapter、原TIME未加载 | 人工监督、语言注意力可更新均已有，但并非单clip多段JSON或逐评审完整摘要序列生成。其失败保持，不加载该失败PAIR200作为新初始化。 |
| SOURCE_CONTEXT28 / GPU29 | 已冻结PAIR200/BASE；增加整源Overview，与局部A/B构成三video；optimizer0 | 不是新的摘要SFT。其不足提示全源摘要偏好与局部观察的差异仍在；不能把仅换目标称已解决语境缺失。 |
| temporal_selector BCE/SET | 冻结时序特征→CPU头；逐原生帧的评审选择概率、mean per-rater softF1 | 生成任务与可训练表示不同。原9.74/9.31及崩塌不能回写；新任务仍必须同完整40.47检查覆盖/大删选。 |
| branch_pilot | 对KEEP/ORDINARY/UNKNOWN完整固定回复做teacher-forced likelihood读出；无optimizer | 名称含teacher forcing，但没有训练直接B0人工摘要选择。 |

TIME证据（本地缓存与实际运行报告）：

- [原训练来源/窗口构造 prepare_inputs.py:31](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/prepare_inputs.py:31)：严格704/602，42行要求WEAK_TEACHER；67–90行只生成有正交集窗。
- [原token监督 train_sft.py:76](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/train_sft.py:76)：`segments_clip_local`序列化为answer，assistant suffix加入终止token，prompt/视觉token掩码后CE。旧`build_example`会重新解码并两次processor，不应直接复跑用于新用途。
- [全量协议:5](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1/PROTOCOL.md:5)、[实际训练报告](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1/train_report_completion_01.json)。后者只读取status/counter，未重跑或重新计算loss。
- [PAIR_PROTOCOL_17:7](G:/ai/AIC视频/reports/diagnostic_score_goal_20261018_v1/PAIR_PROTOCOL_17.md:7)、[pair_preference_gpu.py:345](G:/ai/AIC视频/improvement/diagnostic_score_goal_v1/pair_preference_gpu.py:345)、[SOURCE_CONTEXT_PROTOCOL_28:3](G:/ai/AIC视频/reports/diagnostic_score_goal_20261018_v1/SOURCE_CONTEXT_PROTOCOL_28.md:3)。
- [BCE/SET监督 head.py:148](G:/ai/AIC视频/improvement/temporal_selector_v1/head.py:148)、[branch_pilot.py:1](G:/ai/AIC视频/improvement/diagnostic_score_goal_v1/branch_pilot.py:1)。

上述“未发现相同训练”限定于这些已有主线和本次代码搜索，不声称穷尽全部历史归档。

## 2. SumMe人工摘要实际能支持的目标

- 原`user_score`每列是一位评审的逐帧摘要选择；正整数为片段编号，选中应取`>0`，不能把编号当强度、时间、类别或序数评分。`gt_score`是这些布尔选择的列均值，不能代替逐评审完整序列。
- 可支持“在该原作者来源上模仿人类摘要取舍”的多参考区间生成/集合预测监督；同一输入对应不同评审目标并不构成数据错误，但损失必须显式对全部原列等权求平均，不挑最有利列、不取union或多数mask冒称原始目标。`all_userIDs`长度与摘要列数的历史不一致不允许删列。
- 逐帧原生ordinal映射已存在，可把每列连续选帧run转换为原生时间范围，再按已冻结clip窗口求交。目标必须通过“序列化JSON→原parser/半开区间→native ordinal集合”完整往返相等；原作者名义FPS、video_duration、1fps网格不能生成或拉伸native标签。
- 不能支持赛事时间∧构图联合GT、明确普通/无高光负例或所有未显示动作的事实判断。源级人工摘要来自整源观看，原64帧局部clip只提供稀疏视觉观察；监督存在语境与观察覆盖限制。新模型最终输出仍须对所有评审共用一份预测。

证据：[HUMAN_REFERENCE_SCOPE:7](G:/ai/AIC视频/reports/human_reference_iteration_20261013_v1/HUMAN_REFERENCE_SCOPE.md:7)、[作者帧序映射v3:5](G:/ai/AIC视频/reports/human_reference_iteration_20261013_v1/NATIVE_MAPPING_CONTRACT_V3.md:5)、[native_mapping_v3.py:9](G:/ai/AIC视频/improvement/human_reference_v1/native_mapping_v3.py:9)、[原选帧编码检查:20](G:/ai/AIC视频/improvement/human_reference_v1/register_human_sources.py:20)。历史初始“不训练新模型”是当时阶段边界；后续[source_clear PLAN:13](G:/ai/AIC视频/reports/source_clear_residual_plan_20261018_v1/PLAN.md:13)及本轮明确人工训练授权优先，不能拿旧阶段文字循环阻塞新用途，也不能因此扩大媒体再分发范围。

## 3. B0输入、prompt、labels最需防的实质错位

1. **空摘要不是无高光。** 当前[EMPTY_PROMPT:19](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/contracts.py:19)明确`[]`代表“no worthwhile highlight”，且禁止以不确定/观察不足代空。一个评审在某窗没有摘要选帧并不能证明该句。如果坚持原prompt完全不变，并把这种空窗直接监督为`[]`，当前方案应STOP。须在一次新注册中明确摘要选择目标与空答案含义；不能通过删除空窗、把它称“普通”、临时改prompt或看结果选择来暗中解决。若选择只做正参考条件的工程试验，也必须明确不能训练拒选/空输出能力，且不是全部评审完整摘要目标。
2. **原输出容量不是无限。** B0只容许0–5段、256输出token；原旧SFT的`segments_valid`更是1–5段，拒空。逐评审native run可能超段数或token预算；本次未读取标签统计，未知是否发生。必须先登记全25源/全评审/全原窗的目标可表达性清单和精确失败分母。不能按标签多少挑窗、截前5段、合并穿过未选帧、裁掉超预算尾部或复制旧正窗过滤。表示失败应停止/明确注册统一解决规则，不自动掉样本。
3. **source-global、clip-local与真实原点不能混。** 原SumMeclock归一化减真实首PTS；当前[原RGB metadata:149](G:/ai/AIC视频/improvement/human_reference_v1/prepare_rgb_v3.py:149)已记录`original_clock_origin_exact/window_start/window_end/sample_exact_pts`。新answer必须减同一个window_start；末端用physical_end，不用容器时长。小数精度不能沿用旧round4并假定native集合无变化；必须验证往返native集合完全相等，特别是窗边界与最后帧。
4. **复用原B0输入，不以2Hz图像或PAIR拼接替代。** [runtime.encode:84](G:/ai/AIC视频/improvement/temporal_refinement_pilot/runtime.py:84)绑定原source ordinal、exact PTS与单video。训练可读取原已验收vision cache并新建文本/assistant标签；不重做旧成功processor或B0推理。现成[cv_tokens.retarget:26](G:/ai/AIC视频/improvement/candidate_verify_v2/cv_tokens.py:26)只保证prompt替换时视觉prefix不动，不是已经合格的SFT labels builder。
5. **权重与模型角色必须明示。** 新学习起点应绑定已存在TIME权重的副本和独立新输出根，不改原adapter；原8B/vision逐参数冻结，只有预先登记的语言adapter可更新。不能像BASE context代码那样disable TIME后仍声称TIME初始化，也不能暗加载PAIR200或再叠未计参数的新adapter。
6. **评审等权不能被token/窗数偷换。** 需写清源等权、同源所有评审列等权、窗权重固定且和1，及每序列CE采用token均值还是总和。若把不同长度全部token混成一个全局平均，长摘要/长视频/更多评审来源会改变预期权重。所有prompt、video、padding应mask=-100；assistant JSON及终止token受监督，核causal shift与tail-logits索引，不能监督完整prompt或把EOS漏掉。
7. **B0原输出和完整40.47不是同一基线。** 完整链含TIME VERIFY、D8、原semantic与其baseline占有率；[replay.py:120](G:/ai/AIC视频/improvement/calibrated_confirm4_v1/replay.py:120)及145–170行给出真实finalize。新B0若直接替换时间集合而仍经D8/VERIFY/semantic，应事先固定下游组合，不可评价B0后生产时临时换组合；正式只可输出原全空间场可覆盖的native集合。

## 4. 当前证据可准入到哪里

主代理报告的44源共同输出诊断提示，保留所有旧帧对摘要代理的限制比之前估计大：SumMe baseline/add/delete/replace约0.302480/0.332331/0.466458/0.500236，VideoXum约0.298799/0.390242/0.442489/0.557951。本审查仅引用其已完成结果，未重新计算。Linux证据：`/home/inspur/aic_video_work/bottleneck_24h_20261019_v1/common_output_01/result.json`。其[common_prefix实现:17](G:/ai/AIC视频/improvement/bottleneck_24h_v1/common_output_diagnostic.py:17)按人工密度排序时间组、择前缀，每源全评审共用mask；这是参考辅助的可行下界，不是模型、精确oracle或官方分。

该诊断**不证明**原64帧观察能识别这些组，也不证明其可行集合能装进每窗最多5段。它支持一次“直接内容选择”新机制的小规模工程验证理由，不能支持预计质量收益或预先采用删除策略。

允许继续的下一步仅为在同一新主线上补齐目标合同和已有输入绑定；本审查不启动这些工作。必须在GPU前冻结：

- 全部逐评审目标/空答案语义、原生往返和输出容量合同；任何遗漏/无法表示均显式记录，不按结果救样本。
- 单一初始化、可训练参数清单、固定final-only日程、保存/恢复与实际预算；极小pilot及remaining界线事先登记，成功更新不得重复。不能把pilot工程通过当质量通过。
- pilot先验证实际非零且连通梯度、冻结base/vision、有限loss、adapter变化、保存重载、输入/labels/EOS与native映射；只允许显式new remaining接续，不盲重启。
- 固定19个已曝光VideoXum的完整40.47对照与新方法确切下游规则，评价源宏/all-rater，报告删/增/空源/覆盖/逐源明显退化，不以train loss、格式正确或平均小收益掩盖大删选崩塌。19仅开发，不能据其结果再改目标/选checkpoint/换窗/阈值。

**当前判断：只支持先补目标合同，不准入training；极小工程pilot也须新合同与成本审查后单独决定。若原prompt不变且把摘要空窗当“无高光”，或无法满足全评审原生目标的段数/token表示，则保持STOP。没有证据要求复活旧PAIR/BCE/SET，也没有证据承诺这一路能突破40.47。**

## 5. 主线补充后的精确历史重复核查

主代理随后明确：先统计原25源所有window×rater的native run数及精确JSON可表达性；不GPU、不动旧prompt。拟新目标是“整源摘要选择”，新输入为源级概览+当前excerpt，空仅表示该评审没有把该excerpt选进整源摘要。此定义消除了把摘要未选冒称“毫无高光”的错误，但也**改变了任务与输入**，不能套原B0输入验收、原性能结论或原预算。现阶段仍不准入training。

本次进一步核到以下近似路线，未发现实质相同的“source overview+excerpt→SumMe逐评审直接interval SFT”旧成功/失败：

- [context_advisory_v1/PROTOCOL:7](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/PROTOCOL.md:7)：全源事实粗览关闭B adapter、局部原B开启，**训练更新0**；粗览生成文本作为局部上下文，不是人工摘要SFT。15行给出N/R/X等推理臂，不能据名称称本新输入首次包含全源信息。
- [teacher_context_diagnostic_v3/PROTOCOL:5](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_context_diagnostic_v3/PROTOCOL.md:5)：32B概览+目标64图，问相对整段源片的摘要必要性；15行明确只定位监督目标、不直接准入学生。是教师诊断，非SumMe人工训练，不可复活其教师/学生失败链。
- [SOURCE_CONTEXT_PROTOCOL_28:3](G:/ai/AIC视频/reports/diagnostic_score_goal_20261018_v1/SOURCE_CONTEXT_PROTOCOL_28.md:3)与[context_gpu.py:1](G:/ai/AIC视频/improvement/diagnostic_score_goal_v1/context_gpu.py:1)：Overview+A+B，固定PAIR200和BASE、无训练，仍输出0/1/2偏好。
- [global_context_common.py:18](G:/ai/AIC视频/improvement/sprint45_global_context_v1/global_context_common.py:18)：global8/local8图的binary global_highlight/event_payoff推理任务，并非逐评审区间SFT。
- 原TIME `build_example`实际只有当前clip单video及`tc.PROMPT`，无source overview；BCE/SET有人工摘要但不更新8B、不生成区间JSON。

这是限定现存明确近似主线的否定检索；没有证据可宣称所有历史档案均无此方案。新定义相对这些链有具体差异，**不能因此自动推定有效**。训练前仍须补：新summary prompt和空含义、overview/excerpt双方真实PTS与不同时间原点、所有评审native目标完整性、组合视觉/token实测预算、与同新输入的未更新TIME初始化基线、assistant-only mask/终止token、新scope独立注册。不得把旧多video拼接证明或旧B0首QA冒充这个新组合验收，也不得根据19开发结果换模型/目标/窗口。任何发现同输入、同人工目标、同可训练部分的旧已失败训练，应立即报告并禁止重启，而不是换名复活。

本次唯一写入本文件；未改代码/旧锁/协议/产物，未访问远端或启动任何实验。
