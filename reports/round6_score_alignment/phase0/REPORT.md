# 第六轮 P0 证据审计报告

- run_id：`round6_p0_20260917T0155Z`
- 执行时间：2026-09-17 01:55Z–02:05Z（北京时间 09:55–10:05）
- 执行范围：只读审计、CPU 小型统计、文档交付
- 未执行：GPU、训练、模型推理、权重/媒体下载、安装、上传、清理、生产代码修改、P1 内容
- 阶段状态：`P0_EXECUTED_PENDING_SUPERVISOR_ACCEPTANCE`（本报告不自行批准进入 P1）

---

## 0. 结论摘要（先读这一段）

1. **第五轮候选的包与产物哈希全部自洽，可复现。** ZIP、包内 `predictions.jsonl`、40,568 帧、174 视频、203 窗口、S2 epoch_3 adapter、空间基底、时序原始输出，本地与远端 SHA-256 全部一致；我用合成器代码独立重算预测帧集合，**174/174 视频逐帧完全一致**。
2. **43.4800 对应的提交是 `qwen3vl_lora_reader_20260912`**（prediction `A81A…`），而不是第五轮包；第五轮包的 `official_new_score` 至今为 `null`，只有用户“约一分”的口头反馈（`USER_REPORTED_APPROX`）。
3. **“收益低”有直接证据的解释只有一类：评测口径与空间链路的结构性错配，而不是某一处 bug。**
   - 第五轮的候选选择与门槛用的是**纯时序并集 F1**（秒），完全没有空间项；官方指标是“同帧时间∧空间联合 IoU”。离线涨的 14 个百分点不可能等价成官方分。
   - 第五轮**没有做任何新的空间推理**：40,568 帧里 37,325 帧直接沿用 43.48 的同帧旧框，3,243 帧（8.0%）用“最近旧框”复制补上。
   - 这 3,243 帧的复制距离中位数 **25.2 秒**、P90 **108.3 秒**、最大 **131 秒**；其中 95.7% 位于旧空间模型**预测覆盖区之外**（复制自覆盖区边缘）。
4. **空预测链路确实存在“合法空 = 解析失败”的合并，但本次提交没有触发。** 203/203 窗口解析合法、0 次 fallback、0 条空视频。这条缺口是代码层事实，**不是本轮丢分的证据**。
5. **时间帧端点约定在第五轮被改了**：43.48 用 `ceil + 半开区间`（已核对为 `range(start,end)`），第五轮合成器用 `round + 闭区间`。差别已量化：40,568 vs 40,384 帧（+184 帧，+0.46%），端点最多各偏 1 帧。方向谁对**未确认**（官网明确未写帧上界是否闭区间）。
6. **官方 evaluator 未取得（NOT_AVAILABLE）**，但官方页面已记录了部分规则与三处不确定边界；内部重写只能标 `INTERNAL_SPEC_REIMPLEMENTATION_PROPOSAL`。
7. **资源可核算**：累计 GPU 14.1564 h / 24 h，剩余 **9.8436 h**；work root 38 GiB / 80 GiB；文件系统剩余 143 GiB；GPU 空闲、无活动作业、无残留进程。
8. **尚不能归因**：官方丢分究竟主要在时间选择还是空间构图。原因是**没有任何可信的非测试空间参考**（唯一空间参考是 10 来源组/40 帧的 `WEAK_PROXY` 裁剪框，且宽度恒等于最大合法宽度）。本轮不把任一原因写成主因。

---

## 1. 任务 1：提交包、哈希与历史记录对账

### 1.1 分数链（区分官方分数 / 用户反馈 / 内部指标）

| 提交 | 包 | 官方分数 | 名次 | 依据等级 |
|---|---|---|---|---|
| baseline qwen3vl | `baseline_qwen3vl_20260910.zip` | **41.09** | 24 | 已记录（页面回读，2026-09-10） |
| multi_reader | `aic-qwen3vl-multi-20260910.zip` | **41.22** | 23 | 已记录（页面回读，2026-09-10） |
| lora_reader（= **43.4800**） | `aic-qwen3vl-lora-reader-20260912.zip` | **43.48** | 25 | 用户反馈 + 2026-09-16 登录态榜单快照（提交时间 2026-09-12 12:51:09 与包文件时间 12:50 吻合） |
| round5_s2_temporal | `aic-round5-s2-temporal-20260917.zip` | **null** | null | `submission_attempt.json`：门户在文件传输前被浏览器文件选择器拦下；用户后续只反馈“约一分” |

