# T学生训练与主控接口

`train_student.py` 只实现一次登记的GPU job内部训练与开放开发选择，不下载、传输、调度GPU、封包或上传。成功状态只证明新学生adapter已训练并按弱开发指标选择；官网质量仍未知。正式C BCE保持STOP。

调用：

```text
PY train_student.py --run-dir RUN --labels-dir TEACHER_OUT/validated --out-dir RUN/teacher_student_autopilot_v1/student_01 --config CONFIG
```

同样参数加`--check-only`执行stdllib准入，仍会核验真实模型/媒体SHA，且不会导入模型库、创建训练目录或训练。主控必须用当前共享`resource_unlimited_v1_20261007/gpu_run.py`登记实际容量和单次作业；本脚本验证该进程属于共享GPU锁持有者。不得对已创建输出目录重复运行。

配置schema为`aic_t_student_config_v1`，`authorized=true`、`formal_C_BCE_admitted=false`、`official_upload_authorized=false`。以下示例只说明字段，主控须填真实路径和SHA：

```json
{
  "schema": "aic_t_student_config_v1",
  "authorized": true,
  "formal_C_BCE_admitted": false,
  "official_upload_authorized": false,
  "source_lock": {"path": "LOCK", "sha256": "SHA"},
  "model": {
    "base_id": "Qwen/Qwen3-VL-8B-Instruct",
    "base_revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
    "base_model_dir": "RUN/models/Qwen3-VL-8B-Instruct",
    "model_receipt": {"path": "RUN/controller/model_download_v2_status.json", "sha256": "SHA"},
    "initial_adapter_dir": "RUN/temporal_sft8b_full_v1/train_01/adapter",
    "initial_adapter_model_sha256": "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23",
    "initial_adapter_config_sha256": "SHA",
    "lora_rank": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05
  },
  "data": {
    "approved_train_manifest": {"path": "ORIGINAL_R7_TRAIN", "sha256": "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf"},
    "approved_dev_manifest": {"path": "ORIGINAL_R7_DEV", "sha256": "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"},
    "validation_receipt": {"path": "LABELS/validation_receipt.json", "sha256": "SHA"},
    "semantic_review_receipt": {"path": "SEMANTIC_RECEIPT", "sha256": "SHA"}
  },
  "input_contract": "COPY THE train_student.INPUT_CONTRACT OBJECT",
  "optimization": {
    "lr": 0.00001, "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 0.00000001,
    "weight_decay": 0.0, "grad_clip_norm": 1.0, "effective_batch_windows": 16,
    "microbatch_windows": 1, "gradient_accumulation_steps": 16, "max_epochs": 3,
    "smoke_update_limit": 20, "seed": 20261007, "precision": "bf16",
    "attn_implementation": "sdpa", "gradient_checkpointing_use_reentrant": false
  },
  "dev_stop_rule": {
    "all_selected_fraction": 0.99,
    "widespread_degraded_group_fraction": 0.75,
    "widespread_macro_f1_drop": 0.05
  }
}
```

动态source lock采用`{"files":{"ABSOLUTE_PATH":"SHA",...}}`，必须覆盖`train_student.REQUIRED_HELPERS`列出的全部冻结helpers和`train_student.py`，可以覆盖更多文件；路径按Linux最终落点写。配置、清单、语义receipt、原approved registry和模型receipt由独立引用核SHA，不把config↔source lock做成循环哈希。模型全文件核验复用现有`verify_model_receipt`。

教师验证输出保留既有schema：`eligible_train.jsonl`、`eligible_dev.jsonl`每行包括`window`、`target_json`、`teacher_record_sha256`、`explicit_no_highlight`、`label_status`；同目录有`validated_records.jsonl`和`validation_receipt.json`。record SHA精确采用`sha256(json.dumps(record,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())`的默认分隔符。学生重新验证真实raw answer、固定32B权重和解释格式，并比较每张实际学生帧RGB24的SHA及原生PTS。目标超过四位可表数字时STOP，绝不round、clamp或merge。

