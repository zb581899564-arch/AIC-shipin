# orarl_round3 — 时间审计纠错 + 最小可计算空间诊断

- 远程目录：`/home/inspur/aic_video_work/orarl_round3`
- 本地副本：`G:\ai\AIC视频\reports\orarl_round3`
- 复用：round1 模型（`orarl_round1/model/Video-ORA-4B`）与环境（`orarl_round1/env/orarl_hf`）；
  round1 / round2 目录**全部只读**，两份 REPORT.md 哈希未变
  （`30295caf…` / `048bf1e6…`）
- 本轮**不训练、不跑全量测试推理、不提交比赛、不升级驱动、不安装新的大型推理栈、不下载其他大模型**
- 交付：`REPORT.md`、`ERRATA.md`、`evidence/time_token_audit.json`、冻结数据清单、
  生成配置、逐样本指标、复现入口

---

## 0. 五个必答问题

### Q1. 模型实际收到了哪些时间信息？旧结论哪里错了？

**模型收到的是显式时间文本，每个 temporal patch 一个 `<X.X seconds>` 标签。旧结论「最终输入没有时间信息」是错的。**

已安装文件 `transformers/models/qwen3_vl/processing_qwen3_vl.py`
（sha256 `b51f77d783b4a88d503bf9198828d46f71e3ead3833da2631748188b159253ba`）第 151–162 行：

```python
151  # if timestamps are not provided, calculate them
152  curr_timestamp = self._calculate_timestamps(
153      metadata.frames_indices, metadata.fps,
155      self.video_processor.temporal_patch_size)
158  video_placeholder = ""
160  for frame_idx in range(video_grid_thw[index][0]):
161      curr_time = curr_timestamp[frame_idx]
162      video_placeholder += f"<{curr_time:.1f} seconds>"
163      video_placeholder += (self.vision_start_token + "<|placeholder|>"*frame_seqlen
                                + self.vision_end_token)
```

`_calculate_timestamps`（第 257–268 行）：`t = idx / fps`，再按 temporal patch（2 帧）取均值。

**实测（`evidence/time_token_audit.json`，本轮真实跑处理器并解码 `input_ids`）**

| 视频 | `input_ids` 长度 | video_pad 数 | **时间字面量个数** | 前 6 个 | 末 2 个 |
|---|---|---|---|---|---|
| `known_time_32s_30fps.mkv`（32.000 s） | 1115 | 960 | **16** | `<0.5> <2.6> <4.7> <6.7> <8.8> <10.8>` | `<29.4> <31.4>` |
| round1 片段（32.200 s / 962 帧） | 2603 | 2448 | **16** | `<0.5> <2.6> <4.7> <6.7> <8.8> <10.9>` | `<29.4> <31.5>` |

`input_ids` 解码（保留特殊 token）实文开头：

```
<|im_start|>user
<0.5 seconds><|vision_start|><|video_pad|><|video_pad|>…（每 patch 60 个）
```

**旧结论错在哪**：round2 的 `input_time_info.py` 检查的是**加工前**的 `text`
（`apply_chat_template` 的输出），并把 `any_numeric_timestamp_list` **硬编码为 `False`**；
随后只列出 processor 的**输出张量键名**，**从未解码 `input_ids`**。
而时间恰恰是在 processor 内部以**文本**形式插入的，不体现为任何张量键。

**附带的重要事实**：32 秒视频只有 **16 个**标签（2 帧合 1 patch），间距约 **2.07 s**，
且值是 **patch 内两帧名义时间的均值**，因此**不是整数秒**（0.5, 2.6, 4.7 …）。
而提示词要求输出键 1..32（每秒一个）。**两者粒度与取值都不一致**——
这正是「键 N ↔ 真实秒 N」无法从模型输入本身推出的原因（见 Q2 的指标判定）。

**时间语义的两层区分（本轮明确分开）**

