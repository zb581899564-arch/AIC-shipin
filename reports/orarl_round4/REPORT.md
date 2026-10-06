# orarl_round4 — 真实非测试视频上的空间裁剪四臂对照

- 远程目录：`/home/inspur/aic_video_work/orarl_round4`
- 本地副本：`G:\ai\AIC视频\reports\orarl_round4`
- 复用：OraRL 模型与环境（`orarl_round1`）、当前 Qwen3-VL baseline 与环境（`models/Qwen3-VL-4B-Instruct` +
  `env/qwen3vl_isolated_20260910`）、预算工具 `improvement_round1/budget_run.py`
- round1/round2/round3、旧模型、adapter、提交包、原始数据**全部只读**；三份旧报告哈希未变
  （`30295caf…` / `048bf1e6…` / `06e0c483…`）
- 交付：`REPORT.md`、`ROUND3_REVIEW.md`、映射报告与排除清单、冻结样本清单、四臂原始输出、
  逐帧/逐组/分层指标、bootstrap 结果、回画接触图、资源账本与复现入口
- 本轮**不训练、不访问比赛测试集、不生成提交、不上传系统**
- 禁止项全部遵守：**未把任何视频/帧/标签发给第三方 API**；未安装新大模型；未改驱动；
  **未使用跟踪输出作为裁剪框**；未按结果更换样本；弱标签全程标记为 `WEAK_PROXY`，未称为真值

---

## 0. 六个必答问题

### Q1. 30 个来源组的媒体映射是否足够支持弱代理诊断？

**不够：只能冻结出 10 个来源组（不是 30 个），且只填满了高运动层。**

映射门禁结果（`evidence/mapping_report.json`，987 行全部处理）：

| 分类 | 数量 | 说明 |
|---|---|---|
| **usable（可用）** | **820** | 唯一精确匹配 + 可读 + 时间在范围内 + 内在一致 |
| missing | 75 | `videos/` 下**没有任何文件 stem 精确等于** `clip.source_vid` |
| time_uncertain | 92 | 连 2 组可用 `(frame, time)` 对都没有，clip-local fps 无法唯一恢复 |
| ambiguous | 0 | 无「一个 source_vid 对应多个文件」的情况 |
| vfr_excluded | 0 | 987 行的 `r_frame_rate` 与 `avg_frame_rate` 全部一致 |
| out_of_range_or_inconsistent | 0 | 标签时间均在源文件范围内，且 `source_start_sec == start_sec + clip.start_sec` 全部成立 |

时间转换（`evidence/mapping_report.json` 的 `time_convention`，已用 4 个 `start_sec>0` 的行逐条验证）：

```
clip_local_time  = clip_local_frame / clip_fps
source_time      = clip_local_time + clip.start_sec
source_frame     = round(source_time * source_fps)
```
- `clip_fps` 不直接存储，由 `crop_keyframes` 的 `(frame, time_sec)` 对**稳健中位数拟合**恢复
  （snap 到 23.976/24/25/29.97/30），要求所有点残差 ≤1.5 帧；`crop_keyframes` 为空时回退到
  `segments[].{start,end}_frame/_sec`。得到 30.0(401)/25.0(173)/24.0(108)/29.97(101)/23.976(35) 等。
- `crop_keyframes[].time_sec` 是 **clip-local**；`clip.start_sec`/`clip.end_sec` 与
  `segments[].source_*_sec` 是**源文件时间**；三者在报告与逐帧清单中分列保存，未混用。

**分层（按 brief 固定的 `free_axis_travel` 阈值）**

| 层 | 候选数 | 选中 |
|---|---|---|
| `≤ 0.05` | **0** | **0** |
| `0.05 – 0.25` | **0** | **0** |
| `≥ 0.25` | 459 | **10** |

**987 行的 `free_axis_travel` 全部落在 0.4375–0.7630**，因此低层与中层**根本不存在候选**。
按 brief「不足时记录实际数量，不从其他层补齐」，**低/中层记为 0，未从高层回填**。

