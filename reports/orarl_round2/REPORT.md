# orarl_round2 — 验证入口修正、跟踪协议核对与小规模受控对照

- 目录：`/home/inspur/aic_video_work/orarl_round2`（新代码/输出全部在此，未覆盖 round1）
- 本地副本：`G:\ai\AIC视频\reports\orarl_round2`
- 时间：2026-09-16（UTC 00:08 起；GPU 作业 00:2x – 00:4x 完成）
- 复用：round1 的模型（`orarl_round1/model/Video-ORA-4B`）与独立环境（`orarl_round1/env/orarl_hf`），只读使用 round1 证据
- **本轮不训练、不升级驱动、不装 vLLM/FlashAttention、不下载其他大模型、不跑全量测试集、不提交比赛、不使用比赛测试集。**
- 本轮不比较 AIC 官方分数，不宣称提升到 57 分。

---

## 0. 直接回答最终报告要求回答的四个问题

### Q1. 上一轮的静止框是否与初始化或时间映射有关？证据能支持到什么程度？

**主要是"初始化/协议"层面的问题，但不是"缺少首帧框导致静止"这一个方向的因果关系。时间映射有缺陷但不足以解释静止框。证据强度如下。**

**(a) 时间映射确实有缺陷，且已被量化 —— 但它解释不了静止框。**

- 上一轮片段实测 **32.200 s / 962 帧**（`evidence/tracking_analysis.json` 的 `sampling`，及 `no_gpu_tests/known_time_mapping.json`）。
- 用已知时间视频（32.000 s，每帧用黑白位块编码"真实秒"）实测作者 canonical 采样：**槽位 N 落在第 N−1 个秒格，32/32 正确**；换成 32.200 s 片段则 **2/32 槽（第 31、32 槽）落入错误秒格**，间隔 1.0333 s 而非 1.000 s。
- 结论：时基偏差真实存在，但只影响末尾 2 个槽，**不可能让全部 32 槽退化成同一个框**。
- 补充证据：模型最终输入里**根本没有任何时间信息**（`evidence/final_input_time_info.json`）——processor 只输出 `input_ids / attention_mask / mm_token_type_ids / pixel_values_videos / video_grid_thw`，**没有任何 timestamp 张量**。时间语义完全依赖提示词那句"per second, ONLY up to 32 seconds"。所以时基错位不会以"时间戳矛盾"的形式暴露，只会让键 N 与真实秒 N 错位。

**(b) 协议层面：上一轮的输入本身就不符合作者协议（缺首帧框），这一点被本轮直接证实。**

- 作者协议要求把首帧框写成**提示词里的整数坐标字面量**（`eval_tracking_vllm.py:343-347` 给出措辞 `Given the bounding box [537,403,768,703] of the target object`）。上一轮**只给了自然语言描述、没有框**。
- 本轮做了 A/B/C 对照（A = 复现上一轮"仅描述"；B = 作者协议 + agent-reviewed 框；C = 作者协议 + 模型自产框），**在同一个片段上**：
  | 条件 | 输入 | distinct 框数 | 与 anchor 完全相同的占比 |
  |---|---|---|---|
  | A（上一轮做法） | 仅描述 | 3 / 32 | 无 anchor |
  | B（作者协议） | 描述 + agent-reviewed 框 | **1 / 32** | **1.00** |
  | C（作者协议） | 描述 + 模型自产框 | 2 / 32 | 0.031（IoU 0.989） |
- **A 复现出上一轮"3 个不同框"的结果，说明该现象可复现。** 但 B/C（补齐了协议要求的框）**比 A 更静止**，B 甚至逐字复制了提示词里的框。
- 所以：**"上一轮静止框"不能归因于"缺少首帧框"**（补齐框后更静止）；准确表述是：**该模型在这类输入下的默认行为就是输出恒定框，而作者协议（把框写进提示词）反而触发了逐字复制。**

**(c) 证据能支持到的边界。**
- 支持：时基偏差量化为 2/32 槽；协议差异（缺框）确凿；A/B/C 三条件下的静止程度排序可复现；模型输入无时间戳这一事实。
- **不支持**：任何"哪个框是对的"的判断。本轮全部 7 个片段都**没有可信真值**，因此 `quality` 一律 `NOT_COMPUTABLE`，不能计算准确率、不能宣称模型胜出。
- 不支持把 A 条件下出现的"移动的小框"（见 Q2）称为"正确跟踪"——它只是"有变化"，变化本身不是正确性。

### Q2. 自动初始化相对诊断初始化有哪些可观察差异？