| 层 | 内容 | 证据 |
|---|---|---|
| 真实容器 PTS | 从文件读出的帧时间戳 | `time_token_audit.json` 的 `real_container_pts_sec_for_sampled_frames`（字段 `best_effort_timestamp_time`，962/962 帧取到） |
| 名义时间 `index/fps` | 采样序号 ÷ 容器 fps | 同上 `index_over_fps_nominal_sec` |
| 处理器插入的时间标签 | patch 内名义时间的均值 | 同上 `processor_time_computation.timestamps` |

实测两者**不总是相等**：

| 视频 | 名义 vs 容器 PTS 最大差 | 平均差 |
|---|---|---|
| `known_time`（32.000 s） | 0.000333 s | −0.000021 s（1 ms 内一致） |
| round1 片段（32.200 s） | **0.132683 s** | **+0.068099 s** |

round1 片段抽样帧：帧 0 名义 0.0000 / PTS **0.066016**；帧 961 名义 32.0333 / PTS **32.166016**。

**并且**：「第 N 个采样帧落在某秒格」与「输出键 N 的真实标注语义」是**两件事**。
前者本轮已实测（known-time 视频 32.000 s 下槽位 N ↔ 第 N−1 个秒格，0/32 错；
32.200 s 片段 2/32 槽错）。**但这只能说明采样落点，不能证明作者标注里键 N 就等于真实秒 N**
——后者要看标注文件，而 `annotations/tracking/got10k.jsonl` 属于未下载的 `OraRL-Data`，
本轮无证据，故不作断言（见 `ERRATA.md` ERRATUM 4）。

---

### Q2. 在有精确运动真值的条件下，跟踪是否优于固定首帧框？

**没有。跟踪（S1）没有优于固定首帧框基线（S0）。**

4 条合成视频，目标几何真值由生成代码逐帧给出；初始化帧单独报告，主对照**排除**初始化帧。

**（a）S1 vs S0，32 个一秒槽的均值（排除初始化槽）**

| 片段 | S0（首帧框恒定） | S1（跟踪） | S1−S0（M1/M2/M3 三种映射） | 说明 |
|---|---|---|---|---|
| syn1_translate_x | 0.084 | 0.084 | +0.000 / +0.000 / +0.000 | **S1 逐字复制 anchor**（32/32），与 S0 完全等价 |
| syn4_translate_scale | 0.104 | 0.104 | −0.000 / −0.000 / −0.000 | **S1 逐字复制 anchor**（32/32），与 S0 完全等价 |
| syn3_scale_up | 0.204 | 0.120 | **−0.084 / −0.074 / −0.066** | S1 明显**更差** |
| syn2_translate_xy | 0.047 | 0.088 | **+0.041 / +0.046 / +0.047** | S1 名义上更好，但该次**唯一出现协议失败**（越界框） |

- 4 条中有 **2 条 S1 ≡ S0**（因为 S1 把提示词里的 anchor 原样复制了 32 次）；
  1 条 S1 更差；1 条 S1 略好（+0.041 绝对 IoU，但两者都极低，且该次输出含越界框）。
- **结论跨 M1/M2/M3 三种键↔时间映射符号一致**，因此定性结论稳健。

**（b）主指标判定：`NOT_COMPUTABLE`。**
理由（按本轮要求，不强行配对）：处理器实际给模型的时间标签是 **16 个、非整数、间距约 2.07 s 的 patch 均值**，
而输出键被要求为 1..32 每秒一个。**键 N ↔ 真实秒 N 的对应无法从模型输入本身建立**，
作者评测代码也从不校验。因此 S1 的绝对 IoU 不作正式指标，只报三种候选映射下的取值；
**只有跨映射不变的结论才允许使用**，而上面的「S1 不优于 S0」正属于此类。

**（c）初始化帧单列**：初始化槽 IoU（S0/S1 在 t=0）为 0.990–0.998
（因 anchor 就是 GT 首帧框），**已按要求从主对照中排除**。

---

### Q3. 独立空间定位能否随目标平移和缩放作出正确响应？

