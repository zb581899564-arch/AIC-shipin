# P1a 定向修复报告

- run_id：`round6_p1a_fix_20260917T0510Z`
- 执行时间：2026-09-17 04:40Z–04:55Z
- 依据：`reports/round6_score_alignment/SUPERVISOR_P1A_REVIEW.md`（状态 `P1A_CHANGES_REQUIRED`）+ `prompts/round6_p1a_fix_handoff.md`
- 范围：仅 CPU 工程修复；未进入 P1b/P2，未联网、未连接远端、未用 GPU、未解码视频、未推理、未训练、未上传
- 首次 P1a 报告**未覆盖**：`reports/round6_score_alignment/phase1a/` 下 5 个文件哈希与修复前记录逐一相同（见 §6）
- 阶段状态：`P1A_FIX_EXECUTED_PENDING_SUPERVISOR_ACCEPTANCE`
- CPU 用时：**1.37 秒**（上限 20 分钟）；新增/更新文件 **32 个 / 0.539 MiB**（上限 100 MiB）

---

## 0. 结论摘要

1. **先补失败测试，再修复。** 新增回归套件 26 例，修复前 **1 通过 / 11 失败 / 14 错误**；修复后 **26/26 通过**。另用总控的三个复现案例写成脚本，修复前 6/6 不合规、修复后 **6/6 合规**（`prefix_reproduction.json` vs `postfix_reproduction.json`）。
2. **全量测试 110/110 通过**（原 84 + 回归 26），历史重放 **174/174 逐项一致**、解析一致性 **203/203**，受保护输入前后哈希 **5/5 未变**。
3. **三条阻塞问题全部关闭**：非法参考不再产生 OK/100 分（改为拒绝 + 公开边界非零退出）；稀疏参考不再泄漏全视频语义（泄漏字段 12 → 0）；合成器有了明确顶层状态与可交付标志。
4. **命名与参数收紧**：`SOURCE_SHOT_NEAREST` 取代 `SOURCE_SHOT_INTERPOLATION`（最近框复制，不是线性插值）；距离上限必须是**非 bool 正整数**，NaN/Infinity/float/bool 一律拒绝（修复前这四种会被接受）。
5. **两条措辞勘误**（重复计数、对称差表述）已在代码文案与 protocol 中改正，并在 §5 集中说明，未修改首次报告。
6. 本轮**不产生任何分数、不评估质量、不宣称提分**。

---

## 1. 逐条对应总控问题

### 阻塞 1：`load_reference` 把缺失/null 的 `frames` 当空数组

| | 修复前 | 修复后 |
|---|---|---|
| `{"video_id":"0"}`（无 frames 字段）+ 合法空预测 | **status OK / score 100.0** | `ReferenceError`（公开边界 exit 2，结果 JSON `status=INVALID_REFERENCE`, `score=null`） |
| `frames: null` | 接受为空 | 拒绝 |
| `frames: {}` / 字符串 / 数字 | 接受为空 | 拒绝 |
| 顶层 `videos` 缺失 / null / 非 list / 空 list | 接受 | 拒绝 |
| 显式 `frames: []` | 接受 | **仍接受**（明确表示"该视频没有标注帧"） |

实现：新增 `_load_reference_payload()` 做显式结构校验；`Reference.as_summary()` 增加
`trusted_annotation: false` 与 `official_status: "NOT_OFFICIAL_GROUND_TRUTH"`，参考元数据缺失（`label_status` / `annotation_source` 为空）直接拒绝——**缺元数据不再被伪称可信标注**。

### 阻塞 2：重复 `video_id` 静默覆盖

| | 修复前 | 修复后 |
|---|---|---|
| 先声明 frame 0 真值、再用同 ID 写空 frames + 空预测 | **status OK / score 100.0**（末条覆盖首条） | `ReferenceError`（不选首条也不选末条） |

重复 `video_id`、重复帧、越界帧、未知 ID 均在载入时失败；错误由公开调用边界（`aic6.cli`）转换为 `exit 2` 与 `INVALID_REFERENCE` 记录。

### 阻塞 3：sparse 分支泄漏全视频语义