- 第五轮包的官方分数按提示词要求写 `null`，并注明 `USER_REPORTED_APPROX`。**本报告不写 44.4800，也不写任何推算值。**
- 远端全盘扫描（2026-09-17 02:00Z）未发现第五轮上传或新分数的任何记录，与本地 `submission_attempt.json` 一致。

### 1.2 哈希核对（本轮实测，全部 MATCH）

| 对象 | SHA-256 | 结果 |
|---|---|---|
| 第五轮 ZIP | `e5df99b8…c3584` | MATCH（本地重算） |
| ZIP 内 `predictions.jsonl` | `f8f026a6…f3ef` | MATCH（且与远端 `test_candidate/predictions.jsonl` 一致） |
| 空间基底 `qwen3vl_lora_reader_20260912/predictions.jsonl` | `a81a7118…ef471` | MATCH |
| 时序原始输出 `temporal_raw_v1.jsonl` | `3bc0fc59…9cf72` | MATCH（本地=远端） |
| S2 epoch_3 adapter | `6cb2ac3b…7a9f` | MATCH（远端 `runs/S2_WARM_epochs3_v2/epoch_3/adapter_model.safetensors`） |
| 43.48 ZIP / 41.22 ZIP / 41.09 ZIP | `60188E90…` / `6DF46D39…` / `2F8FE862…` | MATCH |
| train/dev/holdout jsonl | `e54e2178…` / `e5d2113c…` / `e2c8d0cf…` | MATCH（本地 evidence = 远端 data） |
| `supervisor_test_metadata.json` | `7f38d3f7…c428` | MATCH（只含视频ID/尺寸/帧数，无标签） |

### 1.3 独立复算（不是重跑推理，是代码级复现）

- 用 `compose_temporal_candidate_v1.py` 的规则从 `temporal_raw_v1.jsonl` 重算：**174/174 视频帧集合完全一致**，总数 40,568 帧 = 包内帧数。
- 用项目既有的格式校验器对**四个**提交包做独立校验（全部 `ok=true`、0 error、0 warning），帧数分别为：41.09 → 52,734；41.22 → 56,855；43.48 → 66,890；第五轮 → 40,568（174 行 / 174 视频）。校验器源码在远端 `/home/inspur/aic_video_work/evaluation/`，本地仓库只有一份**更旧的编译产物**（2026-09-09 22:36 的 `.pyc` vs 23:03 的源码）；两者在“小数框 / 真值帧严格性”上行为不同，本轮**以已核对哈希的源码为准**（见 §6 与 `scoring_spec.md`）。
- 第五轮候选的空间框全部通过旧校验器的 `[x,y,w]` 与“推导高度后仍在源帧内”检查（0 条 `BOX_OUT_OF_BOUNDS`）。
- **校验器是内部实现，不是官方 evaluator。**

---

## 2. 任务 2：生产调用链审计（引用文件:行号）

### 2.1 第五轮实际生产入口

`infer_temporal_test_v1.py`（推理）→ `temporal_common.py`（提示词/解析/虚拟片段）→ `compose_temporal_candidate_v1.py`（合成官方 JSONL）→ 内部校验器 → ZIP。