对比 **B（agent-reviewed 诊断上限）** 与 **C（模型空间定位自动产生）**，在 7 个片段 × 32 秒上的可观察差异：

| 维度 | B（agent-reviewed 框） | C（模型自产框） |
|---|---|---|
| 与自身 anchor 完全一致的占比 | clip1 1.00、sel06 1.00、sel07 1.00、sel08 1.00、sel12 1.00、sel02 0.062、sel04 0.031 | clip1 0.031、sel02 0.75、sel06 1.00、sel07 1.00、sel12 1.00、sel08 0.469、sel04 0.031 |
| distinct 框数 | 1,1,1,1,1,3,32 | 2,3,1,1,1,2,2 |
| **协议完整性** | **sel04_B 失败**（框越界：`[0,850,0,1600]`、`[0,1600,0,2350]`） | **7/7 全部协议完整** |
| 框的几何特征 | 多数 = 提示词里那个框本身 | 多数 = 模型空间定位给的大框（更宽、常到 y=997） |

**可观察差异的实质：**
1. **两者的静止程度几乎一样**——B 有 5/7、C 有 5/7 是"逐字复制 anchor"。**自动初始化并没有让输出更有跟踪性，只是换成了另一个（通常更大更松的）恒定框。**
2. **C 更"安全"**：C 的 7 个案例全部协议完整；B 出现 1 例越界退化。原因是模型自产框更保守（常贴着 y=997、x 覆盖更宽），而 agent-reviewed 框更紧，模型在"改写"这个紧框时越界。
3. **anchor 的松紧会被继承**：C 的框普遍比 B 大（例：sel06 B=`[220,0,660,700]` vs C=`[264,0,853,997]`），C 的输出也相应更大。
4. 两者都**没有表现出跟随**：跨切镜后仍输出 anchor（sel08_B 在 Monument Valley 镜头上仍画原框）。

### Q3. 单镜头跟踪与切镜压力测试分别表现如何？

**单镜头（S1/S2，5 个片段：sel04 / sel12 / sel06 / sel07 / sel02 的单镜头段）**

- **协议完整率**：B 条件 4/5、C 条件 5/5。
- **B/C（有 anchor）**：4 个片段（sel06/sel07/sel12 及 clip1）输出**逐字等于 anchor 的恒定框**；sel02_B 轻微漂移。
- **A（仅描述）**：出现两种形态——
  - **小范围移动框**：sel06_A 从 `[525,622,748,733]`（手/刷子附近）移到 `[189,150,333,369]`（脸部区域），32 个框互不相同、27→31 次变化。视觉核查（`outputs/overlays/abc_sel06.png`）显示该框在**头部/手部区域游走**，但**没有稳定锁定单一物体**。
  - **大范围移动框**：sel04_A 为全高框、随人物水平平移（`[534,0,814,997]` → `[465,0,745,997]` → `[545,0,825,997]`），视觉上大致跟着人物走。
- **判定**：单镜头下模型**能产出格式合法、可解析的框**；但"框在动"不等于"跟踪正确"。**无真值 ⇒ NOT_COMPUTABLE。**

**切镜压力测试（S3，3 个片段：clip1 / sel02 / sel08）**

- **协议无法表达"目标消失"**（`protocol_audit.md` §5）：答案 schema 只有 `boxes`，缺帧记 0 分，全文无 absent/null 分支。
- 实测表现：
  - **sel08_B**：切镜到 Monument Valley 后，模型仍然输出 anchor 原框，画在**完全无关的风景**上（`abc_sel08.png` 第 2 行 sec=17/25/29）。这是典型的"目标已离开但仍在输出框"。
  - **sel08_A**：只返回 **15/32 个键**（缺 16..32）→ 被判定 `output_incomplete`。这是**唯一一个"模型停止输出"的行为**，但它同时意味着协议不完整。
  - **clip1_B/C**：约 22 s 处切镜后仍输出恒定框。
- **判定**：切镜后失败**不能**解释为标准跟踪基准不达标——**作者协议本身不支持目标消失**，模型没有合法方式表达"缺席"。这是**能力边界**，不是本轮新增的问题，本轮也**未擅自添加检测器/分割器/跟踪系统**。

### Q4. 是否值得由总控安排下一轮空间裁剪对照？

**建议：值得，但前提是先解决"评估"而不是"裁剪"。**

