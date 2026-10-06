# P2-R9 总控验收记录

日期：2026-09-20

## 结论

总控状态为 **`ACCEPTED_PERMISSION_CONCLUSION_WITH_SEALED_EVALUATOR_FIX_REQUIRED`**。

执行轮的唯一数据结论 `P2R9_PERMISSION_REQUIRED` 被接受：LIVE-YT VC 是本轮唯一在原生 9:16、人工稀疏构图语义和设计上的媒体/帧绑定方面接近合格的候选，但发布者仓库与数据入口没有为派生视频和标注包给出明确许可证；底层 YouTube-UGC 与 LSVQ 条款不能自动替代 LIVE-YT 自身授权。没有用户明确授权，不发送询问稿，不下载 LIVE-YT 标签或媒体。

`PROCESS_SEALED` 工程部分暂不通过真实绑定准入。当前 commitment 是 `NOT_BOUND_NO_ELIGIBLE_CANDIDATE`，因此缺口尚未接触真实留出或产生错误分数；修复前不得把该入口用于任何真实参考。

本验收不修改 `round6_p2r9_20260920T040552Z` 冻结产物。原冻结 SHA-256 保持 `8f3a71e23b2e30f55a9d73c56c30d868e0ab408a50f394da4fc03ba82093503c`。

## 独立复核通过项

- 按 `final_freeze.json` 重算 59 个输出/代码条目：59/59 存在，大小和 SHA-256 全部一致；冻结文件哈希与 `final_freeze.sha256.txt` 一致。
- 测试需要先设置 `P2R9_RUN_DIR`。设置为冻结运行目录后独立重跑：30/30 通过，0 失败、0 错误；不设置该变量时套件在 `setUpClass` 退出，这一复现前置必须保留在后续说明中。
- LIVE-YT 当前 GitHub 仓库的 license 字段为 null，根目录只有 README，License API 返回不存在，releases 为空；执行报告的“没有数据/标注许可证”结论与当前一手来源一致。
- YouTube-UGC 官方页声明视频采用 CC BY 4.0；LSVQ 官方页给出使用、复制、修改和分发条款及通知/引用要求。这些条款只约束各自底层数据，不能推导 LIVE-YT 派生包的授权。
- 当前没有真实 commitment、dev/holdout、访问日志调用或候选媒体。资源台账记录 GPU、模型、训练、推理、比赛测试视频和外发消息均为 0。
- 下载过 2,047,240 字节的 Portrait1K 压缩标注索引作为候选元数据审计；因此准确表述是“LIVE-YT 标签下载 0、候选媒体下载 0”，不能笼统写“所有候选标签下载 0”。

## 阻断缺陷：保护身份字段可省略

`sealed_evaluator.py` 对真实 reference 强制要求 `item_id/source_group/media_sha256/...`，但没有强制原始数据集哈希、来源命名空间或发布者原始 ID。`assert_not_protected` 只在候选实际携带旧数据集哈希、旧路径、旧 ID/组件时命中注册表。

总控最小复现：构造 `split=process_sealed_holdout`，把 `item_id/source_group` 改名，同时令 `source_dataset_sha256=null`、`provenance_path=''`，`assert_not_protected` 返回通过，结果为 `BYPASS_ACCEPTED`。现有 30 项测试只覆盖“保护身份字段存在”的情况，没有覆盖“字段省略或改名”。

这意味着：

1. “64 条弱 holdout、4 条 GNMC 暴露项、旧 88 条历史 holdout 均已封禁”只能解释为已知身份和命名空间被登记，不能解释为无法通过改名/省略字段重新引入；
2. `PROCESS_SEALED` 仍是合成原型，不能绑定真实数据；
3. 该缺陷不影响 LIVE-YT 许可缺失和本轮不下载的结论。

## 修复门

真实绑定前必须另做定向修复：

- `BOUND` commitment 强制提供非空且格式合法的 `source_dataset_sha256`、固定 `provenance_namespace` 和发布者版本；
- reference 强制提供不可由下游任意改名的发布者原始 item ID；能取得时同时登记媒体 SHA；
- 保护注册表按数据集哈希、来源命名空间、发布者原始 ID、来源组和媒体 SHA 多层拒绝；缺任一必需身份字段应 fail closed；
- 先增加“字段省略、改名、伪造 source_group、null 数据集哈希”的失败回归测试，再修实现；
- 公开 commitment、stdout、异常和日志仍不得包含参考坐标或逐项分数。

## 下一步分支

1. 若用户明确授权联系 LIVE-YT 作者：只发送经用户确认的询问稿，等待书面答复；收到答复后先验许可范围，再下载最小试点。发送前不需要也不允许下载标签/媒体。
2. 若用户不授权联系、暂不联系或长期无答复：结束空间参考路线，冻结未微调 Qwen 空间基线，由总控另行制定 P2-T 高光时间路线。

无论选择哪一条，当前均不批准模型对照、GPU、训练、比赛测试推理、打包、上传或提交。
