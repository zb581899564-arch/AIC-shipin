# 联合评分规范（P0 草案）

- run_id：`round6_p0_20260917T0155Z`；起草日期：2026-09-17
- 状态：**`INTERNAL_SPEC_REIMPLEMENTATION_PROPOSAL`** — 官方 evaluator 未取得，本文件不是官方实现，也不得被引用为官方分数口径。
- 适用：P1 联合评分器实现与边界测试。**本文件只写规范，不含实现。**

---

## 1. 官方已记录的内容与来源

来源：官方赛题页 <https://www.aicomp.cn/tracks/tracks-6/4267.html>，项目内记录见远端 `reports/eval_source_audit.md`（读取日期 **2026-09-09**）与 `reports/eval_boundary_tests.json`。本轮按“默认不联网”未重新抓取页面。

已记录为官方页面内容（`OFFICIAL_PAGE_RECORDED`）：

1. 提交为 JSONL；每行至少含 `video_id`、`targetRatioWH`、`predictions`。
2. 预测框为 `[x, y, w]`，**高度由目标比例推导** `h = w * target_h / target_w`。
3. 评分是**同视频同帧**的空间 IoU 加权。
4. 重复帧有“**首个有效**”处理规则。
5. 按视频聚合 F。
6. 页面给出非法预测示例。

官方页面**未写明**（`OFFICIAL_UNRESOLVED`）：

- U1 非法/畸形行是**整文件拒绝**，还是把该行计为假阳性继续评分。
- U2 是否接受**小数坐标**。
- U3 帧号**上界是否闭区间**。
- U4 冲突行/无效行是否影响该视频其余预测的计数。
- U5 真值（GT）侧的帧号与框的构造方式（我们看不到官方 GT 生成脚本）。
- U6 双方为空、单方为空的计分（项目 `AGENTS.md:31` 记为“双方均空计 1、单方为空计 0”，属项目记录，**不是**页面逐字引用）。

---

## 2. 建议的内部规范（供 P1 实现）

以下每条都标注：`CONFIRMED_OFICIAL_PAGE` / `INTERNAL_现有实现` / `PROPOSAL`。

### 2.1 序列化契约

| 项 | 规则 | 状态 |
|---|---|---|
| 行 | 每行一个 JSON 对象，UTF-8，无 BOM | INTERNAL_现有实现 |
| 必需键 | `video_id`(str)、`targetRatioWH`([tw,th] 正有限数)、`predictions`(数组) | CONFIRMED_OFICIAL_PAGE |
| 顶层额外键 | 校验器接受；交付包只允许这 3 个键 | INTERNAL_现有实现（校验器）/ PROPOSAL（打包期收紧） |
| 预测项 | `{"frame": int, "bboxes": [x, y, w]}` | CONFIRMED_OFICIAL_PAGE + INTERNAL_现有实现 |
| 空数组 | `predictions: []` 合法 | INTERNAL_现有实现（边界测试 empty_both / empty_one_side 均通过） |
| 重复行 | 不得出现（同一 `video_id` 出现两次即 error） | INTERNAL_现有实现 |
| 缺失行 | 索引中的视频缺行即 error | INTERNAL_现有实现 |

### 2.2 校验规则（既有内部实现，实测自源码）

被测实现：远端 `evaluation/schema.py` 与 `evaluation/internal_metric.py` 的**只读副本**（哈希见 `evidence/existing_internal_evaluator/`：`schema.py 0236f987…`、`internal_metric.py 41ec9ecf…`）。实测见 `evidence/validator_boundary_probe.json`（174 行记录集，逐例替换 video 0）。

**版本提示**：本地 `tmp_agent_c/evaluation/__pycache__/*.pyc` 是 2026-09-09 22:36 的**更旧构建**，与 23:03 的源码在“小数框、真值帧严格性”上不同。本文件以源码为准；任何再实现都必须先固定版本。

