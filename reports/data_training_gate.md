# 数据训练准入

当前结果：`FAIL`。

证据文件：`data_audit/training_gate.json`

| split | candidate 标签行 | 来源组 | 严格可信身份行 | 最低要求 |
|---|---:|---:|---:|---:|
| train | 789 | 694 | 0 | 200 |
| dev | 99 | 84 | 0 | 50 |
| holdout | 99 | 85 | 0 | 50 |

`alignment_verified=false`：912 条精确文件名匹配的 MP4 均未通过 provenance SHA-256，同名文件不能证明标注媒体身份；另有 75 条源文件不存在，并且没有加工短片到原始源视频的生成/对齐清单。`video_path` 987 条全为空。

固定 seed 42 的来源组候选划分三组交集为空，但所有候选行都写有 `candidate_only=true` 和 `do_not_use_as_training=true`，不属于 accepted split。
