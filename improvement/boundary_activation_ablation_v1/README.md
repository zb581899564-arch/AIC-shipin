本目录是新的 LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION，复用已完成 local_boundary_v2 smoke 的 start/end 两个完全相同输入和两个 TIME 回答，仅比较局部 native-index 边界任务的 adapter activation。代码未部署、未准入、未启动模型。

固定 ROOT：`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/boundary_activation_ablation_v1`。只有 `run_ablation.py --root ROOT --stage admit|infer|replay` 三个明确阶段；admit 是只读旧 proof/cache 的 SHA 与新 metadata admission，不调用 processor、decoder 或模型，也不授权 GPU。主控另冻结 protocol/source/code/唯一 job 和 gpu_admission，经既有共享 gpu_run.py 运行 infer，终态后再独立 CPU replay。CPU 子只隐藏自己的 CUDA，GPU child/parent 必须保持显式非空 CUDA。

原目录、7 份原 code、CPU cache、完整源/root input-lock 字典、TIME raw/request/done、GPU unique resource/ledger 与成功的两份独立 pixel/input replay 全部强绑定、不回写。旧 source/NPZ pixels 不再读或 encode，既有 gzip 张量不复制；原 source_input_lock 字典通过旧 gpu_admission 的 SHA 继承。admit/infer/replay 会读取并核所需既有 compressed cache SHA；infer 和新 output replay 只 load 已验缓存并检查原 tensor signature。新 output replay 只检查新 tokens/有限grammar/raw/native端点及 all144 states/weights/unique ledger，复用原成功输入 replay，不调用 runtime.encode/baseline_frames。

物理模型仍实际 8782459120 参数，基座激活参数 8767123696，adapter 15335424 参数仍加载；不把 disabled 称卸载或物理参数减少。加载原 frozen base/time adapter，枚举全144 LoRA 层：每次 context 前全部 disable_adapters=False，内部全 True，退出后全 False 且同 layer names；上下文前后用原 engine.frozen_identity/adapter_identity 对全部 frozen 参数及288 adapter tensors 核查。每次独立 generate/prefill，不提供跨 role past_key_values 或 prior output context；model.generate kwargs、prompt、frames、tokens、finite grammar、parser/UNKNOWN/冲突/exclusive end 都复用 frozen v2。raw 在 parser 和后续状态校验前保存；输入/模型/语法/绑定失败阻断，不转 UNKNOWN 或空候选，不重复任何成功调用。

原 B0 coarse 与 VERIFY 使用 TIME adapter 不变，旧 base-only12 coarse/F1 STOP、失败与费用不改。两个 TIME KEEP 并不证明 LoRA 妨碍边界；BASE 出更多 REFINE/changed 不算质量或选择依据。此2call只观察 activation 行为和预算，结果 UNKNOWN/KEEP 也照实保留。角色质量选择须另用冻结 Charades dev/reference 对应和 worker-disjoint confirm，覆盖 UNKNOWN/ambiguous/censored，不能挑 BASE 变化事件或按 GT 逐条择优。

主控在 ROOT 保存以下 protocol.json（字段必须填写实际值；不是运行授权）：

```json
{
  "schema":"LOCAL_BOUNDARY_ACTIVATION_ABLATION_V1",
  "hypothesis":"LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION",
  "validation_scope":"PAIRED_TWO_CALL_SAME_INPUT_ACTIVATION_DIAGNOSTIC",
  "source_root":"/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v2",
  "max_new_model_calls":2,
  "actual_physical_parameters":8782459120,
  "activated_base_parameters":8767123696,
  "disable_time_adapter_layers":144,
  "optimizer_updates":0,
  "new_input_processor_encodes":0,
  "new_media_decodes":0,
  "coarse_and_verify_time_adapter_unchanged":true,
  "old_base_only12_failed_status_and_cost_unchanged":true,
  "quality_gate_or_change_based_selection_admitted":false,
  "gpu_job_name":"NEW_UNIQUE_MAIN_RESERVED_NAME",
  "deadline":"2026-10-14T11:56:40Z"
}
```

ROOT/registration.json 字段：`schema` 同上、`status=FROZEN_TWO_EXISTING_BOUNDARY_SMOKE_INPUTS_FOR_ACTIVATION_ONLY`、`source_root` 同上、`protocol_sha256`、`official_rule_check_path/sha256`（规则小回执放 ROOT）、`code_files`（本3py的 exact Linux path/SHA）、`expected_source_code_files`（原 cpu completion.bindings.own_code_files 原7份path/SHA）、`prior_cpu_completion_sha256`、`prior_gpu_completion_sha256`、`prior_replay_completion_sha256`、`prior_model_identity_sha256`、`request_ids=["SMOKE_ORIGINAL_SCREEN_001.start","SMOKE_ORIGINAL_SCREEN_001.end"]`。admit 保存 source_lock.json 与 admission.json，全 `x` 创建，拒绝重复；不读参考/质量内容。

ROOT/gpu_admission.json 由主控独立审查后冻结：`status=PASS_INDEPENDENT_BOUNDARY_ACTIVATION_GPU_ADMISSION`、`source_lock_sha256`、`input_admission_sha256`、`actual_model_call_budget=2`、`gpu_job_name`、`actual_physical_parameters=8782459120`、`activated_base_parameters=8767123696`、`optimizer_updates=0`。此文件必须匹配实际共享唯一 reservation；本目录不提供 wrapper/后台启动器。

输出 GPU `BEGIN_MODEL_CALL/raw/done/ACCEPTED_MODEL_CALL` 2次分母完整后，独立 CPU output replay 保存两proof/completion和activation_behavior_export。导出只报告对应 TIME/disabled BASE decision、端点、generate时长/实际唯一 charged_seconds，`quality_gate_or_change_based_selection_admitted=false`。本目录不调用任何训练、评分、GT选择、正式426推理或封包。旧 smoke wrapper charged 83.02639091201127 秒包含模型加载/哈希等；本版本额外每call上下文前后完整 weight hash，需要主控按实测冻结总 GPU 秒预算，不能仅按原3.86/3.38秒 generate 时长估计整job。
