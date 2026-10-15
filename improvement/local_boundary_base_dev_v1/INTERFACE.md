# BASE 配对 driver 接口（代码交付，尚无实际作业）

Linux 代码目标：`CAMPAIGN/local_boundary_base_dev_v1/code/`。当前 dev 输出根为
`CAMPAIGN/local_boundary_base_dev_v1`；同代码可用于明确的 `/dev` 或 `/confirm` 子根，
各根独立注册与终态。确认只允许读取 metric08 已冻结的全局 BASE 选择后再执行。
所有实际部署、注册、source lock、独立 GPU 准入和 shared wrapper 均由主控负责。

入口：`driver.py infer --base ROOT`；CPU 新输出重放：
`driver.py replay --base ROOT`，后者只屏蔽该 CPU 子进程的 CUDA。
driver 不启动 wrapper，不准备或重放任何成功输入，不评价参考标签、不选择角色。

主控在 TIME 自然终态与首次输入重放全部成功后，可调用
`bd_io.source_bundle(V4_ROOT/'dev', 'dev')` 获取 `required_metadata_files` 与已验收
`rows/events/skips/denominators`。这个函数只读取 metadata/token 原回答；未完成的
TIME、首独立输入重放或共享 ledger 不返回。它不读取 RGB 数组、tensor cache 或媒体。

新根文件接口：

- `registration_01.json`：`schema/status` 均为
  `LOCAL_BOUNDARY_BASE_PAIRED_ROLE_V1` / `FROZEN_LOCAL_BOUNDARY_BASE_PAIRED_ROLE_V1`；
  `role='dev'`, `source_root=V4_ROOT/dev`, `events=20`，
  `nominal_endpoints=40`, `actionable_requests=37`, `structural_skips=3`,
  `actual_model_call_budget=37`, `actual_physical_parameters=8782459120`,
  `activated_base_parameters=8767123696`, `optimizer_updates=0`；
  `own_code_files=bd_io.own_code_files()`；protocol/current rule `*_path/*_sha256`，
  `required_files` 包含 `required_metadata_files`、四份本代码、protocol/current rule。
- `protocol.json`：schema 同上；`role/source_root/三分母/actual_model_call_budget/参数/optimizer`
  同注册；`hypothesis='SAME_INPUT_LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION'`，
  `disable_time_adapter_layers=144`, `new_input_processor_encodes=0`, `new_media_decodes=0`，
  `prior_TIME_completed_and_first_input_replay_required=true`,
  `same_prompt_grammar_native_conversion=true`, `independent_prefill_per_call=true`,
  `quality_claim_or_selection_by_this_driver=false`，
  `weight_check_strategy='ENGINE_LOAD_BASE_AND_288_ADAPTER_BEFORE_FULL_REHASH_AFTER_JOB'`，
  新唯一 `gpu_job_name` 与本轮 `deadline`。
- `source_lock.json`：`status='FROZEN_BASE_PAIRED_SOURCE_INPUT_CLOSURE'`，
  `role/source_root` 同注册，`files={path:sha256}` 包含全部上述必需文件。
- `gpu_admission.json`：
  `status='PASS_INDEPENDENT_LOCAL_BOUNDARY_BASE_PAIRED_GPU_ADMISSION'`，
  `registration_sha256/source_lock_sha256/actual_model_call_budget/gpu_job_name/参数/optimizer`。

每次 BASE 调用绑定相同 prompt、有限 grammar、真实缓存 tensor、TIME done 与原 first-input
replay SHA。仅在 generate 上下文 disable TIME；before144false/grad0、inside144true/grad0；
退出先 `model.requires_grad_(False)`，保留实际退出前和恢复后的 gradient 数，再核144false。
job load 证完整 base+288adapter，job结束再全量核一次；不在每次调用重复全模型 hash。
每次 generate 全输入重新 prefill，不传旧回答或 `past_key_values`。

新输出 CPU replay 只实例化 `AutoTokenizer`；不实例化 `AutoProcessor`，不读 cache、RGB，
不调用 encoder。它重做新 tokens/有限 JSON/grammar/独立 native 转换，引用旧输入重放。
三个结构性 skip 直接引用原几何 proof，无模型、raw 或假 token replay。最终
`boundary_prediction_export.json` 保留20事件、40端点和3静态原点；
`paired_behavior_export.json` 仅报告同输入行为差异，`SCI=false/quality_claim=false`。
坏输出、梯度、schema、ledger 或 SHA 均失败并保留 raw/proofs，不转 UNKNOWN。

未来 confirm 的 `registration.frozen_development_selection` 必须是 metric08 根内的
`{path,sha256}`；其原结果必须
`status='FROZEN_GLOBAL_REFINER_ROLE_FROM_DEV_DIAGNOSTIC_NOT_SCIENCE_PASS'`、
`chosen_role='BASE'`、`confirm_outputs_read=false`。本 driver 不把开发或作者动作 proxy
称为高光验证，也不改当前 known-ID/bytes 隔离范围或预训练 UNKNOWN。

纯检查01验证重复 PEFT 退出288 trainable tensors 后显式恢复为0，144 false/true/false，
同 V4 的 KEEP/UNKNOWN/REFINE 原生转换、40=37+3、37BEGIN/37ACCEPTED、全20事件导出、
坏 tokens/score/gradients 阻断和输出 replay 无 encoder/cache。02只增量验证新 closure AST
及合成 TIME36/37、首输入 replay36/37 不得准入；没有重复01成功检查。
两次均通过 SSH stdin 内存代码执行，无生产代码部署、实际 source gate、CPU、GPU或模型调用。