| 项 | 实测 | 位置 |
|---|---|---|
| 窗口 | 30 秒，**不重叠**（`start=end` 递进），最后一窗不足 0.2 s 丢弃 | `infer_temporal_test_v1.py:18,84-89` |
| 视频时长 | `duration = n_frames / fps`（整数帧数÷平均帧率） | `infer_temporal_test_v1.py:81` |
| 虚拟片段 | `sf=ceil(start*fps)`、`ef=floor(end*fps)`，均夹到 `[0,total-1]`；`ef=max(sf+1,…)` | `temporal_common.py:55-59` |
| 采样 | 片段内均匀取 64 帧（`round(linspace)`），时间戳 = `local_idx/fps`，**clip-local 且以 frame sf 为 0 点** | `temporal_common.py:60-68` |
| 提示词 | 要求“1–5 个区间”“不得重叠”“只输出 JSON”；**没有空集选项** | `temporal_common.py:26-37` |
| 解析 | 严格 JSON；`segments` 为空 → **报错**；>5 段 → **报错**；单段越界/非有限 → 整窗判无效 | `temporal_common.py:90-140` |
| 秒→帧 | `fa=round((start+a0)*fps)`、`fb=round((start+b0)*fps)`，**闭区间** `range(fa,fb+1)`，夹到 `[0,n_frames-1]`；`fb<=fa` 时补到 `fa+1` | `compose_temporal_candidate_v1.py:110-115` |
| 跨窗去重 | 用 `set` 收集帧，逐帧输出；窗口不重叠，故无重叠合并逻辑 | `compose_temporal_candidate_v1.py:90,115,120` |
| 空间框来源 | 同帧旧框；缺失则取**同视频最近的旧框**（按帧号距离，平局取小帧号），**无镜头/距离保护** | `compose_temporal_candidate_v1.py:121-127` |
| 空/非法 | `output_valid=False` 或空段 → 同一分支，回退“窗口居中 80%”；整视频为空直接报错 | `compose_temporal_candidate_v1.py:99-102,116-117` |
| 健康门 | 非法窗口比例 >5% 直接拒绝合成 | `compose_temporal_candidate_v1.py:48-50` |

### 2.2 与 43.48 链路的差异（同一官方指标下被换掉的约定）

| 维度 | 43.48（`inference_v2`） | 第五轮 | 证据 |
|---|---|---|---|
| 空预测 | 解析器区分 `valid_empty`；提示词给“Valid empty example”；状态 `valid_empty` 时输出空 `predictions` | 空 = 解析失败 = 居中 80% 回退；整视频空被拒 | `inference_v2/temporal.py:32-48,193-194,96-98`、`baseline_v2.py:345`、`accept_candidate.py:71` vs `temporal_common.py:108-109`、`compose_temporal_candidate_v1.py:99-117` |
| 秒→帧 | `ceil(start*fps-ε)`、`ceil(end*fps-ε)`、**半开区间** | `round`、**闭区间** | `inference_v2/temporal.py:231-250` vs 合成器 110-115 |
| 输出帧集合 | `range(start,end)`，已核对 174/174 | `range(fa,fb+1)`，已核对 174/174 | `accept_candidate.py:68` |
| 窗口 | `policy=multi`：整视频单窗（采样 64 帧铺满全片） | 30 秒非重叠窗，每窗 64 帧 | `baseline_v2.py:480`、`qwen_io.py:371-374` vs `infer_temporal_test_v1.py:18,84-89` |
| 解码约束 | `constrained_json=True`（lm-format-enforcer 正则，允许 0–4 段且允许空） | 不约束，靠提示词 + 严格解析 | `baseline_v2.py:483`、`temporal.py:143-160` |
| 帧数 | 66,890 帧（174 视频，平均覆盖全片 78.1%） | 40,568 帧（平均覆盖 49.1%） | 包文件实测 |

**量化后的端点差异**：同一批模型输出，旧约定选 40,384 帧，新约定选 40,568 帧，差 +184 帧（+0.456%）；逐视频差值中位 0、最大 15 帧（见 `evidence/p0_cpu_stats.json`）。
**额外发现**：合成器把“本地时间 0”当成“窗口起点”，而模型看到的“本地时间 0”其实是帧 `ceil(start*fps)`（`temporal_common.py:55`、`qwen_io.py:194` 都用 ceil）。除第一窗外的窗口存在 **<1 帧** 的系统性偏移（203 窗中 29 个非首窗受影响）。量级很小，但属于同一类约定不一致。

### 2.3 已确认缺口 vs 仅风险

**已确认缺口（代码层事实，可复现）**

- G1 合法空与解析失败合并；空预测无法表达（提示词 + 解析器 + 合成器三处）。
- G2 整视频空被合成器拒绝（`raise`），官方格式其实允许空数组（内部校验器与边界测试都接受空）。
- G3 单段越界即整窗判无效（无“丢弃坏段保留好段”路径），与“1–5 段”约束叠加后，模型一次越界就损失整窗。
- G4 训练目标里存在 **1 条 7 段样本**（train 640 行中 1 行，`n_segments=7`），而推理契约上限为 5 段 → 该目标在推理期永远无法被解析通过。
- G5 时间帧端点约定在轮次之间被改，且无共享转换函数；43.48 与第五轮各自实现。

