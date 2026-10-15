# 正式时间推理单批 runtime v2（代码原型）

当前未部署、正式426 decode/processor/GPU/训练均0。此目录仅新的单批消费者、输出独立CPU验证和本批新RGB lease闭环；不修改旧模型/输入/成功proof、critic库或旧失败费用。完整全局graph先由输入层冻结，总控负责容量分批controller与所有独立自然终态的最终无重复聚合，不在此自动选择角色、来源或参数。

按冻结source顺序的连续来源块组批，每source的全部endpoint/VERIFY MODEL消费者和typed no64结果同批。最大1995是逻辑上限，实际call预算严格为该批global graph MODEL request_ids长度；no64原端点UNKNOWN是pre-model typed skip，无BEGIN、无fake raw model call。批列表由实际storage estimate/当时容量明确登记；不按预测或GT选批。每批一份完整CPU acceptance、一份main GPU admission、现有 `gpu_run.py` 唯一job和自然completed0 ledger；批内原base+TIME adapter仅load一次。模型不逐source重载。全图单job的自然terminal前不能逐批release，因此本版明确多批自然终态，预计批数由实测容量决定，不写死为20/40。

endpoint角色为开发冻结 `TIME_ENABLED` 或 `BASE_DISABLED`，VERIFY固定TIME_ENABLED。没有默认/自动挑角色。144 LoRA layer在调用前enabled；BASE局部调用仅在disable_adapter context内144全disabled；退出显式 `model.requires_grad_(False)` 并核144恢复、trainable0和完整physical inventory。TIME/VERIFY同样每call独立prefill，无跨role KV或旧回答上下文。实际GPU tensor来自输入层永久exact dict ABI，逐call核全部dtype/stride/offset/alias/bytes/tokens/grid与actual GPU signature；不用普通dict.to丢view语义。

原B完整base hash和288实际saved adapter values装载时检查；批末再完整复核一次，中间每call核frozen inventory和144状态，协议策略 `FULL_ENGINE_LOAD_AND_FULL_BATCH_END_BASE_288_ADAPTER_REHASH_PER_CALL_FROZEN_INVENTORY` 必須事前登记。加载物理总参数8,782,459,120始终计入9B门；BASE激活8,767,123,696不意味着卸载TIME或降低实际总参数。无optimizer/新模型下载。

BEGIN先写journal；真实raw/token IDs/scores在post-context/grammar/parser/native验收前永久保存。任何输入/生成/grammar/post-state失败保留所有raw及费用，阻断并exit1，不转UNKNOWN/空段，不自动重跑已经BEGIN的请求。端点prompt、finite grammar、source-edge inward、native duration连续性与END=最后included下一PTS语义hashbound复用v3；VERIFY严格KEEP/UNKNOWN/DROP复用CV contract。输出CPU独立转换复用v3独立endpoint函数AST；VERIFY独立核原candidate/原window与可见sample gate。

控制根：`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_production_runtime_v2`。

全局 `protocol.json` 字段：schema `TEMPORAL_PRODUCTION_RUNTIME_V2`；training/test_GT_read/old_successful_outputs_modified=false；algorithm_and_uniform_roles_frozen_before_production=true；natural_terminal_per_batch_before_RGB_release=true；weight_check_strategy；actual_physical_parameters；optimizer_updates0；deadline；endpoint_model_role/verify_model_role；selected_uniform_development_role_ref（与input registration完全相同）；original_B_config_sha256；input_library_directory固定输入层code；input_registration_ref；full_plan_ref；cache_initialization_ref；cache_global_request_lock_ref（critic permanent relative ref）；required_code_files所有自身、input ABI与v3 grammar/independent replay/CV grammar的路径SHA。input registration本身已含完整规则/角色/processor/cache库绑定，runtime只继承并核SHA。

`batches/B0001.json`：schema/batch_id；protocol_sha256；global_graph_sha256=whole full_plan SHA；global_source_order_sha256；source_ids连续冻结来源段；logical_request_ids全该源请求含typed skips；request_ids全该源MODEL请求，顺序逐source/原graph；actual_model_call_budget；gpu_job_name（每批不同）；membership_reason `FROZEN_SOURCE_ORDER_AND_ACTUAL_CAPACITY_ONLY`；predictions_or_reference_metrics_used_for_membership=false；capacity_receipt_ref（root/inputs下真实容量登记）。全局分母保持，即使某source无候选，不按结果追加或替换。全空MODEL批须由controller写CPU-only覆盖receipt，本脚本不启动fake GPU0call job。

`runs/B0001/CPU_admission.json`：status `PASS_INDEPENDENT_COMPLETE_BATCH_CPU_INPUTS`；batch_sha256/global_graph_sha256/source_ids/request_ids；source_completion_refs按source指向永久新的真实CPU completion。`admit_batch.py` 核全部native/原候选/prompt/consumer graph、每个永久cache文件SHA和still-present RGB后写 `input_admission.json`，这不是GPU许可。

总控另写 `runs/B0001/gpu_admission.json`：status `PASS_INDEPENDENT_PRODUCTION_BATCH_GPU_ADMISSION`；protocol_sha256/batch_sha256/global_graph_sha256；batch_CPU_admission_sha256/input_admission_sha256；actual_model_call_budget/gpu_job_name/actual_physical_parameters/optimizer_updates0。总控通过现有共享wrapper启动 `infer_batch.py`，脚本仅验证live reservation，不自行申请/启动wrapper。

未来CLI（此次均未执行）：

```text
python admit_batch.py --protocol ROOT/protocol.json --batch-id B0001
# root freezes GPU admission, then invokes infer once through existing gpu_run.py:
python infer_batch.py --protocol ROOT/protocol.json --batch-id B0001
python replay_batch.py terminal --protocol ROOT/protocol.json --batch-id B0001
# root first invokes input-layer replay_input.first_input_replay for each batch consumer,
# passing permanent refs from runs/B0001/terminal_pointer.json. Never repeat successes.
python replay_batch.py replay --protocol ROOT/protocol.json --batch-id B0001
python close_batch.py --protocol ROOT/protocol.json --batch-id B0001
```

terminal阶段只从实际shared resource/ledger核唯一自然completed0并copy小量永久snapshot给输入first replay。输出阶段只加载原local tokenizer；不读source/RGB、不encode vision、不load模型，不重复成功first input replay，只引用其不同PID、完整签名、普通processor实证。再独立核token逐前缀finite grammar/raw/parser/native、actual GPU signature、实际weights/144/gradient状态、raw→done和真实ledger，写critic `CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1`；cache policy的 independent_replay_code_sha256 必须为本 `replay_batch.py` 的SHA。

close阶段先接受本批所有预冻结MODEL consumer，之后仅调用critic release_rgb删除本批事前声明ephemeral的新RGB。完整canonical tensor、raw、proof、clock与所有旧成功永保留。未完成/失败consumer阻断release；跨batch拆source或lease阻断release。任何阶段已尝试/已成功均不自动重复，部分失败由总控另定独立恢复边界。输出QA和lease关闭仅工程一致性，不宣称科研质量、提分、5个提交包或总global已完工。

新增配置：protocol.input_root显式指定已登记production input v1/v2版本，input_library_directory必须严格等于该root/code，live process禁止中途切换root。总controller本轮限定input_v2/runtime_v2/cache_v2；旧v1全部字节保持。数学/提示/activation和自然QA/lease规则不变；新permanent proofs命名空间runtime_v2。
