# 原作者人工监督：已取得，但尚未准入新训练

2026-10-18 02:56 UTC。本轮新ZIP仍为0；40.47原包保持。以下是新增的监督可用性证据，不是候选质量或提分证据。

## 实际取得与身份对应

固定原作者仓库提交 `b7e553ac3b0c898ee6b85e03ee507c064eab89ca`，仅取得 `data/README.md`、`data/LICENSE`、`data/highlight_train_release.jsonl`，实际载荷3,979,871字节。原raw端点首请求超时、成功文件0，145失败保留；146明确改用同一作者仓库的GitHub API内容端点直达Linux，逐文件大小、Git blob及SHA校验通过。没有Windows载荷中转、媒体下载、代理或连接配置改动。

原训练标注有7,218条查询、7,100个视频片段、2,214个原YouTube来源；标注schema检查未发现异常，每个已标2秒片段有3位评审的0..4等级。这里的“train”是外部QVHighlights训练分组，不是AIC测试标注。

与当前TIME冻结身份注册的对应：

| 范围 | 结果 |
| --- | --- |
| TIME原媒体父项 | 704 |
| 同原作者完整片段名匹配 | 577；其余127未匹配原作者train文件 |
| TIME原YouTube来源 | 602；其中492出现在作者train文件 |
| 已注册TIME窗口 | 724；其中593属于上述577父项 |

这些是名称/来源ID对应，未升级为原始媒体字节相同或逐帧对齐。已有媒体SHA与官方426的精确交集0证据继续引用144，不据此推定原YouTube全局无重叠。

## 时间与任务边界

新增纯metadata诊断使用既有 `n_frames * fps_den / fps_num` 与作者 `duration` 比较。匹配父项的时长差绝对值中位数0.016533秒、最大1.566667秒，5项大于1秒；7个父项至少一个已注册窗口越过某条作者时长。这个公式只是已有帧数/fps诊断，不能代替原生PTS。没有伸缩、截断、补零标签或修正旧缓存。

原作者任务是**给定query后的片段相关性与精彩程度**。人工分数只附在相关的2秒片段上，不能把其他位置当作无条件普通负例，也不能把这一数据直接冒充AIC的无条件高光/构图联合真值。旧TIME没有输入这些query，教师时间标签也不是这些人类评级的替身。查询语义能否迁移到无条件高光仍需要独立研究，当前未验证。

作者明确将标注置于CC BY-NC-SA 4.0，代码为MIT；两者不同。用户已声明仅学生参赛/科研，未安排原图或标注分发。这解决了这一原始标注文件的公开来源与许可识别，**没有补齐旧视频分享发布者、各原视频使用权、全局原来源隔离或空间人工GT**。不据此重新训练旧TIME或恢复闭源教师。

作者原始说明：[数据schema](https://github.com/jayleicn/moment_detr/blob/b7e553ac3b0c898ee6b85e03ee507c064eab89ca/data/README.md)、[数据许可](https://github.com/jayleicn/moment_detr/blob/b7e553ac3b0c898ee6b85e03ee507c064eab89ca/data/LICENSE)、[代码与数据许可区分](https://github.com/jayleicn/moment_detr/blob/b7e553ac3b0c898ee6b85e03ee507c064eab89ca/README.md#license)。

## 实际裁决

保留为已曝光外部研究训练材料及后续监督设计依据。没有新增模型、processor、训练、正式生产或封包，也没有将它称为新盲测。原候选STOP、旧失败及所有费用不改。不能在剩余时间中把查询条件忽略后直接训练出包；下一轮若采用，应先解决任务定义与真实时轴，不能再把换一个数据集名称当成监督质量修复。

Linux证据根：`/home/inspur/aic_video_work/diagnostic_score_goal_20261018_v1/qvh_original_human_146`。保留完整原始文件、`recovery_registration.json`、`parent_id_join.json`、`result.json`、`metadata_alignment_diagnostic.json`和明细。本地仅本文与简短回执，没有回传原始标注或媒体。

- 原始train标注SHA256：`fd28404187468f57cf99242be2963127dc9b4aef26c7de3cb9469569801f2625`。
- 取得与身份结果SHA256：`73d8c712e462ecae165528aedb088e960a7a40aa2e259b4d73028483944ca2e6`。
- 时间metadata诊断SHA256：`3899af17f98551da931714022a5fcc698eafa70c1690ebbeaa7f99350d7f39ee`。
