# ERRATA.md — 对 orarl_round1 / orarl_round2 报告的更正

本文件**追加**，不覆盖或修改 `orarl_round1/REPORT.md`（sha256 `30295caf…`）与
`orarl_round2/REPORT.md`（sha256 `048bf1e6…`）。两者保持原样以便追溯。

所有更正均由本轮可复现证据支撑，证据文件在 `orarl_round3/evidence/` 下。

---

## ERRATUM 1 — 「最终输入没有时间信息」是**错误**的

### 原结论（round2 §0 Q1(b)、§4、REPORT 中的 `final_input_time_info.json` 结论段）

> 「模型最终输入里**根本没有时间信息**……processor 只输出 `input_ids / attention_mask /
> mm_token_type_ids / pixel_values_videos / video_grid_thw`，**没有任何 timestamp 张量**……
> 所以时间语义完全依赖提示词那句 'per second'。」

### 错在哪里

`orarl_round2/scripts/input_time_info.py` 检查的是**加工前的 `text`**（`apply_chat_template` 的输出），
并把 `explicit_time_tokens_in_prompt` 里的 `any_numeric_timestamp_list` **硬编码为 `False`**；
它随后只列出了 processor 的**输出张量键名**，**从未解码 `input_ids`**。
而时间信息恰恰是在 processor 内部、以**文本**形式插入 `input_ids` 的，不会体现为任何张量键。

### 实际机制（已安装文件，带行号）

`env/orarl_hf/lib/python3.11/site-packages/transformers/models/qwen3_vl/processing_qwen3_vl.py`
（sha256 `b51f77d783b4a88d503bf9198828d46f71e3ead3833da2631748188b159253ba`，共 271 行）：

```python
151  # if timestamps are not provided, calculate them
152  curr_timestamp = self._calculate_timestamps(
153      metadata.frames_indices,
154      metadata.fps,
155      self.video_processor.temporal_patch_size,
156  )
158  video_placeholder = ""
159  frame_seqlen = video_grid_thw[index][1:].prod() // merge_length
160  for frame_idx in range(video_grid_thw[index][0]):
161      curr_time = curr_timestamp[frame_idx]
162      video_placeholder += f"<{curr_time:.1f} seconds>"
163      video_placeholder += (
164          self.vision_start_token + "<|placeholder|>" * frame_seqlen + self.vision_end_token
165      )
```

```python
257  def _calculate_timestamps(self, indices, video_fps, merge_size=2):
262      timestamps = [idx / video_fps for idx in indices]
265      timestamps = [
266          (timestamps[i] + timestamps[i + merge_size - 1]) / 2
267          for i in range(0, len(timestamps), merge_size)
268      ]
```

即：**每个 temporal patch（2 帧）之前会被插入一个字面量 `<X.X seconds>`**，其值等于该 patch 内两帧
`index / fps` 的**平均值**。

### 实测（`evidence/time_token_audit.json`，本轮实跑处理器）

| 视频 | 最终 `input_ids` 长度 | video_pad token 数 | **真实时间字面量个数** | 前 6 个 | 末 2 个 |
|---|---|---|---|---|---|
| `known_time_32s_30fps.mkv`（32.000 s） | 1115 | 960 | **16** | `<0.5>` `<2.6>` `<4.7>` `<6.7>` `<8.8>` `<10.8>` | `<29.4>` `<31.4>` |
| round1 片段（32.200 s / 962 帧） | 2603 | 2448 | **16** | `<0.5>` `<2.6>` `<4.7>` `<6.7>` `<8.8>` `<10.9>` | `<29.4>` `<31.5>` |

`input_ids` 解码（保留特殊 token）开头实文：

```
<|im_start|>user
<0.5 seconds><|vision_start|><|video_pad|><|video_pad|>…（每个 patch 60 个 video_pad）
```

处理器算出的 16 个时间戳（round1 片段）：
`0.5167, 2.5833, 4.65, 6.7167, 8.7833, 10.85, 12.9167, 14.9833, 17.05, 19.1167, 21.1833, 23.25, 25.3167, 27.3833, 29.45, 31.5167`

**更正后的正确表述**：模型**确实**收到显式时间信息，形式是**每个 temporal patch 一个
`<X.X seconds>` 文本标签**；32 秒视频共 **16 个**标签，间距约 2.07 s（因为 2 帧合一个 patch），
且标签值是**该 patch 内两帧 `index/fps` 的均值**，因此**不是整数秒**（0.5, 2.6, 4.7 …）。

### 由此产生的补充结论（原报告未提及）

- 提示词里被要求输出的键是 1..32（每秒一个），而模型**实际看到的时间标签只有 16 个、且非整数、间距约 2.07 s**。
  两者粒度不一致，这是「键 N ↔ 真实秒 N」无法从模型输入本身推出的直接原因（见 round3 REPORT 的 S1 指标判定）。