**冻结结果**（`evidence/frozen_set.json`，冻结时间早于任何模型输出）：

| 项 | 值 |
|---|---|
| 来源组 | **10**（上限 30） |
| 评测帧 | **40**（上限 120） |
| 每组评测时刻 | 4（全部来自落在 `segments` 内的 `crop_keyframes`） |
| 来源视频唯一性 | 10 组 = **10 个不同 YouTube 视频**（`source_group` 只等于窗口名，同一视频的不同窗口会被去重） |
| `quality.status` | 10/10 `accepted` |
| 空间覆盖 | 10/10 `timeline_coverage == trajectory_coverage == 1.0` |
| 目标比例 | 10/10 `[9.0, 16.0]`（竖屏） |
| 弱代理框来源 | `cropRois` @ 最近 clip 帧（`roi_frame_delta` 全为 0） |

额外条件筛选中被排除的 361 条：`no_cropRois` 243、`lt3_in_segment_moments` 113、
`coverage_incomplete` 5。

**结论**：映射**本身可用**（820/987 可用、0 歧义、0 VFR、0 越界），
但**诊断集规模远小于设计目标**（10/30 组、40/120 帧），且**没有任何低/中运动样本**。
因此本轮只能回答「在这 10 个高运动来源组上，四臂相对如何」，
**不能**回答「在不同运动强度下的分层差异」。

### Q2. P2、P3 相对当前 P1 是否通过门槛？

**都没有通过。两条路线均未通过任何一项质量门槛。**

`WEAK_PROXY_IoU`（40 帧，无效输出计 0 且**保留在分母**；本轮四臂有效率均为 100%，故分母未损失）：

| 臂 | 定义 | 均值 | 中位 | 最小 | 最大 | 有效率 |
|---|---|---|---|---|---|---|
| **P0** | 画面中心 + 最大合法裁剪宽度 | 0.6993 | 0.8083 | 0.0833 | 0.9882 | 1.000 |
| **P1** | 当前 Qwen3-VL baseline `predict_focus` | **0.7989** | **0.8520** | 0.0833 | 0.9882 | 1.000 |
| **P2** | Video-ORA-4B 直接显著主体定位 | 0.6294 | 0.6858 | 0.1046 | 0.9651 | 1.000 |
| **P3** | Qwen 主体描述 → OraRL 定位 | 0.6686 | 0.7377 | 0.0432 | 0.9882 | 1.000 |

**P1 是四臂中最好的，且优于纯中心基线 P0（+0.100）。**

**配对 bootstrap（以来源组为单位，10000 次，seed 20260916）**

| 对比 | 观测均值差 | 95% 区间 | P(>0) |
|---|---|---|---|
| P2 − P1 | **−0.1695** | **[−0.3137, −0.0406]** | 0.004 |
| P3 − P1 | **−0.1304** | **[−0.2640, −0.0189]** | 0.007 |

两个区间**都完全落在 0 以下** → P2、P3 **显著劣于** P1。

**门槛逐项判定**（`evidence/r4_metrics.json` 的 `gate`）

| 门槛 | P2 | P3 |
|---|---|---|
| 有效输出率 100% | ✅ 1.000 | ✅ 1.000 |
| `WEAK_PROXY_IoU` 均值相对 P1 提高 ≥0.03 | ❌ −0.1695 | ❌ −0.1304 |
| 中位数不下降 | ❌ −0.1662 | ❌ −0.1143 |
| ≥60% 来源组胜过 P1 | ❌ **3/10 = 0.30** | ❌ **3/10 = 0.30** |
| 高运动层不明显退化 | ❌ 0.6294 vs 0.7989 | ❌ 0.6686 vs 0.7989 |
| 二阶抖动 ≤ P1 的 1.25 倍 | ❌ **1.55×** | ❌ **1.96×** |
| **总判定** | **不通过** | **不通过** |

补充：**P3 优于 P2**（均值 +0.0392、中位 +0.0519）——加上 Qwen 的主体描述确实让 OraRL 好一些，
但**仍远低于 P1**，不足以改变判定。

