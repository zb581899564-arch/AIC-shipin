# Control V4 — 输入 v5 / runtime v5，全生产执行 0

新 root `CAMPAIGN/temporal_production_control_v5`，schema `TEMPORAL_PRODUCTION_CONTROL_V5`；registration 必须明确 `input_root_name=temporal_production_inputs_v5`、`runtime_root_name=temporal_production_runtime_v5`、`cache_version_root_name=production_stream_cache_v2`，cache code/policy `LINUX_PERSISTENT_FLOCK_V2`。不改旧 control v1 和任何成功锁。

controller 按预冻结 source 顺序和真实字节容量运行多批，每 source 全消费者不拆。完整 global graph/角色/batch membership 在首次正式模型前固定。批内 CPU 多 source 并发数来自实时 memory/disk/core pressure 与保守 source envelope，GPU 单批一次加载；prepare B0 → GPU0 并行 prepare B1 → GPU0 自然 terminal → GPU1 并行首次 input+output QA/close0 → close0 后 prepare B2。资源 reservation 原子登记，cache mutation 由 critic flock；不外套可重入锁。所有启动 journal/launchclaim 禁重复，无 wholechain 自动 retry；deadline 不启动新任务，已启动任务自然结束。

registration 仍需完整 `required_code_files`、`runtime_protocol_ref`、`frozen_batch_index_ref`、`global_graph_sha256`、role/rules/deadline；`whole_graph_batches_and_roles_frozen_before_first_model=true`、`main_controller_execution_approved=true` 和 training/testGT/oldsuccess false。最终 `main_execution_admission_path` 仅 path，root 最后 create-x 状态 `PASS_MAIN_CONTROLLED_PRODUCTION_BOOTSTRAP_AND_EXECUTION`、实际 reg SHA 与 `allow_controller_issue_batch_gpu_admission=true`，避免循环 SHA。每 batch 实际全部 CPU acceptance 后才签具体 GPU admission；不是 quality gate。

CPU envelope 使用真实 `actual_peak_rss_kib/conservative_overhead_bound_bytes/actual_proof_ref`。GPU envelope 明确支持 `OBSERVATION_UNAVAILABLE_WITH_CODE_BOUNDED_ENVELOPE`：cold_load_HWM_observed=false，observed_BASE_host_peak_rss_bytes/observed_peak_proof_ref=null；base BF16 bytes + actual largest shard + actual CPU process peak + processor/token cap prefill bound + 明示 adapter/prefill copy margins。resource17 的 conservative bytes 27013789672 是代码包络，不是观测冷加载 HWM 或固定 GB 准入线；实际 `MemAvailable/disk free` 动态判定，reg reservation 必须覆盖该包络及本批真实输出预算。所有 leaf evidence path/SHA 强绑定，缺观察不捏造。

`aggregate.exact_clock` 独立核旧全 PTS/count/origin/geometry 和新 `first_RGB_decoder_terminal_witness`：实际 positive last Frame.duration 必须与原 unique/max-display packet duration 精确相同。packet registration.source + completion.video_id → terminal ref 强 join；五个旧 end equality FAIL 的 body/status 保留，只允许注册为该旧 equality mismatch，新实际 end 不再要求旧 N/fps 或 explicit end ticks 相等。

source clock exports 同存新实际 full raw/normalized PTS/origin/end/actual Frame.duration、packet observation/registration/completion refs、旧 recipe end audit 和旧 validation status。`native_clock_original_bindings` 包含七个 path/SHA ref（original_clock_ref/new_clock_ref/source_CPU_completion_ref/independent_equality_ref/packet_terminal_observation_ref/packet_registration_ref/packet_completion_ref）及独立 status/bool/audit/witness；package 必须分别核 ref 和 metadata，不能把每个 binding value 当 ref。

global exports 保留原 IDs，P_hash→0..425 一一自动映射，events665/endpoints1330（含 typed no64）/verification665/source_clocks426/actual MODEL 首次 proof 全覆盖。endpoints 为 runtimev4 双坐标 exports；events 同存旧 recipe 与 native-cut interval。KEEP/UNKNOWN/未改 side/cross 必须由 root family 使用旧 recipe native predicate 保持 D8；新 REFINE 才应用新 point，不能 native pivot 再 pad 假保原。

全 input/token/parser/native/GPU/weights/自然账本/LeaseStore 接受与新 RGB release 没有失败/遗漏后才产生 `PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS`。这个工程 PASS 不改旧五份诊断 FAIL，不宣称 scientific quality 或五 ZIP。root 独占 package-family 的 D8 122050 baseline/空间场/规则/风险/格式最终验收。

未来唯一 CLI：

```text
# parent CUDA explicitly nonempty; final main/source permission files must exist
python controller.py --registration ROOT/registration.json
```

此前 control_v2/runtime_v3 七项新增纯检查及代码保持原 SHA，不重跑。当前版本只补 root/schema/真实 ordinal-context metadata smoke；正式 project/init/source prepare/GPU/cache/lease 操作仍 0，未正式部署。

V4 继承官方规则仅准 INPUT4/bindings/official_rules.json 同原SHA，不开放整个旧root。所有 actual_GPU_budget_ref 仅准 BOOTSTRAP2。结构性 VERIFY UNKNOWN 从 output replay 保kind输入 verification 总数，独立结构proof全分母核验；不进 MODEL acceptance、GPU journal 或 RGB release分母。

CONTROL5 是独立环境恢复：只恢复 original helper PYTHONPATH，复用原 INPUT5/runtime5/BOOT2/cache/global graph/49 batch/index；旧 CONTROL4 failed/code/journal/logs保留。固定 child 环境在所有 CPU/GPU Popen 前整串覆盖 PYTHONPATH，不继承 cwd、空项或旧杂项；SOURCE CPU仅遮自己CUDA，GPU/父CUDA0保持。SFT helper真实根为 temporal_sft8b_v1，而 timeadapter数据根仍 temporal_sft8b_full_v1/train_01/adapter，二者不混同。共享gpu_run继承os.environ并保PYTHONPATH，未改wrapper。
新 registration 必须有 original_control_registration_ref、explicit_import_environment_recovery_ref、explicit_child_environment；旧原125SHA完整保留，加本版6py和4个已存在的vendor/SFT传递helper真实SHA（共135）。frozen_batch_index_ref只准CONTROL4/batch_index.json原成功leaf。main_execution_admission须新ROOT最终创建，同原status并额外绑定新regSHA、explicit_import_environment_recovery_ref、original_control_failure_ref、10 failedsource IDs、recovery_scope=IMPORT_ENVIRONMENT_ONLY_NO_SUCCESSFUL_STAGE_REPLAY。旧10失败仅在新run_01 journal中重新尝试未开始的SOURCE，不重复metadata或成功processor，旧失败不升PASS。
恢复receipt核十个SOURCE BEGIN/FAILED唯一配对及先后，每个log exact_pts错误、原零产物诊断、实际helpers ownerSHA。诊断是旧失败时的immutable快照，后续成功源码不将其回写。aggregate读取CONTROL5自己的registration/journal/run_01/exports_01，完整旧graph/coverage门不变。当前只code/静态metadata，未部署/运行恢复或CPU/GPU；root会先做一次独立原legacy_runtime module-owner导入预检（无processor/model/AV/tensor），然后最后签新admission及唯一launch。旧科学pure不因环境恢复重跑。
