# 新完整窗口监督：CPU 工具已就绪，32B 教师容量 STOP

本目录只新增准备、校验和训练合同。旧训练数据、模型、冻结源码、运行器及提交包均未改动。没有标注成功、训练启动或官方质量通过的声明。

## 实际结果与停止边界

- 原 R7 train/dev 的文件 SHA、704/104 条及 602/96 个 YouTube 来源组已通过本地 CPU 合同核验；两名单按 `youtube_id` 隔离。没有打开 `confirm_temporal.jsonl` 或比赛媒体/模型输出。
- CPU 选择器和教师校验器已实现；真实 Linux 全来源 PTS 扫描和窗口选择由主控部署后执行。本代理没有回传新文件或写远端数据。
- 官方 HF 元数据实查见 `teacher_metadata_20261007.json`。状态为 **`STOP_32B_TEACHER_CAPACITY`**。不下载权重、不安装环境、不删除已有资产、不用当前 8B 静默替代强教师。
- 新教师响应和实际解码 receipt 尚不存在；已标注数量为 **0**，完整列表 SFT 尚未准入。`train_config_template.json` 是不可直接开训的合同模板。
- 首工作日边界登记为 **2026-10-07 23:59:59 UTC+8**。若届时仍无可解释正样本与明确无高光监督，`check_supervision_gate.py` 产生 `STOP_T_FIRST_WORKDAY_SUPERVISION_UNAVAILABLE`。Z 继续推进，不等待 T；M 已交付。

## 选择器的实际输入和范围

选择器只接受下列原 R7 两个精确文件 SHA，不打开 confirm：

| 输入 | 条数 / 来源组 | SHA256 |
|---|---:|---|
| `train_temporal.jsonl` | 704 / 602 | `ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf` |
| `dev_temporal.jsonl` | 104 / 96 | `53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700` |

R7 行中的 `source_group` 是下载片段的身份。为避免同一 YouTube 视频的不同片段跨 split，本次新 `source_group` 使用 `youtube_id`，原片段身份保存在 `downloaded_clip_group`。旧 JSON 仅为抽取白名单身份而加载，旧 `clip_*` 与正区间字段不参与选择。

每个 split 按冻结哈希顺序排列来源组，每组只取一份现有完整 `source_path`，均限定在 `/home/inspur/aic_video_data/videos`。首批 128 train + 32 dev，扩展最多 512 + 64；首批是扩展名单的前缀。每个组本轮选一个自然窗口，固定交替覆盖视频开头、内部与结尾。语义上的普通背景、多事件比例必须等实际标注后统计，不能由位置采样宣称已覆盖。

`ffprobe -show_frames` 对被选来源完整扫描呈现 PTS，要求每一帧 PTS 存在且严格递增，末帧实际 duration 存在。窗口从实际首 PTS 开始，30 秒、步长 30 秒，保留最后不足 30 秒的尾窗；不以旧高光 clip 边界、FPS 推算或标题拼接起止。缺少末帧 duration 或时钟异常会 STOP，不能估一个终点补齐。`ffprobe` 会进行 CPU 帧元数据解码；本工具不导出或检视像素，也不使用 GPU。

窗口保存媒体 SHA、整条 PTS 序列 SHA、实际窗口范围、计划源帧 ordinal 与 PTS。最多 64 帧，包含首末可用帧。**这时只是计划，不是实际教师输入或完整观看证明。**后续 decoder 必须顺序恢复同一 ordinal/PTS 与逐帧 pixel SHA，并给出实际 processor 的 frame/pixel/token receipt。采样间隙仍可能遗漏短事件；完整窗口教师判断也只是弱证据。

## 教师 prompt、响应和清洗合同

`teacher_prompt.txt` 要求通用高光、全部保留区间、明确允许不选，并说明相对窗口起点的秒数。`teacher_response.schema.json` 提供外部接口；`validate_teacher.py` 用 stdlib 执行更严格的跨字段、PTS、权重与边界检查。

每条记录保存完整 window、来源组、媒体 SHA、实际 PTS/pixel/processor receipt、官方模型 revision 和全部已选权重 SHA、实际 runtime revision、展开 prompt 与 SHA、原始 answer 与 SHA、全部 retained segments、`explicit_no_highlight`、`uncertain`、清洗/排除理由。

状态分开：

- 明确可解释的正区间进入弱完整列表目标。
- `[]` 只有在 `explicit_no_highlight=true`、`uncertain=false` 且有解释时进入目标；不按空样本配额制造它。
- uncertain 的空或候选正区间均保留审计记录、排除 SFT。
- 未标注、未生成、解析失败、输入失败均没有目标，不能转成空。
- 超过新生产合同 5 段的响应保留原文和全部区间，因当前目标不能表示而排除；不截断、删段、排序修复或合并。新生产若以后变更上限，需要独立修订该合同。

教师只承诺审阅实际提供的采样帧，校验器不把教师自报完整、两次一致或更大参数当作真值。不确定的观察间隙不能认证为负例；独立参考仍须单列。

## 32B 的精确只读可行性

API 只请求公共模型元数据与小 `config.json`，没有请求任何权重文件。Jina 对 HF 域的匿名访问临时拒绝后，转到官方页面与公共 HF 元数据接口；未读取用户 token。