按 brief「如果 P2、P3 均不通过，停止 OraRL 空间接入路线」：
**建议停止把 OraRL 空间定位接入 AIC 裁剪。** 本轮**未**为通过门槛调整样本、提示词或阈值。

### Q3. 提升或退化集中在哪类运动样本？

**无法按运动分层回答——只有高运动层存在样本（低/中层为 0）。**
10 个来源组的 `free_axis_travel` 全在 0.5781–0.7630，层内没有对比度。

在**唯一可得的层内**逐组看（`evidence/r4_metrics.json` 的 `per_group`）：

| 来源组 | P0 | P1 | P2 | P3 | P2−P1 | P3−P1 |
|---|---|---|---|---|---|---|
| B39Cz-4_Z5M | 0.9882 | 0.8935 | 0.5328 | 0.8360 | −0.361 | −0.058 |
| nuZ_0pN8F-U | 0.5169 | 0.8273 | 0.7829 | 0.8116 | −0.044 | −0.016 |
| Lv5OXEW54m4 | 0.7875 | 0.9079 | 0.4893 | 0.3150 | −0.419 | −0.593 |
| Ovwki2mGOS8 | 0.1615 | 0.6446 | 0.6755 | 0.6579 | **+0.031** | **+0.013** |
| bJZ-FTeG7D8 | 0.7533 | 0.7562 | 0.1416 | 0.6554 | −0.615 | −0.101 |
| moANeGDU7lQ | 0.8272 | 0.7685 | 0.8005 | 0.8202 | **+0.032** | **+0.052** |
| 2QTwpuAdBb0 | 0.4372 | 0.7861 | 0.7529 | 0.7275 | −0.033 | −0.059 |
| gPHzl9NTZFE | 0.7694 | 0.7679 | 0.5069 | 0.3721 | −0.261 | −0.396 |
| 8XvAeVheeHg | 0.7913 | 0.6966 | 0.7918 | 0.7579 | **+0.095** | **+0.061** |
| 7L0MVxLFDL4 | 0.9606 | 0.9406 | 0.8201 | 0.7320 | −0.121 | −0.209 |

- P2/P3 各只在 **3/10** 组上胜过 P1（Ovwki2mGOS8、moANeGDU7lQ、8XvAeVheeHg）。
- 退化最厉害的是 **bJZ-FTeG7D8**（P2 −0.615）与 **Lv5OXEW54m4**（P3 −0.593）：
  这两组的画面是演播室/新闻画面，弱代理框稳定居中，而 OraRL 把框推到了别处。
- **共同规律（描述性）**：弱代理框几乎居中（见 Q5），P1 的预测也接近居中，
  所以凡是 OraRL 把中心推离弱标签中心较多的组，退化就大；OraRL 偶尔与弱标签中心碰巧一致的组
  （8XvAeVheeHg、moANeGDU7lQ）才小额胜出。
- **这不是"某类运动上更好"的证据**，因为样本只覆盖一个运动层，且每组只有 4 帧。

### Q4. P3 的主体描述失败率和额外耗时是多少？

**主体描述本身没有失败，但它没有把 OraRL 拉到 P1 的水平。**

| 项 | 值 |
|---|---|
| P3 第一步（Qwen 输出 `{"target": ...}`）成功率 | **40/40 = 1.000** |
| 严格解析失败率（空 target / 多 target / 不可解析 / 含数字） | **0.000** |
| P3 端到端（描述 + OraRL 定位）有效率 | **40/40 = 1.000** |
| 额外模型调用 | **+80 次**（40 次描述 + 40 次 OraRL 定位；P1 只需 40 次） |
| 额外耗时（仅描述步） | **0.40 s/帧** |
| arm B 总生成耗时 | 134.2 s（P2+P3b 共 80 次调用，均值约 1.68 s/次） |
| arm A 总生成耗时 | 37.8 s（P1+P3a 共 80 次调用） |

target 示例：`a couple walking past a Louis Vuitton store`、`bearded man speaking into microphone`、
`man in red cap receiving vaccine`、`person in shiny blue jacket`、`motorcycle`。
**描述质量看起来合理**，但把描述交给 OraRL 后，定位中心的偏移方向与弱代理并不一致。

