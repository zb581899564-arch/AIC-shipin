# orarl_round1 — Video-ORA-4B 本机部署与最小推理验证报告

- 执行时间（UTC）：2026-09-15 15:10 起，GPU 验证 15:48–15:49 完成
- 范围：仅部署 + 最小推理验证。**本轮不训练、不生成全量测试集提交、不上传比赛系统、不声明任何比赛分数。**
- 远程目录：`/home/inspur/aic_video_work/orarl_round1`
- 本机报告副本：`G:\ai\AIC视频\reports\orarl_round1`

---

## 1. 完成项、未完成项与具体阻塞

### 1.1 完成项

| 项 | 结果 |
|---|---|
| 连接与硬件核实 | `ssh aic-inspur-home` 正常；RTX 6000 Ada，驱动 570.144，显存 46068 MiB |
| 源码固定 | `HVision-NKU/OraRL` 克隆到远程，HEAD = `e1ec91ff00f59ee0da04d285938c1f7247daa69c`，与历史记录**一致**，工作区干净 |
| 权重固定与下载 | `OraRL/Video-ORA-4B` revision `01850297d5ab2adaaf130f700ed7cec52993d956`，5 分片 + 索引 + tokenizer 全部就位 |
| 权重字节级校验 | 5 个 safetensors + tokenizer.json 的本地 SHA-256 与官方 LFS sha256 **逐一相等**（见 §3） |
| 独立环境 | `env/orarl_hf`（venv, Python 3.11.10, torch 2.10.0+cu129, transformers 5.5.4）；未改动任何旧环境 |
| GPU 框架可用性 | `cuda_available=True`，capability 8.9，matmul 通过 |
| 离线加载 | CPU 离线加载：0 missing / 0 unexpected / 0 mismatched keys，`weights_fully_consumed=True` |
| 三类最小推理 | 图片空间定位、短视频时序定位、短视频跟踪**全部产出可解析输出**（`valid=true`） |
| 结果可视化核查 | 框/时间已回画到真实帧上，可肉眼核查（见 §4.4） |
| 固定配置重跑 | `orarl_r1_replay_sg` exit 0，原始输出与首轮**逐字节一致**（见 §10.1） |
| 无效输出不被计为成功 | 26 个负例全部被判无效、3 个正例通过（见 §10.3） |
| 预算与边界遵守 | 本轮 GPU 151.6 s（上限 1800 s）；磁盘增量 17.716 GiB（上限 25 GiB） |

### 1.2 未完成项 / 未做项（有意留在范围外）

1. **未做任何精度/准确率评测。** 没有官方 AIC evaluator，且本地 987 条弱标签身份未确证（`trusted_identity=false`）。本轮所有指标均为**诊断量**，不可当作准确率或比赛分数。
2. **未复现作者完整评测栈。** 未安装 vLLM 0.19.1、flash-attn 2.8.3、flash-linear-attention 0.4.2，未使用 `orarl-eval` 跑 canonical benchmark。
3. **未复现作者训练配方**（其单卡峰值约 50.9 GB，且本轮不训练）。
4. **未下载 OraRL-Data**（作者整理后的训练/评测数据），本轮只取必要源码 + 4B 权重 + 依赖。
5. **未验证跟踪质量。** 见 §4.3 与 §7：跟踪输出格式合法但**近乎静止**（32 秒仅 3 个不同框），不能作为"跟踪能力可用"的证据。
6. **未切换 9B、未量化替换正式权重、未启动 LoRA/RL 训练。**

### 1.3 具体阻塞与偏差（需要记录的事实）