**能——位置响应正确；尺寸响应在目标很小时不够准。**

S2 = 在 8 个**预先固定**的关键帧（帧 10,50,…,290；t = 1,5,…,29 s）上逐帧独立做空间定位，
**不传上一帧框**。同一片段、同一目标、同一评估时刻下三方对比：

| 片段 | S0 恒定首帧框 | S1 跟踪 | **S2 逐帧定位** | S2−S0 | S2−S1 |
|---|---|---|---|---|---|
| syn1_translate_x（平移） | 0.126 | 0.126 | **0.487** | +0.361 | +0.361 |
| syn2_translate_xy（对角平移） | 0.086 | 0.122 | **0.380** | +0.295 | +0.258 |
| syn3_scale_up（原地放大） | 0.241 | 0.159 | **0.494** | +0.253 | +0.335 |
| syn4_translate_scale（平移+缩小） | 0.145 | 0.145 | **0.474** | +0.329 | +0.329 |

- S2 在**每一条**上都大幅优于 S0 与 S1（+0.25 ~ +0.36 IoU）。
- **中心误差很小**：4 条片段均值 0.0400–0.0492（按 1414 对角线归一），说明**框跟着目标移动**。
- **尺寸响应较弱**：面积比中位数 0.909–1.019（整体尺度尚可），
  但单帧极值暴露问题——`syn3_scale_up` 在目标最小（30 px）时 IoU 仅 **0.055**，
  `syn4` 在目标缩到最小时 IoU 仅 **0.067**。即**目标很小时框偏大**。
- 逐帧明细（32 点）与回画见 `evidence/r3_metrics.json`、`outputs/overlays/s2_synthetic_keyframes.png`。

**适用范围限定**：合成片段的目标是一个**纯色矩形**，并非自然物体；
它只能证明「受控几何响应」，**不能**据此声称真实视频跟踪可用，也不能换算比赛分数。

---

### Q4. 公开可信图片评测是否完成，结果和适用范围是什么？

**完成。10 张公开 RefCOCO 图片（官方标注框），全部有效输出。**

- **标注来源**：RefCOCO val 拆分，取自 HF 镜像仓 `rhymes-ai/RefCOCO` 的 `val.jsonl`
  （3,671,331 B，sha256 记录在案）——RefCOCO 正是作者空间定位评测器所针对的基准族，
  属「可从作者评测清单追溯的合法公开数据」。
- **图片来源**：**官方 COCO 图床** `images.cocodataset.org`（200 OK），按标注行的
  `COCO_train2014_*.jpg` 文件名下载。
- **选取规则（在任何模型输出之前写定）**：按文件顺序读 `val.jsonl`，每个不同图片取首行，
  取前 10 张不同图片；表达式取 `messages` 里固定前缀之后的文本；真值取该行 `bbox`
  （像素 xyxy，位于该行 `hw` 声明的画幅内），换算成 norm1000。
  **看到模型输出后没有替换或剔除任何一行。**
- **身份校验**：下载后逐张比对解码得到的 (w,h) 与标注行声明的 (h,w)：**10/10 一致**
  （`evidence/refcoco_frozen.json` 的 `hw_matches_image`）。

**结果（`evidence/r3_metrics.json`，无效输出保留在分母中）**

| 指标 | 值 |
|---|---|
| 请求样本数 | 10 |
| **有效输出比例** | **1.000**（10/10；分母含任何无效输出，本轮为 0） |
| **IoU 中位数** | **0.9312** |
| IoU 均值 | 0.8740 |
| IoU 最小 / 最大 | **0.3283** / 0.9803 |
| IoU ≥ 0.5 | **9 / 10** |
| IoU ≥ 0.25 | 10 / 10 |
| 中心误差均值 | 0.0215 |
| 面积比中位数 | 1.012 |