→ **P3 的代价是 2 倍模型调用，换来的是 −0.13 的 `WEAK_PROXY_IoU`。**
（这不否定 P3 作为「可部署两阶段路线」在**接口上**成立：两阶段全部有效、无静默改写。）

### Q5. 弱标签是否支持动态裁剪宽度？

**不支持。弱标签几乎全部使用最大合法宽度，因此本轮没有增加动态尺度实验。**

只读统计（`evidence/crop_scale_stats.json`，577 条可用且带 `cropRois` 的行；
最大合法宽度由**冻结入口** `compute_crop_size`（sha256 `a5222447…`）计算）：

| 统计 | 值 |
|---|---|
| `cropRois` 宽度 ÷ 最大合法宽度：中位 | **1.006** |
| 最小 / 最大 | 1.006 / 1.006 |
| **恰好等于最大合法宽度的比例** | **1.000（577/577）** |
| 在最大合法宽度 2% 以内的比例 | 1.000 |
| 987 条标签的 `targetRatioWH` | **全部 `[9.0, 16.0]`** |

即：**弱标签的裁剪宽度是常量**（= 最大合法宽度），唯一变化的自由度是**位置**。
按 brief「如果弱代理几乎全部是最大宽度，本轮不要增加动态尺度实验」——
**本轮未做任何动态尺度实验**，四臂全部使用与 P1 相同的最大合法宽度。

作为补充（同一文件）：`cropRois` 的 **x 位移**（按合法 x 范围归一）
中位 **0.0956**、均值 0.1432；**36.6% 的组 x 位移 ≤0.05**、79.2% ≤0.25。
→ 弱代理**本身也很少移动**。这有两层含义，均需上报总控：

1. `clip.free_axis_travel`（0.44–0.76）**并不等于弱代理裁剪框自身的位移**（中位 0.096），
   两者测的不是同一件事；
2. 由于参考框几乎固定居中，本轮对照**主要衡量「预测中心离弱代理中心的远近」**，
   **不衡量跟踪或主体定位能力**。这与 round3「弱标签不能作为跟踪真值」的判断一致。

### Q6. 是否值得总控批准小规模比赛测试候选？只给建议，不自行执行。

**建议：不批准基于 OraRL 空间接入的候选；如要出候选，应沿用当前 P1 路线。**

理由（全部来自本轮数字）：

1. **门槛全灭**：P2、P3 在 6 项门槛中只过了「有效输出率 100%」一项；
   均值差为负且 95% 区间完全在 0 以下（P2 −0.17、P3 −0.13）。
2. **连纯中心基线都没超过**：OraRL 两臂（0.629 / 0.669）**低于** P0 中心基线（0.699），
   而 P1（0.799）高于 P0。这说明接入 OraRL 会**主动损害**当前位置质量。
3. **抖动更差**：P2 二阶抖动是 P1 的 1.55×、P3 的 1.96×，超过 1.25× 上限。
4. **代价更高**：P3 需要 2 倍模型调用（+80 次/40 帧），换来的却是负收益。

但**必须同时上报本轮的强限定**，以免过度解读：

- 诊断集只有 **10 个来源组 / 40 帧**，且**只有高运动层**，样本量小、层内无对比度；
- 参考标签是 **`WEAK_PROXY`**（Seed 弱空间标签），**不是**官方或人工真值；
- 弱代理框**几乎固定居中**（宽度恒为最大合法宽度、x 位移中位 0.096），
  因此本轮的判别力**有限**——它足以说明「OraRL 两臂在这批样本上没有更好」，
  **不足以**说明「OraRL 在任何场景下都不可能更好」；
- 因此「停止 OraRL 空间接入」是**基于本轮证据的合理建议**，
  但若总控认为值得，可以在**补齐低/中运动层 + 更可信参考**后重做一次判别力更强的对照。

**本轮未生成任何裁剪候选、未打包、未上传、未访问比赛测试集。**

---