| # | 事项 | 性质 | 处理 |
|---|---|---|---|
| B1 | 训练机**无法访问 github.com 与 huggingface.co**（curl 超时，http=000） | 环境限制 | 使用公开镜像 `ghproxy.net`（源码）与 `hf-mirror.com`（权重）；镜像内容与官方 revision/SHA-256 逐一核对通过，非同名替代模型。**未修改任何网络配置。** |
| B2 | 驱动 570.144 的 `nvidia-smi` 报告 CUDA 12.8，低于作者要求的 CUDA 12.9 / 驱动 ≥575.51.03 | 偏差 | 未升级驱动。改用官方 cu129 wheel，实测 CUDA 12.9 运行时在该驱动上可正常初始化并完成全部推理（见 §2）。 |
| B3 | 作者 pinned 的 `flash-attn==2.8.3`、`vllm==0.19.1` 需要编译/更重依赖 | 范围控制 | 改用 `attn_implementation="sdpa"` + HF Transformers 直接推理。**记为明确偏差，不通过 `--no-deps` 或覆盖依赖掩盖。** |
| B4 | `transformers` 加载 qwen3_5 时提示 linear-attention 快速路径缺失，回落到 PyTorch 实现 | 性能偏差 | 未安装 `flash-linear-attention`。功能正常；速度非作者测试栈水平。 |
| B5 | `qwen_vl_utils>=0.0.10` 在 new-API 中硬编码 torchvision；作者为此提供 `eval/task/qwenvl_decord_patch.py` | 复现保真 | 已安装 `decord 0.6.0` 并设置 `FORCE_QWENVL_VIDEO_READER=decord`，日志确认 `qwen-vl-utils using decord to read video`。 |
| B6 | 首次 GPU 作业失败（我方脚本 bug：`video_metadata` 传了 tuple，应为 list） | 我方缺陷 | 已修复并重跑成功；失败作业的 30.3 s 仍如实计入预算。 |
| B7 | 跟踪任务处理器提示 `max_pixels[786432] exceeds limit[524288.0]`，被内部收紧 | 事实记录 | 实际帧 534×300 归一后 156,672 px，未触发实际降采样；仍如实记录。 |
| B8 | 本次样本集的任务输入（表达式/事件文本/跟踪目标描述）由执行 Agent 定义 | 真值性质 | **明确不是人工真值**，见 §4.1 与 §7。 |

---

## 2. 源码、模型、环境的精确版本与路径

### 2.1 源码

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/HVision-NKU/OraRL` |
| 实际取得方式 | `https://ghproxy.net/https://github.com/HVision-NKU/OraRL.git`（镜像） |
| 路径 | `/home/inspur/aic_video_work/orarl_round1/src/OraRL` |
| commit | `e1ec91ff00f59ee0da04d285938c1f7247daa69c`（与历史记录一致，`dirty=false`） |
| 源码打包副本 | `evidence/OraRL_src.tar.gz`，sha256 `d00ed7154a9b1577a8e6420843f970c6cb5595b8b0422d0f679bfd9ae7caabe2` |

### 2.2 模型

| 项 | 值 |
|---|---|
| 模型 | `OraRL/Video-ORA-4B` |
| revision | `01850297d5ab2adaaf130f700ed7cec52993d956`（与历史记录一致） |
| 路径 | `/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B`（10,370,252,800 bytes ≈ 9.66 GiB） |
| 架构 | `Qwen3_5ForConditionalGeneration`，`model_type=qwen3_5`，5.175 B 参数（分片头求和），dtype bfloat16 |
| 加载类（实测） | `AutoModelForImageTextToText`；处理器 `AutoProcessor` → `Qwen3VLProcessor` + `Qwen2VLImageProcessor` |
| 下载工具 | `huggingface_hub 0.36.2` `snapshot_download`，`HF_ENDPOINT=https://hf-mirror.com`，带断点续传 |

**未下载内容（本轮磁盘策略，非缺失）：** 模型仓内自带源码副本的 `code/assets/*` 文档图片/动画（9 个 LFS 文件）。源码已由同 commit 的 git 克隆取得。

### 2.3 环境

| 项 | 值 |
|---|---|
| 路径 | `/home/inspur/aic_video_work/orarl_round1/env/orarl_hf`（8,599,650,304 bytes ≈ 8.01 GiB） |
| 方式 | `python3.11 -m venv`（基于 `/home/inspur/anaconda3/envs/test_env/bin/python`，仅作解释器来源，未修改该环境） |
| Python | 3.11.10 |
| torch / torchvision | `2.10.0+cu129` / `0.25.0+cu129`（官方索引 `https://download.pytorch.org/whl/cu129`） |
| transformers | `5.5.4`（与作者 pin 相同） |
| 其他关键 | `accelerate 1.13.0`、`qwen-vl-utils 0.0.14`、`decord 0.6.0`、`av 18.1.0`、`numpy 2.2.6`、`pillow 12.1.1`、`safetensors 0.8.0`、`tokenizers 0.22.2` |
| 冻结清单 | `evidence/env_pip_freeze.txt` |
| 未安装 | vllm、flash-attn、flash-linear-attention、causal-conv1d |

### 2.4 与作者测试栈的差异（明确记录）