支持开展的证据：
1. 空间定位在 7/7 片段上**协议完整、可解析、可核查**（`outputs/r2sg`），说明空间分支是可用且稳定的。
2. 跟踪分支在作者协议下**退化为复制 anchor**，因此**跟踪输出不能作为裁剪框来源**；若要做空间裁剪，用空间定位框（而非跟踪框）更合理。
3. AIC 任务真正需要的是"主体在哪里 + 如何裁剪"，本轮证明**空间定位可用**、**跟踪不可依赖**——这正是安排裁剪对照的充分理由。

不建议现在就启动的理由（需要总控先决策）：
1. **没有可信真值**，任何"裁剪对照"都无法给出可信指标；需要先建立小而独立的诊断标注（见下）。
2. 若要引入跟踪，必须先明确"目标消失/切镜"如何处理——作者协议不支持，需总控决定是否允许在协议之外自建缺席表达。
3. 本轮只用了 7 个片段、每片段 3 个条件，样本量不足以支撑收益判断。

**仅给建议，未自行启动任何下一轮实验。**

---

## 1. 完成项、未完成项与阻塞

### 1.1 完成项

| 项 | 结果 | 证据 |
|---|---|---|
| 上一轮入口的可追溯副本 | `scripts/orarl_verify.py`（新写），round1 入口保持不动 | `scripts/`，round1 目录未改 |
| D1 四态分离 | `output_parseable` / `protocol_complete` / `task_success` / `quality` | `no_gpu_tests/test_results.json` |
| D2 非零退出码 + 逐任务状态 | 任一 case 失败 → exit 5；已实测触发 | `outputs/r2tr/summary.json` exit_code=5 |
| D3 run_id 隔离 + 拒绝覆盖 | 已实测同 run_id 二次运行被拒（exit 3） | 测试 D3 组 |
| D4 严格解析 | NaN/Infinity/布尔/重复键/多答案/时序多余数字全部拒绝 | 测试 D4 组 |
| D5 键集合来自协议+样本配置 | 10 s → 1..10；32.2 s → 1..32；未声明则不算完整 | 测试 D5 组 |
| D6 测试与结果保存 | **54 项全部通过** | `no_gpu_tests/test_results.json`、`test_stdout.txt` |
| 勘误 1：三方认证措辞 | 已改为"传输/文件一致性证据"，并实测官方域名 | `evidence/erratum1_official_domain.json` |
| 勘误 2：参数量差异 | 已用配置+权重键+运行时对象同一性举证 | `evidence/erratum2_param_count.json` |
| 跟踪协议直读审计 | 带行号 `protocol_audit.md`，回答 8 项 | `protocol_audit.md` |
| 已知时间视频核查 | 32.000 s 视频上槽位↔秒格 0/32 错 | `no_gpu_tests/known_time_mapping.json` |
| 最终输入时间信息核查 | 输入**无任何时间张量** | `evidence/final_input_time_info.json` |
| 冻结样本清单 | 7 个片段（含 8 个被拒候选及理由） | `evidence/samples_frozen.json` |
| A/B/C 受控对照 | clip1 上三条件 + 6 个扩展片段 | `evidence/tracking_analysis.json` |
| 逐样本结果与回画图 | 21 个 case + 7 张 A/B/C 三联图 | `outputs/r2tr/raw/`、`outputs/overlays/abc_*.png` |
| 失败分类 | `output_incomplete` / `static_output` / `time_mapping_error` 等 | `evidence/tracking_analysis.json` |

### 1.2 未完成项 / 有意留在范围外

1. **没有可信真值，因此没有任何准确率**。全部 case 的 `quality.status = NOT_COMPUTABLE`。
2. **未下载 `OraRL-Data`**（GOT-10k 原始标注与媒体），故 `protocol_audit.md` 中凡涉及标注原文处均标注为"无法从仓库确证"。
3. **未复现作者完整评测栈**（vLLM 0.19.1 / flash-attn / fla 未安装）。
4. **未做官方 benchmark 评测**，未生成任何提交。
5. **未新增检测器/分割器/跟踪系统**（切镜能力边界按要求只记录，不擅自扩展）。
6. 扩展片段为 **6 个**（规则的 6 个候选通过），另有 8 个候选被规则拒绝并记录理由（`evidence/samples_frozen.json` 的 `rejected`）。

### 1.3 具体阻塞与偏差

