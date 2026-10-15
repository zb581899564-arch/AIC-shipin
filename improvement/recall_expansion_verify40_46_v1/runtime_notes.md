# 小试运行接口

仅新增 B0/VERIFY 实现。代码未启动 SSH、媒体处理、模型、GPU 或数据下载；本地语法与合成检查不能证明真实 CPU/GPU 准入或模型质量。

Linux 实际运行根目录 `--root NEWROOT` 必须位于 `/home/inspur/aic_video_work` 下。`--group` 为 `dev` 或 `confirm`。每个阶段输出目录只允许首次创建；失败保留全部已成功证据，不自动恢复、不重复成功调用，不把工程失败改成 UNKNOWN 或空结果。主代理另行通过现有共享 GPU wrapper 发起两个独立作业，没有自动 launcher。

```text
CUDA_VISIBLE_DEVICES=0 python pilot_runtime.py infer  --root NEWROOT --group dev
python pilot_runtime.py replay --root NEWROOT --group dev
python pilot_verify.py prepare --root NEWROOT --group dev
# 主代理独立验收并冻结 source_lock_dev_VERIFY.json 和 GPU admission 后：
CUDA_VISIBLE_DEVICES=0 python pilot_verify.py infer  --root NEWROOT --group dev
python pilot_verify.py replay --root NEWROOT --group dev
```

CPU 的 `prepare`/`replay` 入口仅清空自身 `CUDA_VISIBLE_DEVICES`；GPU 入口要求父进程保留显式非空 CUDA。开发完成后按独立冻结方案第一次执行 `confirm`，不要求现在准备确认组。

`--cpu-acceptance`、`--source-lock` 可覆盖默认路径，但必须与阶段 admission 的路径和 SHA 一致。B0 默认 `cpu_acceptance_GROUP.json`、`source_lock_GROUP_B0.json`。VERIFY `prepare` 仍读取这两个 B0 文件；VERIFY `infer/replay` 默认读取 `GROUP/VERIFY/cpu_01/completion.json`、`source_lock_GROUP_VERIFY.json`。

## 主代理提供的 B0 CPU 验收

`cpu_acceptance_GROUP.json`：

```json
{
  "status": "PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION",
  "group": "dev",
  "CPU_only": true,
  "CUDA_initialized": false,
  "new_model_calls": 0,
  "new_optimizer_updates": 0,
  "entries": [{
    "case_id": "actual_case_001", "group": "dev",
    "input_path": "/absolute/input.json", "input_sha256": "64hex",
    "proof_path": "/absolute/cpu_input.json", "proof_sha256": "64hex"
  }]
}
```

每组 `entries` 只包含该组全部实际唯一输入，不把共享 baseline/overlap 视图重复计入调用预算。metadata 必需原字段 `case_id/source_path/source_name/source_sha256/window_start/window_end/source_total_frames/all_source_exact_pts/physical_end_exact/source_frame_ordinals/sample_exact_pts/pixel_sha256/frame_array_path/frame_array_sha256/audio_observed=false/reference_available_to_inference=false`，以及 `window_role=baseline|overlap`。可带 `view_roles=[baseline,overlap]` 记录共用实际视图，baseline 优先作为 `window_role`；原生时钟要求归一化、严格递增，64 个不同真实样本逐项对上原 PTS，窗口不超过 30 秒。

proof 必需 `status=PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT`、`CPU_only=true`、相同 `case_id/source_name/input_sha256`、`input_tokens`、`encoded_tensor_path/sha256`、`encoded_tensor_format=TORCH_SAVE_GZIP_LOSSLESS_LEVEL1` 和 `input_evidence`。evidence 沿用原 `runtime.encode`：`case_id/source_sha256/source_start/source_frame_ordinals/sample_exact_pts/pixel_sha256/physical_frames=64/prompt_sha256/tensor_signature` 及原生 processor 证据。输入 token 上限 16384；B0 精确沿用原 EMPTY_PROMPT、allow_empty grammar、256 输出 token。

## 独立 GPU admission 与不可变 lock

`gpu_admission_GROUP_STAGE.json`（STAGE 为 `B0` 或 `VERIFY`）：

```json
{
  "status": "PASS_INDEPENDENT_RECALL_GPU_ADMISSION",
  "group": "dev", "stage": "B0",
  "expected_input_count": 1,
  "gpu_job_name": "unique_registered_job",
  "deadline": "2026-10-14T23:00:00Z",
  "cpu_acceptance_path": "/absolute/cpu_acceptance_dev.json",
  "cpu_acceptance_sha256": "64hex",
  "source_lock_path": "/absolute/source_lock_dev_B0.json",
  "source_lock_sha256": "64hex",
  "source_scope": "EXTERNAL_NONTEST_ONLY",
  "model_parameters": 8782459120, "optimizer_updates": 0,
  "reference_available_to_inference": false
}
```

`source_lock_GROUP_STAGE.json` 为 `{"files":{"/absolute/file":"64hex"}}`。不要在原锁后追加改写；VERIFY 新 token/proof/request 使用独立锁。锁须包含 `model_common.code_files()`、`runtime_dependencies()`、`processor_assets()`、原 config、该阶段 CPU 验收和所有实际 input/proof/source/RGB/cache。准备 VERIFY 前 B0 锁也须包含既有 `CV_CODE/cv_contract.py/cv_grammar.py/cv_tokens.py`。`runtime_dependencies()` 仅枚举既有实现目录 `.py` 文件，不扫描模型权重字节；模型加载后实际 base/adapter identity、8782459120 参数及全 144 TIME LoRA 层 enabled/frozen 仍逐项检查。

VERIFY 锁另外绑定 CPU completion 中 `bindings` 指向的 B0 CPU 验收、B0 source lock、B0 admission、B0 GPU completion、B0 replay completion，`requests.json`，全部新 request/proof/token cache，原 B0 input/proof/done/replay 与视觉 cache。CPU completion 的 `entries` 已直接提供上述新 request/proof 路径和 SHA。GPU 运行检查 `active_gpu_job.json.name` 精确匹配；独立 replay 只在自然 `resource.status=completed/exit_code=0` 且共享 ledger 对该 job 恰好一行、对象与 resource 一致后执行。

## 输出与合并边界

B0 输出 `GROUP/B0/gpu_01`、首次独立 `GROUP/B0/replay_01`；VERIFY 输出 `GROUP/VERIFY/cpu_01`、`gpu_01`、首次独立 `replay_01`。每阶段保留 launch claim、调用 attempts、request/raw/done、failure 或 completion。B0 replay 是新输入首次独立 RGB/native processor/tensor/token/grammar/parser/native membership 检查；VERIFY prepare/replay 只复用原视觉，不重新解码媒体或编码视觉。

VERIFY 对全部 B0 原始 segment 确定 event denominator 后才准备全部 prompt-only token cache。使用既有 candidate_verify_v2 精确 contract/grammar/retarget，不做 D8 padding。合法 B0 全空时 CPU prepare 可输出零事件 completion，并明确要求不启动 VERIFY GPU 作业。

最终 `GROUP/VERIFY/verification_export.json.events` 含 `source_name/source_sha256/event_id/original_case_id/original_segment_index/original_interval_exact/window_role/view_roles/original_native_range/decision_result/eligible_for_new_addition`。decision_result 保留 KEEP/UNKNOWN/DROP 及旧 contract 的 `candidate_kept` 语义；新增只看显式 `decision == KEEP`，UNKNOWN 不能据 `candidate_kept=true` 新增。baseline D8 时间 padding、源级全空保护及新 overlap 无 padding 由主代理冻结的评价/合并实现处理，runtime 仅导出原区间。