逐样本：ref00 0.885、ref01 0.930、ref02 0.946、ref03 0.980、ref04 0.905、ref05 0.930、
ref06 0.968、ref07 0.935、ref08 0.932、**ref09 0.328**。
失败案例 **ref09**（表达式 `person in white sleeping far away`，暗光卧室场景）：
预测框偏移且面积偏大（面积比 2.935），已保留不剔除，回画见
`outputs/overlays/s2_public_refcoco.png`。

**适用范围**：
- 该结果说明模型在**真实图片、公开标注、norm1000 坐标约定**下，空间定位**确实有效**；
  这与 round2 仅凭「7/7 格式完整」的说法有本质区别——**这次是有真值的指标**。
- **不适用**于：AIC 赛道评分、视频跟踪、裁剪收益、任何与 43.4800 / 57 分的比较。
  样本仅 10 张，取自 RefCOCO val 前 10 个不同图片（非随机抽样），不能当作 RefCOCO 全量精度。

---

### Q5. 哪条路线值得交由总控安排真实视频裁剪对照？

**建议：把资源投到「独立逐帧空间定位」，不要投到跟踪；两者不要在真实视频裁剪对照里等价对待。**

证据：

1. **跟踪路线在受控条件下没有优势**：S1 与固定首帧框基线 S0 打平（2/4 逐字复制 anchor）、
   输 1/4、仅 1/4 名义略好且那次含协议失败。**用一个不优于常量的模块来产生裁剪框，收益无从谈起。**
2. **逐帧定位路线在同样条件下大幅领先**：S2 相对 S0 提升 +0.25 ~ +0.36 IoU，相对 S1 亦然。
3. **逐帧定位在真实公开图片上也成立**：IoU 中位数 0.931、9/10 ≥ 0.5（有真值）。
4. **但仍有明确缺口需要总控决策**：
   - 合成目标是纯色矩形，**小目标尺寸响应差**（最小尺寸时 IoU 0.055）；
     真实视频里主体尺度变化大，需要在真实视频上验证。
   - 逐帧定位的**时间一致性**未知：逐帧独立定位可能抖动；本轮没有测跨帧稳定性。
   - **没有可信真值的真实视频**仍然算不出指标。round2 的 7 个真实片段全部 `NOT_COMPUTABLE`，
     本轮也**没有**为它们补真值。
   - **无论哪条路线，都不能把目标检测框直接当成 AIC 最优裁剪框**；本轮**未生成任何裁剪候选**。

**建议交给总控决策的具体问题**（本轮不自行启动）：
- 是否批准在**真实、非测试**视频上建立少量人工核验的时空标注（作为裁剪对照的评测基础）？
- 若做真实视频裁剪对照，是否同意**先把逐帧定位作为框来源**、跟踪只作为对照臂（或不设跟踪臂）？
- 逐帧定位的**跨帧稳定性**是否需要单列一个诊断（例如抖动率），还是与精度合并看？

---

## 1. 完成项、未完成项与阻塞

### 1.1 完成项

| 项 | 结果 | 证据 |
|---|---|---|
| 时间 token 实测 | 解码最终 `input_ids`，提取 16 个 `<X.X seconds>` | `evidence/time_token_audit.json` |
| 四类信息对应关系保存 | 帧索引 / 元数据 / 处理器时间计算 / 最终 token 解码 | 同上（同一条记录内含四个字段组） |
| 真实 PTS 与名义时间分开 | 962 帧 PTS 全部取到；两者最大差 132.7 ms | 同上 `nominal_vs_real_pts` |
| 「采样落点」与「标注语义」分开 | 前者实测、后者无证据不表态 | 本文 Q1 末段 + `ERRATA.md` ERRATUM 4 |
| `ERRATA.md` | 6 处更正，不覆盖旧报告 | `ERRATA.md` |
| B/C 复制情况程序化重统计 | 整段复制 vs 部分复制 vs 接近但不等 | `evidence/bc_copy_recount.json` |
| 公开可信图片 | 10 张 RefCOCO，10/10 身份校验通过 | `evidence/refcoco_frozen.json` |
| 合成几何诊断 | 4 条片段、32 秒、10 fps、逐帧精确真值 | `evidence/synthetic_manifest.json`、`data/gt_*.json` |
| S0/S1/S2 对照 | 含**同点位**公平对照 | `evidence/r3_metrics.json` |
| 逐样本指标 + 回画 | IoU / 中心误差 / 面积比 / 有效比例 | 同上 + `outputs/overlays/*.png` |
| 失败案例保留 | ref09、`s1_syn2_translate_xy`（越界框）均保留 | 同上 |
| 未因纠错重跑 round2 全部 GPU 作业 | 仅新跑 2 个必要作业 | `evidence/r3_accounting.json` |