| # | 事项 | 处理 |
|---|---|---|
| E1 | `huggingface.co` 在本机**不可达**：DNS 解析到 `108.160.170.52` / `2a03:2880:f134:183:face:b00c:0:25de`（无关地址段），全部请求 20 s 超时 | 权重元数据的独立交叉来源**无法取得**，已如实记录为限制。改用 `raw.githubusercontent.com`（**官方域名，实测可达**）对源码做独立校验 |
| E2 | 该 ffmpeg（5.1，无 libx264） | 已知时间视频改用无损 `ffv1/mkv`；先做编解码探测确认标签 100% 可读（`no_gpu_tests/codec_probe.json`） |
| E3 | 派生的 32 s 片段实际时长为 32.17–32.28 s（`-c copy` 落在关键帧边界） | **不强行改成 32.000 s**；改为在 case 中按实测时长推导 `expected_seconds`，并把逐槽秒格映射写入结果（D5）。时基偏差由 `time_mapping_error` 分类显式标出 |
| E4 | 源片段帧率不一（30 / 29.97 / 25 / 23.976 fps） | 逐片段记录 `decoded_at_fps`、`frames_indices`、`second_bin_per_slot` |
| E5 | 多个候选片段的 query 文本与画面不符（sel01/sel03/sel09/sel11/sel13/sel15） | 按预设规则 R4 **拒绝并记录理由**，未为了凑数而更换描述 |
| E6 | `tr_sel04_B` 输出越界框、`tr_sel08_A` 只返回 15/32 键 | 均被判定失败（`output_incomplete`），作业 exit code 5 —— 正是 D2 期望行为 |

---

## 2. 源码、模型、环境的精确版本与路径

| 项 | 值 |
|---|---|
| 源码 | `/home/inspur/aic_video_work/orarl_round1/src/OraRL` @ `e1ec91ff00f59ee0da04d285938c1f7247daa69c`（`dirty=false`） |
| 源码独立复核 | `raw.githubusercontent.com` 直取 6 个文件，与本地**逐字节一致**（`README.md`、`eval/task/eval_prompt.py`、`eval/task/tracking/eval_tracking_vllm.py`、`data/eval/datasets.jsonl`、`eval/task/qwenvl_decord_patch.py`、`docs/evaluation.md`） |
| 模型 | `/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B` @ revision `01850297d5ab2adaaf130f700ed7cec52993d956` |
| 环境 | `/home/inspur/aic_video_work/orarl_round1/env/orarl_hf`：Python 3.11.10、torch 2.10.0+cu129、transformers 5.5.4、qwen-vl-utils 0.0.14、decord 0.6.0 |
| attention | `sdpa`（作者用 flash_attention_2，偏差沿用 round1 记录） |
| 驱动 | 570.144（未改动）；`nvidia-smi` 报 CUDA 12.8，实测 cu129 运行时可用 |

---

## 3. 上一轮报告勘误（不改动原报告）

### 勘误 1 —— "三方一致"的措辞不成立

**上一轮表述**：下载器 metadata、镜像 API、本地 SHA-256 构成"三方一致"。

**更正**：这三者中，**镜像 API 与下载器记录是同一上游对象的两种视图、走同一条网络路径**，它们是**传输与文件一致性的证据，不是三个独立来源的认证**。真实取得路径为：

- 权重：`https://hf-mirror.com`（`HF_ENDPOINT`）经 `huggingface_hub.snapshot_download`
- 模型元数据 API：`https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true`
- 源码：`https://ghproxy.net/https://github.com/HVision-NKU/OraRL.git`

**本轮补充实测**：官方 `huggingface.co` 域名**不可达**（记录见 `evidence/erratum1_official_domain.json` 的 `dns` 与 `probes`），**因此模型权重的独立交叉来源确认无法完成，如实标注为限制**。
**但源码可以**：`raw.githubusercontent.com` 属官方域名且实测可达（HTTP 200），直取固定 commit 的 6 个文件与本地克隆**逐字节一致** → **源码 revision 获得了真正不同域名/不同传输路径的独立确认**。

### 勘误 2 —— 5.1750 B 与 4.5393 B 的差异已举证解释

两者都正确，差异来自**参数绑定（tie_word_embeddings）**，证据链（`evidence/erratum2_param_count.json`）：

1. **配置**：`config.json` → `tie_word_embeddings: true`，`vocab_size=248320`，`hidden_size=2560`。
2. **权重键**：checkpoint 里**同时存在**两个同形状张量
   - `lm_head.weight` `[248320, 2560]` = 635.7 M（在 shard 1）
   - `model.language_model.embed_tokens.weight` `[248320, 2560]` = 635.7 M（在 shard 2）
   → 分片求和把这块矩阵**数了两次**。