| 维度 | 作者 | 本轮 | 影响 |
|---|---|---|---|
| CUDA / torch | cu129 / torch 2.10.0+cu129 | **相同** | — |
| transformers | 5.5.4 | **相同** | — |
| 推理引擎 | vLLM 0.19.1 | HF `generate()`（batch=1） | 采样/解码等价性未验证；吞吐不可比 |
| attention | flash_attention_2 2.8.3 | **sdpa** | 数值可能有微小差异 |
| linear attention | flash-linear-attention 0.4.2 | PyTorch 回落实现 | 速度较慢，功能可用 |
| 视频后端 | decord（作者 patch） | **decord**（env 开关生效） | 一致 |
| Python | 3.11（conda） | 3.11.10（venv） | 无实质差异 |

---

## 3. 权重完整性及离线加载证据

### 3.1 字节级校验（对官方 LFS sha256）

`evidence/weight_sha256_manifest.json`；官方哈希取自 `https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true`。

| 文件 | 大小 (bytes) | sha256 vs 官方 |
|---|---|---|
| model-00001-of-00005.safetensors | 1,271,398,528 | 相等 |
| model-00002-of-00005.safetensors | 2,474,053,512 | 相等 |
| model-00003-of-00005.safetensors | 2,472,678,384 | 相等 |
| model-00004-of-00005.safetensors | 2,477,924,456 | 相等 |
| model-00005-of-00005.safetensors | 1,653,963,896 | 相等 |
| tokenizer.json | 19,989,343 | 相等 |

结论：`all_required_local_bytes_match_official_lfs = true`。

### 3.1.1 三方一致（额外的独立校验路径）

`huggingface_hub` 在下载时于 `.cache/huggingface/download/*.metadata` 留下了 16 个记录文件
（**纯文本 3 行**：revision / 期望哈希 / mtime，而非 JSON）。把三者对齐后：

| 校验路径 | 来源 | 结果 |
|---|---|---|
| 下载器自己记录的期望哈希 | `*.metadata` 第 2 行 | — |
| 本地重新计算的 SHA-256 | 本次实测 | — |
| 官方 API 的 LFS sha256 | `hf-mirror.com/api/...?blobs=true` | — |

**三个值在 5 个 safetensors 分片 + tokenizer.json 上完全一致（6/6）。**

> **方法学说明（含一次自我纠正）**：最初一版校验脚本按 JSON 解析这些 `.metadata`，取 `etag` 字段，结果为 0 条，于是错误地推断"huggingface_hub 不写这些文件"。复核后确认文件确实存在、内容为 3 行文本；脚本已改为按文本解析，并据此补上了这条独立校验路径。报告中保留此纠正过程。另注意：非 LFS 文件（如 `config.json`）第 2 行记录的是 git blob sha1（40 位），不是 sha256，故不参与上面的 LFS 比对。

### 3.2 索引与张量一致性

`evidence/preflight.json` → `index_check`：

- `model.safetensors.index.json` 的 `weight_map` 共 **724** 条，横跨 5 个分片。
- 逐分片比对 index 键集合 vs safetensors 头部键集合：**5/5 完全一致**（missing=[]、extra=[]）。
- 分片参数合计 **5.1750 B**；全部张量 dtype = BF16。
- `metadata.total_size = 10,349,929,472`。

### 3.3 离线加载证据（CPU，不占 GPU 预算）

`evidence/offline_load_probe.json`（`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`）：

```
AutoConfig            -> model_type=qwen3_5, architectures=[Qwen3_5ForConditionalGeneration]
AutoModelForImageTextToText 注册 qwen3_5 -> True
AutoProcessor         -> Qwen3VLProcessor / Qwen2VLImageProcessor
from_pretrained(device_map=cpu) -> params=4.5393 B, dtype=bf16,
                                   missing_keys=0, unexpected_keys=0, mismatched_keys=0,
                                   weights_fully_consumed=True
tiny CPU generate     -> 'ok'
all_ok = True
```

加载期提示：`The fast path is not available ... Falling back to torch implementation`
（linear-attention 快速路径缺失，回落 PyTorch 实现；功能正常，见 B4）。

### 3.4 GPU 侧加载

预算作业 `orarl_r1_verify2` 日志：`loaded in 4.8s, allocated 8678 MiB`，dtype bfloat16。

---

## 4. 三类推理的输入说明、原始输出位置与运行结果

统一设置：`enable_thinking=False`（作者推荐的 answer-only 方式）、`do_sample=False`（temperature=0）。

### 4.1 样本来源与选择方式

`evidence/sample_manifest.json`：