| 输入 | 结果 | 错误码 |
|---|---|---|
| `frame` 为 `5.0` 或 `True` | 非法 | `FRAME_TYPE` |
| `frame == n_frames`（越上界） | 非法 | `FRAME_OUT_OF_RANGE` |
| `frame == n_frames-1` | 合法 | — |
| `bboxes` 非 3 元素 | 非法 | `BBOX_SHAPE` |
| `bboxes` 含 bool / 非数 / 嵌套 list | 非法 | `NON_FINITE` |
| `w <= 0`（含负） | 非法 | `BBOX_SIGN` |
| 推导高度后越出源帧（x+w>W+1e-9 或 y+h>H+1e-9，`h=w*th/tw`） | 非法 | `BOX_OUT_OF_BOUNDS` |
| 小数坐标且在界内（如 `[0.0,0.0,720.0]`、`[0.0,0.0,719.5]`） | **合法** | — |
| 重复帧（同视频同帧两次） | 合法，**2 条都计入**有效预测 | `DUPLICATE_FRAME`（warning） |
| 空数组 / 顶层或预测项多余键 | 合法 | — |
| `targetRatioWH` 与索引不符（容差 rel 1e-9） | 非法 | `TARGET_RATIO_MISMATCH` |
| 同一 `video_id` 出现两行 | 非法 | `DUPLICATE_VIDEO_ID` |
| 索引中的视频缺行（`require_complete=True`） | 非法 | `MISSING_VIDEO_ID` |
| 空行 / JSON 解析失败 | 行级问题 | `BLANK_LINE` / `JSON_PARSE` |

**帧号约定**（内部）：0 基、上界开区间 `0 <= frame < n_frames`。**U3 未与官方核对**。
**坐标类型**：内部接受界内有限实数；交付包在打包期额外要求 int（`accept_candidate.py:76`）。**U2 未与官方核对**。
**真值侧**：当前源码用 `_strict_frame` 只接受整数（bool/float 均拒绝，数字字符串被接受）。历史审查文档 `reports/data_c_review.md` 记录的“float/bool 被 `int()` 静默截断”缺陷在当前源码中已不存在。

### 2.3 计数与匹配

```
N_pred(v)  = 该视频所有被接受的预测帧记录数（重复帧每条都计；无效行不计入）
N_gt(v)    = 该视频真值帧数（含框）
matched(v) = { f : f 同时出现在 N_pred 与 N_gt 中 }
IoU(f)     = 预测框([x,y,w] + 推导高度) 与真值框 的 2D IoU
F(v)       = 2 * Σ_{f∈matched(v)} IoU(f) / (N_pred(v) + N_gt(v))
总指标      = 所有视频 F(v) 的等权平均（含空视频）
```

| 情形 | F(v) | 状态 |
|---|---|---|
| `N_pred=0` 且 `N_gt=0` | 1 | 项目记录（U6 待核对） |
| 只有一方为 0 | 0 | 项目记录（U6 待核对） |
| 完全匹配、IoU 全为 1 | `2*N/(N+N)=1` | 公式推论 |
| 有交集但框不重合 | `2*ΣIoU/(N_pred+N_gt)` ∈ (0,1) | 公式推论 |
| 无交集（时间无重叠） | 0 | 公式推论 |
| 预测帧越界/NaN/未知视频 | 该行**无效**；官方未知是计入 `N_pred` 还是拒绝整文件（U1/U4） | **UNRESOLVED** |
| 重复帧 | `N_pred` 计入两次；只有首次可匹配（“首个有效”） | CONFIRMED_OFICIAL_PAGE（措辞）+ INTERNAL_现有实现 |

**禁止**：把无效预测静默删除后仍按干净分母报告；禁止在分母为 0 时做除法（必须走空规则）。

**源码实测值**（`evidence/existing_internal_evaluator/internal_metric.py` + 174 视频索引，仅 video 0 带预测/真值）：