**仅有风险（有代码依据，但没有本轮实测影响）**

- R1 `output_valid=False` 与空段共用回退分支 ⇒ 一旦出现解析失败，会把“无高光”变成“居中 80%”的强预测。本轮 0 次触发。
- R2 空间框复制无镜头边界保护；距离可达 131 秒。本轮 8.0% 帧受影响（见第 3 节）。
- R3 无跨窗合并：模型若在窗口边界切开同一段高光，输出为两段相邻区间（帧集合仍是并集，影响主要在 N_pred 与数组长度）。
- R4 合成器要求空间基底与 temporal 的 `targetRatioWH` 完全一致，否则报错（本轮一致，119×16:9 + 55×9:16）。

---

## 3. 问题 3 专项：旧框复用能不能跨镜头/远距离延用

用现有 JSONL 做纯算术审计（不解码视频）：

| 指标 | 值 |
|---|---|
| 复用帧总数 | **3,243**（占预测帧 8.0%） |
| 涉及视频 | 54/174；其中 13 个视频 >20%，3 个 >50% |
| 帧距中位 / P90 / P99 / 最大 | **755 / 3,248 / 3,898 / 3,930 帧** |
| 换算秒数：中位 / P90 / 最大 | **25.17 s / 108.27 s / 131.00 s** |
| 帧距 >30 帧（约 1 秒）的占比 | 2,768 / 3,243 = 85.4% |
| 复制框与“最近旧框”不一致 | **0**（规则被精确复现） |
| 复用帧位于**所有**旧预测区间之外 | **3,243 / 3,243 = 100%** |
| 复用帧所在空隙**开在视频首/尾**（只有一侧有锚点） | 3,105 / 3,243 = 95.7% |
| 两侧都有锚点时的两侧框 IoU | ≥0.8：123 帧；0.2–0.5：15 帧；<0.2：0 帧 |

**具体例子（vid 19，172.07 s，9:16）**：旧空间基底只覆盖帧 3960–5159（132–172 s，仅 1 段）；第五轮候选选了 13 段、2,401 帧，主要落在 1–89 s。于是该视频 1,725 帧（71.8%）的框都来自 132 s 之后那一段，最远复制距离 131 s。

**能确定到哪一步**：复制规则与距离分布已确证；复制帧全部落在旧模型覆盖区之外也已确证。
**不能确定**：这些空隙是否跨镜头切换——需要解码视频，P0 不允许；因此“跨镜头”仍是 UNKNOWN，只能说“跨越了旧模型未预测的区间，且距离可以很大”。

---

## 4. 任务 3：818 条训练样本映射的证据等级

### 4.1 数据事实（远端实测，只读）

- 987 行标签 → 映射 gate：`usable 820 / time_uncertain 92 / missing 75 / ambiguous 0 / vfr_excluded 0 / out_of_range 0`。
- 第五轮行级复核：2 行因零长段 `[0.0,0.0]` 被拒 → **818 条入库**；另有 3 行做了 <5 ms 的段尾 clamp（记在 `segment_clamp_notes`）。
- 划分：train 640 行 / 559 来源组，dev 90 行 / 80 组，holdout 88 行 / 80 组；`youtube_id` 不跨 split；三份数据集哈希与 supervisor 记录一致。
- 30 个来源组的 PTS/边界抽查：30/30 CFR（步长偏差 ≤1 µs）、30/30 流起点为 0、30/30 首尾帧不同。**只覆盖这 30 组。**
- 单条记录样例（dev 首条）：`source_probe = {width:534, height:300, avg_fps:23.976, nb_frames:3597, duration:150.025}`，`clip_start_sec=116.634`、`clip=[2.961292,6.172833]`（clip-local）、`segments_source=[119.595292,122.806833]`、`targetRatioWH=[9,16]`、`label_status=WEAK_TEACHER`、`free_axis_travel_role=metadata_only`。

### 4.2 逐项证据等级