3. **加载无丢失**：`0 missing / 0 unexpected / 0 mismatched`；`sum(checkpoint keys, 724) = sum(loaded names, remove_duplicate=False) = 5,174,964,736`，**两者完全相同（差异 0）**。
4. **运行时对象同一性**：用 `named_parameters(remove_duplicate=False)` 观测到
   ```
   ptr=139813841786888 n=635699200 shape=(248320, 2560)
       model.language_model.embed_tokens.weight
       lm_head.weight
   ```
   两个名字指向**同一个 Parameter 对象**（`data_ptr` 相同）。
5. **数值闭合**：`sum(unique objects) = 4,539,265,536`（=4.5393 B）；`5,174,964,736 − 4,539,265,536 = 635,699,200 = 248320 × 2560` **精确相等**。

**结论**：4.5393 B 是唯一参数对象数，5.1750 B 是分片存储求和；差额恰为一块被绑定共享的词嵌入矩阵，**不是权重丢失**。
（说明：上一轮之所以没看出别名，是因为 `named_parameters()` 默认 `remove_duplicate=True` 已经隐藏了别名——本轮用 `remove_duplicate=False` 才观测到。）

---

## 4. 协议审计要点（详见 `protocol_audit.md`，含文件行号）

| 问题 | 结论 |
|---|---|
| 首帧框如何提供 | **提示词文本里的整数坐标字面量** `[x1,y1,x2,y2]`（`eval_tracking_vllm.py:343-347` 给出措辞 `Given the bounding box [537,403,768,703] of the target object`）；不是单独图片、不是画框图片 |
| 是否还给自然语言描述 | 仓库证据里**没有**独立描述通道，只把 `problem`/`question` 整段送模板（`:238-242`） |
| 输出键语义 | GT 键是**真实秒** 1..32，**不是采样帧序号**（`:15`、`:529-530`） |
| 首帧/采样/输出键/GT 对应 | 首帧框 = GT 第 1 秒框（`:507-520`）；`fps=1, max_frames=32` 整段均匀取帧（`:760`、`qwenvl_decord_patch.py:167-168`）；键对键比较（`:161-163`）；**代码从不校验第 N 个采样帧是否落在第 N 秒** |
| 是否要求目标始终存在 / absent/null | **不支持**；schema 只有 `boxes`，缺帧记 0，全文无缺席分支 |
| 长视频 | 默认路径整段送、32 帧摊到整段，**不对齐真实秒且无告警**；另有明确标注为**诊断**的 `--chunked_reprompt`（`:907-925`，注释 `NOT the default GOT-10k protocol`）按真实秒切窗 |
| 切镜 | **无任何处理** |
| 不足 32 秒 | 采样按 `round(duration*fps)` 少取，但提示词仍要 1..32 键 |
| canonical 参数 | `eval.sh:510-516` / `datasets.jsonl`：fps=1、max_frames=32、min=4096、max=786432、total=8388608、max_new_tokens=8192；**与脚本 argparse 默认（fps=2、max_frames=64…）不同，canonical 才是协议** |

**时间映射核查（保存并比对四类信息）** —— 见 `evidence/final_input_time_info.json`：

| 阶段 | 内容 |
|---|---|
| 真实解码时间戳 | 由 `frames_indices / decoded_at_fps` 得到，单调递增，已保存 |
| 采样帧索引 | 32 个索引已保存（如已知时间视频 `[0,31,62,…,959]`） |
| 传入处理器的元数据 | `{fps, total_num_frames, frames_indices, video_backend=decord}` |
| **最终输入中的时间信息** | **没有**。processor 输出仅 `input_ids / attention_mask / mm_token_type_ids / pixel_values_videos / video_grid_thw`；`video_grid_thw=[[16,12,20]]`（时间格 16 × temporal_patch_size 2 = 32 帧）——只有"顺序与帧数"，**没有秒** |

**因此**：不能因为提示词写了"秒"就把第 N 个均匀采样帧直接解释为第 N 秒；只有在时长≈32.000 s 时才近似成立（已知时间视频实测 0/32 错），否则需按逐槽秒格显式记录（本轮已记录）。

---

## 5. 验证入口修正与测试

入口：`scripts/orarl_verify.py`（round1 入口未改动，保持可追溯）。

**四态语义**（写入每次运行的 `run_status.json`）：

- `output_parseable`：模型文本能按任务 schema 解码
- `protocol_complete`：可解析 **且** 协议要求的字段齐全、数值在范围内、无重复键、无多答案歧义
- `task_success` = 前两者成立且无执行异常
- `quality`：**除非声明可信真值，否则恒为 `NOT_COMPUTABLE`**（并给出原因）

