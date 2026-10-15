# 第五包独立 CPU 入口：PAIR_ONLY 短源补充适用性确认

本目录为本地准备稿，未部署、未运行。`package_math.py` 与 `production_evidence.py` 沿用前轮已实现的原生帧数学与518真实调用＋1 alias读取器；独立入口 `package_five.py` 增加补充质量范围与原四包保护。不会修改原 `package_code_v2`、`package_inputs.json`、`quality_admission.json`，不会重跑模型、输入处理、首次QA或已交付四包。

仅允许 `python -B package_five.py --arms REDUNDANT`，默认也是REDUNDANT。必须Linux CPU环境 `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1`。部署代码须另选新目录。固定根仍为 `/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1`，新增引用文件固定：

- `package_inputs_pair_supplement.json`
- `quality_admission_pair_supplement.json`

唯一新包目标为原根 `packages/package_REDUNDANT/candidate_MIDNIGHT_REDUNDANT.zip`。已有 `ORDINARY/ACTION/REACTION/INFORMATION` 四包按原completion与ZIP真实字节保护，只读核对、去重。不会重新compose或封这四臂。开始前及取得独占封包锁后均要求REDUNDANT目录不存在；无论已有成功还是部分失败都停止，不覆盖、不重做、不自动恢复。已成功结果由主代理直接引用其原receipt。

## 新 inputs 契约

所有ref均 `{"path":"Linux绝对路径","sha256":"实际SHA"}`，可附bytes。原保护基线保持旧根 `temporal_family_native_package_v3/package_VERIFY/candidate_TEMPORAL_VERIFY.zip` 的380199B/SHA `86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543`，426源/122002帧。

新inputs沿用原字段：`old_package_inputs_ref`、`old_source_package_lock_ref`、`protected_baseline_zip_ref`、`production_completion_ref`、`history_ref`、`protocol_ref`、`authorization_ref`、`official_rule_check_ref`、`package_admission_ref`、`code_files`。其中：

- `production_completion_ref` 必须原 `production_unique_09/completion.json`，模型/QA计数与原成功工程permit都严格相同：logical519、model518、alias1、first-model-output-QA518、alias-application-QA1。
- `protocol_ref` 必须原 `publication_protocol_13.json`，REDUNDANT仍为 `WORST_PAIR_ONLY`；数学只在n==2时删除真实 `parsed.redundant` 的至多1个最弱候选，原parsed和端点不变。
- `history_ref` 必须保留25条实际历史记录，即原21条＋当前4包；原21条含19个不同canonical，合并后恰23个不同canonical，且包含四个当前包。历史真实重复不删、不造记录。支持列表或带records字典，zip_ref若提供则核实际预测。
- `code_files` 必须绑定本目录部署后的4个py：`package_five.py/package_math.py/production_evidence.py/supplement_quality.py`。

新增inputs字段：

- `original_package_inputs_ref`：原根 `package_inputs.json` 的原实际字节。
- `original_quality_admission_ref`：原根 `quality_admission.json` 的原实际字节，REDUNDANT仍 `FAILED_FIXED_NEW_CONFIRMATION`。
- `quality_admission_ref`：新固定 `quality_admission_pair_supplement.json`。
- `existing_four_package_refs`：四个实际 `packages/package_ARM/completion.json` ref，恰ORDINARY＋三个risk，不能用预测副本或改名包替代。

原old/source/baseline/production/protocol五类refs须与 `original_package_inputs_ref` 内容逐项相同。原inputs和原quality在写最终ZIP前再次核字节，整个入口从不写它们。

## 新工程 permit 契约

`package_admission_ref` 指另一个新文件，保留原工程准入字段：

