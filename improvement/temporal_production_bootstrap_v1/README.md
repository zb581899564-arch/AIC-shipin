# 一次 metadata bootstrap generator（只代码，无执行）

Linux root `CAMPAIGN/temporal_production_bootstrap_v1`，schema `TEMPORAL_PRODUCTION_METADATA_BOOTSTRAP_V1`。root review 后才可调用：

```text
CUDA_VISIBLE_DEVICES='' PY -B -u ROOT/code/build.py --config ROOT/bootstrap_config.json
```

builder 一次冻结 inputv4 registration → 一次 metadata-only `project_legacy.main` → metadata-only cache initialize → 实时 capacity snapshot → 连续完整 source 双缓冲 batches → runtimev4 protocol → controlv3 index/registration。没有正式 media decode/processor/model/GPU wrapper，不创建 source preparation 或 controller final admission。started/failure/partial metadata 永久保留，不能 wholechain retry。

config 字段：schema、metadata_build_approved=true、formal_prepare_or_GPU_execution_by_builder=false、test_GT_read=false、whole_graph_batch_roles_frozen_before_first_model=true、deadline；required_code_files 全 bootstrap/input/runtime/control/cache/boundary/VERIFY 及原 source_color/common py 的真实绝对 path→SHA；input_registration_template、runtime_protocol_template、control_registration_template；CPU_resource_envelope_ref、GPU_host_resource_envelope_ref、CPU_process_overhead_bound_bytes、GPU_host_resource_bound={memory_bytes,disk_bytes}、QA_memory_bound_bytes、metadata_output_bound_bytes；source_storage_estimator_template_ref、frozen_GPU_budget_ref、unique_gpu_job_prefix。

三 template 必须由 root 按各目录 README 审查完整 flags/refs，builder 不猜 role/规则/科学许可。input template 包含 source_color_config_ref 和全部旧 D8/packet refs、新 reader scope；official rules、selection、scope 原字节分别保留到 INPUT/bindings。input permission path 和 control main admission path 事前均不存在；root 最后创建实际 SHA 绑定许可。runtime protocol 不含 batch/index refs，所以 protocol → batch SHA → index → control registration 没有循环。

storage estimator template 推荐 `REPRESENTATIVE_LOSSLESS_RATIO_NONFIT_FORECAST`，另可 `PC_SOURCE_BOUND_UNCOMPRESSED_CODE_ONLY`；均 require source_membership_uses_only_frozen_graph_and_bytes=true、predictions_or_reference_metrics_used=false。代表 method 只带 representative_ratio_ref，不捏逐源compressiontable。该小receipt schema=REPRESENTATIVE_EXACT_CACHE_STORAGE_RATIO_NONFIT_FORECAST_V1、probe_ref、new_LUT_gzip_bytes/original_gzip_bytes/logical_tensor_bytes 三个真实整数、independent_exact_roundtrip_verified=true、forecast_fit_guaranteed=false、unsupported_dictionary_uses_original_gzip=true。全局 raw canonical 列 NOT_FIT_THEORETICAL（若超当前容量），ratio 仅给 non-fit estimate，完全不参与分批/准入；不要求提前放下全部约 566GB raw tensor。

分组使用当前可用 memory 扣 GPU 和 QA 包络再取两个 live batch；disk 仅扣 metadata/output budget，再取两份完整 source uncompressed canonical fallback + staging/transient。没有固定 GiB/worker count，不按预测质量、GT 或变化挑批，不拆 source，不重算 event IDs，空源 CPU-only 不造 GPU0。无法放下一个完整 source 则 STOP，保留已创建 metadata；未来每批当前容量和实际 canonical 保存字节再严格核，不宣称初始 forecast 保证全局 fit。

budget template 字段：maximum_nominal_calls=1995、model_call_denominator_source=FIRST_FROZEN_PLAN_ACTUAL_MODEL_REQUESTS、per_call_seconds（已有真实生成/对照的事前保守预算）、cold_load_seconds、queue_seconds、output_bytes_per_call、batch_fixed_output_bytes。唯一首次 project 后 create-x actual_GPU_budget.json，绑定 template SHA/full plan SHA，实际 denominator=len(plan.consumers) 且不超过 1995；未用模型结果或猜 1993。已精确知道整数的旧 template 也可显式 model_call_denominator，但必须等于首次 plan。

各 batch 引 actual_GPU_budget_ref，max_seconds 按真正 MODEL 数算；prefix+batch_id 唯一共享 job 名，root 还需查原 ledger 未使用。全部 membership/roles/消费者/ordinal 在首次模型前冻结，实际尺寸增长只可使容量 STOP，不能按模型结果重分组。

当前交付只包含可执行代码及新增 metadata smoke；builder/project/init/cache/prepare/GPU 实际调用均 0。metadata smoke 不是 bootstrap 实际执行或生产 fit 证明。
