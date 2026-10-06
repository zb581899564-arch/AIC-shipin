# P1b 离线标注说明

run_id：`round6_p1b_20260917T0615Z`；样本：8 个来源组（4 个目标 16:9、4 个目标 9:16），全部标记 `pilot_dev`。

## 打开方式

直接双击 `annotate.html`（纯 `file://`，不需要服务器、不联网）。若浏览器限制本地视频，
用 `python -m http.server` 起一个本地静态服务并从 `http://127.0.0.1:8000/annotate.html` 打开即可
（页面本身不发起任何外部请求）。

## 媒体清单

| 样本 | 来源组(YouTube) | 源分辨率 | fps | 帧数 | 目标比例 | 大小 | SHA-256 |
|---|---|---|---|---|---|---|---|
| P01 | `0ReDuH0_rpI` | 534x300 | 23.976 | 3597 | 16:9 | 11.72 MiB | 85999bd93264… |
| P02 | `FQEW3xLOa9M` | 534x300 | 29.970 | 4496 | 16:9 | 11.18 MiB | c32486d888ec… |
| P03 | `GYH6HdJ6nao` | 534x300 | 25.000 | 3750 | 16:9 | 8.76 MiB | 6c0e966e42f8… |
| P04 | `QPcwfuStFnU` | 534x300 | 23.976 | 3597 | 16:9 | 17.95 MiB | 6bad7c178fe0… |
| P05 | `Snpclpo7Ono` | 534x300 | 25.000 | 3750 | 9:16 | 4.16 MiB | e01cb649f2ff… |
| P06 | `Xm1ouND-aiQ` | 534x300 | 29.970 | 4496 | 9:16 | 9.98 MiB | c4375a95f042… |
| P07 | `dEuxoRj0G5Y` | 534x300 | 30.000 | 4500 | 9:16 | 13.82 MiB | e8c410e21d5d… |
| P08 | `vvT-gqzwUxA` | 534x300 | 25.000 | 3750 | 9:16 | 9.65 MiB | 2f8462e601fd… |

（完整字段见 `pilot_manifest.json`；每个样本的远端哈希、PTS 统计、12 个已校验采样帧都在里面。）

## 标注状态机（重要）

| 状态 | 含义 | 能否导出为参考 |
|---|---|---|
| `UNANNOTATED`（默认） | 尚未标注 | **否**；导出 `NOT_EXPORTABLE`，且 `intervals/keyframes = null`（不是 `[]`） |
| `HAS_HIGHLIGHT` + 有时间区间 + 有关键帧 | 稀疏构图标注 | 导出 `coverage=sparse`（只有列出的帧被标注） |
| `HAS_HIGHLIGHT` + 只有时间区间 | 仅时间标注 | `TEMPORAL_ONLY`：只能做时间诊断，**不构成联合指标参考** |
| `NO_HIGHLIGHT` + 勾选确认 | 标注者主动确认整段无高光 | 导出空帧集合（`coverage=full, frames=[]`） |
| `UNCERTAIN` | 不确定 | **否**；不计入参考 |

- 未标注 ≠ 空。只有真实标注者勾选“确认无高光”才会产生空真值。
- 复核者字段默认留空；**没有人工复核就不要填写**，页面不会自动填。
- 页面导出的 `label_status` 固定为 `WEAK_HUMAN_SPARSE_PENDING_REVIEW`，人工复核前不得升格。

## 帧号与误差

浏览器 `currentTime` 不是精确帧号。页面做法：

1. 顶部按钮是**已用容器 PTS 校验过**的采样帧，点击可跳到精确位置；
2. `帧号` 输入框是权威字段，可用 “用当前时间估算帧号” 填入估算值（此时记录
   `frame_source=browser_estimate`、`estimated_error_frames=1`）；
3. `±1 / ±10 帧` 按钮按 `t = frame / fps` 跳转；
4. 目标比例约束：框高按 `h = w · th / tw` 推导，宽度不得超过 `max_legal_crop.max_width`。

## 导出

- `导出本样本 JSON`：单样本，含 `reference_derivation`（模式 + 理由 + 可直接喂给 P1a 的参考片段）。
- `导出全部已标注样本`：只导出**已标注且填了标注者**的样本，未标注样本不会进入导出。
- 导出文件请放在 `reports/round6_score_alignment/phase1b/annotations/` 下再用
  `round6_score_alignment/p1b/validate_exports.py` 校验（含未标注≠空、框界内/比例、身份、时间映射）。

## 禁止

- 不得把本页或任何帧/视频上传到外部服务；
- 不得用测试视频做标注；
- 不得由模型代替人工填写高光或构图语义；本页面初始状态即为“未标注”，这是有意为之。
