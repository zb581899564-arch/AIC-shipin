# 复赛 A：冻结 4B/P2-T2 基线执行入口

状态：**本地 CPU 合同、历史输出重放和独立严格封包已通过；新 Linux 模型 E2E 尚未通过。** 主控实际尝试 02 在权重加载前 SIGSEGV，61.2587 秒按其账本保留；尝试 03 的导入均通过，首次 CUDA init 报 `random_device could not be read`，未到 tiny alloc/model load。当前入口先完成 torch/CUDA 初始化再导入 Decord，交主控验证加载次序假设。此子任务没有运行 GPU、连接远端、下载、读取复赛内容或上传。

职责只覆盖此新目录。历史媒体、adapter、报告和代码只读；`vendor/` 是逐字节复制的原冻结源，其来源和 SHA-256 见 `vendor_lock.json`。主控负责实时资源、GPU 排队、Linux 部署/执行、阶段准入和最终验收。

## 冻结链与输入

时间：`Qwen3-VL-4B-Instruct` + P2-T2 最终 adapter。空间：相同基础权重、不加载时间 adapter 的独立进程。A 是一个共享基础架构加 LoRA 的完整配方；逻辑参数量在加载时按唯一参数对象计数，量化不减参数数量。本入口不加载 8B、OraRL、辅助头或旧测试框。

- 4B：`/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct`，五个基础文件哈希见 `config_a.json`。
- adapter：`/home/inspur/aic_video_work/round6_score_alignment/p2t_temporal_improvement/round6_p2t2_equal_exposure_20260920T1555Z/runs/full_epochs5/adapter`。
- adapter SHA-256：`c9bf3754a05a42d69ee8c4d11f56c41346d927094fd643863f0cb55626b8e6a0`。
- 原共享时间代码：`/home/inspur/aic_video_work/temporal_round5/scripts/temporal_common.py`，`bb8f47896e20e069e9ddf992d94488132ccbee46dc850a2658851f4aa52946b4`；当前使用本目录相同字节的 vendor 副本。
- 原空间代码：`/home/inspur/aic_video_work/inference/baseline_qwen3vl.py`，`a522244712831e7fddc605bce73b083851b7353dac1ceb2a9e4f41b948733631`。
- 非测试清单：`inputs/non_test_frozen8.json`，SHA-256 `7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a`。
- 配方：`config_a.json`，SHA-256 `137a60e3efae567794105bac8d2fcb4288c7d1b289ab4ad1d0a81e2ba11c5414`，入口直接核对此哈希。

非测试使用历史 P2-J 的八个独立来源、原 clip 边界、媒体 SHA-256 和源几何/timebase。仅包含元数据，不加载教师标签、ROI、文字或确认集。八条都是 9:16，不能据此声称真实 16:9 构图质量通过。其历史使用依据在清单中如实继承，许可证和教师语义的进一步审核由主控的数据审计负责。

复赛完整源使用 30 秒不重叠窗，每窗最多 64 采样帧，131072 pixels/帧，256 个生成 token，确定性生成。尾窗不足 0.2 秒沿用旧链省略行为。旧提示词和 parser 保留 1–5 段、非空约束、原宽松 JSON 提取及 overlap warning 行为；**A 不支持已验证的合法空**。任何推理失败、解析失败或空输出均保留原始记录并阻断候选，改掉旧链“最多 5% 无效窗口后跳过”的工程风险，不以失败构造空预测。

非测试回归严格继承 P2-J 的 `ceil(clip_start*fps) + ceil(local_time*fps)`、半开端点；复赛完整源继承 P2-Final 的 `ceil(absolute_time*fps)`、半开端点。这两个旧入口在非整数 clip 起点存在差异，未把它们合并成新规则。

空间继承旧完整配方：选中源帧不连续时开启镜头；HSV Bhattacharyya >=0.35 或灰度 MAD >=0.18 开启新镜头；每个镜头首尾锚点、最大 8 帧间距；锚点 pixel SHA 与模型实际解码逐帧绑定；仅同一镜头内整数线性插值。没有跨镜头复用、中心回退或旧框填补。当前 A 的锚点日程依赖选中 run，是历史基线行为；C 的源时间固定空间场是另外的方案，不能写成 A 已采用。

## 主控 Linux 非测试 E2E