**测试结果**：`no_gpu_tests/test_results.json` → **54 passed, 0 failed**（`test_stdout.txt` 为原始输出）。覆盖：

| 组 | 例数 | 关键断言 |
|---|---|---|
| D1 四态 | 8 | 缺键时 `output_parseable=True` 但 `protocol_complete=False`、`task_success=False` |
| D4 严格解析 | 10+7 | NaN / Infinity / -Infinity / 布尔 / 字符串 / 重复键 / 双 `<answer>` / null / 非整数秒键 / 时序三数字 / 多区间 / 尾随文字 全部拒绝；干净跨度与小数仍通过 |
| D5 键集合 | 8 | 10 s→1..10；32.2 s→1..32；未声明 `expected_seconds` 时不得判为完整 |
| D3 run_id | 7 | 二次同 run_id 被拒（exit 3）；路径穿越 run_id 被拒（exit 2） |
| D2 退出码 | 13 | 1 例失败→exit 5；全通过→exit 0；单例异常不中断整个作业但整体失败；逐 case 状态表打印并落盘 |

---

## 6. 冻结样本清单

规则在**任何模型输出之前**写定（`evidence/samples_frozen.json` 内含完整规则与判定依据）：源池 = `/home/inspur/aic_video_data/videos`（只读非测试）；**测试集 `/home/inspur/aic_video_data/test` 从不使用**；片段一律 `-ss 0 -t 32 -c copy`；分层只用**模型输出之前可得的信息**（query 文本 + 4 帧目视带）；目标 = query 中最显著主体，其首帧框由执行 Agent 在 norm1000 网格上读出并**渲染回看确认**（`frames/grid/anchor_boxes_check.png`）。

| sample | 层 | 源 group | 时长 | 目标 | anchor 框 (norm1000) |
|---|---|---|---|---|---|
| clip1 | S3 切镜/离开 | wk2CeU_DcBo | 32.200 | the man in the white sleeveless shirt | [420,15,1000,1000] |
| sel04 | S1 可见+位移 | lwNho_1tKrc | 32.266 | the man in the blue jacket | [520,50,820,800] |
| sel12 | S1 可见+位移 | gcrsfhqTmmk | 32.166 | the man talking | [140,170,900,1000] |
| sel06 | S2 尺度/遮挡 | iH1-Z6eB2cY | 32.200 | the blonde woman holding the makeup brush | [220,0,660,700] |
| sel07 | S2 尺度/遮挡 | JlWjckrziyw | 32.199 | the woman reading the book | [220,0,590,700] |
| sel02 | S3 切镜/离开 | ioWAoEVYaP0 | 32.283 | the man in the dark jacket with glasses | [420,210,690,790] |
| sel08 | S3 切镜/离开 | QHFy-nWNJYk | 32.241 | the woman in the red top | [40,100,470,950] |

- **anchor 来源一律标记 `agent-reviewed`**：由执行模型目视确定，是**初始化先验，不是人工真值**。
- **被拒候选 8 个**，理由已记录（例：sel01 query 说"戴眼镜的女人"而 t=0 是男人；sel03 的 t=0 画面里没有人）。**未为凑数更换描述或挑样本。**
- 三个条件的问题措辞：A = 仅描述；B/C = `Given the bounding box [x1,y1,x2,y2] of the target object, please track this object throughout the video.`（前半句取自作者注释中的字面措辞；**完整原句不在仓库中，已标注**）。
- 无公开可信首帧标注可用，故未使用；**987 条弱标签未作为真值。**

---

## 7. 逐样本结果

完整数据：`evidence/tracking_analysis.json`、`outputs/r2tr/run_status.json`、`outputs/r2tr/raw/*.raw.txt`（**原始输出，未清洗**）、`outputs/overlays/abc_*.png`（每样本 A/B/C 三联回画图）。

运行：空间定位 7/7 成功（exit 0）；跟踪 **19/21 成功、2 失败**（exit 5 —— 符合 D2 设计）。