自动语义门必须来自第二次真实32B看相同画面、PTS和原解释的review。仅机械validator、格式通过、两次回答一致或模型大小都不能证明语义真值。该门允许无人值守继续弱监督实验，但所有receipt仍声明`WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH`。自然选出的train/dev都需要至少一个可解释正例和一个明确空例；不足时向主控报告扩展数据需求，不造固定配额或把UNKNOWN补空。

语义receipt字段：

```text
schema = aic_automated_weak_semantic_review_v1
status = PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW
mode = AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH
manual_ground_truth = false
confirm_opened = false; contest_assets_opened = false
validation_receipt_sha256 = actual SHA
files = {eligible_train.jsonl: SHA, eligible_dev.jsonl: SHA, validated_records.jsonl: SHA}
reviewed_teacher_record_sha256 = all eligible record hashes
positive_reviewed = true; explicit_empty_reviewed = true
multisegment_and_boundary_reviewed_without_fabrication = true
raw_review_receipts = {path: actual JSONL, sha256: actual SHA}
```

每条raw review至少包括`window_id`、`teacher_record_sha256`、`review_status=PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW`、`all_provided_frames_reviewed=true`、`uncertain=false`、`semantics_consistent=true`、非空`reason`、`reviewer_model_id=Qwen/Qwen3-VL-32B-Instruct`、`raw_response`及其`raw_response_sha256`、`parsed_response`、`source_frame_pixel_sha256`、`source_frame_ordinals`和`actual_pts_sec`。raw JSON字段恰好为`window_id,observation_scope,semantics_consistent,uncertain,reason,issues`；scope必须绑定完整原窗口边界和实际PTS，raw `issues=[]`、非不确定且语义一致，parsed/normalized reason及pixel/ordinal/PTS与原记录相等。真实推理额外receipt由teacher/controller锁保存。自然多段或边界例不存在时应写明确缺失说明，不能伪造实例；主控决定是否扩展自然样本，不为了凑类别暂停已有充分可解释的弱实验。

训练先用真实合格正例和明确空例各做一次assistant-only CE forward（0更新），再对相同新dev一次性评初始B作为退化参照。随后固定独立seed shuffle的3个epoch，每个自然epoch尾batch按真实样本数归一化。总更新数为`3*ceil(Ntrain/16)`，不足20即STOP。第20步属于该计划，保存prefix adapter、LoRA、optimizer、Python/NumPy/Torch/CUDA RNG、optimizer参数名顺序、完整schedule、report、完成的epoch checkpoint/dev清单和下一位置。20步恰为epoch尾时，状态明确标`EPOCH_END_CHECKPOINT_AND_DEV_PENDING`及pending epoch，不会在后续恢复时把未执行的保存/dev误记成已完成；普通batch边界标`NEXT_TRAIN_BATCH`。此版本故障后不自动resume，后续独立登记必须先处理记录的pending阶段，再从下一batch继续。

保存后真实`torch.load(...,map_location='cpu',weights_only=False)`逐项比对own SHA-bound checkpoint的全部tensor字节/dtype、NumPy/Python结构、optimizer/RNG、数据位置和活动LoRA。该pickle只读取本作业刚生成、已SHA绑定的文件，不读取外部checkpoint。活动optimizer/参数引用和实际RNG状态全程不替换、不重新seed；比对失败STOP。

随后启动独立CPU子进程，从同一固定base加载prefix adapter，核144语言target/288张量与safetensors逐字节相等、8,782,459,120总参数及完整基座/视觉、adapter-off冻结身份。子进程设置`CUDA_VISIBLE_DEVICES=''`、`device_map={'':'cpu'}`，不接触active CUDA model/optimizer/RNG，不forward/backward或更新。父进程前后再核活动参数引用/RNG不变。运行前按实际frozen tensor字节和LoRA缓冲估计与当前`psutil.virtual_memory().available`比较；容量不足STOP，不设置人为RAM限额。新增磁盘是一个`prefix_20/adapter`，不复制base权重。

