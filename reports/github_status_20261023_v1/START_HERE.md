## Follow-up diagnosis — no new candidate

The R01/R02 scores10.74/6.96 have now been traced through the actual frozen caches and native clocks. The major measured effect is severe temporal reduction:234159 native frames→48453 nonordinary→48250 apex-containing pool→29869 event output→15341 apex output. Only13.6%/7.1% of40.48 frames remain. All116 empty sources are explicit decisions:50 allordinary and66 with feasible but nonpositive penalized events. No source-to-ZIP, common-box or native-partition mismatch was found. Retention is not hidden-GT recall. Read [full diagnosis and evidence-bounded next plan](../github_status_20261024_v1/R_SELECTION_FAILURE_DIAGNOSIS.md) and [aggregate receipts](../github_status_20261024_v1/R_SELECTION_FAILURE_AGGREGATE.json). The next spatial-only external diagnostic is a proposal, not a registered GPU/production run. No new model/ZIP/submission occurred in this diagnosis.

## Latest: seven official DONE results — 2026-10-24

The requested5+2 sprint is complete: seven distinct426-source ZIPs passed engineering/independent11strict/Windows checks and were actually uploaded through the user-authorized Edge session. Official scores by frozen order:22.12/19.64/39.21/16.59/14.38 onOct23, then10.74/6.96 onOct24 at00:01:16/00:03:44. All are below the protected40.48; original40.47 and both dependency chains remain intact. This is completion of submissions, not improvement or the45-point goal.

Read [actual full sprint results](FINAL_SPRINT_V6_ACTUAL_RESULTS.md), [M costs and differences](M_FIVE_DELIVERY_COSTS_V6.json), and [R costs, recovery and official scores](R_TWO_DELIVERY_COSTS_V6.json). Latest terminals supersede historical pending snapshots below. Do not rerun, retune or resubmit these seven frozen recipes. No new Goal, automation or experiment is created by this handoff.

The user confirmed a QQ extension, and the account actually accepted the five entries after the old20:00 notice and the two entries after midnight. Runtime/source locks stay8dcde128be0ffe2df3ccba75d69929b7a9769a6f; explicit remaining-only CPU recovery controllerdf429691e623666fd94264ebeb8fb7b55d3dd1a9 reused all old successes with0newmodel calls and preserved all failed attempts/costs. The separately committed general forecast fix was not hot-patched into v6. All owned chains exited; GPU released; CONTROL5 untouched. No network/service or external-contact changes. Files published in this last increment are listed in [publication scope](../../docs/publication_scope_final_results_20261024.json).

# 2026-10-23最新事实与审查入口

本次同步包括10月21日上次公开快照之后的源码、固定协议和聚合结果。基于已采纳PR #5精确提交`72533ece44cb490c48cea88fab41463bdf14eb3c`，保留此前审查修复，不合并或改写其他分支。

**当前用户反馈最佳是40.48删弱包，原40.47仍保护。最新局部注意力真实8B小试完整完成，但选片退化，没有新T包。** 分数为用户反馈，未独立登录核分；下面外部代理不等于官方联合分。

## 先读这些

1. [实际结果总表](EXPERIMENT_LEDGER.md)：区分完成、质量退化、成本停止和未准入。
2. [代码与证据地图](CODE_AND_EVIDENCE_MAP.md)：完整历史报告和实际实现路径。
3. [结构化聚合](aggregate_results.json)：当前累计费用、调用、原生指标与私有短回执SHA绑定。
4. [T路线](../../T_BRANCH_PLAN_20261022.md)和[已采纳Pro计划](../../SPRINT_PLAN_20261021.md)：历史计划不覆盖后来真实终态。
5. [最新122/123结果](../t_branch_execution_20261022_v1/RESULT122_123.md)：25窗真实8B与全部首次独立CPU已过，固定科学门未过。

## 基线与交付

| 包 | 用户反馈 | 文件大小/SHA | 解释 |
| --- | ---: | --- | --- |
| SPORT_ROUTE_REMOVE | 40.48 | 384482B / `85778a086f3fb0152947ece40b8dc258c7fef717b40519fe3e23fd4f7b0fabbe` | 仅3源删27帧；不证明扩大删除有益 |
| 原CONTEXT_SEMANTIC_RESIDUAL | 40.47 | 384630B / `b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3` | 原包及全部依赖继续保护 |
| SPORT_ROUTE_RERANK | 40.12 | 384575B / `f9bd8474b07365893498d27b16c16fa21f5e7ea677e37e125b2437c50f455a6f` | 11源等覆盖替换724帧，未采用 |

两个SPORT包已经过实际426/原生PTS/空间来源/格式/CRC/最终Windows一致验收。本次不重新发布这些私有预测ZIP，仅发布聚合成绩及身份。T分支新ZIP仍0，目标未达成。

## 最新实际终态

122/123：原BASE/TIME冻结，25窗、800原生决策、50物理前向，314.609349 GPU秒；全部25首次视觉、遮挡注意力、完整词表和原生输出CPU复核通过。正确外部F1从未遮挡0.115142840降到0.081512730，覆盖11.7931%降至3.2362%。窗内AUC从0.47917升至0.52192，但低于事先固定0.55；不训练、确认或全量，不改变门后再试。

T累计21279.932355 GPU秒、3646历史口径8B任务、19旧optimizer更新。任务计数与内部物理前向不同，不能相加混称回答数量。4个原确认来源质量仍未读。最新父链和GPU已退出，Goal工具实读blocked；用户本轮授权的小试已完成，未声称恢复工具Goal或总体完成。

## 后续审查重点

- 完整强控制优于只比较弱代理。正确AV内容似然提高、loss下降、窗口AUC略升或工程通过都曾不带来完整选帧收益。
- 新方案应解释为何能改变内容对应与整源动作选择。避免重复旧小头、固定阈值、提示词、边界和已失败的剂量扫描。
- 当前原生局部KV屏蔽仍共享完整前缀；缓存及非视觉位置可含全局信息。不能把它称为严格局部输入隔离，也不能由一个已曝光来源否定所有局部建模。
- 任一新实验须明确证据缺口、真实输入/参数/预算、原TIME及实际40.48完整对照、首次独立复核与停止条件。源码存在不是启动授权；不能直接跑本仓库的历史launcher。

## 发布与规则边界

新代码和报告可公开，但完整模型、媒体、标注、输入锁、tensor、raw、预测包及签名下载元数据留在私有运行环境。公开checkout缺这些资产，不能声称在这里复现过Linux结果。

不向闭源服务上传官方数据，不用测试GT、测试标注/人工修正或排行榜反构规则，不自动官网提交。真实主辅模型总参数≤9B；来源/许可证、实际直连、共享资源仍须核查。不联系作者/其他聊天、不改连接/服务，CONTROL5永不恢复。官方结果提交截止已核为2026-10-23 20:00(+08)，历史预算不能延长截止。

本次同步未重新运行任何科学实验。原STOP、UNKNOWN、失败、费用和冻结锁保持；原manifest冻结，增量发布另列[范围](../../docs/publication_scope_20261023.json)。