### 1.2 未完成项 / 范围外

1. **真实视频仍无真值**，故 round2 的 7 个真实片段**没有**重算指标；本轮不为其编造真值。
2. **未测逐帧定位的时间一致性（抖动）**——本轮只测逐帧精度。
3. **未做真实视频裁剪对照**，未生成裁剪候选（按本轮要求）。
4. **未下载 `OraRL-Data`**，故 GOT-10k 标注原文仍无法确证（`ERRATA.md` ERRATUM 4 的限定）。
5. 未复现作者完整评测栈（vLLM / flash-attn / fla 未安装）。

### 1.3 阻塞与偏差

| # | 事项 | 处理 |
|---|---|---|
| F1 | `huggingface.co` 与 `datasets-server.huggingface.co` 在本机不可达 | 走 `hf-mirror.com` 取数据集文件；**未使用** `load_dataset` 流式接口 |
| F2 | `raw.githubusercontent.com` 本轮复测超时（round2 曾成功） | 该域名可达性不稳定，如实记录；round2 的源码独立复核结论保留其当时的成功证据 |
| F3 | 该 ffprobe 对 `frame=pts_time` 在 ffv1/mkv 上返回空 | 改用 `best_effort_timestamp_time`，962/962 帧取到，字段名已记录 |
| F4 | RefCOCO 常见镜像多为 parquet（130–440 MB/片）或 images.zip 2.68 GB | 改用 `rhymes-ai/RefCOCO` 的 `val.jsonl`（3.7 MB）+ 官方 COCO 单图下载；**未下载整套数据集** |
| F5 | 本次 ffmpeg 无 libx264 | 合成视频用无损 `ffv1/mkv` |
| F6 | `s1_syn2_translate_xy` 出现越界框（`[384,997,541,997]` 等，高为 0） | 判定 `protocol_complete=false`、作业 exit 5 —— 正是 D2 机制；**该案例保留不剔除** |

---

## 2. 时间 token 证据摘要

详见 `evidence/time_token_audit.json`。要点：

- 处理的是**已安装**文件 `.../transformers/models/qwen3_vl/processing_qwen3_vl.py`
  （sha256 `b51f77d783b4a88d503bf9198828d46f71e3ead3833da2631748188b159253ba`，271 行）。
- 插入点：第 151–162 行；时间算法：第 257–268 行（`idx/fps`，按 patch 取均值）。
- 每个 patch 的替换串为 `<X.X seconds>` + `vision_start` + `frame_seqlen` 个占位 + `vision_end`；
  最终占位被换成 `video_pad`（id 248057）。
- 实测每视频 **16** 个时间字面量、**960 / 2448** 个 `video_pad`。
- 已知时间视频（32.000 s）的 patch 0 = 帧 [0, 31]，其**像素编码的真实秒为 [0, 1]**，
  而插入标签是 `<0.5 seconds>`（两帧名义时间均值）——**标签落在 2 秒跨度中点，不对应单帧秒**。

---

## 3. 冻结数据清单与生成配置

### 3.1 公开图片（`evidence/refcoco_frozen.json`）

10 张，均为 `COCO_train2014_*`，身份校验 10/10 通过。选取规则、坐标制、来源 URL、
逐图 sha256 均在文件中。**执行模型未画任何框**；真值全部来自官方标注行。

