> 本ROLE确认现已STOP_ROLE_FRESH_CONFIRM_REJECTED，禁止为该配方部署/注册/执行本入口。下文是历史条件设计，不是当前准入；不得改原门或伪造确认PASS复活。

# ROLE固定事实检查（仅条件代码）

独立角色方案版本，当前没有注册、部署或执行。本目录不授权恢复旧positive/consensus失败路线。必须采用真正ROLE开发10调用及全新确认的实际8门PASS、完整输入/输出QA和唯一账本，且三份prompt/grammar/metrics保持原字节，才能注册本入口。开发与新确认有不同实际证据schema，分别硬核查，不伪造统一的旧回执。

以下数学上界与完整集合检查沿用原证明；它只证明B0候选并集避开已知ORDINARY的充分条件，不把未决当失败或通过，不能自动426。

## 第一层结论

完整17个原0起15秒/7.5秒网格且能触原222 ORDINARY点的视图为S，P为其全部真实B0候选原段的原生帧并集。新配方不扩边，最终选择是实际保护基线B与新严格KEEP集合K的并集，因此K⊆P：

`P ∩ O = ∅` 足以证明 `(B ∪ K) \ B` 不新增任何已知ORDINARY点，并由冻结并集规则保持B。

- P避O：`B0_UPPER_BOUND_SUFFICIENT`。只证明该充分条件，不声称完整配方执行、已知KEEP全覆盖、旧FAILED修复或最终426原帧框保留已验收。
- P触O：`INCONCLUSIVE_PENDING_REGISTERED_VERIFY`。这是未决，不能说质量FAIL或PASS；本运行器停止，不自动注册/启动保守VERIFY、baseline30、strictpositive或生产。
- 缺失、工程失败或不完整QA：异常阻断并保留失败/raw/成功；不转EMPTY/UNKNOWN。合法EMPTY必须来自真实完整B0与独立输出QA。

KEEP、UNKNOWN均保留原语义；只读取原银标明确ORDINARY点，人工未选或模型DROP不是ORDINARY真值。原184 KEEP、222 ORDINARY、2675 UNKNOWN与coverage/reference-quality FAILED不改。

## 几何快照不是旧执行证据

目前没有可引用SHA的独立持久 `source_audit_plan`。`source_audit_plan_ref` 仍为必填；缺失必须拒绝。只能在新四源实际PASS后，由主线程调用已有 source_audit 的纯元数据函数，从既有原9 clock/source descriptors和完整银标形成新冻结快照；不重测时钟、解码、取得新标签，不运行旧失败方向的deploy/launcher。新快照使用原 `source_audit.main` 输出schema（`RECALL_FIXED40_SOURCE_METADATA_PLAN_V1`，source_count9、unique_input_count17、ordinary_observation_count222、metadata_only true、原FAILED保持），完整 sources/views/reference_ref/coverage都必须保留。

该快照本身可以作为同一个 `source_audit_completion_ref`。若有独立成功回执，要求status `PASS_FIXED40_SOURCE_AUDIT_METADATA_ONLY`、`source_plan_ref`精确绑定快照且model_calls0。它们只证明元数据审计完成，绝不当作17次模型或CPU输入已成功。

首次新快照还有独立纯集合QA：用已经读到的原9 clock精确physical end/PTS与222个原ORDINARY点，独立重建0起15秒/7.5秒加精确右尾去重的完整网格，筛出包含任一该源O点的所有窗。归一化的 `(sourceSHA, clockSHA, start, end)` 登记集合必须与应有集合精确相等，并拒绝不同case ID下的重复geometry。仅有9/17/222数量、单窗合法或每点至少覆盖一次均不能通过；漏掉一条重叠覆盖窗、用不触O的合法窗替换也会拒绝。该检查只验证首次新快照，不调用旧source_audit、不重测时钟、不解码或推理。每个登记视图仍另核原时钟/native64身份。

## `positive_fixed40_registration.json`

每个ref均为绝对Linux `{ "path": "...", "sha256": "actual lowercase hex" }`。示意：