| case | 层 | ok | proto | 键数 | distinct | 变化次数 | =anchor | IoU(anchor) | 失败分类 |
|---|---|---|---|---|---|---|---|---|---|
| tr_clip1_A | S3 | T | T | 32 | 3 | 3 | — | — | time_mapping_error |
| tr_clip1_B | S3 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_clip1_C | S3 | T | T | 32 | 2 | 1 | 0.031 | 0.989 | time_mapping_error |
| tr_sel02_A | S3 | T | T | 33 | 2 | 1 | — | — | time_mapping_error |
| tr_sel02_B | S3 | T | T | 32 | 3 | 2 | 0.062 | 0.554 | time_mapping_error |
| tr_sel02_C | S3 | T | T | 32 | 3 | 3 | 0.750 | 0.904 | time_mapping_error |
| tr_sel04_A | S1 | T | T | 33 | 33 | 32 | — | — | time_mapping_error |
| **tr_sel04_B** | S1 | **F** | **F** | 32 | 32 | 31 | 0.031 | 0.052 | **output_incomplete**（框越界 `[0,850,0,1600]`、`[0,1600,0,2350]`）, time_mapping_error |
| tr_sel04_C | S1 | T | T | 32 | 2 | 1 | 0.031 | 0.551 | time_mapping_error |
| tr_sel06_A | S2 | T | T | 32 | 32 | 31 | — | — | time_mapping_error |
| tr_sel06_B | S2 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_sel06_C | S2 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_sel07_A | S2 | T | T | 32 | 32 | 27 | — | — | time_mapping_error |
| tr_sel07_B | S2 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_sel07_C | S2 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| **tr_sel08_A** | S3 | **F** | **F** | **15** | 1 | 0 | — | — | **output_incomplete**（缺 16..32）, static_output, time_mapping_error |
| tr_sel08_B | S3 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_sel08_C | S3 | T | T | 32 | 2 | 1 | 0.469 | 0.489 | time_mapping_error |
| tr_sel12_A | S1 | T | T | 32 | 1 | 0 | — | — | static_output, time_mapping_error |
| tr_sel12_B | S1 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |
| tr_sel12_C | S1 | T | T | 32 | **1** | 0 | **1.00** | 1.000 | static_output, time_mapping_error |

**必须强调的两点：**
1. `distinct` / `变化次数` **只是描述性统计，不是质量指标**；本轮没有任何案例具备可信真值，`quality` 全部 `NOT_COMPUTABLE`。
2. `time_mapping_error` 在全部 case 上出现，是因为所有派生片段时长 32.17–32.28 s（≠32.000 s），末尾 1–2 个槽落入下一年秒格——这是**已知且已量化**的偏差，不是新缺陷。

---

## 8. 实际耗时、峰值显存、磁盘与预算

| 项 | 值 |
|---|---|
| `r2sg`（7 例空间定位） | charged **30.3 s**，exit 0 |
| `r2tr`（21 例跟踪 A/B/C） | charged **757.1 s**，exit 5（2 例失败），采样峰值显存 **11070 MiB** |
| **本轮 GPU 合计** | **787.4 s = 13.12 min**（上限 2700 s = 45 min ✓） |
| 单例生成耗时 | 30.96 – 42.68 s |
| 项目累计 | 31 条记录，charged **36272.8 s = 10.0758 h / 24 h**，**剩余 13.9242 h** |
| round2 目录占用 | 63,995,904 B = **61.0 MiB** |
| work root 增量 | 64,032,768 B = **0.0596 GiB**（上限 3 GiB ✓） |
| 项目 80 GiB 上限 | work root 37.30 GiB < 80 GiB ✓ |
| 文件系统剩余 | 143.51 GiB（≥80 GiB ✓） |
| 结束状态 | GPU 空闲、无 `active_gpu_job.json`、无残留进程 |

---

## 9. 复现入口（一条命令）

```bash
ssh aic-inspur-home
# 条件 C 的 anchor 由空间定位作业产生，故先跑 sg，再跑 tracking
bash /home/inspur/aic_video_work/orarl_round2/scripts/run_gpu_round2.sh \
     r2sg /home/inspur/aic_video_work/orarl_round2/cases/cases_sg.jsonl 600

# 用 sg 结果回填条件 C 的 anchor 框
/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python \
  /home/inspur/aic_video_work/orarl_round2/scripts/freeze_cases.py \
  --from-sg /home/inspur/aic_video_work/orarl_round2/outputs/r2sg

bash /home/inspur/aic_video_work/orarl_round2/scripts/run_gpu_round2.sh \
     r2tr /home/inspur/aic_video_work/orarl_round2/cases/cases_tracking.jsonl 2100
```

- `--run-id` 在账本中必须唯一；重跑请换名（如 `r2sg2`），否则 `budget_run.py` 与 `orarl_verify.py` 都会拒绝。
- 不占 GPU 的检查：`python3 scripts/test_orarl_verify.py`、`python3 scripts/known_time_test.py`、
  `python3 scripts/verify_official_sha256.py`、`python3 scripts/erratum1_official_domain.py`、
  `python3 scripts/orarl_verify.py --cases ... --run-id X --dry-run`。

