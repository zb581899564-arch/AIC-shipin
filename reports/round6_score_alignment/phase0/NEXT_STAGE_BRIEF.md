# 下一阶段交接简报（P1 建议稿）

- run_id：`round6_p0_20260917T0155Z`；日期：2026-09-17
- **本文件只给建议，不批准下一阶段。** P0 的验收与 P1 的启动由总控Agent决定。
- 当前阶段登记建议：`P0_EXECUTED_PENDING_SUPERVISOR_ACCEPTANCE`。

---

## 1. P1 的目标（按 ROADMAP §5 P1 原文，不改范围）

1. 先实现**联合评分器与边界测试**，再用 CPU 重算既有输出；不训练、不跑新模型。
2. 建**独立诊断集**：目标 80 个独立来源组，40 开发 + 40 留出；每部分目标画幅 16:9 与 9:16 各 20；每部分争取 ≥8 条**自然无高光**样本。来源组在所有划分中不交叉，近重复审计不能只看文件名。
3. 标注：只用非测试数据；记录区间、可见主体/构图意图、构图关键帧、切镜、插值规则与不确定性；抽帧标注只能给稀疏帧指标；二次复核 ≥20% 且覆盖全部争议样本，记录复核主体。
4. 开发数据可用于设计；**留出内容与标签封存**，候选冻结后仅评一次。818 条已用弱标签不得与新诊断集来源泄漏。合成图形只测接口。
5. 无法取得可信标注时，**只能交付弱诊断**，不准升级为“可预测官方收益”的验证集。

GPU 需求：**0**（ROADMAP §6）。若确需下载标注媒体，需另行登记（P0 未下载任何媒体）。

---

## 2. 建议的输入/输出接口

### 2.1 评分器（先做）

```
score.py
  --predictions <jsonl>        # 提交格式：[{video_id,targetRatioWH,predictions:[{frame,bboxes:[x,y,w]}...]}]
  --references  <json>         # 诊断参考（弱标签，必须带 label_status / provenance）
  --index       <json>         # 媒体索引：video_id -> {width,height,n_frames,targetRatioWH}
  --frame-convention <spec>    # 必须显式传入并写入结果：'ceil_halfopen' | 'round_inclusive' | ...
  --boundary-suite             # 跑 scoring_spec.md 第 3 节全部用例
  --out <json>
```

输出（每条都必须落盘并带 SHA-256）：

- `per_video[]`：`video_id, n_pred, n_gt, s_iou, precision, recall, f1, duplicate_predictions, unmatched_predictions, missed_ground_truth, empty_both, one_side_empty`
- 聚合：逐视频等权平均（×100）、匹配帧平均 IoU、预测覆盖率、空预测率、合法率
- 分层：来源组 / 目标画幅 / 场景 / 时长分位
- 不确定性：按来源组配对 bootstrap（replicates、seed 必须写进结果）
- 元数据：`official_status=INTERNAL_SPEC_REIMPLEMENTATION_PROPOSAL`、输入哈希、`frame_convention`

### 2.2 诊断集清单（后做）

每条记录建议字段（在 P0 已确认的 818 条 schema 之上扩展）：

```json
{
  "sample_id": "...", "source_group": "...",
  "source_path": "...", "source_probe": {"width":0,"height":0,"avg_fps":0,"nb_frames":0,"duration_sec":0},
  "targetRatioWH": [9,16],
  "license": "...", "download_url": "...", "downloaded_utc": "...", "source_sha256": "...",
  "overlap_with_historical_818": {"same_source_group": false, "same_youtube_id": false, "note": "..."},
  "time_intervals_source_sec": [[0.0,0.0]],
  "composition_keyframes": [{"frame":0,"bbox_xywh":[0,0,0],"frame_is_exact": true}],
  "cut_boundaries_source_sec": [0.0],
  "interpolation_rule": "linear_within_shot_only",
  "has_highlight": true,
  "annotator": "...", "reviewed_by": null, "review_share": 0.0,
  "label_status": "WEAK_HUMAN_SPARSE"   // 或 WEAK_MODEL / WEAK_PROXY，禁止写 ground_truth
}
```

