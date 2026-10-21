# 当前代码与证据地图

新补入的是项目自有源码和聚合报告；不包含官方/外部媒体、受限标签、完整输入/来源锁、模型、tensor、raw或预测载荷。代码中的Linux路径是接口引用，不代表公开checkout具备这些资产。历史launcher只可审查，不能因文件存在而启动。

| 范围 | 实现 | 结果入口 |
| --- | --- | --- |
| PR3原研发代码 | [content_choice_v1](../../improvement/content_choice_v1/PLAN.md)、[RUNBOOK](../../improvement/content_choice_v1/RUNBOOK.md) | [PR3结果与交付](../content_choice_execution_20261020_v1/PR3_REAL_EXECUTION_RESULTS.md)，最新33.33见本目录聚合表 |
| PR3 Linux控制和端点兼容修复 | [control.py](../content_choice_execution_20261020_v1/control.py)、[clock_bridge19.py](../content_choice_execution_20261020_v1/clock_bridge19.py)、[render_remaining19.py](../content_choice_execution_20261020_v1/render_remaining19.py) | [最终交付](../content_choice_execution_20261020_v1/DELIVERY_FINAL20.md) |
| 四个已失败风险整包 | [risk_four21.py](../online_temporal_probe4_20261020_v1/risk_four21.py) | [官网结果](../online_temporal_probe4_20261020_v1/OFFICIAL_SUBMISSION_RESULTS26.md) |
| 证据重置、音频、耦合纠偏、视觉训练/迁移 | [evidence_reset_v1源码目录](../../improvement/evidence_reset_v1) | [经验总表](../evidence_reset_goal_20261020_v1/EXPERIENCE_AND_DECISIONS.md)、[增量经验](../evidence_reset_goal_20261020_v1/EXPERIENCE_ADOPTION16.md)、[视觉/TIME终态](../evidence_reset_goal_20261020_v1/RESULTS68.md) |
| I3D＋UMT原视频与留域闭环 | [i3d_umt_v1源码目录](../../improvement/i3d_umt_v1) | [RESULT14](../i3d_umt_cross_domain_20261021_v1/RESULT14.md)、[范围](../i3d_umt_cross_domain_20261021_v1/CROSSDATA12_SCOPE.md) |
| 静态图文正对照 | [independent_text_grounding_v1](../../improvement/independent_text_grounding_v1) | [RESULT04](../independent_text_grounding_20261021_v1/RESULT04.md) |
| 原作者视频编码器对照及首7缓存恢复 | [video_text_grounding_v1](../../improvement/video_text_grounding_v1) | [RESULT08](../video_text_grounding_20261021_v1/RESULT08.md)、[同帧准备范围](../video_text_grounding_20261021_v1/NEXT_VIEW_PROFILE12.md) |
| 最新同帧两视图 | [prepare.py](../../improvement/full_view_context_v1/prepare.py)、[render.py](../../improvement/full_view_context_v1/render.py)、[infer.py](../../improvement/full_view_context_v1/infer.py)、[review.py](../../improvement/full_view_context_v1/review.py)、[audit.py](../../improvement/full_view_context_v1/audit.py) | [RESULT13](../full_view_context_20261021_v1/RESULT13.md)、[CONTINUATION](../full_view_context_20261021_v1/CONTINUATION.md) |

机器级状态、全部成功/失败和费用以私有Linux自然终态/共享账本为准。本公开镜像用[aggregate_results.json](aggregate_results.json)绑定本地短回执大小/SHA，明确不能代替重跑或假装已看到私有文件。

## 审查时要避免的混淆

- `RESULTS68.md`才是视觉LoRA＋TIME43的终态；`VISION_ATTENTION_PLAN62.md`和历史STOP后的重新开放是沿革，不是待执行任务。
- [SCIENTIFIC_CLOSEOUT57](../evidence_reset_goal_20261020_v1/SCIENTIFIC_CLOSEOUT57.md)是用户后来明确重开的旧阶段结论，不代表总体任务已完成，也不应据它忽略62–68和I3D/CLIP后续真实结果。
- [NEXT_VIEW_PROFILE12](../video_text_grounding_20261021_v1/NEXT_VIEW_PROFILE12.md)是当时的准备范围；后续56点已实际跑完，不能把“7个首帧成功”当成当前待补49个。
- 原PR #1媒体SHA/真实路径/发布增量清单修复和PR #2、#3实现保持。工作区较旧的同名文件没有覆盖它们；精确保留列表见[本次发布范围](../../docs/publication_scope_20261021.json)。
- 三个独立辅助模型的合计参数分别与保护基线核过：I3D/UMT8.81681B、CLIP8.93383B、X-CLIP8.97914B。它们是不同方案的完整预算，不能把三个辅助模型同时并用后仍沿用其中一个数。

公开仓库没有完整媒体/权重，因此只能够运行不依赖私有资产的针对性CPU检查。本文描述的是已留存Linux实验事实；本次同步没有重新运行科学实验来刷新结果。