修复前后 `per_video` 字段对比（同一合成输入：预测帧 {5,6}，仅帧 5 有稀疏标注）：

| | 修复前 | 修复后 |
|---|---|---|
| 字段 | `n_pred, n_gt, precision, recall, f1, time_precision, time_recall, time_f1, unmatched_predictions, missed_ground_truth, both_empty, one_side_empty, s_iou, matched_frames, mean_matched_iou, duplicate_frames` | `annotated_frames, matched_annotated_frames, missed_annotated_frames, matched_iou_sum, mean_matched_iou_on_annotated_frames, predictions_total, predictions_not_evaluated` |
| 泄漏计数 | **12 个全视频语义字段** | **0** |

- 未标注帧计入 `predictions_not_evaluated`（**上下文，不是假阳性**），不再出现 `unmatched_predictions`。
- 不再出现整视频空判断（`both_empty` / `one_side_empty` / `empty_both_count` / `one_side_empty_count` 全部移除）。
- 零已标帧 → `sparse.evidence_status = "NO_EVIDENCE"`、`annotated_frames = 0`，仍不产出任何分数。
- `score` 始终为 `null`，状态 `SPARSE_DIAGNOSTIC`。

### 其他必要修正 1：命名与距离限制

- `SOURCE_SHOT_INTERPOLATION` → **`SOURCE_SHOT_NEAREST`**；参数 `allow_within_shot_interpolation`/`max_interpolation_gap_frames` → `allow_within_shot_nearest`/`max_shot_nearest_gap_frames`；统计键 `shot_interpolation` → `shot_nearest`；机器可读文本中不再出现 "interpolation" 字样（模块 docstring 明确写明"最近框复制，**不是**线性插值"，未实现新算法）。
- 距离上限校验 `validate_shot_nearest_gap()`：只接受**非 bool 正整数**。

| 取值 | 修复前 | 修复后 |
|---|---|---|
| `NaN` | **被接受**（比较恒为 False，上限形同失效） | 拒绝 `CompositionError` |
| `Infinity` | **被接受** | 拒绝 |
| `True` | **被接受**（等于 1） | 拒绝 |
| `1.5` | **被接受** | 拒绝 |
| `0` / `-1` | 拒绝 | 拒绝 |
| `"30"` | `TypeError` | 拒绝（`CompositionError`） |
| `30` | 接受 | 接受 |

### 其他必要修正 2：顶层状态与可交付标志

新增 `status` / `status_reason` / `deliverable` / `exit_code`，规则：

| 情形 | status | deliverable | exit |
|---|---|---|---|
| 所有窗口合法、所有选中帧有可追溯来源 | `OK_DELIVERABLE` | True | 0 |
| 存在解析失败窗口 | `FAILED_INVALID_WINDOWS` | False | 2 |
| 解析全通过但有帧缺空间来源 | `NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE` | False | 4 |
| legacy 历史重放 | `LEGACY_REPLAY_COMPLETED` | False（历史复现不是交付路径） | 0 |

- **合法空仍是成功**：只有 `{"segments":[]}` 的窗口 → `empty_windows=1`、`invalid_windows=0` → `OK_DELIVERABLE`。
- **一好一坏不被伪装成成功**：新增用例（窗口 0 合法 + 窗口 1 解析失败）→ `FAILED_INVALID_WINDOWS`，且逐窗口状态同时保留 `VALID_NONEMPTY` 与 `INVALID`，可审计。
- 公开边界 `aic6/cli.py`：`score` 与 `compose` 两条子命令都把失败写成非零退出并落盘结果 JSON；`INVALID` 优先于 `NEEDS_SPATIAL_INFERENCE`。

### 其他必要修正 3：两条措辞勘误

1. **重复计数**：`DEVIATIONS_FROM_VENDORED` 原文 "duplicate predictions are counted in N_pred through the *first valid* record only" 容易被读成"只有首条进分母"。已改为："**每一条重复记录都留在 `N_pred` 里**（作为假阳性，与既有实现一致）；只有同一帧的首条记录贡献 IoU"。行为未变，只是文案与协议口径修正。
2. **对称差表述**：首次报告与 README 里"只差 1 帧"应表述为"**1 条视频（vid 107）上移除 1 帧（1833）并新增 1 帧（1907），对称差 2 帧**"，不是"只改变一条帧记录"。新表述见 §4 与本轮 `replay_comparison.json`（`frames_added_total=1`、`frames_removed_total=1`、`videos_with_identical_frame_sets=173`）。

