# 共享 8B 后置查询头：工程入口

当前交付状态：**10/10 CPU 逻辑测试、7/7 正式入口拒绝测试、8/8 成本合同测试通过；真实 processor 和 4 秒合成 8B 工程探针 02 已通过。**证据为 `../controller/processor_preflight_02/processor_preflight_report.json` 与 `../controller/probe8b_02_report.json`。`train_dense.py` 已准备，当前正式 C 二分类因缺少可信观察与负监督语义而保持 `STOP_C_FORMAL_BCE_UNKNOWN_NEGATIVE_SEMANTICS`；Linux 拒绝验收证明 `started_runtime=false`。新 32 秒真实非测试成本入口已完成 CPU 预检，尚待主控真实运行。以上状态均不代表模型质量或官方提分。

仅新增本 `dense_head/` 目录文件，未修改旧代码、旧 adapter、数据、报告或提交包。源码已只读核对训练机 transformers 4.57.1 的 `modeling_qwen3_vl.py`、`processing_qwen3_vl.py`；旧 R7 视频 processor 入口只作调用约定参考。

## 模块与硬门

- `dense_time.py`：现有词表普通字符串 ` [GRID_QUERY_00]\n` 等固定编号查询，全部放在窗口完整视频之后。每个查询的读取位置由实际 processor 展开后的 `input_ids` 唯一子串匹配决定，读取查询字符串的最终 token；尾换行固定 Qwen 标点与换行的 BPE 上下文。缺失、重复、位于视频之前、padding 命中均报错；不增加 token/embedding。
- 时间 forward 直接调用 `get_base_model().model`，只取得最终 `last_hidden_state`，先取查询位置再送入 FP32 的共享 `4096→128→1` 头。明确关闭缓存、全层 hidden_states 和 attentions，完全绕过 LM head；真实探针还在 LM head 注册禁止前向的 hook。
- 精确匹配 `model.language_model.layers.*.self_attn.{q,k,v,o}_proj` 注入 rank16 LoRA，视觉与基座参数冻结。工程配置 alpha32/dropout0.05；仅 `use_reentrant=False` checkpoint，不用 embedding-grad hook掩盖冻结输入断梯度。不得 `modules_to_save`、扩词表或 merge。
- 实际 `numel` 按同一 Parameter 对象去重，记录共享别名。硬门为基座 **8,767,123,696**、LoRA **15,335,424**、头 **524,545**、全链 **8,782,983,665**，且不超过十进制9B。实际加载不一致立即失败，不用量化字节数替代参数数目。
- `grid_targets.py`：输入同一源 PTS 坐标上的完整连续源帧、二值弱帧状态以及明确观察区间。完整可观察格的 target 为格内源帧二值标签平均；观察边缘、padding、空格或任何 UNKNOWN 帧使整格 mask。观察本身不把未选帧推断成负例。提供格→源帧编号/PTS回放。
- BCE 先以 boolean mask 索引，再计算已知格损失；累积批次统一除以整个批次已知格数量。全 UNKNOWN 批次不 forward/backward，不调用 optimizer/scheduler，不增加有效 steps/known_cells 计数。
- 3–5 次真实有效更新，检查 head/LoRA B 首步梯度与实际变化，以及 LoRA A 后续非零梯度和变化。首步 LoRA A 可因 LoRA B 零初始化而为零，这不能作为断梯度结论。所有冻结基座与视觉参数按小块逐字节 SHA256 比较。
- 固定输入仅改 masked label，要求 loss 与全部 trainable gradients 逐元素相同。probe 01 的默认 CUDA SDPA 同标签重复梯度也不相同；probe 02 使用 `SDPBackend.MATH`、严格 deterministic algorithms 和相同 RNG 通过逐元素检查，不能放宽 tolerance。视频错配诊断保持 input IDs、时间和几何不变，仅替换真实 processor 得到的合成视频 pixels；查询 logits 应有所变化。这只检验视觉敏感性。
- `spatial_base()` 使用同一基座的真正 `disable_adapter()` context，禁用时间头，清除外部缓存和 Qwen 的 `rope_deltas`，禁止合并 adapter。真实探针对照注入前原始基座的最后一个 token logits及3 token greedy output，均要求逐元素一致。空间测试期间 head 前向被 hook 禁止。

## 本机已验证

在现有 Windows `E:\conda\python.exe` / torch2.5.1+cpu 执行：

```powershell
python test_cpu.py
python -m py_compile dense_time.py grid_targets.py probe_8b.py processor_preflight.py test_cpu.py
```

`cpu_test_report.json` 状态为 `PASS_CPU_LOGIC_ONLY`：10项覆盖查询展开索引与拒绝条件、524545头参数、源帧/观察边缘/UNKNOWN/padding、masked label loss/gradient不变、累积已知格分母、全 UNKNOWN 跳过、非reentrant冻结输入下3次LoRA/head更新与基座冻结/恢复、共享参数计数与拒绝merge，以及下载中元数据receipt/完整模型准入/路径绑定/文件篡改拒绝。CPU toy 模块不替代真实 Qwen、真实 tokenizer 或真实 GPU 验收。

## 训练机运行

主控先完成既有共享资源、身份、80GiB新增磁盘与GPU记账/排队准入。本模块不启动远端、不下载、不安装、不抢占。运行环境使用既有隔离环境，要求 transformers4.57.1 / peft0.17.1；权重只允许 `local_files_only=True`，固定 revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`。

```bash
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
RUN=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z
$PY "$RUN/dense_head/processor_preflight.py" \
  --model-dir "$RUN/models/Qwen3-VL-8B-Instruct" \
  --model-receipt "$RUN/controller/model_download_v2_status.json" \
  --out-dir "$RUN/dense_head/processor_preflight"