| 官方来源 | 固定 revision | 选用权重体积 |
|---|---|---:|
| [Qwen3-VL-32B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct/tree/0cfaf48183f594c314753d30a4c4974bc75f3ccb) BF16 | `0cfaf48183f594c314753d30a4c4974bc75f3ccb` | 14 分片，66,714,912,872 bytes |
| [官方 GGUF Q4_K_M + FP16 mmproj](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct-GGUF/tree/e3e1fe0c76de7ee58ea65db420c643adfe2e457c) | `e3e1fe0c76de7ee58ea65db420c643adfe2e457c` | 20,958,945,472 bytes / 19.5195 GiB |

Q4 语言权重 19,762,150,432 bytes，SHA `5cf0136e721d6294718ec71fd8c93b17ab5dd4e2714d6079e83fa46571ad94c8`；FP16 视觉 projector 1,196,795,040 bytes，SHA `8617824839df91f84b4840ad5084dcf50a1403a435a1f4cfc4d8c84ce6cac2fc`。这是官方发布的较低精度语言组件与 FP16 视觉组件组合，并非全模型所有张量都量化为 4bit。[官方 model card](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct-GGUF/blob/e3e1fe0c76de7ee58ea65db420c643adfe2e457c/README.md)

主控当日实时占用 Linux 50,907,619,328 + Mac 28,053,655,552 = **78,961,274,880 bytes**。边界为 **80 GiB = 85,899,345,920 bytes**，剩余 **6,938,071,040 bytes / 6.4616 GiB**。只加选定权重、假设没有任何缓存/临时文件的理论最低合计已为 99,920,220,352 bytes，超边界 14,020,874,432 bytes；因此容量 STOP 不依赖不确定的缓存估计。

缓存峰值不能只报最终量化文件：理想同文件系统 `.incomplete` 重命名路线最低仍需完整 19.52 GiB，但该实现尚未验证；Hub blob cache + 独立 model copy + 一份旧最大 partial 的保守情景需 61,680,041,376 bytes，再加 Xet、环境、解码、日志等。此数是情景上界，不是本次实测。不得下载全 GGUF repo 的 FP16/Q8 文件，也不得先下载 BF16 再量化并隐去其峰值。

只读 SSH 已确认 `inspur-NP5570M5`，RTX 6000 Ada 46,068 MiB、used 182 MiB、GPU 0%、compute 为空；系统可用 RAM 126,149,324,800 bytes。这不是 32B 运行验收。既有 `/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python` 的包元数据为 torch 2.5.1+cu124、transformers 4.57.1、qwen-vl-utils 0.0.14；llama-cpp-python/autoawq/vllm/bitsandbytes 无安装记录，PATH 无 llama-cli/llama-server。官方 GGUF 需要另外验收兼容运行时和视频 PTS 行为；本次不安装、不加载、不作 GPU/RAM 峰值承诺。既有 Andy ffprobe 绝对路径存在。

## 训练合同与调用入口

模板从 Linux 最终 adapter SHA `8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23` 初始化，保留旧文件，语言 q/k/v/o r16、alpha32、dropout0.05，基座和视觉冻结。lr=1e-5、AdamW、clip1.0、有效 batch16、最多新数据 3 轮。前20次更新属于这同一轮最多三 epoch 的前缀，不额外再训三轮；保存 epoch1/2/3 adapter，并保存 update20 的 optimizer/RNG/位置以便有证据后接续。

开放开发来源与训练来源分组隔离，事前冻结 checkpoint selection，视频宏指标为点估计，按来源组重采样；格式/空/解析/执行失败分别报告。原100confirm只保留给最终一次确认。本模板 deliberately 留空实际统一 pixel/token budget、microbatch 与 manifest SHA；须由主控基于真实 processor 合同和资源填写，不能把占位值当开训许可。

全部命令先由主控核实时资源，再按传输约束经 Mac 部署；以下不含下载或 GPU 入口。Linux 的 `$SUPERVISION` 应是本目录的对应远端路径。

```bash
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
R7=/home/inspur/aic_video_work/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs
SUPERVISION=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision
$PY -B "$SUPERVISION/test_cpu.py" --receipt "$SUPERVISION/cpu_linux_result_01.json"
$PY -B "$SUPERVISION/select_windows.py" --train-manifest "$R7/train_temporal.jsonl" --dev-manifest "$R7/dev_temporal.jsonl" --ffprobe /home/inspur/anaconda3/envs/Andy/bin/ffprobe --tier first --out-dir "$SUPERVISION/selection_01"
```

如果未来强教师实际准入并生成 annotation receipts，批量校验入口为：

```bash
$PY -B "$SUPERVISION/validate_teacher.py" --selected-train "$SUPERVISION/selection_01/selected_train.jsonl" --selected-dev "$SUPERVISION/selection_01/selected_dev.jsonl" --selection-receipt "$SUPERVISION/selection_01/selection_receipt.json" --annotation-receipts "$SUPERVISION/real_teacher_annotations_01.jsonl" --out-dir "$SUPERVISION/validation_01"
```

annotation 每行 `{window_id, observation, teacher, raw_answer}`；`test_cpu.py::fixture` 仅展示字段形状，其 `SYNTHETIC_TEST_ONLY` receipt 绝不是实际标注。未来真实 receipt 格式由该 fixture 和严格校验函数共同约束。

验证证据见 `cpu_contract_result_01.json`。本地测试只核合成合同与真实原 train/dev 身份，没有执行实际视频扫描、teacher 标注或训练。当前没有可供开训的新监督包。