| 构造 | n_pred | n_gt | s_iou | F(video 0) | 174 视频均值 | score_percent |
|---|---|---|---|---|---|---|
| 双方空 | 0 | 0 | 0 | **1.000000** | 1.000000 | 100.0 |
| 单方空 | 0 | 1 | 0 | **0.000000** | 0.994253 | 99.425287 |
| 完全匹配 | 1 | 1 | 1.0 | **1.000000** | 1.000000 | 100.0 |
| 重复预测同帧 | 2 | 1 | 1.0 | **0.666667** | 0.998084 | 99.808429 |

**分母口径警告**：`score_predictions(..., require_complete_gt=False)` 会把“索引里有、真值里没有”的视频当作 `n_gt=0`；若预测也为空，该视频按 F=1 计入平均（上表第 1 行的 174 视频均值即由此而来）。**实现必须先明确视频全集与真值全集**，否则“平均分”会被未标注视频抬高。

### 2.4 聚合与报告

- 主口径：**按视频**等权平均；不得用“所有帧汇总”替代（`AGENTS.md:27`）。
- 必须同时输出：联合分、时间 precision/recall/F1、匹配帧平均 IoU、预测覆盖率、空预测率、合法率。
- 分层：按视频、来源组、目标画幅（16:9 / 9:16）、场景。
- 不确定性：按**来源组**配对 bootstrap；样本不足时报告区间跨 0，不得放宽门槛。
- 抖动只作诊断项，不并入联合分。

### 2.5 与现有内部指标的差异登记（必须显式区分）

| 指标 | 单位 | 空间项 | 双空 | 用途 |
|---|---|---|---|---|
| AIC 联合指标（本规范） | 帧 | 有（同帧 IoU） | 1 | 目标口径 |
| 第五轮选择指标 `WEAK_TEACHER temporal union F1` | 秒（并集） | **无** | 0（`interval_metrics` 在任一侧为空时返回 0） | 仅候选选择 |
| 43.48 时代的 `internal_metric` | 帧 | 有 | 1 | 历史诊断 |
| `evaluation_v2/temporal.py` | 秒（并集） | 无 | 1（双方空） | 历史诊断（query-conditioned） |

**这四者不可互换**；第五轮的门槛结论不能换算成官方期望值。

---

## 3. 边界测试表（P1 必须逐条通过）

`规则来源` 列：`OFFICIAL_PAGE` / `INTERNAL`（现有实现已确认）/ `PROPOSAL`（本文件提议，需总控冻结）。

