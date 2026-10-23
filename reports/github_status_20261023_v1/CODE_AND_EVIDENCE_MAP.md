# 实现与证据地图

| 范围 | 实现 | 已完成报告 |
| --- | --- | --- |
| 当前T路线 | [T_BRANCH_PLAN](../../T_BRANCH_PLAN_20261022.md)、[原Pro计划](../../SPRINT_PLAN_20261021.md) | [最新入口](START_HERE.md) |
| S1三臂与S0独立评分器 | [S1源码](../../improvement/sprint_spatial_s1_v1)、[S0源码](../../improvement/sprint_spatial_s0_v1) | [S1结果](../sprint_spatial_s1_20261021_v1/RESULT.md)、[S0结果](../sprint_spatial_s0_20261021_v1/RESULT.md) |
| 音频事件 | [音频源码](../../improvement/sprint_audio_events_v1) | [两种真实音频输入结果](../sprint_audio_events_20261021_v1/RESULT12.md) |
| 新来源/监督与运动路由 | [监督源码](../../improvement/general_highlight_supervision_v1)、[原生来源准入](../../improvement/highlight_source_admission_v1) | [SportCLIP](../highlight_source_admission_20261021_v1/RESULT19.md)、[LVSum](../general_highlight_supervision_20261021_v1/RESULT28.md)、[QV](../general_highlight_supervision_20261021_v1/RESULT47.md)、[实际两包交付](../general_highlight_supervision_20261021_v1/RESULT64.md) |
| 整源策略与摘要 | [全部T源码](../../improvement/t_branch_v1)、[策略协议](../../improvement/t_branch_v1/joint_policy_protocol44.json)、[摘要协议](../../improvement/t_branch_v1/summary_protocol85.json) | [四更新](../t_branch_execution_20261022_v1/RESULT53.md)、[实际完整开发](../t_branch_execution_20261022_v1/RESULT57_60.md)、[完整摘要结果](../t_branch_execution_20261022_v1/RESULT85_97.md) |
| 内容与事件记忆 | [内容似然协议](../../improvement/t_branch_v1/description_protocol67.json)、[记忆协议](../../improvement/t_branch_v1/event_memory_protocol69.json) | [内容似然](../t_branch_execution_20261022_v1/RESULT63_67.md)、[事件完整结论](../t_branch_execution_20261022_v1/RESULT76_80.md) |
| 原生顺序/并行选择 | [顺序协议](../../improvement/t_branch_v1/native_action_protocol98.json)、[并行协议](../../improvement/t_branch_v1/parallel_protocol105.json)、[原生渲染](../../improvement/t_branch_v1/native_render100.py) | [成本停止](../t_branch_execution_20261022_v1/RESULT98_104.md)、[并行训练](../t_branch_execution_20261022_v1/RESULT105_108.md)、[完整开发](../t_branch_execution_20261022_v1/RESULT109_115.md) |
| 实际字母依赖诊断 | [拟合协议](../../improvement/t_branch_v1/parallel_fit115.json)、[因果协议](../../improvement/t_branch_v1/query_binding_protocol117.json) | [拟合](../t_branch_execution_20261022_v1/RESULT115_116.md)、[因果与视觉查询](../t_branch_execution_20261022_v1/RESULT117_120.md) |
| 共享KV与直接视觉查询 | [共享内核](../../improvement/t_branch_v1/shared_visual_query118.py)、[真实8B运行路径](../../improvement/t_branch_v1/visual_query_runtime119.py) | [完整25窗](../t_branch_execution_20261022_v1/RESULT120_121.md) |
| 最新局部注意力真实小试 | [可见性内核](../../improvement/t_branch_v1/localized_visual121.py)、[实际GPU](../../improvement/t_branch_v1/localized_query122_gpu.py)、[独立CPU](../../improvement/t_branch_v1/localized_query_review122.py)、[首次指标](../../improvement/t_branch_v1/localized_query_metrics122.py)、[固定协议](../../improvement/t_branch_v1/localized_query_protocol122.json)、[显式接续](../../improvement/t_branch_v1/localized_query_remaining123.py) | [真实终态与科学停止](../t_branch_execution_20261022_v1/RESULT122_123.md) |

这些模块引用私有Linux上的媒体、原生时钟、模型、输入缓存、永久raw/proof和资源账本；公开checkout只有代码与聚合证据。小试CPU原型通过不替代实际8B与独立复核，报告中的RUNNING式历史快照须服从最新START_HERE和最终报告。

原PR #1媒体SHA/真实路径/发布增量绑定，PR #2 DPO、PR #3内容选择，以及PR #5原生评价修复均保留。工作区同名旧代码不会覆盖公开审查修复；本次新增/保留列表见[发布范围](../../docs/publication_scope_20261023.json)。冻结原manifest未改，当前公开字节由增量manifest绑定。