| 项 | 值 |
|---|---|
| 源视频 | `/home/inspur/aic_video_data/videos/w/wk2CeU_DcBo_60.0_210.0.mp4`（项目源视频池，**只读**） |
| 源 sha256 | `7a0e79837ef5ae662b8ec65365aab51495275955f370d0d4237527752c2d9b3b` |
| 源属性 | 534×300，30 fps，4500 帧，150.024 s，h264 |
| 派生片段 | `clips/src_wk2CeU_DcBo_60_210_off0_len32.mp4`，sha256 `f6327e9cd68f04e5ba7e79bf1a22619ab591013f57e870230f2cf610710b419d` |
| 派生方式 | `ffmpeg -ss 0 -t 32 -c copy`（**流拷贝，无重编码**）→ 534×300，30 fps，962 帧，32.2 s |
| 片段偏移 | **0.0 s** → 片段内时间 == 源视频时间（该片段内），无需平移换算 |
| 派生静帧 | `frames/sg_frame_off0.png`（t=0，无损 PNG），sha256 `438c5de617d87c8f52cb69e52035f41f3d4b7d468bc789d0025a577072b776fa` |

**为何片段取 32 s**：作者的跟踪 profile 是 `TRACKING_FPS=1 / TRACKING_MAX_FRAMES=32`，即任务本身以 32 秒为界。若片段更长，`max_frames=32` 会把 32 个采样点摊到整段上，"第 N 秒"就不再近似第 N 秒（实测 40 s 片段下采样间隔变成 ≈1.29 s）。

**未使用 AIC 测试集。** 未使用 987 条弱标签作为真值。

**任务输入性质（重要）**：

| 任务 | 输入 | 来源 | 是否真值 |
|---|---|---|---|
| 图片空间定位 | 表达式 `the man in the white sleeveless shirt` | 执行 Agent 看过该帧后自行撰写 | **否** |
| 短视频时序定位 | 事件 `Man and woman walk through the park sidewalk together.` | `frozen_data/dev.jsonl` 行 `qvh_934` 的 `query` 字段（该行 `trusted_identity=false`、`source_trust_status=PENDING_SUPERVISOR_ADJUDICATION`） | **否** |
| 短视频跟踪 | 目标描述 `the man in the white sleeveless shirt in the foreground` | 执行 Agent 撰写 | **否** |

### 4.2 各任务输入构造（与作者代码逐字对齐）

| 任务 | 采样/像素参数（来自 `data/eval/datasets.jsonl`） | 提示词（逐字来自 `eval/task/eval_prompt.py`） |
|---|---|---|
| 空间定位 | `min_pixels=65536`, `max_pixels=1048576`（min_tokens=64, total_tokens=1024, dr=32） | `QWEN_NATIVE_PROMPT_SG`：`Locate "…" in the image. Output its bounding box in JSON format within <answer>…</answer> tags. …` |
| 时序定位 | `fps=4`, `max_frames=2048`, `max_pixels=409600`, `total_pixels=131072000`, `min_pixels=1024` | `TEMPORAL_GROUNDING_PROMPT`：`To accurately pinpoint the event "…" … "start time to end time" within <answer> </answer> tags. …` |
| 跟踪 | `fps=1`, `max_frames=32`, `max_pixels=786432`, `total_pixels=8388608`, `min_pixels=4096` | `GROUNDING_QUESTION_TEMPLATE_NO_THINK` + `TRACKING_TAIL`：每秒一个框，仅到第 32 秒，`{"boxes": {"1": [x1,y1,x2,y2], …}}` |

### 4.3 运行结果（原始输出见 `outputs/raw/*.raw.txt`）

| 任务 | 状态 | 原始输出 | 解析结果 | 生成耗时 | 输出 token | 峰值显存 |
|---|---|---|---|---|---|---|
| 空间定位 | ok / valid | `<answer>[{"bbox_2d": [393, 11, 998, 997]}]</answer>` | 1 个框，norm1000 | 2.58 s | 32 | 8774 MiB |
| 时序定位 | ok / valid | `<answer> 0 to 21 </answer>` | span = [0.0, 21.0] s | 3.18 s | 13 | 11525 MiB |
| 跟踪 | ok / valid | `<answer>{"boxes": {…"1": [392,0,998,997], "2": [400,0,998,997], … "32": [400,0,998,997]}}</answer>` | 32 个秒键，norm1000 | 29.41 s | 704 | 9456 MiB |

解析错误：三者均为 `[]`；解析警告：均为 `[]`。空输出 / 非法 JSON / 越界框**均未被静默修补**——解析器遇到这些情况会置 `valid=false` 并写入 `parse_errors`。