### 3.2 合成视频（`evidence/synthetic_manifest.json` + `data/gt_*.json`）

- 画布 **320×240**，**10 fps**，**32.000 s**，**320 帧**，种子 `20260916`（轨迹为解析式，与种子无关）。
- 4 条轨迹（**推理前固定**）：

| 片段 | 轨迹 | 首帧框 (norm1000) | 末帧框 (norm1000) |
|---|---|---|---|
| syn1_translate_x | 左侧→右侧平移，尺寸不变 | [31.25, 375, 218.75, 625] | [781.25, 375, 968.75, 625] |
| syn2_translate_xy | 对角平移 | [46.88, 62.5, 203.12, 270.83] | [796.88, 729.17, 953.12, 937.5] |
| syn3_scale_up | 居中放大 | [453.12, 437.5, 546.88, 562.5] | [281.25, 208.33, 718.75, 791.67] |
| syn4_translate_scale | 右移同时缩小 | [0, 333.33, 250, 666.67] | [828.12, 437.5, 921.88, 562.5] |

- 目标**全程可见**，**无切镜、无遮挡、无消失**。
- 逐帧真值：`gt_box_px_per_frame`（320 条）与 `gt_box_norm1000_per_frame`（320 条），
  由生成代码解析式给出；`gt_index_to_seconds` 给出帧↔秒对应。
- 关键帧**先固定**：帧 10,50,90,130,170,210,250,290（t = 1,5,…,29 s），最多 8 帧/条，符合要求。
- **冻结后推理**，未按输出挑选成功案例。

**范围声明（同时写入 manifest）**：合成片段只检验受控几何响应，
**不能**据此声称真实视频跟踪可用，**不能**换算比赛分数。

---

## 4. 逐样本结果

### 4.1 S2 公开 RefCOCO（10 例，有真值）

| case | IoU | 中心误差 | 面积比 |
|---|---|---|---|
| s2_ref00 | 0.8852 | 0.0087 | 0.977 |
| s2_ref01 | 0.9299 | 0.0018 | 0.944 |
| s2_ref02 | 0.9455 | 0.0043 | 1.021 |
| s2_ref03 | 0.9803 | 0.0032 | 1.003 |
| s2_ref04 | 0.9053 | 0.0128 | 1.068 |
| s2_ref05 | 0.9302 | 0.0038 | 1.023 |
| s2_ref06 | 0.9681 | 0.0028 | 1.023 |
| s2_ref07 | 0.9348 | 0.0027 | 0.935 |
| s2_ref08 | 0.9322 | 0.0009 | 0.943 |
| **s2_ref09（失败保留）** | **0.3283** | **0.1743** | **2.935** |

有效输出比例 1.000（无效输出保留在分母）。

### 4.2 S2 合成关键帧（4×8 = 32 例，有解析真值）

| 片段 | IoU 均值 | IoU 中位 | 中心误差均值 | 面积比中位 | IoU 最小 | IoU 最大 |
|---|---|---|---|---|---|---|
| syn1_translate_x | 0.487 | 0.520 | 0.0422 | 0.925 | 0.280 | 0.624 |
| syn2_translate_xy | 0.380 | 0.336 | 0.0438 | 0.909 | 0.222 | 0.626 |
| syn3_scale_up | 0.494 | 0.562 | 0.0492 | 1.019 | **0.055** | 0.746 |
| syn4_translate_scale | 0.474 | 0.501 | 0.0400 | 0.940 | **0.067** | 0.867 |
| **合计 32 例** | **0.459** | 0.496 | 0.0438 | 0.959 | 0.055 | 0.867 |

有效输出比例 1.000。

### 4.3 S1 跟踪（4 例，主指标 NOT_COMPUTABLE）

