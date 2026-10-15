# 本轮五臂 CPU 封包入口（尚未部署/执行）

仅新增代码，不执行旧 launcher、旧封包、模型、解码、训练或远端写入。预期部署至 Linux 新根的 `package_code/`，父进程应显式使用 `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python -B`。入口 `package_five.py --arms ACTION REACTION INFORMATION` 可单独封三风险臂；以后通过独立质量准入后可单独请求 `--arms ORDINARY REDUNDANT`。不重复已成功臂，全部输出只写新根 `packages/`。

新根固定 `/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1`；旧根固定 `/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_native_package_v3`。保护基线固定旧根 `package_VERIFY/candidate_TEMPORAL_VERIFY.zip`，380199B、SHA256 `86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543`、426非空源/122002帧。

## 主代理需提供的输入

新根 `package_inputs.json` 的以下字段均为 `{"path":"Linux绝对路径","sha256":"..."}`（可附 `bytes`）：

- `old_package_inputs_ref`、`old_source_package_lock_ref`：旧根对应两个原文件。
- `protected_baseline_zip_ref`：上述40.46原ZIP。
- `production_completion_ref`：新实际完整推理终态。
- `history_ref`：所有既有交付的 canonical 哈希列表，每条有 `canonical_SHA256`；可附 `zip_ref` 并核实际ZIP预测。支持直接列表或 `{"records":[...]}`。须包含此前五包，不只引用生成五包前的旧history。
- `protocol_ref`、`authorization_ref`、`official_rule_check_ref`、`package_admission_ref`：本轮冻结规则/人工授权/本次官方规则核对/工程准入，不能拿旧失败方向的准入代替。

另有 `code_files`，至少绑定 `package_five.py`、`package_math.py`、`production_evidence.py` 三个实际部署文件，例如 `{"/新根/package_code/package_five.py":"sha", ...}`。新根 `package_inputs.json` 不需要绑定自己的哈希，避免循环。

`protocol_ref` 内容至少包含 `arms=["ORDINARY","REDUNDANT","ACTION","REACTION","INFORMATION"]`、`empty_source_guard="PRESERVE_ORIGINAL_VERIFY40_46_SOURCE_SELECTION"`、`test_content_or_leaderboard_parameter_selection=false`。

若采用新预登记保守删除策略，协议增加 `deletion_application_policy={"ORDINARY":"某冻结策略","REDUNDANT":"另一冻结策略"}`，必须恰含这两键，值只允许以下三个字符串：

| 策略 | 仅消费真实 `parsed.redundant` 的确定性应用 |
| --- | --- |
| `WORST_ALL` | 当前窗原存活候选数 `n>=2` 时删除该最弱候选 |
| `WORST_FRACTION_1_3` | 仅 `n>=3` 时删除该最弱候选，保留至少2/3候选 |
| `WORST_PAIR_ONLY` | 仅 `n==2` 时删除该最弱候选 |

这些策略要求真实 `parsed.redundant` 最多1个索引；允许为空，不补造必须删除的回答。两臂均读取这个原字段，忽略原 `parsed.ordinary` 作为派生删除来源；不修改原raw/done或宣称派生选择是新模型直接输出。每臂回执明确写 `actual_model_parsed_unchanged=true` 和 `deterministic_deletion_policy`。未提供map时保持原direct行为，分别记录 `DIRECT_PARSED_ORDINARY` / `DIRECT_PARSED_REDUNDANT`。风险三臂不附删除policy数据，预测逻辑不变。

`package_admission_ref` 内容至少包含：

```json
{
  "status": "PASS_NEW_FIVE_WAY_CPU_PACKAGE_ENGINEERING_ADMISSION",
  "actual_parameters": 8782459120,
  "production_completion_sha256": "实际新completion的SHA",
  "automatic_removal_and_recall_authorized": true,
  "three_risk_arms_without_offline_quality_screening": true,
  "test_labels_or_manual_edits_used": false,
  "current_official_rules_rechecked": true,
  "history_complete_for_all_preexisting_deliveries": true
}
```

`production_completion_ref` 内容：

```json
{
  "status": "COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY",
  "actual_parameters": 8782459120,
  "first_input_QA_complete": true,
  "first_output_QA_complete": true,
  "actual_model_calls": 1,
  "unique_gpu_terminal_ref": {"path":"...", "sha256":"..."},
  "entries": []
}
```