| 字段 | 现状 | 等级 |
|---|---|---|
| 身份 | 只用“文件 stem 精确等于 `clip.source_vid`”匹配；**912/912 行的 `provenance.video_sha256` 与源文件不一致**；`trusted_identity_rows = 0`；`data_audit` 训练门 `passed=false`（理由含“正式 clip 生成/对齐清单缺失”） | **未证明**（弱身份：stem 匹配） |
| 时间偏移 | `source_time = clip_local_time + clip.start_sec`；行级验证 `source_start_sec == start_sec + clip.start_sec` 全数成立；转换后的源窗口落在源文件时长内（818/818） | **内部自洽已证明**；跨媒体正确性未证明 |
| clip fps | 不直接存储，用 `crop_keyframes` 的 `(frame,time_sec)` 中位比恢复、snap 到广播帧率、残差 ≤1.5 帧（无 2 组可用对则回退 segments 字段），否则判 `time_uncertain` 排除 | 已记录且可复现；属**恢复值**而非实测值 |
| 源 fps / CFR | 源 fps 取 ffprobe `avg_frame_rate`；820 行“0 个 rate-field mismatch”**不等于** CFR（第四轮勘误 3）；只有 30 组做了逐帧 PTS | 部分证明（30 组） |
| 尺寸 | 818/818 行有 `source_probe.width/height`（例 534×300）；注意这些“源文件”本身是 **150 秒窗口的派生文件**（文件名 `{youtube_id}_{start}_{end}.mp4`），不是原始投稿视频 | 已记录 |
| crop/resize | **训练集完全没有空间字段**（0/818 行含 crop/roi 字段）；原始 987 行标签的 `cropRois`/`crop_keyframes` 属 **clip 坐标系**，加工短片的生成参数与 clip→源 的缩放/裁剪链**未取得** | **未证明** |
| 坐标约定 | 官方 `[x,y,w]` + 推导高度（页面级）；标签侧 `cropRois` 宽度 ≈ 该派生文件内 9:16 的最大合法宽度（534×300 下 168.75 → 标签 169），x 位移中位 0.096 → 近乎恒定居中 | 只能作 `WEAK_PROXY` |
| 监督可用性 | 818 条**只能支撑时序监督**；空间监督需要回到原始标签并先解决坐标空间与媒体身份两件事 | 见第 5 节 |

**结论**：字段自洽成立，**媒体身份与坐标空间未被证明**，因此 818 条继续是 `WEAK_TEACHER`，不得升格为真值或“官方训练集”。

---

## 5. 任务 4：官方 evaluator 与规则快照

- **official evaluator：`NOT_AVAILABLE`。** 项目内（本地 `tmp_agent_c/`、`improvement/`、`reports/`；远端 `aic_video_work/`、`aic_video_data/`）未找到任何官方脚本、官方样例标签或官方规则文件快照。
- 已有的最接近“来源”的记录是 `reports/eval_source_audit.md`（远端，读取日期 **2026-09-09**）：官方页面明确 JSONL 契约、`[x,y,w]`、推导高度 `h=w*target_h/target_w`、同视频同帧空间 IoU、**重复帧按“首个有效”计数**、按视频聚合 F、并给出非法预测示例；页面称提供基础评测脚本但**页面源码里没有链接**。
- 该记录同时列出三处官方未写明的边界：**（a）非法行是整文件拒绝还是计为假阳性；（b）是否接受小数坐标；（c）帧号上界是否闭区间**。
- 项目内已有内部重写：`evaluation/schema.py`（格式/非法项）+ `evaluation/internal_metric.py`（`F=2ΣIoU/(N_pred+N_gt)`，双空=1、单空=0，重复帧首个计入 `N_pred`，按视频等权平均后 ×100）。**这两个文件的源码在远端 `/home/inspur/aic_video_work/evaluation/`，本地仓库缺失（本地只有 `tmp_agent_c/evaluation/__pycache__/*.pyc` 且比源码旧）。本轮以只读方式取回源码并逐个核对 SHA-256（`schema.py 0236f987…`、`internal_metric.py 41ec9ecf…`、`README.md 4878fc19…`、`validate_predictions.py f34003df…`、`__init__.py 3b812379…`），随后用源码而非字节码重做了边界探测。** 源码缺失本身列为缺口（同步问题）。
- 用源码实测的既有行为（`evidence/validator_boundary_probe.json`）：`frame` 必须是非 bool 整数（`FRAME_TYPE`）；`0 <= frame < n_frames`（`frame == n_frames` 报 `FRAME_OUT_OF_RANGE`）；`[x,y,w]` 必须为三元素有限数（bool/嵌套列表报 `NON_FINITE`）；`w>0`（否则 `BBOX_SIGN`）；推导高度后越出源帧报 `BOX_OUT_OF_BOUNDS`；**小数坐标在范围内被接受**；重复帧只给 `DUPLICATE_FRAME` warning 且两条都计入有效预测；空数组合法；真值侧帧号必须为整数（float/bool 均被拒）。
- 注意：`reports/data_c_review.md:28-32` 记录的“内部 GT parser 会把 `1.9`/`True` 静默截断为帧 1”这一缺陷，在**当前源码中已被修复**（`internal_metric.py:94-103` 的 `_strict_frame` 明确拒绝 bool 与 float）。该历史记录与当前源码不一致时，以源码为准，并在 P1 复核。
- 项目内另有一处第三方 evaluator 探针记录（QVHighlights 视频包 URL，`reports/supervisor_official_archive_probe.json`），与 AIC evaluator **无关**，不得替代。
- 按提示词“默认不联网更新仓库”，本轮**未联机抓取官网**；规则快照的日期/版本记录仍缺（ROADMAP §3 要求后续执行时保存读取日期与版本）。