- 标签值来自 `index/fps`，**不是容器 PTS**；见 ERRATUM 2。

---

## ERRATUM 2 — 把 `index/fps` 称作「真实解码时间戳」

### 原做法（round2 的 `sampling_observed` / `decoded_timestamps_sec`）

round2 把 `frames_indices / fps` 记为「解码时间戳 / real second」，并在多处直接当时间用。

### 更正

`frames_indices / fps` 是**名义时间（nominal）**，由采样序号与容器声明的 fps 推算；
真正的容器时间戳（PTS）必须从文件读取。本轮实测两者**并不总是相等**：

| 视频 | 名义 vs 容器 PTS 最大差 | 平均差 | 是否 1 ms 内一致 |
|---|---|---|---|
| `known_time_32s_30fps.mkv` | 0.000333 s | −0.000021 s | **是** |
| round1 片段（32.200 s） | **0.132683 s** | **+0.068099 s** | **否** |

round1 片段抽样帧实测（`real_pts_field_used = best_effort_timestamp_time`，962 帧全部取到）：

| 帧号 | 名义 `idx/30` | 容器 PTS |
|---|---|---|
| 0 | 0.0000 | **0.066016** |
| 31 | 1.0333 | **1.099349** |
| 62 | 2.0667 | **2.132682** |
| 93 | 3.1000 | **3.166016** |
| 961 | 32.0333 | **32.166016** |

该文件首帧 PTS 即为 0.066 s（非 0），且名义值与 PTS 系统性相差约 66–133 ms。

**更正后的正确表述**：
- `index/fps` 只能叫**名义时间**；
- 只有在 CFR 且首帧 PTS 为 0 的文件上，它才**恰好**等于容器 PTS（`known_time` 视频属于这种）；
- round2 的「解码时间戳」应改称「名义时间」，并用容器 PTS 另行核对。
- 同时说明：processor 插入的 `<X.X seconds>` 用的也是**名义时间**，因此对 round1 片段，
  模型看到的时间标签相对真实内容时刻偏早约 68 ms（标签还是 patch 均值，见 ERRATUM 1）。

---

## ERRATUM 3 — 「主因是缺首帧框」是**越界推断**

### 原结论（round2 §0 Q1 与 Q1(c)）

> 「主因是 **D-a 缺首帧框**」/「主因在协议/初始化层面，但方向与预期相反」。

### 更正

round2 的实验实际只支持**排除**，不支持**指认主因**：

- 条件是 A（仅描述，等价 round1 输入）/ B（作者协议 + agent 框）/ C（作者协议 + 模型框）。
- 观测：A 在 clip1 上复现 3 个不同框；B/C **更静止**。
- 由「B/C 更静止」能推出的是：**加上首帧框并不能让输出变得更有跟踪性**。
- 但**不能**由此指认「缺框」是静止的原因——因为补上框之后静止**依然存在甚至更强**。
- 同样也**不能**指认时间映射是主因（偏差仅 2/32 槽，见 round2 已量化的结果与 ERRATUM 1 的补充）。

**正确表述**：本轮与上一轮的证据**排除了**「时间映射」和「缺首帧框」这两个候选解释，
但**没有识别出真正的主因**。静止输出是模型+提示词+输入三者在这些样本上的表现，
其成因尚未定位。**不应以「主因」措辞呈现一个只完成了排除的结论。**

补充：round2 引入的「B/C 复制 anchor」本身是对的现象（ERRATUM 4 修正其计数方式），
但「复制 anchor」与「因为缺框所以静止」是两件事，不能互相论证。

---

## ERRATUM 4 — 「schema 无 absent」被写成「数据全程可见」

### 原结论（round2 的 `protocol_audit.md` §5）

> 「GT 方面，注释称 'got10k always = 32'，即每个样本都有 32 个 GT 帧 → **目标被假定全程可见**。」

### 更正

这里把**两件不同强度的事**混为一谈：

1. **评测器 schema 无法表达缺席** —— 这一条有代码证据，成立：
   答案只有 `boxes`（`eval_tracking_vllm.py:14-16`），缺帧记 0 分（`:151-164`），
   全文无 absent/null 分支。
2. **数据集里的目标是否全程可见** —— 这一条**不能**由 1 推出。
   仓库里唯一相关的是注释 `got10k always = 32`（`:22`），它说的是**每个样本的 GT 帧数恒为 32**，
   是**帧数**陈述，不是**可见性**陈述。真正的标注文件（`annotations/tracking/got10k.jsonl`）
   属于未下载的 `OraRL-Data`，本轮也无法据其判定。
   同时，GOT-10k 本身是否包含「目标不存在」的情形，本仓库与本地证据都无法回答。

**正确表述**：**作者的评测器没有表达「目标缺席」的手段**，因此在该评测口径下，
目标消失只能表现为 IoU 下降；**关于 GOT-10k 数据本身是否全程可见，本轮无证据，不作断言。**

