# 明确剩余 metadata 恢复壳（未部署或执行）

独立代码 root `CAMPAIGN/metadata_recovery_v1/code`。保留第一次失败的 `BOOTSTRAP/bootstrap_run_01`、原 125 项代码 SHA、INPUT4 registration 和三个 bindings 原字节。恢复壳不会再调用旧 builder，也不调用旧或新 projection 的 `main`；只调用 root 新批准的独立 module `project(reg)->dict`，首次创建此前不存在的 `INPUT4/plan_01`，再首次创建 budget/cache metadata/分批/runtime protocol/control index 和 registration。

```text
CUDA_VISIBLE_DEVICES='' PY -B -u CAMPAIGN/metadata_recovery_v1/code/recover_metadata.py --protocol CAMPAIGN/metadata_recovery_v1/protocol_01.json
```

仅提供代码。当前不得调用该 CLI；源代理尚在定位真实接口问题，壳没有猜测字段修正。只有 projection 字段读取/interface 改动可以复用旧 INPUT4 根；若旧 contract/math/io 要变，立即停止并由 root 决定独立新输入版本。

协议 schema `EXPLICIT_REMAINING_METADATA_RECOVERY_V1`，必须有：deadline；remaining_metadata_only=true；projection_interface_only=true；old_input_helpers_or_math_changed=false；old_head_bindings_or_registration_recreated=false；test_GT_read=false；formal_source_decode_calls_authorized=processor_calls_authorized=model_calls_authorized=0；required_code_files（原 125 map 原值加本壳和实际新 projection/依赖 SHA）；old_bootstrap_config_ref、failed_input_registration_ref、old_failure_ref、old_failed_projection_ref、new_projection_ref；new_projection_API=`PURE_METADATA_PROJECT_REG_DICT_V1`；reused_binding_refs（official_rules_ref、selected_uniform_development_role_ref、reader_native_terminal_scope_ref 原 refs）；recovery_admission_path。

root 最后创建独立 admission，status=`APPROVED_ONCE_REMAINING_METADATA_RECOVERY_NO_FORMAL_SOURCE_OR_GPU`，绑定 recovery_protocol_sha256 和协议五个旧/新 refs，以及三个 calls_authorized=0。protocol 的 code map 不包含 protocol 或 admission，避免 SHA 循环；registration 始终引用原 frozen map，runtime/control 的新 code map 则明确添加本次实际代码。

恢复前原 failed terminal 必须存在且无 completion，plan/cacheinit/cache root/runtime protocol/batches/control index/registration/新恢复目录/两个正式许可均不存在。所有写入 create-x；不删除旧文件、覆盖或自动恢复部分新尾段。新失败继续保留 partial 并停止。

`plan_01/full_plan.json` 和 completion 添加 metadata_projection_recovery，绑定原失败 registration/failure/projection、实际新 projection、恢复 protocol/admission SHA。旧失败 projection 不被重标成功。cache initialize 仍按原 registration；runtime/control 另引用 `metadata_recovery_plan_completion_ref`，不引用尚未形成的尾段 completion，所以没有循环。最终新 metadata completion 存 `BOOTSTRAP/metadata_recovery_01/completion.json`，actual_GPU_budget.json 同目录，满足旧 runtime budget reader 的 BOOTSTRAP 根边界。

最后实际 source permission 须由 root 另行绑定这个 recovery completion SHA 和实际新 projection SHA。此壳不创建 source/controller/GPU 许可，不调用媒体、processor、模型或 shared GPU wrapper，不改源码/标注/科学算法/旧包。