---

## 2. 修复前的失败证据（先补测试）

| 证据 | 文件 | 内容 |
|---|---|---|
| 总控复现（行为记录，不断言） | `prefix_reproduction.json` | C1 OK/100、C2 OK/100、C3 泄漏 12 字段、C4 无状态字段、C5 NaN/Inf/bool/float 被接受、C6 旧名称+interpolation 字样 |
| 回归套件修复前结果 | `prefix_regression_outcomes.json` + `prefix_regression_tests.txt` | 26 例：**pass 1 / fail 11 / error 14**（14 个 error 含"`aic6.cli` 缺失：不存在公开失败边界"） |
| 源码修复前哈希 | `prefix_code_hashes.json` | 19 个文件的修复前 SHA-256（来自首次 protocol 的 code_manifest） |
| 首次报告保护快照 | `phase1a_first_report_hashes.json` | 首次 5 个报告文件的哈希与字节数 |

修复后同一脚本重跑 → `postfix_reproduction.json`，6/6 合规（逐案 before/after 对照见 `test_results.json` 的 `supervisor_reproductions.comparisons`）。

新增回归测试文件：`round6_score_alignment/p1a/tests/test_boundary_regressions.py`（26 例，覆盖上表全部行为，含 CLI 退出码与真实子进程边界）。

---

## 3. 完整测试结果（`test_results.json`）

| 模块 | 用例数 | 结果 |
|---|---:|---|
| `test_timebase` | 22 | 全通过 |
| `test_segments` | 24 | 全通过 |
| `test_scoring` | 23 | 全通过 |
| `test_compose` | 15 | 全通过 |
| `test_boundary_regressions`（新增） | 26 | 全通过 |
| **合计** | **110** | **110 通过 / 0 失败 / 0 错误** |

执行命令（均记录在 `test_results.json.commands`）：

```bash
python -B -m unittest discover -s round6_score_alignment/p1a/tests -t round6_score_alignment/p1a
python round6_score_alignment/p1a/run_p1a.py --out-dir reports/round6_score_alignment/phase1a_fix
```

runner 新增 `--out-dir`（默认即 `phase1a_fix`），并**硬拒绝**写入首次报告目录：

```
$ python round6_score_alignment/p1a/run_p1a.py --out-dir reports/round6_score_alignment/phase1a
refusing to write into the first P1a report directory; pass --out-dir reports/round6_score_alignment/phase1a_fix
```

---

## 4. 历史重放结果（`replay_comparison.json`，修复后重跑）

| 检查 | 结果 |
|---|---|
| legacy 规则逐帧复现（帧+框） | **174 / 174 一致**；40,568 帧；缺失 0、多余 0、框不一致 0、回退 0 |
| legacy 重放状态 | `LEGACY_REPLAY_COMPLETED`，`deliverable=false`（历史复现非交付路径） |
| 三态解析对既有文本 | **203 / 203** 与记录一致（`VALID_NONEMPTY` 203） |
| 新时间策略 vs 第五轮 `round+闭区间` | 40,384 vs 40,568；新增 1、移除 185；61/174 帧集合完全相同 |
| 新时间策略 vs 43.48 `ceil+半开` | 40,384 vs 40,384；**新增 1、移除 1（对称差 2 帧）**；173/174 完全相同（唯一差异 vid 107：移除 1833、新增 1907） |
| 采样起点偏移 | 248 个区间中 11 个非零，最大 0.016629 s |
| 空间缺口（无镜头信息） | 选中 40,384 → 同帧 37,184、**缺口 3,200**（47 个视频）；状态 `NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE` |
| 空间缺口（单“整视频镜头”+声明 30 帧上限） | 同帧 37,184、`SOURCE_SHOT_NEAREST` 453、**缺口 2,747**（14 个视频） |
| 旧规则对照 | 3,243 帧全部由最近旧框填满（最远 3,930 帧）；新规则不复现该行为 |