---

## ERRATUM 5 — 「7/7 格式完整」被写成「空间定位可用」

### 原结论（round2 §0 Q4、§10）

> 「空间定位在 7/7 片段上**协议完整、可解析、可核查**，说明空间分支是**可用且稳定**的。」
> 「空间定位 7/7 成功且目视合理」→ 并据此建议开展裁剪对照。

### 更正

`protocol_complete=true` 只表示：能解析、键/字段齐全、数值在范围内、无重复键、无多答案歧义。
它**不表示**框落在正确目标上，也**不表示**框的紧致度可接受。round2 对该 7 个片段
**没有任何可信真值**（自拟 target + agent-reviewed 框），因此：

- 「7/7 协议完整」只能支持「**输出格式与坐标约定可用**」；
- **不能**支持「空间定位**正确**」或「空间定位**可用**」；
- 更**不能**作为「值得安排下一轮空间裁剪对照」的充分理由。

**本轮的处理**：round3 用**带真值**的样本重新回答这个问题——
10 张公开 RefCOCO 图片（官方标注框）+ 4 条几何真值已知的合成视频（32 个固定关键帧），
按 IoU / 中心误差 / 框面积比 计算，结果见 `orarl_round3/REPORT.md`。
只有那一组数字才允许用于判断空间分支是否值得继续投入。

---

## ERRATUM 6 — 「B/C 整段复制 anchor」的计数方式被修正

### 原措辞（round2 §0 Q1/Q2、§7）

> 「B/C（有 anchor）在 5/7 片段**逐字复制 anchor**」；
> 「B 有 5/7、C 有 5/7 是『逐字复制 anchor』」。

这句话把「有若干帧等于 anchor」与「**整段**所有帧都等于 anchor」混为一谈，
而且把 C 说成 5/7 也是错的。

### 程序化重统计（`evidence/bc_copy_recount.json`，容差 tol=1 个 norm1000 单位＝舍入级）

| 条件 | 整段全部等于 anchor | 部分等于 anchor | 完全不等 | 接近但不等 |
|---|---|---|---|---|
| **B** | **5/7**：clip1, sel12, sel06, sel07, sel08 | 2/7：sel04(1/32), sel02(2/32) | 0 | 0 |
| **C** | **3/7**：sel12, sel06, sel07 | 4/7：clip1(1/32), sel04(1/32), sel02(24/32), sel08(15/32) | 0 | 1/7：clip1（最大偏差 7.0） |

逐片段「等于 anchor 的框占比」：

- B：clip1 1.000、sel12 1.000、sel06 1.000、sel07 1.000、sel08 1.000、sel02 0.0625、sel04 0.0312
- C：sel12 1.000、sel06 1.000、sel07 1.000、sel02 0.750、sel08 0.4688、clip1 0.0312、sel04 0.0312

作为对照，条件 A（无 anchor，故用「整段恒定」衡量）：

- A 整段恒定 **2/7**：sel12、sel08（其中 sel08_A 只返回 15/32 个键）

**更正后的正确表述**：
- B：**5/7 片段整段都是 anchor 的复制**；另 2/7 只有极少数帧等于 anchor（1/32、2/32），**不构成整段复制**。
- C：**只有 3/7 片段整段复制**；其余 4/7 是部分复制（含 sel02 的 24/32、sel08 的 15/32）。
- 不得把「有一些帧复制」写成「整段复制」；也不得把 C 说成 5/7。

---

## 未更改的结论（经本轮复核仍然成立）

以下 round1/round2 结论本轮未发现错误，予以保留：

- 权重字节完整性：5 个 safetensors + tokenizer.json 对官方 LFS sha256 逐一相等；
  `5.1750 B` 与 `4.5393 B` 的差异由参数绑定（`tie_word_embeddings`）解释，
  含运行时 `data_ptr` 同一性证据（round2 ERRATUM 2 已举证，本轮复核有效）。
- **源码** revision 经 `raw.githubusercontent.com` 官方域名独立复核（round2 实测 6/6 逐字节一致）。
  （round3 复测时该域名出现超时，见 `evidence/` 记录——域名可达性本身不稳定，故该结论依据 round2 当时的成功记录。）
- `huggingface.co` 在本机不可达；模型权重**没有**独立交叉来源。
- 时基偏差量化：32.000 s 视频槽位↔秒格 0/32 错；32.200 s 片段 2/32 槽错。
- 作者协议把首帧框写成**提示词文本坐标**；输出键字面语义是**真实秒**
  （但见 ERRATUM 1：模型实际收到的是 16 个非整数 patch 均值标签，二者粒度不一致）。
- 切镜/目标消失在本评测器 schema 内**无法表达**（见 ERRATUM 4 的限定）。
- 本轮全部样本无真值时，`quality` 必须为 `NOT_COMPUTABLE`。