**跟踪结果的重要负面事实**：32 个秒键中只有 **3 个不同的框**，全部为 `x1∈[392,406]`、`y1=0`、`x2=998`、`y2=997`。即输出**近乎静止**，没有表现出对目标的跟随或尺度变化。

### 4.4 可视化核查（回画到真实帧）

`outputs/overlays/`：

| 文件 | 内容 | 肉眼核查结论 |
|---|---|---|
| `spatial_grounding_overlay.png` | 把 norm1000 框换算到 534×300 像素并画在原帧上 | 框（像素 [209.9, 3.3, 532.9, 299.1]）**确实套住了白衣无袖男子**；框偏松，覆盖了部分背景 |
| `temporal_grounding_frames.png` | 预测起/中/止 与 存储窗口起/止 五帧并排，各帧标注真实时间 | 预测 0–21 s 落在公园并肩行走段落内；存储窗口端点 24 s 已切到另一镜头（街景），说明该窗口本身较宽/含切镜 |
| `tracking_overlay_sheet.png` | 32 个秒键对应的真实采样帧各画一框（6×6 拼图） | 第 1–22 秒框一致停在白衣男子身上（因他占画面右侧）；**约 22 秒后镜头切走，模型仍输出同一个静止框，落在无关内容上** |

`tracking_sec_01.png … tracking_sec_32.png` 为逐秒已画框图，可单独放大核查。

诊断量（**不是准确率**）：

- 时序定位 vs 存储窗口 [0,24] 的 IoU = **0.875**。该标签身份未确证（`trusted_identity=false`），此数字仅作并列观察。

---

## 5. 时间、帧号、坐标的转换约定

### 5.1 坐标

| 任务 | 模型输出坐标制 | 框格式 | 判定依据 |
|---|---|---|---|
| 图片空间定位 | **norm1000**（0–1000 归一化整数） | `[x1, y1, x2, y2]`，JSON `[{"bbox_2d": [...]}]` | `datasets.jsonl` 的 `preprocessing.coordinate_system="norm1000"`；`eval_refcoco_vllm.py` 注释明确 "the model is known to emit norm1000"、"vanilla Qwen3.5-4B emits norm1000 too" |
| 短视频跟踪 | **norm1000** | `[x1, y1, x2, y2]`，JSON `{"boxes": {"<秒>": [...]}}` | `eval_tracking_vllm.py` 文件头注释："Each value is a 4-number bbox [x1, y1, x2, y2] in norm1000 coords" |
| 短视频时序定位 | **秒**（浮点，相对输入片段起点） | `<answer> start to end </answer>` | `TEMPORAL_GROUNDING_PROMPT` 与 `eval_prompt.py` |

像素换算（**仅在核查时使用，不参与模型输入**）：

```
x_px = x_norm1000 / 1000 * frame_width
y_px = y_norm1000 / 1000 * frame_height
```

例：`[393, 11, 998, 997]` @ 534×300 → `[209.86, 3.30, 532.93, 299.10]`。

越界判定：norm1000 框要求 `0 ≤ 坐标 ≤ 1000` 且 `x2>x1, y2>y1`，否则写入 `parse_errors`。

### 5.2 时间与采样帧

- 输出时间**相对输入片段起点**。本片段 `source_offset_sec = 0.0`，故 `t_source = t_clip`（片段内成立）。
- 采样规则（`qwen_vl_utils`）：`nframes = clamp(round(duration × fps), min_frames, max_frames)`；`indices = linspace(0, total_frames-1, nframes)`；帧号为该视频**原生 fps** 下的索引。

实测（片段 962 帧 @30 fps，时长 32.2 s，后端 decord）：

| 任务 | fps | max_frames | 实际采样帧数 | 帧号范围 | 时间范围 |
|---|---|---|---|---|---|
| 时序定位 | 4 | 2048 | 128 | 0 → 961 | 0.000 s → 32.033 s |
| 跟踪 | 1 | 32 | 32 | 0 → 961 | 0.000 s → 32.033 s |

**跟踪任务的"第 N 秒"与真实采样时刻并不严格相等**：32 帧均摊在 32.2 s 上，间隔 ≈1.0333 s，故
`sampled_t(N) ≈ (N-1) × 1.0333 s`。逐秒对应关系见 `outputs/sampled_frames_tracking.json` 的
`secondN_vs_sampled_time` 字段；可视化图每格都标注了真实时间戳。

- 时序定位的 128 帧在 32.2 s 上均摊，间隔 ≈0.2535 s（目标 4 fps ≈ 0.25 s，存在确定性的均摊偏差）。

---

## 6. 实际耗时、峰值显存、本轮磁盘增量与 GPU 预算消耗