将本目录完整同步到新的 `/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/.../baseline_a`。传输遵守 Mac 跳板约定；不要复制旧媒体或重建模型环境。CPU 静态入口不需要模型依赖；GPU 使用现有 Qwen 环境。

每个实际新尝试使用不同 run_dir。以下变量只用于命令示例：

```sh
A='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/baseline_a'
R="$A/runs/a_non_test_e2e_UNIQUE"
M="$A/inputs/non_test_frozen8.json"
S='7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a'
PY='<现有Qwen环境的python绝对路径>'
"$PY" -B "$A/run_a.py" --stage preflight --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
```

主控为该实际 run_dir 填写 `admission_TEMPLATE_DO_NOT_RUN.json` 的独立副本，登记 `A_NONTEST_E2E`、当前资源通过、共享 GPU 排队批准、新增磁盘同时存在峰值 <=80 GiB，以及同一个清单哈希。模板所有授权/资源字段默认 false，不能直接运行。

`temporal`、`spatial` 分别由主控共享资源 wrapper 启动；每个 GPU job 的 max-seconds 基于非测试实际峰值和耗时登记。入口核验共用 `improvement_round1/active_gpu_job.json` 的 runner_pid/child_pid 是当前进程祖先，因此兼容主控新 `gpu_run.py`，不限定 wrapper 文件名，也不改账本或固定 OMP 线程。

```sh
# temporal 由主控 gpu_run.py 包裹以下命令，并设置 PYTHONFAULTHANDLER=1。
"$PY" -B "$A/run_a.py" --stage temporal --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R" --admission '<主控实际admission.json>'
"$PY" -B "$A/run_a.py" --stage select --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
"$PY" -B "$A/run_a.py" --stage shots --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
"$PY" -B "$A/run_a.py" --stage anchors --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
# spatial 也由主控 gpu_run.py 单独包裹。
"$PY" -B "$A/run_a.py" --stage spatial --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R" --admission '<主控实际admission.json>'
"$PY" -B "$A/run_a.py" --stage compose --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
"$PY" -B "$A/run_a.py" --stage package --manifest "$M" --expected-manifest-sha256 "$S" --run-dir "$R"
```

所有输出 exclusive-create；失败不覆盖，重试使用新 run_id。锚点解码身份失败时阻断，不自动换算法或静默补框；主控可沿既有 P2-Final 修复方案单独登记身份修复，保留之前的有效对象和全部失败。

成功标准：8 条来源均完成真实 temporal+spatial；所有窗口有效；exact selected/shot/anchor/provenance/frame coverage；同帧身份、比例/坐标和资源账通过；独立严格 loader 和仅含 predictions.jsonl 的 ZIP CRC/字节回读通过。工程通过不代表弱指标或官方提分。

## 复赛 M0 和独立 PTS 门

主控于 2026-10-05 当前官方页复核 `targetRatioWH` 的算法输入用途；第一 `0.jsonl` 仅含此 array key。该实时证据由主控保存在 `controller/input_role_approval.json`。主控第一 M0 尝试全部 426 条 keys/type 已通过，提取了三个视频，随后旧 metadata equality 门拒绝第三条；失败及 partial 保留。当前版本改为只记录 fps/start 歧义，另开新 M0 根完整执行，未添加 resume、覆写或旧媒体复用功能。

`inspect_first_jsonl.py` 只开 1 个对象的键/类型；`prepare_rematch_m0.py` 才执行新获准的 426 条元数据读取。M0 每条先检查全部键与类型，允许 `targetRatioWH` 及可选字符串 `video_id`；未知/疑似标签键在消费字段值之前停止。通过后才解析这两个获准值：一行一对象、无第二行、ratio 只能 [16,9] 或 [9,16]，video_id 若存在必须与原 archive stem 原样相同。`000` 不会改成 `0`。任何失败停止后续读取，保留失败，不使用剩余条目凑数。

主控 approval 文件字段：`status=APPROVED_METADATA_ONLY`，`archive_sha256=8e4aa94f19c4e495952300ae19d37019fea4d2cbb3237120934c6b8d546c28e3`，`allowed_keys=["targetRatioWH","video_id"]`，三个布尔 `allow_jsonl_metadata_values`、`allow_video_extraction`、`allow_ffprobe_metadata` 均为 true，附官方用途证据字符串 `official_target_ratio_evidence`。