---

## 10. 哪些结论有证据支持，哪些只能算"流程可运行"

**有证据支持**
1. 入口六项缺陷已修复并有 54 项测试通过。
2. 时基偏差已量化：32.000 s 视频 0/32 错；32.2 s 片段 2/32 槽错。
3. 模型最终输入**不含任何时间信息**（processor 输出键已列出）。
4. 作者协议把首帧框写成**提示词文本坐标**，且键语义是**真实秒**（带行号）。
5. 协议**不支持** absent/null，切镜无处理（全文无相关分支）。
6. 5.1750 B vs 4.5393 B 由**参数绑定**解释，含运行时 `data_ptr` 同一性证据。
7. 源码 revision 经 `raw.githubusercontent.com` 官方域名独立复核（6/6 逐字节一致）。
8. **A/B/C 对照**：B/C（有 anchor）在 5/7 片段逐字复制 anchor；A（无 anchor）在 clip1 复现上一轮的 3 个不同框。
9. 两例协议失败被正确捕获并使作业返回非零退出码。

**只能算"流程可运行"、不能主张正确性**
1. 条件 A 下出现的移动框（sel04_A、sel06_A）——**"框在动"不是"跟踪正确"**；无真值 ⇒ 无法判定。
2. 空间定位 7/7 成功且目视合理，但**没有人工真值**，只能说输出可解释、物理自洽。
3. 任何"B 比 C 好/差"的质量判断——只能描述几何与协议完整性差异。

**明确不可作出**
- 不得把本轮任何数字与 43.4800 或 57 分比较或换算。
- 不得声称模型胜出、不得声称跟踪可用。
- 不得把切镜后的失败当作标准跟踪基准不达标（协议不支持目标消失）。

---

## 附录 A：产物清单（`/home/inspur/aic_video_work/orarl_round2`）

| 路径 | 内容 |
|---|---|
| `REPORT.md` | 本报告 |
| `protocol_audit.md` | 带文件行号的作者跟踪协议审计 |
| `scripts/` | `orarl_verify.py`（修正后入口）、`test_orarl_verify.py`、`known_time_test.py`、`input_time_info.py`、`erratum1_official_domain.py`、`erratum2_param_count.py`、`select_samples.py`、`select_samples_b.py`、`verify_boxes.py`、`freeze_cases.py`、`make_overlays_round2.py`、`analyze_round2.py`、`account_round2.py`、`run_gpu_round2.sh`、`poll_round2.sh`、`codec_probe.py`、`anchor_sheet.py`、`make_grid_frame.py` |
| `cases/` | `cases_sg.jsonl`（7）、`cases_tracking.jsonl`（21，含三种条件） |
| `evidence/` | `samples_frozen.json`（冻结清单 + 8 个拒选及理由）、`tracking_analysis.json`、`final_input_time_info.json`、`erratum1_official_domain.json`、`erratum2_param_count.json`、`resource_accounting.json`、`overlay_manifest_r2.json`、`selection_candidates*.json` |
| `no_gpu_tests/` | `test_results.json`、`test_stdout.txt`、`known_time_mapping.json`、`codec_probe.json` |
| `outputs/r2sg`、`outputs/r2tr` | `run_status.json`、`summary.json`、`raw/*.raw.txt`（原始输出） |
| `outputs/overlays/` | `abc_<sample>.png` 每样本 A/B/C × 8 秒回画图；`tracking_sec_*.png` |
| `frames/grid/` | `anchor_boxes_check.png`（anchor 框回看确认）、`clip1_t*_grid.png` |
| `clips/` | `known_time_32s_30fps.mkv`（已知时间验证视频）、6 个扩展片段 |

## 附录 B：本轮未触碰的边界

- 未升级驱动、未修改全局 Python 环境、未改动 SSH/网络配置、未影响其他 GPU 任务。
- 未覆盖 round1 任何文件；原始数据、旧模型、旧 adapter、既有提交包与实验日志全部保留。
- 所有 GPU 作业均经 `improvement_round1/budget_run.py` 串行化并计入原 24 h 预算。
- 未使用 `/home/inspur/aic_video_data/test`（比赛测试集）；未把任何比赛视频/帧/标签发送给第三方 API。
- 未新增检测器、分割器或跟踪系统；未训练；未生成提交。
- 987 条身份未确认的弱标签**未作为真值**。