## 1. 完成项、未完成项与阻塞

### 1.1 完成项

| 项 | 结果 | 证据 |
|---|---|---|
| `ROUND3_REVIEW.md` | 4 项更正（标注来源措辞、不可称泛化、S1/S2 仅为敏感性、仍成立的三条） | `ROUND3_REVIEW.md` |
| 映射门禁 | 987 行全处理：820 可用 / 75 缺失 / 92 时间不可确定 / 0 歧义 / 0 VFR / 0 越界 | `evidence/mapping_report.json`、`mapping_rows.jsonl` |
| 时间转换公式与分列 | clip-local / source / offset 三套字段分列保存 | 同上 `time_convention` |
| 接触图抽查 | 10 组接触图 + 2 张合并图，**agent-reviewed** | `evidence/contact_review.json`、`outputs/contact/` |
| 冻结清单 | 10 组 / 40 帧，冻结早于推理 | `evidence/frozen_set.json`、`frozen_frames.jsonl` |
| 四臂原始输出 | P0/P1/P2/P3 全部原始输出落盘 | `outputs/arms/*.jsonl` |
| 逐帧/逐组/分层指标 | 含无效输出保留在分母 | `evidence/r4_metrics.json` |
| bootstrap | 以来源组为单位的配对 bootstrap，10000 次 | 同上 `bootstrap` |
| 回画接触图 | 四臂各一张，弱代理框(青)+该臂裁剪框(红) | `outputs/overlays/arm_P*_overlay.png` |
| 尺度假设只读统计 | 宽度比、位移、目标比例分布 | `evidence/crop_scale_stats.json` |
| 资源账本 | GPU/磁盘/耗时/显存 | `evidence/r4_accounting.json` |

### 1.2 未完成项 / 范围外

1. **未冻结到 30 组 / 120 帧**：只有 10 组 / 40 帧，因为低/中运动层无候选（未回填）。
2. **无分层对比**：只有一个运动层。
3. **未做动态尺度实验**：弱标签宽度恒为最大合法宽度，按 brief 不做。
4. **未做公开图片评测**：round3 已做，且 `ROUND3_REVIEW.md` 更正 2 指出其不能称为泛化成绩；
   本轮聚焦 AIC 裁剪几何，不再重复。
5. **未生成裁剪候选、未打包、未上传。**

### 1.3 阻塞与偏差

| # | 事项 | 处理 |
|---|---|---|
| G1 | 低/中运动层**无候选**（`free_axis_travel` 全域 0.4375–0.7630） | 记为 0，**未从高层回填**；诊断集因此只有 10 组 |
| G2 | 92 行连 2 组可用 `(frame, time)` 对都没有 | 判为 `time_uncertain` 并排除；clip_fps 由 `crop_keyframes` 稳健拟合（577 行）+ `segments` 回退（243 行）恢复 |
| G3 | `crop_keyframes[].time_sec` 有浮点舍入，逐对比例投票不可靠 | 改用中位比 + snap 到广播帧率 + 残差 ≤1.5 帧的判据 |
| G4 | 首次 arm B **80/80 失败**：把 PIL 直接传给 processor，qwen3_5 走了 video/temporal-patch 路径，报 `shape '[1, 1, 2, 3, 9, 2, 16, 16, 2, 16]' is invalid` | 改为走 round3 已验证的 `process_vision_info` 路径；**失败输出保存在 `outputs/arms_failed_v1/`**；重跑成功 80/80 |
| G5 | 指标脚本曾把 `grows.append(row)` 写在逐帧循环之外，导致逐组统计只用最后 1 帧 | 已修并重跑；修正前后的**总体**数值不变，逐组与 bootstrap 已按 4 帧重算 |
| G6 | P1 的二阶抖动为 0 时 1.25× 比值无定义 | 门槛改为「P1 抖动为 0 时要求候选抖动也为 0」；本轮 P1 抖动非 0，比值正常计算 |
| G7 | 两个模型环境互斥（transformers 4.57.1 vs 5.5.4） | 拆成两个 GPU 作业（arm A / arm B），各自经 `budget_run.py` |