| ID | 场景 | 构造 | 期望结果 | 规则来源 | 状态 |
|---|---|---|---|---|---|
| B01 | 双方空 | pred=[]，gt=[] | F=1 | 项目记录 | 待冻结（U6） |
| B02 | 单方空（pred 空） | pred=[]，gt=1 帧 | F=0 | 项目记录 | 待冻结（U6） |
| B03 | 单方空（gt 空） | pred=1 帧，gt=[] | F=0 | 项目记录 | 待冻结（U6） |
| B04 | 完全匹配 | 1 帧、IoU=1 | F=1 | 公式 | 可测 |
| B05 | 部分匹配 | pred 2 帧、gt 1 帧、IoU=1 | F=2/(2+1)=0.666667 | 公式 | 可测 |
| B06 | 无交集 | pred 帧与 gt 帧无重叠 | F=0 | 公式 | 可测 |
| B07 | 部分时间重叠 + 框部分重叠 | 重叠帧 IoU=0.6 | F=2*0.6/(N_pred+N_gt) | 公式 | 可测 |
| B08 | 重复帧（同帧两次、框相同） | N_pred=2 | 只有首次可匹配；F=2*1/(2+1)=0.666667 | OFFICIAL_PAGE + INTERNAL | 与现有边界测试一致 |
| B09 | 重复帧（第二次框不同） | N_pred=2 | 第二次不匹配但仍计入 N_pred | OFFICIAL_PAGE | 需补测 |
| B10 | 完整重复行（同视频两行） | 2 行同 `video_id` | 校验失败（`DUPLICATE_VIDEO_ID`） | INTERNAL | 已实现 |
| B11 | 非法：`frame` 为 float/bool | — | 校验失败（`FRAME_TYPE`） | INTERNAL | 已实测 |
| B12 | 非法：`frame == n_frames` | — | 校验失败（`FRAME_OUT_OF_RANGE`） | INTERNAL | 已实测 |
| B13 | 合法上界：`frame == n_frames-1` | — | 通过 | INTERNAL | 已实测 |
| B14 | 非法：`w=0` / `w<0` | — | `BBOX_SIGN` | INTERNAL | 已实测 |
| B15 | 非法：NaN/Inf 坐标 | — | `NON_FINITE` | INTERNAL | 已实测 |
| B16 | 非法：推导高度后越界 | `y=900,w=720,H=1280,[16,9]` | `BOX_OUT_OF_BOUNDS` | INTERNAL | 已实测 |
| B17 | 小数坐标 | `[0.0,0.0,720.0]` | 内部接受；**官方未知（U2）** | INTERNAL + UNRESOLVED | 需总控裁决 |
| B18 | 未知 `video_id` | `999` | `UNKNOWN_VIDEO_ID` + `MISSING_VIDEO_ID` | INTERNAL | 已实测 |
| B19 | 缺视频（索引中缺行） | 173 行 | `MISSING_VIDEO_ID` | INTERNAL | 已实测 |
| B20 | `targetRatioWH` 与索引不符 | `[9,16]` vs `[16,9]` | `TARGET_RATIO_MISMATCH` | INTERNAL | 已实测 |
| B21 | 空行 / JSON 解析失败 | 空行或坏 JSON | 行级 `BLANK_LINE`/`JSON_PARSE`；**官方是拒文件还是计假阳性未知（U1）** | INTERNAL + UNRESOLVED | 需总控裁决 |
| B22 | 目标画幅换算 | 竖屏 9:16 的 `[x,y,w]` 高度推导 | `h = w*16/9`；盒须在源帧内 | OFFICIAL_PAGE | 可测 |
| B23 | 帧端点：秒→帧（选择语义） | 同一 `[a,b)` 秒区间 | 需冻结唯一约定；现状差异 +184 帧 | **UNRESOLVED（U3 相关）** | P1 第 1 项修正 |
| B24 | GT 侧帧号非整数/bool | `5.0` / `True` | 当前源码拒绝（`_strict_frame`）；数字字符串 `"5"` 被接受（需在 P1 明确是否保留该宽松） | INTERNAL（源码实测） | 可测 |
| B25 | GT 视频完全缺失 | 索引有、GT 无 | `require_complete_gt=True` 时直接报错；置 False 时该视频 `n_gt=0` | INTERNAL（源码实测） | 需总控裁决口径 |
| B26 | 每视频平均 vs 全帧汇总 | 两视频帧数悬殊 | 必须用按视频等权（内部实现 ×100） | 项目记录 + INTERNAL | 已实测 |
| B27 | 空视频参与聚合 | 某视频双方空 | 该视频以 F=1 计入平均（实测：174 视频中 1 条空 → mean_f1=0.994253） | INTERNAL（源码实测） | 已实测 |
| B28 | 冗余：pred 帧合法但视频时长未知 | 索引缺 `n_frames` | 校验失败（媒体元数据不可信） | INTERNAL | 已实现 |
| B29 | 版本一致性 | 本地 `.pyc`(22:36) vs 源码(23:03) | 行为不同（小数框/GT 帧）；再实现前必须固定版本 | INTERNAL（本轮发现） | 需登记 |

---

## 4. 未确认项的书面限度（写进任何 P1 报告）

1. 本规范是**内部重写**，与官方实现的差异未知；任何分数必须标 `INTERNAL_SPEC_REIMPLEMENTATION`。
2. 官方 evaluator 未取得前，**不得**用本规范产出的分数宣称达到 50/55 分门槛，也不得换算官方提分预期。
3. 帧端点约定（B23）与非法行处理（B21）两项未裁决前，评分器输出的“合法率/空预测率”只能按内部口径解释。
4. 真值侧：本规范只处理“预测 vs 参考”的评分；由谁提供、如何构造参考，另行登记（P1 诊断集的参考必须是弱标签，需显式标注）。
