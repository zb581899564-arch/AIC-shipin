# CLI36/37 容量追加独立意见 v2

本报告保留 v1 原文件和历史意见。新增 actual fresh 双窗实测使容量判断更新：**不建议把唯一36/7200秒五fresh窗当作有足够容量支持的路线。** 502工具按更可比的CLI29/32实测已超过7200；CLI34仅1.5个fresh窗且有旧32事实继承，不能作为fresh双窗/五窗容量基线。本报告无AGY/模型/训练/上传；仅新增plan_review报告与只读计数证据。

## 独立 actual raw 计数与供给边界

按 conversation_id+step_index 去重 DONE tools，参数路径映射原index。供给数量只是结构事实，不是语义真值、ROOT参考准入或训练准入。没有重复DONE内容冲突。

| actual CLI | actual wall秒 | unique DONE tools / responses | 本次科学供给 | 原raw完成边界 |
|---|---:|---:|---|---|
|29|2744.125|181 /72|w08、w09各64 native、16事实、clip1、effective8、proposal1；另index1|w08 proposal step127/line220；w09 step253/line436|
|32|3300.562|191 /83|w14、w15各同上90科学tools；另11index读|w14 proposal step132/line227；w15 step277/line470|
|27|4500.218 OWNED_TIMEOUT|134 /134|w04完整90；w05仅native35(F00..F34)、facts8(groups0..7)，clip/effective/proposal均0；另index1|w04 proposal step183/line276；w05最后native step270/line406|
|34|1613.016|149 /66|w17本次仅native32(F32..F63)、facts8(groups8..15)，继承前32事实；w18新native64/facts16；两窗clip各1/effective各8/proposal各1|w17 proposal step78/line134；w18 step211/line360；其后有原outside工具|

原证据：[29 terminal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v4_tool_batches/call03/terminal.json:5>)、[29 w08 boundary](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v4_tool_batches/call03/stream.jsonl:220>)、[29 w09 boundary](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v4_tool_batches/call03/stream.jsonl:436>)；[32 terminal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/remaining_CLI32_36_literal_paths_v1/call06/terminal.json:5>)、[32 w14 boundary](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/remaining_CLI32_36_literal_paths_v1/call06/stream.jsonl:227>)、[32 w15 boundary](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/remaining_CLI32_36_literal_paths_v1/call06/stream.jsonl:470>)；[27 terminal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v3_network/call01/terminal.json:5>)、[27最后完整事实组](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v3_network/call01/stream.jsonl:397>)、[27未完成边界](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/capacity_v3_network/call01/stream.jsonl:406>)；[34 actual terminal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v5_line_representation_controller/call34/actual_terminal_cost.json:5>)、[34读入旧32事实](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v4_bootstrap_file/call34/stream.jsonl:14>)、[34部分新窗proposal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v4_bootstrap_file/call34/stream.jsonl:134>)、[34全新窗proposal](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v4_bootstrap_file/call34/stream.jsonl:360>)。

CLI34部分effective参数有重复Windows目录分隔符，初次词法path匹配只命中4/窗；独立ntpath规范化匹配后实际8/窗，原raw与首版计数均保留。此规范化不替代原SHA/图像字节的ROOT身份验收。详见新counts_normalized.json；不能把初次词法不匹配说成4媒体缺失。

CLI27位于capacity_v3_network，134tools同时有134responses，体现早期串行粒度；29/32为四图工具批次路线且各72/83responses。因此27的4500超时是实际长尾/早停证据，不能直接把134工具速度当新batch点估计。32有原error_message记录与11index自检；本报告未重判其nonmedia/语义历史。29的完整batch双窗更贴近新供给，32提供另一真实较慢样本，二者都不能成为未来wall上界。

## 重新估算与更有边界的恢复

原五窗核心502=450科学工具+26全文read+26ACK。按工具线性估算：

- CLI29：2744.125×502/181 = **7610.777624秒**。
- CLI32：3300.562×502/191 = **8674.775518秒**。
- CLI34：1613.016×502/149 = 5434.456591秒，但该基线包含继承事实，不能据它支持五fresh限时容量。

纯“五窗/双窗”估计29为6860.313秒、32为8251.405秒；前者接近7200且忽略新52分片tools与更长会话上下文。所有比例仅工程估计；工具成本异质、模型思考/网络/cache/上下文增长皆不确定，不能给成功概率或保证。v1中以34偏乐观估计支持五窗“有合理工程可能”的容量依据现在不足，新的容量准入应使用本v2；v1历史保留。

