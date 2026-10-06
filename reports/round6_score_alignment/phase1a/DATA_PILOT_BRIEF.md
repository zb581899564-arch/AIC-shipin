# 数据试点简报（P1b 建议稿，8–16 来源组）

- 归属：`round6_score_alignment` P1b 前置建议；由 P1a 出具，**只建议不批准**
- 状态：**未完成人工审查，未构建任何数据集，未下载任何素材**（P1a 不联网、不连接远端）
- 目标口径：本文件只规划 8–16 个来源组的**试点**；ROADMAP 的 80 组仍是扩展目标，不因数量强造负例或机器“真值”

---

## 1. 为什么先做 8–16 组试点

- 现有唯一可用的空间参考（历史 `cropRois`）坐标空间与媒体身份均未确证，且只覆盖 10 组/40 帧，判别力不足。
- 在没有**人工复核**的参考之前，任何更大规模的自动化“标注”都只是弱标签，无法支撑 P2 的候选选择。
- 试点用于检验：素材许可是否可得、标注协议是否可执行、复核是否真的发生。**试点通过前不扩到 80 组。**

---

## 2. 材料盘点（严格区分本地可得 / 远端 / 公开来源）

### 2.1 本地已存在（P1a 实测）

| 路径 | 内容 | 备注 |
|---|---|---|
| `高光剪辑训练集/qvhighlights-videos/` | **空目录（0 文件）** | 本地无任何训练视频 |
| `tmp_orarl_round1/frames/*.jpg` | 8 张抽帧图（probe0/1/2/3 各 2 张） | 第 1 轮诊断期产物；**图像而非视频**，不足以做逐帧联合诊断 |
| `reports/orarl_round*/outputs/overlays/*.png` | 回画接触图（含框叠加） | 渲染图，非原始媒体 |
| `tmp_orarl_round1/src/OraRL/assets/orarl-teaser.mp4` | 第三方仓库自带的宣传视频 | **不是**诊断素材，许可不明 |
| 结论 | 本地**没有**可用的合规非测试视频语料 | 试点必须先解决素材来源 |

### 2.2 远端已记录（P1a **不访问**，仅列路径与哈希）

| 路径 | 内容 | 已记录哈希 |
|---|---|---|
| `/home/inspur/aic_video_data/videos` | 11,576 个 mp4（150 秒窗口派生文件，如 `1J7QewIO9tc_210.0_360.0.mp4`） | 未逐文件哈希 |
| `/home/inspur/aic_video_data/labels/train.jsonl` | 987 行原始标签（含 `cropRois`/`crop_keyframes`） | `7177731fb7af99e8581c0ec071d116cdb9e6652a6b2b355cd8100364a004c629` |
| `orarl_round4/evidence/mapping_rows.jsonl` | 987 行映射结论（usable 820 / missing 75 / time_uncertain 92） | `a07a1ba0ea89e820311989b523ca85c87b65cb7b6381f8ff97d597e9994732fc` |
| `temporal_round5/data/{train,dev,holdout}.jsonl` | 818 行派生**时序**记录（**无空间字段**） | `e54e2178…` / `e5d2113c…` / `e2c8d0cf…` |

**必须区分**：原始 987 行标签**有** `cropRois`/`crop_keyframes`；818 行派生记录**没有**。派生字段缺失不等于原始标签没有空间信息（总控 P0 勘误 4）。当前未批准 `cropRois` 作为可信空间监督，不等于其永远不能利用。

### 2.3 公开来源（项目既有记录，未在 P1a 访问）

| 来源 | 记录位置 | 许可/身份要点 |
|---|---|---|
| RefCOCO val（HF 镜像 `rhymes-ai/RefCOCO`，`val.jsonl` sha256 `340d94be…`；图像 `images.cocodataset.org`） | `reports/orarl_round3/evidence/refcoco_frozen.json` | 仅用于**空间定位接口**测试；是 RefCOCO 标注 + COCO 图像，**不是**高光剪辑任务标注 |
| QVHighlights 视频包 `nlp.cs.unc.edu/data/jielei/qvh/qvhilights_videos.tar.gz`（143.7 GB） | `reports/supervisor_official_archive_probe.json` | 第 1 轮只读了 8 MiB 探针，**未下载**；任务语义不同 |
| 比赛测试视频 | — | **禁止**作为诊断素材、禁止人工查看、禁止样本调参 |

---

## 3. 试点设计（8–16 来源组）

