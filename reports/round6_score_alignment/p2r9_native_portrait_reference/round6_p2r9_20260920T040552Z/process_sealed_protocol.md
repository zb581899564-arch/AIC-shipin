# P2-R9 `PROCESS_SEALED` 聚合评分协议

## 当前可用性

入口代码已实现并通过纯合成测试，但**没有绑定真实候选**。当前状态为 `SYNTHETIC_PROTOCOL_ONLY / REAL_HOLDOUT_NOT_BOUND`，原因是没有候选通过书面资格门。它不是密码学盲测，也不是操作系统权限隔离；共享工作区无法证明执行Agent绝对不能读取底层文件。

## 文件分离

- 公开 commitment 只允许数据集版本、项目 ID、来源组、媒体 SHA-256、目标比例、固定选样规则/种子、标签文件 SHA-256、项目数、评测代码哈希和保护注册表哈希。
- 私有参考文件由评分入口内部读取；真实绑定时不得复制到普通报告、普通 manifest、接触图或 stdout。
- 预测文件包含同一项目/来源组/媒体哈希/比例、`OK|FAILED` 状态和预测框。失败项必须空框，并以 0 分留在分母。
- `holdout_access_log.jsonl` 只追加调用时间、执行者、代码/预测/commitment 哈希、聚合是否生成及错误码，不记录项目 ID、框或逐项分数。

## 坐标与评分

- 框格式为源像素浮点 `[x,y,w,h]`，四个值必须有限、非 bool、面积为正、在源图边界内，并以 `1e-6` 容差满足目标比例。
- 空参考与空预测计 1；只有一方为空计 0。
- 多参考保留全部标注，单帧得分取预测框与全部可接受参考中的最大 IoU；不得按模型结果预先选择参考。
- 稀疏标签只评发布者标注的稀疏帧，不插值。
- 先按项目计算，再给项目宏均值；同一来源组内先平均，再对来源组做宏平均。失败项保持在各自来源组和总体分母。

## 硬拒绝

缺失/多余/重复项目、非法 JSON、NaN/Infinity/bool、越界、错误比例、媒体哈希不符、来源跨 split、评测代码哈希变化、原始标签哈希变化、保护注册表哈希变化、公开 commitment 含坐标/轨迹/逐项分数，以及 64 条弱 holdout、4 条 GNMC exposed sealed 或旧 88 条历史 holdout 的任何命中都拒绝运行。异常只输出稳定错误码，不输出参考 payload 或栈。

## 入口

`G:/ai/AIC视频/round6_score_alignment/p2r9_native_portrait_reference/evaluate_process_sealed.py`

真实数据只有在总控确认候选为 `ELIGIBLE_PROCESS_SEALED_PILOT` 后才能生成 `BOUND` commitment。本轮的模板故意为 `NOT_BOUND_NO_ELIGIBLE_CANDIDATE`，因此入口会拒绝真实运行。