### 6.1 GPU 预算（经 `improvement_round1/budget_run.py` 串行化并记账）

| 作业名 | 状态 | 计入秒数 | 采样峰值显存 |
|---|---|---|---|
| `orarl_r1_verify` | failed（我方脚本 bug，见 B6） | 30.3 s | — |
| `orarl_r1_verify2` | completed（exit 0，跑齐三类任务） | 60.7 s | 12426 MiB |
| `orarl_r1_replay_sg` | completed（exit 0，固定配置重跑） | 60.6 s | 12426 MiB |
| **本轮合计** | | **151.6 s**（上限 1800 s） | 峰值 **12426 MiB ≈ 12.14 GiB** |

原项目累计：账本 29 条记录，`charged = 35485.4 s`（含初始 7200 s 保守计费）= **9.8571 h / 24 h**，**剩余 14.1429 h**。

> 说明：`budget_run.py` 按整段墙钟计费，故 60.7 s 包含模型加载（4.8 s）、三次前向与进程启动开销，而非纯 GPU 计算时间。

### 6.2 耗时明细

| 阶段 | 耗时 |
|---|---|
| 模型加载（GPU，bf16） | 4.8 s，分配 8678 MiB |
| 空间定位生成 | 2.58 s |
| 时序定位生成 | 3.18 s |
| 跟踪生成 | 29.41 s（704 输出 token，是三者中最慢的） |
| `orarl_r1_verify2` 整段墙钟 | 60.7 s |
| CPU 离线加载（不占 GPU） | 0.76 s |

### 6.3 磁盘

| 项 | 值 |
|---|---|
| 本轮前 `/home/inspur/aic_video_work` | 20,961,681,408 B = 19.52 GiB |
| 本轮后 | 39,983,161,344 B = 37.24 GiB |
| **本轮增量** | **19,021,479,936 B = 17.716 GiB**（上限 25 GiB ✓） |
| 其中模型 | 10,370,252,800 B ≈ 9.66 GiB |
| 其中环境 | 8,599,650,304 B ≈ 8.01 GiB |
| 项目 80 GiB 新增上限 | 37.24 GiB < 80 GiB ✓ |
| 文件系统剩余 | 154,268,635,136 B = 143.67 GiB（要求 ≥80 GiB ✓） |

### 6.4 复现一个样本的耗时

| 场景 | 墙钟（计费） |
|---|---|
| 固定配置重跑（`orarl_r1_replay_sg`，含加载 + 三类任务） | **60.6 s** |
| 其中模型加载（GPU，bf16） | 4.7 s |
| 其中空间定位生成 | 2.58 s |
| 其中时序定位生成 | 3.18 s |
| 其中跟踪生成（704 输出 token，最慢） | 29.41 s |

---

## 7. 哪些结果仅证明可运行，哪些有可信标注支持

### 7.1 有确凿证据支持的结论

1. **权重与源码版本正确且字节可核**：revision / commit 与历史记录一致；5 分片 + tokenizer 的 SHA-256 与官方 LFS 逐一相等；index 的 724 个键与分片头部完全吻合。
2. **模型在本机可离线加载**：CPU 离线加载 0 missing / 0 unexpected / 0 mismatched；GPU 侧 4.8 s 加载完成，8.6 GiB 权重驻留。
3. **CUDA 12.9 运行时在驱动 570.144 上可用**：`cuda_available=True`，matmul 通过，三次推理全部完成。作者文档称 cu129 需驱动 ≥575.51.03；本机 570.144 实测可用（偏差 B2，已记录，未改驱动）。
4. **三类任务端到端可跑通且输出可解析**：提示词、采样参数、坐标约定与作者发布一致；无效输出会显式标错而非静默修补。
5. **坐标与时间可解释、可肉眼核查**：norm1000 → 像素换算经原帧回画确认；采样帧号、时间、每秒对应关系均已落盘。

### 7.2 仅证明"流程可运行"、不能主张正确性的结论