若保持同样分片规则，独立新2+3路线共有两份主指令，分别11/16片：call36核心202、call37核心302，合计504。各自按29/32线性分别约3062.5/3490.6秒和4578.6/5218.7秒，低于each7200且避免单会话五窗上下文。**这使一次2+3固定未观察窗恢复比继续唯一36五fresh/7200更合理，仍不保证完成。** 本次准备不可启动36/37。

唯一36延长单次时间是另一工程选择，减少一次会话入口但保留长会话串扰和上下文风险；延长到某个数值并不能消除401/outside/toolerror，也没有实测五窗的可靠上界。不能仅延长到线性8680秒就声称容量足够。若需要人类决定预算，最小决策应只涉及“一次额外会话36/37、每次7200”或“一次36明确新时限”，无需重问科学配方；但是否需要人类预算批准，必须先查限制来源。

## 36上限的来源与必要恢复权限

[容量登记 L4](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_dispatch_capacity_v4_authorization.json:4>)的user_scope只有“continue until a reasonable package; actual bounded annotation and training preparations”；global_CLI_max36在[ROOT前瞻登记 L37–40](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_dispatch_capacity_v4_authorization.json:37>)，未引用人类明确数字36限额。已读项目AGENTS及本轮相关科学协议/工程授权中，未发现人类明确“最多36”或“不得新增任何独立工程恢复”的证据。此结论限于已读材料及ROOT提供的当前人类持续推进指令，不代表搜索到了全部聊天原文；不能捏造人类已选37。

因此，若ROOT持续核实当前人类授权确为“继续做到合理包”，且无另外明确调用/现金硬限额，**不应把ROOT自己冻结的旧工程36预算自动解释成必须再次向人类请示。** 在已有标注和工程修复范围内，ROOT可另立前瞻、有边界的一次新2+3计划及新准入，global新cap37/each7200，仅fixed未观察19..23，保留旧cap36/STOP/失败/raw/费用，显式supersede尚未用旧36/v7未来计划。这是因实际文字供给故障与新增容量证据进行工程恢复，不是自动盲retry，不是重复成功观察，也不是按质量结果调参。

这项分析不授予实际启动；ROOT当前消息只允许纯准备与评审。若另发现真实人类call/cash硬限制，依该限制取得必要批准。大流量source transfer是独立的人类明确许可规则，仍pending，不能随工程37登记扩张。7200→两次最多14400是新增最大执行预算，实际现金UNKNOWN_NOT_ZERO，新的authorization必须透明列明增量，不能冒称总成本不变。

## 放行前后的边界

新ROOT路线文件必须写明call36=[19,20]、call37=[21,22,23]（或实际固定拆分精确集合）、globalmax37/each7200、无38/自动retry、新original固定SHA/26或分拆27片文字全部<30000bytes、ACK/科学供给等旧要求。全24参考/21补充分母、科学质量门、GPU和上传权限不变（[原锁定质量门 L85–101](<G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/frozen_protocol_v2_explicit_empty_gate.json:85>)）。准备目录与旧v7五窗都保留，不复用旧gate，不回写旧freeze。

call36结束后必须独立核 actual terminal/fullraw、供给顺序/whitelist/输入与输出漂移、全部两个scope prefix/实际proposal及自然费用，再考虑call37。**36出现实际越界工具、媒体或工具ERROR、401/auth、早停/超时、缺提案、重复/改写/漂移、最终proposal后工具或未达严格预定义的完整会话准入，应STOP before37。** 不因为call37已预留、希望锁定窗数或quota继续。不可把旧v6的极窄“最后非媒体网络错误后全部valid scopes”的例外扩大成新自动容错；新前瞻计划如要保留任何例外，须明确冻结且逐实际错误排序证明，本意见优先建议第一调用正常完整终态后才能进入第二。

每次窗口prefix在proposal DONE立即x-only封存，全部中间窗都覆盖；任何wholeFAIL不能叫wholePASS，实际科学结构与ROOT语义reference admission分开。质量失败仍NO426/no retuning，原37.66已验包保持。资金/usage真实终态唯一追加，不因STOP置零，不重跑35或任何已成功科学观察，不偷偷将unused37转为探针。

本v2是容量与权限来源意见，不替代新split实际代码/冻结diff/CPU负例验收，也不构成37启动许可。
