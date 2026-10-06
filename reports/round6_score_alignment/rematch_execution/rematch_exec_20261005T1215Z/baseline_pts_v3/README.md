# 复赛源时间身份 v3（CPU）

生产源码已冻结。该目录只做源字节、帧序号、PTS 原点与 Decord 时间表的身份检查；不运行模型，不读取比赛 JSONL 或标签，不显示/导出帧图像，不转码或改写比赛源媒体。FFprobe/Decord 在内部可能解码像素，报告不声称“没有内部解码”。

## 修复结论与合同

官方当前输入/输出说明要求原视频帧序号 `frame >= 0`，没有明确 timestamp 原点。以下是**本地源帧身份合同**，不是新增官方要求：

- 源帧身份为原视频展示/解码顺序的索引 `i`，不能用 `round(rawPTS * fps)` 反推出身份。
- `source_relative_PTS[i] = rawPTS[i] - rawPTS[0]`。移除的只能是同一源、同一字节身份下经证据绑定的常数原点。
- FFprobe 的全部整数 `best_effort_timestamp * stream.time_base` 必须存在，并与全部文本 `best_effort_timestamp_time` 相符；不以文本猜补缺失整数。
- 整数 `stream.start_pts * time_base`、文本 `stream.start_time`、首帧 raw PTS 必须相符。缺失/无法绑定则阻断。
- Decord 的**每一帧** start/end 数值均读取；全部 starts 必须绑定到 raw PTS 或 source-relative PTS 的一种已确认时钟。首、早期、中、尾代表点只作报告摘要，不代替全帧比较。
- 均检查帧数、几何、注册 fps、严格单调、有限数值、区间合法性，以及全部帧时间的旧 CFR 兼容门 `abs((PTS-firstPTS)-i/fps) <= 1/fps + 1e-6`。该一帧容差未改。
- 时钟绑定另用一 stream tick / float 表示误差界，raw 与 relative 分别按各自数值量级计算。精度不足以区分半帧，或非零原点同时能匹配两种时钟时，失败封闭；该界不是质量阈值。
- 成功后，冻结 A 继续用相对源帧零点的 `i / registered_fps` 与原帧索引抽取。不改 A 历史提示词、空间、段数、空输出或模型合同。

上一份 WIP 已正确提出常数原点和保留一帧门，但仅绑定 7 个 Decord 点、未知 stream start 可通过、缺整数 PTS 可退到文本，且用 raw 量级计算 relative float 容差。收尾版分别补齐全帧绑定、未知/缺失证据阻断和两种时钟的独立表示误差界。复制的 `a_contract.py`、`vendor/p2j_core.py` 与其锁保持原字节。

## 冻结与实际本地验证

`source_lock.json` 绑定三份生产源码。扫描启动前复核该锁及 `dependency_lock.json`；扫描期间不得修改生产码/锁。每份正式 receipt 记录源码、锁、FFprobe executable SHA-256，以及 Python/Decord 版本、实际 worker 参数。

本地 `cpu_numeric_tests_02.json`：**26/26 PASS_CPU_NUMERICAL_ONLY**，含：

- 942 帧、30 fps、0.046 s 原点与毫秒量化；旧 raw-zero 门拒绝，新源相对合同通过；raw/relative 两种 Decord 时钟及零原点。
- 分数 fps、负/大 raw 原点；大原点不放大 relative 绑定容差。
- 超过旧一帧门的 VFR/错误 fps 漂移；旧一帧边界仍通过。
- raw/Decord 缺失、NaN、重复、计数错误、非代表点坏时间戳、坏 interval end、未知表示精度及 stream metadata 错误。
- native worker 失败与坏时间戳后的完整 **426/426** 分母、426 条逐源失败/成功证据；最后一条仍扫描。
- 生产和复制依赖源码 SHA 检查。

`cpu_numeric_tests_01.json` 是保留的首次测试：一处测试断言忘记考虑 1/16000 stream tick。修改测试断言后重跑通过；两份 receipt 的生产源码 SHA 相同。

