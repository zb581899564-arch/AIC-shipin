# P1b 标注协议（8 来源组试点）

- run_id：`round6_p1b_20260917T0615Z`
- 适用：`round6_score_alignment/p1b/annotate.html` 的 8 个 `pilot_dev` 样本
- 状态：**协议草案，尚未被任何人工执行过**；本文件不宣称已有标注或复核

---

## 1. 这份协议解决什么

试点要回答的不是“模型能得几分”，而是：

1. 这批非测试媒体能不能被**人工**标出时间区间与稀疏构图框；
2. 标注结果能不能通过 P1a 的参考接口，而**不会把未标注当成空真值**；
3. 复核流程需要多少成本，是否值得扩展到 80 组。

它不产出质量分数，也不允许用机器输出代替人工语义。

---

## 2. 角色与身份

| 角色 | 谁来做 | 必须留下的证据 |
|---|---|---|
| 标注者（annotator） | 真人；**不得**由模型或脚本代填 | 页面 `标注者` 字段填写真实执行者标识；导出 JSON 的 `identity.annotator` |
| 复核者（reviewer） | 另一名真人 | `identity.reviewer`；复核比例 ≥20% 且覆盖全部争议样本 |
| 执行/审计（本 Agent） | 只准备工具与校验，**不填语义** | 本协议、`tool_validation.json`、`RESOURCE_USAGE.json` |

- 没有人工复核时，`reviewer` 必须留空；`label_status` 保持
  `WEAK_HUMAN_SPARSE_PENDING_REVIEW`，**不得**仅改写字符串就升格为“已复核”。
- 机器生成的任何标注都是弱标签，须显式标注来源，且不得冒充人工。

---

## 3. 逐样本操作步骤

1. 在 `annotate.html` 左栏选择样本，确认右下角显示的 `源分辨率 / fps / 帧数 / 目标比例`。
2. 用视频控件粗略定位，然后：
   - 点顶部**已校验采样帧**按钮跳到精确位置（这些位置来自容器 PTS，误差 0 帧）；
   - 或点 `用当前时间估算帧号`（此时会记录 `frame_source=browser_estimate`、`estimated_error_frames=1`）；
   - 用 `±1 / ±10 帧` 和 `对齐到最近的已校验采样帧` 精调。
3. `帧号` 输入框是**权威字段**；一切区间与关键帧都以帧号记录，秒数由 `t = frame / fps` 推导。
4. 记录时间区间：填 `起帧/止帧` → `添加区间`。区间必须满足 `0 ≤ start < end ≤ N-1`。
5. 记录稀疏构图关键帧：设 `x, y, w`（高度按 `h = w · th / tw` 推导）→ 把当前帧 `添加为关键帧`。
   宽度不得超过页面显示的 `最大合法裁剪宽度`，框必须完整落在源帧内。
6. 选择状态：
   - `有高光` — 至少一个区间；
   - `确认无高光` — 必须勾选确认框（这是唯一允许导出空真值的路径）；
   - `不确定` — 记录但不进入参考。
7. 填写 `标注者`、`不确定性说明`；有复核再填 `复核者`。
8. 导出：`导出本样本 JSON`（单个）或 `导出全部已标注样本`（跳过未标注样本）。

---

## 4. 状态与导出规则（与工具、校验器一一对应）

| 状态 | 导出 `reference_derivation.mode` | 产生 P1a 参考？ | 语义 |
|---|---|---|---|
| `UNANNOTATED`（初始） | `NOT_EXPORTABLE` | 否（`intervals/keyframes = null`） | 未标注 ≠ 空 |
| `UNCERTAIN` | `NOT_EXPORTABLE` | 否 | 不计入参考 |
| `NO_HIGHLIGHT` 未勾选确认 | `NOT_EXPORTABLE` | 否 | 防止把“没标”当“无高光” |
| `NO_HIGHLIGHT` 已勾选确认 | `NO_HIGHLIGHT_EMPTY_GT` | 是：`coverage=full, frames=[]` | 整段无高光；空预测得 1，非空预测得 0 |
| `HAS_HIGHLIGHT` + 区间 + 关键帧 | `SPARSE_KEYFRAME_GT` | 是：`coverage=sparse` | 只有列出的帧被标注 → P1a 只出 `SPARSE_DIAGNOSTIC` |
| `HAS_HIGHLIGHT` 只有区间 | `TEMPORAL_ONLY` | 否 | 仅时间诊断，不构成联合指标参考 |

**未标注样本不会“消失后仍得分”**：若参考只覆盖部分视频，P1a 对完整覆盖要求为 `full` 的评分会返回
`NOT_COMPUTABLE`（`tool_validation.json` 的 `p1a_integration.incomplete_full_reference_is_refused` 实测为
`NOT_COMPUTABLE`，分数为 `null`）。

---

## 5. 时间与帧号的误差约定

- 浏览器 `currentTime` 不是精确帧号；页面把估算与帧号分开记录（`frame_source` / `estimated_error_frames`）。
- 采样帧位置来自容器 PTS（`media_verification.json` 的 `pts`）：本试点 8 个文件均为 CFR
  （步长与 `1/fps` 完全一致，最大偏差 0，流起点为 0），因此 `frame / fps` 与容器时间一致。
- 若以后接入 VFR 素材：必须先提供显式 PTS 列表，不得用 `index/fps` 冒充帧时间（P1a 的 VFR 接口即为此设计）。

---

## 6. 复核要求

1. 复核比例 ≥20% 的样本，且**覆盖全部争议样本**（状态为 `UNCERTAIN` 或区间/框存在分歧的）。
2. 复核者独立打开媒体核对帧号与框，不允许只看导出 JSON。
3. 复核结论写入 `复核者` 字段与 `说明`；出现分歧时保留两方记录，不做静默合并。
4. 复核完成后由总控决定是否把 `label_status` 升格；升格必须附复核记录与协议更新，不能只改字符串。

---

## 7. 明确禁止

- 不得标注官方测试视频（测试素材不在本包内，也不得加入）。
- 不得把媒体、帧或标注上传到任何外部服务，也不得调用外部模型生成标注。
- 不得由执行 Agent 或脚本代替人工填写 `有高光 / 无高光 / 构图框`。
- 不得为了让某个候选“看起来更好”而修改已导出的标注；修订须新增记录并注明原因。
- 不得把这 8 组当成“盲测留出集”：全部为 `pilot_dev`，后续 80 组扩展时试点及其同源视频不得进入新 holdout。
