# P2-R 可信非测试构图参考门

**唯一状态：`REFERENCE_GATE_PARTIAL`。** 本轮完成现有证据清算、一手来源候选审计、一个受限 16:9 外部参考试点、严格 loader/评分边界测试、有限泄漏检查和视觉落框检查。9:16 独立参考仍未通过使用边界与语义门，因此不满足 `PASS_PILOT` 的双比例、16 来源要求。未使用 GPU、未训练/推理、未读取比赛测试视频、未生成候选或提交。初版结构脚本越界解析了 64 条弱 holdout 的标签结构；未打开媒体、未评分或用于选样，最终重算已排除，但本执行轮不得再称该弱 holdout 保持封存，详见 `boundary_incident.json`。

报告根目录：`G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z`。主要交付：[候选登记](G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/candidate_registry.json)、[使用边界审计](G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/source_and_usage_audit.json)、[现有证据清单](G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/existing_evidence_inventory.json)、[参考协议](G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/reference_protocol.md)、[最终冻结](G:/ai/AIC视频/reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/final_freeze.json)。

## 四个问题的回答

### 1. 官方 9:16 标签能支持什么

它们只能作为 `TIER_W_WEAK_TEACHER`。987 行均由教师模型生成；全量有 9,041 个 `crop_keyframes` 和 98,242 个逐帧 `cropRois`。既有冻结报告记录 577 条可映射带 ROI、8,369 个教师关键帧和 90,172 个逐帧 ROI。最终重算先排除 64 条弱 holdout，只处理 513 条非 holdout 带 ROI 记录：81,128 个可由相邻关键帧夹住的 ROI 中，80,214 个（98.87%）与 1 Hz 关键位置线性插值在 1 像素内一致，且有 64,300 次相邻框完全重复。这强烈支持“逐帧 ROI 主要是稀疏教师轨迹的复制/插值产物”，但没有发布的生成代码，故不把统计一致性写成实现事实。36 帧既有可视抽样只证明部分媒体映射可用，不升格构图真值。

### 2. 项目内是否已有可信 16:9 参考

没有。P1b 有 4 条 16:9 与 4 条 9:16 非测试媒体，但 8/8 均为 `UNANNOTATED`，annotator/reviewer 都不存在，只能做接口检查。它们的底层 YouTube 媒体也没有逐视频许可证。

### 3. 公开数据是否提供可用参考

GNMC 0.0.1 通过了**受限**试点门：官方 Zenodo 归档 363,946,070 字节，本地 MD5 与发布记录 `0f2c3e47c8cd28af6a424d3e356b052b` 一致；经验编辑者为每张图像提供固定比例裁剪，16:9 可直接使用。限制是每比例单编辑者、无独立复核、无每图来源 URL，并采用 PolyForm Noncommercial；所以只批准 P2-R 本地非商业诊断，不能自动扩展到竞赛训练/提交。

LIVE-YT VC 有人类 9:16 视频框，GAICD 同时包含 16:9/9:16 的人类评分候选，但二者官方仓库均未发现明确数据许可证；“公开下载”不等于许可，故只登记 `METADATA_ONLY`，没有下载媒体。RetargetVid、FLMS、CUHK、CPC、Carousel 因比例或标注语义不匹配被排除；MIR-Thumb 的规范下载与条款仍为 `UNKNOWN`。

### 4. 是否能冻结双比例试点

不能。已冻结 GNMC 16:9 的 8 个文件级唯一图像项；因无逐图原始 URL，文件层面以外的来源独立性为 `UNKNOWN`：4 个 dev、4 个 `sealed_holdout`，全部媒体 SHA、坐标转换和格式检查通过。9:16 合格来源为 0，故总量只有 8/16，比例只覆盖一侧。封存清单由脚本生成但未用于模型判断。

## 试点验收

- 严格 loader/诊断边界：25/25 通过，覆盖双空/单空、多参考、稀疏、重复帧、NaN/Infinity/bool、越界、错误比例、缺媒体、哈希不符与 split 泄漏。
- 视觉落框：4/8（50%，全部 dev）接触图已实际查看，4/4 红框在源图内且呈 16:9；只验证落地/身份/比例，不评价构图美感，sealed holdout 未视觉打开。
- 泄漏：GNMC 数字 ID 与 AIC `video_id/youtube_id` 无交集；8 张图与 P1b 8 个非测试来源的 96 帧完成 768 次 pHash 比较，阈值 6 下 0 匹配。GNMC 不提供原图 URL，且未全盘解码 AIC 语料，所以完整来源泄漏为 `UNKNOWN`，不能宣称全局隔离。
- 同帧历史模型输出：不存在；按协议没有启动推理，也没有模型排名或质量分。

## 产物

- `candidate_registry.json`：9 个候选及资格结论。
- `source_and_usage_audit.json`：使用边界和限制。
- `existing_evidence_inventory.json`：官方弱标签/P1b 证据矩阵及逐行结构统计。
- `pilot_manifest.jsonl`、`dev_manifest.jsonl`、`sealed_holdout_manifest.jsonl`、`conversion_records.jsonl`：受限 GNMC 16:9 试点。
- `reference_protocol.md`、`annotation_semantics.md`、`loader_test_results.json`、`leakage_audit.json`、`visual_qa.json`。

## 停止与交接

`REFERENCE_GATE_PARTIAL` 不批准下一阶段模型对照，也不批准 GPU、训练、弱 holdout、比赛测试、打包或提交。总控可选择：取得 LIVE-YT VC/GAICD 的明确使用授权后补齐 9:16；或另找带明确许可证、媒体身份和原生 9:16 人工裁剪的第一方数据。不得把现有 9:16 弱教师框或执行Agent自画框填入独立参考。