**关键要求**：`source_sha256` 必须真的计算（P0 发现 818 条历史样本的媒体身份从未哈希验证）；近重复审计至少要用（时长、分辨率、fps、来源组、关键帧指纹）多字段，不能只看文件名。

---

## 3. 阻塞项（需总控裁决或授权，P1 无法自行解决）

| # | 阻塞 | 影响 | 建议处理 |
|---|---|---|---|
| K1 | 官方 evaluator 未取得，且官方页面未写明帧上界闭/开与非法行处理粒度 | 评分器所有结果的“接近官方程度”无法界定；帧端点约定直接决定 +184 帧是否应存在 | 总控裁决：① 继续尝试取得官方脚本/样例（本轮按“不联网”未抓取）；② 或书面接受内部重写并冻结上述边界 |
| K2 | 帧端点约定在 43.48 与第五轮之间不一致，且无共享转换函数 | 任何跨轮对比都带 ±1 帧噪声；第五轮结果可能系统性多 1 帧/端点 | P1 第一项修正（纯 CPU） |
| K3 | 无可信空间参考：历史弱标签的裁剪框在未验证的 clip 坐标系内，width≈最大合法宽度，媒体身份 0 条可信 | 空间诊断无法进行；只能做时间维度的独立诊断 | 若 P1 必须含空间诊断，需先解决坐标空间与身份；否则 P1 明确限定为“时间+接口”诊断并写明限度 |
| K4 | 独立诊断素材：许可、可得性、横竖比例（目标各 20）、标注人力与 ≥20% 复核 | 决定诊断集能否达到设计目标 | 总控确认素材来源与标注安排；若达不到，按 ROADMAP 允许调整协议并记录分歧，不伪造负例 |
| K5 | 既有内部 evaluator 的版本基线（旧 .pyc vs 现源码行为不同） | 用哪个版本重算历史结论会影响可比性 | P1 开始时固定并登记一个版本 + 哈希，历史重算需注明版本 |

---

## 4. 建议执行顺序（确定性优先）

1. **联合评分器 + 边界测试**（scoring_spec.md 第 3 节全部用例），CPU，无外部依赖。
2. **CPU 重算既有输出**：43.48 / 41.22 / 41.09 / 第五轮四个包的 `predictions.jsonl` 用同一个评分器重算“时间阈值下的上界”，明确标为内部重写；附带 `frame_convention` 双跑（ceil 半开 vs round 闭区间）以量化 §2 的差异。
3. **空/失败三态接口修正**（提示词—解析器—合成器—校验器贯通），用记录在案的 203 窗做重放，确认输出不变或变化可解释。
4. **诊断集构建**（素材、许可、标注、复核、封存），先 8–16 条打通流程，再扩到目标规模。
5. 只有在 1–4 完成后，才讨论是否把接口/评分结论用于 P2 的候选设计。

---

## 5. P1 明确不要做的事

- 不训练、不微调、不做新模型推理（含测试集）、不下载权重。
- 不使用测试视频内容定规则、修标签或挑坏例；不把测试帧/视频/标签发给外部模型。
- 不复活 OraRL 跟踪或空间替换路线（已有负面证据）。
- 不改写历史报告；勘误另立文件。不覆盖他人未提交工作。
- 不把内部重写分数说成官方分数，不把“格式合法/弱标签上涨”写成提分。
- 不因 P0/P1 的中间结果调整样本、阈值或划分。

---

## 6. P1 验收要点（供总控参考）

- 评分边界用例全部通过，且每个用例标注“规则来源（官方/内部/提议）”。
- 重算结果的每一个数字都能追溯到输入哈希、代码版本与 `frame_convention`。
- 诊断集：来源组不交叉、身份有哈希、许可与来源可核、横竖比例达标、负例定义的分歧被记录。
- 明确区分：官方分数 / 独立诊断指标 / 弱标签一致性 / 格式检查 / 执行成功。
- 若素材或标注无法达标：按 ROADMAP 交付弱诊断并写明证据不足，不得放宽门槛。