---

## 2. 映射报告摘要

- 标签：`/home/inspur/aic_video_data/labels/train.jsonl`，987 行，
  sha256 `7177731fb7af99e8581c0ec071d116cdb9e6652a6b2b355cd8100364a004c629`
- 源视频池：`/home/inspur/aic_video_data/videos`，索引 11576 个 mp4 / 11576 个不同 stem
- 匹配规则：**文件 stem 与 `clip.source_vid` 精确相等**，无模糊匹配；0 → missing，>1 → ambiguous
- `provenance.video_sha256` 与源文件不同**未记为失败**（它可能对应加工短片），
  同时也**未被当作媒体身份已确认**；本轮未对未冻结的行计算源文件哈希
- `cropRois` 全程标记 **`WEAK_PROXY`**，仅用于评测，**从未进入任何模型提示词**

**接触图抽查（`agent-reviewed`）**：10 组各 4 帧，画面与其 `teacher_signals.summary`
在肉眼层面**未发现明显矛盾**（例：g00 = 娱乐新闻采访场景；g02 = TV NEWS 疫苗报道；
g04 = 演播室节目；g09 = 食品/蟹类画面）。
**这是 agent-reviewed 一致性抽查，不是独立真值确认**；summary 为空或含糊时该检查无法判定，
且它**不能**证明 clip→source 偏移在每一帧都正确。

---

## 3. 四臂设定（与 brief 一致）

所有臂使用**完全相同的冻结帧**与**当前官方输出几何规则**：

- 目标比例：从样本读取（10/10 为 `[9, 16]`）
- 最大合法宽度：冻结入口的 `compute_crop_size(W, H, tw, th)`（sha256 `a5222447…`）
- 裁剪框：`[x, y, w]`，高度由官方规则推导 `h = w * th / tw`
- 位置：`center_to_box(cx, cy, W, H, cw, h_float)`

| 臂 | 方法 | 是否可用（可部署） |
|---|---|---|
| **P0** | 画面中心 + 最大合法宽度（基线） | 是（无模型） |
| **P1** | `Qwen3VL.predict_focus`（**原样**提示词 + **原样** `parse_focus_norm` + **原样** `center_to_box`） | 是 |
| **P2** | Video-ORA-4B spatial grounding，固定表达式 `the most important visual subject or region to preserve in a vertical highlight crop`（竖屏时用 vertical），bbox 中心 → 同一宽度裁剪 | 是 |
| **P3** | ① Qwen3-VL 输出 `{"target": "..."}`（要求单一主体、不输出坐标）→ ② 把 target 原样作为 OraRL 的 referring expression → bbox 中心 → 同一宽度裁剪 | 是（两阶段，推理时不使用标签/summary/人工描述） |

**未悄悄修改任何提示词、解析器或后处理**：P1 完全复用冻结文件的函数；
P2/P3 使用作者 `eval_prompt.py` 的空间定位提示词原文；
OraRL 输出经严格解析（单 `<answer>`、JSON、4 个数、norm1000 范围内、正向宽度），
失败即判无效且**计 0 分**，不做静默修补。

---

## 4. 指标与判定

指标全部命名 `WEAK_PROXY_*`：

| 指标 | 定义 | 位置 |
|---|---|---|
| `WEAK_PROXY_IoU` | 预测裁剪框 与 `cropRois` 弱代理框 的 IoU | 逐帧 + 逐组均值 |
| `WEAK_PROXY_hcenter_abs_err` / `_vcenter_abs_err` | 中心绝对误差 ÷ 画面宽/高 | 逐帧 |
| 逐组胜负 | 组均值 > P1 组均值 | `per_group.wins_vs_P1_*` |
| 无效输出比例 | 无效**计 0 且保留在分母** | `valid_rate_by_arm` |
| 路径总变差 / 二阶抖动 | 组内 4 个时刻的裁剪中心 x 轨迹 | `path_total_variation_*`、`second_order_jitter_*` |
| 运行时间 / 模型调用数 / 峰值显存 | 见 `cost` 与 `evidence/r4_accounting.json` | — |