```sh
"$PY" -B "$A/prepare_rematch_m0.py" \
  --zip '/home/inspur/aic_video_work/round6_score_alignment/rematch_intake/rematch_download_20261005T041135Z/archive/复赛-基于视频大模型的通用视频高光剪辑.zip' \
  --approval '<controller/input_role_approval.json>' \
  --output-root '<全新M0目录>' \
  --ffprobe '/home/inspur/anaconda3/envs/Andy/bin/ffprobe'
```

全体元数据通过后才提取视频。仅 MP4、原 stem 对应、逐字节 SHA-256/ZIP CRC，不提取 JSONL、`__MACOSX`、`.DS_Store`、脚本或未知文件。仅新输出根；禁止覆盖已存在目录。ffprobe 读取尺寸、平均/名义帧率、frame count；必要时 count-only 自动内部解码，不显示/导出图像。名义与平均帧率不同、非零或未知 start_time 仅记 `timebase_flags` 和 `require_full_pts=true`，交独立实际 PTS 门判断，不用 fps 字段相等替代时间身份。M0 输出 `clean_manifest_426.json` 与独立 keys/type、媒体元数据和 receipt；它仍标记 PTS 未验收，不能直接启动复赛 A。

`prepare_full_pts.py` 是分开的自动源时间身份入口，不自动从 M0 启动：

```sh
"$PY" -B "$A/prepare_full_pts.py" --manifest '<M0/clean_manifest_426.json>' \
  --expected-manifest-sha256 '<M0 receipt哈希>' --output-root '<全新PTS目录>' \
  --ffprobe '/home/inspur/anaconda3/envs/Andy/bin/ffprobe'
```

它只保存实际 PTS 元数据，复核字节/帧数、单调性、零点和旧协议一帧容差，不显示媒体、不读取标签、不运行模型。ffprobe 的 frame metadata 扫描可能内部解码；当前报告的 `pixels_decoded_or_displayed=false` 应解释为没有导出/显示帧图像，正式归档宜更名为 `media_images_exported_or_displayed=false`。全部通过生成 `clean_manifest_426_pts.json`。复赛 A 仍需主控登记 `A_REMATCH426_INFERENCE` admission，先时间作业，按真实选中帧和锚点重新登记空间资源；不得上传。

## 实际本地验证与限制

`cpu_tests.json`：24 项全部通过，覆盖 unknown role/清单标签字段/重复 ID/漏视频/解析失败/空输出/重复锚点/同帧哈希变化/非法坐标/漏镜头帧/重复最终帧，以及键名值前停止、路径穿越、重复/不配对归档 stem、额外 JSONL 行、非法比例、video_id 不符和前导零保留。

`cpu_legacy_replay/`：本地真实调用新 `run_a.py` 的 static preflight、select、compose、package；使用既有非测试时间/镜头/锚点输出，没有重新推理。396 选中源帧与历史集合完全相同，68 锚点；完整 provenance SHA-256 `1ea2d03078c517ed9c61d8172e5d1f3433191d8d72b7ea6f70b90b4f111b547e` 与历史逐字节相同。新官方预测只移除历史 dev 每帧的额外 source 字段，frame/bboxes 保持相同。独立严格 loader 11 项检查全通过，0 issues、0 missing/extra/duplicates。此 8 视频 ZIP 只用于回归，不能充当 426 视频复赛候选。

运行入口已通过 AST 语法解析。当前诊断时间入口 SHA-256 `3a3baea17c9eeb357d582945d7da789248773b12e2b4deae56347937f57d2202`，次序 torch→CUDA init/tiny alloc→Decord→PEFT→Transformers；这是主控批准的次序验证，不改 science config。当前 M0 入口 SHA-256 `a0f32803c779a4c112dbff094d373be9ad2f1732f95b46a6fbb73cde72ec2158`。`cpu_probe_flags_tests.json` 的三个合成 probe 用例通过：fps 不同、start 非零、nominal/start 未知均保留 PTS pending。

未完成：新真实 GPU E2E、实际 A 参数与峰值证据、426 M0/PTS 实际执行、复赛完整推理/验证/封包、官方成绩和上传授权。没有把 CPU 重放、启动或格式成功写成提分成功。内部评分器继续是 `INTERNAL_SPEC_REIMPLEMENTATION`。