1. **空间定位的框看起来套住了目标**（人工目视确认）。但该表达式由执行 Agent 自拟，**没有人工真值文件**，因此只能说明"输出可解释且物理自洽"，不能给出 IoU/准确率。
2. **时序定位输出 0–21 s 与存储窗口 [0,24] 的 IoU = 0.875**。该标签来自身份未确证的弱标签集（`trusted_identity=false`、`PENDING_SUPERVISOR_ADJUDICATION`），**这是一个诊断并列量，不是准确率**。回画核查还显示存储窗口端点 24 s 已切镜，说明该窗口本身可能过宽。
3. **跟踪输出格式完全合法但行为退化**：32 秒仅 3 个不同框、近乎静止；目标在约 22 秒后离开画面而模型继续输出同一框。**因此本轮不能声称模型具备可用的跟踪能力**，只能声称"跟踪接口能跑通、输出可解析、坐标可核查"。
4. **跟踪的初始化先验与 GOT-10k 不同**：作者评测给出首帧框，本轮只给了自然语言目标描述。这是跟踪退化的一个可能原因，也是必须交给总控 Agent 决策的点（见 §8）。
5. **不得将本报告任何数字与 43.4800 或 57 分比较**，也不得换算成比赛分数：本地无官方 AIC evaluator，样本量为 1/任务，且无对齐真值。

---

## 8. 需要总控 Agent 决策的问题（3 项）

1. **跟踪的初始化先验怎么定？**
   作者 GOT-10k 协议给首帧框；本轮只给自然语言描述，得到近乎静止的输出。下一轮是否改用"首帧框 + 目标描述"？若用首帧框，可否接受由现有工具/人工在没有可信真值的源视频上点选得到（即该框只作输入先验、不作真值）？还是必须等 987 条弱标签的媒体映射恢复后再做？

2. **是否投入建立一套小而独立可信的诊断标注？**
   现有弱标签身份未确证，导致任何"新旧模型对比"都无法给出可信数字。是否批准在**非测试的公开视频**上建立少量（例如 20–50 条）人工核验的时序/空间标注，作为 OraRL 与旧 Qwen3-VL 对照的诊断基准？这需要人工时间，但它是把"能跑"变成"可比较"的唯一途径。

3. **下一轮是补环境保真度，还是先看能力边界？**
   本轮为适配现有驱动用了轻量栈（sdpa、无 vLLM/flash-attn/fla，线性注意力回落 PyTorch）。是否需要投入一次到作者的完整栈（vLLM 0.19.1 + flash-attn 2.8.3 + fla 0.4.2）以便与论文公开指标同条件对照？还是优先在轻量栈上扩大任务样本、先把"时序定位"这一最贴近 AIC 的能力边界摸清？

---

## 9. 一条可复现命令

**下面这条命令已被实际执行并验证通过**（即账本中的 `orarl_r1_replay_sg`，exit 0，60.6 s，三类任务全部 `valid=true`）：

```bash
ssh aic-inspur-home
bash /home/inspur/aic_video_work/orarl_round1/scripts/run_gpu_budgeted.sh \
     orarl_r1_replay_sg 600
```

它等价于（`run_gpu_budgeted.sh` 内部展开的形式，`budget_run.py` 会强制注入
`HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`）：

```bash
cd /home/inspur/aic_video_work && python3 improvement_round1/budget_run.py \
  --name orarl_r1_replay_sg --max-seconds 600 -- \
  /home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python \
  /home/inspur/aic_video_work/orarl_round1/scripts/run_inference.py \
    --model   /home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B \
    --samples /home/inspur/aic_video_work/orarl_round1/evidence/sample_manifest.json \
    --out     /home/inspur/aic_video_work/orarl_round1/outputs \
    --attn sdpa --tasks spatial_grounding,temporal_grounding,tracking
```

注意事项：

1. **`--name` 在账本中必须唯一**；重跑请换名（如 `orarl_r1_replay_sg2`），否则 `budget_run.py` 会以
   `job name already exists; preserve prior evidence` 拒绝启动。
2. 只跑单个任务时，把最后一行改成 `--tasks spatial_grounding`（**不要**用包装脚本，它固定传三类任务）。
3. 当前 GPU 上不能有其他计算进程，且 `improvement_round1/active_gpu_job.json` 必须不存在，否则同样被拒。

只验证离线加载、不占 GPU 预算：

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python \
  /home/inspur/aic_video_work/orarl_round1/scripts/cpu_load_probe.py \
  /home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B \
  /home/inspur/aic_video_work/orarl_round1/evidence/offline_load_probe.json