中心位移（描述性，`overall.centre_motion_by_arm`）：

| 臂 | 路径总变差均值 | 二阶抖动均值 | 组内总变差为 0 的组数 |
|---|---|---|---|
| P0 | 0.000 | 0.000 | 10/10 |
| P1 | 0.138 | 0.069 | 0/10 |
| P2 | 0.228 | 0.107 | 0/10 |
| P3 | 0.245 | 0.135 | 0/10 |

即 OraRL 两臂**动得更多**，但动的方向与弱代理不一致，因此 IoU 更低、抖动更大。

---

## 5. 回画接触图

- `outputs/overlays/arm_P0_overlay.png` … `arm_P3_overlay.png`：每臂一张，
  **青色 = 弱代理参考框**，**红色 = 该臂裁剪框**，每格标注该帧的 `WEAK_PROXY_IoU`。
- `outputs/contact/contact_g*.png` 与 `contact_sheet_1/2.png`：映射抽查用接触图。
- 目视核查可见：弱代理框在多数组内几乎停在画面中心同一位置，
  而 P2/P3 的红框明显摆向别处（如 `7L0MVxLFDL4` 的 P3 中心偏左，IoU 仅 0.006）。

---

## 6. 资源账本

| 项 | 值 |
|---|---|
| `r4armA`（P1 + P3a，Qwen3-VL 环境） | charged **60.6 s**，exit 0，峰值 9072 MiB |
| `r4armB`（首次，**失败**） | charged **30.3 s**，exit 0 但输出全无效（见 G4），已保留 |
| `r4armB2`（重跑 P2 + P3b） | charged **151.5 s**，exit 0，峰值 11082 MiB |
| **本轮 GPU 合计** | **242.4 s = 4.04 min**（上限 3600 s ✓） |
| 生成耗时 | arm A 37.8 s（80 次调用）；arm B 134.2 s（80 次调用） |
| 模型加载 | arm A 7.89 s；arm B 4.9 s |
| 显存峰值 | arm A 8534 MiB；arm B 8788 MiB（外层采样 11082 MiB） |
| 项目累计 | 36 条记录，charged **36787.9 s = 10.2189 h / 24 h**，剩余 **13.7811 h** |
| round4 目录 | 21,512,192 B ≈ 20.5 MiB |
| work root 增量 | 21,598,208 B = **0.0201 GiB**（上限 3 GiB ✓） |
| 项目 80 GiB 上限 | work root 37.33 GiB < 80 GiB ✓ |
| 文件系统剩余 | 143.41 GiB（≥80 GiB ✓） |
| 结束状态 | GPU 空闲、无 `active_gpu_job.json`、无残留进程 |

---

## 7. 复现入口

```bash
ssh aic-inspur-home
R4=/home/inspur/aic_video_work/orarl_round4
W=/home/inspur/aic_video_work

# ---- CPU：映射门禁 + 冻结 + 接触图 + 只读尺度统计 ----
python3 $R4/scripts/map_labels.py          # 输出 evidence/mapping_report.json + mapping_rows.jsonl
python3 $R4/scripts/freeze_r4.py           # 输出 evidence/frozen_set.json + frozen_frames.jsonl
python3 $R4/scripts/contact_r4.py          # 映射抽查接触图（agent-reviewed）
python3 $R4/scripts/crop_scale_stats.py    # 只读裁剪尺度统计

# ---- GPU：四臂（两个环境，各自经预算闸门）----
bash $R4/scripts/run_r4_arms.sh            # r4armA(Qwen3-VL) 然后 r4armB2(OraRL)

# ---- CPU：指标 + bootstrap + 回画 + 账本 ----
$W/orarl_round1/env/orarl_hf/bin/python $R4/scripts/metrics_r4.py
$W/orarl_round1/env/orarl_hf/bin/python $R4/scripts/overlay_r4.py
```

注意：`--run-id` 在账本中必须唯一；重跑请换名（如 `r4armA2`）。
`arms_orarl.py` 必须通过 `process_vision_info` 传图（见 G4），否则 80/80 失败。