| 片段 | 协议完整 | 键数 | distinct 框 | =anchor | 整段复制 anchor | 初始化槽 IoU |
|---|---|---|---|---|---|---|
| s1_syn1_translate_x | 是 | 32 | 1 | 32/32 | **是** | 0.997 |
| s1_syn2_translate_xy | **否**（越界框） | 32 | 32 | 1/32 | 否 | 0.995 |
| s1_syn3_scale_up | 是 | 32 | 32 | 1/32 | 否 | 0.990 |
| s1_syn4_translate_scale | 是 | 32 | 1 | 32/32 | **是** | 0.998 |

### 4.4 S0 基线（解析，无模型）

即「GT 首帧框恒定」。在 8 个关键帧点上的均值：syn1 0.126、syn2 0.086、
syn3 0.241、syn4 0.145（见 §0 Q3 表）。

### 4.5 回画（可肉眼核查）

- `outputs/overlays/s2_public_refcoco.png` —— 10 张公开图：绿=真值、红=预测，标注 IoU
- `outputs/overlays/s2_synthetic_keyframes.png` —— 4 条合成片段 × 8 关键帧：绿=真值、红=预测
- `outputs/overlays/s1_tracking.png` —— 4 条合成片段 × 8 秒：绿=真值、红=跟踪预测、蓝=anchor

---

## 5. 耗时、峰值显存、磁盘与预算

| 项 | 值 |
|---|---|
| `r3s2`（42 例空间定位） | charged **90.9 s**，exit 0，42/42 成功，模型加载 5.02 s |
| `r3s1`（4 例跟踪） | charged **181.8 s**，exit 5（1 例越界失败），模型加载 5.08 s |
| **本轮 GPU 合计** | **272.7 s = 4.55 min**（上限 2700 s ✓） |
| 单例生成耗时 | 空间定位均值 **1.78 s**；跟踪均值 **34.69 s** |
| 峰值显存 | r3s2 **8811 MiB**；r3s1 **9148 MiB** |
| 项目累计 | 33 条记录，charged **36545.5 s = 10.1515 h / 24 h**，**剩余 13.8485 h** |
| round3 目录 | 15,810,560 B ≈ 15.1 MiB |
| work root 增量 | 15,855,616 B = **0.0148 GiB**（上限 3 GiB ✓） |
| 项目 80 GiB 上限 | work root 37.31 GiB < 80 GiB ✓ |
| 文件系统剩余 | 143.45 GiB（≥80 GiB ✓） |
| 结束状态 | GPU 空闲、无 `active_gpu_job.json`、无残留进程 |

---

## 6. 复现入口

```bash
ssh aic-inspur-home
R3=/home/inspur/aic_video_work/orarl_round3
PY=/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python

# ---- CPU：审计纠错 ----
$PY $R3/scripts/time_token_audit.py          # 解码最终 input_ids，提取真实时间 token
$PY $R3/scripts/recount_bc_copy.py           # B/C anchor 复制重统计
$PY $R3/scripts/select_refcoco.py            # 冻结 + 下载 10 张公开 RefCOCO 图片
$PY $R3/scripts/gen_synthetic.py             # 生成 4 条已知几何真值的合成视频
$PY $R3/scripts/build_r3_cases.py            # 冻结 S0/S1/S2 案例清单与关键帧

# ---- GPU：经预算闸门 ----
bash $R3/scripts/run_r3_gpu.sh               # 顺序跑 r3s2(42 例) 与 r3s1(4 例)

# ---- CPU：指标与回画 ----
cd $R3/scripts && $PY make_overlays_r3.py
$PY $R3/scripts/analyze_r3.py                # IoU/中心误差/面积比/同点位对照
$PY $R3/scripts/account_r3.py
```

注意：`--run-id` 在账本中必须唯一；重跑请换名（如 `r3s2b`）。
`orarl_verify.py` 为 round2 版本的**只读副本**（sha256 与 round2 相同
`0eeb252bf40ec465dc63772f024af4a9a354f8a40157664c1b648b04a29562c7`）。

---

## 7. 哪些结论有证据支持 / 哪些不能主张

