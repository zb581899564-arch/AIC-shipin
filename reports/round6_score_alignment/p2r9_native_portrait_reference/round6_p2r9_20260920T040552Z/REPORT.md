# P2-R9 原生 9:16 参考与流程封存门报告

**唯一最终状态：`P2R9_PERMISSION_REQUIRED`。**

有界一手来源检索已结束，不再扩展候选清单。LIVE-YT VC 的原始稀疏标签在比例、人工构图语义和文件/帧绑定设计上是唯一技术上接近合格的首选；YouTube-UGC 与 LSVQ 的底层媒体各有第一方使用声明，但 LIVE-YT 派生的六秒视频和标注包本身没有 LICENSE、数据卡或明确研究/竞赛使用条款。因此本轮在下载真实标签或媒体前停止，并生成未发送的精确询问稿。其余候选没有通过比例、人工语义、第一方归档、媒体身份或许可门。

## 五个问题的闭环答案

1. **LIVE-YT / GAICD / MIR-Thumb 的遗漏证据。** LIVE-YT 仓库在固定 commit 下只有 README、无 release、无 LICENSE；但底层 YouTube-UGC 明示 CC BY 4.0，LSVQ 明示可使用/复制/修改/分发并要求完整通知与引用。这补全了底层媒体边界，却不能替代 LIVE-YT 派生包许可。GAICD 仍无仓库许可证，且 Flickr 原图逐项 ID/URL/许可未在审计证据中保留。MIR-Thumb 仍未找到第一方数据归档、版本或许可。
2. **其他公开原生 9:16 人工参考。** 未找到可落地的新来源。Portrait1K 是真实专家裁剪，但官方 1000 图索引的 2260 个框中精确 9:16 为 0；H2V 的 9:16 是围绕人工主体框机械生成；UGCrop5K 是算法网格候选后人工评分且数据未在官方仓库发布。
3. **8 个来源组试点。** 未执行。没有候选通过书面资格门，因而没有下载真实媒体/标签、没有建立 4 dev + 4 process-sealed，也没有用同源复制凑数。
4. **`PROCESS_SEALED` 入口。** 代码和纯合成门禁已经实现，30 项测试覆盖不泄漏、严格格式、多参考、稀疏、空值、宏平均、失败留在分母、哈希锁定、来源隔离和三类保护输入拒绝。真实 commitment 故意保持 `NOT_BOUND`；这只是流程封存，不是密码学盲测。
5. **路线切换。** 公开空间参考的继续搜索正式停止。最小外部动作只有一次明确的 LIVE-YT 书面许可确认；在许可到来前不再下载或扩展空间参考。若用户不授权联系或许可未获得，建议总控冻结当前未微调 Qwen 空间基线，另行制定 P2-T 高光时间误差、端点与召回路线；本轮没有启动 P2-T。

## 事实

- 保护注册表封禁 64 条弱 holdout、4 条 GNMC exposed sealed，以及旧 88 条历史 holdout 的固定数据集哈希/来源命名空间；未读取这些材料的参考框做评分或选样。
- 输入和工作区在在线候选检索前冻结；固定搜索优先级和停止条件未因下载便利调整。
- 一手证据快照 24/24 成功。只有网页、论文、仓库元数据和 2.0 MiB 的 Portrait1K 压缩标注索引；候选媒体下载为 0。
- GPU、模型加载、训练、推理、比赛测试视频读取、外发消息、打包和上传均为 0。
- 评测入口正常 stdout 只含聚合值和哈希；拒绝路径只含稳定错误码。测试使用的坐标完全是运行时临时合成数据，不是候选或历史留出答案。

## 推断

- LIVE-YT 的原始 30 个采样帧标签适合未来做稀疏 9:16 独立诊断；VC++ 是时间滤波后的派生标签，不能冒充每帧直接人工真值。
- LIVE-YT 最可能只需一轮作者确认即可进入最小试点，但在得到书面回答和实际字节哈希前，`BYTE_BOUND_IDENTITY` 只能写“设计上可绑定、尚未字节核验”。
- GAICD 即使取得许可，也应保留所有候选与人评分，不能挑最高分后称唯一人工框；它不是当前首选。

## 未知与限制

- LIVE-YT Box 目录未提供数据专属许可、每项底层来源/归属映射和文件大小清单；这些必须由维护方确认或在获准下载后核验。
- 没有候选媒体，因此没有做 pHash/帧指纹；AIC 交集只能写 `UNKNOWN_BEYOND_METADATA`。
- 共享工作区不提供真正的权限隔离，`PROCESS_SEALED` 只能约束正常入口和普通产物，不证明底层文件绝对不可读。
- 本轮没有独立 9:16 分数，更没有 AIC 官方联合分或官方提分证据。

## 关键交付

- [候选登记](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/targeted_candidate_registry.json)
- [许可证据矩阵](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/license_evidence_matrix.json)
- [标注语义矩阵](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/annotation_semantics_matrix.json)
- [保护注册表](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/protected_input_registry.json)
- [流程封存协议](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/process_sealed_protocol.md)
- [未绑定 commitment 模板](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/holdout_commitment_template.json)
- [未发送授权询问稿](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/permission_request_draft.md)
- [一手来源快照索引](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/source_snapshot_index.json)
- [资源记录](G:/ai/AIC视频/reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/resource_usage.json)

## 停止边界

本阶段到此停止，等待总控Agent验收。该状态不批准 P2-Q、P2-T、P3、GPU、训练、比赛测试推理、真实留出调用、候选打包、上传或提交。