```json
{
  "status":"PASS_NEW_FIVE_WAY_CPU_PACKAGE_ENGINEERING_ADMISSION",
  "actual_parameters":8782459120,
  "production_completion_sha256":"原production_unique_09完成文件SHA",
  "automatic_removal_and_recall_authorized":true,
  "three_risk_arms_without_offline_quality_screening":true,
  "test_labels_or_manual_edits_used":false,
  "current_official_rules_rechecked":true,
  "history_complete_for_all_preexisting_deliveries":true,
  "production_evidence_counts":{"logical_cases":519,"actual_model_calls":518,"adopted_identical_input_aliases":1,"first_model_output_QA_count":518,"alias_application_QA_count":1},
  "original_package_inputs_ref":{"path":"...","sha256":"..."},
  "original_quality_admission_ref":{"path":"...","sha256":"..."},
  "supplementary_quality_admission_ref":{"path":"...","sha256":"..."},
  "existing_four_package_refs":[]
}
```

末四项必须与新inputs相应refs完全相同，四包列表须完整。`three_risk_arms_without_offline_quality_screening`仅保留原授权身份；新入口不能请求或发布risk臂。

## 新质量文件契约

`quality_admission_pair_supplement.json` 必须仅含 `arms.REDUNDANT`，其字段：

```json
{
  "status":"PASS",
  "reference_scope_kind":"SHORT_SOURCE_PAIR_APPLICABILITY_SUPPLEMENT_ONLY",
  "reference_scope":"仅新四个作者时长不超过30秒、原B0单窗native64外部来源的PAIR_ONLY短源适用性确认；原四源零变化失败保留；不代表全局或官方成绩",
  "supplemental_scope_only":true,
  "independent_confirmation":true,
  "test_labels_used":false,
  "actual_model_parsed_unchanged":true,
  "deterministic_deletion_policy":"WORST_PAIR_ONLY",
  "old_result_unchanged":true,
  "policy_and_gates_unchanged":true,
  "development_ref":{"path":"原policy_comparison_08.json","sha256":"..."},
  "confirmation_ref":{"path":"实际新补充结果","sha256":"..."},
  "frozen_rule_ref":{"path":"原publication_protocol_13.json","sha256":"..."},
  "original_nonapplicable_confirmation_ref":{"path":"原relative_confirm/policy_fresh_comparison.json","sha256":"..."},
  "supplemental_confirmation_ref":{"path":"实际新补充结果","sha256":"..."},
  "supplementary_source_registration_ref":{"path":"新来源分层/身份及冻结登记实际回执","sha256":"..."}
}
```

`confirmation_ref`与`supplemental_confirmation_ref`须同一实际文件；原nonapplicable ref必须精确对应原quality中REDUNDANT的confirmation_ref。原quality、原comparison都不得覆盖或改PASS。新PASS只写新scope。

原、新comparison均须实际 `MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1/group=confirm/status=FIRST_FRESH_POLICY_COMPARISON_COMPLETE/full_source_count=4`。原PAIR_ONLY仅 `real_changed_sources=false`，其余七门true，PASS/ passed_policies.PAIR_ONLY均false；宏三项delta.exact=0，四源各removed/added=0且三个baseline/candidate metric精确相同。新补充必须 `selected_policies=["PAIR_ONLY"]`，PAIR_ONLY的PASS/ passed_policies均true、同原8门全true、实际至少一源有删选且无新增帧。

三次结果（原dev、原confirm、新supplement confirm）的bindings.protocol_ref必须同原publication中的policy_protocol_ref，即原 `policy_protocol_07.json`。新四源必须在manifest中身份/字节均与原dev及原confirm隔离；只绑定主代理实际新来源登记，不在封包阶段挑源或重评。开发PASS仅引用原结果，不重评分。新scope仅补充短源n2适用范围，算法、质量门、最大30秒输入profile不改变。

## 输出边界与准备检查

唯一第五预测仍需原426非空、原PTS、保留原框逐值一致、新框来源既有连续场、原11strict、单JSONL/CRC/memberSHA，并对25条历史记录的23个不同canonical去重（已含当前四包）；不变/重复结果不能改名充数。实际驻留参数仍8782459120，封包新模型调用0。最终receipt明确原失败未提升、补充scope、两次确认refs以及原四包未重跑。

本次只准备代码与契约，做内存AST/静态读回；不运行封包、模型、QA、数据准备、部署或远端操作。实际新四源PASS、部署、集成和第五ZIP最终验收由主代理完成。