```json
{
  "schema": "POSITIVE_FIXED40_B0_UPPER_BOUND_REGISTRATION_V1",
  "status": "REGISTERED_POSITIVE_FIXED40_B0_ONLY_AFTER_DEV_FRESH_CONFIRM_PASS",
  "source_scope": "EXTERNAL_NONTEST_ONLY",
  "scope": "FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5",
  "model_parameters": 8782459120,
  "optimizer_updates": 0,
  "source_count": 9,
  "unique_input_count": 17,
  "production_admitted": false,
  "reference_available_to_inference": false,
  "next_level_automatically_authorized": false,
  "protocol_ref": {"path": "MAIN/protocol_v2.json", "sha256": "..."},
  "authorization_ref": {"path": "MAIN/USER_AUTHORIZATION.json", "sha256": "..."},
  "dev_result_ref": {"path": "MAIN/dev/comparison_01/result.json", "sha256": "..."},
  "confirm_result_ref": {"path": "MAIN/confirm/comparison_01/result.json", "sha256": "..."},
  "phase_execution": {
    "dev": {
      "chain_ref": {"path": "MAIN/dev/chain_01/completion.json", "sha256": "..."},
      "registration_ref": {"path": "MAIN/registration.json", "sha256": "..."},
      "gpu_admission_ref": {"path": "MAIN/gpu_admission_dev_POSITIVE.json", "sha256": "..."},
      "gpu_completion_ref": {"path": "MAIN/dev/POSITIVE/gpu_01/completion.json", "sha256": "..."},
      "output_QA_completion_ref": {"path": "MAIN/dev/POSITIVE/output_qa_01/completion.json", "sha256": "..."},
      "resource_ref": {"path": "RUN/controller/actual_dev_job.resource.json", "sha256": "..."}
    },
    "confirm": {
      "chain_ref": {"path": "MAIN/fresh_01/confirm/chain_02/completion.json", "sha256": "..."},
      "registration_ref": {"path": "MAIN/registration_confirm.json", "sha256": "..."},
      "gpu_admission_ref": {"path": "MAIN/gpu_admission_confirm_POSITIVE.json", "sha256": "..."},
      "gpu_completion_ref": {"path": "MAIN/confirm/POSITIVE/gpu_01/completion.json", "sha256": "..."},
      "output_QA_completion_ref": {"path": "MAIN/confirm/POSITIVE/output_qa_01/completion.json", "sha256": "..."},
      "resource_ref": {"path": "RUN/controller/actual_confirm_job.resource.json", "sha256": "..."}
    }
  },
  "source_audit_plan_ref": {"path": "new immutable complete metadata snapshot", "sha256": "..."},
  "source_audit_completion_ref": {"path": "same plan or exact completed metadata receipt", "sha256": "..."},
  "source_audit_code_ref": {"path": "existing frozen source_audit.py", "sha256": "..."},
  "reference_ref": {"path": "original complete 594682-byte silver JSON", "sha256": "37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8"},
  "positive_code_files": {"MAIN/code/positive_contract.py": "...", "all frozen main positive .py": "..."},
  "required_files": {"every actual code/source/clock/reference/phase metadata path": "sha256"},
  "capacity_contract": {"video_size": {"shortest_edge": 131072, "longest_edge": 25165824}, "processor_source_path": "actual installed video_processing_qwen3_vl.py", "processor_source_sha256": "..."},
  "deadline": "explicit new timezone-aware deadline",
  "gpu_budget": {"max_actual_calls": 17, "max_seconds": 1800, "gpu_job_name": "new_unique_positive_fixed40_b0_job"},
  "execution_plan": [{"case_id": "first exact audited window ID", "mode": "NEW"}]
}
```

`execution_plan` 必须按source_audit快照顺序列足全部17个ID，每个为NEW或ADOPT。`gpu_budget.max_actual_calls`精确等于NEW数量，最多17；全部精确成功adoption时可为0，不能假造零调用完成。若尚无精确成功执行证据，登记17 NEW，不能凭窗口类似/几何lookup填ADOPT。

`required_files` 必须包含全部本目录9 `.py`、`facts_common.runtime_dependencies()`、`processor_assets()`、`CONFIG`、`RUNTIME`、共享gpu_run.py及直接依赖、实际processor源码、完整原银标/原媒体9 SHA/原9 clock SHA、所有注册refs、两阶段实际model_identity和attempts（由各gpu completion ref给出）、新快照和其审计代码、冻结的正面准入合同/合并实现。`positive_code_files` 至少含`positive_contract.py`、`positive_io.py`、`positive_metrics.py`、`positive_evaluate.py`、`positive_runtime.py`，它们必须同时与真实dev/confirm registration.required_files一致。原最大视频总像素25165824，不允许改成per-frame或降低输入要求。

## 精确成功 ADOPT

如某窗确有相同原源SHA、clock SHA、full original context/endpoints、native64 ordinals/PTS、原EMPTY_PROMPT、tensor signature、8.78245912B模型及成功首次独立QA，才可登记：

```json
{
  "case_id": "same exact audited case ID",
  "mode": "ADOPT",
  "evidence": {
    "input_ref": {"path": "...", "sha256": "..."},
    "primary_proof_ref": {"path": "...", "sha256": "..."},
    "first_input_QA_ref": {"path": "...", "sha256": "..."},
    "done_ref": {"path": "...", "sha256": "..."},
    "output_QA_ref": {"path": "...", "sha256": "..."},
    "gpu_completion_ref": {"path": "...", "sha256": "..."},
    "output_QA_completion_ref": {"path": "...", "sha256": "..."},
    "gpu_admission_ref": {"path": "...", "sha256": "..."},
    "model_identity_ref": {"path": "...", "sha256": "..."},
    "resource_ref": {"path": "...", "sha256": "..."}
  }
}
```

所有refs、实际retained tensor cache、原raw/request、原完整attempts须进required_files。adoption只读核原完整journal/唯一ledger/natural completed/exit0/输出QA与native集合，不重复成功decode/processor/model/QA；不接受猜测或补写的成功。当前代码仅接受本层新成功或原fixed40完整实际B0 QA状态，不能把只存在几何的旧方向声明为可adopt。

## 运行与检查边界

NEW输入逐源一次RGB union decode、每窗一次primary processor；所有NEW窗在单独CPU进程完成首次真实vision/native/tensor逐bit QA之后，才经既有共享wrapper唯一新B0 job。自然终态/唯一共享ledger后，独立输出token/grammar/parser/native QA引用已经完成的first input proof，GPU后不再encode输入。动态容量按每源实际几何、原processor smart_resize与实测MemAvailable/free disk计算，不用固定利用率/空闲GiB门。

本地 `python -B improvement/recall_positive_fixed40_v1/check_pure.py` 已覆盖完整9源17窗集合QA、保持17数量的合法漏/替窗拒绝、不同ID重复geometry拒绝、右尾额外多重覆盖/去重与半开边界，以及P避O/触O未决、完整输出分母/失败/错native拒绝、新fresh失败或旧consensus结果硬拒、QA在GPU前与无下一级launcher。它不代表实际17窗执行或固定事实已通过。