---

## 8. 哪些结论有证据支持 / 不能主张

**有证据支持**
1. 映射门禁：820/987 可用、75 缺失、92 时间不可确定、0 歧义、0 VFR、0 越界；
   时间转换公式在三套字段上分列并逐条验证。
2. 低/中运动层**无候选**，冻结集只有 10 组 40 帧（未回填）。
3. `cropRois` 宽度**恒为最大合法宽度**（577/577），987 条标签目标比例全为 9:16。
4. 四臂 `WEAK_PROXY_IoU`：P1(0.7989) > P0(0.6993) > P3(0.6686) > P2(0.6294)。
5. P2−P1、P3−P1 的 95% bootstrap 区间**完全在 0 以下**。
6. P2、P3 **均未通过**门槛（各只过 1/6 项）；抖动为 P1 的 1.55×/1.96×。
7. P3 主体描述成功率 40/40，额外 80 次调用、0.40 s/帧。

**只能算「流程可运行」/不能主张**
1. 参考是 **`WEAK_PROXY`**（Seed 弱空间标签），**不是**官方真值、人工真值或 AIC 准确率。
2. 样本仅 **10 组 / 40 帧**、单一运动层；不能外推到「高运动样本普遍如此」。
3. 弱代理几乎固定居中 → 本轮主要衡量「预测中心离弱代理中心的远近」，**不衡量跟踪能力**。
4. `free_axis_travel`（0.44–0.76）与弱代理框自身位移（中位 0.096）**不是同一量**。

**明确不可作出**
- 不得与 43.4800 或 57 分比较或换算；本轮**无官方分数**。
- 不得声称 OraRL 提升、不得声称任何裁剪方案在比赛中更好。
- 不得把弱标签称为官方真值、人工真值或 AIC 准确率。
- 不得把本轮的「停止 OraRL 空间接入」当成对 OraRL 全模型的否定——
  本轮只检验了**空间定位接入裁剪**这一条路径。

---

## 附录 A：产物清单

| 路径 | 内容 |
|---|---|
| `REPORT.md` / `ROUND3_REVIEW.md` | 本报告 / round3 追加更正 |
| `scripts/` | `map_labels.py`、`freeze_r4.py`、`contact_r4.py`、`crop_scale_stats.py`、`arms_qwen.py`、`arms_orarl.py`、`run_r4_arms.sh`、`metrics_r4.py`、`overlay_r4.py`、`probe_convention.py`、`diag_fps.py` |
| `evidence/` | `mapping_report.json`、`mapping_rows.jsonl`、`frozen_set.json`、`frozen_frames.jsonl`、`contact_review.json`、`crop_scale_stats.json`、`r4_metrics.json`、`r4_accounting.json` |
| `outputs/arms/` | `p1_qwen.jsonl`、`p2_orarl.jsonl`、`p3a_target.jsonl`、`p3b_orarl.jsonl`、`arm_a_run.json`、`arm_b_run.json` |
| `outputs/arms_failed_v1/` | **首次失败的 arm B 输出（保留）** |
| `outputs/overlays/` | `arm_P0..P3_overlay.png` |
| `outputs/contact/` | 10 组接触图 + 2 张合并图 |
| `frames/` | 冻结的 40 张源帧 |

## 附录 B：本轮未触碰的边界

- round1/round2/round3、旧模型、adapter、提交包、原始数据全部只读；三份旧报告哈希未变。
- 未训练、未访问比赛测试集、未生成正式提交、未上传系统。
- 未把任何视频、帧或标签发送给第三方 API（全程本地推理）。
- 未安装新大模型、未修改驱动。
- **未使用跟踪输出作为裁剪框**（P2/P3 用的是 OraRL **spatial grounding**，不是 tracking）。
- 未按实验结果更换样本；冻结发生在任何模型输出之前。
- 所有 GPU 作业均经 `improvement_round1/budget_run.py` 排队并计入原 24 h 总预算。
- 完成后停止，未自动启动下一轮。