| 项 | 建议 |
|---|---|
| 规模 | 先 **8 组**跑通全流程；协议无误后扩到 16；80 组为目标，不在试点内 |
| 划分 | 试点内 4 组用于开发、4 组封存用于一次留出；来源组不交叉，近重复审计按（时长, 分辨率, fps, 来源组, 关键帧指纹）多字段，不只比文件名 |
| 画幅 | 目标 16:9 与 9:16 **各半**（历史弱标签 987 条全为 9:16，测试集为 119:16:9 + 55:9:16，比例不匹配） |
| 负例 | 每部分争取 ≥2 条**自然无高光**样本；“无高光”的可操作定义尚未达成一致 → **先记录分歧再定协议**，不得为了凑数人工制造负例 |
| 时长/密度 | 覆盖短（≈10 s）与长（≈150 s）两端；长视频用于检验 30 秒窗口边界与跨窗行为 |
| 标注粒度 | 时间区间（起止秒 + 对应源帧）；**稀疏**构图关键帧（帧号 + `[x, y, w]`，高度按目标比例推导）；可见主体/构图意图；切镜边界（若人工可见）；插值规则；不确定性说明 |
| 允许的产物 | 稀疏帧指标（`SPARSE_DIAGNOSTIC`）；不得把未经验证的插值框当逐帧真值；不得据此产出全视频联合分 |
| 禁止 | 用测试视频；把机器输出标成人工；用机器“真值”替代复核；为凑规模伪造负例或复制来源组 |

---

## 4. 每个样本必须留下的证据

```json
{
  "sample_id": "…", "source_group": "youtube_id", "split": "dev|holdout_pilot",
  "media": {
    "local_path": "…", "source_url": "…", "access_date_utc": "…",
    "license_or_terms": "许可名称/条款链接", "sha256": "本地文件真实哈希",
    "ffprobe": {"width": 0, "height": 0, "avg_fps": 0.0, "nb_frames": 0, "duration_sec": 0.0},
    "is_cfr": "measured|unknown", "pts_available": false
  },
  "target_ratio_wh": [9, 16],
  "time_intervals_source_sec": [[0.0, 0.0]],
  "composition_keyframes": [{"frame": 0, "box_xyw": [0, 0, 0], "frame_is_exact": true}],
  "cut_boundaries_source_sec": [0.0],
  "interpolation_rule": "linear_within_shot_only",
  "has_highlight": true,
  "annotation": {"annotator": "…", "annotated_utc": "…", "uncertainty": "…"},
  "review": {"reviewed_by": null, "review_share": 0.0, "disputed": false},
  "label_status": "WEAK_HUMAN_SPARSE",
  "overlap_with_historical": {"same_youtube_id": false, "same_source_group": false}
}
```

- `sha256` 必须是**真实计算**的媒体哈希（历史 818 行的媒体身份从未被哈希验证；`provenance.video_sha256` 与源文件全部不一致，只说明非同字节媒体，不能单独证明映射错误）。
- 复核：**≥20% 样本 + 全部争议样本**由第二人复核，记录复核主体；其他模型输出**不得**标成人工。
- 来源泄漏：与历史 818/987 行做 `youtube_id` 与 `source_group` 交集检查并落档。

---

## 5. 人工审查状态（未完成，必须如实记录）

| 项 | 状态 |
|---|---|
| 是否已有人工标注 | **否** |
| 是否已有第二人复核 | **否** |
| 是否有书面许可记录 | **否** |
| 是否有可用素材 | **否**（本地 0 个可用视频） |
| 本文件中的任何“标注协议” | 仅为建议，未经人工执行验证 |

**不得**由本模型或任何自动流程充当人工标注员；未经人工执行的参考一律只能标为弱标签，且不得据此宣布任何提分或门槛达成。

---

## 6. 进入 P1b 前需要总控决定的事项

1. 素材来源与许可路线：允许下载公开视频（需登记 URL/许可/日期）还是仅使用远端已记录的既有语料（需先解决媒体身份与坐标空间）？
2. 标注人力与复核安排：谁标注、谁复核、可投入多少工时；若无人力，P1b 只能交付“协议 + 空表”，不得启动扩集。
3. “自然无高光”的可操作定义是否先冻结；若分歧无法收敛，按 ROADMAP 记录分歧并调整协议。
4. 是否接受试点阶段只产出 `SPARSE_DIAGNOSTIC`（不足以支撑 P2 的候选选择门槛）。
5. 磁盘/带宽预算登记（历史上限 80 GiB 仍生效；P1a 未新增媒体）。