本地缺少 Decord 和 FFmpeg/FFprobe，因此**尚未执行真实解码器的合成媒体验收，尚未在本地扫描实际 426 条比赛源**。AST 与 CLI help 已通过。主控负责远端部署、CPU 扫描和验收。

## 部署与复现（主控执行）

只使用已验证 Decord 0.6.0 的现有 `qwen3vl_isolated_20260910` 环境。FFprobe 使用已有 Andy binary；不要安装环境或改变系统配置。传输遵守 Mac mini 中转规则。至少部署：三份生产源码、两个锁、`a_contract.py` 和 `vendor/p2j_core.py`。可以一并部署本目录两个测试入口及文档。

```bash
RUN=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
PTS="$RUN/baseline_pts_v3"

"$PY" -B "$PTS/test_origin_cpu.py" --output "$PTS/cpu_numeric_linux_01.json"

"$PY" -B "$PTS/scan_source_origin.py" \
  --manifest "$RUN/baseline_a/m0_finalize_01/clean_manifest_426.json" \
  --expected-manifest-sha256 57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32 \
  --output-root "$PTS/scan_01" \
  --ffprobe /home/inspur/anaconda3/envs/Andy/bin/ffprobe \
  --source-timeout-seconds 900 --decord-num-threads 0
```

`PY` 上述完整路径需以主控实际已验证环境位置为准；不因路径不符换到未经验证的解释器。`decord-num-threads=0` 使用库自动线程，不设置写死 CPU 环境。每个源顺序独立 worker，原生崩溃/超时记为失败后继续其余源。源字节扫描前后 SHA-256 均复核。每源硬上限 900 秒只用于失败隔离，FFprobe 子任务 600 秒；全量入口只对固定 M0 SHA 和 426 白名单记录开放。

可选真实解码器自检仅生成 3 个 64x64、2 秒黑色合成 MP4（共 180 帧），无比赛素材；另在其 numeric 副本改变一个非代表点时间戳。它不改冻结生产码：

```bash
"$PY" -B "$PTS/test_decoder_synthetic.py" \
  --output-root "$PTS/synthetic_decoder_01" \
  --ffmpeg /home/inspur/anaconda3/envs/Andy/bin/ffmpeg \
  --ffprobe /home/inspur/anaconda3/envs/Andy/bin/ffprobe \
  --decord-num-threads 0
```

黑色 CFR 零原点和 0.046 s 原点应通过；实际编码的 VFR 时间缺口和修改后的非代表点 start 应被拒绝。没有既有 FFmpeg 或 codec 就记录阻塞，不安装或猜测通过。每个合成生成命令限制 60 秒，全部产物限本目录新证据根。

## 成功与停止标准

仅当全体 **426/426** 完整扫描、每源字节身份/整数 PTS/stream 原点/Decord 全帧绑定/旧 CFR 门均通过，最终 exit 0，状态 `PASS_CFR_WITH_LEGACY_ONE_FRAME_TOLERANCE`，才生成 `clean_manifest_426_pts_origin_v3.json`。记录本身（ID、路径、hash、几何、fps、比例、范围）不变，只附加 input_contract 的身份 receipt 和 origin registry。

任一源失败，仍保留全部分母、`records/<id>.identity.json`、worker log 和可用 numeric 证据，最终 exit 4，状态 `BLOCK_SOURCE_ORIGIN_IDENTITY`，**不生成准入 manifest**。不删除失败、不放宽容差、不静默转码、不直接以旧 PTS 结果代替本次源身份。进程被中断时逐源证据仍在，但没有最终完整 receipt，不能认定通过。

即使成功，receipt 的 `inference_allowed=false`；模型自动推理仍需主控单独核验阶段准入。该工具不修改正式训练/测试授权，不代替已完成 908 条历史 train PTS 审计，不扩大训练、不上传提交。
