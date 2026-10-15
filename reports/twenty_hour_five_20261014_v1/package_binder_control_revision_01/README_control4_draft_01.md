# Linux 最终封包元数据绑定器

`bind.py --config /absolute/Linux/config.json`。仅 standard library，不导入 input/runtime/package，不运行 model、decoder、processor、tensor loader、旧 ZIP 验收或正式 package。

入口先严格要求 `CONTROL4/exports_01/global_completion.json` 的真实全体 PASS 和 `CONTROL4/run_01/completion.json` 的后续自然终态；未满足时不写 package root。它收集所有原/新 clock 的七类引用、每个真实 MODEL 的首个独立验收和 retained evidence、canonical input manifests/payload SHA、typed structural proof、每个 batch 的 immutable resource/ledger/closure、INPUT5/runtime5/control4/bootstrap2 的注册/完整 graph/roles/code/QA/cache、原 source field 和旧 source/model/vendor/strict-loader 定义。

canonical tensor 和已有 source field/D8 ZIP 只引用既有验收 SHA 并核大小/存在；不会重做 tensor decode、RGB、processor、旧包 canonical 或完整模型哈希。最终 renderer 的 `checked_inputs` 负责读取锁中必要文件并检查 SHA。已释放的 staging RGB 和 source-media SHA 只保留历史 provenance，不当成 retained 文件加入锁。旧 Windows 路径的历史 provenance 不被转换成 Linux 假路径。

成功仅创建 `CAMPAIGN/temporal_family_native_package_v3/package_inputs.json`、`history.json`、`source_package_lock.json` 和 `technical_preparation_receipt.json`；协议、authorization、当前规则三份 root 提供的小 JSON 如果目标不存在，则按原字节首次复制，已存在一致副本直接引用。任何存在的最终 `package_admission.json` 会阻止再绑定；模块永不创建它。后续风险/规则/工程准入由 root 独立决定。这里不评价质量、不宣称五包或 Goal 完成。

root 的 config 必须事先固定以下字段及 SHA：

- `schema=TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_V1`、固定 `package_root`。
- `production_completion_ref`、`controller_completion_ref`，以及 `production_refs` 七项：`input_registration`、`full_plan`、`plan_completion`、`cache_initialization`、`runtime_protocol`、`control_registration`、`bootstrap_completion`，均为当前 INPUT5/runtime5/control4/bootstrap2 实际入口。
- `legacy_inputs`：`baseline_zip`、`metadata`、`source_manifest`、`source_field_files`（四个原 filename→ref）、`source_binding_ref`。field refs 必须等于全体 frozen plan 的 `old_spatial_field_refs`。
- `package_code_refs`：root package code 目录中每个 `.py` 的 name→ref。`package_family.py` 必须为 `9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e`；不改八臂及 priority。
- `package_document_refs`：`protocol`、`authorization`、`official_rule_check` 三个 root 提供的冻结 JSON。
- `additional_metadata_refs`：额外必要 metadata ref 列表。`frozen_file_lock_specs`：旧模型/source 完整锁回执列表，每项 `{receipt_ref, files_key_path}`，该路径指向已有的绝对 Linux file→SHA map；不给名称推测或目录广扫。
- `history_specs`：固定既有 canonical receipt 列表。每项 `{receipt_ref, rows_path, field_map, selectors}`；`rows_path` 为键/索引列表，`field_map` 将已有字段映射到 `filename/ZIP_SHA256/member_SHA256/canonical_SHA256`，值为点分字段路径；selectors 是 root 预先指定的唯一记录匹配条件。明确取整个既有 list 时可用 `select_all_records=true` 替代 selectors。不按文件时间选择，也不重读历史 ZIP。
- `required_binder_code_files`：实际 Linux binder code 绝对路径→SHA，包含本文件。

当前只交代码与 AST 检查；未执行实际 binder。成功结果禁止整链重跑；若写入阶段失败，保留已完成文件，之后只能由 root 登记显式剩余恢复。