---

## 6. 任务 5：远端只读核对（已连接，SSH OK）

| 项 | 值 |
|---|---|
| 连接 | `aic-inspur-home`（`inspur-NP5570M5`），2026-09-17T01:55Z；未改任何设置、未读私钥 |
| GPU | RTX 6000 Ada 46,068 MiB；**占用 180 MiB、利用率 0%、无计算进程** |
| 进程 | 无训练/推理进程（仅系统 python 服务） |
| 活动作业 | 无 `active_gpu_job.json` |
| 磁盘 | `/` 剩余 **143 GiB**；`aic_video_work` **38 GiB**（temporal_round5 = 575 MiB） |
| 代码一致性 | 6 个关键文件（`temporal_common.py`、`infer_temporal_test_v1.py`、`compose_temporal_candidate_v1.py`、`inference_v2/{temporal,baseline_v2,qwen_io}.py`）本地↔远端 SHA-256 **全部一致** |
| 数据集一致性 | train/dev/holdout 与 `split_manifest.json` 本地 evidence ↔ 远端 data **全部一致** |

**资源账本**（`improvement_round1/gpu_ledger.jsonl`，68 行）：本轮 charged 合计 43,762.95 s（12.1564 h），加首行带入的保守 prior 7,200 s，**累计 50,962.95 s = 14.1564 h**；24 h 预算**剩余 9.8436 h**。其中第五轮时期（2026-09-16 起）39 行、15,477.53 s = **4.2993 h**（低于该轮自设 6 h 上限）。失败/非零退出记录 13 条（含首次 CUDA 段错误探针），均留档。

---

## 7. 三个必答问题的直接回答

**Q1 线上收益低，哪些解释有直接证据？**
有直接证据的是“口径与链路结构”：① 第五轮的门槛与选择指标是**纯时序并集 F1**，没有空间项（`decision_policy_v2.json` 的 `selection.metric`、`eval_gate_v2.py:23-24`），而官方指标要求时间∧空间同帧 IoU；② 第五轮**没有新增任何空间预测**（37,325 帧沿用同帧旧框，3,243 帧复制旧框）；③ 时间帧端点约定被换（+184 帧、端点最多各偏 1 帧）；④ 窗口/上下文策略被换（整片稀疏 vs 30 秒稠密）。**不能归因**的是丢分主因究竟在时间还是空间：唯一空间参考是 10 组/40 帧的 `WEAK_PROXY`，且其宽度恒为最大合法宽度、近乎不动，判别力不足；官方逐视频分项也不可得。

**Q2 空预测链路具体哪里不兼容？合法空与解析失败是否混淆？**
是，四处合并/缺失：提示词只允许 1–5 段（`temporal_common.py:34`）；解析器把 `[]` 判为 `'segments' is empty` 错误（`:108-109`）；`output_valid` 是单一布尔（`infer_temporal_test_v1.py:119`）；合成器 `if not segs:` 把“无效”和“空”送进同一个居中 80% 回退（`compose_temporal_candidate_v1.py:99-102`），并且整视频为空直接 `raise`（`:116-117`）。43.48 链路本来区分（`valid_empty` + 显式空示例 + `accept_candidate.py:71` 的“空/失败一致性”检查），内部校验器也接受空数组。**但本轮 203/203 窗口有效、0 次回退、0 条空视频，缺陷未被触发。**