通常 `actual_model_calls==len(entries)`；如有事先登记的完全相同输入复用，则必须 `actual_model_calls+adopted_identical_input_aliases==logical_cases==len(entries)`，并按下述证据链逐项重算，不把逻辑映射数冒充调用数。首input QA覆盖所有逻辑输入；首模型output QA只计真实调用，alias另计CPU native应用验收。若提供 `engineering_failed_requests`、`missing_requests` 必须均0。每entry仅包含具有实际64采样且有原KEEP/UNKNOWN存活候选的case，字段如下：

```json
{
  "case_id": "唯一ID",
  "source_id": "0",
  "source_sha256": "原源实际SHA",
  "source_ordinals": ["实际64个int，此处仅作说明"],
  "exact_pts": ["实际64个normalized精确有理数字符串"],
  "window_exact": ["lo", "hi"],
  "window_native_end_exact": "实际exclusive端点",
  "window_native_end_ordinal": 123,
  "candidate_events": [
    {"event_id":"原665之一", "original_interval_exact":["a","b"],
     "selected_interval_exact":["原VERIFY已padding的a","b"], "decision":"KEEP"}
  ],
  "decision_ref": {"path":"实际新回答或done", "sha256":"..."}
}
```

每个真实entry还必须 `output_qa_ref` 指向原 `PASS_FIRST_INDEPENDENT_OUTPUT_QA`，绑定其实际done/raw/first_input_qa/parsed。实际done的 `input_ref`、`first_input_qa_ref` 必须绑定当前逻辑case的新输入和原首次QA；raw明确 `actual_model_call=true`，且其input/first QA/原输出parsed与done及首output proof相符。entry的native字段逐值绑定自己的实际input文档，避免把另一输入的回答用于当前source。

### 完全相同输入alias（519逻辑case、518真实调用）

completion顶层增加 `logical_cases=519`、`actual_model_calls=518`、`adopted_identical_input_aliases=1`、`first_model_output_QA_count=518`、`alias_application_QA_complete=true`、`alias_application_QA_count=1`。每个逻辑case仍有独有的实际 `decision_ref` 和CPU验收proof；复用并不增加模型推理或首模型QA。

alias entry明确 `actual_model_call=false`、`alias_of=canonical case_id`，并有 `canonical_model_done_ref`、`canonical_output_QA_ref`、`identical_input_equality_ref`、自己的 `input_ref`、`first_input_qa_ref`、`output_qa_ref`。canonical必须是同completion内已核验的非alias真实调用，禁止alias串链。

alias done的status为 `ADOPTED_IDENTICAL_NEW_INPUT_MODEL_OUTPUT_NO_NEW_CALL`，含 `actual_model_call=false`、case/alias_of、canonical_model_done_ref、identical_input_equality_ref、自己的input/first_input_qa，以及与canonical逐值相同的 `raw_ref`、`parsed`。GPU时done不依赖未来output QA。之后的alias proof status为 `PASS_IDENTICAL_INPUT_ALIAS_NATIVE_APPLICATION_QA`，绑定own done、own first_input_qa、canonical_model_done、canonical原首output QA、同一equality table、unchanged parsed，且 `CPU_only=true/new_model_calls=0`。

equality table schema必须 `PRE_GPU_IDENTICAL_NEW_INPUT_ALIAS_TABLE_V1`，含 `logical_count=519/model_count=518/registered_before_GPU=true/actual_parameters=8782459120`、`generation={"do_sample":false,"max_new_tokens":192,"model_role":"BASE_ONLY"}` 和实际 `cpu_completion_ref`。`aliases` 中每项有 `alias_case_id/canonical_case_id/alias_input_ref/canonical_input_ref/input_signature/candidate_count/native_identity_equal=true/candidate_semantics_equal=true`。

独立读取器逐项核表、原519 CPU input/firstQA引用，以及alias/canonical四个完整张量的shape/dtype/bit签名相同、candidate_count相同、source SHA/原PTS/ordinals/window/end相同、候选interval/已padded interval/decision顺序相同；允许官方source_id/event_id因重复源不同画幅任务而不同。每份最终封包回执分别写真实调用数、alias数、逻辑数及两种QA数。三风险臂不读人工质量数据。

真实模型entry不含旧DROP或旧结构性NO64候选。事件可以跨窗重复出现；同窗不能重复。原665事件由真实entry加以下`structural_skips`完整覆盖，并与旧冻结原 `candidate(...,'VERIFY')` 结果相符。候选删除采用跨窗显式OR；保留事件取native帧并集，因此重叠事件不误删。原665事件的未删除并集必须严格重现40.46的122002帧，否则报工程错误，不猜padding或回退旧D8。