$PY "$RUN/dense_head/probe_8b.py" \
  --model-dir "$RUN/models/Qwen3-VL-8B-Instruct" \
  --model-receipt "$RUN/controller/model_download_v2_status.json" \
  --out-dir "$RUN/dense_head/probe8b" --engineering-only --updates 3
```

若 Linux 的 run 根目录不同，主控替换 `RUN`；不从本地目录名推断远端路径。两个入口均拒绝覆盖非空输出。修复复跑使用新的输出目录，保留失败报告。

模型receipt兼容主控 `model_download_v2_status.json`：`repo/revision/model_path/completed[{name,bytes,sha256,official_content_hash,verification}]`；实际8B加载必须 `status=COMPLETE_HASH_VERIFIED`，独立核文件字节与SHA256并复核官方 LFS SHA256或Git blob SHA1。processor-only允许权重尚未下完，但其所用 config/tokenizer/preprocessor 元数据必须已经逐文件核验。另兼容完整 `{repo_id,revision,files[{path,sha256,size_bytes}]}` receipt。

processor preflight在CPU实际处理8帧合成视频，核4个查询、真实展开位置、源frame indices/fps→temporal merge时间、时间文字0.1秒舍入、真实padding17 token后的索引偏移关系及实际截断拒绝。不会载入模型权重、调用GPU或读取比赛媒体。

真实8B探针只用8帧224×224、4秒/4格合成输入，3更新各2 microbatch；这是工程成本，不能换算成32秒窗口、完整视频、真实训练或空间链端到端成本。成功才写 `PASS_REAL_8B_SYNTHETIC_ENGINEERING_ONLY`；任何失败保留 `probe_report.json`，返回非零。保存的 `synthetic_adapter/` 和 `synthetic_head.pt` 明确为合成探针产物，禁止作为正式模型或候选。

## 固定 32 秒真实非测试成本

`cost_probe.py`、`cost_config_32s_v1.json`、`cost_admission_32s_v1.json` 是单独工程入口。只允许 frozen8 清单第一条 `qvh_000056_9x16` 的完整来源视频 source-relative `[0,32)`，不用旧 A 的 `138.089–143.649` 短 scope。64 个样本按原生 PTS 选择，16 个 2 秒 query，max_pixels=131072，3 次真实更新；标签仅按格编号交替生成 0/1，不读取 train/dev/confirm 语义标签或比赛视频。正式 epochs/steps 模板继续为 null、admission 为 false。

仅对该固定源运行 ffprobe `best_effort_timestamp/pkt_duration`，核3750帧、150秒、25fps、534×300、零原点与真实连续时长；timestamp 用原生整数 PTS × 有理 time_base，禁止 avg-fps 合成时钟或默改原点。torch CUDA 初始化后才导入 Decord，核所选64帧 IDs/PTS、几何和每帧 RGB SHA256，并在重复解码时要求哈希相同。复用 `train_dense.prepare_window` 与 `exact_pts.exact_source_pts`，不重跑908条审计。

本机预检：

```powershell
python test_cost_cpu.py
python cost_probe.py --config cost_config_32s_v1.json --admission cost_admission_32s_v1.json --plan-only --metadata-root ..
```

预检不加载 torch/模型/decoder，不读取媒体。主控把 `cost_probe.py` 及依赖 `formal_contract.py / exact_pts.py / train_dense.py / dense_time.py / probe_8b.py / grid_targets.py` 复制到独立 `dense_head_cost_v1/`，连同固定 config/admission 部署。真实 CLI 由既有 `controller/gpu_run.py` 包装并核实时资源、容量与共享账本：

```bash
$PY "$RUN/dense_head_cost_v1/cost_probe.py" \
  --config "$RUN/controller/c_cost_32s_01.config.json" \
  --admission "$RUN/controller/c_cost_32s_01.admission.json"
```

主控实时核验发现模板中的 `/usr/bin/ffprobe` 不存在，已在上述独立运行 config 中将唯一 binary path 改为已确认的 `/home/inspur/anaconda3/envs/Andy/bin/ffprobe` 并重新绑定 admission SHA256；模型、窗口、采样和更新协议不变。原 `cost_config_32s_v1.json` 留作 CPU 合同模板，不直接当此次 Linux 命令配置。

固定输出为 `dense_head_cost_v1/cost32_01/`，即使旧目录为空也拒绝复用；修复复跑必须新登记 run_id/out_dir 并重新绑定 config SHA256。1800秒为本次作业停止条件；8192 token 为实际 processor 展开后的长度上限，超长或 OOM 直接失败保留证据，不缩帧/降像素重试。`decoder_threads=0` 沿用 Decord 自动选择，不改全局 CPU 线程设置。

报告拆分模型/processor加载、解码、预处理、像素哈希、query合同与传输、每步 forward/backward检查/optimizer、单次时间推理和空间 signature 耗时，附显存、token、实际参数数目、基座/视觉字节哈希及真正 adapter-off 恢复。失败阶段即时保存 `cost_probe_report.json`；准入或旧输出拒绝时完整 JSON 写 stdout，供 controller 日志保留。该入口不保存 checkpoint。32秒成本使用默认 SDPA，复用 probe02 已通过的严格 UNKNOWN 门，不声称重新完成32秒 MATH invariance。

空间测量只有同一窗口/query prompt 的 raw-base 最后 token logits 与3个 greedy token恢复 signature，没有正式构图提示词、锚点循环或裁剪输出；**不能称为 production crop throughput**。尚未验收：32秒真实媒体/PTS与成本、完整视频及426条吞吐、许可与负语义、正式校准/训练/评估、426条输出完整性和官方分数。正式数据门保持停止。