**Q3 旧框复用能否跨镜头/远距离延用？**
规则上没有任何限制：3,243 帧复用、中位距离 25.2 s、最大 131 s、85.4% 的复制距离超过 30 帧（约 1 秒，随帧率而变）、100% 落在旧模型预测区之外、95.7% 复制自覆盖区边缘。是否跨镜头本身无法在 P0 判定（需解码视频）。**已有证据能确定到“复制来源可以离得很远且位于未预测区间”，不能确定到“跨了镜头切点”。**

**Q4 标签分别能支撑什么？**
时序：818 条 clip-local 区间标签可支撑**弱时序**监督与诊断（已有第五轮实践），但只有 30 组做过 PTS/CFR 验证，媒体身份全部未证明。空间：**不能支撑任何监督**——训练集无空间字段；原始标签的裁剪框在未验证的 clip 坐标系内、宽度≈最大合法宽度、位移极小、媒体身份未证。任务画幅：标签 987 条全为 9:16 与测试集 119:16:9 + 55:9:16 的分布不匹配，竖屏空间诊断缺失。

**Q5 官方评分器是否取得？内部实现还有哪些边界无法确认？**
未取得（`NOT_AVAILABLE`）；不得用 QVHighlights/TimeLens 的 evaluator 顶替。内部重写（源码已核对哈希）可确认：公式 `2ΣIoU/(N_pred+N_gt)`、双空=1、单空=0、重复帧首个计入 `N_pred` 而重复项仍留分母、按视频等权平均 ×100、`frame` 必须为非 bool 整数且 `0<=frame<n_frames`、`[x,y,w]` 必须三元素有限数（bool 拒绝）、`w>0`、推导高度后须在源帧内、空预测合法、GT 侧帧号必须为整数。**无法确认**：帧上界是否闭区间（直接决定本次 +184 帧该不该有）、非法行是整文件拒绝还是计假阳性、小数坐标是否被官方接受、`N_gt` 是否允许为空、真值帧的构造方式。详见 `scoring_spec.md`。

**Q6 资源余额能否核算？进 P1 最少还缺什么？**
能核算：GPU 剩余 9.8436 h（P1 计划为 0 GPU）、work root 38/80 GiB、文件系统 143 GiB、无活动作业。进 P1 最少还缺：① 帧端点约定的裁决（内部先冻结一种并登记，或取得官方 evaluator）；② 一片**非测试**的独立诊断媒体来源（80 来源组，横竖各半）与标注人力/复核安排；③ 可信空间参考的替代方案（若坚持空间诊断，必须解决媒体身份与坐标空间）；④ 明确的评分为内部重写的书面豁免（否则 P1 结论只能标弱诊断）。

---

## 8. 进 P1 前的最小修正清单（按确定性/影响依据/验证成本排序，最多 5 项）

| # | 修正 | 确定性 | 影响依据 | 验证成本 |
|---|---|---|---|---|
| 1 | 冻结**唯一**“秒→帧”转换函数（含端点闭开、起点 ceil 语义），并登记它与历史约定的差异 | 高（纯代码，可离线复算） | 已量化 +184 帧、端点 ±1 帧；官方明确未写帧上界 | 低（CPU，用现有 `temporal_raw_v1.jsonl` 即可重放 203 窗） |
| 2 | 把“有效区间 / 合法空 / 解析失败”三态贯通提示词→解析器→合成器→校验器，回退规则先冻结再评测 | 高 | G1/G2 已确认；官方格式允许空数组 | 低（CPU 边界表 + 203 窗重放，预期输出不变） |
| 3 | 为新选帧建立**空间来源规则**：或重新做空间推理，或对“锚点距离/超出旧覆盖区”设阈值并登记 | 中（阈值需定） | R2 已量化：8.0% 帧、中位 25 s、最大 131 s | 中（阈值验证需 P2 的空间推理能力） |
| 4 | 落地**内部联合重评分器**（`2ΣIoU/(N_pred+N_gt)`）与边界测试表，标 `INTERNAL_SPEC_REIMPLEMENTATION_PROPOSAL` | 高（规范已在 `scoring_spec.md` 起草） | 现选择指标无空间项，无法对 A/B/C 候选做联合排序 | 中（实现 + 边界套件，CPU） |
| 5 | 建**独立诊断集**（80 来源组：40 开发/40 留出，横竖各 20；每部分争取 ≥8 条自然无高光） | 低（依赖外部素材与标注） | 现有标签横竖分布不匹配、空间不可用 | 高（素材许可、标注、≥20% 复核） |