`no_ground_truth_used=true`、`no_quality_score_computed=true`：**未计算任何测试准确率、上界或质量分**，旧包始终是预测而非参考。

---

## 5. 源码前后差异与受保护输入

**源码差异清单**（`test_results.json.source_diff`，共 7 个文件：2 新增、5 修改）

| 文件 | 变化 | 修复前 | 修复后 |
|---|---|---|---|
| `round6_score_alignment/p1a/aic6/cli.py` | 新增 | — | `c9ca0cc1…` |
| `round6_score_alignment/p1a/aic6/scoring.py` | 修改 | `d03d5d7f…` | `81d2886c…` |
| `round6_score_alignment/p1a/aic6/compose.py` | 修改 | `0045592a…` | `aaf26758…` |
| `round6_score_alignment/p1a/aic6/replay.py` | 修改 | `24bb7224…` | `40e24e87…` |
| `round6_score_alignment/p1a/run_p1a.py` | 修改 | `39a5dc8c…` | `595cf1ff…` |
| `round6_score_alignment/p1a/tests/test_boundary_regressions.py` | 新增 | — | `74b39dbd…` |
| `round6_score_alignment/p1a/tests/test_compose.py` | 修改（随重命名同步） | `3ade4996…` | `7d110373…` |

未改动：`timebase.py`、`segments.py`、`provenance.py`、`test_timebase.py`、`test_segments.py`、`test_scoring.py`、`hand_cases.py`、vendor 副本。

**受保护输入前后哈希**（`protocol.json` 的 `protected_inputs_before/after`，`protected_inputs_unchanged=true`）：

| 输入 | SHA-256（前=后） |
|---|---|
| 第五轮 ZIP | `e5df99b8…c3584` |
| 第五轮 predictions.jsonl | `f8f026a6…f3ef` |
| 时序原始输出 temporal_raw_v1.jsonl | `3bc0fc59…9cf72` |
| 空间基底 lora_reader predictions.jsonl | `a81a7118…ef471` |
| 测试索引 supervisor_test_metadata.json | `7f38d3f7…c428` |

**首次报告保护**（`test_results.json.first_p1a_report`）：`REPORT.md`、`protocol.json`、`test_results.json`、`replay_comparison.json`、`DATA_PILOT_BRIEF.md` 五个文件的当前哈希与修复前快照逐一相同 → `matches_first_report = true`（5/5）。

---

## 6. 未完成项与限制

1. **仍无任何真实数据的联合评分**：非测试数据没有参考标签，`OK` 分支只在手算与合成用例上验证；本轮未改变这一点（也不得用旧预测当参考）。
2. **sparse 诊断仍只有合成参考**：`SPARSE_DIAGNOSTIC` 的全部行为由合成用例与总控复现脚本覆盖；没有可用的真实稀疏空间参考。
3. **VFR 与镜头语义仍只有合成用例**：不实现镜头检测；真实数据上唯一可声明的仍是"整视频一个镜头"。
4. **818 行真实标签的段数核查仍未执行**（split 文件只在远端，本轮不连远端）。
5. **官方 evaluator 仍未取得**：`aic6` 是内部重写；官方对非法提交的处置与隐藏标签端点语义仍未知。
6. **CLI 的 `compose` 子命令未接镜头文件以外的输入校验**（例如 shots JSON 的越界检查只做区间合法性；不检查是否覆盖整视频）。
7. 本轮**未做**：P1b 数据工作、下载、远端核对、GPU、模型、训练、提交候选文件。

---

## 7. 不得主张

- 修复的是**工程边界**，不是模型能力；本轮无分数、无提分、无门槛达成。
- `SPARSE_DIAGNOSTIC` / `NOT_DELIVERABLE_*` 等状态是内部口径；官方对非法提交与稀疏标注的处理仍待核实。
- 重放假定"旧包是预测、空间基底是框来源"，不构成对官方分数的任何推断。
- 本报告不批准 P1b/P2；等待总控验收。