```

只跑无效输出检查（纯 CPU）：

```bash
python3 /home/inspur/aic_video_work/orarl_round1/scripts/test_invalid_outputs.py
```

---

## 10. 本轮"可复现性"与"无效输出不计成功"的直接证据

### 10.1 固定配置重跑成功且结果逐字一致

`orarl_r1_replay_sg` 与 `orarl_r1_verify2` 的原始输出**逐字节相同**：

```
<answer>[{"bbox_2d": [393, 11, 998, 997]}]</answer>
```

（`do_sample=False`、`temperature=0`，故这是确定性解码，重跑一致是预期行为，可作为配置固定成功的证据。）

### 10.2 离线加载的直接证据

- `budget_run.py:68` 明确设置 `HF_HUB_OFFLINE='1'`、`TRANSFORMERS_OFFLINE='1'`（两个 GPU 作业均经此包装）。
- 模型目录 `.cache` 内最新文件 mtime 为 **23:33:57（本地）**，即下载结束时刻；GPU 作业运行于 **23:45–23:59**。
  **23:45 之后模型 `.cache` 与全局 `~/.cache/huggingface` 均无任何新写入** → 作业确实只读本地磁盘。

### 10.3 无效输出不会被计为成功

`scripts/test_invalid_outputs.py`：**26 个负例全部被正确判为无效**（`valid=false` 且 `parse_errors` 非空），
**3 个正例全部通过**。覆盖：空输出、无 `<answer>`、空 `<answer>`、非 JSON、类型错误、
框数不足、norm1000 越界、框反向、秒键越界、非整数秒键、时间起止反序、时间超出片段时长等。

另：跟踪任务若秒键不齐（例如只有 2 个），**记为 warning 而非静默成功**，且在 `run_status.json` 中可见：

```
parsed seconds=2 errors=[] warnings=['missing seconds (n=30): [2, 3, 4, ...]']
```

### 10.4 视频时间与框坐标可解释、可检查

- 采样帧号 ↔ 时间：`outputs/sampled_frames_temporal_grounding.json`、`outputs/sampled_frames_tracking.json`
  （含 `frames_indices`、`frames_seconds`、`secondN_vs_sampled_time`）。
- 框坐标 ↔ 像素：`outputs/overlay_manifest.json` 中每个框同时给出 norm1000 与像素值。
- 肉眼核查：`outputs/overlays/` 下三类回画图（跟踪含逐秒 32 张 `tracking_sec_NN.png`）。

---

## 附录 A：产物清单（远程 `/home/inspur/aic_video_work/orarl_round1`）

| 路径 | 内容 |
|---|---|
| `REPORT.md` | 本报告 |
| `scripts/` | `run_inference.py`（三类推理入口）、`test_invalid_outputs.py`（无效输出负例测试）、`cpu_load_probe.py`、`verify_official_sha256.py`、`verify_and_preflight.py`、`make_overlays.py`、`make_summary.py`、`prepare_samples.sh`、`run_gpu_budgeted.sh`、`r04_download_model.sh`、`r09_build_env.sh` |
| `src/OraRL/` | 作者源码 @ `e1ec91ff…` |
| `model/Video-ORA-4B/` | 官方 4B 权重 @ `01850297…` |
| `env/orarl_hf/` | 独立推理环境 |
| `evidence/preflight.json` | 硬件/磁盘/预算/准入结论 |
| `evidence/weight_sha256_manifest.json` | 官方 SHA-256 校验清单 |
| `evidence/offline_load_probe.json` | 离线加载证据 |
| `evidence/env_pip_freeze.txt` | 锁定依赖 |
| `evidence/sample_manifest.json` | 样本来源、哈希、任务输入说明 |
| `evidence/hf_model_api*.json` | 官方模型元数据快照 |
| `outputs/run_status.json` | 完整运行记录（含异常栈） |
| `outputs/round_summary.json` | 报告用汇总数字 |
| `outputs/raw/*.raw.txt` | **原始模型输出**（未清洗） |
| `outputs/sampled_frames_*.json` | 采样帧号 ↔ 时间对应 |
| `outputs/overlays/` | 回画核查图（含逐秒 32 张） |
| `outputs/overlay_manifest.json` | 回画清单与诊断量 |
| `logs/` | 下载、环境构建、两次 GPU 作业日志 |

## 附录 B：本轮未触碰的边界

- 未升级系统驱动、未修改全局 Python 环境、未修改 SSH/网络配置、未影响其他 GPU 任务。
- 原始数据、旧模型、旧 adapter、已有提交包与实验日志全部保留，未做任何清理或覆盖。
- 未绕过 `budget_run.py` 的锁与预算；两个 GPU 作业均经其串行化并计入原 24 h 总预算。
- 未下载整套 OraRL 训练/评测数据。
- 未把任何比赛视频、帧或标签发送到第三方模型 API（全程本地推理）。
- 未切换 9B、未量化替换正式权重、未启动 LoRA 或 RL 训练。
- 未将 987 条弱标签的时间与裁剪框套到源视频上。