第 1、2、4 项是纯 CPU 且确定性最高，应作为 P1 的第一批；第 3 项涉及空间，天然落在 P2；第 5 项是 P1 的主体成本。

---

## 9. 事实 / 假设 / 未知 分列

**已确认（可复现）**

- 第 1、2 节的全部哈希、计数、174/174 复现、独立格式校验结果。
- 第二至四节引用的代码行为（空/非法合并、端点约定、窗口策略、最近框复用、1–5 段约束、7 段样本）。
- 3,243 帧复用的距离分布与“全部落在旧预测区之外”。
- 远端资源与账本数字、本地↔远端代码/数据哈希一致。
- 官方 evaluator 在项目内不存在；官方页面的部分规则与三处未写明边界。

**假设（写明但未证明）**

- 第五轮候选相关的“约一分”提升来自第五轮包（用户口径），无页面证据。
- 43.48 与第五轮“同为同一 evaluator 评分”成立（提交清单与榜单时间吻合，但未见评分系统内部记录）。
- 官方页面 2026-09-09 的读取内容仍与当前版本一致（本轮未联机复核）。

**未知（必须留档，不得猜测）**

- 第五轮候选的精确官方分数与名次。
- 官方帧上界闭/开、非法行处理粒度、小数坐标接受度。
- 复用帧是否跨镜头切换。
- 官方丢分在时间与空间之间的比例（无可信空间参考、无逐视频分项）。
- 987 条标签对应的加工短片生成脚本/参数与媒体身份。
- 既有内部 evaluator 的**版本一致性**：本地 `.pyc`（2026-09-09 22:36）与远端源码（23:03）行为不同，两份中哪一份参与了历史哪次验收需要 P1 对照；本轮以源码为准。

---

## 10. 未完成项与边界遵守

- 未做：任何 GPU 作业、模型加载/推理、训练、权重或媒体下载、环境安装、上传、文件清理、生产代码修改、浏览器操作、联网抓取官方页面。
- 未做（受 P0 边界限制）：解码任何视频以确认镜头切换与真 CFR；查看测试视频内容；把任何测试帧/视频/标签送出外部。
- 受限说明：`evaluation/schema.py`、`internal_metric.py` 源码缺失，格式规则由 `.pyc` 反汇编与边界测试记录恢复，未逐行复核源码。
- 本报告与随附 JSON 不构成提分证据，也不构成进入 P1 的批准。

---

## 11. 产物清单

| 路径 | 内容 |
|---|---|
| `reports/round6_score_alignment/phase0/REPORT.md` | 本报告 |
| `reports/round6_score_alignment/phase0/evidence_index.json` | 结论 ID + 证据等级 + 文件/行号/URL + 读取时间 + 哈希 |
| `reports/round6_score_alignment/phase0/resource_reconciliation.json` | 活动作业/GPU/磁盘/预算/余额 |
| `reports/round6_score_alignment/phase0/scoring_spec.md` | 联合评分规范 + 边界测试表（`INTERNAL_SPEC_REIMPLEMENTATION_PROPOSAL`） |
| `reports/round6_score_alignment/phase0/NEXT_STAGE_BRIEF.md` | P1 范围、接口、阻塞、建议（不批准） |
| `…/phase0/evidence/p0_cpu_stats.json` | 复现/端点/复用统计原始输出 |
| `…/phase0/evidence/box_gap_continuity.json` | 复用空隙两侧框 IoU 统计 |
| `…/phase0/evidence/independent_format_validation.json` | 两个包的独立格式校验结果 |
| `…/phase0/evidence/validator_boundary_probe.json` | 既有内部校验器的边界行为实测（源码版） |
| `…/phase0/evidence/existing_internal_evaluator/` | 远端既有内部 evaluator 源码只读副本（5 个文件，哈希已核对） |
| `…/phase0/evidence/supervisor_test_metadata.json` | 既有测试索引（仅 ID/尺寸/帧数，无标签），本地副本 |
| `…/phase0/scripts/p0_audit_stats.py`、`p0_box_gap_continuity.py` | 可复现脚本 |