`production_completion_ref` 顶层可附 `structural_skips` 列表，每项为：

```json
{
  "case_id":"原case ID",
  "source_id":"273",
  "reason":"ADOPTED_ORIGINAL_NO64_UNKNOWN_PRESERVE_BASELINE",
  "candidate_events":[{"event_id":"原event ID","original_interval_exact":["a","b"],
                       "selected_interval_exact":["已padding的a","b"],"decision":"UNKNOWN"}],
  "old_decision_ref":{"path":"旧inputs.verification的实际export路径","sha256":"原SHA"}
}
```

只接受两种理由：`OLD_VERIFY_DROP_NO_BASELINE_CONTRIBUTION` 必须原decision=DROP且selected=null；`ADOPTED_ORIGINAL_NO64_UNKNOWN_PRESERVE_BASELINE` 必须原decision=UNKNOWN，并从实际旧verification export逐字段确认 `actual_model_call=false`、`applied_decision=UNKNOWN_SHORT_ORIGINAL_VISUAL_CONTEXT_UNAVAILABLE`、`predeclared_skip=true`、`declared_before_model=true`、实际采样数小于64、`required_distinct_native_frames=64`、`successful_model_call_required=false`、`verify_view_kind=PREDECLARED_SHORT_ORIGINAL_VIEW_NO_MODEL_CONTEXT`。原锁中这种NO64证据必须恰有1项。

每个skip的 `old_decision_ref` 必须精确绑定旧inputs的verification export路径/SHA，case/event/source/原interval也需逐项相符。skip不可带 `parsed` 或新 `decision_ref`，不增加新调用/首QA分母。跳过事件不可同时出现在模型entry；NO64 case不可有新模型调用。DROP skip可与真实entry同case，以支持同窗同时存在存活及旧DROP候选。NO64保留原基线贡献；DROP不产生基线贡献。所有实际跳过记入各臂回执。

实际 `decision_ref` JSON 必含 `parsed`，其精确schema为：

```json
{"ordinary":[0],"redundant":[],"action":[10,30],"reaction":[],"information":[50,64]}
```

候选index为0-based；后三类只能 `[]` 或一个 `[a,b]`，`0<=a<b<=64`。右端小于64时以sample b的实际source ordinal为exclusive边界；右端64时使用明确提供且由完整native clock验证的 `window_native_end_exact/ordinal`。不以第63个sample冒充64端点，不增加经验padding。可选entry `input_qa_ref`、`output_qa_ref` 若提供会验证实际字节。

仅ORDINARY/REDUNDANT读取新根 `quality_admission.json`：`arms.ORDINARY` 或 `arms.REDUNDANT` 中必须 `status="PASS"`、非空 `reference_scope`、`independent_confirmation=true`、`test_labels_used=false`，并有 `development_ref`、`confirmation_ref`、`frozen_rule_ref` 三个实际path/SHA引用。每臂还必须 `actual_model_parsed_unchanged=true`，且 `deterministic_deletion_policy` 与其实际应用策略完全相同；`frozen_rule_ref` 的path/SHA必须精确等于新 `package_inputs.protocol_ref`。缺少或未通过时跳过该臂，不能用另一策略的确认结果准入。风险三臂完全不读取这个文件或人工效果指标，也不写删除policy数据。

## 实际封包行为

普通/冗余臂分别删除对应候选事件；三风险臂分别将对应类别的新native段与40.46原帧并集。任何源变空时只保留该源原40.46选择，回执明确记录这是格式工程保护。保留原基线框逐值完全相等，新帧仅复用已验收连续空间场 `compose_from_field`，新空间模型调用0。

消费旧原PTS/元数据/连续空间场和纯helper时逐项核原锁与SHA，不遍历旧锁全部32025项或重跑旧成功阶段。每个实际变化且不与历史/本轮预测重复的臂，独立运行现有 `independent_validate.py` 的11项strict检查，再核单JSONL、CRC、memberSHA；通过才将 `.PENDING.zip` 改为最终ZIP并写completion。未知成绩保持UNKNOWN。部分成功目录不会被覆盖或自动恢复，成功包不会被重做。

本地仅允许 `python -B check_pure.py` 做合成事件并集/端点64/原PTS身份/空源保护检查，`python -B check_production_evidence.py` 做内存中的真实调用/alias计数及证明链反例检查，以及内存中 `ast.parse` 语法检查；这些检查不表示实际生产、封包或五包交付已完成。