主控训练CLI无新增必填参数；引擎内部自动调用以下子命令，主控不另行启动它：

```text
PY -B train_student.py verify-prefix-adapter --run-dir RUN --config CONFIG --prefix-adapter OUT/prefix_20/adapter --expected-adapter-sha SHA --expected-adapter-config-sha SHA --expected-base-sha SHA --verification-report OUT/prefix20_adapter_reload.json
```

该CPU核验属于原登记GPU作业内的工程门，额外CPU内存估计为实际frozen tensor字节+4倍LoRA tensor字节，时间/CPU占用由主控按当时机器实际资源安排。`prefix20_gate.json`只有真实state roundtrip和独立CPU adapter reload均PASS后生成；包含各自回执、pending phase、state/adapter SHA及真实冻结身份。原进程原optimizer继续剩余batch，绝不重新初始化或追加三个epoch。

epoch1/2/3各保存adapter，并各评同一新dev一次：生产同输入、相同0..5提示、可空受约束greedy。按弱标签时间交并算video macro F1，source-group bootstrap仅说明不确定性，不要求CI下界为正。选F1最大，精确并列选较小epoch。任一epoch全窗空、每窗选满99%以上，或相对初始B至少75%来源组F1下降且video macro F1下降至少0.05时STOP。该预声明启发式是防崩溃门，非官网分或因果提分证据。

成功`student_completion.json`状态为`PASS_TRAINED_SELECTED_STUDENT_ADAPTER`，主控消费字段：

- `selected_adapter_dir`、`selected_adapter_sha256`、`selected_adapter_config_sha256`、`selected_epoch`。
- `prefix_completed_updates=20`、`total_updates`、`prefix_gate`的state路径和SHA。
- `devmetrics`、`initial_B_dev`、`selected_video_macro_f1`、`selection_rule`。
- `base_frozen_evidence`（训练前、20步、训练后、selected reload和adapter-off全字节身份）、`base_frozen=true`、`vision_frozen=true`。
- `actual_logical_parameters=8782459120`、真实backward和optimizer计数、峰值显存、实际CE/梯度/首步变化。
- `T_production_inference_started=false`、`ZIP_delivered=false`、`official_score=null`。

任何失败保留`student_completion.json`与已有progress、逐例证据、checkpoint；模型库导入前失败返回3，GPU执行失败返回4。不能把checkpoint存在当最终PASS。

T生产公有接口，主控先调用`helper_paths(Path(RUN))`，不调用训练`admit/execute`：

```python
window = window_from_pts(source_path, source_sha, raw_full_source_pts,
                         natural_start, natural_end, window_id)
frames, metadata, native_plan, evidence = decode_window(window)
encoded, details = production_encode(processor, window)
result = production_generate(model, processor, window, encoded, details, candidates)
```

`window_from_pts`使用64帧整数floor含首尾，与teacher选择完全相同；原source PTS的非零origin必须保留，自然窗口尾端使用已核packet duration。`decode_window`顺序PyAV RGB24，从ordinal0解码，不seek、不按FPS造时钟，返回真实pixel SHA。`production_encode`自动调用该decoder和同一`exact_native_pts`、显式4096/25165824 budget及16384上限，无截断/降像素。`production_generate`返回window-local秒；主控加上注册source起点并沿既有源时钟映射帧，保持空与失败分离。此T的floor/PyAV/native处理差异是新整套科学recipe，不能声称与Z逐logit相同或单独归因。Z冻结入口不动。

验证命令：`PY student_cpu_tests.py`。CPU测试验证空CE标签mask、未知拒绝、同轮20步、pending epoch阶段、真实CPU AdamW checkpoint roundtrip/RNG和活动对象不变、source/parent白名单、floor/真实PTS身份与无静默边界round。两个顶层`test_production_*`函数可由pytest单独收集，直接调用新T原生selector与`raw_window_bounds`，覆盖CFR容差选ordinal1、`.1+.2`非零origin边界、LEGAL_EMPTY及失败阻断。CPU测试不能代替真实CUDA训练或完整8B CPU重载验收。