**有证据支持**
1. 最终输入含 16 个 `<X.X seconds>` 时间字面量（实测解码 `input_ids`）——**round2 的相反结论被推翻**。
2. 名义 `index/fps` 与容器 PTS 在 round1 片段上最大差 132.7 ms，**不能把前者叫真实 PTS**。
3. 公开 RefCOCO 10 张：IoU 中位 0.931、9/10 ≥ 0.5、有效输出 10/10（**有真值**）。
4. 同点位对照下 S2 > S0 且 S2 > S1，四条片段一致，幅度 +0.25 ~ +0.36。
5. 受控合成条件下 **S1（跟踪）不优于 S0（固定首帧框）**。
6. B/C 复制统计：B 整段复制 5/7、部分 2/7；C 整段复制 3/7、部分 4/7。
7. `s1_syn2_translate_xy` 的越界框被正确判失败并使作业返回非零退出码。

**只能算「流程可运行」/不能主张**
1. 合成目标为纯色矩形，**不能**据此声称真实视频跟踪或定位可用。
2. S1 绝对 IoU **NOT_COMPUTABLE**（键↔时间无法可靠建立）；只有跨映射不变的定性结论可用。
3. 10 张图片是 RefCOCO val 前 10 个不同图片，**非随机抽样**，不代表全量精度。
4. **没有**任何真实视频真值；round2 的真实片段结论仍为 `NOT_COMPUTABLE`。

**明确不可作出**
- 不得与 43.4800 或 57 分比较或换算。
- 不得声称跟踪可用、不得声称模型胜出。
- 不得把目标框当作 AIC 最优裁剪框；本轮**未生成任何裁剪候选**。

---

## 附录 A：产物清单（`/home/inspur/aic_video_work/orarl_round3`）

| 路径 | 内容 |
|---|---|
| `REPORT.md` / `ERRATA.md` | 本报告 / 6 处更正（追加，不覆盖旧报告） |
| `scripts/` | `time_token_audit.py`、`recount_bc_copy.py`、`select_refcoco.py`、`gen_synthetic.py`、`build_r3_cases.py`、`run_r3_gpu.sh`、`make_overlays_r3.py`、`analyze_r3.py`、`account_r3.py`、`probe_public_data.sh`、`list_refcoco_repos.py`、`fetch_refcoco.py`、`orarl_verify.py`（round2 只读副本） |
| `evidence/` | `time_token_audit.json`、`bc_copy_recount.json`、`refcoco_frozen.json`、`synthetic_manifest.json`、`s0_baseline.json`、`r3_metrics.json`、`s1_detail.json`、`r3_accounting.json` |
| `cases/` | `cases_s1.jsonl`（4）、`cases_s2.jsonl`（42） |
| `data/` | `refcoco_val.jsonl` + 10 张 COCO 图；`gt_syn{1..4}_*.json`（逐帧真值） |
| `clips/` | 4 条合成视频（ffv1/mkv） |
| `outputs/r3s2`、`outputs/r3s1` | `run_status.json`、`summary.json`、`raw/*.raw.txt`（原始输出） |
| `outputs/overlays/` | `s2_public_refcoco.png`、`s2_synthetic_keyframes.png`、`s1_tracking.png` |
| `frames/kf/` | 32 张合成关键帧 PNG（冻结的 S2 输入） |

## 附录 B：本轮未触碰的边界

- round1 / round2 目录只读；两份 REPORT.md 哈希未变。
- 未训练、未跑全量测试推理、未提交比赛、未升级驱动、未安装新的大型推理栈、未下载其他大模型。
- **未使用比赛测试集**（`/home/inspur/aic_video_data/test` 从未访问）；
  **未向任何第三方模型 API 发送视频、图片或标签**（全程本地推理）。
- 未使用身份未确认的 987 条弱标签作为真值；未由执行模型画框后称其为人工真值。
- 所有 GPU 作业均经 `improvement_round1/budget_run.py` 串行化并计入原 24 h 预算。
- 未生成裁剪候选；未自行启动下一轮。
