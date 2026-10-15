# Existing-candidate VERIFY V1

独立外部VERIFY驱动，只处理原B0已经真实完成并独立重放的粗候选。当前没有这样的Charades新回答，本目录只实现代码和合成检查，真实输入/模型/媒体均0；不启动共享wrapper，不改local_boundary_v1/v2或Charades代码。

Linux未来根：`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/candidate_verify_v1`，代码放`code/`。scope固定`EXTERNAL_NONTEST_ONLY`；正式426不属于本驱动路径范围。

## 语义和不确定

有限输出为KEEP/UNKNOWN/DROP。KEEP和UNKNOWN完整保留原候选及原精确端点。仅有正面清晰视觉证据，确认整个候选普通或冗余且没有任何值得保留的可辨内容，才能DROP。静态风景、讲座、无音轨讲话、未完成动作、身份不清或稀疏可见证据不足都不能自动称普通；不要求完整动作/结果，不把摘要未选或动作GT未标称普通。

零个实际shown sample位于候选时，事前不确定gate把有限grammar限制为UNKNOWN。这是已冻结的证据不足政策，不是把运行失败转为UNKNOWN。输入/缓存/绑定/解析/模型失败一律阻断，并保留raw及成功项；没有空事件、UNKNOWN或DROP回退。

`cv_contract.render_retained_union(events, decisions, native_pts, physical_end)`要求完整注册决定分母，按所有KEEP/UNKNOWN候选贡献求并集。DROP只失去自身贡献，与其他保留候选重叠的帧仍保留。可选`render_interval_exact`须由主integrator事先冻结D8 padding/时间候选映射；本驱动不改空间或自选padding。

## 无视觉重做的token输入

每候选复用其原B0完整<=30s窗口、64个原帧、原timestamp视觉token prefix、pixel_values_videos/video_grid_thw及原模型/timeadapter。无媒体decode，无新vision processor encode。

原CPU完整cache必须已经是已验`TORCH_SAVE_GZIP_LOSSLESS_LEVEL1` `.pt.gz`，实际tensor signature与原CPUproof完全一致。只是pixel SHA、clock/raw或RGB NPZ不足以满足此模式；缺原vision tensor时明确`MissingOriginalCacheError`报告主代理，不擅自重decode/重processor。

新输入从原expanded input_ids文本只替换唯一EMPTY_PROMPT；原全文tokenizer roundtrip必须完全一致，新旧完整vision prefix IDs必须相同，pixel/grid signature必须相同。只用tokenizer生成新input_ids/attention_mask，既不截断也不改时间/像素/归一化。若tokenizer或输入keys不匹配就失败，无猜测适配。

新磁盘cache仅存`prompt_tokens.pt.gz`，严格SHA引用原大visioncache。GPU加载两份已验cache组合并核完整CPU/GPUsignature，避免按每候选再落盘重复大tensor。独立CPU replay用partition+tokenizer.encode重构新token，核旧vision prefix/缓存原signature、原case/segment/秒/native membership、token IDs/raw/grammar/实际模型身份、唯一resource/ledger。没有模型或视觉重做。

当前生产665候选/1995请求路线的原缓存只有hash/clock/oldraw，没有RGB/tensor。不能由本外部驱动声称生产decode/processor0；生产独立materialization协议由主代理另冻，本目录不提供fallback。

## 注册与次序

先准备真实B0 coarse/raw/独立replay、完整source separation、当前官方规则receipt与protocol，再写`BASE/registration.json`。

必要字段：

```json
{
  "schema":"CANDIDATE_VERIFY_V1",
  "status":"FROZEN_EXTERNAL_ORIGINAL_B0_CANDIDATE_VERIFY",
  "source_scope":"EXTERNAL_NONTEST_ONLY",
  "model_parameters":8782459120,
  "new_optimizer_updates":0,
  "selection_frozen_before_verify_answers":true,
  "actual_model_call_budget":10,
  "allowed_source_roles":["dev"],
  "new_media_decode_admitted":false,
  "new_vision_processor_admitted":false,
  "protocol_path":"BASE/PROTOCOL.md",
  "protocol_sha256":"ACTUAL_SHA",
  "official_rule_check_path":"BASE/official_rules.json",
  "official_rule_check_sha256":"ACTUAL_SHA",
  "required_files":{"EXACT_PATH":"ACTUAL_SHA"},
  "events":[{
    "event_id":"DEV_001",
    "original_case_id":"ORIGINAL_B0_CASE_ID",
    "original_segment_index":0,
    "original_interval_exact":["EXACT_SOURCE_START","EXACT_SOURCE_END"],
    "clock_object_keys":["clock"],
    "original_evidence":{
      "input":{"path":"OLD_INPUT_JSON","sha256":"ACTUAL_SHA"},
      "cpu_proof":{"path":"OLD_CPU_PROOF_JSON","sha256":"ACTUAL_SHA"},
      "done":{"path":"OLD_DONE_JSON","sha256":"ACTUAL_SHA"},
      "raw":{"path":"OLD_RAW_JSON","sha256":"ACTUAL_SHA"},
      "request":{"path":"OLD_REQUEST_JSON","sha256":"ACTUAL_SHA"},
      "independent_replay":{"path":"OLD_REPLAY_JSON","sha256":"ACTUAL_SHA"},
      "model_identity":{"path":"OLD_ACTUAL_MODEL_IDENTITY_JSON","sha256":"ACTUAL_SHA"},
      "source_separation":{"path":"CANONICAL_COMPLETE_SOURCE_SEPARATION_JSON","sha256":"ACTUAL_SHA"},
      "clock":{"path":"COMPLETE_CLOCK_JSON","sha256":"ACTUAL_SHA"}
    }
  }]
}
```

占位模板不能直接执行。预算必须等于events数；确认角色需独立冻结protocol后明确登记。原外部coarse证据schema必须匹配接口，规范receipt必须有`known_current_b_training_and_426_test_identities_complete=true`及空identity/byte intersections；缺schema/实际证据先适配审查，不忽略字段。

1. `plan_verify.py`只读旧证据/缓存，输出独立plan，不读媒体。
2. `prepare_verify_tokens.py`逐新候选一次新tokenizer输入，输出小tokencache、完整signature及byte/time/RSS回执；原vision/timestamp cache只读取。
3. 主代理独立审查后写`gpu_admission.json`，status `PASS_INDEPENDENT_VERIFY_GPU_ADMISSION`，字段registration_sha256/cpu_completion_sha256/actual_model_call_budget/gpu_job_name/source_input_lock_files。锁覆盖registration/protocol/rules/code/plan/所有旧coarse证据/原visioncache/新meta/proof/tokencache。
4. 唯一原共享`gpu_run.py` job运行`infer_verify.py`，原B及timeadapter实际8,782,459,120参数、optimizer0；完整BEGIN/raw/done/ACCEPTED journal，一候选一次新VERIFY，不重跑B0。
5. actual completed/exit0及唯一ledger一致后，独立CPU进程运行`replay_verify.py`，输出`verification_export.json`。它只证明工程执行和重放，质量/科学对照/联合renderer/实际差异/新ZIP由主代理验收。

这些入口都无自动恢复，输出目录和文件以create-x防重复。纯合成通过不等于真实tokenizer retarget可用、新schema模型效果或生产准入。
